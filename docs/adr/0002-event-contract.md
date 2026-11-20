# ADR 0002 — Event contract as JSON Schema

Status: accepted

Context: edge agents in the wild and cloud services must agree on the
economic event format; FiveM resources are Lua/JS (JSON-native).

Decision: `schemas/economic-event.v1.schema.json` is the source of truth.
Validated at ingest; additive evolution only within v1.

Consequences: language-agnostic contract; schema CI check; predictable
compatibility for third-party integrations later.
