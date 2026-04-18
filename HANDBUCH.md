# Kursanmeldung - Benutzerhandbuch

## Projektübersicht

Die **Kursanmeldung** ist eine webbasierte Anwendung zur Verwaltung von Kursen im Breitensport-Verein. Sie ermöglicht die einfache Organisation von Kursen, Anmeldungen und Teilnehmerlisten.

---

## Für Kursleiter und Administratoren

### Admin-Zugang
- **URL:** `https://[domain]/admin/`
- **Login:** Mit Ihren Admin-Zugangsdaten

### Hauptfunktionen im Admin-Bereich

#### 1. Kursverwaltung
Unter **KURSE** können Sie:
- Neue Kurse anlegen
- Bestehende Kurse bearbeiten
- Kurse löschen

**Kursdetails festlegen:**
- **Titel:** Name des Kurses
- **Beschreibung:** Detaillierte Kursinformationen
- **Kursleitung:** Verantwortliche Person(en)
- **Ort:** Veranstaltungsort
- **Start-/Enddatum:** Zeitraum des Kurses
- **Wochentage:** Regelmäßige Termine
- **Preis:** Mitglieder/Nicht-Mitglieder
- **Max. Teilnehmer:** Begrenzung der Teilnehmerzahl

#### 2. Ortverwaltung
Unter **ORTE** können Sie:
- Veranstaltungsorte anlegen und verwalten
- Adressen und Kapazitäten festlegen

#### 3. Preisverwaltung
Unter **PREISE** können Sie:
- Verschiedene Preismodelle definieren
- Mitglieder- und Nicht-Mitgliederpreise festlegen

#### 4. Teilnehmerlisten exportieren
- **CSV-Export:** Alle Teilnehmerdaten herunterladen
- **Filterung:** Nach Kursen und Zeiträumen
- **Kontaktdaten:** Für Kommunikation mit Teilnehmern

---

## Für Kursteilnehmer

### Anmeldung zu Kursen

#### 1. Kursübersicht
- Rufen Sie die Kursseite auf
- Alle verfügbaren Kurse werden mit Details angezeigt:
  - Titel und Beschreibung
  - Datumsspanne und Wochentage
  - Anzahl der Einheiten
  - Preise für Mitglieder/Nicht-Mitglieder
  - Verfügbare Plätze

#### 2. Anmeldeprozess
1. Gewünschten Kurs auswählen
2. "Anmelden" Button klicken
3. Microsoft-Konto-Login (falls konfiguriert) oder Registrierung
4. Persönliche Daten eingeben
5. Mitgliedschaftsstatus auswählen
6. Anmeldung bestätigen

#### 3. Warteliste
- Bei voll belegten Kursen wird automatisch eine Warteliste geführt
- Bei Absagen werden Plätze automatisch nachgereiht
- Benachrichtigung per E-Mail bei freien Plätzen

---

## Benutzerrollen und Berechtigungen

### 1. Abteilungsleitung / Admin
- Vollständiger Zugriff auf alle Funktionen
- Kurse anlegen, bearbeiten, löschen
- Teilnehmerlisten verwalten
- Preise und Orte verwalten
- Benutzerkonten verwalten

### 2. Kursleitung
- Zugriff auf eigene Kurse
- Teilnehmerlisten einsehen
- CSV-Export durchführen
- **Keine** Bearbeitungsmöglichkeiten für Kurse

#### Kursleitung zuweisen:
1. Admin-Bereich → Benutzer → Gruppen
2. Gruppe "Kursleitung" anlegen (falls nicht vorhanden)
3. Benutzer zur Gruppe hinzufügen
4. Beim Kursanlegen unter "Kursleitung (Benutzer)" zuweisen

---

## Wichtige Administrationsaufgaben

### Neuen Kurs anlegen
1. Admin-Bereich → KURSE → Add
2. Alle Pflichtfelder ausfüllen:
   - Titel, Beschreibung
   - Start- und Enddatum
   - Wochentage und Uhrzeiten
   - Ort und Preis
   - Kursleitung zuweisen
3. Speichern

### Kursänderungen durchführen
1. Kurs in der Liste auswählen
2. Änderungen vornehmen
3. Speichern
4. **Wichtig:** Teilnehmer werden über Änderungen informiert

### Teilnehmerliste exportieren
1. Kurs auswählen
2. "Teilnehmer" Tab öffnen
3. "CSV Export" Button klicken
4. Datei herunterladen

---

## Anmeldezeiträume und Regeln

### Anmeldefristen
- Anmeldungen nur innerhalb des Kurszeitraums möglich
- Startdatum muss erreicht oder überschritten sein
- Enddatum darf nicht überschritten sein

### Preisberechnung
- **Festpreis pro Kurs** (nicht pro Einheit)
- Preis wird einmalig berechnet
- Mitglieder- und Nicht-Mitgliederpreise werden unterschieden

### Platzvergabe
- Begrenzte Teilnehmerzahl pro Kurs
- "First come, first served" Prinzip
- Automatische Wartelistenführung

---

## Microsoft-Login Integration

### Für Benutzer
- Anmeldung mit bestehendem Microsoft-Konto möglich
- Keine zusätzliche Registrierung erforderlich
- Sichere Authentifizierung über Microsoft

### Für Administratoren
- Provider muss im Admin-Bereich konfiguriert sein
- Azure AD Anwendung muss eingerichtet sein
- Redirect URI muss korrekt konfiguriert sein

---

## Fehlerbehebung

### Häufige Probleme

**"Anmeldung nicht möglich"**
- Kurszeitraum prüfen
- Plätze verfügbar?
- Warteliste voll?

**"Login funktioniert nicht"**
- Microsoft-Konto gültig?
- Passwort korrekt?
- Browser-Cache leeren

**"Kurs nicht sichtbar"**
- Kurs aktiv geschaltet?
- Startdatum erreicht?
- Admin-Berechtigung prüfen

**"Export funktioniert nicht"**
- Teilnehmer vorhanden?
- Browser-Downloads aktiviert?
- Datei im Download-Ordner suchen?

---

## Mobile Nutzung

### Responsive Design
- Anwendung funktioniert auf Smartphones und Tablets
- Touch-optimierte Bedienung
- Vollständige Funktionalität auch mobil

### Empfehlungen
- Aktuelle Browser-Version verwenden
- WLAN-Verbindung für stabile Nutzung
- Bildschirmgröße mindestens 5 Zoll

---

## Technische Informationen

### Systemanforderungen
- Webbrowser mit JavaScript-Unterstützung
- Internetverbindung
- Microsoft-Konto (für Login)

### Browser-Unterstützung
- Chrome (aktuellste Version)
- Firefox (aktuellste Version)
- Safari (aktuellste Version)
- Edge (aktuellste Version)

---

## Support und Hilfe

### Technischer Support
Bei Problemen mit der Anwendung:
- IT-Abteilung des Vereins kontaktieren
- Screenshot des Fehlers machen
- Browser und Version angeben

### Inhaltliche Fragen
Bei Fragen zu Kursen und Anmeldungen:
- Kursleitung kontaktieren
- Abteilungsleitung
- Vereinsbüro

---

## Rechtliche Hinweise

### Datenschutz
- Alle personenbezogenen Daten werden DSGVO-konform verarbeitet
- Speicherung nur für vereinbarte Zwecke
- Löschung nach Ablauf der Aufbewahrungsfristen

### Teilnahmebedingungen
- Anmeldung ist verbindlich
- Teilnahmegebühren werden fällig bei Anmeldung
- Absagefristen müssen beachtet werden

---

*Letzte Aktualisierung: April 2026*
