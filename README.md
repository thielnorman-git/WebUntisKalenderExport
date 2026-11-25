<h1>WebUntisKalenderExport</h1>

<p><strong>ICS-Export als Wochenplan für Familien und Eltern</strong></p>

<h2>WebUntis iCal-Exporter &amp; Dashboard (v1.0.0)</h2>

<p>
Exportiert Stundenpläne, Hausaufgaben, Mitteilungen und Prüfungen aus WebUntis
über ein Python-Skript in <code>.ics</code>-Kalenderdateien.
</p>

<p>
Zusätzlich werden kombinierte Kalenderfeeds
(<code>*_alle.ics</code>) erzeugt und optional über Apache oder Nginx zusammen mit einem
Web-Dashboard unter <code>/untis/</code> bereitgestellt. Hauptziel für Dienste wie
<strong>Daely</strong> ist der automatische Sync in den Google Kalender.
</p>

<hr>
<img width="800" height="1314" alt="image" src="https://github.com/user-attachments/assets/bbadbcf7-59b0-4beb-bc9d-080af195096f" />

<h2>🚀 Features</h2>

<ul>
<li>Export von Stundenplänen (inkl. klarer Titel-Tags wie <code>[ENTFALL]</code>, <code>[VERTRETUNG]</code>, <code>[HA]</code>, <code>[PRÜFUNG]</code>, <code>[NEU]</code>)</li>
<li>Export von Hausaufgaben</li>
<li>Export von Mitteilungen</li>
<li>Export von Prüfungen (falls verfügbar)</li>
<li>Erzeugung kombinierter Kalenderfeeds (<code>*_alle.ics</code>)</li>
<li>Unterstützung mehrerer Schulen und WebUntis-Instanzen</li>
<li>Automatische Aktualisierung per Cronjob</li>
<li>Optionales Web-Dashboard mit Wochenansicht</li>
<li>Google-Kalender-Synchronisierung (empfohlen für Daely)</li>
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
<td>WebUntis Exporter und ICS-Erzeugung</td>
</tr>

<tr>
<td><code>/opt/untis-ical/google_calendar_sync.py</code></td>
<td>Google Kalender Synchronisierung</td>
</tr>

<tr>
<td><code>/opt/untis-ical/config.json</code></td>
<td>WebUntis Konfiguration (Server, Zeitraum, Profile)</td>
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
<td>Optionales Dashboard</td>
</tr>

<tr>
<td><code>/var/www/html/untis/children.json</code></td>
<td>Öffentliche Profilliste für das Dashboard</td>
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
sudo mkdir -p /opt/untis-ical /var/www/html/untis
sudo chown -R "$USER":"$USER" /opt/untis-ical /var/www/html/untis

git clone https://github.com/thielnorman-git/WebUntisKalenderExport.git /opt/untis-ical
cd /opt/untis-ical

python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

cp config.example.json config.json
./venv/bin/python3 untis_to_ical.py
</code></pre>

<hr>

<h2>⚙️ Voraussetzungen</h2>

<ul>
<li>Python 3.10 oder neuer (mit virtueller Umgebung <code>venv</code>)</li>
<li><code>requests</code>, <code>icalendar</code>, <code>pytz</code></li>
<li><code>google-api-python-client</code> und <code>google-auth</code> (für Google Kalender Sync)</li>
<li>Apache oder Nginx (optional für Web-Dashboard und ICS-Auslieferung)</li>
</ul>

<hr>

<h2>🔧 Konfiguration</h2>

<p>
Die Hauptkonfiguration liegt unter:
</p>

<pre><code>/opt/untis-ical/config.json</code></pre>

<h3>Unterstützte Profiltypen</h3>

<h4>children</h4>

<p>Normale Schülerprofile auf der Haupt-WebUntis-Instanz.</p>

<h4>children_other_school</h4>

<p>Profile auf anderen WebUntis-Instanzen, zum Beispiel:</p>

<ul>
<li><code>schule.webuntis.com</code></li>
<li><code>andere-schule.webuntis.com</code></li>
</ul>

<h3>🔍 Automatische Erkennung der Schüler-ID</h3>

<p>
In den meisten Fällen werden <code>element_type</code> und <code>element_id</code>
nicht benötigt. Das Skript erkennt die Werte automatisch über den Login.
</p>

<pre><code>
2026-11-23 11:55:18 [INFO] Login erfolgreich für 'Kind 1' (personType=5, personId=10188)
2026-11-23 11:55:20 [INFO] Login erfolgreich für 'Kind 2' (personType=5, personId=10254)
2026-11-23 11:55:21 [INFO] Login erfolgreich für 'Kind 3' (personType=12, personId=7542)
</code></pre>

<h3>Zeitraumsteuerung</h3>

