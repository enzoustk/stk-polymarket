"""
Stream do canal de mercado (CLOB WebSocket, não autenticado).

Subscreve uma lista de token_ids e chama `on_new_data(message=...)` a cada update.
Migrado para a API asyncio nova do `websockets` (>=14): sem `ws.open`, ping embutido.
"""

import asyncio
import json
from typing import Awaitable, Callable, Sequence

import websockets

MARKET_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


async def run(
    token_ids: Sequence[str],
    on_new_data: Callable[..., Awaitable[None]],
    url: str = MARKET_WS_URL,
    *,
    reconnect_delay: float = 5.0,
) -> None:
    """
    Conecta ao canal de mercado e encaminha cada mensagem para `on_new_data`.

    Args:
        token_ids: lista de token_ids (assets_ids) a subscrever.
        on_new_data: corrotina chamada como `await on_new_data(message=<str>)`.
    """
    print(f"🚀 Polymarket market stream para {len(token_ids)} tokens...")
    subscribe = json.dumps(
        {"assets_ids": [str(t) for t in token_ids], "type": "market"}
    )

    while True:
        try:
            async with websockets.connect(url) as ws:
                await ws.send(subscribe)
                print("📡 Inscrito no canal de mercado.")
                async for message in ws:
                    await on_new_data(message=message)
        except asyncio.CancelledError:
            print("🛑 Market stream cancelado.")
            break
        except Exception as e:
            print(f"⚠️ Erro no WS de mercado: {e}; reconectando em {reconnect_delay}s")
            await asyncio.sleep(reconnect_delay)


__all__ = ["run", "MARKET_WS_URL"]
