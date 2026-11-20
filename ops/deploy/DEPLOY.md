# GameShield — guia de despliegue

Nada de esto se ejecuta automaticamente. Orden manual, una sola vez.

## 1. VPS (recomendado: Hetzner CX22, ~4.5 EUR/mes, Ubuntu 24.04)

    sudo apt update && sudo apt install -y docker.io docker-compose-v2 \
      postgresql redis-server caddy ufw fail2ban

## 2. Usuario y permisos

    sudo useradd -m -s /bin/bash gameshield
    sudo mkdir -p /srv/gameshield /etc/gameshield /var/backups/gameshield
    sudo chown -R gameshield:gameshield /srv/gameshield /var/backups/gameshield

## 3. Segredos

    sudo cp .env.example /etc/gameshield/env
    sudo nano /etc/gameshield/env      # claves reales, generadas con: openssl rand -hex 32
    sudo chmod 600 /etc/gameshield/env

## 4. Base de datos

    sudo -u postgres psql -c "CREATE USER gameshield WITH PASSWORD 'CAMBIAR-CONTRASENA-FUERTE';"
    sudo -u postgres psql -c "CREATE DATABASE gameshield OWNER gameshield;"

## 5. DNS (en el panel del DNS de hyperiumia.com)

    games.hyperiumia.com      A     IP_DEL_VPS
    ingest.games.hyperiumia.com A   IP_DEL_VPS

## 6. Servicios

    sudo cp ops/deploy/gameshield-*.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now gameshield-ingest gameshield-engine

## 7. Caddy

    sudo cp ops/deploy/Caddyfile /etc/caddy/Caddyfile
    sudo systemctl reload caddy     # TLS automatico via Let's Encrypt

## 8. Backup diario

    crontab -e    # agregar:
    0 4 * * * bash /srv/gameshield/ops/deploy/backup.sh >> /var/log/gameshield-backup.log 2>&1

## 9. Firewall

    sudo ufw allow 22,80,443/tcp && sudo ufw enable

## Deploy continuo (despues del setup inicial)

    GAMESHIELD_HOST=gameshield@IP bash ops/deploy/deploy.sh

## Checklist post-deploy

    curl https://games.hyperiumia.com/healthz
    curl https://ingest.games.hyperiumia.com/healthz
    # en un servidor FiveM: convars gameshield_ingest_url / gameshield_api_key / gameshield_secret
