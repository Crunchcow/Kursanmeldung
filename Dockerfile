FROM python:3.13-slim

# System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Abhängigkeiten installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

EXPOSE 8000

CMD ["gunicorn", "kursanmeldung.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
