# Kindle family-calendar display: feasibility and proposed implementation

Status update 2026-09-21: jailbreak and USBNetwork installed with user approval;
SSH over USB and concurrent charging verified. A PNG was transferred to /tmp
with matching checksum and rendered using built-in eips (exit 0); physical
screen confirmation was provided by the user. No FBInk installation needed for
this test: the existing eips renderer successfully displayed the grayscale PNG.

## Confirmed implementation details

- Board: Amazon.com MX50 YOSHI, revision 50011, ARMv7 Cortex-A8 CPU part 0xc08.
- Firmware: /etc/version.txt reports 001-H303_yoshi-354363, dated May 30 2019.
- Framebuffer: eink_fb, 600x800, 8bpp.
- Networking mode: 0525:a4a2, CDC/RNDIS gadget, host cdc_subset driver working.
- USB SSH at KINDLE_USB_IP from USB_HOST_IP. Local helper `./kindle-ssh`
  uses a project-only key/known_hosts and RSA compatibility option. No global
  SSH settings changed. Temporary NetworkManager settings apply to the current
  connection only; reconnect persistence is not configured yet.
- Battery 53%, charging yes during SSH. This validates simultaneous power/data,
  but not overnight power balance or cold-boot reliability.
- Built-in `/usr/sbin/eips -f -g /tmp/display-test.png` returned success. For a
  static PNG calendar, use this as the initial renderer in the service design;
  repeated refresh and unattended operation still need testing. FBInk remains
  an option if more control over refresh behavior becomes necessary.
- Stock UI, screensaver and sleep behavior are unchanged; they can overwrite
  the test. No automatic networking or display startup hook enabled.
- Default USBNetwork permissive USB auth/telnet remains a deployment issue;
  key login is working but does not by itself disable those defaults.

## Identification

