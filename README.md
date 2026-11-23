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
<li>Google-Kalender-Synchronisierung</li>
<li>Kalender-Abonnement für Outlook, Apple Kalender, Google Kalender und Smartphones</li>
<li>Daely-Integration über Google Kalender</li>
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
<td>WebUntis Exporter und ICS-Erzeugung</td>
</tr>

<tr>
<td><code>/opt/untis-ical/google_calendar_sync.py</code></td>
<td>Google Kalender Synchronisierung</td>
</tr>

<tr>
<td><code>/opt/untis-ical/config.json</code></td>
<td>WebUntis Konfiguration</td>
</tr>

<tr>
<td><code>/opt/untis-ical/google_sync.json</code></td>
<td>Google Synchronisierungskonfiguration</td>
</tr>

<tr>
<td><code>/opt/untis-ical/service-account.json</code></td>
<td>Google Service Account Schlüssel</td>
</tr>

<tr>
<td><code>/opt/untis-ical/untis-ical.log</code></td>
<td>WebUntis Export Log</td>
</tr>

<tr>
<td><code>/opt/untis-ical/google-sync.log</code></td>
<td>Google Sync Log</td>
</tr>

<tr>
<td><code>/var/www/html/untis/index.html</code></td>
<td>Dashboard</td>
</tr>

<tr>
<td><code>/var/www/html/untis/children.json</code></td>
<td>Öffentliche Profilliste</td>
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
<td>Kombinierter Kalender</td>
</tr>

</table>

<hr>

<h2>🚀 Quick Start</h2>

<pre><code>
git clone https://github.com/thielnorman-git/WebUntisKalenderExport.git

cd WebUntisKalenderExport

pip install -r requirements.txt

cp config.example.json config.json

python3 untis_to_ical.py
</code></pre>

<hr>

<h2>⚙️ Voraussetzungen</h2>

<ul>
<li>Python 3.10 oder neuer</li>
<li>requests</li>
<li>icalendar</li>
<li>pytz</li>
<li>google-api-python-client (optional für Google Sync)</li>
<li>google-auth (optional für Google Sync)</li>
<li>Apache oder Nginx (optional für Dashboard)</li>
</ul>

<hr>

<h2>🔧 Konfiguration</h2>

<p>
Die Konfiguration erfolgt über:
</p>

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

<h3>🔍 Automatische Erkennung der Schüler-ID</h3>

<p>
In den meisten Fällen werden
<code>element_type</code>
und
<code>element_id</code>
nicht benötigt.
</p>

<p>
Das Skript erkennt die Werte automatisch über den Login.
</p>

<pre><code>
2026-11-23 11:55:18 [INFO] Login erfolgreich für 'Kind 1'
(personType=5, personId=10188)

2026-11-23 11:55:20 [INFO] Login erfolgreich für 'Kind 2'
(personType=5, personId=10254)

2026-11-23 11:55:21 [INFO] Login erfolgreich für 'Kind 3'
(personType=12, personId=7542)
</code></pre>

<h3>Zeitraumsteuerung</h3>

<pre><code>{
  "include_weeks_back": 6,
  "weeks_ahead": 12
}</code></pre>

<hr>

<h2>📅 Google Kalender Synchronisierung</h2>

<p>
Optional können die erzeugten WebUntis-Kalender automatisch
mit Google Kalender synchronisiert werden.
</p>

<p>
Dies ist insbesondere für Dienste wie Daely relevant,
welche keine lokalen oder nicht öffentlich erreichbaren
ICS-Dateien verarbeiten können.
</p>

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

<h3>📂 Benötigte Dateien</h3>

<table>
<tr>
<th>Datei</th>
<th>Beschreibung</th>
</tr>

<tr>
<td><code>google_calendar_sync.py</code></td>
<td>Google Kalender Synchronisierung</td>
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
<td>Kindprofile</td>
</tr>

<tr>
<td><code>*_alle.ics</code></td>
<td>Kombinierte Kalenderdateien</td>
</tr>

</table>

<h3>⚙️ Beispielkonfiguration</h3>

<pre><code>{
  "google": {
    "service_account_file": "service-account.json",
    "delete_missing": true,
    "timezone": "Europe/Berlin"
  }
}</code></pre>

<h3>🔑 Google Service Account</h3>

<p>
Das Projekt verwendet einen Google Service Account.
Es werden keine Browser-Anmeldungen, Tokens oder OAuth-Dialoge benötigt.
</p>

<ol>
<li>Google Cloud Projekt erstellen</li>
<li>Google Calendar API aktivieren</li>
<li>Service Account erstellen</li>
<li>JSON-Schlüssel herunterladen</li>
<li>Als <code>service-account.json</code> speichern</li>
<li>Google Kalender für den Service Account freigeben</li>
</ol>

<h3>📆 Kalenderstruktur</h3>

<p>
Für jedes Kind wird automatisch ein eigener Google Kalender erzeugt:
</p>

<ul>
<li><code>WebUntis - Kind 1</code></li>
<li><code>WebUntis - Kind 2</code></li>
<li><code>WebUntis - Kind 3</code></li>
</ul>

<p>
Empfehlung:
</p>

<table>
<tr>
<th>Kalender</th>
<th>Farbe</th>
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

<h3>📖 Synchronisierte Inhalte</h3>

<ul>
<li>Stundenplan</li>
<li>Hausaufgaben</li>
<li>Mitteilungen</li>
<li>Prüfungen</li>
</ul>

<h3>⏱ Rate-Limit Schutz</h3>

<p>
Das Synchronisationsskript verwendet automatisches Exponential Backoff
bei Google API Rate-Limits.
</p>

<p>
Zusätzlich werden API-Aufrufe künstlich gedrosselt, um die
Google Calendar API nicht zu überlasten.
</p>

<h3>🕒 Cronjob</h3>

<pre><code>
*/20 * * * * /opt/untis-ical/venv/bin/python /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1

*/25 * * * * /opt/untis-ical/venv/bin/python /opt/untis-ical/google_calendar_sync.py >> /opt/untis-ical/google-sync.log 2>&1
</code></pre>

<h3>📱 Daely Integration</h3>

<p>
Die Google Kalender können direkt in Daely eingebunden werden.
</p>

<p>
Damit wird kein öffentlich erreichbarer ICS-Feed benötigt.
</p>

<hr>

<h2>🖥️ Web-Dashboard</h2>

<p>
Das Dashboard lädt die Daten dynamisch aus
<code>children.json</code>
und den jeweiligen ICS-Dateien.
</p>

<ul>
<li>Kinderauswahl</li>
<li>Wochennavigation</li>
<li>Stundenplan</li>
<li>Hausaufgaben</li>
<li>Mitteilungen</li>
<li>Prüfungen</li>
<li>Kalender-Links</li>
</ul>

<hr>

<h2>🔐 Sicherheit</h2>

<p>
Folgende Dateien dürfen niemals veröffentlicht werden:
</p>

<ul>
<li><code>service-account.json</code></li>
<li><code>google_sync.json</code></li>
<li><code>config.json</code></li>
<li><code>children.json</code></li>
</ul>

<p>
Empfohlene <code>.gitignore</code>:
</p>

<pre><code>
service-account.json

google_sync.json

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
</p>
