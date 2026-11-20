import json
from pathlib import Path

from app.rules import cascade_dupes, chained_transfers, money_without_origin

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
    for alert in money_without_origin(FIXTURE) + cascade_dupes(FIXTURE):
        assert len(alert.explain) > 20
