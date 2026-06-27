"""
Oráculo de paridade: o FastTrader (hot path) deve produzir EXATAMENTE a mesma ordem
assinada e o mesmo payload serializado que o caminho oficial do SDK
(`OrderBuilder.build_order(version=2)` / `order_to_json_v2`).

Tudo offline (salt+timestamp congelados pelo fixture `frozen`).
"""

import dataclasses
import json

import pytest
from py_clob_client_v2 import OrderArgsV2, OrderType, SignatureTypeV2
from py_clob_client_v2.clob_types import CreateOrderOptions
from py_clob_client_v2.order_builder.builder import OrderBuilder
from py_clob_client_v2.order_utils.model.order_data_v2 import order_to_json_v2
from py_clob_client_v2.signer import Signer

from stk_polymarket.trading.fast import FastTrader

TID = "71321045679252212594626385532706912750332728571942532289631379312455583992563"

CASES = [
    # side, price, size, tick, neg_risk
    ("BUY", 0.62, 12.5, "0.01", False),
    ("SELL", 0.41, 30.0, "0.01", True),
    ("BUY", 0.123, 100.0, "0.001", False),
    ("SELL", 0.9999, 5.0, "0.0001", False),
    ("BUY", 0.5, 7.0, "0.1", True),
]


@pytest.mark.parametrize("side,price,size,tick,neg", CASES)
def test_build_signed_matches_sdk(frozen, pk, dummy_creds, side, price, size, tick, neg):
    # SDK de referência
    signer = Signer(pk, 137)
    ob = OrderBuilder(signer, SignatureTypeV2.EOA, funder=None)
    sdk = ob.build_order(
        OrderArgsV2(token_id=TID, price=price, size=size, side=side),
        CreateOrderOptions(tick_size=tick, neg_risk=neg),
        version=2,
    )

    # FastTrader
    ft = FastTrader(pk)
    ft.set_market(TID, tick, neg)
    ft.creds = dummy_creds
    fast = ft.build_signed(TID, price, size, side)

    # Ordem assinada idêntica (inclui a assinatura ECDSA)
    assert dataclasses.asdict(fast) == dataclasses.asdict(sdk)

    # Payload serializado byte-a-byte idêntico
    sdk_payload = json.dumps(
        order_to_json_v2(sdk, dummy_creds.api_key, OrderType.GTC),
        separators=(",", ":"),
        ensure_ascii=False,
    )
    assert ft.serialize(fast, OrderType.GTC) == sdk_payload
    ft.close()


def test_signed_order_has_v2_shape(frozen, pk, dummy_creds):
    ft = FastTrader(pk)
    ft.set_market(TID, "0.01", False)
    ft.creds = dummy_creds
    signed = ft.build_signed(TID, 0.62, 12.5, "BUY")
    # campos do struct V2 (timestamp em ms, signature 0x..., signatureType EOA)
    assert signed.signatureType == SignatureTypeV2.EOA
    assert signed.signature.startswith("0x")
    assert len(signed.timestamp) == 13  # ms (13 dígitos)
    assert signed.maker == signed.signer == ft.address
    ft.close()
