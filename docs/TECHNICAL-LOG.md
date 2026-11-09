# Kindle display feasibility — technical log

The public log uses placeholders for local network addresses, device IDs,
and host paths. Older entries retain the project paths used at the time.

## 2026-09-21, 14:06 EDT — initial discovery

Scope: read-only host discovery. No device writes, mounts, ejects, resets,
mode switches, firmware changes, exploits, or installations performed.
Only this workspace log was created. Device serial is abbreviated here.

### Commands and relevant output

- `pwd`; `rg --files -g AGENTS.md -g '*kindle*' -g '*log*' .`; `ls -la`;
  checked parent AGENTS.md files: workspace initially empty apart from reserved
  directories; no applicable instruction file found.
- `uname -a`: Linux HOST 7.0.0-31-generic, x86_64,
  Ubuntu kernel build dated 2026-08-01.
- `lsusb`; `lsusb -t`: initial sandbox lsusb failed with libusb -99.
  Repeated outside sandbox: initially only root hubs, Genesys 05e3:0608 hub,
  MSI 1462:7c95 lighting, Intel 8087:0aa7 Bluetooth. Kindle appeared subsequently.
- `dmesg | tail -n 100`: kernel buffer permission denied even outside sandbox.
  Used readable kernel journal instead.
- `journalctl -k -n 100 --no-pager`; `journalctl -k -b --no-pager`
  filtered for USB, Kindle, Amazon, networking, serial, and SCSI events;
  additional `journalctl -k -n 25 --no-pager` and journal since 14:06:30:
  at 14:06:34 a device appeared on port 5-4; at 14:06:39 descriptor read/64
  returned error -71, followed by successful enumeration as Amazon Kindle
  1949:0004, bcdDevice 1.00. usb-storage bound to 5-4:1.0.
  At 14:06:40 SCSI reported Kindle Internal Storage 0100; /dev/sda attached,
  with `Media removed, stopped polling` and `Power-on or device reset occurred`.
  These are kernel observations, not actions issued by this session.
- `lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,SERIAL` and repeated
  with `-e 7`: host Samsung 970 EVO Plus 1TB, 1G EFI and 930.5G ext4;
  newly attached Kindle sda reports 0B, no partition, filesystem, or mount.
- `findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS`; filtered vfat/exfat/GVFS:
  no Kindle mount. Sandbox mount flags describe the sandbox view, not actual
  host read-only protection. Host EFI is rw. No Kindle filesystem was read.
- `ip -brief link`; `ip -brief addr`: sandbox netlink denied; succeeded
  outside sandbox. Interfaces lo, WIRED_INTERFACE, WIFI_INTERFACE, VPN_INTERFACE only.
- Inspected USB sysfs vendor/product attributes and `/sys/class/net`;
  no ttyUSB* or ttyACM* in sysfs. udev version 259.
- `rg -n -i 'kindle|amazon|1949|usbnet|rndis' /etc/udev/rules.d /usr/lib/udev/rules.d`:
  no Kindle-specific match; only unrelated cellular modem RNDIS comments.
- `udevadm info --query=all --path=/sys/bus/usb/devices/1-7` identified
  the existing Genesys hub before the Kindle was available.
- `udevadm info --query=all --path=/sys/bus/usb/devices/5-4`:
  Amazon Kindle; serial prefix B00E; ID_USB_INTERFACES=:080650:;
  ID_REVISION=0100; path pci-0000:2d:00.3-usb-0:4.
- `lsusb -v -d 1949:0004` outside sandbox:
  bus 005 device 002, USB 2.00, negotiated 480Mbps; one configuration,
  one interface, alternate setting 0; class 08 mass storage, subclass 06 SCSI,
  protocol 50 hexadecimal (80 decimal) bulk-only. Bulk endpoints 0x81 IN,
  0x01 OUT, packet size 512. bcdDevice 1.00. Descriptor self-powered,
  MaxPower 2mA (not a measurement of actual charging demand).
  Tool warned `Couldn't open device, some information will be missing`;
  cached descriptors and sysfs/udev corroborate the exposed interface.
- `ls -la /media/LOCAL_USER /run/user/1000/gvfs`: no /media/LOCAL_USER;
  GVFS contained unrelated SMB mounts only.
- Final check: `udevadm info --query=all --path=/sys/class/block/sda`;
  read sysfs `size`, `removable`, `ro`; repeated lsblk and recent journal.

### Deductions and uncertainties

- The connected device is an Amazon Kindle with serial prefix B00E.
  The USB database label “Kindle 3/4/Paperwhite” is shared and cannot establish
  the exact model. No model is inferred from appearance.
- bcdDevice 1.00 / SCSI revision 0100 do not establish the hardware board
  revision or installed Kindle firmware. Both remain unknown.
- Currently mass storage only: no MTP, USB network, serial/debug, or
  vendor-specific interface is advertised. This does not rule out other
  modes that might be enabled later or an existing jailbreak.
- The 0B LUN means the host has no accessible storage medium at present;
  it does not establish physical flash capacity or corruption. Internal
  system partitions are not mapped by this observation.
- One descriptor failure occurred before successful enumeration. Connection,
  power, and device readiness remain possible factors; cause unconfirmed.
- Jailbreak markers, SSH configuration, firmware metadata, and rendering
  tools cannot yet be inspected because no Kindle filesystem is accessible.
- Research deferred as requested until model and firmware are identified.
  FBInk support and model-specific USB networking remain unverified.

### Next safest action

Read the Kindle's Device Info/settings screen for model and exact firmware,
and report its present screen (USB drive mode, home, charging, etc.). Avoid
reset, update, diagnostics, or mode-switch commands. If storage remains absent,
check a known data-capable cable and direct USB port after recording device
state; repeat enumeration. When storage becomes accessible, establish a
read-only inspection method before traversing it, preventing access-time writes.

### Provisional architecture requirements (not yet a compatibility claim)

Preferred design, conditional on supported device shell/rendering access:
Pi systemd timer renders a calendar at the verified panel dimensions, compares
the image hash, transfers changed images over USB networking, and invokes a
Kindle renderer for a controlled refresh. Serialize jobs, use atomic image
replacement, bounded retries, and retain the last successful image. Determine
refresh waveform, sleep policy, framework interference, and charging behavior
from this model's documentation and later approved tests.

Wi-Fi plus USB power is the alternative if USB networking is unsuitable.
Mass-storage file transfer alone does not demonstrate a way to trigger local
rendering or refresh; a supported viewer or device-side program is still needed.
Select among these only after identification and compatibility research.

Any proposed firmware, partition, exploit, or unknown block-device write must
first be presented with purpose, exact target, rollback, and brick risk.

## 2026-09-21 — charging screen and printed model supplied

- User reports the device shows charging and its printed model is D01100;
  firmware is unknown. Record this alongside USB serial prefix B00E; exact
  retail generation mapping and board revision have not been verified.
- Repeated `lsusb`, `lsusb -t`, `lsblk -e 7 -o
  NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,SERIAL`, `findmnt -rn -t vfat,exfat`,
  and `journalctl -k --since '2026-09-21 14:06:30' --no-pager`.
  Kindle remains 1949:0004, mass storage only; sda remains 0B and unmounted.
  No subsequent USB/kernel events were returned.
- Read this log with `sed -n '1,240p' TECHNICAL-LOG.md`.
  `id` confirms the local account, with adm/sudo/plugdev membership;
  `sudo -n true` reports interactive authentication required. No privileged
  device operation was attempted. Unrestricted tool access does not grant root.
- Charging is consistent with a device that is not ready to export storage,
  but does not prove low battery is the cause. No accessible metadata exists
  to read the firmware at this point. No device changes made.
- Next safest action: leave attached to charge, try a brief normal wake press,
  and, if the home screen becomes available, read Settings' version information.
  Avoid a long power-button hold, reset, update, or diagnostics. If it remains
  on a charging-only screen, report that state; firmware-dependent research
  remains deferred under the user's original constraint.

## 2026-09-21, 14:19 EDT — storage available; read-only inspection

Commands run:

- `date -Is`; `lsusb`; `lsusb -t`; `lsblk -e 7 -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,SERIAL`;
  `findmnt -rn -t vfat,exfat`; `ip -brief link`; `journalctl -k -n 45 --no-pager`;
  `ls -l /dev/sda /dev/sda1`; `command -v mdir`; `command -v udisksctl`.
- Kindle re-enumerated at 14:17:23 as bus 005 device 005, still 1949:0004;
  another descriptor error -71 preceded successful enumeration. At 14:18:03
  capacity became 2,846,720 sectors of 512 bytes (1.36 GiB), with sda1.
- Host automounted sda1 read-write at KINDLE_MOUNT before inspection.
  Ran `udisksctl unmount -b /dev/sda1 && udisksctl mount -b /dev/sda1 --options ro`;
  verified `findmnt -rn -S /dev/sda1 -o SOURCE,TARGET,FSTYPE,OPTIONS` reported ro.
  Clean unmount can flush pre-existing host writes; no intentional content
  writes were issued by this session. All file inspection occurred after ro verification.
- `ls -la KINDLE_MOUNT`; `find` of non-document files to depth 3;
  `udevadm info -q all -n /dev/sda1`; `lsusb -v -d 1949:0004`.
- Recursive filename-only search for version, firmware, jailbreak, usbnet,
  dropbear, authorized_keys, id_rsa, update*.bin, diagnostic, fbink, and device
  returned no matches. Listed system directory names to depth 4.
- Read `driveinfo.calibre`: generic Amazon Kindle name and Calibre 4.12.0,
  with a 2020 connection timestamp. Calibre version is NOT Kindle firmware.
- Read sysfs sda size and sda1 start/size; `df -h KINDLE_MOUNT`.

Findings:

- Exposed DOS partition table: one FAT32 partition type 0x0b, start sector 16,
  length 2,846,704 sectors, filesystem size 1,457,512,448 bytes, label Kindle,
  UUID 0000-000B. About 97 MiB used, 1.3 GiB available. This is the USB-exported
  user volume, not evidence of the complete internal flash partition layout.
- Root contains documents, system, .active-content-data, old Mac metadata,
  Windows System Volume Information, Calibre metadata, and a zero-length
  DONT_HALT_ON_REPAIR marker dated today. Marker origin/meaning unverified;
  it alone is not evidence of a jailbreak and was not modified.
- No obvious jailbreak/developer directories or firmware metadata found.
  No private keys or book contents were read. Internal root filesystem remains
  unavailable, so jailbreak status and board revision are still unknown.
- One mass-storage interface only; no new Kindle network interface. The
  vendor-specific interface on port 5-3 belongs to an unrelated Pixel phone
  (18d1:4ee7), not the Kindle, and was not investigated further.
- Firmware-dependent research and FBInk compatibility remain deferred.

Next safest action: unmounted using `udisksctl unmount -b /dev/sda1` and
confirmed no mount using `findmnt -rn -S /dev/sda1`. User can disconnect the
USB cable and read Settings' firmware version, then reconnect for charging.
No eject/power-off command, exploit, reset, installation, or firmware change
was performed. Device identity remains printed D01100 plus serial prefix B00E,
pending authoritative generation mapping once firmware is available.

## 2026-09-21 — firmware identified; feasibility research

- User reports Settings: Kindle 4.1.4 (3543630001).
- Began web research only after this firmware report. Queried MobileRead for
  B00E identification and K4 4.1.4 USBNetwork/jailbreak; queried upstream FBInk
  support. Read developer-maintained serial table, K4 hacking wiki, original
  K4 jailbreak thread, USBNetwork maintainer thread, FBInk README and K4 issue
  #32. Also opened the legacy KindleModding K4 page; conclusions rely on the
  primary project/developer sources linked in FEASIBILITY.md.
