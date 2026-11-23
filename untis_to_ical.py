#!/usr/bin/env python3
"""
Holt Stundenplan-, Hausaufgaben- und Mitteilungsdaten aus WebUntis
(JSON-RPC + REST homeworks/lessons + REST messages) für mehrere Accounts
und erzeugt jeweils eigene .ics-Kalenderdateien sowie eine children.json.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

import pytz
import requests
from icalendar import Calendar, Event


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("untis_to_ical")


class WebUntisRpcError(RuntimeError):
    """Fehler bei der Kommunikation mit dem WebUntis JSON-RPC-Endpunkt."""


class WebUntisClient:
    """Kleiner JSON-RPC- und REST-Client für WebUntis-Instanzen."""

    def __init__(self, server: str, user_agent: str = "UntisIcalExporter/1.0", timeout: int = 20) -> None:
        self.host = server.replace("https://", "").replace("http://", "").strip("/")
        self.base_url = f"https://{self.host}/WebUntis"
        self.url = f"{self.base_url}/jsonrpc.do"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Content-Type": "application/json",
            }
        )
        self._req_id = 0

    def _next_id(self) -> str:
        self._req_id += 1
        return f"req-{self._req_id}"

    def call(self, method: str, params: dict[str, Any] | None = None) -> Any:
        payload = {
            "id": self._next_id(),
            "method": method,
            "params": params or {},
            "jsonrpc": "2.0",
        }
        response = self.session.post(self.url, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        if "error" in data and data["error"]:
            err = data["error"]
            raise WebUntisRpcError(f"JSON-RPC Fehler bei '{method}': {err.get('message')} (Code {err.get('code')})")
        return data.get("result")

    def login(self, username: str, password: str) -> dict[str, Any]:
        result = self.call(
            "authenticate",
            {
                "user": username,
                "password": password,
                "client": self.session.headers.get("User-Agent", "UntisIcalExporter/1.0"),
            },
        )
        if not isinstance(result, dict) or "sessionId" not in result:
            raise WebUntisRpcError("Login fehlgeschlagen: Keine sessionId erhalten.")
        return result

    def logout(self) -> None:
        try:
            self.call("logout")
        except Exception as exc:  # noqa: BLE001
            logger.debug("Logout-Hinweis: %s", exc)

    def fetch_homework_payload(self, start_date: dt.date, end_date: dt.date) -> dict[str, Any]:
        """Ruft Hausaufgaben über den internen WebUntis-REST-Endpunkt /api/homeworks/lessons ab."""
        url = f"{self.base_url}/api/homeworks/lessons"
        params = {
            "startDate": start_date.strftime("%Y%m%d"),
            "endDate": end_date.strftime("%Y%m%d"),
        }
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{self.base_url}/",
        }
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, dict):
            return {}
        data = payload.get("data")
        return data if isinstance(data, dict) else payload

    def fetch_exams_payload(
        self,
        start_date: dt.date,
        end_date: dt.date,
        student_id: int | str | None = None,
        with_grades: bool = True,
        klasse_id: int = -1,
    ) -> list[dict[str, Any]]:
        """Ruft Prüfungen über den internen WebUntis-REST-Endpunkt /api/exams ab."""
        base = getattr(self, "base_url", None) or f"https://{getattr(self, 'server', '')}/WebUntis"
        base = str(base).rstrip("/")
        url = f"{base}/api/exams"
        params: dict[str, Any] = {
            "startDate": start_date.strftime("%Y%m%d"),
            "endDate": end_date.strftime("%Y%m%d"),
            "withGrades": str(bool(with_grades)).lower(),
            "klasseId": int(klasse_id),
        }
        # studentId absichtlich nicht mitschicken: WebUntis /api/exams liefert mit studentId oft []
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{base}/",
        }
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        raw = response.json()
        if isinstance(raw, list):
            return [item for item in raw if isinstance(item, dict)]
        if isinstance(raw, dict):
            for key in ("exams", "data", "items", "list"):
                val = raw.get(key)
                if isinstance(val, list):
                    return [item for item in val if isinstance(item, dict)]
                if isinstance(val, dict):
                    for inner_key in ("exams", "items", "list"):
                        inner_val = val.get(inner_key)
                        if isinstance(inner_val, list):
                            return [item for item in inner_val if isinstance(item, dict)]
        return []

    def _get_bearer_token(self, base_headers: dict[str, str]) -> str | None:
        """Holt ein aktuelles JWT-Bearer-Token über /api/token/new für REST-Endpunkte."""
        token_url = f"{self.base_url}/api/token/new"
        try:
            resp = self.session.get(token_url, headers=base_headers, timeout=self.timeout)
            resp.raise_for_status()
            token = resp.text.strip().strip("\"")
            return token or None
        except Exception as exc:  # noqa: BLE001
            logger.debug("Bearer-Token über %s nicht abrufbar: %s", token_url, exc)
            return None

    def fetch_messages_payload(self, ref_date: dt.date, custom_url: str | None = None) -> list[dict[str, Any]]:
        """Ruft Mitteilungen (incomingMessages) über WebUntis-REST-Endpunkte ab (mit Bearer-Token & Fallback)."""
        tenant_id = self.session.cookies.get("Tenant-Id", "").strip("\"")
        headers: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "Referer": f"{self.base_url}/messages/inbox",
        }
        if tenant_id:
            headers["Tenant-Id"] = tenant_id

        bearer_token = self._get_bearer_token(headers)
        auth_headers = dict(headers)
        if bearer_token:
            auth_headers["Authorization"] = f"Bearer {bearer_token}"

        endpoints: list[tuple[str, dict[str, Any] | None, dict[str, str]]] = []
        if custom_url:
            endpoints.append((custom_url, None, auth_headers if bearer_token else headers))
        if bearer_token:
            endpoints.append((f"{self.base_url}/api/rest/view/v1/messages", None, auth_headers))
        endpoints.extend([
            (f"{self.base_url}/api/messages/received", {"date": ref_date.isoformat()}, headers),
            (f"{self.base_url}/api/messages/received", {"date": ref_date.strftime("%Y%m%d")}, headers),
            (f"{self.base_url}/api/messages/received", None, headers),
            (f"{self.base_url}/api/rest/view/v1/messages", {"date": ref_date.isoformat()}, auth_headers if bearer_token else headers),
            (f"{self.base_url}/api/messages", None, headers),
        ])

        last_err: Exception | None = None

        for url, params, req_headers in endpoints:
            try:
                response = self.session.get(url, params=params, headers=req_headers, timeout=self.timeout)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                raw = response.json()

                if isinstance(raw, list):
                    return [item for item in raw if isinstance(item, dict)]
                if isinstance(raw, dict):
                    for key in ("incomingMessages", "messages", "data", "items", "list"):
                        val = raw.get(key)
                        if isinstance(val, list):
                            return [item for item in val if isinstance(item, dict)]
                        if isinstance(val, dict):
                            for inner_key in ("incomingMessages", "messages", "items", "list"):
                                inner_val = val.get(inner_key)
                                if isinstance(inner_val, list):
                                    return [item for item in inner_val if isinstance(inner_val, dict)]
                return []
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                logger.debug("Mitteilungs-Endpunkt %s fehlgeschlagen: %s", url, exc)

        if last_err is not None:
            raise last_err
        return []


def parse_untis_date(value: int | str) -> dt.date:
    s = str(value).strip()
    return dt.date(int(s[0:4]), int(s[4:6]), int(s[6:8]))


def parse_untis_time(value: int | str) -> dt.time:
    s = str(value).strip().zfill(4)
    return dt.time(int(s[:-2]), int(s[-2:]))


def is_all_day_lesson(entry: dict[str, Any]) -> bool:
    """Erkennt ganztägige / tagesübergreifende Einträge in getTimetable mit startTime 0."""
    raw_start = str(entry.get("startTime") or "0").strip()
    try:
        start_num = int(raw_start)
    except ValueError:
        return False
    return start_num == 0


def format_element_names(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    names: list[str] = []
    for item in items:
        label = item.get("longname") or item.get("name") or ""
        if label and label not in names:
            names.append(str(label))
    return ", ".join(names)


def _strip_html(raw: str) -> str:
    cleaned = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"</p\s*>", "\n", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _parse_message_date(msg: dict[str, Any], fallback: dt.date) -> dt.date:
    for field in ("sentDateTime", "sentDate", "createdDate", "date", "validFrom", "lastUpdated"):
        val = msg.get(field)
        if not val:
            continue
        s = str(val).strip()
        iso_match = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if iso_match:
            return dt.date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))
        compact_match = re.match(r"^(\d{8})", s)
        if compact_match:
            return parse_untis_date(compact_match.group(1))
    return fallback


def _extract_names_field(val: Any) -> str:
    if not val:
        return ""
    if isinstance(val, str):
        return val.strip()
    if isinstance(val, dict):
        return str(val.get("longName") or val.get("longname") or val.get("name") or "").strip()
    if isinstance(val, list):
        parts: list[str] = []
        for item in val:
            part = _extract_names_field(item)
            if part and part not in parts:
                parts.append(part)
        return ", ".join(parts)
    return ""


def _parse_optional_time(value: Any) -> dt.time | None:
    s = str(value or "").strip()
    if not s:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        return dt.time(h, mi) if 0 <= h <= 23 and 0 <= mi <= 59 else None
    digits = re.sub(r"\D", "", s).zfill(4)
    h, mi = int(digits[:-2]), int(digits[-2:])
    return dt.time(h, mi) if 0 <= h <= 23 and 0 <= mi <= 59 else None


def build_exams_calendar_for_child(
    child: dict[str, Any],
    exams: list[dict[str, Any]],
    tz_name: str,
) -> Calendar:
    """Baut einen iCalendar aus dem /api/exams-Payload auf."""
    tz = pytz.timezone(tz_name)
    child_name = child["name"]
    slug = child["slug"]

    cal = Calendar()
    cal.add("prodid", f"-//UntisToIcal// {child_name} Prüfungen //DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"Prüfungen – {child_name}")
    cal.add("x-wr-timezone", tz_name)

    added_count = 0
    for idx, exam in enumerate(exams):
        raw_date = exam.get("examDate") or exam.get("startDate") or exam.get("date") or exam.get("endDate")
        if not raw_date:
            continue
        exam_date = parse_untis_date(raw_date)
        subject = _extract_names_field(exam.get("subject")) or _extract_names_field(exam.get("subjectName")) or "Prüfung"
        exam_type = str(exam.get("examType") or exam.get("type") or "").strip()
        exam_name = str(exam.get("name") or exam.get("title") or "").strip()
        text = _strip_html(str(exam.get("text") or exam.get("notes") or exam.get("description") or "").strip())
        rooms = _extract_names_field(exam.get("rooms") or exam.get("room"))
        teachers = _extract_names_field(exam.get("teachers") or exam.get("teacher"))
        classes = _extract_names_field(exam.get("studentClass") or exam.get("klassen") or exam.get("classes") or exam.get("klasse"))
        grade = str(exam.get("grade") or exam.get("mark") or "").strip()

        title_bits: list[str] = [subject]
        if exam_type:
            title_bits.append(f"({exam_type})")
        detail_title = " / ".join(p for p in (exam_name, text.splitlines()[0].strip() if text else "") if p)
        if detail_title:
            title_bits.append(f"– {detail_title[:75]}")
        summary = f"[PRÜFUNG] {' '.join(title_bits)}"[:110]

        start_time = _parse_optional_time(exam.get("startTime") or exam.get("start"))
        end_time = _parse_optional_time(exam.get("endTime") or exam.get("end"))
        if start_time is not None and end_time is not None:
            dt_start: dt.date | dt.datetime = tz.localize(dt.datetime.combine(exam_date, start_time))
            dt_end: dt.date | dt.datetime = tz.localize(dt.datetime.combine(exam_date, end_time))
            if dt_end <= dt_start:
                dt_end = dt_start + dt.timedelta(minutes=45)
        elif start_time is not None:
            dt_start = tz.localize(dt.datetime.combine(exam_date, start_time))
            dt_end = dt_start + dt.timedelta(minutes=45)
        else:
            dt_start = exam_date
            dt_end = exam_date + dt.timedelta(days=1)

        desc_lines: list[str] = [f"Fach: {subject}"]
        if exam_type:
            desc_lines.append(f"Prüfungsart: {exam_type}")
        if exam_name:
            desc_lines.append(f"Bezeichnung: {exam_name}")
        if classes:
            desc_lines.append(f"Klasse: {classes}")
        if teachers:
            desc_lines.append(f"Lehrkraft: {teachers}")
        if rooms:
            desc_lines.append(f"Raum: {rooms}")
        if grade:
            desc_lines.append(f"Note/Bewertung: {grade}")
        if text:
            desc_lines.append(f"Thema/Hinweis:\n{text}")

        exam_id = exam.get("id") or idx
        uid_seed = f"{slug}-exam-{exam_id}-{exam_date.isoformat()}-{summary}"
        uid_hash = hashlib.sha256(uid_seed.encode("utf-8")).hexdigest()[:24]

        event = Event()
        event.add("uid", f"{uid_hash}@untis-ical.local")
        event.add("summary", summary)
        event.add("dtstart", dt_start)
        event.add("dtend", dt_end)
        event.add("dtstamp", dt.datetime.now(dt.timezone.utc))
        if rooms:
            event.add("location", rooms)
        event.add("description", "\n".join(desc_lines))
        cal.add_component(event)
        added_count += 1

    logger.info("Für '%s' wurden %d Prüfungen in den Kalender geschrieben.", child_name, added_count)
    return cal


def build_messages_calendar_for_child(
    child: dict[str, Any],
    messages: list[dict[str, Any]],
    tz_name: str,
    fallback_date: dt.date,
    max_items: int = 25,
) -> Calendar:
    """Baut einen iCalendar aus WebUntis-Mitteilungen (incomingMessages) auf."""
    child_name = child["name"]
    slug = child["slug"]

    cal = Calendar()
    cal.add("prodid", f"-//UntisToIcal// {child_name} Mitteilungen //DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"Mitteilungen  {child_name}")
    cal.add("x-wr-timezone", tz_name)

    added_count = 0
    for idx, msg in enumerate(messages[:max_items]):
        msg_date = _parse_message_date(msg, fallback_date)
        sent_dt_str = str(msg.get("sentDateTime") or "").strip()

        subject = str(
            msg.get("subject")
            or msg.get("title")
            or msg.get("headline")
            or "Mitteilung"
        ).strip()
        body_raw = str(
            msg.get("contentPreview")
            or msg.get("body")
            or msg.get("content")
            or msg.get("text")
            or msg.get("message")
            or ""
        ).strip()
        body_text = _strip_html(body_raw)

        sender = ""
        for s_key in ("sender", "author", "createdBy", "from"):
            s_val = msg.get(s_key)
            if isinstance(s_val, dict):
                sender = str(
                    s_val.get("displayName")
                    or s_val.get("name")
                    or s_val.get("longName")
                    or ""
                ).strip()
            elif isinstance(s_val, str) and s_val.strip():
                sender = s_val.strip()
            if sender:
                break

        is_unread = (
            msg.get("isMessageRead") is False
            or msg.get("isRead") is False
            or msg.get("read") is False
            or msg.get("unread") is True
        )
        prefix = "[NEU] " if is_unread else ""
        first_line = body_text.splitlines()[0].strip() if body_text else ""
        summary_base = subject if subject and subject.lower() != "mitteilung" else (first_line[:70] or "Mitteilung")
        summary = f"{prefix}{summary_base}"[:100]

        desc_lines: list[str] = []
        if sender:
            desc_lines.append(f"Von: {sender}")
        desc_lines.append(f"Datum: {sent_dt_str or msg_date.isoformat()}")
        if is_unread:
            desc_lines.append("Status: Ungelesen")
        if body_text:
            desc_lines.append(f"\n{body_text}")

        msg_id = msg.get("id") or msg.get("messageId") or idx
        uid_seed = f"{slug}-msg-{msg_id}-{msg_date.isoformat()}-{summary}"
        uid_hash = hashlib.sha256(uid_seed.encode("utf-8")).hexdigest()[:24]

        event = Event()
        event.add("uid", f"{uid_hash}@untis-ical.local")
        event.add("summary", summary)
        event.add("dtstart", msg_date)
        event.add("dtend", msg_date + dt.timedelta(days=1))
        event.add("dtstamp", dt.datetime.now(dt.timezone.utc))
        if desc_lines:
            event.add("description", "\n".join(desc_lines))

        cal.add_component(event)
        added_count += 1

    logger.info("Für '%s' wurden %d Mitteilungen in den Kalender geschrieben.", child_name, added_count)
    return cal


def build_homework_calendar_for_child(
    child: dict[str, Any],
    homework_data: dict[str, Any],
    tz_name: str,
) -> Calendar:
    """Baut einen iCalendar aus dem /api/homeworks/lessons-Payload auf."""
    child_name = child["name"]
    slug = child["slug"]

    raw_homeworks = homework_data.get("homeworks") or []
    raw_lessons = homework_data.get("lessons") or []
    raw_teachers = homework_data.get("teachers") or []
    raw_records = homework_data.get("records") or []

    lesson_subjects: dict[int, str] = {}
    for lesson in raw_lessons:
        if isinstance(lesson, dict) and lesson.get("id") is not None:
            subj = str(lesson.get("subject") or lesson.get("subjectName") or "").strip()
            if subj:
                lesson_subjects[int(lesson["id"])] = subj

    teacher_names: dict[int, str] = {}
    for teacher in raw_teachers:
        if isinstance(teacher, dict) and teacher.get("id") is not None:
            t_name = str(teacher.get("longName") or teacher.get("name") or "").strip()
            if t_name:
                teacher_names[int(teacher["id"])] = t_name

    homework_teachers: dict[int, list[str]] = {}
    for rec in raw_records:
        if not isinstance(rec, dict):
            continue
        hw_id = rec.get("homeworkId")
        t_id = rec.get("teacherId")
        if hw_id is not None and t_id is not None:
            t_label = teacher_names.get(int(t_id))
            if t_label:
                bucket = homework_teachers.setdefault(int(hw_id), [])
                if t_label not in bucket:
                    bucket.append(t_label)

    cal = Calendar()
    cal.add("prodid", f"-//UntisToIcal// {child_name} Hausaufgaben //DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"Hausaufgaben  {child_name}")
    cal.add("x-wr-timezone", tz_name)

    added_count = 0
    for hw in raw_homeworks:
        if not isinstance(hw, dict):
            continue
        raw_due = hw.get("dueDate") or hw.get("endDate") or hw.get("date")
        if not raw_due:
            continue
        due_date = parse_untis_date(raw_due)

        lesson_id = hw.get("lessonId")
        subject = (
            lesson_subjects.get(int(lesson_id))
            if lesson_id is not None and int(lesson_id) in lesson_subjects
            else str(hw.get("subject") or hw.get("subjectName") or "Hausaufgabe").strip()
        )

        text = str(hw.get("text") or "").strip()
        remark = str(hw.get("remark") or "").strip()
        combined_text = " | ".join(part for part in (text, remark) if part)
        single_line_text = " / ".join(line.strip() for line in combined_text.splitlines() if line.strip())
        completed = bool(hw.get("completed") or False)

        hw_id = hw.get("id")
        teachers = homework_teachers.get(int(hw_id), []) if hw_id is not None else []

        has_meaningful_text = bool(single_line_text) and single_line_text.strip().lower() != "ha"
        prefix = "[ERLEDIGT] " if completed else ""
        if has_meaningful_text:
            summary = f"{prefix}HA {subject}: {single_line_text[:80]}"
        else:
            summary = f"{prefix}HA {subject}"

        desc_lines: list[str] = [f"Fach: {subject}"]
        if text:
            desc_lines.append(f"Aufgabe:\n{text}")
        if remark:
            desc_lines.append(f"Bemerkung: {remark}")
        if teachers:
            desc_lines.append(f"Lehrkraft: {', '.join(teachers)}")
        if hw.get("date"):
            desc_lines.append(f"Aufgegeben am: {parse_untis_date(hw['date']).isoformat()}")
        desc_lines.append(f"Fällig am: {due_date.isoformat()}")
        desc_lines.append(f"Status: {'Erledigt' if completed else 'Offen'}")

        uid_seed = f"{slug}-hw-{hw_id}-{due_date.isoformat()}-{subject}-{single_line_text}"
        uid_hash = hashlib.sha256(uid_seed.encode("utf-8")).hexdigest()[:24]

        event = Event()
        event.add("uid", f"{uid_hash}@untis-ical.local")
        event.add("summary", summary)
        event.add("dtstart", due_date)
        event.add("dtend", due_date + dt.timedelta(days=1))
        event.add("dtstamp", dt.datetime.now(dt.timezone.utc))
        event.add("description", "\n".join(desc_lines))
        if completed:
            event.add("status", "COMPLETED")

        cal.add_component(event)
        added_count += 1

    logger.info("Für '%s' wurden %d Hausaufgaben in den Kalender geschrieben.", child_name, added_count)
    return cal


def build_calendars_for_child(
    child: dict[str, Any],
    server: str,
    user_agent: str,
    tz_name: str,
    start_date: dt.date,
    end_date: dt.date,
    mark_cancelled: bool,
    skip_cancelled: bool,
) -> tuple[Calendar, Calendar | None, Calendar | None, Calendar | None]:
    tz = pytz.timezone(tz_name)
    child_name = child["name"]
    slug = child["slug"]
    child_server = str(child.get("server") or server).strip()
    username = child["username"]
    password = child["password"]

    client = WebUntisClient(server=child_server, user_agent=user_agent)
    logger.info("Melde Account für '%s' (%s @ %s) an...", child_name, username, child_server)

    auth_info = client.login(username=username, password=password)
    person_type = auth_info.get("personType")
    person_id = auth_info.get("personId")
    logger.info("Login erfolgreich für '%s' (personType=%s, personId=%s)", child_name, person_type, person_id)

    homework_data: dict[str, Any] | None = None
    messages_data: list[dict[str, Any]] | None = None
    try:
        configured_type = child.get("element_type")
        if configured_type is not None:
            element_type = int(configured_type)
        elif person_type in (1, 2, 3, 4, 5):
            element_type = int(person_type)
        else:
            element_type = 5

        element_id = child.get("element_id") if child.get("element_id") is not None else person_id
        logger.info("Rufe Timetable ab für '%s' (element.id=%s, element.type=%s)...", child_name, element_id, element_type)

        timetable = client.call(
            "getTimetable",
            {
                "options": {
                    "element": {
                        "id": element_id,
                        "type": element_type,
                    },
                    "startDate": int(start_date.strftime("%Y%m%d")),
                    "endDate": int(end_date.strftime("%Y%m%d")),
                    "showLsText": True,
                    "showStudentgroup": True,
                    "klasseFields": ["id", "name", "longname"],
                    "roomFields": ["id", "name", "longname"],
                    "subjectFields": ["id", "name", "longname"],
                    "teacherFields": ["id", "name", "longname"],
                }
            },
        )

        try:
            homework_data = client.fetch_homework_payload(start_date=start_date, end_date=end_date)
        except Exception as hw_exc:  # noqa: BLE001
            logger.warning("Hausaufgaben-Abruf für '%s' nicht verfügbar/fehlgeschlagen: %s", child_name, hw_exc)
            homework_data = None

        try:
            custom_url = child.get("messages_url") or None
            messages_data = client.fetch_messages_payload(ref_date=dt.date.today(), custom_url=custom_url)
        except Exception as msg_exc:  # noqa: BLE001
            logger.warning("Mitteilungen-Abruf für '%s' nicht verfügbar/fehlgeschlagen: %s", child_name, msg_exc)
            messages_data = None

        exams_data: list[dict[str, Any]] | None = None
        try:
            student_id = (
                child.get("student_id")
                if child.get("student_id") is not None
                else (person_id if person_type == 5 else element_id)
            )
            with_grades = bool(child.get("with_grades", True))
            klasse_id = int(child.get("klasse_id", -1))
            back_weeks = max(4, int(child.get("include_weeks_back", 4) or 4))
            exam_start_date = min(start_date, dt.date.today() - dt.timedelta(weeks=back_weeks))
            exams_data = client.fetch_exams_payload(
                start_date=exam_start_date,
                end_date=end_date,
                student_id=student_id,
                with_grades=with_grades,
                klasse_id=klasse_id,
            )
        except Exception as exam_exc:  # noqa: BLE001
            if "403" in str(exam_exc):
                logger.debug("Prüfungen-Endpunkt für '%s' liefert 403 (nicht freigeschaltet): %s", child_name, exam_exc)
            else:
                logger.warning("Prüfungen-Abruf für '%s' nicht verfügbar/fehlgeschlagen: %s", child_name, exam_exc)
            exams_data = None
    finally:
        client.logout()

    if not isinstance(timetable, list):
        raise WebUntisRpcError(f"Unerwartetes Timetable-Format für '{child_name}': {type(timetable)}")

    cal = Calendar()
    cal.add("prodid", f"-//UntisToIcal// {child_name} //DE")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", f"Untis  {child_name}")
    cal.add("x-wr-timezone", tz_name)

    added_count = 0
    for entry in timetable:
        code = str(entry.get("code") or "").lower()
        is_cancelled = code == "cancelled"

        if is_cancelled and skip_cancelled:
            continue

        entry_date = parse_untis_date(entry["date"])
        all_day = is_all_day_lesson(entry)

        if all_day:
            dt_start: dt.date | dt.datetime = entry_date
            dt_end: dt.date | dt.datetime = entry_date + dt.timedelta(days=1)
        else:
            start_dt_naive = dt.datetime.combine(
                entry_date,
                parse_untis_time(entry["startTime"]),
            )
            end_dt_naive = dt.datetime.combine(
                entry_date,
                parse_untis_time(entry["endTime"]),
            )
            dt_start = tz.localize(start_dt_naive)
            dt_end = tz.localize(end_dt_naive)

        subjects = format_element_names(entry.get("su"))
        rooms = format_element_names(entry.get("ro"))
        teachers = format_element_names(entry.get("te"))
        info_text = str(entry.get("lstext") or entry.get("info") or "").strip()

        base_title = subjects or info_text or "Unterricht"
        if is_cancelled and mark_cancelled:
            summary = f"[ENTFALL] {base_title}"
        elif code == "irregular":
            summary = f"[VERTRETUNG] {base_title}"
        else:
            summary = base_title

        description_parts: list[str] = []
        if all_day:
            description_parts.append("Ganztägig")
        if rooms:
            description_parts.append(f"Raum: {rooms}")
        if teachers:
            description_parts.append(f"Lehrkraft: {teachers}")
        if info_text and info_text != base_title:
            description_parts.append(f"Hinweis: {info_text}")
        if code:
            description_parts.append(f"Status: {code}")

        lesson_id = entry.get("id", "")
        uid_seed = f"{slug}-{lesson_id}-{entry.get('date')}-{entry.get('startTime')}-{entry.get('endTime')}"
        uid_hash = hashlib.sha256(uid_seed.encode("utf-8")).hexdigest()[:24]

        event = Event()
        event.add("uid", f"{uid_hash}@untis-ical.local")
        event.add("summary", summary)
        event.add("dtstart", dt_start)
        event.add("dtend", dt_end)
        event.add("dtstamp", dt.datetime.now(dt.timezone.utc))
        if rooms:
            event.add("location", rooms)
        if description_parts:
            event.add("description", "\n".join(description_parts))
        if is_cancelled:
            event.add("status", "CANCELLED")

        cal.add_component(event)
        added_count += 1

    logger.info("Für '%s' wurden %d Termine in den Kalender geschrieben.", child_name, added_count)

    hw_cal = (
        build_homework_calendar_for_child(child=child, homework_data=homework_data, tz_name=tz_name)
        if homework_data is not None
        else None
    )
    msg_cal = (
        build_messages_calendar_for_child(
            child=child,
            messages=messages_data,
            tz_name=tz_name,
            fallback_date=dt.date.today(),
        )
        if messages_data is not None
        else None
    )
    exams_cal = (
        build_exams_calendar_for_child(child=child, exams=exams_data, tz_name=tz_name)
        if exams_data is not None
        else None
    )
    return cal, hw_cal, msg_cal, exams_cal


def write_file_atomically(target_path: Path, content: bytes) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target_path.name}.", suffix=".tmp", dir=str(target_path.parent))
    try:
        with os.fdopen(fd, "wb") as tmp_file:
            tmp_file.write(content)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        os.chmod(tmp_name, 0o644)
        os.replace(tmp_name, target_path)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def build_combined_calendar(
    main_cal: Any,
    extra_cals: list[tuple[Any, str]],
) -> Any:
    """Führt Hauptkalender und Zusatzkalender (Hausaufgaben, Mitteilungen, Prüfungen) in einem VCALENDAR zusammen."""
    combined = Calendar()
    for prop, val in main_cal.property_items():
        name = str(prop).upper()
        if name not in ("VERSION", "PRODID", "CALSCALE"):
            combined.add(prop, val)
    combined.add("version", "2.0")
    combined.add("prodid", "-//UntisToICal//Combined//DE")
    combined.add("calscale", "GREGORIAN")

    seen_uids: set[str] = set()

    def _add_events(source_cal: Any, prefix: str = "") -> None:
        if source_cal is None:
            return
        for component in source_cal.walk():
            if component.name == "VTIMEZONE":
                # Nur hinzufügen, falls noch nicht vorhanden
                tz_id = str(component.get("TZID", ""))
                already = any(
                    c.name == "VTIMEZONE" and str(c.get("TZID", "")) == tz_id
                    for c in combined.walk()
                )
                if not already:
                    combined.add_component(component)
            elif component.name == "VEVENT":
                uid = str(component.get("UID", "")).strip()
                if uid and uid in seen_uids:
                    continue
                if uid:
                    seen_uids.add(uid)
                ev = component.copy()
                if prefix and "SUMMARY" in ev:
                    summary_str = str(ev.get("SUMMARY", ""))
                    if not summary_str.startswith(prefix):
                        ev["SUMMARY"] = f"{prefix}{summary_str}"
                combined.add_component(ev)

    _add_events(main_cal, "")
    for sub_cal, prefix in extra_cals:
        _add_events(sub_cal, prefix)

    return combined


def write_children_manifest(output_dir: Path, profiles: list[dict[str, Any]]) -> None:
    """Schreibt ausschließlich öffentliche Profilmetadaten (name, slug) ohne Zugangsdaten."""
    public_children = [
        {
            "name": str(profile.get("name") or profile.get("slug") or "").strip(),
            "slug": str(profile.get("slug") or "").strip(),
        }
        for profile in profiles
        if str(profile.get("slug") or "").strip()
    ]
    payload = (json.dumps(public_children, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path = output_dir / "children.json"
    write_file_atomically(manifest_path, payload)
    logger.info("Gespeichert: %s (%d Profile)", manifest_path, len(public_children))


def compute_date_range(include_weeks_back: int, weeks_ahead: int) -> tuple[dt.date, dt.date]:
    today = dt.date.today()
    monday_this_week = today - dt.timedelta(days=today.weekday())
    start_date = monday_this_week - dt.timedelta(weeks=max(0, include_weeks_back))
    end_sunday = monday_this_week + dt.timedelta(weeks=max(1, weeks_ahead), days=6)
    return start_date, end_sunday


def collect_profiles(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Sammelt reguläre 'children'-Einträge sowie den separaten 'children_other_school'-Zweig."""
    profiles: list[dict[str, Any]] = []

    raw_children = config.get("children", [])
    if isinstance(raw_children, list):
        for child in raw_children:
            if isinstance(child, dict):
                profiles.append(child)

    other_school_branch = config.get("children_other_school") or config.get("children_otherSchool")
    if isinstance(other_school_branch, list):
        for entry in other_school_branch:
            if isinstance(entry, dict):
                profiles.append(dict(entry))
    elif isinstance(other_school_branch, dict) and other_school_branch:
        profiles.append(dict(other_school_branch))

    return profiles


