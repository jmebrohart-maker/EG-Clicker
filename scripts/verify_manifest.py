#!/usr/bin/env python3
"""Verify the repository's recorded SHA-256 digests without executing app code."""
import hashlib
import json
from pathlib import Path
import re
import sys


def verify(root):
    entries = json.loads((root / 'SHA256-MANIFEST.json').read_text())
    if not isinstance(entries, dict) or not entries:
        raise ValueError('Manifest must be a nonempty object')
    failures = []
    for name, expected in entries.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or not isinstance(expected, str) or not re.fullmatch(r'[a-f0-9]{64}', expected):
            raise ValueError(f'Invalid manifest entry: {name}')
        source = root / path
        if source.is_symlink() or not source.is_file():
            failures.append(f'Missing or nonregular file: {name}')
        elif hashlib.sha256(source.read_bytes()).hexdigest() != expected:
            failures.append(f'Checksum mismatch: {name}')
    if failures:
        raise ValueError('\n'.join(failures))
    return len(entries)


if __name__ == '__main__':
    try:
        print(f'Verified {verify(Path(__file__).resolve().parents[1])} source checksums.')
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
