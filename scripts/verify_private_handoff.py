"""Verify a private payload, then optionally restore ignored files without overwriting."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def within(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise ValueError('Invalid relative payload path')
    parts = PurePosixPath(relative)
    if parts.is_absolute() or any(x in ('..', '.') for x in parts.parts):
        raise ValueError('Payload path escapes its root')
    resolved_root = root.resolve()
    target = (root / relative).resolve()
    if resolved_root not in target.parents:
        raise ValueError('Payload path escapes its root')
    return target


def verify(bundle):
    manifest_path = bundle / 'manifest.json'
    checksum_parts = (bundle / 'manifest.sha256').read_text(encoding='utf-8').split()
    if not checksum_parts:
        raise ValueError('Manifest checksum is empty; wait for the private bundle to finish syncing')
    expected = checksum_parts[0]
    if not re.fullmatch(r'[0-9a-f]{64}', expected) or digest(manifest_path) != expected:
        raise ValueError('Manifest checksum mismatch')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or not isinstance(manifest.get('files'), list):
        raise ValueError('Unsupported manifest schema')
    payload = bundle / 'payload'
    seen = set()
    for entry in manifest['files']:
        name = entry['path']
        path = within(payload, name)
        if name in seen:
            raise ValueError('Duplicate payload path')
        seen.add(name)
        if not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
            raise ValueError('Invalid SHA-256 in manifest')
        if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError('Integrity mismatch: ' + name)
    actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
    if actual != seen:
        raise ValueError('Payload file list differs from manifest')
    return manifest


def restore(bundle, repository, manifest):
    repository = repository.resolve()
    top = subprocess.check_output(['git', '-C', str(repository), 'rev-parse', '--show-toplevel'], text=True).strip()
    if Path(top).resolve() != repository:
        raise ValueError('Restore target must be the repository root')
    tracked = set(subprocess.check_output(['git', '-C', str(repository), 'ls-files', '-z']).decode().split('\0'))
    prepared = []
    for entry in manifest['files']:
        name = entry['path']
        target = within(repository, name)
        if name in tracked:
            raise ValueError('Refusing to restore a tracked file: ' + name)
        check = subprocess.run(['git', '-C', str(repository), 'check-ignore', '-q', '--', name], capture_output=True)
        if check.returncode != 0:
            raise ValueError('Restore destination is not Git ignored: ' + name)
        if target.exists() and (not target.is_file() or digest(target) != entry['sha256']):
            raise ValueError('Existing destination differs; preserve both versions: ' + name)
        prepared.append((entry, target))
    # Validate every destination before making any changes.
    copied = 0
    for entry, target in prepared:
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with (bundle / 'payload' / entry['path']).open('rb') as source, target.open('xb') as output:
            shutil.copyfileobj(source, output)
        if digest(target) != entry['sha256']:
            raise ValueError('Restored checksum differs: ' + entry['path'])
        copied += 1
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--restore-to', type=Path)
    args = parser.parse_args()
    try:
        manifest = verify(args.bundle)
        result = {'integrity': 'verified', 'files': len(manifest['files']), 'restored': 0}
        if args.restore_to:
            result['restored'] = restore(args.bundle, args.restore_to, manifest)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'ERROR: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
