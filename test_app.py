import hashlib
import hmac
import json

from fastapi.testclient import TestClient

import app as app_module
from app import SECRET, app, relay_with_backoff, verify_signature

client = TestClient(app)


def sign(body: bytes) -> str:
    return hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_verify_signature_valid():
    body = b'{"a":1}'
    assert verify_signature(body, sign(body)) is True


def test_verify_signature_invalid():
    assert verify_signature(b'{"a":1}', "deadbeef") is False


def test_verify_signature_missing():
    assert verify_signature(b"{}", None) is False


def test_endpoint_rejects_bad_signature():
    r = client.post("/events", content=b'{"a":1}', headers={"x-signature": "bad"})
    assert r.status_code == 401


def test_endpoint_accepts_good_signature(monkeypatch):
    monkeypatch.setattr(app_module, "relay_with_backoff", lambda payload: True)
    body = json.dumps({"a": 1}).encode()
    r = client.post("/events", content=body, headers={"x-signature": sign(body)})
    assert r.status_code == 200


def test_endpoint_returns_502_after_relay_failure(monkeypatch):
    monkeypatch.setattr(app_module, "relay_with_backoff", lambda payload: False)
    body = json.dumps({"a": 1}).encode()
    r = client.post("/events", content=body, headers={"x-signature": sign(body)})
    assert r.status_code == 502


def test_relay_retries_then_succeeds():
    calls = {"n": 0}

    class FakeResp:
        status_code = 200

    def fake_post(url, json=None, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise __import__("requests").exceptions.ConnectionError()
        return FakeResp()

    assert relay_with_backoff({"a": 1}, post=fake_post) is True
    assert calls["n"] == 3


def test_relay_gives_up_after_max_retries():
    def always_fail(url, json=None, timeout=None):
        raise __import__("requests").exceptions.ConnectionError()

    assert relay_with_backoff({"a": 1}, post=always_fail) is False
