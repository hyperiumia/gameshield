#!/usr/bin/env bash
# GameShield — deploy manual desde el Legion al VPS.
# USO: GAMESHIELD_HOST=deploy@IP bash ops/deploy/deploy.sh
# No corre solo: hay que invocarlo a mano. No toca la base de datos.
set -euo pipefail

HOST="${GAMESHIELD_HOST:?define GAMESHIELD_HOST=deploy@IP}"
REMOTE_DIR=/srv/gameshield
HERE="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> 1/5 build local del dashboard"
(cd "$HERE/apps/web" && npm ci --silent && npm run build)

echo "==> 2/5 sincronizar codigo (excluye artefactos locales)"
rsync -az --delete \
  --exclude '.git' --exclude 'node_modules' --exclude 'target' \
  --exclude '.venv' --exclude 'dist' --exclude '.env' \
  "$HERE/" "$HOST:$REMOTE_DIR/"

echo "==> 3/5 build remoto (rust + python + web)"
ssh "$HOST" bash -s << 'REMOTE'
set -euo pipefail
cd /srv/gameshield/services/ingest && cargo build --release
cd /srv/gameshield/services/engine && uv sync
cd /srv/gameshield/apps/web && npm ci --silent && npm run build
REMOTE

echo "==> 4/5 reiniciar servicios"
ssh "$HOST" 'sudo systemctl restart gameshield-ingest gameshield-engine'

echo "==> 5/5 healthchecks"
curl -fsS https://games.hyperiumia.com/healthz || true
curl -fsS https://ingest.games.hyperiumia.com/healthz || true

echo "==> deploy completo"
