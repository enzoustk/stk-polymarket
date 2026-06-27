"""Regressão: os módulos wss importam (o bug `on_new_data: function` dava NameError)."""

import importlib

import pytest


@pytest.mark.parametrize(
    "mod",
    [
        "stk_polymarket",
        "stk_polymarket.connection.connect",
        "stk_polymarket.connection.auth",
        "stk_polymarket.trading.fast",
        "stk_polymarket.trading.send",
        "stk_polymarket.trading.orders",
        "stk_polymarket.wss.market_channel",
        "stk_polymarket.wss.user_channel",
    ],
)
def test_module_imports(mod):
    importlib.import_module(mod)


def test_public_api_surface():
    import stk_polymarket as s

    for name in ["clob", "auth", "FastTrader", "send_order", "OrderType", "HOST", "CHAIN_ID"]:
        assert hasattr(s, name), name


def test_chain_id_is_int():
    from stk_polymarket.connection.connect import CHAIN_ID

    assert CHAIN_ID == 137 and isinstance(CHAIN_ID, int)
