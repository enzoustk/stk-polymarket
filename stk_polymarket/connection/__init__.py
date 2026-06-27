"""Conexão e autenticação com a CLOB V2 da Polymarket."""

from stk_polymarket.connection.auth import auth, derive_or_create_creds
from stk_polymarket.connection.connect import CHAIN_ID, HOST, clob

__all__ = ["clob", "auth", "derive_or_create_creds", "HOST", "CHAIN_ID"]
