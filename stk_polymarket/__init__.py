"""
striker-polymarket — dados e trading de baixa latência na Polymarket (CLOB V2).

API pública principal:
    from stk_polymarket import clob, FastTrader, send_order, OrderType

A camada de dados (mercados, posições, PnL, CLV, preço histórico) fica em
`stk_polymarket.api.*` e o WebSocket em `stk_polymarket.wss.*` (importe sob demanda
para não puxar pandas/loading_animation desnecessariamente).
"""

__version__ = "0.2.0"

from stk_polymarket.connection import HOST, CHAIN_ID, auth, clob
from stk_polymarket.trading import (
    FastTrader,
    OrderRejected,
    OrderType,
    is_filled,
    send_order,
)

__all__ = [
    "clob",
    "auth",
    "FastTrader",
    "send_order",
    "is_filled",
    "OrderRejected",
    "OrderType",
    "HOST",
    "CHAIN_ID",
    "__version__",
]
