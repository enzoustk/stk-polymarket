"""
Contrato de assinatura L2 (HMAC) — trava os gotchas que rejeitam ordem:
  * POLY_TIMESTAMP em SEGUNDOS (header), distinto do timestamp do struct (ms);
  * requestPath = "/order" puro;
  * body do HMAC byte-idêntico ao POSTado.
"""

import base64
import hashlib
import hmac

import py_clob_client_v2.headers.headers as H
from py_clob_client_v2.clob_types import RequestArgs
from py_clob_client_v2.endpoints import POST_ORDER
from py_clob_client_v2.signer import Signer
from py_clob_client_v2.signing.hmac import build_hmac_signature


def _manual(secret, ts, method, path, body):
    msg = (str(ts) + method + path + body).encode("utf-8")
    return base64.urlsafe_b64encode(
        hmac.new(base64.urlsafe_b64decode(secret), msg, hashlib.sha256).digest()
    ).decode("utf-8")


def test_build_hmac_matches_manual():
    secret = base64.urlsafe_b64encode(b"k" * 32).decode()
    got = build_hmac_signature(secret, "1700000000", "POST", "/order", '{"a":1}')
    assert got == _manual(secret, "1700000000", "POST", "/order", '{"a":1}')


def test_l2_header_timestamp_is_seconds_and_path_order(monkeypatch, pk, dummy_creds):
    signer = Signer(pk, 137)
    serialized = '{"order":{"x":1},"owner":"test-key","orderType":"GTC"}'

    class _FakeDateTime:
        @staticmethod
        def now():
            class _T:
                def timestamp(self):
                    return 1_700_000_000.987  # fração deve ser truncada p/ segundos

            return _T()

    monkeypatch.setattr(H, "datetime", _FakeDateTime)

    headers = H.create_level_2_headers(
        signer,
        dummy_creds,
        RequestArgs(
            method="POST",
            request_path=POST_ORDER,
            body=None,
            serialized_body=serialized,
        ),
    )

    # SEGUNDOS (10 dígitos), não ms
    assert headers["POLY_TIMESTAMP"] == "1700000000"
    # assinatura sobre ts(seg) + POST + /order + serialized
    assert headers["POLY_SIGNATURE"] == _manual(
        dummy_creds.api_secret, "1700000000", "POST", "/order", serialized
    )
    assert headers["POLY_API_KEY"] == dummy_creds.api_key
    assert headers["POLY_PASSPHRASE"] == dummy_creds.api_passphrase
