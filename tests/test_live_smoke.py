"""
Smoke ao vivo (gated). Valida o caminho REAL contra a CLOB V2 sem mexer em fundos
por padrão.

Rodar:
    RUN_LIVE=1 STK_PK=0x... STK_TOKEN_ID=<token> pytest -m live

Por padrão (read+sign, NÃO envia ordem):
    - deriva credenciais L2;
    - get_ok;
    - cacheia tick_size + neg_risk do token;
    - constrói e assina uma ordem (offline) — prova o caminho completo até o POST.

Para ENVIAR uma ordem FOK mínima de verdade (gasta saldo!):
    STK_LIVE_ORDER=1 STK_PRICE=0.01 STK_SIZE=1 ...
"""

import os

import pytest

RUN_LIVE = os.getenv("RUN_LIVE") == "1"

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not RUN_LIVE, reason="defina RUN_LIVE=1 (e STK_PK/STK_TOKEN_ID)"),
]


@pytest.fixture
def env():
    pk = os.environ.get("STK_PK")
    tid = os.environ.get("STK_TOKEN_ID")
    if not pk or not tid:
        pytest.skip("defina STK_PK e STK_TOKEN_ID")
    return pk, tid


def test_read_and_sign_live(env):
    from stk_polymarket.trading.fast import FastTrader

    pk, tid = env
    ft = FastTrader(pk).warmup(token_ids=[tid])
    try:
        assert ft.creds is not None and ft.creds.api_key
        assert tid in ft._tick and tid in ft._neg
        signed = ft.build_signed(tid, 0.5, 1, "BUY")
        assert signed.signature.startswith("0x")
    finally:
        ft.close()


@pytest.mark.skipif(
    os.getenv("STK_LIVE_ORDER") != "1",
    reason="defina STK_LIVE_ORDER=1 para realmente enviar (gasta saldo)",
)
def test_send_tiny_fok_live(env):
    from stk_polymarket.trading.fast import FastTrader

    pk, tid = env
    price = float(os.getenv("STK_PRICE", "0.01"))
    size = float(os.getenv("STK_SIZE", "1"))
    ft = FastTrader(pk).warmup(token_ids=[tid])
    try:
        resp = ft.fok(tid, price, size, "BUY", raise_on_reject=False)
        print("FOK resp:", resp)
        assert isinstance(resp, dict)
    finally:
        ft.close()
