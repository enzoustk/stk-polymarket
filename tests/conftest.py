import base64
import random
import time

import pytest
from eth_account import Account
from py_clob_client_v2 import ApiCreds


@pytest.fixture
def pk():
    """Chave privada efêmera (não toca rede; só assina localmente)."""
    return Account.create().key.hex()


@pytest.fixture
def frozen(monkeypatch):
    """
    Congela salt + timestamp para o SDK e o FastTrader produzirem ordens idênticas.

    generate_order_salt() = int(random.random() * (time.time_ns()//1_000_000)) e o
    timestamp da ordem = time.time_ns()//1_000_000 — patchar ambos torna tudo determinístico.
    """
    monkeypatch.setattr(time, "time_ns", lambda: 1_700_000_000_123_000_000)
    monkeypatch.setattr(random, "random", lambda: 0.42)


@pytest.fixture
def dummy_creds():
    """ApiCreds com secret base64-urlsafe válido (decodável pelo HMAC)."""
    secret = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode()
    return ApiCreds(api_key="test-key", api_secret=secret, api_passphrase="test-pass")
