#!/usr/bin/env python3
"""Build reproducible source/install archives from a checked-out Git revision."""
import argparse
import ast
import datetime
import gzip
import hashlib
import io
from pathlib import Path
import re
import subprocess
import tarfile
import tomllib
import zipfile
from verify_manifest import verify


def build(version, output):
    root = Path(__file__).resolve().parents[1]
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?', version):
        raise ValueError('Use a semantic version such as 3.1.0')
    module = ast.parse((root / 'EG-Clicker.py').read_text())
    app_version = next(ast.literal_eval(node.value) for node in module.body
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in node.targets))
    rust_version = tomllib.loads((root / 'Cargo.toml').read_text())['package']['version']
    if app_version != version or rust_version != version:
        raise ValueError('Application and Cargo versions must match the release')
    verify(root)
    if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain']).strip():
        raise ValueError('Release builds require a clean Git checkout')
    names = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z']).decode().split('\0')
    names = sorted(name for name in names if name)
    epoch = int(subprocess.check_output(['git', '-C', str(root), 'log', '-1', '--format=%ct']))
    output.mkdir(parents=True, exist_ok=True)
    prefix = f'EG-Clicker-{version}'
    archive = output / f'EG-Clicker-v{version}.tar.gz'
    zipped = output / f'EG-Clicker-v{version}.zip'
    with archive.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=epoch) as gz:
        with tarfile.open(mode='w', fileobj=gz) as tar:
            for name in names:
                source = root / name
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f'Refusing nonregular source: {name}')
                data = source.read_bytes()
                info = tarfile.TarInfo(f'{prefix}/{name}')
                info.size, info.mtime = len(data), epoch
                info.mode = 0o755 if source.stat().st_mode & 0o111 else 0o644
                tar.addfile(info, io.BytesIO(data))
    timestamp = datetime.datetime.fromtimestamp(epoch, datetime.timezone.utc).timetuple()[:6]
    with zipfile.ZipFile(zipped, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in names:
            source = root / name
            item = zipfile.ZipInfo(f'{prefix}/{name}', date_time=timestamp)
            item.create_system = 3
            item.external_attr = ((0o755 if source.stat().st_mode & 0o111 else 0o644) | 0o100000) << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(item, source.read_bytes())
    sums = output / 'SHA256SUMS'
    sums.write_text(''.join(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in (archive, zipped)))
    return archive, zipped, sums


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('dist'))
    args = parser.parse_args()
    for path in build(args.version, args.output_dir):
        print(path)
