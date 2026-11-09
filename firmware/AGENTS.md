# Kindle 4 USB and firmware work

This directory covers the Kindle 4 Non-Touch D01100 with the B00E serial
prefix and firmware 4.1.4. `packages/` contains the reviewed jailbreak and
USBNetwork packages. `device/` holds the earlier stock-reader overlay, and
`experiments/` holds historical USB boot tests. The live calendar appliance
is maintained in [`appliance/`](../appliance/AGENTS.md).

## Identify the device and USB mode

Run commands from the repository root.

```sh
lsusb
lsblk -e 7 -o NAME,TRAN,MODEL,SIZE,FSTYPE,MOUNTPOINTS
ip -brief address
```

- In USB storage mode, confirm the Kindle's identity and actual mount point
  with `udevadm info` and `findmnt`. A zero-size disk is not a usable volume.
- In USBNetwork mode, expect Ethernet gadget `0525:a4a2`. Identify its
  actual interface, check for a route conflict, and give that interface
  `192.168.15.201/24` without a default route. The Kindle uses
  `192.168.15.244`. The [SSH helper](kindle-ssh) checks the route and uses
  the repository's ignored `.ssh/` key and pinned host key.

```sh
ip route get 192.168.15.244
./kindle-ssh 'cat /etc/version.txt; powerd_test -s'
```

When the stock reader is available, unplug USB and enter `;debugOn`,
`~usbNetwork`, and `;debugOff` as separate Home search commands to switch
modes, then reconnect. Follow the bundled
[USBNetwork instructions](packages/k4-usbnetwork-reviewed/README_FIRST.txt)
for key setup. Install only the public key on the Kindle and keep the USB
link isolated. Boot the appliance with USB unplugged, then connect for
maintenance. The tested stock-mode recovery path is in
[appliance operations](../docs/OPERATING.md).

## Stage a reviewed update over USB

Use this procedure when the task calls for a device update. Verify model,
firmware, and charge first. Mount the identified user volume read-only for
inventory and copy it to a private backup. Verify the backup against the
volume before remounting writable. Check both archive hashes against the
[package review](../docs/PACKAGE-REVIEW.md).

1. For the initial jailbreak, check the USB volume for collisions with
   `runme.sh`, `data.tar.gz`, `ENABLE_DIAGS`, and `diagnostic_logs/`.
   Preserve existing diagnostics and resolve collisions before proceeding.
   Copy only the reviewed `data.tar.gz`, `ENABLE_DIAGS`, and
   `diagnostic_logs/device_info.xml` to the user-volume root. Keep the tar
   compressed. Verify each copy with `cmp`, sync, and safely unmount.
2. Unplug USB and use **Settings → Menu → Restart**. In Diagnostics select
   **D**, then **R**, then **Q** to continue. Verify normal boot and the
   `You are Jailbroken` document. The exact sequence is in the bundled
   [jailbreak README](packages/k4-jailbreak-reviewed/README).
3. After verifying the jailbreak, stage only
   `Update_usbnetwork_0.57.N_k4_install.bin` from the reviewed USBNetwork
   package on the USB volume. Check for other staged updates, verify the
   copy, sync, and unmount. Unplug and use **Settings → Menu → Update Your
   Kindle**. Verify the USBNetwork install log after the device returns.
4. To uninstall with the stock update menu available, remove dependent
   packages first with their matching uninstallers. The jailbreak
   uninstaller comes last.

## Backups and recovery limits

`backups/` and `evidence/` are private and Git-ignored. The current
snapshots cover visible user storage and the root partition at specific
points in the September setup. The backup and verification scripts use
those historical paths and guard their output files against overwrites.
Pass the verified serial to `backup-root.py` or the verified user-volume
mount point to `verify-backup.py`.
The root image is an input to the appliance userspace build. A complete
firmware image and a validated raw partition restore procedure are still
missing. Treat unexpected boot or USB behavior as a recovery diagnosis.
The [technical log](../docs/TECHNICAL-LOG.md) records the tested steps and
failed boot experiments.
