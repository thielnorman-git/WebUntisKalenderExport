#!/usr/bin/env python3

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from icalendar import Calendar
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

UNTIS_DIR = Path("/var/www/html/untis")

CONFIG_FILE = Path(
    "/opt/untis-ical/google_sync.json"
)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

GOOGLE_CFG = CONFIG["google"]

SERVICE_ACCOUNT_FILE = GOOGLE_CFG["service_account_file"]

DELETE_MISSING = GOOGLE_CFG.get(
    "delete_missing",
    True
)

TIMEZONE = GOOGLE_CFG.get(
    "timezone",
    "Europe/Berlin"
)

CALENDAR_PREFIX = "WebUntis - "

GOOGLE_OWNER = GOOGLE_CFG.get("owner", "").strip()


def execute_with_retry(
    request,
    description=""
):

    max_retries = 8

    for attempt in range(max_retries):

        try:

            result = request.execute()

            time.sleep(0.15)

            return result

        except HttpError as exc:

            if (
                getattr(exc, "resp", None)
                and exc.resp.status == 403
                and "rateLimitExceeded" in str(exc)
            ):

                wait_seconds = min(
                    30,
                    2 ** attempt
                )

                print(
                    f"RATE LIMIT: {description} | Warte {wait_seconds}s ..."
                )

                time.sleep(wait_seconds)

                continue

            raise

    raise RuntimeError(
        f"Zu viele Rate-Limit Fehler: {description}"
    )


def get_google_service():

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def get_or_create_calendar(
    service,
    child_name
):

    calendar_name = (
        f"{CALENDAR_PREFIX}{child_name}"
    )

    page_token = None

    while True:

        result = execute_with_retry(
            service.calendarList().list(
                pageToken=page_token
            ),
            "calendar-list"
        )

        for cal in result.get("items", []):

            if cal.get("summary") == calendar_name:

                return cal["id"]

        page_token = result.get(
            "nextPageToken"
        )

        if not page_token:
            break

    print(
        f"Erstelle Kalender: {calendar_name}"
    )

    created = execute_with_retry(
        service.calendars().insert(
            body={
                "summary": calendar_name,
                "timeZone": TIMEZONE
            }
        ),
        f"create-calendar-{child_name}"
    )

    calendar_id = created["id"]

    try:

        if GOOGLE_OWNER:
            execute_with_retry(
                service.acl().insert(
                    calendarId=calendar_id,
                    body={
                        "role": "owner",
                        "scope": {
                            "type": "user",
                            "value": GOOGLE_OWNER
                        }
                    }
                ),
                f"acl-create-{child_name}"
            )

            print(
                f"Freigabe erstellt fuer {GOOGLE_OWNER}"
            )

    except Exception as exc:

        print(
            f"ACL Fehler: {exc}"
        )

    return calendar_id


def ensure_calendar_shared(
    service,
    calendar_id
):

    if not GOOGLE_OWNER:
        return

    try:

        acl = execute_with_retry(
            service.acl().list(
                calendarId=calendar_id
            ),
            f"acl-list-{calendar_id}"
        )

        already_exists = False

        for item in acl.get("items", []):

            scope = item.get(
                "scope",
                {}
            )

            if (
                scope.get("type") == "user"
                and scope.get("value") == GOOGLE_OWNER
            ):
                already_exists = True
                break

        if not already_exists:

            execute_with_retry(
                service.acl().insert(
                    calendarId=calendar_id,
                    body={
                        "role": "owner",
                        "scope": {
                            "type": "user",
                            "value": GOOGLE_OWNER
                        }
                    }
                ),
                f"acl-insert-{calendar_id}"
            )

            print(
                f"Freigabe nachgezogen fuer {GOOGLE_OWNER}"
            )

    except Exception as exc:

        print(
            f"ACL Fehler: {exc}"
        )


def parse_ics(path):

    with open(path, "rb") as f:

        cal = Calendar.from_ical(
            f.read()
        )

    events = {}

    for component in cal.walk():

        if component.name != "VEVENT":
            continue

        uid = str(
            component.get("UID", "")
        ).strip()

        if not uid:
            continue

        events[uid] = component

    return events


