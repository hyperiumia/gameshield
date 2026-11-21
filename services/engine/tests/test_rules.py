import json
from pathlib import Path

from app.rules import (
    cascade_dupes,
    chained_transfers,
    evaluate,
    money_without_origin,
)

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "dupe_incident.json").read_text()
)


def test_money_without_origin_flags_unexplained_credit():
    alerts = money_without_origin(FIXTURE)
    assert [a.player_id for a in alerts] == ["p-042"]


def test_legit_credit_is_not_flagged():
    alerts = money_without_origin(FIXTURE)
    assert all(a.player_id != "p-007" for a in alerts)


def test_cascade_dupes_flags_grant_spam():
    alerts = cascade_dupes(FIXTURE)
    assert len(alerts) == 1
    assert alerts[0].player_id == "p-042"
    assert "SULTAN_RS" in alerts[0].summary
    assert len(alerts[0].event_ids) == 5


def test_chained_transfers_flags_laundering_chain():
    alerts = chained_transfers(FIXTURE)
    assert any(a.player_id == "p-042" for a in alerts)
    chain = next(a for a in alerts if a.player_id == "p-042")
    assert len(chain.event_ids) == 3


def test_alerts_are_explainable():
    for alert in evaluate(FIXTURE):
        assert len(alert.explain) > 20


def test_stages_are_escalated():
    by_rule = {a.rule: a.stage for a in evaluate(FIXTURE)}
    assert by_rule["chained_transfers"] == "anomaly"
    assert by_rule["money_without_origin"] == "suspicion"
    assert by_rule["cascade_dupes"] == "suspicion"


def test_every_alert_requires_human_review():
    for a in evaluate(FIXTURE):
        assert a.review_required is True
        assert "revision del staff" in a.explain


def test_staff_credit_is_not_flagged():
    ev = {
        "schema_version": "1",
        "event_id": "33333333-3333-4333-8333-333333333301",
        "server_id": "s1",
        "occurred_at": "2026-11-20T10:00:00Z",
        "type": "money.credit",
        "actor": {"player_id": "admin-1", "role": "staff"},
        "economy": {"currency": "USD", "amount": 500000.0},
        "source": {"resource": "admin-menu", "event_name": "give"},
    }
    assert money_without_origin([ev]) == []


def test_known_legit_source_suppresses_alert():
    assert (
        money_without_origin(FIXTURE, legit_resources=frozenset({"unknown"})) == []
    )
