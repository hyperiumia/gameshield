#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

export GAMESHIELD_API_KEY="${GAMESHIELD_API_KEY:-dev-key}"
export GAMESHIELD_HMAC_SECRET="${GAMESHIELD_HMAC_SECRET:-dev-secret}"
export DATABASE_URL="${DATABASE_URL:-postgres://gameshield:gameshield@localhost:5432/gameshield}"

DC="docker compose"
$DC ps >/dev/null 2>&1 || DC="sudo docker compose"

echo "==> 1/5 postgres up"
$DC up -d postgres

echo "==> 2/5 build ingest"
(cd services/ingest && cargo build)

echo "==> 3/5 start ingest"
(cd services/ingest && ./target/debug/gameshield-ingest) &
INGEST_PID=$!
trap 'kill "$INGEST_PID" 2>/dev/null || true' EXIT

for i in $(seq 1 60); do
    curl -fsS http://localhost:8080/healthz >/dev/null 2>&1 && break
    sleep 1
done
curl -fsS http://localhost:8080/healthz

echo ""
echo "==> 4/5 send signed batch"
python3 ops/scripts/send_test_batch.py

echo "==> 5/5 rows in postgres"
$DC exec -T postgres psql -U gameshield -d gameshield -c \
    "SELECT event_id, type, actor_player_id, amount FROM economic_events ORDER BY id DESC LIMIT 5;"

echo "==> e2e OK: edge-format batch -> HMAC -> schema validation -> PostgreSQL"