The USB-observed serial prefix B00E identifies the **Kindle 4 non-touch Silver
(2011), K4/K4S**, per the developer-maintained
[serial table](https://wiki.mobileread.com/wiki/Kindle_Serial_Numbers).
Printed model supplied by user: D01100. User read firmware **4.1.4 (3543630001)**
from Settings. Physical board revision remains unknown; USB bcdDevice 1.00
does not identify it.

Observed USB VID:PID 1949:0004; USB 2 high speed, mass storage interface
08/06/50 only. No current USB network, serial, MTP, or vendor interface.
The accessible user disk contains one 1.36 GiB FAT32 partition; internal root,
diagnostics, and boot partitions have not been inspected. No obvious jailbreak
or SSH artifacts found on the user volume; this cannot prove an unmodified OS.

## Compatibility evidence

- [K4 hacking documentation](https://wiki.mobileread.com/wiki/Kindle4NTHacking)
  explicitly covers firmware 4.0.0 through 4.1.4. Its documented jailbreak
  installs a developer signing key, then permits additional packages. It
  recommends the K4 USBNetwork package for SSH; factory diagnostics SSH is
  only available on some devices, so it is not a dependable architecture.
- [Original K4 jailbreak publication](https://www.mobileread.com/forums/showthread.php?t=191158)
  supplies kindle-k4-jailbreak-1.8.N.zip. Its older thread title ends at 4.1.2;
  the linked wiki explicitly includes 4.1.4. Package contents have not yet
  been downloaded/audited, and compatibility is documented, not locally tested.
- [USBNetwork maintainer thread](https://www.mobileread.com/forums/showthread.php?t=88004)
  includes kindle-usbnetwork-0.57.N-k4.zip and describes SSH over USB or Wi-Fi.
  Use the K4 package and its README, not K5/Touch/Paperwhite instructions.
- [FBInk upstream README](https://github.com/NiLuJe/FBInk/blob/master/README.md)
  supports Kindles from K2 onward and PNG image rendering with e-ink refresh.
  Use a Kindle-compatible build with image support; modern ARM binaries are
  not interchangeable with binaries for this old OS.
- [Actual K4 FBInk report](https://github.com/NiLuJe/FBInk/issues/32) shows a
  600x800 framebuffer and legacy einkfb handling. It also reports an old
  noninteractive SSH invocation problem. Verify the chosen binary's remote
  execution behavior rather than assuming a successful interactive test is
  sufficient. Screen dimensions/orientation still need confirmation locally.

## Architecture decision

| Option | Assessment |
|---|---|
| USB networking + USB power | Preferred. Documented K4 SSH route; isolated direct link, single cable. Needs jailbreak/package installation and tests of charging and suspend behavior. |
| Wi-Fi + USB power | Viable fallback using the same renderer. Adds Wi-Fi setup and sleep/reconnection handling; restrict SSH exposure. |
| Mass-storage image transfer | Can transfer files, but does not itself provide automatic rendering or refresh. Host/device ownership of the user volume complicates continuous updates. Not recommended for unattended operation. |

Feasible in principle, with strong model-specific evidence. The Kindle would
run a small local rendering program; it does not become a generic USB monitor.
“Read-only display” describes its user-facing role, not literally write-free
installation or operation.

## Proposed Pi service

1. A systemd timer runs a calendar job every five minutes (adjustable). Calendar
   credentials stay on the Pi. Fetch data and render a 600x800 grayscale PNG,
   or 800x600 with explicitly tested landscape handling. Include last-updated
   time so stale data is visible.
2. Validate dimensions and compare image hashes. Skip unchanged images. Use a
   job lock, bounded connection timeout, and retry on the next timer tick.
3. Give the USB link a dedicated private subnet, chosen after checking the
   actual USBNetwork configuration and Pi routes. No gateway, forwarding,
   Internet sharing, or DHCP dependency is necessary. Match the device using
   observed networking-mode identifiers, not today's mass-storage identifiers.
4. Use SSH keys and a fixed command to transfer a PNG into a temporary file
   and invoke a narrowly scoped Kindle rendering script. Restrict the key to
   that operation where supported by the installed SSH server. Avoid relying
   on modern scp's SFTP default if the old server lacks SFTP; SSH stdin transfer
   is sufficient. Validate the file before atomic replacement.
5. Render with FBInk using the confirmed K4 framebuffer settings. Start with
   a full refresh only on changed images. Evaluate ghosting before adopting
   partial refreshes. Keep the last good image on network failure.
6. First test manually, without boot hooks. Resolve stock UI/screensaver
   interference and suspend behavior reversibly, then add a removable startup
   hook only after reboot/reconnect tests pass. Test Pi power loss, cable
   reconnection, timed updates, and overnight charging/display stability.

## Proposed device changes — not authorized or executed

| Change | Purpose | Rollback / limitation | Risk assessment |
|---|---|---|---|
| K4-specific jailbreak via documented diagnostics route | Permit signed community packages | Audit the exact package's cleanup/uninstall path before proceeding. Exiting diagnostics is not necessarily full jailbreak removal. A user-volume backup does not restore internal firmware. | Nonzero boot/recovery risk from incorrect package, interrupted writes, or diagnostics trouble; no credible numeric brick probability. |
| K4 USBNetwork package | Provide SSH and USB networking | Review package uninstaller and manual return-to-storage procedure first; initially avoid automatic activation at boot. | Configuration can remove normal USB storage access or expose a privileged shell; package install modifies internal state. |
| FBInk and calendar wrapper in user storage | Display image and refresh | Remove files and restore transient UI/power settings; retain stock boot behavior during trials. | Much lower persistence risk than firmware work; UI conflicts, hangs, and power drain require testing. |

No firmware upgrade/downgrade, repartitioning, factory reset, or raw block write
is proposed. Before any jailbreak, fully charge and check stable power/USB,
copy the user volume read-only with a checksum manifest, download and audit
the exact original packages on the host, and document their exact recovery
steps. User-volume backup protects books/settings there, not boot recovery.
After shell access, inventory internal partitions and make appropriate backups
before further persistent changes. Recovery needing flashing would be a new,
separately reviewed action; a working rollback cannot currently be guaranteed.

Next safe phase: host-only package audit and user-volume backup when reattached.
Obtain explicit approval before copying exploit files, entering diagnostics,
installing packages, or enabling boot-time changes, as requested by the user.

## Next implementation phase after successful physical display test

The original feasibility question is resolved: this specific Kindle can display
a host-rendered image and refresh over the same USB cable that charges it.
The user confirmed the actual panel showed the test correctly.

Start the Pi implementation with eips as renderer. Still required:

1. Calendar source/access choice (e.g. private ICS feed, Google Calendar, or a
   local calendar file), plus the Pi's OS and connection details.
2. Pi-side render-and-push service and timer, retaining credentials on the Pi.
3. Reversible stock-UI/screensaver handling with a documented normal-reader
   restoration command. The current test does not prevent UI overwrites.
4. USB reconnect and cold-boot behavior, consistent address configuration,
   authentication tightening, and timed/overnight validation.

No further approval is needed to repeat the authorized reversible display
tests. New boot persistence or recovery writes should be described before use.
