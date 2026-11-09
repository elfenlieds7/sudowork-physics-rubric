"""Synthetic payloads exercise integrity and non-destructive private restoration."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('handoff', Path(__file__).resolve().parents[1] / 'scripts/verify_private_handoff.py')
handoff = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(handoff)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.bundle = self.root / 'bundle'
        p = self.bundle / 'payload/data/private/example.bin'
        p.parent.mkdir(parents=True)
        p.write_bytes(b'synthetic fixture')
        self.manifest = {'schema_version': 1, 'files': [{'path': 'data/private/example.bin', 'bytes': p.stat().st_size, 'sha256': handoff.digest(p)}]}
        (self.bundle / 'manifest.json').write_text(json.dumps(self.manifest))
        (self.bundle / 'manifest.sha256').write_text(handoff.digest(self.bundle / 'manifest.json') + '  manifest.json\n')

    def tearDown(self):
        self.temp.cleanup()

    def repo(self):
        r = self.root / 'repository'
        r.mkdir()
        subprocess.run(['git', 'init', '-q', str(r)], check=True)
        (r / '.gitignore').write_text('data/private/\n')
        return r

    def test_complete_payload_verifies_and_restores_idempotently(self):
        m = handoff.verify(self.bundle)
        r = self.repo()
        self.assertEqual(handoff.restore(self.bundle, r, m), 1)
        self.assertEqual(handoff.restore(self.bundle, r, m), 0)

    def test_corrupt_payload_is_rejected(self):
        (self.bundle / 'payload/data/private/example.bin').write_bytes(b'corruption')
        with self.assertRaisesRegex(ValueError, 'Integrity mismatch'):
            handoff.verify(self.bundle)

    def test_corrupt_manifest_is_rejected(self):
        (self.bundle / 'manifest.json').write_text('{"schema_version": 1, "files": []}')
        with self.assertRaisesRegex(ValueError, 'Manifest checksum mismatch'):
            handoff.verify(self.bundle)

    def test_path_traversal_and_unlisted_files_are_rejected(self):
        with self.assertRaises(ValueError):
            handoff.within(self.root, '../escape')
        with self.assertRaises(ValueError):
            handoff.within(self.root, 'C:/escape')
        (self.bundle / 'payload/extra.bin').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError, 'file list differs'):
            handoff.verify(self.bundle)

    def test_existing_different_file_is_preserved(self):
        r = self.repo()
        p = r / 'data/private/example.bin'
        p.parent.mkdir(parents=True)
        p.write_bytes(b'existing data')
        with self.assertRaisesRegex(ValueError, 'Existing destination differs'):
            handoff.restore(self.bundle, r, self.manifest)
        self.assertEqual(p.read_bytes(), b'existing data')

    def test_unignored_or_tracked_destination_is_rejected(self):
        r = self.repo()
        (r / '.gitignore').write_text('')
        with self.assertRaisesRegex(ValueError, 'not Git ignored'):
            handoff.restore(self.bundle, r, self.manifest)
        (r / '.gitignore').write_text('data/private/\n')
        p = r / 'data/private/example.bin'
        p.parent.mkdir(parents=True)
        p.write_bytes(b'synthetic fixture')
        subprocess.run(['git', '-C', str(r), 'add', '-f', 'data/private/example.bin'], check=True)
        with self.assertRaisesRegex(ValueError, 'tracked file'):
            handoff.restore(self.bundle, r, self.manifest)


if __name__ == '__main__':
    unittest.main()
