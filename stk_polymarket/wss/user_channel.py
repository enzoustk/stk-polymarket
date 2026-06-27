"""
Stream do canal de usuário (CLOB WebSocket, autenticado L2).

A autenticação L2 é enviada NA MENSAGEM de subscrição ({apiKey, secret, passphrase}),
não em headers. Migrado para a API asyncio nova do `websockets` (>=14): sem
`extra_headers`, sem `ws.open`, ping embutido (keepalive nativo).

`creds` é o ApiCreds da V2 (mesmo objeto retornado por `connection.clob().creds`).

NOTA: o formato exato do subscribe do canal de usuário deve ser confirmado por um
smoke test ao vivo contra a doc atual; o transporte (abaixo) está na API nova.
"""

import asyncio
import json
from typing import Awaitable, Callable, Optional, Sequence

import websockets
from py_clob_client_v2 import ApiCreds

USER_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/user"


async def start(
    creds: ApiCreds,
    on_new_data: Optional[Callable[..., Awaitable[None]]] = None,
    markets: Optional[Sequence[str]] = None,
    url: str = USER_WS_URL,
    *,
    verbose: bool = False,
    reconnect_delay: float = 5.0,
) -> None:
    """
    Conecta ao canal de usuário (autenticado) e encaminha cada mensagem.

    Args:
        creds: ApiCreds (api_key/api_secret/api_passphrase) da V2.
        on_new_data: corrotina chamada como `await on_new_data(message=<str>)`.
        markets: condition_ids a filtrar (opcional).
    """
    subscribe = json.dumps(
        {
            "type": "user",
            "markets": list(markets) if markets else [],
            "auth": {
                "apiKey": creds.api_key,
                "secret": creds.api_secret,
                "passphrase": creds.api_passphrase,
            },
        }
    )

    while True:
        try:
            async with websockets.connect(url) as ws:
                await ws.send(subscribe)
                async for message in ws:
                    if verbose:
                        print(message)
                    if on_new_data is not None:
                        try:
                            await on_new_data(message=message)
                        except Exception as e:
                            print(f"Erro processando update do wss: {e}")
        except asyncio.CancelledError:
            print("🛑 User stream cancelado.")
            break
        except Exception as e:
            print(f"⚠️ Erro no WS de usuário: {e}; reconectando em {reconnect_delay}s")
            await asyncio.sleep(reconnect_delay)


__all__ = ["start", "USER_WS_URL"]
