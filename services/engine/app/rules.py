"""Explainable anomaly rules for game-server economies (v1).

Escalation model:
  anomaly    -> shape worth noting; strong innocent explanations exist
  suspicion  -> pattern strongly tied to exploitation; staff review required
  evidence   -> confirmed only after human review (nothing is auto-evidence)

An anomaly is not proof of an exploit: admin rewards, event payouts and
legitimate scripts can look unusual. Alerts ask for review, never accuse.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

Event = dict[str, Any]

STAGE_ANOMALY = "anomaly"
STAGE_SUSPICION = "suspicion"

REVIEW_NOTE = " Requiere revision del staff: la anomalia no confirma un exploit."


@dataclass
class Alert:
    rule: str
    severity: str  # "low" | "medium" | "high"
    stage: str  # STAGE_ANOMALY | STAGE_SUSPICION
    player_id: str
    summary: str
    event_ids: list[str] = field(default_factory=list)
    explain: str = ""
    review_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _ts(ev: Event) -> float:
    raw = ev.get("occurred_at") or "1970-01-01T00:00:00Z"
    return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()


def _actor(ev: Event) -> str:
    return (ev.get("actor") or {}).get("player_id") or ""


def _role(ev: Event) -> str:
    return (ev.get("actor") or {}).get("role") or "player"


def _amount(ev: Event) -> float:
    return float((ev.get("economy") or {}).get("amount") or 0)


def _resource(ev: Event) -> str:
    return (ev.get("source") or {}).get("resource") or "unknown"


def money_without_origin(
    events: list[Event],
    *,
    threshold: float = 100_000.0,
    window_seconds: int = 600,
    legit_resources: frozenset[str] = frozenset(),
) -> list[Alert]:
    """Large credits to a player with no sale/trade/incoming transfer to justify them."""
    alerts: list[Alert] = []
    ordered = sorted(events, key=_ts)

    for i, ev in enumerate(ordered):
        if ev.get("type") != "money.credit":
            continue
        if _role(ev) != "player":
            continue
        if _resource(ev) in legit_resources:
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
                    stage=STAGE_SUSPICION,
                    player_id=player,
                    summary=f"{player} recibio {amount:,.0f} sin origen economico",
                    event_ids=[ev.get("event_id", "")],
                    explain=(
                        f"Ninguna venta/trueque o transferencia entrante de {player} en los "
                        f"{window_seconds}s previos justifica un credito de {amount:,.0f}"
                        f" (recurso '{_resource(ev)}')." + REVIEW_NOTE
                    ),
                )
            )
    return alerts


def cascade_dupes(
    events: list[Event],
    *,
    min_count: int = 3,
    window_seconds: int = 30,
    legit_resources: frozenset[str] = frozenset(),
) -> list[Alert]:
    """Identical grants (same item/qty/source) repeated to one actor in seconds."""
    alerts: list[Alert] = []
    groups: dict[tuple, list[Event]] = {}

    for ev in events:
        if ev.get("type") not in ("item.grant", "vehicle.grant"):
            continue
        if _role(ev) != "player" or _resource(ev) in legit_resources:
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
                    stage=STAGE_SUSPICION,
                    player_id=key[0],
                    summary=f"{len(evs)}x concesiones identicas de '{key[2]}' en {window_seconds}s",
                    event_ids=[e.get("event_id", "") for e in evs],
                    explain=(
                        f"La misma concesion ({key[1]} de '{key[2]}' qty {key[3]}) se repite "
                        f"{len(evs)} veces en {window_seconds}s con el mismo origen "
                        f"('{key[4]}') por {key[0]} — patron tipico de duplicacion." + REVIEW_NOTE
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
                    stage=STAGE_ANOMALY,
                    player_id=_actor(origin),
                    summary=f"cadena de transferencias de profundidad {len(chain)} desde {_actor(origin)}",
                    event_ids=list(ids),
                    explain=(
                        f"{len(chain)} saltos encadenados de money.transfer moviendo casi el "
                        f"mismo monto (tol {amount_tolerance:.0%}) con menos de {window_seconds}s "
                        "por salto — patron compatible con lavado o embudo coordinado, pero "
                        "tambien con regalos entre jugadores." + REVIEW_NOTE
                    ),
                )
            )
    return alerts


def evaluate(
    events: list[Event],
    *,
    legit_resources: frozenset[str] = frozenset(),
) -> list[Alert]:
    return (
        money_without_origin(events, legit_resources=legit_resources)
        + cascade_dupes(events, legit_resources=legit_resources)
        + chained_transfers(events)
    )