def main() -> int:
    config_path = Path(os.environ.get("UNTIS_ICAL_CONFIG", "/opt/untis-ical/config.json"))
    if not config_path.exists():
        logger.error("Konfigurationsdatei nicht gefunden: %s", config_path)
        return 1

    with config_path.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    server = config["server"]
    user_agent = config.get("user_agent", "UntisIcalExporter/1.0")
    tz_name = config.get("timezone", "Europe/Berlin")
    weeks_ahead = int(config.get("weeks_ahead", 3))
    include_weeks_back = int(config.get("include_weeks_back", 0))
    mark_cancelled = bool(config.get("mark_cancelled", True))
    skip_cancelled = bool(config.get("skip_cancelled", False))
    output_dir = Path(config.get("output_dir", "/var/www/html/untis"))
    profiles = collect_profiles(config)

    if not profiles:
        logger.error("In der config.json sind weder 'children' noch 'children_other_school' eingetragen.")
        return 1

    try:
        write_children_manifest(output_dir=output_dir, profiles=profiles)
    except Exception as exc:  # noqa: BLE001
        logger.error("Fehler beim Schreiben von children.json: %s", exc)

    start_date, end_date = compute_date_range(include_weeks_back=include_weeks_back, weeks_ahead=weeks_ahead)
    logger.info("Abrufzeitraum: %s bis %s", start_date.isoformat(), end_date.isoformat())

    exit_code = 0
    for child in profiles:
        slug = child["slug"]
        out_file = output_dir / f"{slug}.ics"
        hw_out_file = output_dir / f"{slug}_hausaufgaben.ics"
        msg_out_file = output_dir / f"{slug}_mitteilungen.ics"
        exams_out_file = output_dir / f"{slug}_pruefungen.ics"
        try:
            cal, hw_cal, msg_cal, exams_cal = build_calendars_for_child(
                child=child,
                server=server,
                user_agent=user_agent,
                tz_name=tz_name,
                start_date=start_date,
                end_date=end_date,
                mark_cancelled=mark_cancelled,
                skip_cancelled=skip_cancelled,
            )
            write_file_atomically(out_file, cal.to_ical())
            logger.info("Gespeichert: %s", out_file)

            if hw_cal is not None:
                write_file_atomically(hw_out_file, hw_cal.to_ical())
                logger.info("Gespeichert: %s", hw_out_file)

            if msg_cal is not None:
                write_file_atomically(msg_out_file, msg_cal.to_ical())
                logger.info("Gespeichert: %s", msg_out_file)

            if exams_cal is not None:
                write_file_atomically(exams_out_file, exams_cal.to_ical())
                logger.info("Gespeichert: %s", exams_out_file)

            all_out_file = output_dir / f"{slug}_alle.ics"
            combined_cal = build_combined_calendar(
                cal,
                [
                    (hw_cal, "[HA] "),
                    (msg_cal, "[Info] "),
                    (exams_cal, "[Prüfung] "),
                ],
            )
            write_file_atomically(all_out_file, combined_cal.to_ical())
            logger.info("Gespeichert: %s", all_out_file)
        except Exception as exc:  # noqa: BLE001
            exit_code = 1
            logger.error("Fehler bei Kind '%s' (%s): %s", child.get("name"), slug, exc)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())