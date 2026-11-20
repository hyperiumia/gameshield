# gameshield-ingest

Event ingestion service (Rust · Axum).

Responsibilities:
- HMAC-SHA256 auth of signed batches from edge agents
- JSON Schema validation against `schemas/economic-event.v1.schema.json`
- Persist events to PostgreSQL

Endpoints (v1 target):
- `POST /v1/events` — batch ingest
- `GET  /healthz` — liveness
