# Hyperium IA

**GameShield** — economic integrity & forensic telemetry for private game
server economies (FiveM today; Rockstar Creator Platform / ROME next).

> "The day you get duped, don't wipe. Get the evidence."

## Why

Private game servers run real economies: VIP subscriptions, cosmetics,
in-game currency. One duplication exploit can destroy months of retention
in hours. GameShield records every economic event, flags anomalies and
produces evidence — a black box for game server economies.

## Repository layout

- `edge/gameshield/` — FiveM resource: economic flight recorder (Lua/JS, escrow-ready)
- `services/ingest/` — Rust (Axum): event ingestion, schema validation, HMAC auth
- `services/engine/` — Python (FastAPI): anomaly rules, alerts, evidence API
- `apps/web/` — dashboard (phase 2)
- `apps/kit/` — presentation kit: landing + reconstructed dupe demo (phase 2)
- `schemas/` — event contracts (source of truth)
- `docs/` — architecture, ADRs, roadmap

## Quickstart

```bash
make bootstrap   # install toolchains (Rust, uv, Node, Docker)
make up          # start local infra (Postgres + Redis)
make test        # run test suites
Status
v0.1 — scaffold. v1 scope: observe, alert, evidence. Explicitly NOT an
anti-cheat and no global ban network in v1.

License
Proprietary — Hyperium IA. All rights reserved.