<pre><code>{
  "include_weeks_back": 6,
  "weeks_ahead": 12
}</code></pre>

<hr>

<h2>📅 Google Kalender Synchronisierung</h2>

<p>
Optional und für <strong>Daely</strong> empfohlen: Die erzeugten Kalenderdaten werden
automatisch in Google Kalender synchronisiert, damit Daely keine lokalen oder
nicht öffentlich erreichbaren <code>.ics</code>-Dateien abrufen muss.
</p>

<h3>🔄 Ablauf</h3>

<ol>
<li><code>untis_to_ical.py</code> liest WebUntis aus und schreibt die <code>.ics</code>-Dateien (inkl. <code>*_alle.ics</code>).</li>
<li><code>google_calendar_sync.py</code> synchronisiert die Einträge in die jeweiligen Google Kalender (<code>WebUntis - Kind 1</code> usw.).</li>
<li><strong>Daely</strong> bindet diese Google Kalender direkt ein.</li>
</ol>

<h3>📂 Benötigte Dateien</h3>

<table>
<tr>
<th>Datei / Pfad</th>
<th>Beschreibung</th>
</tr>

<tr>
<td><code>/opt/untis-ical/google_calendar_sync.py</code></td>
<td>Google Kalender Synchronisierung</td>
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
<td><code>/var/www/html/untis/*_alle.ics</code></td>
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
Das Projekt verwendet einen Google Service Account. Es werden keine interaktiven
Browser-Logins im Cronjob benötigt.
</p>

<ol>
<li>Google Cloud Projekt erstellen</li>
<li>Google Calendar API aktivieren</li>
<li>Service Account erstellen</li>
<li>JSON-Schlüssel herunterladen</li>
<li>Als <code>/opt/untis-ical/service-account.json</code> speichern</li>
<li>Die Ziel-Google-Kalender für die E-Mail-Adresse des Service Accounts mit Änderungsrechten freigeben</li>
</ol>

<h3>📆 Kalenderstruktur</h3>

<p>
Für jedes Kind wird ein eigener Google Kalender genutzt bzw. angelegt:
</p>

<ul>
<li><code>WebUntis - Kind 1</code></li>
<li><code>WebUntis - Kind 2</code></li>
<li><code>WebUntis - Kind 3</code></li>
</ul>

<p>
Empfohlene Farbcodierung im Google Kalender:
</p>

<table>
<tr>
<th>Kalender</th>
<th>Empfohlene Farbe</th>
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
Das Synchronisationsskript nutzt automatisches Exponential Backoff bei
Google-API-Rate-Limits und drosselt Anfragen, um Kontingente zu schonen.
</p>

<h3>🕒 Cronjob</h3>

<pre><code>
# 1. Schnell-Befehl via SSH (setzt/aktualisiert den Job und erhält andere Einträge)
{ crontab -l 2>/dev/null | grep -vE 'untis_to_ical\.py|google_calendar_sync\.py'; echo '*/20 * * * * cd /opt/untis-ical && PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json /opt/untis-ical/venv/bin/python3 -u /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1 && PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json /opt/untis-ical/venv/bin/python3 -u /opt/untis-ical/google_calendar_sync.py >> /opt/untis-ical/google-sync.log 2>&1'; } | crontab -

# 2. Reine Zeile für crontab -e (alle 20 Minuten: erst iCal-Export, dann Google-Sync)
*/20 * * * * cd /opt/untis-ical && PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json /opt/untis-ical/venv/bin/python3 -u /opt/untis-ical/untis_to_ical.py >> /opt/untis-ical/untis-ical.log 2>&1 && PYTHONPATH=/opt/untis-ical UNTIS_ICAL_CONFIG=/opt/untis-ical/config.json /opt/untis-ical/venv/bin/python3 -u /opt/untis-ical/google_calendar_sync.py >> /opt/untis-ical/google-sync.log 2>&1
</code></pre>

<h3>📱 Daely Integration</h3>

<p>
Die Google Kalender können direkt in Daely eingebunden werden. Ein öffentlich
erreichbarer ICS-Feed wird dafür nicht benötigt.
</p>

<hr>

<h2>🖥️ Web-Dashboard (Optional)</h2>

<p>
Das optionale Web-Dashboard lädt die Daten dynamisch aus
<code>/var/www/html/untis/children.json</code> und den erzeugten ICS-Dateien.
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
Folgende Dateien enthalten Zugangsdaten, Schlüssel oder personenbezogene Daten und
dürfen niemals veröffentlicht werden:
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

<h2>📄 Lizenz &amp; Hinweise</h2>

<p>
Bitte die Datenschutzrichtlinien der jeweiligen Schule sowie
die Nutzungsbedingungen von WebUntis beachten.
</p>

<pre><code>
MIT License

Copyright (c) 2026 Norman Thiel

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
</code></pre>