- Serial B00E maps to K4 non-touch Silver (2011). Board revision unknown.
  Wiki explicitly covers 4.1.4; FBInk supports K4. USBNetwork is the preferred
  proposed transport; single-cable charging/suspend behavior needs testing.
- Ran `lsblk -e 7 -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL`: current sda
  reports 0B again with no mount. This is a state snapshot, not evidence of
  data loss; the user was navigating Settings after disconnecting the cable.
- `git status --short` reports no git repository. Created FEASIBILITY.md using
  apply_patch and appended this log; no device action performed this turn.
- Documented architecture, known limitations, proposed changes, rollback limits,
  and risk assessment in FEASIBILITY.md. No packages downloaded or installed.
- Next safest action: host-only review of original package contents and a
  read-only user-volume backup when the volume is available; explicit approval
  required before the proposed jailbreak/device installation phase.

## 2026-09-21 — user says “ok let's do it”; preparation

- Started authorized backup/package-review phase. `lsblk -e 7 -o
  NAME,SIZE,FSTYPE,LABEL,MOUNTPOINTS,MODEL,SERIAL` still shows the same Kindle
  serial but sda 0B, no partition or mount. Read FEASIBILITY.md; listed workspace.
- Asked user to reconnect into USB Drive Mode and report battery state while
  continuing independent package review. No storage backup possible yet.
- Reopened original MobileRead threads and resolved original attachment links.
  Web reader cannot handle ZIP, so downloaded both via `curl -fL --max-time 60`
  into workspace packages/ (created with mkdir -p).
- `unzip -l` both archives; `sha256sum packages/*.zip`; `unzip -p` jailbreak
  README and USBNetwork README_FIRST.txt and README; `unzip -p` jailbreak
  WHERE_ARE_THE_SOURCES.txt; piped embedded data.tar.gz to `tar -tzvf -` and
  `tar -xzOf - /var/local/system/mntus.params` for inert inspection only.
  Nothing extracted to absolute host paths or executed.
- Repeated lsblk: still sda 0B. Created PACKAGE-REVIEW.md with hashes,
  provenance, actual installer behavior, documented rollback, and review limits.
- Payload review corrects README simplification: two key files, cleanup,
  diagnostics bootmode change, and optional execution of pre-existing runme.sh.
  Check these collision paths against backup before any installation.
- USBNetwork README flags K4 boot-while-plugged-in timing failures and permissive
  USB authentication; retain these as deployment test/security requirements.
- No Kindle writes or mode switches; user-volume backup pending reconnect.

## 2026-09-21, 14:30 EDT — verified user-volume backup

- User confirmed USB mode. `date -Is`; lsblk with serial confirmed expected
  B00E device on sda and FAT32 sda1. `findmnt` showed host automount rw.
  `df -h .` showed 630 GiB available. Listed local packages.
- `udisksctl unmount -b /dev/sda1 && udisksctl mount -b /dev/sda1 --options ro`
  succeeded; verified ro with findmnt before reading/copying files.
- Created private backups/2026-09-21-before-jailbreak directory and copied
  complete visible volume with `cp -a KINDLE_MOUNT/.` into userstore/.
  `du -sh` reports 96M. No existing runme.sh, data.tar.gz, ENABLE_DIAGS,
  diagnostic_logs, usbnet, or top-level *.bin files found.
- `unzip -t` both downloaded archives: all CRC tests passed. rsync available;
  kindletool not installed. No AGENTS.md found in workspace.
- Created verify-backup.py using apply_patch; ran `python3 verify-backup.py`.
  Independently hashed all source and backup files and compared relative paths,
  sizes, and SHA256. PASS: 125 files, 99,972,130 bytes. Wrote local manifest.json
  exclusively (will not silently overwrite an existing manifest).
- Backup includes private book/library content; stored locally only. No
  internal system/diagnostics partitions are included.
- Extracted only selected ZIP members into host packages/k4-jailbreak-reviewed
  using unzip -n: data.tar.gz (left compressed), ENABLE_DIAGS, device_info.xml,
  README, and uninstaller. No extraction of absolute tar paths or execution.
- Asked user for battery state before disconnected restart; response pending.
  Kindle remains mounted ro. No installation files have been copied to it.
- Next action after adequate charge confirmed: stage the reviewed jailbreak
  files on the identified user volume, verify copies, safely unmount, and guide
  the user through the documented device menu steps. Existing “let's do it”
  authorization carries forward; no repeated permission request is needed.

## 2026-09-21 — jailbreak staged, awaiting user menu steps

- User reports approximately 50% battery. Proceeding on existing authorization;
  disconnected runtime stability remains untested after years in storage.
- Re-ran lsblk, findmnt, package SHA256, staging-directory listing and collision
  checks. The serial still matched the verified B00E device. The Kindle was now automounted rw
  (changed since prior turn). Package ZIP checksum unchanged; no collisions.
- In a fail-fast shell, checked exact serial with udevadm and exact mountpoint
  with findmnt; checked absence of runme.sh/data.tar.gz/ENABLE_DIAGS/diagnostic_logs.
- Copied only reviewed data.tar.gz (59,939 bytes), diagnostic_logs/device_info.xml
  (empty), and ENABLE_DIAGS (empty) to the Kindle user-volume root, using cp -n
  / cp -rn to avoid replacing existing files. Created diagnostic_logs directory
  as part of the copy. Did not copy uninstallers, USBNetwork, or runme.sh.
- `cmp` verified each staged file byte-for-byte against the reviewed host copy.
  `sync -f KINDLE_MOUNT` followed by `udisksctl unmount -b /dev/sda1`
  completed successfully. No raw block write or host-triggered reboot.
- Device is now armed for diagnostics on restart. Next user action: disconnect,
  Settings Restart; diagnostics D (Exit/Reboot/Disable), R (Reboot System),
  Q (continue). Follow package README; stop and report any unexpected menu or
  power failure. Success is a normal boot and You are Jailbroken document.
- To cancel before reboot, reconnect and remove only the three staged files
  and newly created diagnostic_logs directory after verifying exact identity;
  these staging files were absent from the verified backup. No removal executed.
- Following successful installation, rollback uses dependent-package uninstallers
  first, then jailbreak uninstaller through Update Your Kindle. If boot fails,
  this rollback may be unavailable; no flashing/recovery writes authorized.

## 2026-09-21 — jailbreak success; USBNetwork installer staged

- User reports You are Jailbroken document. Rechecked lsblk serial, findmnt,
  packages listing, ip -brief addr and ip route. Expected Kindle user volume
  automounted rw; no USB network yet, no main-table USB_SUBNET conflict.
- Unmounted/remounted ro via udisksctl before inspection. Confirmed documents/
  You are Jailbroken.txt and .mbp; data.tar.gz, ENABLE_DIAGS, diagnostic_logs
  absent from root after jailbreak cleanup. Internal key state still unverified.
- Extracted K4 USBNetwork README_FIRST, installer and uninstaller onto host with
  unzip -n. ZIP SHA256 matches previously recorded 17e22860...ad1291e49.
- Explained next install's purpose, uninstaller, mass-storage toggle, and no
  automatic networking at boot. Existing user authorization applies.
- Fail-fast staging: verified exact serial, success document, absence of
  ENABLE_DIAGS/runme.sh and any root-level .bin; unmounted/remounted rw;
  verified target mountpoint. Copied only Update_usbnetwork_0.57.N_k4_install.bin
  using cp --update=none. cmp passed; sync -f and udisksctl unmount succeeded.
- No network activation, persistent host network change, root login, or boot
  auto marker created. Installer binary has not been executed by the host;
  documentation reviewed, but internal installer binary not independently audited.
- Next user action: disconnect USB, Settings > Menu > Update Your Kindle
  (not Restart), allow completion, then reconnect USB for config inspection.
  If Update is unavailable or an error appears, report state before proceeding.

## 2026-09-21 — USBNetwork installed; key prepared

- User reports device back. lsblk/udev confirmed same serial and mounted FAT32.
  ip -brief link still shows no USB network. sudo -n true still requires an
  interactive password; nmcli general permissions allows network-control and
  settings modifications. No privilege escalation attempted.
- Remounted ro with udisksctl and verified options. Read usbnet/etc/config,
  usbnetwork_install.log, info.txt; listed usbnet/bin and inspected first 240
  lines of usbnetwork script. Install log ends Done; version 0.57.N.
- Config: HOST_IP=USB_HOST_IP, KINDLE_IP=KINDLE_USB_IP,
  K3_WIFI=false, K3_WIFI_SSHD_ONLY=false, USE_OPENSSH=false, USE_VOLUMD=true.
  DISABLED_auto present, no auto marker. Config unchanged.
- ip route show table all: no USB_SUBNET route conflict found, including
  VPN routes. No networking profile created yet; wait for exact USB NIC.
- Created project .ssh directory mode 700 and a dedicated RSA 3072-bit key via
  ssh-keygen, with empty passphrase for automation. Private key stays host-only;
  never displayed. Added .gitignore entries for .ssh, backups, evidence.
- Confirmed authorized_keys absent. Saved installed config/log to host evidence/.
  Reconfirmed device serial, remounted rw, checked exact mountpoint, copied
  only public key to usbnet/etc/authorized_keys without overwriting existing
  content. cmp verified it, sync -f completed, udisksctl unmount succeeded.
- This adds key authentication but does not disable the package's permissive
  default USB password/telnet behavior. Link must remain isolated during tests;
  no Wi-Fi SSH, bridge, forwarding, or boot auto activation has been enabled.
- Next user action, unplugged: on Home enter ;debugOn, ~usbNetwork, ;debugOff
  as separate search commands using virtual Enter, not Done; then reconnect.
  Same toggle reverses mode. Host will enumerate actual NIC and assign only
  the dedicated USB address before read-only SSH inventory.

## 2026-09-21 — USB SSH, hardware inventory, and PNG refresh test

- User reconnected after manual toggle. lsusb/lsusb -t, ip -brief addr,
  nmcli device status and journalctl -k -n 25: Kindle port 5-4 now 0525:a4a2,
  RNDIS/Ethernet Gadget, two configurations (RNDIS and CDC Ethernet), no USB
  serial string. cdc_subset owns data interface; cdc_ether probe failed -16,
  but working NIC USB_INTERFACE appeared. Initial link-local address only.
- `nmcli device modify USB_INTERFACE ipv4.method manual ipv4.addresses
  USB_HOST_IP/24 ipv4.gateway '' ipv4.dns '' ipv4.never-default yes
  ipv6.method disabled` applied temporary active-connection changes.
  First immediate route query raced configuration and showed LAN default;
  initial SSH attempt timed out. Rechecked address, nmcli details, and route:
  KINDLE_USB_IP then correctly routed directly via USB. Subsequent SSH bound
  explicitly to USB_HOST_IP. No bridge/forwarding/default route added.
- `lsusb -v -d 0525:a4a2` inspected descriptors (cached; device-open warning).
- SSH using project RSA key first failed public-key authentication. Added
  per-invocation PubkeyAcceptedAlgorithms=+ssh-rsa for the old Dropbear server;
  authentication succeeded. ECDSA host key accepted on initial direct USB
  connection and pinned in project .ssh/known_hosts. No global SSH relaxation.
- Read uname, /etc/prettyversion.txt, /etc/version.txt, /proc/cpuinfo,
  /proc/partitions, /proc/mounts, /proc/cmdline, sysfs framebuffer and partition
  starts, df, updater key metadata, and powerd battery/status properties.
  Created executable kindle-ssh helper with route/source guard and timeouts.
