import hashlib
import hmac
import time
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException, Request

SECRET = "shared-webhook-secret-for-testing"
DOWNSTREAM_URL = "https://example.invalid/relay"
MAX_RETRIES = 3

app = FastAPI()


def verify_signature(body: bytes, signature: Optional[str]) -> bool:
    if not signature:
        return False
    expected = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def relay_with_backoff(payload: dict, post=requests.post) -> bool:
    delay = 0.01
    for _ in range(MAX_RETRIES):
        try:
            resp = post(DOWNSTREAM_URL, json=payload, timeout=2)
            if resp.status_code < 300:
                return True
        except requests.RequestException:
            pass
        time.sleep(delay)
        delay *= 2
    return False


@app.post("/events")
async def receive_event(request: Request, x_signature: Optional[str] = Header(None)):
    body = await request.body()
    if not verify_signature(body, x_signature):
        raise HTTPException(status_code=401, detail="invalid signature")
    payload = await request.json()
    if not relay_with_backoff(payload):
        raise HTTPException(status_code=502, detail="relay failed after retries")
    return {"status": "relayed"}
