# Django Kursanmeldung – Projekt-Briefing für Copilot

## 🎯 Projektübersicht
Eine Django-Webanwendung zur Kursverwaltung und -anmeldung für einen Breitensport-Verein.

## 🛠 Tech Stack
- Django 6.0.2
- Python 3.13
- SQLite (Entwicklung)
- Bootstrap 4.6.2
- django-allauth (Account-Management)
- crispy-forms + crispy-bootstrap4
- multiselectfield
- openpyxl (Excel-Export)

## 📋 Implementierte Features

### 1. Kursverwaltung
- Modelle: `Course`, `Location`, `Registration`
- Kurse mit Start-/Enddatum, Wochentagen, Zeiträumen
- Maximale Teilnehmerzahl + Warteliste
- Preis für Mitglieder/Nicht-Mitglieder
- Option für halbe Kurse
- Automatische Berechnung der Kurseinheiten basierend auf Wochentagen

### 2. Berechtigungssystem
- **Admin:** Vollzugriff auf alles
- **Kursleitung-Gruppe:** 
  - Sieht nur eigene Kurse (via `instructor_user` ForeignKey)
  - Kann nur Teilnehmerlisten sehen/exportieren
  - Keine Änderungs-/Löschrechte
- Benutzer werden nur von Admins angelegt (keine öffentliche Registrierung)

### 3. Frontend
- Rot-weißes Bootstrap-Theme (Vereinsfarben: `#c00000`)
- Responsive Tabellen-Übersicht für Kursliste
- Card-basiertes Design für Formulare
- Deutsche Sprache durchgängig
- Login/Logout in Card-Layout
- Navbar zeigt angemeldeten Benutzer

### 4. Admin-Bereich
- Custom rot-weißes Admin-Theme (`static/admin/css/custom.css`)
- Deutsche Labels (verbose_name für alle Models)
- Excel-Export für Teilnehmerlisten (mit rotem Header)
- CSV-Export für Anmeldungen
- Inline-Editing für Registrations beim Course

### 5. Migrations & Models
- `Course.instructor_user`: ForeignKey zu User für Zugriffskontrolle
- `Course.instructor`: TextField für Rückwärtskompatibilität
- Meta-Klassen mit deutschen verbose_name
- Migration 0007: Automatischer Name→User-Abgleich

## 📁 Projekt-Struktur
```
kursanmeldung/
├── courses/                    # Haupt-App
│   ├── models.py              # Course, Location, Registration
│   ├── views.py               # course_list, register, privacy + NoSignupAdapter
│   ├── admin.py               # Custom Admin + Permissions
│   ├── forms.py               # RegistrationForm mit Datenschutz-Link
│   ├── urls.py                # URL-Routing
│   ├── templates/courses/     # Frontend-Templates
│   │   ├── base.html
│   │   ├── course_list.html   # Tabellen-Layout
│   │   ├── register.html      # Card-Layout
│   │   └── privacy.html
│   └── migrations/            # 0001-0007
├── templates/account/         # Allauth-Overrides
│   ├── login.html             # Card-Styled
│   └── logout.html            # Card-Styled
├── static/admin/css/
│   └── custom.css             # Rot-weißes Admin-Theme
├── kursanmeldung/             # Projekt-Settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── db.sqlite3
└── README.md
```

## ⚙️ Wichtige Settings

### settings.py
```python
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
ACCOUNT_ALLOW_REGISTRATION = False
ACCOUNT_ADAPTER = 'courses.views.NoSignupAdapter'
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
CRISPY_TEMPLATE_PACK = 'bootstrap4'
```

### Installed Apps
- Kein Social-Auth (entfernt)
- Nur `allauth` + `allauth.account` (Login/Logout)

## 🧪 Tests
- 8 Tests in `courses/tests.py`
- Testen Kursleitung-Berechtigungen
- Card-basiertes Layout
- Signup-Disable
- Tabellen-Ansicht der Kursliste

## 🎨 Design-Entscheidungen
- **Vereinsfarbe:** `#c00000` (Rot)
- **Hintergrund:** Weiß
- **Schrift:** Standard Bootstrap, komplett auf Deutsch
- **Formular-Style:** Bootstrap Cards mit Schatten
- **Listen-Style:** Responsive Tabellen statt Cards (bessere Übersicht bei vielen Kursen)

## 🔐 Benutzerkonzept
- Keine öffentliche Registrierung
- Admins legen Benutzer im Django-Admin an
- Kursleitung = normale User + Gruppe "Kursleitung" + `instructor_user`-Zuweisung
- Kurs-Anmeldungen erfolgen über Frontend (ohne Login)

## 📦 Deployment-Status
- Lokale Entwicklung läuft
- `collectstatic` konfiguriert
- Bereit für PythonAnywhere/Render/DigitalOcean
- **NICHT** für GitHub Pages (braucht Python-Server!)

## 🚀 Nächste Schritte (offen)
- Production-Settings (DEBUG=False, ALLOWED_HOSTS, SECRET_KEY via ENV)
- Deployment zu PythonAnywhere oder Render
- Optional: E-Mail-Benachrichtigungen bei Anmeldung
- Optional: Payment-Integration

## 💡 Wichtige Befehle
```bash
# Tests
python manage.py test courses.tests

# Static files sammeln
python manage.py collectstatic

# Migrationen
python manage.py makemigrations
python manage.py migrate

# Server starten
python manage.py runserver

# Superuser anlegen
python manage.py createsuperuser
```

## 🐛 Bekannte Besonderheiten
- `forms.py` hat reverse_lazy im __init__ (für Privacy-Link)
- Admin verwendet is_staff + groups.filter(name='Kursleitung')
- Course-Admin filtert queryset nach instructor_user
- Registration.terms_accepted ist extra BooleanField (nicht im Model)

---

**Dieses Briefing an neuen Copilot übergeben:** Kopiere diesen Text einfach in die erste Nachricht an den neuen Copilot und sage „Lies dieses Projekt-Briefing und hilf mir beim nächsten Feature."
