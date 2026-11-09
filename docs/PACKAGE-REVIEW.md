# Original K4 package review — 2026-09-21

The archives and reviewed payloads now live in [`firmware/packages/`](../firmware/packages/).
See the [Kindle USB runbook](../firmware/AGENTS.md) for the tested staging and
recovery steps.

Downloaded to host only, via HTTPS links from the original maintainer threads:

- [Jailbreak 1.8.N](https://www.mobileread.com/forums/attachment.php?attachmentid=141180&d=1439936080)
  SHA256: `e83da520a25b0186433f50d93e80af7245fbdf2bc2fb3593e25c2c01ddec9c52`
- [USBNetwork 0.57.N K4](https://www.mobileread.com/forums/attachment.php?attachmentid=141341&d=1440341478)
  SHA256: `17e22860b623c39aba876078ddeb538d8b09f60b53554e98e9ea5d1ad1291e49`

Hashes identify downloaded bytes; no independently published checksum was
verified. Neither archive was executed. No archive payload was extracted into
the host root or copied to the Kindle.

## Jailbreak inspection

Read the full README and listed ZIP and embedded tar contents. Read the full
embedded /var/local/system/mntus.params shell payload through tar stdout.
The tar contains absolute Kindle paths; do not extract it onto the host root.

The README's claim of writing only one new file is incomplete for this payload:
it installs /etc/uks/pubdevkey01.pem and overwrites the developer keystore under
/var/local/java/keystore. It stages scripts at /var/local/system/mntus.params
and /var/local/wan/info, removes/regenerates those during cleanup, removes its
payload directory, and writes documents/You are Jailbroken.txt. In diagnostics
it deletes ENABLE_DIAGS and diagnostic_logs, sets bootmode to main using idme,
and reboots. It can execute an existing /mnt/us/runme.sh: explicitly check for
that file before staging anything. Preserve any existing diagnostic_logs first.
The script recognizes model code 0E (our B00E serial) as Kindle 4.

Documented staging targets: user-volume root data.tar.gz, ENABLE_DIAGS, and
diagnostic_logs/device_info.xml. User then disconnects and uses Settings Restart,
followed by diagnostics D, R, Q. Do not stage other update packages simultaneously.
These are proposed actions, not actions performed.

Rollback after a successful normal boot: uninstall dependent packages first,
then use included Update_jailbreak_1.8.N_uninstall.bin through Settings' Update
Your Kindle. The uninstaller binary itself has not been decoded/reviewed.
This rollback depends on a working update system; it is not a guaranteed
debrick path or restoration of an overwritten prior developer keystore.

## USBNetwork documentation review

Read README_FIRST.txt and README in full. Update_usbnetwork_0.57.N_k4_install.bin
and corresponding uninstall.bin are included. Installer binary contents have
not yet been decoded; review is documentation-level for this package.

- Install/uninstall via Settings' Update Your Kindle, not by rebooting with
  the update file in user storage.
- Keep USE_VOLUMD=true for K4. Defaults: host USB_HOST_IP, Kindle
  KINDLE_USB_IP. Check actual configuration and route conflicts first.
- ;debugOn, ~usbNetwork, ;debugOff are the documented activation sequence.
  Repeating the toggle returns to mass storage and stops SSH/telnet.
- Do not create usbnet/auto during initial trials. Disconnect before switching.
- Default USB-only mode permits passwordless telnet and permissive SSH password
  authentication. Keep the link isolated, no forwarding/bridging or Wi-Fi SSH;
  plan key authentication and inspect daemon configuration before deployment.
- usbnet/etc/authorized_keys is the documented key location. SFTP/SCP are
  documented as supported in this package, subject to client compatibility.
- README warns K4 can fail to load g_ether when booted attached to a computer.
  Single-cable cold-boot/recovery behavior must therefore be tested; successful
  manual activation does not establish unattended resilience.

## Current blocker

Kindle serial matches, but /dev/sda is 0B without sda1. Await physical reconnect
into USB Drive Mode and battery state. No user-volume backup exists yet, so no
device modifications should begin. Backup will be read-only, with file hashes
verified against the host copy; it will not back up hidden internal partitions.
