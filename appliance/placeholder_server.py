#!/usr/bin/env python3
"""Serve one daily, Kindle-ready PNG sourced from a placeholder photograph."""

import argparse
import hashlib
import io
import os
import tempfile
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

from PIL import Image, ImageOps

SOURCE = "https://picsum.photos/600/800"


def render_source(source: str) -> bytes:
    with urlopen(source, timeout=20) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise ValueError("source image exceeded 8 MB")
    with Image.open(io.BytesIO(raw)) as original:
        if original.width * original.height > 20_000_000:
            raise ValueError("source image is too large")
        image = ImageOps.fit(original.convert("L"), (600, 800))
        out = io.BytesIO()
        image.save(out, format="PNG")
    return out.getvalue()


class RotatingImageState:
    """Cycle preloaded public images for a short, deterministic wake test."""

    def __init__(self, sources: list[str], seconds: int):
        self.frames = []
        for source in sources:
            png = render_source(source)
            etag = '"' + hashlib.sha256(png).hexdigest() + '"'
            self.frames.append((png, etag))
        self.seconds = seconds
        self.started = time.monotonic()

    def get(self):
        index = int((time.monotonic() - self.started) // self.seconds) % len(self.frames)
        return self.frames[index]


class ImageState:
    def __init__(self, cache: Path, source: str):
        self.cache = cache
        self.source = source
        self.day = None
        self.png = None
        self.etag = None

    def get(self):
        today = date.today()
        if self.day != today:
            try:
                png = render_source(self.source)
                self.cache.parent.mkdir(parents=True, exist_ok=True)
                fd, path = tempfile.mkstemp(prefix=".calendar-", dir=self.cache.parent)
                try:
                    with os.fdopen(fd, "wb") as dest:
                        dest.write(png)
                    os.replace(path, self.cache)
                finally:
                    if os.path.exists(path):
                        os.unlink(path)
                self.png = png
                self.etag = '"' + hashlib.sha256(png).hexdigest() + '"'
                self.day = today
                print(f"updated {today}: {len(png)} bytes, {self.etag}", flush=True)
            except Exception as exc:
                print(f"source refresh failed: {exc}", flush=True)
                if self.png is None:
                    raise
        return self.png, self.etag


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--cache", type=Path, default=Path(__file__).parent / "build" / "placeholder.png")
    parser.add_argument("--source", action="append", help="repeat for rotating test images")
    parser.add_argument("--rotate-seconds", type=int, default=0)
    args = parser.parse_args()
    sources = args.source or [SOURCE]
    if args.rotate_seconds:
        if args.rotate_seconds < 60 or len(sources) < 2:
            parser.error("rotation requires at least two sources and 60+ seconds")
        state = RotatingImageState(sources, args.rotate_seconds)
    else:
        if len(sources) != 1:
            parser.error("multiple sources require --rotate-seconds")
        state = ImageState(args.cache, sources[0])

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/calendar.png":
                self.send_error(404)
                return
            try:
                png, etag = state.get()
            except Exception:
                self.send_error(503, "image unavailable")
                return
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(png)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("ETag", etag)
            self.end_headers()
            self.wfile.write(png)

    state.get()  # Fail at startup if the initial source cannot be fetched.
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    print(f"serving http://{args.bind}:{args.port}/calendar.png", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
