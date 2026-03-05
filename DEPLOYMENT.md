# Django Kursanmeldung – Deployment auf Hetzner

## Server-Setup (bereits eingerichtet)
- **IP:** `89.167.0.28` – Hostname: `WestfaliaOsterwick` (Ubuntu 24.04)
- **App-Pfad:** `/var/www/kursanmeldung/`
- **Stack:** Nginx → Gunicorn (kein Docker)
- **Nginx-Config:** `/etc/nginx/sites-enabled/kursanmeldung`

---

## Update deployen (nach jedem `git push`)

```bash
ssh root@89.167.0.28
cd /var/www/kursanmeldung
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
kill -HUP $(pgrep -f 'gunicorn kursanmeldung' | head -1)
```

Der letzte Befehl lädt Gunicorn graceful neu (keine Downtime).

### Minimalbefehle je nach Änderungstyp

| Was geändert? | Befehle nötig |
|---|---|
| Nur Templates (`.html`) | `git pull` + `kill -HUP` |
| Python-Code (views, models) | `git pull` + `kill -HUP` |
| Neue Migration | + `python manage.py migrate` |
| Neues Paket in `requirements.txt` | + `pip install -r requirements.txt` |
| CSS/JS in `static/` | + `python manage.py collectstatic --noinput` |

> **Hinweis:** `git pull` allein reicht nie – Gunicorn cached Templates und Python-Code im Speicher (DEBUG=False). Immer `kill -HUP` ausführen.

---

## Nützliche Befehle auf dem Server

```bash
# Logs anzeigen
journalctl -u nginx -f
tail -f /var/log/nginx/error.log

# Gunicorn-Prozesse anzeigen
ps aux | grep gunicorn

# Django-Shell
cd /var/www/kursanmeldung
source .venv/bin/activate
python manage.py shell

# Nginx neu laden (nach Konfig-Änderung)
nginx -t && systemctl reload nginx
```

---

## Erstmalige Einrichtung (Referenz)

```bash
cd /var/www/kursanmeldung
cp .env.example .env
nano .env   # SECRET_KEY + ALLOWED_HOSTS=89.167.0.28 eintragen

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

Gunicorn als Daemon starten:
```bash
gunicorn kursanmeldung.wsgi:application --workers 3 --bind 127.0.0.1:8000 --daemon
```

---

## Umgebungsvariablen (`.env` auf dem Server)

| Variable | Wert |
|---|---|
| `SECRET_KEY` | langer zufälliger String |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `89.167.0.28` |


## Voraussetzungen auf dem Server

```bash
# Docker + Docker Compose installieren (einmalig)
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin
```

---

## Erstmalige Einrichtung auf dem Server

```bash
# 1. Repo klonen
git clone <repo-url> /opt/kursanmeldung
cd /opt/kursanmeldung

# 2. Umgebungsvariablen setzen
cp .env.example .env
nano .env
# → SECRET_KEY, ALLOWED_HOSTS (IP/Domain) eintragen

# 3. Container starten
docker compose up -d --build

# 4. Datenbank initialisieren
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Updates deployen (danach bei jedem Push)

```bash
cd /opt/kursanmeldung
bash deploy.sh
```

Das Skript führt automatisch aus:
1. `git pull origin main`
2. `docker compose build --no-cache`
3. `docker compose up -d`
4. `migrate` + `collectstatic`
5. Alte Images aufräumen

---

## Nützliche Befehle auf dem Server

```bash
# Logs anzeigen
docker compose logs -f web

# Container-Status
docker compose ps

# Django-Shell
docker compose exec web python manage.py shell

# Backup der SQLite-Datenbank
docker compose exec web cp db.sqlite3 db.sqlite3.bak
```

---

## Lokale Entwicklung

```bash
pip install -r requirements.txt
python manage.py runserver
```

---

## Umgebungsvariablen (`.env`)

| Variable | Beispiel |
|---|---|
| `SECRET_KEY` | langer zufälliger String |
| `DEBUG` | `False` (Produktion) |
| `ALLOWED_HOSTS` | `89.167.0.28,deine-domain.de` |