def build_google_event(event):

    start = event.decoded("DTSTART")
    end = event.decoded("DTEND")

    summary = str(
        event.get("SUMMARY", "")
    ).strip()

    summary_upper = summary.upper()

    body = {
        "summary": summary,
        "description": str(
            event.get("DESCRIPTION", "")
        ),
        "location": str(
            event.get("LOCATION", "")
        )
    }

    #
    # Event-Farben
    #
    if summary_upper.startswith("[PRÜFUNG]"):

        body["colorId"] = "5"   # Gelb

    elif summary.startswith("[HA]"):

        body["colorId"] = "10"  # Grün

    elif summary_upper.startswith("[INFO]"):

        body["colorId"] = "3"   # Lila

    elif summary_upper.startswith("[ENTFALL]"):

        body["colorId"] = "11"  # Rot

    if hasattr(start, "hour"):

        body["start"] = {
            "dateTime": start.isoformat(),
            "timeZone": TIMEZONE
        }

        body["end"] = {
            "dateTime": end.isoformat(),
            "timeZone": TIMEZONE
        }

    else:

        body["start"] = {
            "date": start.isoformat()
        }

        body["end"] = {
            "date": end.isoformat()
        }

    return body


def load_google_events(
    service,
    calendar_id
):

    events = {}

    page_token = None

    while True:

        result = execute_with_retry(
            service.events().list(
                calendarId=calendar_id,
                pageToken=page_token,
                showDeleted=False
            ),
            f"load-events-{calendar_id}"
        )

        for event in result.get("items", []):

            if "id" in event:
                events[event["id"]] = event

        page_token = result.get(
            "nextPageToken"
        )

        if not page_token:
            break

    return events


def cleanup_removed_events(
    service,
    calendar_id,
    google_events,
    active_google_ids
):

    if not DELETE_MISSING:
        return

    for google_id in google_events:

        if google_id not in active_google_ids:

            try:

                execute_with_retry(
                    service.events().delete(
                        calendarId=calendar_id,
                        eventId=google_id
                    ),
                    f"delete-{google_id}"
                )

                print(
                    f"DELETE: {google_id}"
                )

            except Exception as exc:

                print(
                    f"DELETE FEHLER: {google_id} -> {exc}"
                )


def sync_child_calendar(
    service,
    child_name,
    ics_path
):

    print(
        f"\nSynchronisiere: {child_name}"
    )

    calendar_id = get_or_create_calendar(
        service,
        child_name
    )

    ensure_calendar_shared(
        service,
        calendar_id
    )

    google_events = load_google_events(
        service,
        calendar_id
    )

    active_google_ids = set()

    ics_events = parse_ics(
        ics_path
    )

    sync_delay = 0.20

    for uid, event in ics_events.items():

        summary = str(
            event.get("SUMMARY", "")
        ).strip()

        summary_upper = summary.upper()

        event_prefix = "lesson"

        if summary_upper.startswith("[HA]"):
            event_prefix = "ha"

        elif summary_upper.startswith("[INFO]"):
            event_prefix = "info"

        elif summary_upper.startswith("[PRÜFUNG]"):
            event_prefix = "exam"

        elif summary_upper.startswith("[ENTFALL]"):
            event_prefix = "cancelled"

        #
        # Google Event IDs dürfen nur bestimmte Zeichen enthalten.
        # Deshalb wird eine SHA1-ID erzeugt.
        #
        raw_id = (
            f"{child_name}-"
            f"{event_prefix}-"
            f"{uid}"
        )

        google_id = hashlib.sha1(
            raw_id.encode("utf-8")
        ).hexdigest()

        active_google_ids.add(
            google_id
        )

        body = build_google_event(
            event
        )

        try:

            if google_id in google_events:

                execute_with_retry(
                    service.events().update(
                        calendarId=calendar_id,
                        eventId=google_id,
                        body=body
                    ),
                    f"update-{google_id}"
                )

                print(
                    f"UPDATE: {body['summary']}"
                )

                time.sleep(sync_delay)

            else:

                body["id"] = google_id

                execute_with_retry(
                    service.events().insert(
                        calendarId=calendar_id,
                        body=body
                    ),
                    f"insert-{google_id}"
                )

                print(
                    f"CREATE: {body['summary']}"
                )

                time.sleep(sync_delay)

        except Exception as exc:

            print(
                f"FEHLER: {body['summary']} -> {exc}"
            )

    cleanup_removed_events(
        service,
        calendar_id,
        google_events,
        active_google_ids
    )


def main():

    children_file = (
        UNTIS_DIR /
        "children.json"
    )

    if not children_file.exists():

        raise FileNotFoundError(
            f"{children_file} nicht gefunden"
        )

    with open(
        children_file,
        "r",
        encoding="utf-8"
    ) as f:

        children = json.load(f)

    service = get_google_service()

    for child in children:

        slug = child["slug"]
        child_name = child["name"]

        ics_path = (
            UNTIS_DIR /
            f"{slug}_alle.ics"
        )

        if not ics_path.exists():

            print(
                f"Ueberspringe: {slug}"
            )

            continue

        sync_child_calendar(
            service,
            child_name,
            ics_path
        )

    print(
        "\nGoogle Kalender Synchronisierung abgeschlossen."
    )


if __name__ == "__main__":
    main()