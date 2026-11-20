# GameShield — Architecture

Status: v0.1 · scaffold · 2026-11

## 1. Purpose

GameShield is the economic integrity layer for private game server
economies. It is a flight recorder + anomaly detector + evidence engine.
FiveM today; Rockstar Creator Platform / ROME when it opens.

## 2. Non-goals (v1)

- NOT an anti-cheat. Rockstar protects generic cheats; we protect the
  business logic of each community's economy.
- No real-time blocking promises. v1 observes, alerts, proves.
- No shared/global ban network (phase 4, needs privacy framework first).

## 3. Components

| Component | Tech | Responsibility |
|---|---|---|
| edge/gameshield | Lua/JS FiveM resource | Hook economic events, local queue, async batch upload. Zero native binaries (managed hosts). |
| services/ingest | Rust · Axum | HMAC auth, schema validation, persist events. High throughput, low memory. |
| services/engine | Python · FastAPI | Anomaly rules, alerts, timeline queries, evidence export. |
| apps/web | React + Vite (phase 2) | Dashboard for server owners. |
| apps/kit | Static + demo (phase 2) | Presentation kit: landing + reconstructed dupe incident. |

## 4. Data flow

edge (queue) --HTTPS batch + HMAC-SHA256--> ingest --> PostgreSQL
engine reads PostgreSQL, runs rules, writes alerts
web/kit consume engine REST API

Redis: rate limiting + future job queues.

## 5. Trust & privacy

- Per-server API keys; batches signed with HMAC-SHA256 (replay window 5 min).
- Server owner is data controller; GameShield is data processor (GDPR/LGPD).
- Retention configurable per server; EU region pinning planned (phase 2).
- Player identifiers hashed at rest in shared views.

## 6. Event contract

`schemas/economic-event.v1.schema.json` is the single source of truth.
Any change is additive + versioned. Breaking changes create v2.
