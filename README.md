<h1>WebUntisKalenderExport</h1>

<p><strong>ICS-Export als Wochenplan für Familien und Eltern</strong></p>

<h2>Untis iCal-Exporter &amp; Dashboard (v1.0.0)</h2>

<p>
Exportiert Stundenpläne, Hausaufgaben, Mitteilungen und Prüfungen aus WebUntis
über ein Python-Skript in <code>.ics</code>-Kalenderdateien.
</p>

<p>
Zusätzlich werden kombinierte Kalenderfeeds
(<code>*_alle.ics</code>) erzeugt und über Apache zusammen mit einem
Web-Dashboard unter <code>/untis/</code> bereitgestellt.
</p>

<hr>

<h2>🚀 Features</h2>

<ul>
    <li>Export von Stundenplänen</li>
    <li>Export von Hausaufgaben</li>
    <li>Export von Mitteilungen</li>
    <li>Export von Prüfungen (falls verfügbar)</li>
    <li>Erzeugung kombinierter Kalenderfeeds (<code>*_alle.ics</code>)</li>
    <li>Unterstützung mehrerer Schulen und WebUntis-Instanzen</li>
    <li>Automatische Aktualisierung per Cronjob</li>
    <li>Web-Dashboard mit Wochenansicht</li>
    <li>Kalender-Abonnement für Outlook, Apple Kalender, Google Kalender und Smartphones</li>
</ul>

<hr>

<h2>📁 Verzeichnisstruktur</h2>

<table>
<tr>
<th>Pfad</th>
<th>Beschreibung</th>
</tr>

<tr>
<td><code>/opt/untis-ical/untis_to_ical.py</code></td>
<td>Hauptskript für WebUntis-Abruf und ICS-Erzeugung</td>
</tr>

<tr>
<td><code>/opt/untis-ical/config.json</code></td>
<td>Zugangsdaten, Profile, Zeitraum und Ausgabeziel</td>
</tr>

<tr>
<td><code>/opt/untis-ical/untis-ical.log</code></td>
<td>Laufzeit- und Cron-Log</td>
</tr>

<tr>
<td><code>/var/www/html/untis/index.html</code></td>
<td>Web-Dashboard</td>
</tr>

<tr>
<td><code>/var/www/html/untis/children.json</code></td>
<td>Öffentliches Profil-Manifest</td>
</tr>

<tr>
<td><code>/var/www/html/untis/&lt;slug&gt;.ics</code></td>
<td>Stundenplan</td>
</tr>

<tr>
<td><code>/var/www/html/untis/&lt;slug&gt;_hausaufgaben.ics</code></td>
<td>Hausaufgaben</td>
</tr>

<tr>
<td><code>/var/www/html/untis/&lt;slug&gt;_mitteilungen.ics</code></td>
<td>Mitteilungen</td>
</tr>

<tr>
<td><code>/var/www/html/untis/&lt;slug&gt;_pruefungen.ics</code></td>
<td>Prüfungen</td>
</tr>

<tr>
<td><code>/var/www/html/untis/&lt;slug&gt;_alle.ics</code></td>
<td>Kombinierter Gesamtkalender</td>
</tr>
</table>

<hr>

<h2>📅 Gesamtkalender (*_alle.ics)</h2>

<p>Der kombinierte Kalender enthält:</p>

<ul>
<li>Stundenplan</li>
<li>Hausaufgaben</li>
<li>Mitteilungen</li>
<li>Prüfungen</li>
</ul>

<p>Zur Unterscheidung werden folgende Präfixe verwendet:</p>

<table>
<tr>
<th>Typ</th>
<th>Präfix</th>
</tr>
<tr>
<td>Hausaufgaben</td>
<td><code>[HA]</code></td>
</tr>
<tr>
<td>Mitteilungen</td>
<td><code>[Info]</code></td>
</tr>
<tr>
<td>Prüfungen</td>
<td><code>[Prüfung]</code></td>
</tr>
</table>

<p>
Zusätzlich erfolgt eine UID-basierte Deduplizierung, damit Termine
nicht mehrfach erscheinen.
</p>

<hr>
<h2>🚀 Quick Start</h2>

<pre><code>
git clone https://github.com/thielnorman-git/WebUntisKalenderExport.git

cd WebUntisKalenderExport

pip install -r requirements.txt

cp config.example.json config.json

python3 untis_to_ical.py
</code></pre>

<h2>⚙️ Setup &amp; Berechtigungen</h2>

<h3>Backend</h3>

<p><strong>Verzeichnis</strong></p>

<pre><code>/opt/untis-ical/</code></pre>

<p><strong>Benötigt</strong></p>

