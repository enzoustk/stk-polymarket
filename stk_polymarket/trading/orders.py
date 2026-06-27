"""
Wrappers por tipo de ordem (CLOB V2), roteando para o caminho de baixa latência.

Mudança da V1: estas funções recebem um `FastTrader` (não mais um ClobClient V1).
São açúcar sintático fino sobre `FastTrader`:

    ft = FastTrader(private_key).warmup(token_ids=[tid])
    fok(ft, "BUY", tid, size=10, price=0.62)

Para o caminho simples via SDK use `stk_polymarket.trading.send.send_order`.
"""

from typing import Any

from stk_polymarket.trading.fast import FastTrader


def fok(trader: FastTrader, side: str, token_id: str, size: float, price: float, **kw) -> dict[str, Any]:
    """Fill-or-Kill: executa tudo imediatamente ou cancela."""
    return trader.fok(token_id, price, size, side, **kw)


def fak(trader: FastTrader, side: str, token_id: str, price: float, size: float, **kw) -> dict[str, Any]:
    """Fill-and-Kill: executa o que der imediatamente, cancela o resto."""
    return trader.fak(token_id, price, size, side, **kw)


def gtc(trader: FastTrader, side: str, token_id: str, size: float, price: float, **kw) -> dict[str, Any]:
    """Good-Til-Cancelled: ordem limite que fica no book até cancelar."""
    return trader.gtc(token_id, price, size, side, **kw)


def gtd(
    trader: FastTrader,
    side: str,
    token_id: str,
    size: float,
    price: float,
    expiration_ts: int,
    **kw,
) -> dict[str, Any]:
    """Good-Til-Date: ordem limite com validade. expiration_ts = UNIX (s)."""
    return trader.gtd(token_id, price, size, side, expiration_ts, **kw)


__all__ = ["fok", "fak", "gtc", "gtd"]
