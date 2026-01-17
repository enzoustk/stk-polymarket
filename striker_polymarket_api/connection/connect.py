from py_clob_client.client import ClobClient

def clob(
    funder: str | None,
    private_key: str,
    chain_id: int = 137,
    host: str = "https://clob.polymarket.com",
    ) -> ClobClient:
    

    if funder:
        client = ClobClient(
            host,
            key=private_key,
            chain_id=chain_id,
            signature_type=2,
            funder=funder
        )
    else:
        client = ClobClient(
            host,
            key=private_key,
            chain_id=chain_id
        )
    
    api_creds = client.create_or_derive_api_creds()
    client.set_api_creds(api_creds)
    
    return client