<ul>
<li>Python 3</li>
<li>icalendar</li>
<li>requests</li>
<li>pytz</li>
<li>Apache oder Nginx (optional für das Dashboard)</li>
</ul>

<p><strong>Installation</strong></p>

<pre><code>
pip install -r requirements.txt
</code></pre>

<h3>Webserver</h3>

<pre><code>/var/www/html/untis/</code></pre>

<p>Bereitstellung über Apache unter:</p>

<pre><code>/untis/</code></pre>

<h3>Dateirechte</h3>

<p>Dateien:</p>

<pre><code>0644 (-rw-r--r--)</code></pre>

<p>Verzeichnisse:</p>

<pre><code>0755 (drwxr-xr-x)</code></pre>

<hr>

<h2>🧪 Manueller Testlauf</h2>

<pre><code>PYTHONPATH=/opt/untis-ical \
UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json \
python3 -u /opt/untis-ical/untis_to_ical.py
</code></pre>

<hr>

<h2>🔧 Konfiguration</h2>

<p>Die Konfiguration erfolgt über:</p>

<pre><code>/opt/untis-ical/config.json</code></pre>

<h3>Unterstützte Profiltypen</h3>

<h4>children</h4>

<p>Normale Schülerprofile.</p>

<h4>children_other_school</h4>

<p>Profile auf anderen WebUntis-Instanzen.</p>

<p>Beispiele:</p>

<ul>
<li>schule.webuntis.com</li>
<li>andere-schule.webuntis.com</li>
</ul>
<hr>

<h3>🔍 Automatische Erkennung der Schüler-ID</h3>

<p>
In den meisten Fällen müssen <code>element_type</code> und
<code>element_id</code> nicht manuell angegeben werden.
Das Skript erkennt diese Werte beim Login automatisch.
</p>

<p>
Führe das Skript einmal manuell aus:
</p>

<pre><code>python3 untis_to_ical.py</code></pre>

<p>
Im Log werden die von WebUntis zurückgegebenen Werte angezeigt:
</p>

<pre><code>
2026-11-23 11:55:18 [INFO] Login erfolgreich für 'Kind 1'
(personType=5, personId=10188)

2026-11-23 11:55:20 [INFO] Login erfolgreich für 'Kind 2'
(personType=5, personId=10254)

2026-11-23 11:55:21 [INFO] Login erfolgreich für 'Kind 3'
(personType=12, personId=7542)
</code></pre>

<h4>Bedeutung der Werte</h4>

<table>
<tr>
<th>Wert</th>
<th>Bedeutung</th>
</tr>
<tr>
<td><code>personType=5</code></td>
<td>Schülerkonto</td>
</tr>
<tr>
<td><code>personType≠5</code></td>
<td>z.&nbsp;B. Elternkonto oder anderer Kontotyp</td>
</tr>
<tr>
<td><code>personId</code></td>
<td>Interne WebUntis-ID des angemeldeten Benutzers</td>
</tr>
</table>

<h4>Normale Schülerkonten</h4>

<p>
Bei Schülerkonten (<code>personType=5</code>) wird die Schüler-ID
automatisch verwendet. Eine Konfiguration wie diese genügt:
</p>

<pre><code>{
  "name": "Beispiel Kind",
  "slug": "beispiel-kind",
  "username": "USERNAME",
  "password": "PASSWORD"
}</code></pre>

<p>
Das Skript verwendet automatisch:
</p>

<pre><code>
personType = 5
personId   = 10188
</code></pre>

<h4>Elternkonten oder Sonderfälle</h4>

<p>
Falls WebUntis keinen Schüler direkt anmeldet (z.&nbsp;B. Elternkonto),
kann ein bestimmtes Kind oder eine Klasse explizit angegeben werden.
</p>

<pre><code>{
  "name": "Beispiel Kind",
  "slug": "beispiel-kind",
  "server": "andere-schule.webuntis.com",
  "username": "USERNAME",
  "password": "PASSWORD",
  "element_type": 5,
  "element_id": 12345
}</code></pre>

<h4>Praxisbeispiel</h4>

<p>
Im folgenden Beispiel wurde kein Schülerkonto erkannt:
</p>

<pre><code>
Login erfolgreich für 'Beispiel Kind'
(personType=12, personId=7542)

Rufe Timetable ab für 'Beispiel Kind'
(element.id=511, element.type=1)
</code></pre>

<p>
Daher wird die automatische Zuordnung durch folgende Konfiguration
überschrieben:
</p>

<pre><code>{
  "element_type": 1,
  "element_id": 511
}</code></pre>

<p>
Damit wird gezielt das gewünschte WebUntis-Objekt abgefragt,
anstatt die automatisch erkannte Person-ID zu verwenden.
</p>

