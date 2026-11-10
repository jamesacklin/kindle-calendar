# Wi-Fi image polling

The live calendar runs on TrueNAS and returns a rolling six-day calendar as
a 600x800 grayscale PNG with an ETag. The Kindle reads the endpoint from its
local `IMAGE_URL` file.

The Kindle client is `poll-image.sh`, installed at
`/var/local/calendar-appliance/poll-image.sh`. One manual check:

```sh
./kindle-ssh 'base=/var/local/calendar-appliance; /bin/sh "$base/poll-image.sh" once "$(sed -n "1p" "$base/IMAGE_URL")"'
```

It checks appliance READY, sends If-None-Match when available, requires a
600x800 8-bit grayscale PNG header and a 200 response, then atomically swaps
the image only when its hash differs. The existing supervisor notices the
hash change and refreshes the e-ink display. A 304 or network failure retains
the displayed image. Curl limits transfers to 2 MB and 40 seconds.

A runtime-only loop was started at a 60-second interval for observation and
then replaced with a 900-second (15-minute) loop. The boot worker passed one
unplugged reboot test: after READY, it received304, confirmed this boot,
and started the loop. Inspect the current loop:

```sh
./kindle-ssh 'cat /tmp/calendar-appliance/wifi-client.log'
./kindle-ssh 'p=$(cat /tmp/calendar-appliance/wifi-client.pid); tr "\000" " " < "/proc/$p/cmdline"; echo'
```

Before stopping the worker, verify its current `/proc/PID/cmdline` still
matches the poller. Earlier background loops required KILL after TERM and
a check of their exact PIDs. The boot worker will start a fresh loop on a
successful next boot. The default worker uses a 900-second shell polling loop. Boot
must still start with USB physically unplugged; USB network setup remains in
the appliance manager. A separate bounded RTC test proved four successful
five-minute image transfers and renders with USB absent; the permanent
worker described below supersedes it.

## Hardware wake on battery

Install [`rtc-poll.sh`](../appliance/rtc-poll.sh) and the matching
[`wifi-client.sh`](../appliance/wifi-client.sh) in
`/var/local/calendar-appliance/`. Create an empty `RTC_POLL` file in
that directory to opt in, then restart the Wi-Fi worker or boot with USB
unplugged. After its initial successful poll, the worker can use the
hardware alarm for the next 15-minute poll on battery.

The worker waits for the charger-disconnect event to settle before arming
the alarm. After each wake it attempts the actual HTTP request up to three
times, since a connected Wi-Fi status can precede usable networking. The
display supervisor gets time to draw the image before the next sleep.
Charging and battery levels below 20% use ordinary power management.

Rename `RTC_POLL` to `RTC_POLL.disabled` over USB SSH to return to the
regular poller. The worker releases its power settings and hands off to
the original loop when it next runs.

The opt-in boot files are `/var/local/calendar-appliance/IMAGE_URL`,
`wifi-client.sh`, and the modified `manage.sh`. A copy of the pre-Wi-Fi
manager is `manage.before-wifi.sh`. To opt out before another boot, rename
`IMAGE_URL` to `IMAGE_URL.disabled` over USB SSH. On failure to poll, the
existing ten-minute watchdog disables appliance startup and restores the
reader. RTC deep-suspend wake passed the bounded test, but wall-charger
operation and true-shutdown recovery are not yet tested.

The previous horse image is saved on-device as
`rootfs/data/current.before-picsum.png`. To restore it, use a temporary file
and same-filesystem rename so the supervisor sees a complete frame. The
original family-calendar placeholder is still `current.before-horse.png`.

The [TrueNAS endpoint](CALENDAR.md) serves the calendar over local-network
HTTP. Stock curl 7.21.4 / OpenSSL 0.9.8j
failed TLS negotiation against Picsum, even though it succeeded against
example.com. Host-side fetching avoids that compatibility issue for now.
