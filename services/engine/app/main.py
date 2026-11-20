from fastapi import FastAPI

app = FastAPI(
    title="GameShield Engine",
    version="0.1.0",
    description="Anomaly rules, alerts and evidence API for game server economies.",
)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok", "service": "gameshield-engine", "version": "0.1.0"}
