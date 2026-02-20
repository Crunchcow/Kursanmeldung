# Kursanmeldung

Einfache Django-Anwendung zur automatisierten Kursverwaltung für den Breitensport-Verein.

## Einrichtung

1. Python 3 installieren (>=3.10).
2. In Projektverzeichnis virtuellen Env aktivieren (`.venv` erstellt):
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
3. Abhängigkeiten installieren:
   ```powershell
   pip install -r requirements.txt
   ```
4. Migrationen durchführen:
   ```powershell
   python manage.py migrate
   ```
5. Superuser anlegen:
   ```powershell
   python manage.py createsuperuser
   ```
6. Entwicklungsserver starten:
   ```powershell
   python manage.py runserver
   ```

## Funktionen

- Admin-Dashboard zur Pflege von Kursen, Orten, Preisen und Leitung.
- Anmeldung per Frontend inklusive Warteliste.
- Microsoft-Account-Login via `django-allauth` (Provider in Admin konfigurieren).
- CSV-Export der Teilnehmerlisten.
- Rot/weißes Bootstrap-Theme.

## Kurszeitraum und Einheiten

Jeder Kurs besitzt nun ein Start‑ und Enddatum. Im Admin können diese beim Anlegen gesetzt werden; Anmeldungen sind nur innerhalb dieses Zeitraums möglich.
Bei der Anzeige im Frontend werden außerdem:

* Datumsspanne
* Wochentage
* Anzahl der Einheiten (automatisch berechnet)
* Preise für Mitglieder/Nicht-Mitglieder gezeigt (Festpreis pro Kurs, unabhängig von Einheiten)

Bei der Registrierungsseite aktualisiert ein JavaScript die gewählten Kosten. Eine Multiplikation mit der Anzahl der Einheiten erfolgt **nicht**; der Gesamtpreis entspricht dem einmalig festgelegten Kursbetrag.

## Sprache und Übersetzungen

Alle Texte sind auf Deutsch konfiguriert. Django verwendet `LANGUAGE_CODE = 'de-de'` und `LocaleMiddleware`.
Um eigene Textänderungen zu übernehmen, erzeuge die Übersetzungsdateien im Projektordner:

```powershell
python manage.py makemessages -l de   # benötigt gettext (msguniq, msgfmt)
# anschließend die generierte locale/de/LC_MESSAGES/django.po bearbeiten
python manage.py compilemessages
```

Da auf Windows oft keine GNU‑gettext installiert ist, kannst du die `.po`-Dateien auch manuell anlegen und übersetzen.

## Benutzer und Berechtigungen

- **Abteilungsleitung / Admin:** staff‑Benutzer mit vollem Zugriff.
- **Kursleitung:** lege eine Gruppe `Kursleitung` an (Admin → Benutzer → Gruppen). Mitglieder dieser Gruppe können nur Teilnehmerlisten sehen und als CSV exportieren, aber nichts ändern.

Standard‑Admin‑Login ist unter `/admin/` erreichbar – zusätzlich gibt es im Hauptmenü einen Link für staff‑Benutzer.

Weitere Anpassungen je nach Bedarf.