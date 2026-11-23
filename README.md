WebUntisKalenderExport

ICS-Export als Wochenplan für Familien und Eltern.

Untis iCal-Exporter & Dashboard (v1.0.0)

Exportiert Stundenpläne, Hausaufgaben, Mitteilungen und Prüfungen aus WebUntis über ein Python-Skript in .ics-Kalenderdateien.

Zusätzlich werden kombinierte Kalenderfeeds (*_alle.ics) erzeugt und über Apache zusammen mit einem Web-Dashboard unter /untis/ bereitgestellt.

Features
Export von Stundenplänen
Export von Hausaufgaben
Export von Mitteilungen
Export von Prüfungen (falls in WebUntis verfügbar)
Erzeugung kombinierter Kalenderfeeds (*_alle.ics)
Unterstützung mehrerer Schulen und WebUntis-Instanzen
Automatische Aktualisierung per Cronjob
Web-Dashboard mit Wochenansicht
Kalender-Abonnement für Outlook, Apple Kalender, Google Kalender und Smartphones
Verzeichnisstruktur
Pfad	Beschreibung
/opt/untis-ical/untis_to_ical.py	Hauptskript für WebUntis-Abruf und ICS-Erzeugung
/opt/untis-ical/config.json	Zugangsdaten, Profile, Zeitraum und Ausgabeziel
/opt/untis-ical/untis-ical.log	Laufzeit- und Cron-Log
/var/www/html/untis/index.html	Web-Dashboard
/var/www/html/untis/children.json	Öffentliches Profil-Manifest
/var/www/html/untis/<slug>.ics	Stundenplan
/var/www/html/untis/<slug>_hausaufgaben.ics	Hausaufgaben
/var/www/html/untis/<slug>_mitteilungen.ics	Mitteilungen
/var/www/html/untis/<slug>_pruefungen.ics	Prüfungen
/var/www/html/untis/<slug>_alle.ics	Kombinierter Gesamtkalender
Gesamtkalender (*_alle.ics)

Der kombinierte Kalender enthält:

Stundenplan
Hausaufgaben
Mitteilungen
Prüfungen

Zur Kennzeichnung werden folgende Präfixe verwendet:

Typ	Präfix
Hausaufgaben	[HA]
Mitteilungen	[Info]
Prüfungen	[Prüfung]

Zusätzlich erfolgt eine UID-basierte Deduplizierung, damit Termine nicht mehrfach erscheinen.

Setup & Berechtigungen
Backend

Verzeichnis:

/opt/untis-ical/


Benötigt:

Python 3
icalendar
requests
weitere projektspezifische Abhängigkeiten

Installation der Standard-Abhängigkeiten:

Shell
pip install icalendar requests
Webserver

Verzeichnis:

/var/www/html/untis/


Bereitstellung über Apache unter:

/untis/

Dateirechte

Dateien:

0644 (-rw-r--r--)


Verzeichnisse:

0755 (drwxr-xr-x)


Dadurch kann Apache sämtliche .html, .ics und .json Dateien lesen.

Manueller Testlauf
Shell
PYTHONPATH=/opt/untis-ical \
UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json \
python3 -u /opt/untis-ical/untis_to_ical.py
 
Konfiguration

Die Konfiguration erfolgt über:

/opt/untis-ical/config.json

Unterstützte Profiltypen
children

Normale Schülerprofile.

children_other_school

Profile auf anderen WebUntis-Instanzen.

Beispielsweise:

lasker-schule-veseli-schule.webuntis.com
thalia-grundschule.webuntis.com
Zeitraumsteuerung

Über folgende Parameter wird festgelegt, wie viele Wochen zurück bzw. voraus geladen werden:

JSON
{
"include_weeks_back": 6,
"weeks_ahead": 12
}

Beispiel:

6 Wochen rückwirkend
12 Wochen in die Zukunft
Prüfungen

Prüfungen werden über folgenden Endpunkt abgefragt:

/api/exams


Besonderheiten:

Kein einschränkender studentId-Filter
Vollständige Prüfungsliste des jeweiligen Schülers
Schulen ohne aktiviertes Prüfungsmodul liefern 403 Forbidden

Dieser Fall wird lediglich als DEBUG-Eintrag protokolliert und nicht als Fehler behandelt.

Automatischer Betrieb
Cronjob

Aktualisierung alle 20 Minuten:

JSON
cron wird nicht vollständig unterstützt. Die Syntaxhervorhebung basiert auf JSON.
*/20 * * * * PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json python3 -u /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1
 
Logging & Monitoring
Letzte Logeinträge anzeigen
Shell
tail -n 30 /opt/untis-ical/untis-ical.log
Anzahl exportierter Termine prüfen
Shell
grep -c "BEGIN:VEVENT" /var/www/html/untis/*.ics
Apache-Erreichbarkeit prüfen
Shell
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/untis/
Web-Dashboard

Die Weboberfläche lädt ihre Daten dynamisch aus children.json und den jeweiligen ICS-Dateien des ausgewählten Kindes.

Funktionen
Kind-Auswahl
Wechsel zwischen mehreren Kindern
Dynamische Profilumschaltung
Wochen-Navigation
Vorherige Woche
Aktuelle Woche
Nächste Woche
Stundenplan-Grid

Anzeige von:

Unterricht
Vertretungen
Ausfällen
Prüfungen

Prüfungen werden automatisch aus

<slug>_pruefungen.ics


geladen und im entsprechenden Zeitfenster dargestellt.

Zusatzbereiche
Prüfungen

Wochenübersicht aller Prüfungen.

Hausaufgaben

Übersicht aller fälligen Aufgaben.

Mitteilungen

Anzeige aktueller Mitteilungen inklusive Umschalter für sämtliche Meldungen.

Kalender-Abonnement

Für jedes Kind wird ein kombinierter Kalender bereitgestellt:

/untis/<slug>_alle.ics


Verfügbare Funktionen:

Kalender herunterladen
Kalender direkt öffnen
Kalender abonnieren
Abo-URL kopieren
Ablauf
Plain Text
Cronjob
│
▼
WebUntis Login
│
▼
Abruf von:
- Stundenplan
- Hausaufgaben
- Mitteilungen
- Prüfungen
│
▼
Erzeugung einzelner ICS-Dateien
│
▼
Erzeugung von *_alle.ics
│
▼
Aktualisierung children.json
│
▼
Bereitstellung über Apache
│
▼
Anzeige im Dashboard
Sicherheit
Zugangsdaten verbleiben ausschließlich in config.json
children.json enthält keine Zugangsdaten
Öffentlich bereitgestellt werden nur Kalenderdaten und Profilinformationen
Für externe Nutzung wird HTTPS empfohlen
Lizenz

Dieses Projekt wird ohne Gewähr bereitgestellt.

Die Nutzung erfolgt auf eigene Verantwortung.

Bitte die Datenschutzrichtlinien der jeweiligen Schule sowie die Nutzungsbedingungen von WebUntis beachten.
