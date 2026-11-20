# ADR 0003 — Edge protocol: async batches over HTTPS

Status: accepted

Context: managed hosts forbid native binaries; game loop must never block;
network latency rules out cloud-side real-time blocking.

Decision: lightweight Lua/JS resource -> local queue -> signed HMAC batches
over HTTPS. Cheap rules may run at the edge; deep analysis runs in the cloud.

Consequences: works on any hosting; measurable overhead; no microsecond
blocking claims in marketing.
