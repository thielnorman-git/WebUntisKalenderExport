#!/usr/bin/env python3

from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "service-account.json"

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

CALENDAR_PREFIX = "WebUntis - "

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

service = build(
    "calendar",
    "v3",
    credentials=creds
)

print("\nSuche nach vorhandenen WebUntis-Kalendern ...")

result = service.calendarList().list().execute()

found = False

for cal in result.get("items", []):

    name = cal.get("summary", "")
    calendar_id = cal.get("id", "")

    if not name.startswith(CALENDAR_PREFIX):
        continue

    found = True

    print(f"\nLoesche Kalender:")
    print(f"Name: {name}")
    print(f"ID: {calendar_id}")

    try:

        service.calendars().delete(
            calendarId=calendar_id
        ).execute()

        print("OK")

    except Exception as exc:

        print(f"FEHLER: {exc}")

if not found:

    print("\nKeine WebUntis-Kalender gefunden.")

else:

    print("\nAlle WebUntis-Kalender wurden geloescht.")