"""Read model over the `economic_events` table written by services/ingest."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, BigInteger, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EconomicEvent(Base):
    __tablename__ = "economic_events"

    # BigInteger does NOT autoincrement in SQLite (used by tests);
    # the variant keeps BIGINT in Postgres and INTEGER in SQLite.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    event_id: Mapped[str] = mapped_column(String(36), unique=True)
    server_id: Mapped[str] = mapped_column(String(64), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    type: Mapped[str] = mapped_column(String(32))
    actor_player_id: Mapped[str] = mapped_column(String(128), index=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(128))
    actor_role: Mapped[str] = mapped_column(String(16), default="player")
    currency: Mapped[Optional[str]] = mapped_column(String(16))
    amount: Mapped[Optional[float]] = mapped_column(Float)
    balance_after: Mapped[Optional[float]] = mapped_column(Float)
    subject_kind: Mapped[Optional[str]] = mapped_column(String(32))
    subject_sku: Mapped[Optional[str]] = mapped_column(String(128))
    subject_quantity: Mapped[Optional[float]] = mapped_column(Float)
    source_resource: Mapped[str] = mapped_column(String(128))
    source_event: Mapped[Optional[str]] = mapped_column(String(128))
    counterparty: Mapped[Optional[str]] = mapped_column(String(128))
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def to_canonical(row: EconomicEvent) -> dict[str, Any]:
    """Shape matches schemas/economic-event.v1.schema.json (rules.py input)."""
    if isinstance(row.payload, dict) and row.payload.get("schema_version"):
        return row.payload
    event: dict[str, Any] = {
        "schema_version": "1",
        "event_id": row.event_id,
        "server_id": row.server_id,
        "occurred_at": _iso(row.occurred_at),
        "type": row.type,
        "actor": {
            "player_id": row.actor_player_id,
            "display_name": row.actor_name,
            "role": row.actor_role,
        },
        "source": {
            "resource": row.source_resource,
            "event_name": row.source_event,
            "counterparty_id": row.counterparty,
        },
    }
    if row.currency or row.amount is not None or row.balance_after is not None:
        event["economy"] = {
            "currency": row.currency,
            "amount": row.amount,
            "balance_after": row.balance_after,
        }
    if row.subject_kind or row.subject_sku or row.subject_quantity is not None:
        event["subject"] = {
            "kind": row.subject_kind,
            "sku": row.subject_sku,
            "quantity": row.subject_quantity,
        }
    return event


def from_canonical(data: dict[str, Any]) -> EconomicEvent:
    """Build a row from a canonical event (used by tests/seed tools)."""
    actor = data.get("actor") or {}
    economy = data.get("economy") or {}
    subject = data.get("subject") or {}
    source = data.get("source") or {}
    return EconomicEvent(
        event_id=str(data["event_id"]),
        server_id=data["server_id"],
        occurred_at=_parse(data["occurred_at"]),
        type=data["type"],
        actor_player_id=actor.get("player_id", ""),
        actor_name=actor.get("display_name"),
        actor_role=actor.get("role") or "player",
        currency=economy.get("currency"),
        amount=economy.get("amount"),
        balance_after=economy.get("balance_after"),
        subject_kind=subject.get("kind"),
        subject_sku=subject.get("sku"),
        subject_quantity=subject.get("quantity"),
        source_resource=source.get("resource") or "unknown",
        source_event=source.get("event_name"),
        counterparty=source.get("counterparty_id"),
        payload=data,
        received_at=datetime.now(timezone.utc),
    )
