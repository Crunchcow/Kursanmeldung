# Django Kursanmeldung – Deployment auf Hetzner (Docker Compose)

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

