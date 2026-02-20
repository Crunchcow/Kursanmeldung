# Django Kursanmeldung Deployment-Anleitung

## Vorbereitung für Produktionsumgebung

### 1. `.gitignore` erstellen

```
*.pyc
__pycache__/
.venv/
db.sqlite3
staticfiles/
*.db
.env
```

### 2. `requirements.txt` aktualisieren

```bash
pip freeze > requirements.txt
```

### 3. Production-Settings

In Produktionsumgebung setzen:
- `DEBUG = False`
- `ALLOWED_HOSTS = ['dein-domain.com']`
- `SECRET_KEY` in Umgebungsvariable

### 4. Zu Plattform deployen

#### Option A: PythonAnywhere
- Git-Repo hochladen
- Webapp erstellen
- WSGI-Datei bearbeiten
- Static files sammeln

#### Option B: Render.com
- GitHub-Repo connecten
- Render.yaml hinzufügen
- Deploy-Branch auswählen

#### Option C: Docker
```dockerfile
FROM python:3.13
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "kursanmeldung.wsgi"]
```

## Weitere Informationen

Die App ist für einfaches Deployment vorbereitet. Kontaktiere bei Fragen!
