#!/usr/bin/env python3
"""Render a single day of normalized calendar events for the Kindle 4."""

import argparse
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

SIZE = (600, 800)
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONT_DIR / name), size)


def width(draw, value, face):
    return draw.textbbox((0, 0), value, font=face)[2]


def ellipsize(draw, value, face, max_width):
    value = " ".join(str(value).split())
    if width(draw, value, face) <= max_width:
        return value
    while value and width(draw, value + "…", face) > max_width:
        value = value[:-1]
    return value.rstrip() + "…"


def wrap_title(draw, value, face, max_width):
    words = " ".join(str(value).split()).split(" ")
    if not words:
        return [""]
    first = ""
    for word in words:
        candidate = f"{first} {word}".strip()
        if width(draw, candidate, face) > max_width and first:
            break
        first = candidate
    remainder = " ".join(words[len(first.split()):])
    if not remainder:
        return [ellipsize(draw, first, face, max_width)]
    return [ellipsize(draw, first, face, max_width), ellipsize(draw, remainder, face, max_width)]


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


def sample_document(day):
    def at(hour, minute=0):
        return datetime.combine(day, time(hour, minute), tzinfo=ZoneInfo("America/New_York")).isoformat()

    return {
        "date": day.isoformat(),
        "timezone": "America/New_York",
        "calendar_name": "Work",
        "events": [
            {"title": "Team standup", "start": at(9, 30), "end": at(9, 45)},
            {"title": "Design review · Calendar display", "start": at(11), "end": at(12)},
            {"title": "Lunch", "start": at(12, 30), "end": at(13)},
            {"title": "Project planning", "start": at(14), "end": at(15)},
            {"title": "Focus time", "start": at(16), "end": at(17, 30)},
        ],
    }


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


def document_from_ics(path, day, timezone):
    from icalendar import Calendar
    import recurring_ical_events

    calendar = Calendar.from_ical(path.read_bytes())
    return document_from_components(recurring_ical_events.of(calendar).at(day), day, timezone)


def render(document, day):
    tz = ZoneInfo(document.get("timezone", "America/New_York"))
    events = events_for_day(document, day, tz)
    image = Image.new("L", SIZE, 255)
    draw = ImageDraw.Draw(image)

    ink, muted, rule = 8, 90, 178
    label = font(17, True)
    date_face = font(104, True)
    weekday_face = font(31, True)
    month_face = font(22)
    time_face = font(21, True)
    small_face = font(16)
    title_face = font(24, True)

    draw.text((30, 22), ellipsize(draw, document.get("calendar_name", "Calendar").upper(), label, 540), fill=ink, font=label)
    draw.line((30, 55, 570, 55), fill=ink, width=2)
    draw.text((24, 56), str(day.day), fill=ink, font=date_face, stroke_width=0)
    draw.text((178, 86), day.strftime("%A"), fill=ink, font=weekday_face)
    draw.text((180, 132), day.strftime("%B %Y"), fill=muted, font=month_face)
    draw.line((30, 192, 570, 192), fill=ink, width=4)

    count = len(events)
    draw.text((30, 211), f"{count} EVENT{'S' if count != 1 else ''} TODAY", fill=muted, font=label)
    if not events:
        draw.text((30, 327), "Nothing scheduled", fill=ink, font=font(34, True))
        draw.text((30, 383), "Enjoy the open space.", fill=muted, font=month_face)
    else:
        visible = events[:7]
        row_height = min(94, 464 // len(visible))
        y = 253
        for _order, start, end, title, all_day in visible:
            draw.line((30, y, 570, y), fill=rule, width=1)
            if all_day:
                draw.text((30, y + 18), "ALL DAY", fill=ink, font=small_face)
            else:
                draw.text((30, y + 13), format_time(start), fill=ink, font=time_face)
                draw.text((31, y + 44), format_time(end), fill=muted, font=small_face)
            draw.line((143, y + 13, 143, y + row_height - 13), fill=rule, width=2)
            lines = wrap_title(draw, title, title_face, 401)
            title_y = y + (14 if len(lines) > 1 else max(15, (row_height - 28) // 2))
            for line in lines:
                draw.text((161, title_y), line, fill=ink, font=title_face)
                title_y += 33
            y += row_height
        draw.line((30, y, 570, y), fill=rule, width=1)
        if count > len(visible):
            draw.text((30, y + 14), f"+ {count - len(visible)} MORE", fill=muted, font=label)

    draw.line((30, 750, 570, 750), fill=ink, width=2)
    draw.text((30, 763), "DAILY AGENDA", fill=muted, font=small_face)
    draw.text((472, 763), day.strftime("%a %d %b").upper(), fill=muted, font=small_face)
    return image


def main():
    parser = argparse.ArgumentParser()
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--input", type=Path, help="normalized event JSON")
    sources.add_argument("--ics", type=Path, help="local iCalendar file")
    parser.add_argument("--date", type=date.fromisoformat)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.ics:
        day = args.date or datetime.now(ZoneInfo(args.timezone)).date()
        document = document_from_ics(args.ics, day, args.timezone)
    elif args.input:
        document = json.loads(args.input.read_text())
        tz = ZoneInfo(document.get("timezone", "America/New_York"))
        day = args.date or date.fromisoformat(document.get("date", datetime.now(tz).date().isoformat()))
    else:
        day = args.date or datetime.now(ZoneInfo("America/New_York")).date()
        document = sample_document(day)
    image = render(document, day)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG")
    print(f"rendered {args.output}: {image.width}x{image.height}, {image.mode}")


if __name__ == "__main__":
    main()