- Confirmed Linux 2.6.31-rt11-lab126 armv7l; MX50 YOSHI Board, revision 50011;
  CPU part 0xc08 revision 5. Firmware build 001-H303_yoshi-354363 dated 2019-05-30.
  eink_fb 600x800 8bpp. Boot command line root=/dev/mmcblk0p1; serial console
  ttymxc0,115200 configured (not exposed as USB serial or physically tested).
- Internal block sizes in KiB: mmcblk0=1,912,832; p1=358,400 (root ext3 ro),
  p2=65,536 (not mounted; likely diagnostics, not inspected), p3=32,768
  (/var/local ext3 rw), p4=1,423,360 (userstore container). Start sectors:
  p1=65,536; p2=782,336; p3=913,408; p4=978,944. loop0 user filesystem
  1,423,352 KiB, mounted through /mnt/base-us and fuse /mnt/us.
  Internal partition images have NOT yet been backed up or changed by us.
- /etc/uks/pubdevkey01.pem present. Battery 53%, isCharging=1; powerd Active,
  prevent_screen_saver=0, drive_mode off. Concurrent USB power/data confirmed.
- Old shell lacks `command`, busybox --list and grep -E. These harmless
  discovery attempts failed; use explicit tool paths and old-shell syntax.
- Built-in /usr/sbin/eips exists. eips -h returned 0 without stdout; no useful
  help obtained. Pillow available on host. Created render-test.py via apply_patch
  to render a grayscale diagnostic PNG; ran python3 render-test.py.
- Verified /tmp/display-test.png absent, transferred only that image via
  `tar -cf - display-test.png | ./kindle-ssh 'tar -xf - -C /tmp'`.
  Host and device MD5 both 752473aade81f8b1148ef06733d0039b (transfer integrity,
  not cryptographic provenance). Ran `/usr/sbin/eips -f -g /tmp/display-test.png`:
  exit 0. No rootfs writes, boot hooks, framework or power-policy changes.
- Asked user to confirm physical image. No claim of visual success yet.
  Updated feasibility report. Next: physical confirmation, then reversible
  UI/sleep handling, repeated updates and reconnect tests. User calendar source
  and Raspberry Pi access are still unspecified; no real calendar data loaded.

## 2026-09-21 — physical display success confirmed

- User answered “yes it does!” to the diagnostic PNG confirmation question.
  Physical panel rendering is now verified, not merely inferred from exit code.
- Single USB cable has delivered power, SSH image transfer, and controlled
  refresh using stock eips on this exact K4/4.1.4 device.
- No further device changes this turn. Updated FEASIBILITY.md with confirmed
  result and remaining Pi/calendar integration requirements. Current display
  is a manual proof of concept; UI/sleep, auth hardening, boot/reconnect and
  sustained charging remain deployment work. Await calendar source and Pi
  connection context for implementation.

## 2026-09-21 — standalone boot/wake image persistence

- User explicitly requested image persistence after off/on without CalDAV/Pi.
  Inspected init.d, rc5.d, rcS.d, rc2.d, inittab, usbnet init/helpers, framework
  and boot_finished scripts, ps, lipc-wait-event help and powerd properties.
  Confirmed SysV startup and no existing calendar-display paths.
- Researched K4 powerd event listeners (MobileRead thread 315119). Presented
  exact root changes, purpose, rollback and boot risk before implementation:
  one init script and one S99 symlink, persistent image/service in userstore,
  DISABLED marker and nonblocking startup. Normal sleep/framework stay enabled.
- Created and ran backup-root.py. Verified serial and root ro, streamed
  `dd if=/dev/mmcblk0p1 bs=65536` over pinned SSH to host, checked size and
  local/device MD5, recorded SHA256. PASS: 367001600 bytes; SHA256
  9e0730d759fb8bafa8e549eb22cea0f7b9034034b60149c4cca24a2fce9329dc.
  Stored image/manifest under backups/2026-09-21-before-display-service.
  Root backup is post-jailbreak, not a complete device recovery image.
- Built device/calendar-display/service.sh and calendar-display-init with
  apply_patch. Copied verified PNG as current.png. Local and remote sh -n
  passed. Transferred folder via tar/SSH after absence checks; image MD5 still
  752473aade81f8b1148ef06733d0039b. Started service manually; running pid 8797,
  redraw exit=0. No power-policy, framework or USBNetwork changes.
- Listener uses goingToScreenSaver,outOfScreenSaver,wakeupFromSuspend,
  readyToSuspend events, a 60s timeout, 2s backoff and a 2s settle on most
  events. Boot daemon waits 35s in background. PID/log kept in RAM.
  One-second listener probe returned 255 on timeout with no output. Actual
  power-button sleep/wake test requested from user; response pending.
- Root installer initially failed at `mntroot` not in SSH PATH before changes;
  confirmed root ro and targets absent. Retried with /usr/sbin/mntroot rw and
  exit trap restoring ro. Copied script to /etc/init.d/calendar-display,
  chmod 755; added /etc/rc5.d/S99calendar-display symlink. sync, remount ro,
  verified /proc/mounts. Original Amazon files unchanged.
- Init start detects already-running daemon without duplication. No reboot
  issued. Created DISPLAY-SERVICE.md with disable/rollback instructions.
  An initial combined documentation patch failed on a mismatched context;
  retried this log entry separately.
- Next: physical sleep/wake test, then normal menu Restart unplugged and allow
  roughly 45s after Home appears. Boot behavior remains unverified until that
  test. USB networking remains manual after reboot for maintenance.

## 2026-09-21 — user reports documents menu after power test

- User reports the documents/Home menu instead of persistent image. Wake/boot
  redraw is not validated and needs diagnosis; do not label this completed.
- Attempted read-only log/service/powerd/process inspection via kindle-ssh;
  helper refused because the dedicated USB route was absent. No traffic sent
  through another network.
- Ran lsusb, ip -brief addr, nmcli device status, lsblk with serial, and
  journalctl -k -n 18. Same Kindle is now USB mass storage 1949:0004 (bus 005
  device 011), not 0525:a4a2 Ethernet; no USB NIC. Kernel at 15:35:35 shows
  re-enumeration, then storage capacity dropping to 0 at 15:36:05.
- This establishes a mode change, not whether a reboot or manual toggle caused
  it. Cannot inspect /tmp service log until USB networking is restored. No
  device changes or speculative service patch made.
- Next: user restores networking via the known three search commands while
  unplugged, reconnects; then configure new NIC, inspect uptime/logs/processes
  and actual power events before changing redraw logic. Ask whether the user
  performed a normal restart or only brief sleep/wake presses.

## 2026-09-21 — minimal userspace replacement preparation

- User explicitly requested replacing most userspace. Chosen staged approach:
  independent application userspace/supervisor first; retained hardware-support
  services; no kernel/rootfs/bootloader flash. Explained boundary and dependencies.
- Initial lsusb/ip/nmcli/lsblk: Kindle mass storage, 0B, no network. Asked user
  to re-enable USB networking while continuing offline work.
- Used debugfs read-only (-R, never -w) on verified root image to read init.d
  pmond/powerd/system/rc, list libraries, and inspect extracted /etc scripts.
  rdump /etc into evidence/root-etc reported ownership-preservation warnings
  because host user cannot chown root; contents needed for inspection exist.
  This private copy may contain credentials and is excluded by .gitignore.
- Confirmed powerd/volumd use pmond through LIPC; framework/browser/webreader
  must be stopped through service controls to avoid respawn. E-ink setup
  references /opt/eink/scripts/lifeguard and board sysfs parameters.
- Read original K4-oriented developer/project search results about no-framework
  operation and power events; decisions prioritize inspected on-device scripts.
- debugfs dump of /bin/busybox and /usr/sbin/eips into evidence; file/readelf/
  strings: ARM EABI5, interpreter /lib/ld-linux.so.3, glibc 2.12.1; BusyBox
  GNU/Linux ABI note 2.6.16. eips needs libc/libdl; BusyBox libc/libm/libcrypt.
- Created appliance/build.py, supervisor.sh, PLAN.md with apply_patch.
  Ran python3 appliance/build.py and sh -n appliance/supervisor.sh. Build
  extracts only specified binary/library files from our image, resolves direct
  ELF dependencies, creates a private application tree and tarball. No account
  files included. Prototype application-userspace.tar.gz ~1.2 MiB; manifest
  records binary hashes. This is NOT a bootable image or replacement PID 1.
- Prototype runs hash-on-change PNG rendering; host syntax/ELF checks pass.
  Runtime/chroot, power events, exclusive screen ownership and supervised
  service cutover remain untested. No claim of userspace replacement completion.
- USB then reappeared 0525:a4a2, CDC Ethernet cdc_ether, USB_INTERFACE with
  MAC USB_MAC. Unlike earlier cdc_subset session, carrier remains 0.
  Created memory-only NM profile via nmcli connection add save no, static
  USB_HOST_IP/24, never-default, IPv6 disabled, autoconnect no; activated.
  Route targets correct USB device; SSH attempt fails No route to host and
  neighbor state FAILED. No global DNS/gateway/bridge changes.
- Requested brief wake and connected/awake state from user. No Kindle writes,
  root remounts or service changes this turn. Existing overlay experiment is
  still installed. Next: restore functioning USB link, capture current state,
  test isolated prototype, then reversible supervised service replacement.

## 2026-09-21 — retry after user says “try now?”

- Retried ip -brief addr, lsusb 0525:a4a2, and pinned/bound kindle-ssh.
  Still no SSH: No route to host. Detailed ip link confirms administrative UP
  but NO-CARRIER. USB runtime status active, configuration 1; same device 013.
  NM has correct static address and activated connection; ARP cannot resolve.
- Read NM state, sysfs carrier/configuration, recent kernel journal and USB
  device permissions. sudo -n true still needs interactive authentication.
  Did not change driver binding, unload host modules, or request a password.
- Earlier working session used cdc_subset; current cdc_ether binding is a
  relevant difference, not proof of root cause. Kernel developer sources show
  separate subset/CDC drivers; no model-specific cause established by search.
- Next least invasive attempt: while unplugged toggle USBNetwork off then on
  with pauses, then reconnect awake. If no carrier persists, investigate the
  exact host-driver binding with a narrowly scoped privileged operation rather
  than repeatedly cycling or altering unrelated network devices.

## 2026-09-21 — reconnected after toggle cycle

- Ran lsusb, lsblk with filesystem/mount columns, findmnt and ip -brief addr.
  Kindle now enumerates as 1949:0004 mass storage, /dev/sda1, 1.4G FAT Kindle;
  no USB network interface. This is a confirmed mode change, not merely a
  missing host IP. Exact reason the previous double toggle ended here unknown.
- Desktop had mounted the volume RW. Used udisksctl to unmount/remount RO,
  then read usbnet/bin/usbnetwork, selected non-secret config values and
  directory listings. USBNetwork files and DISABLED_auto remain present.
- Script inspection confirms usbNetwork toggles the current mode through
  volumd and configures usb0 after waiting up to 15 seconds. No script/config
  changes made. Unmounted the user volume before asking for a single toggle.
- Next safest action: unplug, invoke one USBNetwork toggle, allow its wait
  to finish, reconnect; verify actual USB enumeration before any deployment.
  Isolated userspace archive remains host-only; no boot changes this turn.

## 2026-09-21 — check after user disconnected mass storage

- Ran lsusb, ip -brief addr, nmcli device status, lsblk /dev/sda, and
  journalctl -k -n 25 --no-pager. Device still 1949:0004, with /dev/sda now
  0B and no partition/mount; kernel records capacity falling to 0 at 16:19:46.
  No USB NIC exists. This is consistent with ejected/unexported storage,
  not a switch to the Ethernet gadget. SSH cannot be attempted over USB yet.
