"""
Envio de ordens via SDK oficial (caminho de referência / baseline, CLOB V2).

Este é o caminho SIMPLES e CORRETO: usa `ClobClient.create_and_post_order` do
py-clob-client-v2. Serve para:
  - uso direto quando latência não é crítica;
  - oráculo de paridade dos testes (o FastTrader deve produzir o MESMO payload).

Para o caminho de baixa latência use `stk_polymarket.trading.fast.FastTrader`.
"""

from typing import Any

from py_clob_client_v2 import (
    ClobClient,
    OrderArgsV2,
    OrderType,
    PartialCreateOrderOptions,
)
from py_clob_client_v2.exceptions import PolyApiException

# Status terminais retornados pelo /order (ver SendOrderResponse da V2):
#   matched = executada (preenchida) · live = em repouso no book · delayed = enfileirada
TERMINAL_FILLED = "matched"


class OrderRejected(Exception):
    """Ordem rejeitada pelo servidor (não-200 ou success=False)."""


def send_order(
    client: ClobClient,
    price: float,
    size: float,
    side: str,
    token_id: str,
    order_type: str = OrderType.GTC,
    *,
    tick_size: str | None = None,
    neg_risk: bool | None = None,
    expiration: int = 0,
    raise_on_reject: bool = True,
) -> dict[str, Any]:
    """
    Cria, assina e envia uma ordem via SDK V2.

    Diferente da versão V1 (que retornava None em silêncio), aqui o erro é
    propagado e o status é interpretado.

    Args:
        tick_size/neg_risk: se informados, evitam o GET de metadados no caminho da
            ordem (passe-os pré-cacheados para reduzir latência).
        order_type: "GTC" | "GTD" | "FOK" | "FAK".
        expiration: timestamp UNIX (s) para GTD.

    Returns:
        dict de resposta do servidor.

    Raises:
        OrderRejected: em rejeição (se raise_on_reject=True).
    """
    options = None
    if tick_size is not None or neg_risk is not None:
        options = PartialCreateOrderOptions(tick_size=tick_size, neg_risk=neg_risk)

    args = OrderArgsV2(
        token_id=str(token_id),
        price=float(price),
        size=float(size),
        side=side,
        expiration=int(expiration),
    )

    try:
        resp = client.create_and_post_order(args, options, order_type)
    except PolyApiException as e:
        if raise_on_reject:
            raise OrderRejected(_describe_api_error(e)) from e
        return {"success": False, "error": _describe_api_error(e)}

    if raise_on_reject and not _is_accepted(resp):
        raise OrderRejected(f"Ordem rejeitada: {resp}")
    return resp


def is_filled(resp: dict[str, Any]) -> bool:
    """True se a resposta indica execução (status=matched)."""
    return isinstance(resp, dict) and resp.get("status") == TERMINAL_FILLED


def _is_accepted(resp: Any) -> bool:
    if not isinstance(resp, dict):
        return False
    if resp.get("success") is False:
        return False
    if resp.get("errorMsg") or resp.get("error"):
        return False
    # Aceita se veio um id/status de ordem
    return bool(resp.get("orderID") or resp.get("orderId") or resp.get("status") or resp.get("success"))


def _describe_api_error(e: PolyApiException) -> str:
    status = getattr(e, "status_code", None)
    msg = getattr(e, "error_message", None) or getattr(e, "msg", None) or str(e)
    return f"[{status}] {msg}"


__all__ = ["send_order", "is_filled", "OrderRejected", "TERMINAL_FILLED"]
