"""
Conexão e autenticação com a CLOB V2 da Polymarket (py-clob-client-v2).

A V1 (py-clob-client) foi descontinuada/arquivada pela Polymarket em 2026-05-25 e
não funciona mais contra a produção (CLOB V2 desde 2026-04-28). Este módulo usa o
sucessor oficial `py_clob_client_v2`.

`clob()` instancia o ClobClient (caminho "frio"/setup), deriva as credenciais L2 uma
única vez e as define no cliente. Para o envio de ordens de baixa latência use
`stk_polymarket.trading.fast.FastTrader`, que reusa estas credenciais.
"""

from py_clob_client_v2 import ApiCreds, ClobClient

HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon (int — a V1 passava "137" como string, o que quebrava a assinatura)


def derive_or_create_creds(client: ClobClient) -> ApiCreds:
    """
    Obtém as credenciais L2 (apiKey/secret/passphrase).

    Tenta derivar a chave determinística da carteira (idempotente); se a carteira
    ainda não tiver credenciais, cria novas.
    """
    try:
        return client.derive_api_key()
    except Exception:
        return client.create_api_key()


def clob(
    private_key: str,
    creds: ApiCreds | None = None,
    signature_type: int = 0,
    funder: str | None = None,
    host: str = HOST,
    chain_id: int = CHAIN_ID,
) -> ClobClient:
    """
    Cria um ClobClient V2 autenticado.

    Args:
        private_key: chave privada da carteira (EOA) que assina as ordens.
        creds: ApiCreds já existentes; se None, são derivadas/criadas uma vez.
        signature_type: 0=EOA (padrão), 1=POLY_PROXY, 2=POLY_GNOSIS_SAFE, 3=POLY_1271.
        funder: endereço que detém os fundos (proxy/safe). Para EOA deixe None.
    """
    if not private_key:
        raise ValueError("private_key ausente.")

    client = ClobClient(
        host,
        chain_id=chain_id,
        key=private_key,
        creds=creds,
        signature_type=signature_type,
        funder=funder,
    )

    if creds is None:
        creds = derive_or_create_creds(client)
    client.set_api_creds(creds)

    return client
