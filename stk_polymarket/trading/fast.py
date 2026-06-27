"""
Envio de ordens de baixa latência para a CLOB V2 da Polymarket.

Contexto (pesquisa do fonte do py-clob-client-v2): no envio de uma ordem o gargalo é
REDE, não CPU. O hot path oficial já é enxuto quando "quente" — 1 único POST /order,
metadados (tick_size/neg_risk/version) cacheados, httpx HTTP/2 keep-alive, relógio
local. Assinatura ~ms (sub-ms com coincurve); HMAC ~µs.

O FastTrader extrai os ganhos onde a latência realmente está, SEM reimplementar
criptografia (reusa as primitivas auditadas do SDK — paridade byte-a-byte garantida):

  * zero GET no hot path: tick_size/neg_risk/creds pré-cacheados; versão fixada em 2;
  * conexão httpx/HTTP2 própria, persistente e PRÉ-AQUECIDA (TLS fora do caminho da ordem);
  * relógio local (sem GET /time);
  * builders de assinatura por exchange instanciados 1x (domain separator pré-computado);
  * envio mínimo: serializa 1x, 1 HMAC, 1 POST — sem os wrappers de retry/version do SDK;
  * coincurve (se instalado) deixa o ECDSA sub-ms;
  * pré-assinatura (`presign`) de ordens GTC: ao disparar só json.dumps+HMAC+POST.

O hot path mantém ZERO chamadas de rede além do POST /order. Para o caminho simples
(latência não crítica / oráculo de testes) use `stk_polymarket.trading.send.send_order`.
"""

import json
import time
from typing import Any

import httpx
from py_clob_client_v2 import ApiCreds, ClobClient, OrderType, SignatureTypeV2
from py_clob_client_v2.clob_types import RequestArgs
from py_clob_client_v2.config import get_contract_config
from py_clob_client_v2.constants import BYTES32_ZERO
from py_clob_client_v2.endpoints import OK, POST_ORDER
from py_clob_client_v2.headers.headers import create_level_2_headers
from py_clob_client_v2.order_builder.builder import ROUNDING_CONFIG, OrderBuilder
from py_clob_client_v2.order_utils import ExchangeOrderBuilderV2
from py_clob_client_v2.order_utils.model.order_data_v2 import (
    OrderDataV2,
    SignedOrderV2,
    order_to_json_v2,
)
from py_clob_client_v2.utilities import price_valid

from stk_polymarket.connection.connect import CHAIN_ID, HOST, derive_or_create_creds
from stk_polymarket.trading.send import OrderRejected


