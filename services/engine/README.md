# gameshield-engine

Business logic service (Python · FastAPI).

Responsibilities:
- Anomaly rules (explainable, v1): money without origin, cascade dupes,
  chained transfers, coordinated accounts
- Alerts + timeline queries + evidence export
- REST API consumed by apps/web and apps/kit

Endpoints (v1 target):
- `GET  /v1/servers/{id}/timeline` — player/item/transaction timelines
- `GET  /v1/servers/{id}/alerts`  — anomaly alerts
- `POST /v1/servers/{id}/evidence` — incident evidence report
- `GET  /healthz`
