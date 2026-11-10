# Rolling six-day calendar

`render_six_day.py` draws today plus the following five days on a 600x800
8-bit grayscale PNG. Day boundaries use `America/New_York` by default.
Recurring events and exceptions are expanded with `icalendar` and
`recurring-ical-events`; all-day and overlapping events are included.

Days with more than three events grow to use the available screen space.
If the six days still exceed the display, the busiest rows show how many
events are hidden. The renderer and service use [Inter 4.1](https://github.com/rsms/inter/releases/tag/v4.1)
from [`appliance/assets/inter/`](../appliance/assets/inter/), which includes
the font license.

To render a local preview from an exported `.ics` file:

```sh
uv venv .venv --python /usr/bin/python3
uv pip install --python .venv/bin/python -r appliance/requirements.txt
.venv/bin/python appliance/render_six_day.py --ics /path/to/calendar.ics --output appliance/build/six-day.png
```

Without `--ics`, the renderer uses sample events. `--start-date YYYY-MM-DD`
can preview the next day and verify rollover. The real-work preview in
`appliance/build/work-six-day.png` is ignored by Git, as are the feed URL in
`.secrets/work-calendar-url` and `.venv/`.

The server merges events from the configured Google iCal feeds and serves
`/calendar.png` with ETag/304. Each feed has its own five-minute cache.
If a feed fails, the server retains that feed's last good events and retries
it after one minute. `--allow-ip` limits HTTP access to named clients.

## TrueNAS deployment

The `kindle-calendar` app publishes `/calendar.png` on TCP 8765.
TrueNAS builds the image from `/mnt/apps/kindle-calendar` using the
[Dockerfile](../appliance/Dockerfile) and
[Compose configuration](../appliance/compose.truenas.yaml).
The [appliance runbook](../appliance/AGENTS.md) covers rebuild and redeployment.
Set `CALENDAR_HOST_IP` when using the Compose template from the shell.
In the TrueNAS YAML editor, replace the `host_ip` placeholder with the
intended publish address. The app uses `--allow-any` and relies on the
deployment network for access control.

In the TrueNAS app editor, set `CALENDAR_URLS` in the calendar service's
environment. Add one Google Calendar secret iCal URL per line and save the
app to apply it.

```yaml
environment:
  CALENDAR_URLS: |-
    https://calendar.google.com/calendar/ical/FIRST_PRIVATE_FEED
    https://calendar.google.com/calendar/ical/SECOND_PRIVATE_FEED
```

The URLs live in the app configuration and are visible to TrueNAS
administrators. The image contains only application code and assets.
The PNG contains private calendar details and is served over home-network
HTTP.

## Desktop service

`calendar-server.service` runs the desktop instance on port 8765. It
defaults to loopback and reads one feed from the ignored
`.secrets/work-calendar-url` file using `--url-file`. Set
`CALENDAR_DESKTOP_BIND` and `CALENDAR_DESKTOP_CLIENT` in the ignored
`.secrets/desktop.env` to override the desktop and Kindle addresses.
Check it with:

```sh
systemctl --user status calendar-server.service
journalctl --user -u calendar-server.service -n 30 --no-pager
```

The server advances the date range on the first request after local midnight.
The Kindle updates on its next successful poll. The default worker can be
delayed by deep suspend. [Hardware wake mode](POLLING.md#hardware-wake-on-battery)
lets the Kindle wake periodically on battery to fetch the image.