- No device changes. Next action remains one USBNetwork toggle while
  physically unplugged, then reconnect after waiting for configuration.

## 2026-09-21 — USB SSH restored; isolated shell validated

- After user restarted unplugged and enabled networking, ran lsusb selectors,
  ip -brief addr, nmcli device status and journalctl -k -n 18. Device 016 is
  0525:a4a2; cdc_ether interface USB_INTERFACE now has carrier.
- Ran nmcli connection up kindle-usb-test and pinned ./kindle-ssh. SSH works.
  uname/version unchanged; uptime ~2min confirms reboot; root ext3 remains RO.
  df -k /var/local: 23100 KiB available. ps shows stock application/platform
  services running. No host driver workaround required.
- Announced separate-directory trial, no startup/service changes. Streamed
  prepared tarball over SSH to a newly created, previously absent directory
  /var/local/calendar-appliance-trial using tar -xz -C. Old tar skipped PAX
  metadata headers; actual binary/library/supervisor MD5s match host copies.
  Updated future builder to GNU tar format to avoid those metadata warnings.
- chroot /var/local/calendar-appliance-trial /bin/sh succeeded. Initial uname
  lookup failed due inherited PATH; retest with PATH=/bin:/usr/sbin succeeded
  (armv7l). Explicit BusyBox sleep/test/ls/md5sum and symlinks verified.
- lipc-get-prop powerd battLevel=90, isCharging=1. Existing display log has
  one boot redraw exit=0. No pseudo-filesystems bound, new renderer/supervisor
  run, or stock services stopped. No boot files or system partition changed.
- Rollback for this stage: remove only the identified trial directory after
  confirming no processes/mounts use it; no startup references were added.
  Next: controlled renderer test, then time-limited application service
  replacement with independent rollback. Persistent boot cutover still gated.

## 2026-09-21 — first runtime service-replacement trial

- User authorized proceeding. Read actual saved framework/browserd/webreaderd
  scripts and old overlay service; live baseline MemFree 88292 KiB, charging.
- Created appliance/trial.sh, syntax checked, transferred into the known trial
  directory. Armed a detached HUP-ignoring 90-second rollback before changes.
  Trial logs/state under /tmp/calendar-appliance-trial; no startup edits.
- Stopped old overlay, copied existing test PNG into private data directory,
  bound /dev,/proc,/sys into trial root and ran chroot eips -f -g image.
  Returned success (ISOLATED_RENDER_OK): renderer runs in isolated userspace.
- framework stop succeeded. browserd stop returned Killed (137), aborting
  the set-e trial before webreader stop/new supervisor startup. SSH remained
  available and rollback PIDs survived. ps confirms cvm/browserd absent,
  webreader/powerd/volumd/pmond/lifeguard/SSH present; MemFree 137872 KiB.
- Browser init uses BusyBox killall -9 browserd, which may match its own
  calling init shell; this is the likely explanation, not proven tracing.
  Revised local trial to use pmond stop plus executable-verified PID signaling
  instead of name-wide killall. Await automatic first-trial restoration before
  deploying a second trial. No kernel/partition/root/boot changes.
- First timer completed RESTORE_COMPLETE; ps/pidof confirmed cvm/browserd/
  webreader, and mount showed all three trial binds gone. Rollback validated.
- Preserved first device trial.sh as trial-1.sh; deployed revised local script
  (state /tmp/calendar-appliance-trial-2). Removed only the first trial's known
  data/DISABLED marker to re-enable this test. No user content removed.
- Second trial returned ISOLATED_RENDER_OK and APPLIANCE_TRIAL_RUNNING.
  Fresh SSH ps/pidof confirms cvm/browserd/webreader absent. Supervisor PID
  4971 is /bin/sh /sbin/display-supervisor; /proc/4971/root points to the
  isolated root. pmond/powerd/volumd/lifeguards/dropbear remain running.
  MemFree 141012 KiB versus 88292 KiB baseline (~51.5 MiB higher; not a
  controlled memory benchmark). Charging remains 1; supervisor log empty.
- Asked user for physical image confirmation without power-button testing.
  Second 90-second automatic restoration pending; permanent boot unchanged.
- User replied yes: test image physically visible during isolated-supervisor
  trial. Follow-up SSH confirms supervisor remained running, old overlay was
  stopped, all three application daemons absent, charging=Yes (92%).
- Second timed rollback completed RESTORE_COMPLETE. pidof returned cvm 5236,
  browserd 5116, webreader 5085. Supervisor PID 4971 exited; mount confirms
  trial dev/proc/sys binds removed. Stock services restored automatically.
  Only test files remain in /var/local/calendar-appliance-trial and RAM logs.
- Next safest work: improve/test image-update and sleep/wake behavior in
  another reversible trial, then reliable USB maintenance at boot and an
  opt-in stock-mode escape before any persistent application cutover.

## 2026-09-21 — image update and sleep/wake trial (third)

- User authorized proceeding. Added render result logging and a refresh-token
  check to supervisor.sh. Added retained-platform power-events.sh bridge using
  lipc-wait-event (5-second timeout), with 2-second settling then atomic token
  rename for goingToScreenSaver/outOfScreenSaver/wakeupFromSuspend. No power
  settings changed. Trial rollback extended to 240 seconds and bridge cleanup
  grace to 12 seconds; new RAM state /tmp/calendar-appliance-trial-3.
- Created deterministic synthetic 600x800 grayscale UPDATE TEST 2 PNG via
  Pillow script appliance/render-update-test.py. No real calendar information.
- Syntax checked all scripts. Preserved device trial-2.sh, uploaded revised
  trial/supervisor/event bridge only into existing private test directory.
  Confirmed prior restoration before removing its known DISABLED marker.
- Third trial started successfully with detached timed rollback armed. Sent
  new PNG into data/current.png.new, then atomically renamed current.png.
  Supervisor logs RENDER_OK for initial 752473aade81f8b1148ef06733d0039b and
  updated ef19f3e064e52e018de5f89e11008693. Reader/browser/webreader absent.
  Powerd Active, charging, battery93. Asked user for brief sleep/wake test.
- Re-read actual usbnet init for future maintenance design: auto flag causes
  existing toggle script at boot, with emergency.sh taking precedence. No auto
  flag or emergency script created; startup remains unchanged this trial.
- Observed powerd change from Active to Screen Saver while event log stayed
  empty. lipc-wait-event -h confirms syntax; direct wildcard wait timed out
  exit255. Event may have fallen in re-registration gap; cause unproven.
- Added power-state.sh fallback polling the first line of actual powerd status
  every2s, requesting redraw only on state changes. Syntax checked and staged.
  Verified old bridge PID cmdline then sent TERM, waited8s for exit before
  starting replacement. Same DISABLED marker controls rollback cleanup.
  New bridge logged Screen Saver state. This is prototype polling, not proof
  of deep-suspend wake/reconnect reliability; no power property changed.
- Supervisor logged RENDER_OK for the state-1 Screen Saver refresh token.
  No physical sleep/wake answer received during this trial, and no Active
  transition recorded by fallback. Do not claim wake testing passed.
- Third automatic rollback completed RESTORE_COMPLETE; power bridge and
  supervisor logged EXIT. cvm/browserd/webreader returned (6244/6125/6094),
  trial pseudo-filesystem mounts gone. SSH remained reachable throughout.
  Stock services restored; no persistent boot or power-policy changes.
- Next action needs user observation of the prompted physical test, or a
  coordinated new reversible test if they did not perform it in the window.

## 2026-09-21 — fourth trial, coordinated physical wake test

- User missed previous window. Confirmed trial3 restored and stock daemons
  running. Prepared trial4 with 600-second automatic rollback, state polling
  bridge from startup, and UPDATE TEST 2 as initial image. Added restore-now
  action to same idempotent cleanup for early recovery after user observation.
- Saved device trial-3.sh, uploaded revised trial script and synthetic card,
  removed only prior trial DISABLED marker, launched. Stock framework stop
  woke powerd from Screen Saver; trial reports APPLIANCE_TRIAL_RUNNING.
- Logs show successful rendering of ef19f3e064e52e018de5f89e11008693 and
  POWER_STATE Active; live powerd Active, charging95%. Rollback PID6354.
  Test is currently LIVE pending user brief sleep/wake, or automatic timeout.
  No startup/boot/power-policy changes. Need verify cleanup after test.
- User reports image appears to work but cannot trigger apparent power-off
  while USB-connected. Live logs show Active -> Screen Saver -> Active ->
  Screen Saver -> Active -> Screen Saver, with RENDER_OK on all six state
  refreshes. Reader/browser/webreader still absent; powerd currently Screen
  Saver, charging96%, SSH working. This supports brief-button state/redraw
  behavior, not full shutdown or deep-suspend/reboot recovery. Unchanged
  e-ink image does not establish whether the hardware is powered off.
- Invoked trial.sh restore-now to end the test early via existing cleanup.
- Cleanup returned RESTORE_COMPLETE; both prototype processes logged EXIT,
  all three binds removed. Follow-up confirms cvm7127/browserd7002/webreader
  6971 running, restored marker present, previous overlay restarted. Original
  timer remains asleep until its deadline; restore's lock prevents a second
  restoration. No permanent appliance-mode activation performed.

## 2026-09-21 — one-shot USB networking boot test

- User authorized next step. Read live USBNetwork config, usbnet-link and
  init script; confirmed auto/emergency.sh absent and S82usbnet hook present.
  Config remains USE_VOLUMD=true, Wi-Fi SSH disabled; did not edit config.
- Presented purpose/risk/rollback before changes: one-shot networking after
  stock startup; independent 180-second fallback unless SSH acknowledged;
  arm consumed before attempt so next restart does not repeat. No system-root,
  bootloader, kernel or partition writes; temporary access loss is main risk.
- Added appliance/usb-boot-hook.sh and usb-boot-worker.sh, syntax checked on
  host/device. New /var/local/calendar-usb-boot-test stores worker/ARM/logs.
  New /mnt/us/usbnet/bin/emergency.sh uses existing package hook, backgrounds
  worker and returns immediately. Worker waits45s, arms fallback, then calls
  existing USBNetwork toggle only if g_ether absent. Stock reader remains on.
- Verified root ext3 RO, ARM present/CONSUMED absent; sync then /sbin/reboot.
  Tool returned: could not determine runlevel, doing soft reboot (suggests
  shutdown instead next time). Actual reboot/reconnection verification pending.
- Host kernel confirms disconnect/re-enumeration: storage device17 then18;
  serial matches Kindle. No 0525:a4a2 network gadget or USB NIC appeared in
  successive checks. Storage capacity appeared 16:45:25 then fell to0 at
  16:46:21. Desktop auto-mounted RW; remounted RO to inspect our hook, then
  unmounted. Hook file contents intact. No further Kindle writes after reboot.
- At20:46:44UTC device18 remains 1949:0004, /dev/sda0B, no network interface.
  Automatic USB access not established. Cannot yet read internal ARM/CONSUMED,
  worker log or fallback state, so cannot assert hook ran or fallback succeeded.
  Asked user what screen appears. Need physically unplug/manual networking
  recovery, then acknowledge/cancel any remaining fallback and inspect logs.
  Do not call manual recovery an automatic-boot success. No appliance boot
  activation; new hook remains and needs cleanup/disarming once shell returns.

## 2026-09-21 — retry after manual recovery request

- Ran lsusb, ip -brief addr, nmcli device status/connection up, kindle-ssh,
  kernel journal and lsblk. No USB NIC; NM cannot activate its interface-bound
  profile. SSH helper correctly refused another network route.
- Device19 enumerated 1949:0004 at16:48:40; exported storage then capacity
  fell to0 at16:48:51. This does not establish whether the user toggle failed,
  toggled networking off, or the pending boot-test fallback changed the mode.
  No shell, logs or internal arm state available. No writes made this turn.
