"""
Autorização da carteira e geração das credenciais de API (CLOB V2).

Rode uma vez para derivar/criar as credenciais L2 (apiKey/secret/passphrase) a
partir da sua chave privada. Guarde-as com segurança (ex.: .env) e reutilize via
`clob(..., creds=...)` para evitar a derivação a cada start.
"""

from py_clob_client_v2 import ApiCreds

from stk_polymarket.connection.connect import (
    CHAIN_ID,
    HOST,
    clob,
    derive_or_create_creds,
)


def auth(
    private_key: str,
    signature_type: int = 0,
    funder: str | None = None,
) -> ApiCreds:
    """
    Deriva/cria as credenciais L2 e faz um teste autenticado (get_ok).

    Args:
        private_key: chave privada (EOA padrão).
        signature_type: 0=EOA, 1=POLY_PROXY, 2=POLY_GNOSIS_SAFE, 3=POLY_1271.
        funder: endereço dos fundos para proxy/safe; None para EOA.

    Returns:
        ApiCreds(api_key, api_secret, api_passphrase).
    """
    if not private_key:
        raise ValueError("private_key ausente.")

    client = clob(
        private_key=private_key,
        signature_type=signature_type,
        funder=funder,
        host=HOST,
        chain_id=CHAIN_ID,
    )
    creds = client.creds

    print("=== CREDENCIAIS API (CLOB V2) ===")
    print("API Key       :", creds.api_key)
    print("API Secret    :", creds.api_secret)
    print("API Passphrase:", creds.api_passphrase)
    print("Guarde-as com segurança (ex.: .env) e reutilize via clob(creds=...).")

    # Teste autenticado simples (read-only)
    print("=== TESTE: get_ok ===")
    print("get_ok:", client.get_ok())

    return creds


__all__ = ["auth", "derive_or_create_creds"]
