"""Build an isolated, kernel-compatible application userspace from our own backup.

Never writes to a device. This is not a bootable image or a replacement PID 1.
"""
import hashlib
import json
import re
import shutil
import subprocess
import tarfile
from pathlib import Path

project = Path(__file__).resolve().parent.parent
image = project / 'firmware/backups/2026-09-21-before-display-service/mmcblk0p1.img'
output = project / 'appliance/build'
output.mkdir()  # refuse to overwrite an existing build
tree = output / 'rootfs'
tree.mkdir()
files = {
    '/bin/busybox': '/bin/busybox',
    '/usr/sbin/eips': '/usr/sbin/eips',
    '/lib/ld-linux.so.3': '/lib/ld-2.12.1.so',
    '/lib/libc.so.6': '/lib/libc-2.12.1.so',
    '/lib/libm.so.6': '/lib/libm-2.12.1.so',
    '/lib/libcrypt.so.1': '/lib/libcrypt-2.12.1.so',
    '/lib/libdl.so.2': '/lib/libdl-2.12.1.so',
}
manifest = {}
for dest, source in files.items():
    target = tree / dest.lstrip('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['debugfs', '-R', f'dump {source} {target}', str(image)], check=True)
    if not target.is_file() or not target.stat().st_size:
        raise SystemExit(f'Missing extracted file: {source}')
    target.chmod(0o755)
    elf = subprocess.check_output(['readelf', '-d', str(target)], text=True)
    needed = re.findall(r'Shared library: \[(.*?)\]', elf)
    missing = [name for name in needed if '/lib/' + name not in files]
    if missing:
        raise SystemExit(f'Unresolved dependencies for {dest}: {missing}')
    manifest[dest] = {'source': source, 'needed': needed,
                      'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
for applet in ['sh', 'sleep', 'md5sum', 'cat', 'ls', 'echo', 'uname', 'test']:
    (tree / 'bin' / applet).symlink_to('busybox')
for directory in ['dev', 'proc', 'sys', 'tmp', 'run', 'data', 'etc', 'sbin']:
    (tree / directory).mkdir(exist_ok=True)
shutil.copyfile(project / 'appliance/supervisor.sh', tree / 'sbin/display-supervisor')
(tree / 'sbin/display-supervisor').chmod(0o755)
with (output / 'manifest.json').open('x') as stream:
    json.dump({'status': 'HOST BUILT, NOT RUN ON KINDLE, NOT BOOTABLE',
               'files': manifest}, stream, indent=2)
with tarfile.open(output / 'application-userspace.tar.gz', 'w:gz',
                  format=tarfile.GNU_FORMAT) as archive:
    archive.add(tree, arcname='.')
print(f'Built {output}; ELF dependencies resolved. Runtime validation pending.')
