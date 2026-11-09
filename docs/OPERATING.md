# Provisional persistent appliance mode

K4S / firmware4.1.4 only; not a firmware image or replacement PID1.

Verified: unplugged boot reached appliance mode, the Kindle fetched its image
over Wi-Fi and confirmed the boot automatically. USB-bound key-only SSH worked
after reconnection; reader apps were absent, charging active, and the system
root remained read-only. Each later boot still needs its own successful poll
and confirmation.

Boot with the USB cable physically unplugged. Wait for startup, then attach
the cable for power/data. Connected boot has failed in our trials. Do not
assume this is an unattended-reboot solution.

The existing USBNetwork emergency hook starts our internal manager only if
`/var/local/calendar-appliance/ENABLED` exists. The manager starts key-only SSH
on KINDLE_USB_IP, lets stock boot initialize hardware, then stops cvm/framework,
browserd and webreader and runs our chrooted display supervisor. Powerd,
volumd, pmond, LIPC, udev, kernel and e-ink platform helpers remain in use.

Each boot requires confirmation within ten minutes. With `IMAGE_URL` configured,
the Wi-Fi client attempts a validated image poll and confirms automatically
on success. This passed one unplugged reboot test on 2026-09-22.
If the endpoint or Wi-Fi fails, the watchdog still restores the reader.
Manual confirmation over USB SSH after checking the display and logs remains:

```sh
./kindle-ssh '/bin/sh /var/local/calendar-appliance/manage.sh status'
./kindle-ssh '/bin/sh /var/local/calendar-appliance/manage.sh confirm'
```

Confirmation applies to this boot only. It does not disable the next boot's
recovery window. Without confirmation, the manager disables appliance startup,
restores the reader, and requests USB storage. Ten minutes refers to elapsed
timer execution; deep suspend may delay it. This is provisional commissioning,
not the finished unattended family-calendar service.

Manual recovery (drops USB SSH when storage is requested):

```sh
./kindle-ssh '/bin/sh /var/local/calendar-appliance/manage.sh stock'
```

`stock-keep-network` restores reader applications and disables appliance startup
without changing USB mode, allowing recovery checks over the current link.
Original reader files have not been deleted. The marker is renamed to
`DISABLED`, not discarded. Once restored, a normal restart boots the reader.

If SSH is inaccessible, wait for recovery before trying manual USBNetwork
commands. Do not restart/toggle repeatedly during the timer. If recovery fails,
report the screen/device state rather than improvising a reset or flash.

Startup hook is `/mnt/us/usbnet/bin/emergency.sh`. It can be disabled by
renaming that exact file on a safely mounted USB storage volume. Original
system init files are unchanged by this mode. Saved earlier test hooks remain
under `emergency.sh.disabled-boot-test-*` and must not be restored accidentally.

Image: `/var/local/calendar-appliance/rootfs/data/current.png` (600x800 grayscale
PNG), replace via temporary file and same-filesystem rename. Supervisor draws
on changed image hash or power-state token. Logs/PIDs/confirmation live in
`/tmp/calendar-appliance`; startup log is `/tmp/calendar-appliance-boot.log`.
The supervisor draws a power indicator in the upper-right corner after the
calendar image. `On` means Active and `zZ` means the Kindle last reported
screensaver, suspend, or shutdown. The indicator is drawn on the Kindle and
can remain visible when the device is asleep or off.

The live image comes from the [TrueNAS calendar app](CALENDAR.md). See
[Wi-Fi polling](POLLING.md) for the endpoint and worker commands. The
[horse artwork](ARTWORK.md) and the original setup card are retained as
earlier display assets.

Four battery-only RTC wake tests fetched and displayed new images with USB
disconnected. The regular worker uses a 15-minute loop. Wall-charger
operation and recovery from a true shutdown remain open tests.
