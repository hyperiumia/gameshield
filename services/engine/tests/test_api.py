HEADERS = {"X-GS-Key": "dev-key"}


def test_auth_required(client):
    assert client.get("/v1/servers/demo-rp-01/events").status_code == 401
    assert (
        client.get("/v1/servers/demo-rp-01/events", headers={"X-GS-Key": "nope"}).status_code
        == 401
    )


def test_timeline_filter_by_player(client):
    res = client.get(
        "/v1/servers/demo-rp-01/events",
        params={"player": "p-042", "limit": 500},
        headers=HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 7
    assert all(e["actor"]["player_id"] == "p-042" for e in data["events"])


def test_timeline_filter_by_type(client):
    res = client.get(
        "/v1/servers/demo-rp-01/events",
        params={"type": "item.grant"},
        headers=HEADERS,
    )
    assert res.json()["count"] == 5


def test_alerts_integration(client):
    res = client.get("/v1/servers/demo-rp-01/alerts", headers=HEADERS)
    data = res.json()
    assert data["count"] == 3
    assert {a["rule"] for a in data["alerts"]} == {
        "money_without_origin",
        "cascade_dupes",
        "chained_transfers",
    }


def test_evidence_report(client):
    res = client.post(
        "/v1/servers/demo-rp-01/evidence",
        json={"player_id": "p-042"},
        headers=HEADERS,
    )
    data = res.json()
    assert data["summary"]["total_events"] == 7
    assert data["summary"]["alert_count"] >= 2
    assert "money_without_origin" in data["summary"]["rules_triggered"]
    assert all(e["actor"]["player_id"] == "p-042" for e in data["events"])
