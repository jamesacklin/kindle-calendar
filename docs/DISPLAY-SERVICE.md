# Standalone persistent image on Kindle 4

Status: this is the earlier overlay experiment, not the appliance userspace.
Its intended wake-redraw behavior below was not validated: the user saw the
documents menu after sleep/wake. Do not rely on it for kiosk operation.
See the [appliance plan](PLAN.md) for the replacement work and tested limits.

This stage needs neither a Raspberry Pi nor a calendar account.

The image lives at `/mnt/us/calendar-display/current.png`, not `/tmp`.
`service.sh` uses stock `eips -f -g` to render it, waits for powerd's
sleep/wake events, and redraws after those events. Normal sleep and the stock
reader framework remain enabled. Pressing other reader buttons may still draw
over the image; this is not a locked-down kiosk.

Startup uses a new `/etc/init.d/calendar-display` script and a new
`/etc/rc5.d/S99calendar-display` symlink. It launches a background process
without waiting for the renderer. The background process allows 35 seconds
for normal boot before its first draw. Missing image/service or a `DISABLED`
marker makes it do nothing. No original Amazon startup file is replaced.

Brief power presses still sleep/wake. The stock screensaver or UI may appear
briefly, followed by the saved image. A normal restart can show the normal
boot screen and Home screen before the saved image appears. A forced shutdown
or prolonged power-button hold is not equivalent to sleep; do not interrupt
filesystem writes. USB networking still defaults to off after reboot and may
need the previously documented manual toggle for maintenance.

## Control over USB SSH

From this workspace, with the USB network configured:

```sh
./kindle-ssh '/bin/sh /mnt/us/calendar-display/service.sh status'
./kindle-ssh '/bin/sh /mnt/us/calendar-display/service.sh redraw'
./kindle-ssh 'cat /tmp/calendar-display.log'
```

To disable persistently and return to the normal reader on next boot, create
an empty `DISABLED` file inside `calendar-display` using USB mass storage.
The running service checks the marker at least once per event-listener cycle
(roughly a minute while awake). It changes no persistent power settings.
Move that marker out of the folder to enable again and restart normally.

To uninstall the boot hook, disable first, then (over working USB SSH) remove
only `/etc/rc5.d/S99calendar-display` and `/etc/init.d/calendar-display` after
temporarily remounting root writable, and immediately return root read-only.
The service/image folder can be retained or archived. These exact paths did
not exist before installation. No uninstallation has been performed.

## Backups and limits

`firmware/backups/2026-09-21-before-jailbreak/` contains the checksum-verified
original user volume. `firmware/backups/2026-09-21-before-display-service/`
contains a root partition image after jailbreak/USBNetwork and before this boot hook, plus its
verification manifest once the backup completes. These are not a complete
device/bootloader recovery image and should not be flashed casually.

Logs and PID file are in RAM. The service is one process waiting for events,
not a loop continually refreshing the panel. It redraws once initially and
on selected sleep/wake events. No network access or remote calendar is required.

The [technical log](TECHNICAL-LOG.md) records the reboot tests and their results.
