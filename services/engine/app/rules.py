"""Explainable anomaly rules for game-server economies (v1).

Pure functions: events in, alerts out. No ML, no I/O. Every alert
carries an `explain` string a server owner can read.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

Event = dict[str, Any]


@dataclass
class Alert:
    rule: str
    severity: str  # "low" | "medium" | "high"
    player_id: str
    summary: str
    event_ids: list[str] = field(default_factory=list)
    explain: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ts(ev: Event) -> float:
    raw = ev.get("occurred_at") or "1970-01-01T00:00:00Z"
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()


def _actor(ev: Event) -> str:
    return (ev.get("actor") or {}).get("player_id") or ""


def _amount(ev: Event) -> float:
    return float((ev.get("economy") or {}).get("amount") or 0)


def money_without_origin(
    events: list[Event], *, threshold: float = 100_000.0, window_seconds: int = 600
) -> list[Alert]:
    """Large credits to a player with no sale/trade/incoming transfer to justify them."""
    alerts: list[Alert] = []
    ordered = sorted(events, key=_ts)

    for i, ev in enumerate(ordered):
        if ev.get("type") != "money.credit":
            continue
        if (ev.get("actor") or {}).get("role", "player") != "player":
            continue
        amount = _amount(ev)
        player = _actor(ev)
        if amount < threshold:
            continue

        t0 = _ts(ev)
        legit = False
        for prev in reversed(ordered[:i]):
            if t0 - _ts(prev) > window_seconds:
                break
            ptype = prev.get("type")
            if ptype in ("sale", "trade", "purchase") and _actor(prev) == player:
                legit = True
                break
            if ptype == "money.transfer" and (prev.get("source") or {}).get("counterparty_id") == player:
                legit = True
                break

        if not legit:
            alerts.append(
                Alert(
                    rule="money_without_origin",
                    severity="high",
                    player_id=player,
                    summary=f"{player} received {amount:,.0f} with no economic origin",
                    event_ids=[ev.get("event_id", "")],
                    explain=(
                        f"No sale/trade or incoming transfer for {player} in the previous "
                        f"{window_seconds}s justifies a credit of {amount:,.0f}."
                    ),
                )
            )
    return alerts


def cascade_dupes(
    events: list[Event], *, min_count: int = 3, window_seconds: int = 30
) -> list[Alert]:
    """Identical grants (same item/qty/source) repeated to one actor in seconds."""
    alerts: list[Alert] = []
    groups: dict[tuple, list[Event]] = {}

    for ev in events:
        if ev.get("type") not in ("item.grant", "vehicle.grant"):
            continue
        subj = ev.get("subject") or {}
        key = (
            _actor(ev),
            ev.get("type"),
            subj.get("sku"),
            subj.get("quantity"),
            (ev.get("source") or {}).get("event_name"),
        )
        groups.setdefault(key, []).append(ev)

    for key, evs in groups.items():
        evs = sorted(evs, key=_ts)
        if len(evs) >= min_count and (_ts(evs[-1]) - _ts(evs[0])) <= window_seconds:
            alerts.append(
                Alert(
                    rule="cascade_dupes",
                    severity="high",
                    player_id=key[0],
                    summary=f"{len(evs)}x identical '{key[2]}' grants in {window_seconds}s",
                    event_ids=[e.get("event_id", "") for e in evs],
                    explain=(
                        f"Same grant ({key[1]} of '{key[2]}' qty {key[3]}) repeated {len(evs)} times "
                        f"within {window_seconds}s by {key[0]} via the same source event "
                        f"'{key[4]}' — signature of a duplication exploit."
                    ),
                )
            )
    return alerts


def chained_transfers(
    events: list[Event],
    *,
    min_depth: int = 3,
    window_seconds: int = 120,
    amount_tolerance: float = 0.01,
) -> list[Alert]:
    """A -> B -> C -> D moving nearly the same amount in minutes (laundering shape)."""
    transfers = [e for e in events if e.get("type") == "money.transfer"]
    by_sender: dict[str, list[Event]] = {}
    for e in transfers:
        by_sender.setdefault(_actor(e), []).append(e)

    def next_hop(prev: Event) -> Event | None:
        t0 = _ts(prev)
        amount = _amount(prev)
        receiver = (prev.get("source") or {}).get("counterparty_id")
        if amount <= 0 or not receiver:
            return None
        for cand in by_sender.get(receiver, []):
            dt = _ts(cand) - t0
            if 0 <= dt <= window_seconds and abs(_amount(cand) - amount) / amount <= amount_tolerance:
                return cand
        return None

    alerts: list[Alert] = []
    seen: set[tuple] = set()

    for origin in transfers:
        chain = [origin]
        while True:
            nxt = next_hop(chain[-1])
            if nxt is None or any(nxt.get("event_id") == c.get("event_id") for c in chain):
                break
            chain.append(nxt)
        if len(chain) >= min_depth:
            ids = tuple(c.get("event_id", "") for c in chain)
            if ids in seen:
                continue
            seen.add(ids)
            alerts.append(
                Alert(
                    rule="chained_transfers",
                    severity="medium",
                    player_id=_actor(origin),
                    summary=f"transfer chain of depth {len(chain)} starting at {_actor(origin)}",
                    event_ids=list(ids),
                    explain=(
                        f"{len(chain)} chained money.transfer hops moving nearly the same amount "
                        f"(within {amount_tolerance:.0%}) within {window_seconds}s per hop — "
                        "possible laundering or coordinated funneling."
                    ),
                )
            )
    return alerts


def evaluate(events: list[Event]) -> list[Alert]:
    return money_without_origin(events) + cascade_dupes(events) + chained_transfers(events)