<p>
<strong>Hinweis:</strong> Für die meisten Nutzer werden
<code>element_type</code> und <code>element_id</code> nicht benötigt.
Das Skript funktioniert in der Regel ohne diese Angaben.
</p>
<h3>Zeitraumsteuerung</h3>

<pre><code>{
  "include_weeks_back": 6,
  "weeks_ahead": 12
}</code></pre>

<h3>Prüfungen</h3>

<p>Verwendeter Endpunkt:</p>

<pre><code>/api/exams</code></pre>

<ul>
<li>Kein einschränkender <code>studentId</code>-Filter</li>
<li>Vollständige Prüfungsliste des jeweiligen Schülers</li>
<li>403 Forbidden wird lediglich als DEBUG protokolliert</li>
</ul>

<hr>

<h2>⏰ Automatischer Betrieb</h2>

<h3>Cronjob</h3>

<pre><code>*/20 * * * * PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json python3 -u /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&amp;1
</code></pre>

<hr>

<h2>📊 Logging &amp; Monitoring</h2>

<h3>Letzte Logeinträge</h3>

<pre><code>tail -n 30 /opt/untis-ical/untis-ical.log</code></pre>

<h3>Anzahl exportierter Termine</h3>

<pre><code>grep -c "BEGIN:VEVENT" /var/www/html/untis/*.ics</code></pre>

<h3>Apache-Erreichbarkeit</h3>

<pre><code>curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1/untis/</code></pre>

<hr>

<h2>🖥️ Web-Dashboard</h2>

<p>
Die Weboberfläche lädt ihre Daten dynamisch aus
<code>children.json</code> und den jeweiligen ICS-Dateien.
</p>

<h3>Funktionen</h3>

<h4>Kind-Auswahl</h4>

<ul>
<li>Wechsel zwischen mehreren Kindern</li>
<li>Dynamische Profilumschaltung</li>
</ul>

<h4>Wochen-Navigation</h4>

<ul>
<li>Vorherige Woche</li>
<li>Aktuelle Woche</li>
<li>Nächste Woche</li>
</ul>

<h4>Stundenplan-Grid</h4>

<ul>
<li>Unterricht</li>
<li>Vertretungen</li>
<li>Ausfälle</li>
<li>Prüfungen</li>
</ul>

<p>Prüfungen werden aus:</p>

<pre><code>&lt;slug&gt;_pruefungen.ics</code></pre>

<p>automatisch übernommen.</p>

<hr>

<h3>Zusatzbereiche</h3>

<h4>Prüfungen</h4>
<p>Wochenübersicht aller Prüfungen.</p>

<h4>Hausaufgaben</h4>
<p>Übersicht aller fälligen Aufgaben.</p>

<h4>Mitteilungen</h4>
<p>Anzeige aktueller Mitteilungen inklusive Umschalter für sämtliche Meldungen.</p>

<hr>

<h2>📲 Kalender-Abonnement</h2>

<p>Bereitgestellter Feed:</p>

<pre><code>/untis/&lt;slug&gt;_alle.ics</code></pre>

<ul>
<li>Kalender herunterladen</li>
<li>Kalender direkt öffnen</li>
<li>Kalender abonnieren</li>
<li>Abo-URL kopieren</li>
</ul>

<hr>

<h2>🔄 Ablauf</h2>

<pre><code>
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
</code></pre>

<hr>

<h2>🔐 Sicherheit</h2>

<ul>
<li>Zugangsdaten verbleiben ausschließlich in <code>config.json</code></li>
<li><code>children.json</code> enthält keine Zugangsdaten</li>
<li>Öffentlich bereitgestellt werden nur Kalenderdaten und Profilinformationen</li>
<li>HTTPS wird empfohlen</li>
</ul>

<hr>

<h2>📅 Google Kalender Synchronisierung</h2>

<p>
Optional können die erzeugten WebUntis-Kalender automatisch mit
Google Kalender synchronisiert werden.
</p>

<p>
Dies ist insbesondere für Dienste sinnvoll, die keine lokalen oder
nicht öffentlich erreichbaren ICS-Dateien unterstützen.
</p>

<p>
Beispielsweise:
</p>

<ul>
<li>Daely</li>
<li>Google Kalender</li>
<li>Google Nest Hub</li>
<li>Google Assistant</li>
<li>Android Kalender</li>
<li>Familien-Dashboards</li>
</ul>

<hr>

<h3>🔄 Architektur</h3>

<pre><code>
WebUntis
    │
    ▼
untis_to_ical.py
    │
    ▼
*_alle.ics
    │
    ▼
google_calendar_sync.py
    │
    ▼
Google Kalender

WebUntis - Kind 1
WebUntis - Kind 2
WebUntis - Kind 3

    │
    ▼
Daely
</code></pre>

<hr>

<h3>📂 Benötigte Dateien</h3>

<table>
<tr>
<th>Datei</th>
<th>Beschreibung</th>
</tr>

<tr>
<td><code>google_calendar_sync.py</code></td>
<td>Google Kalender Synchronisation</td>
</tr>

<tr>
<td><code>google_sync.json</code></td>
<td>Google Konfiguration</td>
</tr>

<tr>
<td><code>service-account.json</code></td>
<td>Google Service Account Schlüssel</td>
</tr>

<tr>
<td><code>children.json</code></td>
<td>Profilinformationen der Kinder</td>
</tr>

<tr>
<td><code>*_alle.ics</code></td>
<td>Kombinierte Kalenderdateien</td>
</tr>

</table>

<hr>

<h3>⚙️ Konfiguration</h3>

<p>
Beispiel für <code>google_sync.json</code>:
</p>

<pre><code>{
  "google": {
    "service_account_file": "service-account.json",
    "delete_missing": true,
    "timezone": "Europe/Berlin"
  }
}</code></pre>

<hr>

<h3>🔑 Google Service Account</h3>

<p>
Für die Synchronisierung wird ein Google Service Account verwendet.
Dadurch sind keine Browser-Anmeldung, OAuth-Dialoge oder Benutzer-Tokens erforderlich.
</p>

<p>
Erforderliche Schritte:
</p>

<ol>
<li>Google Cloud Projekt erstellen</li>
<li>Google Calendar API aktivieren</li>
<li>Service Account erstellen</li>
<li>JSON-Schlüssel herunterladen</li>
<li>Datei als <code>service-account.json</code> speichern</li>
<li>Google Kalender für den Service Account freigeben</li>
</ol>

<hr>

<h3>📆 Kalenderstruktur</h3>

<p>
Für jedes Kind wird automatisch ein eigener Google Kalender verwendet:
</p>

<ul>
<li><code>WebUntis - Kind 1</code></li>
<li><code>WebUntis - Kind 2</code></li>
<li><code>WebUntis - Kind 3</code></li>
</ul>

<p>
Empfohlen wird eine eigene Farbe pro Kind:
</p>

<table>
<tr>
<th>Kalender</th>
<th>Beispiel-Farbe</th>
</tr>

<tr>
<td>WebUntis - Kind 1</td>
<td>Blau</td>
</tr>

<tr>
<td>WebUntis - Kind 2</td>
<td>Grün</td>
</tr>

<tr>
<td>WebUntis - Kind 3</td>
<td>Lila</td>
</tr>
</table>

<hr>

<h3>📖 Synchronisierte Inhalte</h3>

<p>
Die Google Kalender enthalten alle Einträge aus den jeweiligen
<code>*_alle.ics</code>-Dateien:
</p>

<ul>
<li>Stundenplan</li>
<li>Hausaufgaben</li>
<li>Mitteilungen</li>
<li>Prüfungen</li>
</ul>

<hr>

<h3>⏱ Rate-Limit Schutz</h3>

<p>
Das Synchronisationsskript verwendet automatische Wiederholungen
(Exponential Backoff) bei Google API Rate-Limits.
</p>

<p>
Zusätzlich werden API-Aufrufe künstlich gedrosselt, um die
Google Calendar API nicht zu überlasten.
</p>

<hr>

<h3>🕒 Automatische Ausführung</h3>

<p>
Beispiel-Cronjob:
</p>

<pre><code>
*/20 * * * * /opt/untis-ical/venv/bin/python /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1

*/25 * * * * /opt/untis-ical/venv/bin/python /opt/untis-ical/google_calendar_sync.py >> /opt/untis-ical/google-sync.log 2>&1
</code></pre>

<p>
Dadurch werden zunächst die WebUntis-Daten aktualisiert und
anschließend automatisch nach Google Kalender synchronisiert.
</p>

<hr>

<h3>🔒 Sicherheit</h3>

<p>
Folgende Dateien dürfen nicht veröffentlicht werden:
</p>

<ul>
<li><code>service-account.json</code></li>
<li><code>config.json</code></li>
<li><code>children.json</code></li>
</ul>

<p>
Empfohlene Ergänzung für <code>.gitignore</code>:
</p>

<pre><code>
service-account.json
config.json
children.json

*.ics
*.log
</code></pre>
<hr>
<h2>📄 Lizenz</h2>

<p>
Dieses Projekt wird ohne Gewähr bereitgestellt.
</p>

<p>
Die Nutzung erfolgt auf eigene Verantwortung.
</p>

<p>
Bitte die Datenschutzrichtlinien der jeweiligen Schule sowie
die Nutzungsbedingungen von WebUntis beachten.
</p>****
