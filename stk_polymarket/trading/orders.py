from typing import Optional, Dict, Any
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderType
from stk_polymarket.trading.send import send_order

def fok(
    side: str,
    client: ClobClient,
    asset: str,
    size: float,
    price: float
    ) -> Optional[Dict[str, Any]]:
    return send_order(
        client,
        price,
        size,
        side,
        asset,
        OrderType.FOK
    )


def fak(
    side,
    client: ClobClient,
    asset: str,
    price: float,
    size: float
    ) -> Optional[Dict[str, Any]]:
    """
    Compra/Vende a limite via FAK -> Fill and Kill
    """
    return send_order(
        side=side,
        client=client,
        price=price,
        size=size,
        asset=asset,
        order_type=OrderType.FAK
    )


def gtc(
    side,
    client: ClobClient,
    asset: str,
    size: float,
    price: float
    ) -> Optional[Dict[str, Any]]:
    """Ordem Limit padrão. Fica no livro até você cancelar."""
    return send_order(
        side=side,
        client=client,
        price=price,
        size=size,
        asset=asset,
        order_type=OrderType.GTC
    )


def gtd(
    side,
    client: ClobClient,
    asset: str,
    size: float,
    price: float,
    expiration_ts: int
    ) -> Optional[Dict[str, Any]]:
    """
    Ordem Limit com data de validade.
    expiration_ts: Timestamp UNIX (int) de quando a ordem expira.
    """
    return send_order(
        side=side,
        client=client,
        price=price,
        size=size,
        asset=asset,
        order_type=OrderType.GTD,
        expiration=expiration_ts
    )
