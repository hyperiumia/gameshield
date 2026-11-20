# gameshield (FiveM edge agent)

Economic flight recorder. A single lightweight resource that hooks
economic events, queues them locally and uploads signed batches.

Constraints:
- Lua/JS only — no native binaries (managed hosts forbid them)
- Tebex Escrow-ready distribution
- Overhead budget: < 1ms CPU per tick, fixed memory, drop-oldest queue

Phase 1 scope: record + upload. No blocking, no anti-cheat claims.
