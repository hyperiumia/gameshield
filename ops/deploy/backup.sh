#!/usr/bin/env bash
# Backup diario de Postgres — correr via cron en el VPS.
# 0 4 * * * bash /srv/gameshield/ops/deploy/backup.sh >> /var/log/gameshield-backup.log 2>&1
set -euo pipefail

DEST=/var/backups/gameshield
STAMP=$(date +%F_%H%M)
KEEP_DAYS=14

mkdir -p "$DEST"
pg_dump -U gameshield -d gameshield -Fc -f "$DEST/gameshield_$STAMP.dump"
find "$DEST" -name 'gameshield_*.dump' -mtime +"$KEEP_DAYS" -delete
echo "[$(date -u +%FT%TZ)] backup ok: gameshield_$STAMP.dump"
