# Minimal Kindle appliance userspace

Target: K4S B00E, MX50 YOSHI rev 50011, kernel 2.6.31-rt11-lab126.
User requested replacing most userspace, not merely hiding the reader UI.

## Architecture and milestones

1. Build a separate application filesystem and our own display supervisor.
   Use the exact ARM EABI loader/libraries from the verified device backup for
   compatibility. Do not assume a current distro's binaries support this kernel.
2. Validate the isolated shell and renderer on the device before changing any
   startup behavior. This chroot test is an intermediate step, not a completed
   userspace replacement. A chroot alone does not stop Amazon applications.
3. Replace running application services: stop reader framework, webreader and
   browser through their service controls; run our supervisor. Measure process
   list, RAM, USB access, charge state and power-button behavior. Use an
   independently launched timed rollback to restore the original services.
4. After successful trials, create an opt-in appliance boot mode that bypasses
   application startup, starts our services, and offers a stock-mode escape.
   Keep original application files for recovery; removing files is unnecessary.
5. Reduce remaining platform userspace only when dependency tests demonstrate
   it is safe. A separate root filesystem/PID 1 is later work, not part of this
   first prototype. No bootloader, kernel, partition-table or rootfs flash is
   proposed or authorized by this plan.

## Dependency findings from actual saved root filesystem

| Component | Initial treatment | Reason |
|---|---|---|
| Kernel, modules, firmware and eink lifeguard | Retain | E-ink/platform support is more than /dev/fb0 alone. |
| SysV init, early mounts, udev and kdb | Retain initially | Verified boot/hardware initialization. |
| D-Bus/LIPC and pmond | Retain | powerd and volumd are launched/managed through pmond. |
| powerd | Retain | Battery, power button and suspend dependencies need testing. |
| volumd and USBNetwork/SSH | Retain as maintenance | Existing working gadget switching and recovery access. |
| Java reader, webreader, browserd | Replace as running services | Not needed for image display; stop via init/pmond to avoid respawn. |
| Wi-Fi, time sync, watchdogs and other daemons | Inspect individually | Do not infer harmlessness from names. |
| Display service | Replace our overlay experiment | New supervisor owns application rendering once reader stops. |

BusyBox from this device uses /lib/ld-linux.so.3, glibc 2.12.1, and ELF minimum
kernel note 2.6.16. eips needs libc and libdl. The build verifies DT_NEEDED
closure, but this cannot prove runtime dlopen paths or hardware behavior.

## Prototype artifact

Run `python3 appliance/build.py` once to create appliance/build/rootfs and
application-userspace.tar.gz. It copies only identified executables/libraries
from the saved image. It does not include account credentials, execute ARM
code on the host, or install/flash anything. Host source filesystem is read
with debugfs without -w. Applet availability still needs live validation.

The supervisor expects /data/current.png and an optional /data/DISABLED.
It hashes every five seconds while running and redraws only changed images;
it is a simple prototype, not final event-driven power management. Files must
be replaced atomically by a future receiver. This is not a PID 1 program.

Proposed test location: a new directory in /var/local after checking space;
user FAT storage cannot faithfully store Unix symlinks and permissions.
Bind only required pseudo-filesystems/data for the trial and unmount afterward.
Do not change root, init, boot arguments or global libraries for this trial.

## Rollback and gates

- Before live service replacement: working key-based SSH plus timed rollback,
  confirmed original service state and battery power; disable our old display
  experiment during the test so two renderers cannot compete.
- First trial ends by restoring original services, unmounting prototype binds,
  and leaving files available for inspection. No autonomous permanent cutover.
- Persistent cutover needs a tested stock-mode path and reliable maintenance
  access without the documents menu. Do not depend on entering search commands
  after disabling that menu.
- Root backup exists and is verified, but bootloader/kernel/diagnostics backup
  and an exercised low-level recovery path do not. Do not present flashing as
  recoverable merely because a root image exists.

Current status: prototype staged in /var/local/calendar-appliance-trial and
its isolated shell successfully run on the Kindle. With PATH=/bin:/usr/sbin,
uname reports armv7l; sleep/test/ls/md5sum work. Renderer and library checksums
match host files. Isolated eips rendering succeeded with dev/proc/sys binds.
Second timed trial stopped cvm/browserd/webreader and ran our supervisor in
the chroot; user confirmed the image visible. SSH and charging remained
working. Sleep/wake, image replacement, long-running stability and appliance
boot remain untested. Existing overlay boot hook remains installed. No
flashing or new startup changes performed.

The first trial aborted on the stock browser stop script's exit 137, likely
its broad killall matching the calling script. Its independent timed rollback
restored stock services and unmounted trial binds. Revised trial uses pmond
stop and executable-verified PIDs for browser/webreader. Trial scripts are
single-run diagnostics (fixed state directories); do not blindly rerun them.
Second rollback also completed: supervisor exited, all three application
services returned, and trial binds were removed. Device is back in stock
application mode with the earlier overlay hook retained. Trial files remain
for inspection; no permanent appliance-mode cutover has occurred.

