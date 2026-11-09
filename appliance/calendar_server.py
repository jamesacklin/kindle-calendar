#!/usr/bin/env python3
"""Serve a rolling six-day work agenda to one Kindle on the home network."""

import argparse
import hashlib
import io
import os
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from zoneinfo import ZoneInfo

from render_six_day import document_from_ics_bytes, render

MAX_ICS_BYTES = 8_000_000
REFRESH_SECONDS = 300


@dataclass
class CalendarFeed:
    source: str | Path
    number: int
    next_fetch: float = 0.0
    ics: bytes | None = None
    day: date | None = None
    events: list | None = None

    def parse(self, ics, today, timezone):
        document = document_from_ics_bytes(ics, today, timezone)
        self.ics = ics
        self.day = today
        self.events = document["events"]

    def get(self, today, timezone):
        if time.monotonic() >= self.next_fetch:
            try:
                url = self.source.read_text().strip() if isinstance(self.source, Path) else self.source
                if not url.startswith("https://calendar.google.com/calendar/ical/"):
                    raise ValueError("expected a Google Calendar iCal HTTPS URL")
                with urlopen(url, timeout=30) as response:
                    downloaded = response.read(MAX_ICS_BYTES + 1)
                if len(downloaded) > MAX_ICS_BYTES:
                    raise ValueError("iCal feed exceeds 8 MB")
                if downloaded != self.ics:
                    self.parse(downloaded, today, timezone)
            except Exception as exc:
                print(f"calendar feed {self.number} refresh failed: {type(exc).__name__}", flush=True)
                self.next_fetch = time.monotonic() + 60
            else:
                self.next_fetch = time.monotonic() + REFRESH_SECONDS

        if self.ics is not None and self.day != today:
            self.parse(self.ics, today, timezone)
        return self.events


class CalendarState:
    def __init__(self, url_file: Path | None, timezone: str, *, urls=()):
        sources = [url_file] if url_file is not None else list(dict.fromkeys(urls))
        self.feeds = [CalendarFeed(source, number) for number, source in enumerate(sources, start=1)]
        self.timezone = ZoneInfo(timezone)
        self.lock = threading.Lock()
        self.events = None
        self.day = None
        self.png = None
        self.etag = None

    def get(self, now=None):
        with self.lock:
            today = (now or datetime.now(self.timezone)).astimezone(self.timezone).date()
            try:
                events_by_feed = [feed.get(today, self.timezone.key) for feed in self.feeds]
                available = [events for events in events_by_feed if events is not None]
                if not available:
                    raise RuntimeError("no calendar feed is available")
                events = [event for feed_events in available for event in feed_events]
                if events != self.events or today != self.day or self.png is None:
                    document = {"timezone": self.timezone.key, "events": events}
                    image = render(document, today)
                    out = io.BytesIO()
                    image.save(out, format="PNG")
                    self.png = out.getvalue()
                    self.day = today
                    self.events = events
                    self.etag = '"' + hashlib.sha256(self.png).hexdigest() + '"'
                    print(f"rendered {today}: {len(self.png)} bytes", flush=True)
            except Exception as exc:
                print(f"calendar render failed: {type(exc).__name__}", flush=True)
                if self.png is None:
                    raise
            return self.png, self.etag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url-file", type=Path, help="read a single iCal URL from a file instead of CALENDAR_URLS")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timezone", default="America/New_York")
    access = parser.add_mutually_exclusive_group(required=True)
    access.add_argument("--allow-ip", action="append")
    access.add_argument("--allow-any", action="store_true", help="rely on network-level access controls")
    args = parser.parse_args()
    urls = os.environ.get("CALENDAR_URLS", "").split()
    if args.url_file is None and not urls:
        parser.error("provide --url-file or set CALENDAR_URLS to one or more Google iCal URLs")
    allowed = set(args.allow_ip or ())
    state = CalendarState(args.url_file, args.timezone, urls=urls)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if not args.allow_any and self.client_address[0] not in allowed:
                self.send_error(403)
                return
            if self.path != "/calendar.png":
                self.send_error(404)
                return
            try:
                png, etag = state.get()
            except Exception:
                self.send_error(503, "calendar unavailable")
                return
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("ETag", etag)
            self.end_headers()
            self.wfile.write(png)

    state.get()  # Start only with a successfully fetched and rendered calendar.
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"serving on {args.bind}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
