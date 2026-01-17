"""
Rode o auth para autorizar a wallet a fazer trading e gerar as keys
"""


from py_clob_client.client import ClobClient

def auth(
    PRIVATE_KEY,
    SIGNATURE_TYPE,
    FUNDER
    ):
    
    HOST = "https://clob.polymarket.com"
    CHAIN_ID = "137"


    if not PRIVATE_KEY:
        raise ValueError("PKey missing.")

    # Inicialização do cliente – decidir se proxy ou EOA diretamente
    if SIGNATURE_TYPE is not None and FUNDER:
        # modo proxy
        client = ClobClient(
            HOST,
            key=PRIVATE_KEY,
            chain_id=CHAIN_ID,
            signature_type=int(SIGNATURE_TYPE),
            funder=FUNDER
        )
    else:
        # modo EOA direto (carteira que você controla a chave privada)
        client = ClobClient(
            HOST,
            key=PRIVATE_KEY,
            chain_id=CHAIN_ID
        )

    # Derivar ou criar credenciais de API (L1 → credenciais)
    api_creds = client.create_or_derive_api_creds()
    print("=== CRIADAS/DERIVADAS CREDENCIAIS API ===")
    print("API Key      :", api_creds.api_key)
    print("API Secret   :", api_creds.api_secret)
    print("API Passphrase:", api_creds.api_passphrase)

    # Salve essas 3 em seu .env manualmente ou criptografado
    # Vamos definir no cliente para usar nas requisições
    client.set_api_creds(api_creds)

    # Teste simples: obter server time ou endpoint read-only autenticado
    print("=== TESTE L2 – chamada autenticada ===")
    server_time = client.get_server_time()
    print("Server time:", server_time)
