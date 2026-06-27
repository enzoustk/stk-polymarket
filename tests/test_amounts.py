"""Vetores de escala/arredondamento de amounts (USDC/CTF = 6 casas)."""

import pytest
from eth_account import Account

from stk_polymarket.trading.fast import FastTrader

TID = "123"


@pytest.fixture
def trader():
    ft = FastTrader(Account.create().key.hex())
    yield ft
    ft.close()


@pytest.mark.parametrize(
    "side,price,size,tick,maker,taker",
    [
        # BUY 12.5 @ 0.62: paga 7.75 USDC (maker), recebe 12.5 tokens (taker)
        ("BUY", 0.62, 12.5, "0.01", "7750000", "12500000"),
        # SELL 12.5 @ 0.62: dá 12.5 tokens (maker), recebe 7.75 USDC (taker)
        ("SELL", 0.62, 12.5, "0.01", "12500000", "7750000"),
        # tick 0.001
        ("BUY", 0.123, 100.0, "0.001", "12300000", "100000000"),
    ],
)
def test_amount_scaling(frozen, trader, side, price, size, tick, maker, taker):
    trader.set_market(TID, tick, False)
    from py_clob_client_v2 import ApiCreds

    trader.creds = ApiCreds("k", "c2VjcmV0", "p")
    signed = trader.build_signed(TID, price, size, side)
    assert signed.makerAmount == maker
    assert signed.takerAmount == taker


def test_invalid_price_rejected(trader):
    trader.set_market(TID, "0.01", False)
    with pytest.raises(ValueError):
        trader.build_signed(TID, 1.5, 10, "BUY")  # > 1-tick


def test_uncached_token_raises(trader):
    with pytest.raises(RuntimeError):
        trader.build_signed("999", 0.5, 10, "BUY")  # nunca cacheado