- Need user report of USBNetwork command/error before another blind toggle.
- User confirms physically unplugged and no command error. Read host time,
  VID/PID, interfaces and kernel events since16:47. Physical disconnect was
  16:47:17, reappearance as storage16:48:40. At16:49:52 still storage. This
  timing is consistent with fallback overlapping unplugged toggling, but does
  not prove it. Nominal boot-test delay/fallback window is now past; ask one
  toggle from confirmed storage, without another reboot that could rearm an
  unconsumed hook. Inspect/disable test immediately when SSH returns.

## 2026-09-21 — recovered USB; boot-test cause confirmed

- Device20 returned0525:a4a2. Activated kindle-usb-test; SSH works. Internal
  log confirms ARM consumed; delayed worker couldn't open /mnt/us/usbnet/bin/
  usbnetwork (exit2), usb0 absent. Later fallback logged switching usbnet to
  usbms and exited0, explaining interference with manual recovery.
- Disabled first hook by renaming emergency.sh to emergency.sh.disabled-boot-test,
  retained for recovery/inspection. Wrote ACK (manual recovery, NOT boot-test
  success). No ARM and no fallback process remained; stock daemons running,
  root still RO. User requested continuation after interrupted reporting.
- Second test uses new /var/local/calendar-usb-boot-test-2, one-shot ARM and
  early synchronous invocation from S82 emergency hook (no45s delay). Same
  independent180s fallback. It now refuses false READY if script/interface
  fails, and fallback skips nonexistent networking rather than read hidden
  user-volume script. Purpose/risk/rollback communicated before deployment.
- Host/device syntax checks pass, second hook staged and ARM synced. No
  original init/root/config files changed. Reboot and automatic SSH pending.
- Invoked /sbin/shutdown -r now for second test. Kernel confirms reboot USB
  disconnect and storage device22. No network gadget appeared. Storage export
  became available16:57:37. At16:58:23 read exact hook and verified it targets
  test2, then renamed it through host storage to
  usbnet/bin/emergency.sh.disabled-boot-test-2 (no content deleted), synced
  and unmounted. There is no active emergency.sh for subsequent boots.
- USBNetwork config timestamp16:56 suggests script reached config processing,
  but need internal boot.log to identify actual failure; no speculative fix.
  Allow full180-second fallback window to pass before manual networking so
  recovery does not overlap again. Boot root/reader startup unchanged.
- Kept USB connected without requesting a toggle until after21:00:37UTC,
  three minutes after observed storage export (a conservative bound for the
  synchronous hook's earlier fallback launch). Still only1949:0004. Internal
  logs remain unavailable, so timeout completion inferred, not directly read.
  Next: one unplugged manual network toggle, inspect logs, verify no fallback
  remains; no further boot experiments before diagnosing this attempt.

## 2026-09-21 — recovered via USB telnet; early-start cause confirmed

- Device23 enumerated0525:a4a2. Activated interface-bound host profile;
  neighbor .244 resolves USB_MAC, but SSH port22 refuses. Retried
  after3s; nc -vz bound to .201 confirms22 refused,23 open. Used installed
  USBNetwork telnet shell via nc over isolated USB (no password/secret sent).
- Read test2 boot/fallback logs: volumd property request failed with
  lipcErrNoSuchSource; usb0 never appeared during15s wait, ifconfig failed.
  Package nonetheless started telnet/SSH and returned0. Worker correctly
  failed its subsequent interface check. Fallback logged ALREADY_STORAGE.
  ARM consumed, no active emergency.sh. This is dependency readiness failure,
  not evidence of host driver trouble. Fixed delay previously lost /mnt/us.
- Inspected libkh daemon options and dropbear -h. No sshd PID remained.
  Package's existing-PID branch can stop SSH during a later enable attempt;
  this is a plausible cause of current refusal, not separately traced.
- Started installed Dropbear with -s -p KINDLE_USB_IP:22 -P existing sshd.pid
  path -K15. Key-only, bound to USB address; no config/auth/key files changed.
  Pinned project SSH succeeds. Verified hook disabled, ARM absent, fallback
  PID gone, stock daemons present, system root remains read-only. Closed
  recovery telnet session; installed telnet service itself remains as before.
- Read live rc/pmond/volumd startup scripts and current property (=1).
  init service start requests do not wait for daemon LIPC readiness. Future
  design needs explicit readiness plus startup assets outside exported user
  storage, not guessed delays. No new hook staged or reboot requested.

## 2026-09-21 — readiness-gated USB boot test3

- User authorized test. Re-read package usbnetwork/libkh and probed LIPC
  property metadata (no secret values). New usb-ready-worker.sh lives in
  /var/local/calendar-usb-boot-test-3; uses only stock commands/internal scripts
  until volumd property is readable (90s bounded wait), then requests network
  mode and waits up to45s for usb0 plus SSH assets to become accessible.
- No generic toggle/USBNetwork helpers needed during export. Starts Dropbear
  key-only, bound to KINDLE_USB_IP, using test-local PID. Independent240s
  fallback uses stock LIPC to request storage, not a script on /mnt/us.
  ARM consumed before background worker; stock reader boot is not blocked.
- Host/device syntax checks pass. Read-only worker check reports VOLUMD_READY
  mode1 and SSH_ASSETS_PRESENT. Internal free space20876KiB. New emergency
  hook installed in previously absent path, ARM synced; shutdown -r now.
  No root/kernel/partition/config writes. User asked to leave cable connected
  and not manually toggle during recovery window. Automatic SSH pending.
- Third reboot exposed storage device25; no network gadget observed through
  21:11:12UTC. Storage export began17:10:10 local. Remounted userstore RO to
  inspect hook. Read package README_FIRST.txt BUGS: explicitly warns against
  computer-connected boot on K4, including g_ether Device or resource busy
  even with USE_VOLUMD. This warning should have gated earlier boot trials.
  It is a known possible failure mode, not yet confirmed by test3 internal log.
- Disabled test3 hook recoverably through user volume: renamed emergency.sh
  to emergency.sh.disabled-boot-test-3, synced/unmounted. No deletion or root
  changes. Wait through conservative21:14:10UTC fallback bound before manual
  networking, then inspect readiness/network-asset log and terminate any test
  leftovers. No further connected-reboot experiments planned without evidence.
- Initial host unmount after disabling returned DeviceBusy; a subsequent
  check confirmed hook renamed and unmount succeeded. Waited until21:14:21UTC,
  beyond conservative fallback bound. Device still1949:0004; no automatic
  network appeared. Internal recovery result must still be read after manual
  USB networking restoration. No further writes or reboot attempts.

## 2026-09-21 — test3 recovery and findings

- Device26 is0525:a4a2; activated host profile and pinned SSH succeeds.
  Read internal log: VOLUMD_READY seconds=3 mode=0, then NETWORK_ASSET_TIMEOUT.
  Fallback: RECOVERY_BEGIN, ifconfig No such device, RECOVERY_STORAGE_REQUESTED.
  FINISHED and CONSUMED present; ARM absent, fallback PID gone, hook disabled.
  Thus readiness gate worked but usb0 was still absent at fallback; automatic
  connected-boot networking failed. Charging1; root ext3 remains RO.
- Filtered dmesg and /var/log/messages for gadget/volumd/property errors.
  Kernel shows original storage and later successful g_ether load only at
  uptime1039s during manual recovery. No captured g_ether resource-busy error
  from boot. Current messages begins08:15, after boot attempt, so does not
  retain the needed early daemon details. Do not assert the README's resource
  busy example is the proven root cause of this specific attempt.
- No writes on Kindle this recovery turn. Next useful separation: validate
  automatic network startup with cable unplugged at boot, then attach, versus
  diagnosing connected-boot gadget switching with captured early logs. The
  former allows one-cable operation but not unattended connected reboot.

## 2026-09-21 — unplugged-boot test4 staged

- User authorized unplugged boot test. Live SSH confirms prior hook absent,
  test3 FINISHED, battery100%, working network mode1. New internal directory
  /var/local/calendar-usb-boot-test-4 with readiness worker; same network logic
  as test3 to isolate physical cable state. Recovery extended to600s to allow
  user to restart unplugged then reconnect. Added bounded targeted gadget/
  volumd diagnostics on network-asset timeout; no credential content logged.
- Host/device syntax checks and read-only readiness/SSH-asset checks pass.
  Installed new one-shot emergency hook, created ARM, synced. Root remains RO.
  No reboot issued from host: user must physically unplug FIRST, use Settings
  Restart, allow Home plus30s before reconnecting. Do not manually usbNetwork
  toggle: this test must establish automatic startup, not manual recovery.
- Test is ARMED, not yet run. Need inspect boot log and fresh uptime, then
  ACK successful automatic SSH before600s fallback; otherwise allow recovery
  to finish before manual toggles. Stock reader startup unchanged.

## 2026-09-21 — unplugged automatic networking boot PASS

- User reconnected after instructed unplugged restart. Device27 is0525:a4a2;
  activated existing host profile and pinned SSH succeeded. Uptime1min confirms
  new boot. Test4 log: VOLUMD_READY seconds=3 mode=0, usb0 UP with .244/24,
  USB_BOOT_TEST_READY. Unlike connected test3, no network-asset timeout.
- Verified CONSUMED present and recovery not begun; wrote/synced ACK so timer
  will preserve network rather than switch it off. Renamed only this test's
  emergency.sh to emergency.sh.disabled-boot-test-4; hook absent afterward.
  Preserved file for inspection; no original files removed. Worker PID's
  command confirms Dropbear -s, USB address only, test-local pidfile.
- Charging1, stock cvm/browserd/webreader running, system ext3 root RO.
  Confirmed operating constraint: automatic network during unplugged boot,
  then USB connection for power+data. Connected-boot reliability still failed;
  this is not a permanent auto-start installation or appliance boot cutover.
- Next proposal: opt-in appliance startup using validated unplugged boot path,
  retained hardware daemons, and independently tested stock-mode recovery.

## 2026-09-21 — provisional persistent appliance manager

- User authorized next step. Explained opt-in persistent mode, unplugged-boot
  constraint and ten-minute per-boot confirmation window pending Pi service.
  Unconfirmed boot disables appliance startup and restores stock+USB storage.
- Added appliance/manage.sh, appliance-hook.sh, render-appliance-card.py and
  OPERATING.md. power-state.sh accepts explicit DATA environment override.
  Manager retains stock hardware initialization, waits for framework LIPC then
  forty-second settling, stops framework/browser/webreader using tested controls,
  runs private renderer/supervisor and power-state bridge. No system init edits.
- Staged new /var/local/calendar-appliance/rootfs from GNU-format archive of
  verified original binaries/libs; uploaded updated scripts and neutral card.
  No trial directories overwritten. Chowned private tree root:root. Host and
  device script syntax checks pass; MD5 manager/bridge/supervisor/card match.
- start-live armed independent600s watchdog then returned APPLIANCE_READY.
  Logs RENDER_OK795b4f894cf4bc664578c5ead2aae4ae, Active state; /proc supervisor
  root points to new rootfs, cvm/browser/webreader absent, charging1, SSH works.
  Boot hook not yet installed. Invoked stock-keep-network to verify new
  manager's recovery path before enabling boot startup.
- New manager recovery PASSED: bridge/supervisor EXIT, all binds removed,
  startup marker renamed DISABLED, reader processes4593/4469/4438 restored,
  SSH retained and system rootRO. This tests application rollback; actual
  storage switch uses the stock LIPC path separately exercised in USB trials.
- Installed opt-in appliance emergency hook in confirmed absent path; device
  syntax check passed. Renamed private DISABLED back to ENABLED and synced.
  Appliance boot now ENABLED, but still in stock mode until next restart.
  User must unplug and restart through Settings, wait for appliance card then
  connect without private search commands. First combined boot must be
  inspected and confirmed within600s. No full-userspace/PID1 claim; platform
  services retained, CalDAV/Pi service not implemented.

## 2026-09-21 — persistent appliance boot verified and confirmed

- User reports appliance mode visible upon reconnect after unplugged restart.
  Device28 is0525:a4a2; existing host profile activated, pinned SSH works.
  Uptime1min confirms new boot. Startup log shows VOLUMD_READY seconds3,
  NETWORK_READY, framework stop, APPLIANCE_READY. State ENABLED_FOR_BOOT/READY.
- Supervisor log RENDER_OK795b4f894cf4bc664578c5ead2aae4ae, bridge Active,
  /proc supervisor root is /var/local/calendar-appliance/rootfs. pidof confirms
  no cvm/browserd/webreader. Charging1, battery99, system ext3 rootRO.
- Ran manage.sh confirm successfully; state now CONFIRMED_THIS_BOOT_ONLY.
  Watchdog will not restore stock for this boot. Startup remains enabled;
  every future boot still needs confirmation within600s until Pi automation
  handles it. Key-only Dropbear bound KINDLE_USB_IP:22 verified in ps.
- Combined unplugged appliance boot is PASS. Connected boot, deep suspend,
  unattended Pi recovery and calendar integration remain outside this result.

## 2026-09-21 — appliance artwork replacement

- User supplied Muybridge twelve-panel print and requested artwork crop for
  appliance mode. Initial built-in image editing preview changed image details;
  did not install it. Asked permission for literal crop/resize; user agreed.
- Preserved original3400x2096 PNG in appliance/assets. Added reproducible
  prepare-horse-art.py: crop(40,52,3346,1699), grayscale, proportional576x287,
  centered white600x800. Visually inspected final; retains all12 panels/order,
  excludes caption. No AI-generated pixels in selected final asset.
- USB device30 present; reactivated existing host profile. SSH reports appliance
  ENABLED/READY/CONFIRMED. Old imageMD5 795b4f894cf4bc664578c5ead2aae4ae.
  Copied old card to private data/current.before-horse.png (previously absent),
  uploaded new image to horse-upload.png, verified MD5 against host
  76f1ff76d1654a8531ee1aa7ede9e654, atomically renamed to current.png and synced.
  No boot/power/service changes. New image persists in existing appliance data.

## 2026-09-22 — standalone Wi-Fi client feasibility

- Read local OPERATING.md, manage.sh and prior log. Initial ./kindle-ssh
  inventory blocked by sandbox netlink permissions; escalated retry found no
  configured USB route. lsusb, ip -brief addr and nmcli connection show found
  0525:a4a2 device31 and unaddressed USB_INTERFACE. Activated the existing
  isolated profile with nmcli connection up kindle-usb-test. No other host
  connection was changed.
- USB SSH inventory: uname -a, manage.sh status, free, df -h, ifconfig -a.
  Appliance ENABLED_FOR_BOOT/READY/CONFIRMED. RAM256112KiB total,143760KiB
  free; /var/local18.5MiB available and /mnt/us1.2GiB available. wlan0 up
  but unaddressed. Stock shell lacks command builtin and grep -E; repeated
  tool discovery using which and grep -e.
- curl --version:7.21.4 with OpenSSL0.9.8j; openssl version confirms2009
  runtime. wget present; python not found on PATH. wpa_supplicant, wifid and
  powerd running. Read wpa_cli status/list_networks (no passwords), route -n,
  init scripts wifi/wifid and udhcpc default.script. Wi-Fi authentication
  reported COMPLETED on saved home network, but no IP/default route.
- lipc-probe -v on wifid and powerd exposed supported properties. Powerd
  state suspended/status Shutdown; wifid cmState NA. Broad property probe
  also printed device identifiers; do not repeat it for routine health checks.
- Temporary test: lipc-set-prop -i com.lab126.powerd wakeUp 1; sleep5;
  ifconfig wlan0; route -n; read powerd state and wifid cmState. Result active,
  CONNECTED, DHCP INITIAL_KINDLE_WIFI_IP/24 and gateway WIFI_GATEWAY. No manual DHCP,
  credentials changes, power-policy changes or startup edits needed.
- curl --connect-timeout10 --max-time20 -I https://example.com (arguments
  supplied with spaces) returned HTTP200 with default certificate checks;
  no -k used. This is one endpoint test, not proof of modern TLS support,
  endpoint compatibility, proxy absence, or production downloader security.
