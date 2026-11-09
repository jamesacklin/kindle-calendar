"""Read-only backup of the identified Kindle root partition over pinned USB SSH."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
ssh = str(root / 'kindle-ssh')
backup = root / 'backups/2026-09-21-before-display-service'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('serial', help='exact device serial verified from the physical Kindle')
args = parser.parse_args()

serial = subprocess.check_output([ssh, 'cat /proc/usid'], text=True).strip('\0\r\n ')
if serial != args.serial:
    raise SystemExit('Unexpected Kindle serial')
mounts = subprocess.check_output([ssh, 'cat /proc/mounts'], text=True)
if '/dev/root / ext3 ro,' not in mounts:
    raise SystemExit('Kindle root filesystem is not read-only')
backup.mkdir(mode=0o700, exist_ok=True)
image = backup / 'mmcblk0p1.img'
with image.open('xb') as output:
    subprocess.run([ssh, 'dd if=/dev/mmcblk0p1 bs=65536'], stdout=output, check=True)
if image.stat().st_size != 358400 * 1024:
    raise SystemExit('Wrong root image size; do not treat backup as verified')
with image.open('rb') as stream:
    local_md5 = hashlib.file_digest(stream, 'md5').hexdigest()
remote_md5 = subprocess.check_output([ssh, 'md5sum /dev/mmcblk0p1'], text=True).split()[0]
if remote_md5 != local_md5:
    raise SystemExit('Root image checksum mismatch')
with image.open('rb') as stream:
    sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
with (backup / 'manifest.json').open('x') as output:
    json.dump({'image': image.name, 'bytes': image.stat().st_size,
               'sha256': sha256, 'device_md5': remote_md5,
               'scope': 'Root partition after jailbreak/USBNetwork, before display service; not full-device recovery image'},
              output, indent=2)
print(f'Verified root backup: {image.stat().st_size} bytes, SHA256 {sha256}', flush=True)
