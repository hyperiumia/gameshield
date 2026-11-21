from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import EconomicEvent, to_canonical
from app.rules import evaluate

API_KEY = os.environ.get("GAMESHIELD_API_KEY", "dev-key")

app = FastAPI(
    title="GameShield Engine",
    version="0.2.0",
    description="Timeline, alerts and evidence API for game server economies.",
)


def require_key(x_gs_key: Annotated[Optional[str], Header()] = None) -> None:
    if x_gs_key != API_KEY:
        raise HTTPException(status_code=401, detail="bad api key")


SessionDep = Annotated[Session, Depends(get_session)]


def _legit(value: Optional[str]) -> frozenset[str]:
    return frozenset(s.strip() for s in (value or "").split(",") if s.strip())


def _events_for(
    session: Session,
    server_id: str,
    player: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = 5000,
) -> list[dict[str, Any]]:
    stmt = select(EconomicEvent).where(EconomicEvent.server_id == server_id)
    if player:
        stmt = stmt.where(EconomicEvent.actor_player_id == player)
    if since:
        stmt = stmt.where(EconomicEvent.occurred_at >= since)
    if until:
        stmt = stmt.where(EconomicEvent.occurred_at <= until)
    stmt = stmt.order_by(EconomicEvent.occurred_at).limit(limit)
    return [to_canonical(row) for row in session.scalars(stmt)]


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "gameshield-engine", "version": "0.2.0"}


@app.get("/v1/servers/{server_id}/events", dependencies=[Depends(require_key)])
def list_events(
    server_id: str,
    session: SessionDep,
    player: Optional[str] = None,
    type: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    events = _events_for(session, server_id, player, since, until, limit=limit)
    if type:
        events = [e for e in events if e.get("type") == type]
    return {"count": len(events), "events": events}


@app.get("/v1/servers/{server_id}/alerts", dependencies=[Depends(require_key)])
def list_alerts(
    server_id: str,
    session: SessionDep,
    player: Optional[str] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
    legit_sources: Optional[str] = Query(
        None, description="comma-separated resource names considered legitimate"
    ),
) -> dict:
    events = _events_for(session, server_id, player, since, until)
    alerts = [a.to_dict() for a in evaluate(events, legit_resources=_legit(legit_sources))]
    return {"count": len(alerts), "alerts": alerts}


class EvidenceRequest(BaseModel):
    player_id: Optional[str] = None
    since: Optional[datetime] = None
    until: Optional[datetime] = None
    legit_sources: Optional[list[str]] = None


@app.post("/v1/servers/{server_id}/evidence", dependencies=[Depends(require_key)])
def evidence_report(
    server_id: str,
    session: SessionDep,
    body: EvidenceRequest | None = None,
) -> dict:
    body = body or EvidenceRequest()
    events = _events_for(session, server_id, body.player_id, body.since, body.until)
    alerts = [
        a.to_dict()
        for a in evaluate(events, legit_resources=frozenset(body.legit_sources or []))
    ]
    rules_triggered = sorted({a["rule"] for a in alerts})
    stages = sorted({a["stage"] for a in alerts})
    return {
        "report": {
            "server_id": server_id,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "player_id": body.player_id,
            "window": {"since": body.since, "until": body.until},
        },
        "summary": {
            "total_events": len(events),
            "alert_count": len(alerts),
            "rules_triggered": rules_triggered,
            "stages_present": stages,
        },
        "alerts": alerts,
        "events": events,
    }