- manage.sh status remains ENABLED/READY/CONFIRMED; supervisor tail shows
  horse hash76f1ff76d1654a8531ee1aa7ede9e654 redrawn after Active transition.
- Uncertainties: target server/URL not chosen; secure compatibility with it,
  conditional GET, image validation, timed wake and charger-only boot remain
  untested. No polling client installed. Existing boot watchdog unchanged.
- Next safest action: identify intended image server, test its HTTPS endpoint
  without credentials first, then build a bounded manual download/validate
  trial before changing startup or suspend behavior.

## 2026-09-22 — Picsum placeholder over Wi-Fi

- User chose `https://picsum.photos/600/800` as placeholder source. Kindle
  curl -L -I returned405 (HEAD unsupported). Actual GET to /tmp failed with
  TLS protocol-version alert; stock curl7.21.4/OpenSSL0.9.8j is not usable
  for this source. No certificate checks were disabled.
- Host GET returned200 image/jpeg. Added `appliance/placeholder_server.py`:
  modern host fetches one photo per local day, converts to600x800 grayscale
  PNG using Pillow, serves `/calendar.png` with ETag on Wi-Fi address
  DESKTOP_WIFI_IP:8765. Tested host response200 and 8-bit grayscale PNG.
  Server is foreground test process, not installed as persistent systemd
  service. No calendar data or credentials are used.
- Kindle GET over Wi-Fi to host returned200,175272 bytes, correct PNG header.
  Added `appliance/poll-image.sh`, transferred to internal appliance dir.
  It checks READY, conditional ETag, max size/time, PNG dimensions/mode,
  and atomically replaces current.png on hash change. Saved horse image as
  current.before-picsum.png (MD5 76f1ff76d1654a8531ee1aa7ede9e654).
- Manual first poll: IMAGE_UPDATED MD587833d1943431f2039ef3bff7a4fefa5.
  Supervisor logged RENDER_OK for that hash. User visually confirmed the
  grayscale photo. Manual second poll: NOT_MODIFIED (HTTP304), image hash
  unchanged. Temporary60-second loop produced two NOT_MODIFIED entries.
- Initial poller TERM trap did not stop the Kindle background shell; after
  checking exact /proc cmdlines, KILL stopped duplicate PIDs12965/13276 and
  later13433. Current single loop PID13837 (this boot only), interval900s.
- Added opt-in `appliance/wifi-client.sh`; modified manager boot branch to
  launch it only when IMAGE_URL exists after APPLIANCE_READY. Worker retries
  Wi-Fi poll, confirms this boot only after successful validated200/304,
  then execs15-minute loop. Existing600-second watchdog restores stock if
  unconfirmed. Staged scripts as .new, syntax checked on host and Kindle,
  retained old manager as manage.before-wifi.sh, atomically installed new
  scripts and IMAGE_URL. Live worker logged NOT_MODIFIED,
  CONFIRMED_THIS_BOOT_ONLY, WIFI_CLIENT_READY, NOT_MODIFIED; process now
  /bin/sh poll-image.sh loop URL900. Current ENABLED/READY/CONFIRMED and
  image hash unchanged. No reboot was triggered.
- Uncertainties: opt-in worker not yet tested after physically unplugged
  reboot; manager still requires USB gadget startup (though original unplugged
  boot succeeded); charger-only power behavior and periodic wake not proven.
  HTTP test endpoint is local-network plaintext and contains only public art.
  Host server uptime, IP permanence and production access control remain open.
- Next safest action: user physically unplug USB and restart Kindle through
  known unplugged method while host placeholder server stays up. After boot,
  inspect screen, optionally reconnect USB and read wifi-client.log and state.

## 2026-09-22 — unplugged Wi-Fi boot test passed

- User agreed to coordinated test. Scheduled `/sbin/reboot` after75s over
  USB SSH; user unplugged before timer. USB gadget disappeared from lsusb.
  Host placeholder server remained available. No response from Kindle while
  booting; then at19:49:17 local, server logged two GET/304 requests from
  INITIAL_KINDLE_WIFI_IP. User saw reader screen briefly followed by photo.
- After user reconnected, lsusb found device32 0525:a4a2. Reactivated only
  existing kindle-usb-test profile and inspected key-only SSH. Uptime2min;
  startup log VOLUMD_READY seconds3, NETWORK_READY, APPLIANCE_READY,
  WIFI_CLIENT_STARTED. Worker log NOT_MODIFIED,
  CONFIRMED_THIS_BOOT_ONLY, WIFI_CLIENT_READY, NOT_MODIFIED. Current status
  ENABLED_FOR_BOOT/READY/CONFIRMED; loop PID4125 with900s interval.
- Current image MD587833d1943431f2039ef3bff7a4fefa5, supervisor
  RENDER_OK, no cvm/browserd/webreader PIDs. Battery96%, charging1 after
  USB reconnect. /dev/root ext3 remains ro. Wi-Fi wlan0 DHCP INITIAL_KINDLE_WIFI_IP.
- Deduction: Kindle-only Wi-Fi image polling and automatic per-boot
  confirmation work after an unplugged reboot, without USB data attached.
  Initial reader screen is expected while stock initializes before takeover.
- Remaining: placeholder server is foreground only; host IP fixed only for
  current network session; charger-only power, repeat sleep cycles and true
  shutdown recovery not yet verified. Production calendar renderer and
  access-controlled transport not yet implemented.

## 2026-09-22/23 — battery-only Wi-Fi transfer

- User unplugged Kindle USB cable from computer. Host lsusb no longer showed
  0525:a4a2; user reported photo looked good. The assistant initially
  misunderstood this as a move to a wall charger. An initial wait
  for a scheduled poll was mistimed using host wall time; no request was seen
  in that window. User reconnected to computer for diagnostics.
- Over USB SSH: current boot remained ENABLED/READY/CONFIRMED, poller PID4125
  alive, power-state log showed Active, Screen Saver and Ready to suspend;
  supervisor continued to log RENDER_OK on state changes. Battery97%,
  isCharging1 after reconnect. Wi-Fi was connected with INITIAL_KINDLE_WIFI_IP. At
  00:08:43 UTC, a NOT_MODIFIED entry appeared after reconnection. This does
  not establish that it would have polled on charger power, so a timed test
  followed.
- Verified PID4125 command line then stopped that test loop. Started a
  one-shot shell worker PID9235: sleep90, poll once, then exec normal900s
  polling loop. User unplugged the cable again. Host confirmed Kindle
  absent from USB by00:09:55 UTC. Image server later logged two GET/304
  requests from Kindle Wi-Fi INITIAL_KINDLE_WIFI_IP at20:10:40 local (00:10:40 UTC),
  while USB remained absent. Requests correspond to one-shot poll and loop's
  immediate first poll; no image refresh was needed. Host endpoint still200
  and Kindle still absent from lsusb at00:12:07 UTC.
- Correction after user clarification: No wall charger was present. Kindle
  completed a timed Wi-Fi image check on battery alone. The one-shot worker
  automatically handed over to900-second loop. This verifies USB-free data
  transfer, not external-power operation or continuous ability to wake from
  deep kernel suspend. No root/boot/firmware edits were made during this test.

