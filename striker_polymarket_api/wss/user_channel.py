import json
import time
import hmac
import base64
import hashlib
import asyncio
import websockets
from py_clob_client.client import ClobClient

def get_ws_auth_headers(
    client: ClobClient
    ) -> dict:
    creds = client.creds
    timestamp = str(int(time.time()))
    message = timestamp
    
    signature = base64.b64encode(
        hmac.new(
            creds.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
    ).decode('utf-8')

    return {
        "Clob-Api-Key": creds.api_key,
        "Clob-Timestamp": timestamp,
        "Clob-Signature": signature,
        "Clob-Passphrase": creds.api_passphrase,
    }


async def keep_alive(ws):
    """
    Envia um ping a cada 20 segundos para manter a conexão ativa.
    """
    try:
        while True:
            await asyncio.sleep(20)
            if ws.open:
                await ws.ping()
            else:
                break
    
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Keep-alive error: {e}")


async def start(
    client: ClobClient,
    on_new_data: function | None = None,
    verbose: bool = False,
    url: str = "wss://ws-subscriptions-clob.polymarket.com/ws/user"
    ):
    # A função on_new_data deve ter um arg message!
    
    while True:
        headers = get_ws_auth_headers(client=client)
        keep_alive_task = None

        try:
            async with websockets.connect(
                url,
                extra_headers=headers,
                ping_interval=None
                ) as ws:
                
                # --- SUBSCRIBE ---
                creds = client.creds
                subscribe_msg = {
                    "type": "USER",
                    "markets": [],
                    "auth": {
                        "apiKey": creds.api_key,
                        "secret": creds.api_secret,
                        "passphrase": creds.api_passphrase
                    }
                }
                await ws.send(json.dumps(subscribe_msg))
                
                keep_alive_task = asyncio.create_task(keep_alive(ws))

                async for message in ws:                    
                    if verbose:
                        print(message)
                    
                    try:
                        if on_new_data:
                            on_new_data(message=message)
                    except Exception as e:
                        print(f'Error processing wss update: {e}')
                
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError) as e:
            print(f"Lost Connection: {e}")
            print("Reconnecting in 5 seconds...")
            
        except Exception as e:
            print(f"Uncaught error: {e}")
            print("Reconnecting in 5 seconds...")

        finally:
            if keep_alive_task:
                keep_alive_task.cancel()
                try:
                    await keep_alive_task
                except asyncio.CancelledError:
                    pass
            
            await asyncio.sleep(5)
