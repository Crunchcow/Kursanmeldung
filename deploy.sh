#!/usr/bin/env bash
# deploy.sh – Auf dem Hetzner-Server ausführen
set -euo pipefail

echo "==> Aktuellen Code holen..."
git pull origin main

echo "==> Docker-Image neu bauen..."
docker compose build --no-cache

echo "==> Container neu starten (zero-downtime)..."
docker compose up -d --remove-orphans

echo "==> Datenbankmigrationen ausführen..."
docker compose exec web python manage.py migrate --noinput

echo "==> Static files sammeln..."
docker compose exec web python manage.py collectstatic --noinput

echo "==> Alte Images aufräumen..."
docker image prune -f

echo "✅ Deployment abgeschlossen!"