class FastTrader:
    """
    Enviador de ordens de baixa latência (CLOB V2, carteira EOA por padrão).

    Uso:
        ft = FastTrader(private_key).warmup(token_ids=[tid])
        ft.fok(tid, price=0.62, size=10, side="BUY")     # marketable
        signed = ft.presign(tid, 0.55, 20, "BUY")        # pré-assina (GTC)
        ft.send(signed, OrderType.GTC)                   # dispara depois (só HMAC+POST)
    """

    def __init__(
        self,
        private_key: str,
        creds: ApiCreds | None = None,
        signature_type: int = 0,
        funder: str | None = None,
        host: str = HOST,
        chain_id: int = CHAIN_ID,
        read_timeout: float = 2.0,
        http2: bool = True,
    ):
        if not private_key:
            raise ValueError("private_key ausente.")

        from py_clob_client_v2.signer import Signer

        self.host = host.rstrip("/")
        self.chain_id = chain_id
        self.sig_type = SignatureTypeV2(signature_type)
        self.creds = creds

        self.signer = Signer(private_key, chain_id)
        self.address = self.signer.address()

        # OrderBuilder reusa a lógica auditada de amounts + maker/signer.
        # funder=None faz o OrderBuilder usar o próprio endereço (EOA).
        self._ob = OrderBuilder(
            signer=self.signer, signature_type=self.sig_type, funder=funder
        )
        self.funder = self._ob.funder
        self._order_signer = self._ob._v2_order_signer()  # = address para EOA

        # Um builder de assinatura por exchange (precomputa o domain separator 1x).
        cfg = get_contract_config(chain_id)
        self._exchange_addr = {
            False: cfg.exchange_v2,
            True: cfg.neg_risk_exchange_v2,
        }
        self._builder = {
            nr: ExchangeOrderBuilderV2(addr, chain_id, self.signer)
            for nr, addr in self._exchange_addr.items()
        }

        # Cache de metadados por token (zero GET no hot path).
        self._tick: dict[str, str] = {}
        self._neg: dict[str, bool] = {}

        # Conexão HTTP própria, persistente e tunada.
        self._http = httpx.Client(
            http2=http2,
            timeout=httpx.Timeout(
                connect=5.0, read=read_timeout, write=read_timeout, pool=2.0
            ),
            limits=httpx.Limits(
                max_connections=10, max_keepalive_connections=10, keepalive_expiry=60.0
            ),
            headers={
                "User-Agent": "stk_polymarket_fast",
                "Accept": "*/*",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
            },
        )
        self._setup_client: ClobClient | None = None

    # ----------------------------- setup (caminho frio) -----------------------------

    def _client(self) -> ClobClient:
        """ClobClient lazy, só para setup (derive de creds e fetch de metadados)."""
        if self._setup_client is None:
            self._setup_client = ClobClient(
                self.host,
                chain_id=self.chain_id,
                key=self.signer.private_key,
                creds=self.creds,
                signature_type=int(self.sig_type),
                funder=self.funder,
            )
            if self.creds is not None:
                self._setup_client.set_api_creds(self.creds)
        return self._setup_client

    def warmup(
        self,
        token_ids: list[str] | None = None,
        *,
        derive_creds: bool = True,
        prewarm_conn: bool = True,
        warm_crypto: bool = True,
    ) -> "FastTrader":
        """
        Pré-aquece tudo que sairia do hot path:
          - deriva/cria as creds L2 (1x);
          - cacheia tick_size + neg_risk dos tokens;
          - abre a conexão TLS/HTTP2 (absorve o handshake);
          - aquece o backend ECDSA (absorve import/1ª assinatura).
        """
        if self.creds is None and derive_creds:
            self.creds = derive_or_create_creds(self._client())
            self._client().set_api_creds(self.creds)
        if token_ids:
            self.cache_market(token_ids)
        if prewarm_conn:
            try:
                self._http.get(f"{self.host}{OK}")
            except Exception:
                pass
        if warm_crypto:
            self._warm_crypto()
        return self

    def cache_market(self, token_ids: list[str]) -> "FastTrader":
        """Busca e cacheia tick_size + neg_risk dos tokens (uma vez)."""
        client = self._client()
        for raw in token_ids:
            t = str(raw)
            if t not in self._tick:
                self._tick[t] = client.get_tick_size(t)
            if t not in self._neg:
                self._neg[t] = client.get_neg_risk(t)
        return self

    def set_market(self, token_id: str, tick_size: str, neg_risk: bool) -> "FastTrader":
        """Define tick_size/neg_risk manualmente (sem rede), se já os conhece."""
        self._tick[str(token_id)] = tick_size
        self._neg[str(token_id)] = bool(neg_risk)
        return self

    def _warm_crypto(self) -> None:
        try:
            from eth_account import Account

            Account._sign_hash(b"\x00" * 32, private_key=self.signer.private_key)
        except Exception:
            pass

    # ------------------------------- hot path -------------------------------

    def build_signed(
        self, token_id: str, price: float, size: float, side: str, expiration: int = 0
    ) -> SignedOrderV2:
        """
        Constrói e assina a ordem localmente (zero rede). Replica exatamente
        `OrderBuilder.build_order(..., version=2)` usando os caches.
        """
        token_id = str(token_id)
        try:
            tick = self._tick[token_id]
            neg = self._neg[token_id]
        except KeyError:
            raise RuntimeError(
                f"token {token_id} não pré-cacheado; chame warmup()/cache_market()/set_market() antes."
            )

        if not price_valid(price, tick):
            ts = float(tick)
            raise ValueError(f"preço inválido ({price}); min {ts} max {1 - ts}")

        side_enum, maker_amount, taker_amount = self._ob.get_order_amounts(
            side, size, price, ROUNDING_CONFIG[tick]
        )
        order_data = OrderDataV2(
            maker=self.funder,
            tokenId=token_id,
            makerAmount=str(maker_amount),
            takerAmount=str(taker_amount),
            side=side_enum,
            signer=self._order_signer,
            signatureType=self.sig_type,
            timestamp=str(time.time_ns() // 1_000_000),
            metadata=BYTES32_ZERO,
            builder=BYTES32_ZERO,
            expiration=str(int(expiration)),
        )
        return self._builder[neg].build_signed_order(order_data)

    def send(
        self,
        signed: SignedOrderV2,
        order_type: str = OrderType.GTC,
        *,
        post_only: bool = False,
        defer_exec: bool = False,
        raise_on_reject: bool = True,
    ) -> dict[str, Any]:
        """Envia uma ordem já assinada (só json.dumps + HMAC + POST)."""
        if self.creds is None:
            raise RuntimeError("creds ausentes; chame warmup() ou passe creds no construtor.")

        owner = self.creds.api_key or ""
        payload = order_to_json_v2(signed, owner, order_type, post_only, defer_exec)
        serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        headers = create_level_2_headers(
            self.signer,
            self.creds,
            RequestArgs(
                method="POST",
                request_path=POST_ORDER,
                body=payload,
                serialized_body=serialized,
            ),
        )
        resp = self._http.post(
            f"{self.host}{POST_ORDER}",
            headers=headers,
            content=serialized.encode("utf-8"),
        )
        return self._handle(resp, raise_on_reject)

    def submit(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str,
        order_type: str = OrderType.GTC,
        *,
        expiration: int = 0,
        raise_on_reject: bool = True,
    ) -> dict[str, Any]:
        """Constrói, assina e envia numa chamada."""
        signed = self.build_signed(token_id, price, size, side, expiration)
        return self.send(signed, order_type, raise_on_reject=raise_on_reject)

    def fok(self, token_id, price, size, side, **kw):
        return self.submit(token_id, price, size, side, OrderType.FOK, **kw)

    def fak(self, token_id, price, size, side, **kw):
        return self.submit(token_id, price, size, side, OrderType.FAK, **kw)

    def gtc(self, token_id, price, size, side, **kw):
        return self.submit(token_id, price, size, side, OrderType.GTC, **kw)

    def gtd(self, token_id, price, size, side, expiration, **kw):
        return self.submit(
            token_id, price, size, side, OrderType.GTD, expiration=expiration, **kw
        )

    def presign(
        self, token_id: str, price: float, size: float, side: str, expiration: int = 0
    ) -> SignedOrderV2:
        """Assina agora; dispare depois com `send(signed, ...)` (latência mínima no disparo)."""
        return self.build_signed(token_id, price, size, side, expiration)

    # ------------------------------- helpers -------------------------------

    def serialize(
        self, signed: SignedOrderV2, order_type: str = OrderType.GTC
    ) -> str:
        """Payload serializado idêntico ao do SDK (usado nos testes de paridade)."""
        owner = (self.creds.api_key if self.creds else "") or ""
        payload = order_to_json_v2(signed, owner, order_type)
        return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    def _handle(self, resp: httpx.Response, raise_on_reject: bool) -> dict[str, Any]:
        if resp.status_code != 200:
            body = resp.text
            if raise_on_reject:
                raise OrderRejected(f"[{resp.status_code}] {body}")
            return {"success": False, "status_code": resp.status_code, "error": body}
        try:
            data = resp.json()
        except Exception:
            return {"raw": resp.text}
        if (
            raise_on_reject
            and isinstance(data, dict)
            and (data.get("success") is False or data.get("errorMsg"))
        ):
            raise OrderRejected(f"Ordem rejeitada: {data}")
        return data

    def close(self) -> None:
        try:
            self._http.close()
        except Exception:
            pass

    def __enter__(self) -> "FastTrader":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


__all__ = ["FastTrader"]
