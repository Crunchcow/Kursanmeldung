#!/usr/bin/env bash
# deploy.sh – Auf dem Hetzner-Server ausführen: bash /var/www/kursanmeldung/deploy.sh
set -euo pipefail

cd /var/www/kursanmeldung

echo "==> Aktuellen Code holen..."
git pull origin main

echo "==> Abhängigkeiten installieren..."
source .venv/bin/activate
pip install -r requirements.txt --quiet

echo "==> Datenbankmigrationen ausführen..."
python manage.py migrate --noinput

echo "==> Static files sammeln..."
python manage.py collectstatic --noinput

echo "==> Gunicorn neu laden..."
kill -HUP $(pgrep -f 'gunicorn kursanmeldung' | head -1)

echo "✅ Deployment abgeschlossen!"
