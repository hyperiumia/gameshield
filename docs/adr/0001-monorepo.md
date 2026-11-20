# ADR 0001 — Monorepo

Status: accepted

Context: edge agent, ingestion service, engine, web apps and event
schemas evolve together and must stay version-compatible.

Decision: single repository `hyperiumia` with clear top-level boundaries
(edge/ services/ apps/ schemas/ ops/ docs/).

Consequences: atomic cross-component changes; one CI; simple onboarding.
