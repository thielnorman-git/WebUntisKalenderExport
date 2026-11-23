WebUntisKalenderExport
ICS-Export als Wochenplan für Familien und Eltern

Untis iCal-Exporter & Dashboard (v1.0.0) exportiert Stundenpläne, Hausaufgaben, Mitteilungen und Prüfungen aus WebUntis über ein Python-Skript in .ics-Kalenderdateien. Zusätzlich werden kombinierte *_alle.ics-Feeds erzeugt und über Apache zusammen mit einem Web-Dashboard unter /untis/ bereitgestellt.

Features
Export von Stundenplänen
Export von Hausaufgaben
Export von Mitteilungen
Export von Prüfungen (falls in WebUntis verfügbar)
Erzeugung kombinierter Kalenderfeeds (*_alle.ics)
Unterstützung mehrerer Schulen und WebUntis-Instanzen
Web-Dashboard mit Wochenansicht
Direkte Kalender-Abonnements für Smartphone, Outlook, Apple Kalender und Google Kalender
Automatische Aktualisierung per Cronjob alle 20 Minuten
Verzeichnisstruktur
Pfad	Zweck
/opt/untis-ical/untis_to_ical.py	Hauptskript für WebUntis-Abruf und ICS-Erzeugung
/opt/untis-ical/config.json	Konfiguration, Zugangsdaten und Profile
/opt/untis-ical/untis-ical.log	Laufzeit- und Cron-Log
/var/www/html/untis/index.html	Web-Dashboard
/var/www/html/untis/children.json	Öffentliches Profil-Manifest
/var/www/html/untis/<slug>.ics	Stundenplan
/var/www/html/untis/<slug>_hausaufgaben.ics	Hausaufgaben
/var/www/html/untis/<slug>_mitteilungen.ics	Mitteilungen
/var/www/html/untis/<slug>_pruefungen.ics	Prüfungen
/var/www/html/untis/<slug>_alle.ics	Kombinierter Gesamtkalender
Aufbau des Gesamtkalenders
Der kombinierte Kalender *_alle.ics enthält:

Stundenplan
Hausaufgaben
Mitteilungen
Prüfungen
Zur besseren Unterscheidung werden folgende Präfixe verwendet:

Typ	Präfix
Hausaufgabe	[HA]
Mitteilung	[Info]
Prüfung	[Prüfung]
Zusätzlich erfolgt eine UID-basierte Deduplizierung, damit Termine nicht mehrfach erscheinen.

Installation
Voraussetzungen
Linux Server
Apache HTTP Server
Python 3
Zugriff auf WebUntis
Benötigte Python-Pakete:

pip install icalendar requests
oder weitere projektabhängige Bibliotheken.

Dateiberechtigungen
Empfohlene Berechtigungen:

Dateien
0644 (-rw-r--r--)
Verzeichnisse
0755 (drwxr-xr-x)
Dadurch kann Apache alle .ics, .json und .html Dateien lesen und bereitstellen.

Manueller Testlauf
PYTHONPATH=/opt/untis-ical \
UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json \
python3 -u /opt/untis-ical/untis_to_ical.py
Konfiguration
Die Konfiguration erfolgt über:

/opt/untis-ical/config.json
Unterstützte Profile
Das Projekt unterstützt zwei Profiltypen:

children
Normale Schülerprofile.

children_other_school
Profile auf abweichenden WebUntis-Instanzen.

Beispiele:

lasker-schule-veseli-schule.webuntis.com
thalia-grundschule.webuntis.com
Zeitraumsteuerung
Der Abrufzeitraum wird über folgende Parameter definiert:

{
  "include_weeks_back": 6,
  "weeks_ahead": 12
}
Beispiel
Bei:

{
  "include_weeks_back": 6
}
und einer aktuellen Woche ab dem 23.11.2026 beginnt der Export bereits sechs Wochen früher.

Prüfungen
Prüfungen werden über den WebUntis-Endpunkt abgefragt:

/api/exams
Besonderheiten:

Kein einschränkender studentId-Filter
Vollständige Prüfungsliste des jeweiligen Schülers
Falls eine Schule das Modul nicht aktiviert hat, liefert WebUntis:
403 Forbidden
Dieser Fall wird lediglich als DEBUG-Meldung protokolliert und nicht als Warnung behandelt.

Automatischer Betrieb
Cronjob
Der automatische Abruf erfolgt alle 20 Minuten über den Benutzer autodarts.

*/20 * * * * PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json python3 -u /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1
Logging
Logdatei:

/opt/untis-ical/untis-ical.log
Letzte 30 Log-Zeilen anzeigen
tail -n 30 /opt/untis-ical/untis-ical.log
Anzahl der Termine prüfen
grep -c "BEGIN:VEVENT" /var/www/html/untis/*.ics
Apache-Erreichbarkeit testen
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/untis/
Web-Dashboard
Die Benutzeroberfläche unter

/untis/
lädt ihre Daten dynamisch aus:

children.json
sowie den jeweiligen ICS-Dateien.

Funktionen
Kind-Auswahl
Wechsel zwischen mehreren Kindern
Dynamischer Profilwechsel ohne Seitenreload
Wochen-Navigation
Vorherige Woche
Aktuelle Woche
Nächste Woche
Stundenplan-Grid
Anzeige von:

Unterrichtsstunden
Vertretungen
Ausfällen
Prüfungen
Prüfungen werden automatisch aus:

<slug>_pruefungen.ics
übernommen und im passenden Zeitfenster dargestellt.

Zusatzbereiche
Prüfungen
Wochenübersicht aller anstehenden Prüfungen.

Hausaufgaben
Anzeige aller fälligen Aufgaben der gewählten Woche.

Mitteilungen
Anzeige aktueller Mitteilungen aus WebUntis.

Zusätzlich verfügbar:

Umschalter für sämtliche Nachrichten
Filterung nach aktueller Woche
Kalender-Abonnement
Für jedes Kind wird automatisch ein kombinierter Kalender bereitgestellt:

/untis/<slug>_alle.ics
Im Dashboard stehen folgende Funktionen zur Verfügung:

Kalender herunterladen
Kalender direkt öffnen
Kalender abonnieren
Abo-URL in die Zwischenablage kopieren
Beispiel-Workflow
Cronjob startet alle 20 Minuten.
Python-Skript meldet sich bei WebUntis an.
Stundenplan, Hausaufgaben, Mitteilungen und Prüfungen werden abgerufen.
Einzelne .ics-Dateien werden erzeugt.
Kombinierter *_alle.ics-Feed wird erstellt.
children.json wird aktualisiert.
Apache stellt die Daten unter /untis/ bereit.
Das Dashboard lädt und visualisiert die Informationen automatisch.
Sicherheitshinweise
Zugangsdaten verbleiben ausschließlich in der config.json
children.json enthält keine Zugangsdaten
Öffentlich bereitgestellt werden nur Kalenderdateien und Profildaten
Zugriff auf das Verzeichnis sollte bei externer Veröffentlichung über HTTPS abgesichert werden
Lizenz
Dieses Projekt wird ohne Gewähr bereitgestellt.

Die Nutzung erfolgt auf eigene Verantwortung. Bitte die Nutzungsbedingungen von WebUntis sowie die Datenschutzvorgaben der jeweiligen Schule beachten.
