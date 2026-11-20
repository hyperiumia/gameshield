"""Sends one signed batch to the ingest service. Stdlib only."""
import hashlib
import hmac
import json
import os
import time
import urllib.request
import uuid

API = os.environ.get("GAMESHIELD_API_KEY", "dev-key")
SECRET = os.environ.get("GAMESHIELD_HMAC_SECRET", "dev-secret")
URL = os.environ.get("GAMESHIELD_INGEST_URL", "http://localhost:8080/v1/events")

now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def event(t, player, amount=None, sku=None):
    e = {
        "schema_version": "1",
        "event_id": str(uuid.uuid4()),
        "server_id": "e2e-demo-01",
        "occurred_at": now,
        "type": t,
        "actor": {"player_id": player, "display_name": "e2e", "role": "player"},
        "source": {"resource": "gameshield-e2e", "event_name": "test"},
    }
    if amount is not None:
        e["economy"] = {"currency": "USD", "amount": amount}
    if sku:
        e["subject"] = {"kind": "item", "sku": sku, "quantity": 1}
    return e


batch = {
    "sent_at": now,
    "events": [
        event("money.credit", "p-e2e-01", 250000.0),
        event("item.grant", "p-e2e-01", sku="SULTAN_RS"),
    ],
}

body = json.dumps(batch, separators=(",", ":"))
ts = str(int(time.time()))
sig = hmac.new(SECRET.encode(), f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()

req = urllib.request.Request(
    URL,
    data=body.encode(),
    method="POST",
    headers={
        "content-type": "application/json",
        "x-gs-key": API,
        "x-gs-timestamp": ts,
        "x-gs-signature": sig,
    },
)

with urllib.request.urlopen(req) as r:
    data = json.loads(r.read().decode())

assert data["accepted"] == 2, data
assert data["rejected"] == [], data
print("send_test_batch: OK —", data)