## 2026-09-22/23 — work calendar and six-day preview

- User provided an interactive Google Calendar link; generic web and computer
  browser access could not read it. User then provided a private iCal export
  URL. Fetched over HTTPS to /tmp without printing its token or event text.
  Feed was an iCalendar file of about2.95MB with2191 VEVENT entries,287
  RRULE entries,823 RECURRENCE-ID entries and303 EXDATE entries. URL stored
  locally in `.secrets/work-calendar-url`, mode0600 and ignored by Git.
- Installed Pillow12.3.0, icalendar7.3.0 and recurring-ical-events3.8.2 into
  ignored `.venv` via uv. Added pinned appliance/requirements.txt. Library
  expanded current local day to2 events and next day to3, without exposing
  event titles in diagnostic logs.
- Added daily render_calendar.py using normalized event inputs and ICS
  recurrence expansion. User steered toward a rolling six-day view, so added
  render_six_day.py: today+5, America/New_York, 600x800 L PNG, all-day and
  timed event rows, today highlight, empty days and overflow counts. Local
  real-feed preview is appliance/build/work-six-day.png (Git-ignored).
- Added calendar_server.py reading URL from ignored secret file; HTTPS feed
  check every5min, cached last good data, IP allowlist, ETag/304, local date
  rollover. Tested loopback port8766:200 PNG hash matched CLI preview; 304
  returned for matching ETag. Simulated23:59->00:00 in New York; ETag changed.
  Service is not yet bound to the LAN or connected to Kindle.
- Independently, changed Picsum server source to a mountain image; host ETag
  changed from9d886d... to3d92f4... and validated600x800 grayscale PNG.
  User still saw the prior leaf after expected15-minute window. Server saw no
  Kindle GET in that window. This does not disprove short-interval polling,
  which earlier succeeded unplugged; sleep/timer behavior needs device logs.
- Remaining: diagnose long polling under suspend, choose secure work-image
  LAN exposure and destination server, then deploy six-day endpoint to Kindle.
  Physical display rollover at midnight remains unverified.

## 2026-09-22/23 — USB reconnection, routing and RTC investigation

- With USB reconnected, the device was ENABLED/READY/CONFIRMED and the
  900-second poller remained alive. Charger-test log had only its earlier two
  NOT_MODIFIED results, while power-state log repeatedly showed Screen Saver
  and Ready to suspend. A manual `poll-image.sh once` fetched the changed
  mountain placeholder (MD5 b1af6ac37fd8fa93069ab11f9230846a), and the
  display supervisor logged RENDER_OK for that hash. Thus transport and image
  refresh work while the Kindle is awake.
- Host `ip -br addr` and `ip route get INITIAL_KINDLE_WIFI_IP`: host Wi-Fi is
  DESKTOP_WIFI_IP/24 on WIFI_INTERFACE, with a direct route to Kindle INITIAL_KINDLE_WIFI_IP.
  Kindle `ip route get DESKTOP_WIFI_IP` selected wlan0, source INITIAL_KINDLE_WIFI_IP;
  stock curl obtained HTTP200 from the image server. The USB gadget is on a
  separate USB_SUBNET route. User's hardwired-to-Wi-Fi firewall cannot
  explain this direct same-Wi-Fi path; prior GET/304 requests were observed
  while USB was unplugged. BusyBox `timeout` segfaults on this firmware;
  avoid it. Curl's own `--max-time` works.
