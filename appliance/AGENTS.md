# Calendar appliance

This directory owns the host-side calendar service, Docker build, and
Kindle display and polling workers. See [calendar deployment](../docs/CALENDAR.md),
[operations](../docs/OPERATING.md), and [polling](../docs/POLLING.md). For
Kindle packages, USB setup, and firmware recovery, use the
[firmware runbook](../firmware/AGENTS.md).

## Build and verify

Run commands from the repository root.

```sh
docker build -t kindle-calendar:local appliance
CALENDAR_HOST_IP=192.0.2.42 CALENDAR_URLS=https://calendar.google.com/calendar/ical/example \
  docker compose -f appliance/compose.truenas.yaml config --quiet
.venv/bin/python appliance/render_six_day.py --output /tmp/kindle-calendar-preview.png
```

`calendar_server.py` loads Google iCal feeds and serves a 600×800
grayscale PNG. `render_six_day.py` owns the calendar layout. Kindle
`supervisor.sh` adds its power symbol locally after drawing the PNG.
`build.py` assembles the separate Kindle userspace from the verified
root-partition backup under `firmware/backups/`.

## Rebuild and redeploy on TrueNAS

The custom app is `kindle-calendar`. Its default build directory is
`/mnt/apps/kindle-calendar`, and it publishes TCP 8765. Use the TrueNAS
WebSocket client in `~/src/home-network` with credentials from its
ignored `.env` source. Bound the read if that source is a named pipe.

1. Build locally and validate the Compose file. Sync only the Docker
   inputs listed in [`.dockerignore`](.dockerignore) to the TrueNAS
   build directory.
2. Keep the live `CALENDAR_URLS` runtime setting in the TrueNAS app.
   Preserve the existing value and publish address when updating Compose.
   Set `CALENDAR_HOST_IP` when using the public template. Keep deployment
   values out of the build context, Git, and command output.
3. Redeploy the app with its current Compose configuration or apply
   the intended configuration update. The live `pull_policy: build`
   rebuilds from the NAS source directory. Wait for the TrueNAS job
   and confirm the app reports `RUNNING`.
4. Verify `/calendar.png` returns a valid 600×800 grayscale PNG from the
   network you intend to serve and that the Kindle can poll it over Wi-Fi.
   The regular worker polls every 15 minutes.
