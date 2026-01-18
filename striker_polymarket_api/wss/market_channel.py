"""
Módulo para conectar-se a o wss de uma lista de token_ids
a função run precisa de on_new_data com arg message
"""

import json
import asyncio
import websockets

async def run(
        token_ids: list,
        on_new_data: function,
        url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    ):
    print(f"🚀 Iniciando Polymarket Streamer para {len(token_ids)} tokens...")
    
    while True:
        try:
            async with websockets.connect(url) as websocket:
                msg = {
                    "assets_ids": token_ids,
                    "type": "market"
                }
                await websocket.send(json.dumps(msg))
                print("📡 Inscrito nos canais de mercado.")

                async for message in websocket:
                    await on_new_data(message=message)
                    
        except asyncio.CancelledError:
            print("🛑 Streamer Poly cancelado.")
            break
        except Exception as e:
            print(f"⚠️ Erro na conexão WebSocket Poly: {e}")
            await asyncio.sleep(5) # Reconnect delay