- Read `/sys/class/rtc/rtc1/{name,date,time,since_epoch,wakealarm}` and
  `/proc/driver/rtc`. rtc1 is pmic_rtc with a1970-relative clock and empty
  wakealarm; rtc0 is mxc_rtc with correct2026 time but has no wakealarm node.
  A model-specific [Kindle 4 weather-display daemon](https://github.com/melihkarakelle/kindle4-weather-display/blob/main/kindle_daemon.sh.example)
  suggests rtc1 alarm and `echo mem` for scheduled wake. A brief one-shot
  worker was staged in `/tmp`, but the alarm readback was empty immediately
  after the write. The worker was killed before its scheduled suspend and
  its temporary script removed. A second direct RTC alarm write also
  read back empty after zero and one seconds; it was then cleared. No
  forced suspend occurred and no persistent power-policy change was made.
  [Other Kindle 4 owners report the same empty readback](https://www.mobileread.com/forums/showthread.php?t=256411),
  so the RTC approach is unverified on this unit and should not yet be used
  for unattended wake. The existing stock powerd was observed suspending and
  resuming normally in dmesg; that does not establish our own RTC wake.
- Next safest action: keep stock powerd, determine whether a documented
  powerd/LIPC timed wake is available or test a charging-only keep-awake
  policy with a short interval and measured battery impact. Until one is
  proven, the six-day image can update whenever the Kindle next wakes, but
  an exact midnight display rollover is not guaranteed.
- Further inspection: `lipc-probe -v com.lab126.powerd` exposes a write-only
  integer `rtcWakeup`, and `/sys/devices/platform/mxc_rtc.0/wakeup_enable`
  exists and initially read0. A [related Kindle i.MX508 field report](https://gist.github.com/masudayasuto/1dc1baca03f072f61173cf6358f90508)
  uses the latter with a relative-seconds value; model-adjacent reports say
  LIPC `rtcWakeup` must be issued at readyToSuspend. Wrote180 to
  `mxc_rtc.0/wakeup_enable` without suspending; it returned success and
  read180 immediately and one second later. Writing0 then still read180,
  so the timer may be latched and is not assumed cancelled. After more than
  three wall-clock minutes while awake/USB-connected it still read180, so
  this looks like a pending suspend interval rather than an active countdown.
  No explicit suspend was issued. User was asked to unplug for a natural
  stock-suspend wake test, but USB was still attached at that check.

## 2026-09-22/23 — controlled Kindle 4 wake tests

- User confirmed the forest/mountain placeholder was visible and agreed to
  a coordinated unplugged test. Exact-model [kindle-dash](https://github.com/pascalw/kindle-dash)
  uses `/sys/devices/platform/mxc_rtc.0/wakeup_enable` immediately before
  `echo mem > /sys/power/state` on Kindle 4 NT. No boot hook or permanent
  polling change was made for these tests.
- First temporary `/tmp` one-shot used a stale180-second value written about
  eight minutes before suspend. It suspended at00:50:27 UTC and resumed at
  00:54:39, 252 seconds later, coincident with USB reconnection. It then
  logged NOT_MODIFIED and POLL_OK; RTC read0. This run cannot establish RTC
  wake because the relative timer was written too early.
- Corrected one-shot wrote120 to `mxc_rtc.0/wakeup_enable` immediately before
  suspend at00:55:53; readback was120. The kernel resumed only7 seconds later
  while USB was absent, and the worker successfully logged NOT_MODIFIED and
  POLL_OK at00:56:13 over Wi-Fi. This proves another USB-free fetch, but the
  7-second wake is not the requested120-second wake. Stock power management
  later suspended again for130 seconds and resumed around USB reconnection;
  no independent request was seen around the expected RTC wake window. Wake
  cause of the early resume is uncertain; do not call scheduled RTC wake a
  success. Do not deploy an RTC polling loop yet.
- Both one-shot workers exited. The temporary `/tmp/rtc-wake-test.sh` was
  removed. RTC `mxc_rtc.0/wakeup_enable` read0 and rtc1 wakealarm was empty.
  Normal appliance status remained ENABLED_FOR_BOOT/READY/CONFIRMED; existing
  900-second poller was alive. Current displayed placeholder PNG MD5 is
  b1af6ac37fd8fa93069ab11f9230846a and supervisor logged RENDER_OK.
  Wi-Fi was CONNECTED; battery99% and charging over reconnected USB. Host
  placeholder server remains on Wi-Fi port8765; real calendar server remains
  loopback-only on8766. No public Cloudflare tunnel was started.
- Next session: inspect wake source and interaction with powerd/USB disconnect
  before another controlled RTC test. A fixed-period shell `sleep 900` is
  not yet reliable across deep suspend. The six-day calendar renderer and
  loopback server are ready but not deployed to the Kindle. If using
  TryCloudflare later, first test with a nonprivate placeholder because its
  URL is public/ephemeral and the stock Kindle TLS stack is old.

## 2026-09-23 — retrospective wake-cause diagnosis

- Read-only inspection after overnight USB connection: same Kindle boot has
  uptime >11 hours, appliance ENABLED_FOR_BOOT/READY/CONFIRMED, RTC wakeup
  register0, battery98% and charging. The temporary RTC worker is gone.
  Kindle's `/tmp/calendar-appliance/rtc-wake-test.log` remains intact. Kernel
  ring buffer still shows a `pmic:faulti:sense_0=0x200` USB/charger event
  during the brief6-second suspend. Powerd's detailed syslog for the test
  hour had rotated out of `/var/local/log`; do not infer an exact kernel wake
  IRQ from it.
- Host `journalctl -k` supplies precise cable timing. First test: USB
  disconnected20:50:10 EDT, Kindle explicitly suspended20:50:27 and resumed
  20:54:39, exactly when host detected USB reconnection. Second test: Kindle
  explicitly suspended20:55:53 after setting120 seconds; host USB removal
  was20:55:55, only2 seconds later; Kindle resumed at20:56:01 after7 seconds.
  Host did not see USB reconnection until21:00:01. The close timing, plus the
  Kindle charger notification, makes the delayed unplug event the likely
  cause of the premature wake. It does not prove RTC failure or success.
- Corrected next test design: start a delayed, one-shot worker over USB;
  unplug and leave the device awake for a settling period; verify on-device
  `isCharging=0` and no USB gadget event pending; only then write a fresh
  `mxc_rtc.0/wakeup_enable` interval and immediately enter suspend. Record
  wall-clock times and kernel/host logs. A short power press or reconnect
  remains the recovery path. No such test was run during this diagnosis.
- Overnight host status: neither foreground prototype server on8765 nor
  loopback calendar server on8766 is still listening. Kindle's original
  900-second polling shell remains alive but its test log has repeated
  `curl: (7) couldn't connect to host`/POLL_FAILED entries. This is a
  separate reliability issue: the image endpoint needs a persistent service
  before relying on overnight calendar turnover. Nothing was restarted or
  changed on the Kindle during this read-only inspection.

## 2026-09-23 — four-cycle five-minute unplugged image test

- Started a foreground host placeholder server on DESKTOP_WIFI_IP:8765, now
  preloading four public Picsum images and rotating among them every240
  seconds. This shorter server rotation ensures a different frame is ready
  for each300-second Kindle wake. No private calendar feed was served.
- Staged a runtime-only `/tmp/rtc-five-minute-test.sh` worker on the Kindle.
  It preserves/restores the previous `preventScreenSaver` value, waits90
  seconds after launch for USB disconnection to settle, verifies
  `isCharging=0`, then writes a fresh relative300-second interval to
  `mxc_rtc.0/wakeup_enable` immediately before each suspend. Short spurious
  wakes rearm only the remaining interval; low battery, charger return, and
  repeated fetch errors are fail-safes. It is bounded to four cycles and
  makes no boot changes. Existing900-second poller was left in place.
- Host kernel log confirmed USB removal at07:36:58 EDT; worker started at
  07:36:19, leaving about51 seconds of cable-event settling before first
  RTC arm. Host `lsusb` stayed empty throughout all four checks. Image
  server recorded Kindle Wi-Fi INITIAL_KINDLE_WIFI_IP GET/200 at07:42:54,07:48:11,
  07:53:28 and07:58:44 EDT. Inter-request gaps were317,317 and316 seconds,
  consistent with300 seconds asleep plus Wi-Fi reconnect/render overhead.
  Server ETags changed between intervals, so these were new image transfers.
- User was asked to reconnect USB after the fourth cycle so the Kindle's
  local log, render hashes, battery and restored power state can be checked.
  Reconnection check: Kindle log showed `RESUME` after302 seconds for each
  of all four cycles, `IMAGE_UPDATED`/`POLL_OK` each time, and final
  `DONE_FOUR_CYCLES` followed by `EXIT restored_preventScreenSaver=0`.
  Supervisor logged `RENDER_OK` for each corresponding MD5: cycle1
  9fefc73874576904fc229e3c43aaeb05, cycle2
  9fd852cea27dc75e50d3141ce7a3039e, cycle3
  b1af6ac37fd8fa93069ab11f9230846a, cycle4
  9fefc73874576904fc229e3c43aaeb05. Thus controlled RTC wake,
  Wi-Fi download and e-ink refresh all passed with USB absent.
- After test, RTC register read0, powerd `preventScreenSaver` read0,
  appliance status remained ENABLED_FOR_BOOT/READY/CONFIRMED, and no test
  worker remained. Battery was97% at USB-settled start and96% after later
  reconnection (not a precise 20-minute consumption estimate); charging1.
  The temporary device `/tmp/rtc-five-minute-test.sh` was removed. The
  original900-second poller remains alive and later fetched the server's
  rotating forest frame; current image MD5 is
  b1af6ac37fd8fa93069ab11f9230846a. The rotating host server is still
  a foreground prototype, not a persistent service. No permanent five-
  minute boot loop was installed; the verified bounded test stopped after
  four cycles as designed.

## 2026-09-23 — live six-day calendar endpoint

- Revalidated the private ICS feed and six-day renderer on loopback8766:
  HTTP200 produced a600x800 mode-L PNG of22,826 bytes for2026-09-23;
  matching ETag produced304. The loopback preflight server was stopped.
- Replaced the foreground Picsum server on DESKTOP_WIFI_IP:8765 with an enabled
  user systemd `calendar-server.service`, using the private URL only from
  ignored `.secrets/work-calendar-url` mode0600. The unit restarts on
  failure, binds host Wi-Fi address DESKTOP_WIFI_IP and allows only Kindle
  Wi-Fi INITIAL_KINDLE_WIFI_IP and host Wi-Fi DESKTOP_WIFI_IP. A test request sourced from
  host wired DESKTOP_LAN_IP returned403. This is plain HTTP, not a public
  tunnel; IP allowlisting does not provide encryption/authentication.
  `loginctl show-the local account` reports Linger=no, so the service is not
  guaranteed to survive user logout. Current DHCP addresses are assumed.
- Kindle `IMAGE_URL` already pointed at this endpoint. Manual
  `poll-image.sh once` returned `IMAGE_UPDATED` with MD5
  6bd8db2b45fd713cc66840fd02fcfce8; supervisor logged matching
  `RENDER_OK`. User visually confirmed the calendar on e-ink. Existing
  background poller still uses900-second shell sleep, not RTC wake.
- A two-cycle RTC poll test was launched at09:34:16 EDT with a90-second
  unplug window. Host USB remained attached at09:35:25 and disconnected
  at09:35:54, approximately eight seconds after the safety deadline; this
  run likely exited `ABORT_STILL_CHARGING` and did not test RTC polling.
  Device log confirmation awaits a brief USB reconnection. The test script
  was revised locally to wait up to three minutes for unplug, then allow a
  full minute for the cable event to settle before arm/suspend. That revised
  script has not been transferred or run yet.

## 2026-11-09 — USB rediscovery and calendar refresh

- Found the Kindle 4 (D01100, firmware 4.1.4, build
  `001-H303_yoshi-354363`) as USB Ethernet gadget `0525:a4a2` under
  `cdc_ether`. The host interface `USB_INTERFACE` initially had a
  link-local address. Set `USB_HOST_IP/24` on the active connection
  only and verified host-key-pinned SSH to `KINDLE_USB_IP` with
  `./kindle-ssh`. Reapplied the temporary address after the host switched
  to the wired LAN.
- The appliance reported `ENABLED_FOR_BOOT`, `READY`, and `CONFIRMED`.
  The display supervisor and power-state monitor were alive. The Wi-Fi
  worker's saved PID was absent, so the calendar was still displaying the
  September image despite the desktop server running.
- Fetched the work iCal feed, rendered the November 9–14 image, and
  transferred it over USB SSH. Validated the 600×800 grayscale PNG and
  checked the transfer hash before atomically replacing `current.png`.
  The supervisor logged `RENDER_OK` for the new hash. Subsequent layout
  iterations used the same USB upload and verification path.

## 2026-11-09 — six-day layout and all-day events

- Removed the work label, six-day label, subtitle, and midnight footer.
  Kept the date range and today's gray highlight, and removed the dark
  left bar from today's row.
- `layout_days()` allocates more height to days with over three events.
  It tightens line spacing when needed and uses a `+N more` line if the
  available screen height is exhausted. Checked ordinary, expanded, and
  overflow cases, including a preview with eleven events on one day.
- Bundled Inter 4.1 and its SIL Open Font License in
  `appliance/assets/inter/`. Pillow loads the variable font directly, so
  the renderer and service use the same font on the desktop and in Docker.
- The Thursday, November 12 test event arrived as an all-day entry.
  Verified it sorted before timed events and rendered it on the Kindle.
  Removed the `ALL` label, keeping the time column blank and the event
  title in the same column as timed titles. Pixel checks confirmed the
  blank time column, and the device logged a matching `RENDER_OK`.

## 2026-11-09 — power state and on-device indicator

- `powerd_test -s` reported Screen Saver while USB SSH was responsive.
  Battery was 10% and charging. An attempted `powerd_test -h` sent a
  simulated long power-button press and put the Kindle into suspend.
  `lipc-set-prop -i com.lab126.powerd wakeUp 1` restored Active. The
  Kindle reported 11% and charging after the wake.
- Added a device-side overlay to `appliance/supervisor.sh`. The
  supervisor draws the calendar PNG with `eips`, then draws the current
  power-state symbol as a separate text operation. The source PNG retains
  the same hash during a power-state change.
- Tried a bottom-margin label, then moved it to the upper-right at K4
  text cell `46 2`. The final symbols are `On` for Active and `zZ` for
  Screen Saver, Ready to suspend, Suspended, or Shutdown. Verified both
  symbols across a brief power-button press and USB wake. Framebuffer
  differences were confined to the upper-right status area in that test.
  E-ink retains the last drawn symbol during sleep or power-off.
- Deployed the supervisor to the appliance chroot and restarted only that
  worker. The previous versions are saved on the device beside
  `/sbin/display-supervisor` as `.before-power-overlay` and
  `.before-power-symbol` backups.

## 2026-11-09 — Wi-Fi polling restored

- The Kindle received a new Wi-Fi lease. The desktop service on port 8765
  returned HTTP 403 until its allowlist was updated. Restarted the
  appliance Wi-Fi worker and verified HTTP 200 followed by HTTP 304 from
  the Kindle's new address.
- The regular worker checks every 900 seconds while the processor is
  awake. Screen Saver mode can still allow polling. Deep suspend pauses
  the shell loop, and the display supervisor checks for a changed image
  every five seconds while running. The five-minute RTC wake tests above
  remain separate from the regular updater.
- The physical keypad on `/dev/input/event0` advertises
  `KEY_PAGEDOWN`. A listener could use a long Next Page press to start
  the poller or fetch immediately. The shortcut remains a design option.

## 2026-11-09 — TrueNAS deployment and multi-calendar support

- After the desktop moved to a wired connection, verified
  access to pfSense and TrueNAS management. TrueNAS initially refused TCP
  connections on port 8765. Used the local credential pipe for management access.
- Added `appliance/Dockerfile`, `appliance/.dockerignore`, and
  `appliance/compose.truenas.yaml`. Built the image locally, uploaded
  the allowlisted build files to `/mnt/apps/kindle-calendar`, and built
  and started the TrueNAS custom app `kindle-calendar`. The container
  runs as an unprivileged user with a read-only root filesystem and
  publishes `NAS_HOST:8765`.
- Added `CALENDAR_URLS` as a runtime environment setting for one or more
  Google Calendar secret iCal URLs, one per line. The app merges events
  into one six-day image. Each feed refreshes independently, keeps its
  last good data on fetch or parse failure, and retries failed fetches
  after one minute. Tests covered two feeds, duplicates in the URL list,
  per-feed recovery, and the desktop's existing `--url-file` mode.
  Deployed with the existing work feed. Feed URLs live in the TrueNAS app
  configuration, visible to administrators. The build context contains
  code and assets.
- Backed up the pfSense configuration and allowed inbound TCP on
  the Wi-Fi segment from the Kindle's Wi-Fi address to `NAS_HOST:8765`.
  Fetched and validated the PNG from the Kindle using `wlan0`, then
  changed its `IMAGE_URL` to `http://NAS_HOST:8765/calendar.png`.
  Saved the desktop URL as `IMAGE_URL.before-truenas` on the device.
- Restarted the 900-second worker against TrueNAS. It logged
  `IMAGE_UPDATED` for MD5 `33dd454c18d0e45d290be8051ef01576`, then
  `NOT_MODIFIED` on the conditional request. The display supervisor
  logged the matching `RENDER_OK` while the device was in Screen Saver.

## 2026-11-09 — fixed Wi-Fi address and wired LAN access

- The old Wi-Fi lease was inside the dynamic Kea pool. Checked that an address
  outside the pool was unused and reserved it for the Kindle's Wi-Fi MAC under the
  `kindle-calendar` hostname. Verified the generated Kea reservation
  and renewed the lease on the Kindle.
- The Kindle acquired `RESERVED_KINDLE_WIFI_IP`, but a stale
  `/tmp/no-default-route` file suppressed installation of the DHCP
  gateway. Moved it aside as `/tmp/no-default-route.before-fixed-ip` and
  renewed again. The Kindle installed its default route via
  `WIFI_GATEWAY` and fetched the TrueNAS image with HTTP 200. Removed
  the old `PREVIOUS_KINDLE_WIFI_IP` firewall rule after verifying the new path.
- With wired LAN access approved, added explicit `--allow-any` mode and
  rebuilt the TrueNAS app with that option. The desktop instance can still
  use `--allow-ip`. Verified HTTP 200 and a valid PNG from the wired LAN,
  and a successful Kindle poll from `RESERVED_KINDLE_WIFI_IP`. The pfSense exception
  for the Wi-Fi segment remains limited to the Kindle and TrueNAS TCP 8765.

## 2026-11-09 — repository split and service rebuild

- Moved the reviewed packages, stock-reader overlay, USB experiments,
  diagnostic tools, private backups, and evidence under `firmware/`.
  Added separate [firmware](../firmware/AGENTS.md) and
  [appliance](../appliance/AGENTS.md) runbooks. The root `kindle-ssh`
  entry point links to the relocated helper.
- Verified both package archive hashes and the backup manifests.
  Assembled a fresh Kindle userspace in a temporary directory from the
  relocated root backup and tested USB SSH through both helper paths.
- Replaced local network details and device identifiers in the public
  documentation. The Docker template takes its publish address at
  deployment, and the desktop unit reads network values from an
  ignored override file.
- Rebuilt the Docker image locally, synchronized the build inputs, and
  redeployed the TrueNAS app with its existing runtime configuration.
  Verified a new running container and matching, valid calendar PNGs
  from the wired LAN and the Kindle's Wi-Fi. The Kindle's automatic
  poller was running, and a manual poll fetched the updated frame.

See [calendar deployment](CALENDAR.md), [polling](POLLING.md), and
[appliance operations](OPERATING.md) for the current configuration.