Third trial: USB atomic PNG replacement and render-on-change succeeded.
Supervisor now logs successful/failed refreshes and reads a refresh token.
Initial short-lived LIPC event listener missed an observed Screen Saver
transition; replaced during trial with power-state.sh polling actual powerd
status every2 seconds. It detected Screen Saver and requested a successful
redraw. Physical sleep/wake confirmation and deep-suspend recovery remain
pending. Polling is a prototype; it does not disable suspend or prove USB
will remain available in deeper power states. Do not enable appliance boot
based solely on this trial. Latest source scripts differ from initial tarball.
Third rollback completed successfully: both prototype processes exited,
all stock application daemons returned and temporary mounts were removed.
No physical wake result was available before restoration.

Fourth trial: user operated the power button while USB-connected. Polling
captured repeated Active/Screen Saver transitions and supervisor logged
successful redraws after each. User reports image appears to work. Brief
power-button state transitions/redraw are now validated under USB power;
full shutdown, deeper suspend and reboot/network recovery are NOT validated.
Ended early with restore-now: prototype exited, binds removed, cvm/browserd/
webreader and earlier overlay restored. No persistent boot changes.

USB boot recovery gate remains FAILED: delayed one-shot hook lost access to
USBNetwork script after userstore export. Its fallback later disabled manually
restored networking. A second early synchronous one-shot attempt also exposed
only storage; internal failure log still needs recovery/inspection. Both test
hooks were renamed to disabled files, with originals retained. Do not deploy
persistent appliance mode or rerun these experiments blindly. No active
emergency.sh, no USBNetwork auto flag, no firmware/rootfs changes.
Second test log recovered over USB telnet: com.lab126.volumd returned
lipcErrNoSuchSource, so early invocation preceded daemon readiness. Fallback
completed ALREADY_STORAGE. SSH restored key-only and USB-address-bound; both
boot tests disarmed. Next design must gate on actual LIPC readiness and avoid
relying on exported /mnt/us for startup assets. No further trial installed.

Third USB boot trial used [usb-ready-worker.sh](../firmware/experiments/usb-ready-worker.sh)
from internal storage, polling
volumd readiness before requesting gadget mode and starting USB-bound key-only
SSH. It still exposed only storage; test3 internal log needs recovery. Hook
was disabled recoverably. The original package README_FIRST.txt BUGS explicitly
warns about K4 computer-connected boot and g_ether resource-busy errors even
with USE_VOLUMD. Do not treat another timing change as a justified fix without
the live kernel/device logs. Readiness failure and kernel gadget-busy failure
are separate possibilities. Reliable unplugged boot followed by cable attach
may be an intermediate operating constraint, not the final unattended goal.
Unplugged boot test4 PASSED: readiness after3s, usb0 .244/24 initialized,
USB_BOOT_TEST_READY logged, new uptime1min, pinned key-only SSH succeeded after
cable connection, charging active. ACK written to prevent timed storage switch;
test hook disabled recoverably afterward. This establishes a viable unplugged
boot -> connect USB workflow, NOT reliable reboot with USB still attached.
Permanent appliance startup has not been installed. Any next proposal must
make this constraint explicit and include a stock-mode escape independent of
the disabled reader's search menu.

Latest status supersedes that staging note: provisional opt-in persistent
manager is now installed in /var/local/calendar-appliance with userstore
emergency hook and ENABLED marker. Live takeover and stock-keep-network
recovery passed. Combined unplugged boot remains to be tested. Every boot
requires SSH confirmation within600s or disables appliance mode/restores
stock+storage. See [appliance operations](OPERATING.md). Root/system startup
files unchanged; original reader programs remain installed and platform
daemons remain running.

Combined unplugged appliance boot has now PASSED: user sees appliance card,
logs show NETWORK_READY/APPLIANCE_READY/RENDER_OK, reader daemons absent,
charging and pinned USB SSH working. Current boot explicitly CONFIRMED;
future boots retain the ten-minute confirmation gate. Persistent mode is now
active, but unattended Pi/calendar integration and connected reboot remain
unfinished. See [appliance operations](OPERATING.md) for constraints and
recovery.
Recovered test3 logs confirm volumd ready after3 seconds; subsequent network
asset wait timed out and usb0 was absent at fallback. Fallback finished, hook
disabled, ARM consumed, manual SSH restored. Current early syslog had rotated;
no captured resource-busy error proves that specific kernel cause. Readiness
was fixed, but connected-boot gadget transition remains unresolved.

USB networking reappeared as 0525:a4a2 using cdc_ether and interface
USB_INTERFACE. A memory-only NetworkManager profile assigns the host USB
address with IPv6 and autoconnect disabled. After an unplugged restart and networking toggle,
carrier and pinned SSH work with the same cdc_ether driver. Battery reports
90%, charging. Earlier no-carrier failure was not proof of a driver defect.
No device services replaced yet.
