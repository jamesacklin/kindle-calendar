"""Shared event normalization and text helpers for the Kindle calendar renderer."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def width(draw, value, face):
    return draw.textbbox((0, 0), value, font=face)[2]


def ellipsize(draw, value, face, max_width):
    value = " ".join(str(value).split())
    if width(draw, value, face) <= max_width:
        return value
    while value and width(draw, value + "…", face) > max_width:
        value = value[:-1]
    return value.rstrip() + "…"


def local_datetime(raw, tz):
    value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError(f"timed event has no UTC offset: {raw}")
    return value.astimezone(tz)


def events_for_day(document, day, tz):
    start_of_day = datetime.combine(day, time.min, tzinfo=tz)
    end_of_day = datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
    selected = []
    for event in document.get("events", []):
        title = str(event.get("title") or "Untitled event")
        if event.get("all_day"):
            start = date.fromisoformat(event["start"][:10])
            end = date.fromisoformat(event.get("end", event["start"])[:10])
            if end <= start:
                end = start + timedelta(days=1)
            if start <= day < end:
                selected.append((0, start_of_day, end_of_day, title, True))
        else:
            start = local_datetime(event["start"], tz)
            end = local_datetime(event["end"], tz)
            if end <= start:
                raise ValueError(f"event ends before it starts: {title}")
            if start < end_of_day and end > start_of_day:
                selected.append((1, start, end, title, False))
    selected.sort(key=lambda item: (item[0], item[1], item[3].casefold()))
    return selected


def format_time(value):
    return value.strftime("%I:%M").lstrip("0") + ("a" if value.hour < 12 else "p")


def document_from_components(components, day, timezone):
    events = []
    for component in components:
        if str(component.get("STATUS", "")).upper() == "CANCELLED":
            continue
        start = component.decoded("DTSTART")
        if component.get("DTEND") is not None:
            end = component.decoded("DTEND")
        elif component.get("DURATION") is not None:
            end = start + component.decoded("DURATION")
        else:
            end = start + (timedelta(hours=1) if isinstance(start, datetime) else timedelta(days=1))
        all_day = not isinstance(start, datetime)
        if isinstance(start, datetime) and start.tzinfo is None:
            start = start.replace(tzinfo=ZoneInfo(timezone))
        if isinstance(end, datetime) and end.tzinfo is None:
            end = end.replace(tzinfo=ZoneInfo(timezone))
        events.append({
            "title": str(component.get("SUMMARY") or "Untitled event"),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "all_day": all_day,
        })
    return {"date": day.isoformat(), "timezone": timezone, "calendar_name": "Work", "events": events}
