"""Verify a Kindle file backup without modifying the source; save hashes locally."""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path, help='verified Kindle user-volume mount point')
source = parser.parse_args().source
backup = Path(__file__).resolve().parent / 'backups/2026-09-21-before-jailbreak'
target = backup / 'userstore'

def inventory(root):
    result = {}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise RuntimeError(f'Unexpected symlink: {path}')
        if path.is_file():
            with path.open('rb') as stream:
                digest = hashlib.file_digest(stream, 'sha256').hexdigest()
            result[str(path.relative_to(root))] = {
                'bytes': path.stat().st_size, 'sha256': digest
            }
    return result

original = inventory(source)
copied = inventory(target)
if not original or original != copied:
    raise SystemExit('FAIL: source and backup differ, or source is empty')
manifest = backup / 'manifest.json'
with manifest.open('x') as stream:
    json.dump({'verified_source': str(source), 'files': original}, stream, indent=2)
print(f'PASS: {len(original)} files, {sum(f["bytes"] for f in original.values())} bytes; all SHA-256 hashes match')
print(f'Manifest: {manifest}')
