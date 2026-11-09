#!/usr/bin/env python3
"""Render today and the following five days on a Kindle 4 screen."""

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont

from render_calendar import document_from_components, ellipsize, events_for_day, format_time

WIDTH, HEIGHT = 600, 800
DAY_COUNT = 6
ROW_TOP = 76
ROW_BOTTOM = HEIGHT - 24
INTER = Path(__file__).with_name("assets") / "inter" / "InterVariable.ttf"


def font(size, weight=400):
    face = ImageFont.truetype(str(INTER), size)
    face.set_variation_by_axes([14, weight])
    return face


def sample_document(start_day, timezone):
    tz = ZoneInfo(timezone)
    plan = [
        [(9, 30, "Team standup"), (14, 0, "Project review")],
        [(10, 0, "Planning"), (13, 30, "Design sync"), (16, 0, "Focus time")],
        [(11, 0, "Weekly review")],
        [(9, 0, "Standup"), (15, 0, "Release check-in")],
        [],
        [(12, 0, "Family lunch")],
    ]
    events = []
    for offset, day_plan in enumerate(plan):
        day = start_day + timedelta(days=offset)
        for hour, minute, title in day_plan:
            start = datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz)
            events.append({"title": title, "start": start.isoformat(), "end": (start + timedelta(minutes=45)).isoformat()})
    return {"timezone": timezone, "calendar_name": "Work", "events": events}


def document_from_ics_bytes(data, start_day, timezone):
    from icalendar import Calendar
    import recurring_ical_events

    calendar = Calendar.from_ical(data)
    components = recurring_ical_events.of(calendar).between(start_day, start_day + timedelta(days=DAY_COUNT))
    return document_from_components(components, start_day, timezone)


def document_from_ics_range(path, start_day, timezone):
    return document_from_ics_bytes(path.read_bytes(), start_day, timezone)


def layout_days(counts):
    available = ROW_BOTTOM - ROW_TOP
    step, padding = 24, 16
    needed = sum(max(3, count) for count in counts)
    if needed * step + DAY_COUNT * padding > available:
        step, padding = 20, 12

    capacity = (available - DAY_COUNT * padding) // step
    slots = counts.copy()
    if needed > capacity:
        # Give each busy day another line in turn, reserving its last line
        # for an overflow count if some events still won't fit.
        slots = [min(3, count) for count in counts]
        remaining = capacity - 3 * DAY_COUNT
        while remaining:
            for index, count in enumerate(counts):
                if slots[index] < count:
                    slots[index] += 1
                    remaining -= 1
                    if not remaining:
                        break

    heights = [max(3, slot) * step + padding for slot in slots]
    extra, remainder = divmod(available - sum(heights), DAY_COUNT)
    heights = [height + extra + (index < remainder) for index, height in enumerate(heights)]
    return step, slots, heights


def render(document, start_day):
    tz = ZoneInfo(document.get("timezone", "America/New_York"))
    image = Image.new("L", (WIDTH, HEIGHT), 255)
    draw = ImageDraw.Draw(image)
    ink, muted, line = 8, 90, 176
    days = [start_day + timedelta(days=index) for index in range(DAY_COUNT)]
    daily_events = [events_for_day(document, day, tz) for day in days]
    step, slots, heights = layout_days([len(events) for events in daily_events])
    range_face = font(36, 700)
    weekday_face = font(19, 700)
    day_face = font(38, 700)
    time_face = font(17, 600)
    event_face = font(18 if step == 24 else 17)

    last_day = days[-1]
    first_label = start_day.strftime("%b").upper() + f" {start_day.day}"
    last_label = last_day.strftime("%b").upper() + f" {last_day.day}"
    draw.text((28, 27), f"{first_label} — {last_label}", fill=ink, font=range_face, anchor="lt")

    top = ROW_TOP
    for index, (day, events, slot, height) in enumerate(zip(days, daily_events, slots, heights)):
        bottom = top + height
        middle = top + height // 2
        if index == 0:
            draw.rectangle((24, top, 576, bottom - 1), fill=236)
        else:
            draw.line((30, top, 570, top), fill=line, width=1)

        draw.text((37, middle - 26), day.strftime("%a").upper(), fill=ink, font=weekday_face, anchor="lt")
        draw.text((35, middle - 5), str(day.day), fill=ink, font=day_face, anchor="lt")
        draw.line((132, top + 12, 132, bottom - 12), fill=line, width=2)

        if not events:
            draw.text((150, middle), "No events", fill=muted, font=event_face, anchor="lm")
        else:
            visible = slot - 1 if slot < len(events) else slot
            y = middle - (slot - 1) * step // 2
            for _order, start, _end, title, all_day in events[:visible]:
                if not all_day:
                    draw.text((150, y), format_time(start), fill=ink, font=time_face, anchor="lm")
                draw.text((235, y), ellipsize(draw, title, event_face, 328), fill=ink, font=event_face, anchor="lm")
                y += step
            if visible < len(events):
                draw.text((235, y), f"+ {len(events) - visible} more", fill=muted, font=event_face, anchor="lm")
        top = bottom
    return image


def main():
    parser = argparse.ArgumentParser()
    sources = parser.add_mutually_exclusive_group()
    sources.add_argument("--ics", type=Path)
    sources.add_argument("--input", type=Path, help="normalized event JSON")
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--timezone", default="America/New_York")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    start_day = args.start_date or datetime.now(ZoneInfo(args.timezone)).date()
    if args.ics:
        document = document_from_ics_range(args.ics, start_day, args.timezone)
    elif args.input:
        document = json.loads(args.input.read_text())
    else:
        document = sample_document(start_day, args.timezone)
    image = render(document, start_day)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG")
    print(f"rendered {args.output}: {image.width}x{image.height}, {image.mode}")


if __name__ == "__main__":
    main()
