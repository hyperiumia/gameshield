from fastapi import FastAPI

from app.rules import evaluate

app = FastAPI(
    title="GameShield Engine",
    version="0.2.0",
    description="Anomaly rules, alerts and evidence API for game server economies.",
)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "gameshield-engine", "version": "0.2.0"}


@app.post("/v1/alerts/evaluate")
def evaluate_alerts(payload: list[dict]) -> dict:
    """Run all v1 rules over an event list (same shape as schemas/economic-event.v1)."""
    alerts = [a.to_dict() for a in evaluate(payload)]
    return {"count": len(alerts), "alerts": alerts}
