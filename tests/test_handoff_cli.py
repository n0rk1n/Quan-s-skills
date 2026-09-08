from __future__ import annotations

import json
import argparse
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_handoff_validator import VALIDATOR, valid_snapshot, latest_text

CLI = VALIDATOR.with_name('handoff.py')


class HandoffCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.candidate = self.root / 'candidate.md'
        self.candidate.write_text(valid_snapshot(), encoding='utf-8')
        self.directory = self.root / '.oriki' / 'handoffs'

    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-B', str(CLI), *map(str, args)],
                              capture_output=True, text=True)

    def publish(self):
        return self.run_cli('publish', '--root', self.root, '--candidate',
                            self.candidate, '--topic', 'example',
                            '--timestamp', '2026-09-08-1200')

    def write_latest(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        snapshot = directory / '2026-09-08-1200-existing.md'
        snapshot.write_text(valid_snapshot(), encoding='utf-8')
        (directory / 'LATEST.md').write_text(latest_text(snapshot.name), encoding='utf-8')
        return snapshot

    def test_publish_and_read_only_resume(self):
        result = self.publish()
        self.assertEqual(0, result.returncode, result.stderr)
        published = json.loads(result.stdout)
        snapshot = Path(published['snapshot'])
        self.assertEqual(self.directory / '2026-09-08-1200-example.md', snapshot)
        self.assertEqual(self.candidate.read_bytes(), snapshot.read_bytes())
        self.assertTrue(published['latest_updated'])
        self.assertIn(str(snapshot), published['resume_prompt'])
        before = {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                  for p in self.root.rglob('*') if p.is_file()}
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(0, result.returncode, result.stderr)
        restored = json.loads(result.stdout)
        self.assertEqual(str(snapshot), restored['snapshot'])
        self.assertEqual(valid_snapshot(), restored['content'])
        self.assertEqual('unavailable', restored['git']['status'])
        after = {str(p): (p.read_bytes(), p.stat().st_mtime_ns)
                 for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_repeated_publish_preserves_snapshot(self):
        first = self.publish()
        self.assertEqual(0, first.returncode, first.stderr)
        original = Path(json.loads(first.stdout)['snapshot'])
        second = self.publish()
        self.assertEqual(0, second.returncode, second.stderr)
        self.assertTrue(json.loads(second.stdout)['snapshot'].endswith('-example-02.md'))
        self.assertEqual(valid_snapshot(), original.read_text())

    def test_invalid_candidate_preserves_old_index(self):
        self.write_latest(self.directory)
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        self.candidate.write_text('incomplete', encoding='utf-8')
        result = self.publish()
        self.assertEqual(1, result.returncode)
        self.assertIn('missing-section', result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.directory.iterdir()})

    def test_malformed_index_blocks_publish_and_resume_without_fallback(self):
        self.write_latest(self.directory)
        self.write_latest(self.root / 'oriki-handoffs')
        latest = self.directory / 'LATEST.md'
        latest.write_text('bad index')
        for result in (self.publish(), self.run_cli('resume', '--root', self.root)):
            self.assertEqual(1, result.returncode)
            self.assertIn('invalid-latest-link', result.stderr)
        self.assertEqual('bad index', latest.read_text())
        self.assertEqual(2, len(list(self.directory.iterdir())))

    def test_legacy_priority_and_explicit_snapshot(self):
        old = self.write_latest(self.root / '.codex' / 'handoffs')
        first = self.run_cli('resume', '--root', self.root)
        self.assertEqual(0, first.returncode, first.stderr)
        self.assertEqual(str(old), json.loads(first.stdout)['snapshot'])
        newer = self.write_latest(self.root / 'oriki-handoffs')
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(str(newer), json.loads(result.stdout)['snapshot'])
        current = self.write_latest(self.directory)
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(str(current), json.loads(result.stdout)['snapshot'])
        result = self.run_cli('resume', '--snapshot', old)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(str(old), json.loads(result.stdout)['snapshot'])

    def test_unsafe_index_target_is_rejected(self):
        self.write_latest(self.directory)
        (self.directory / 'LATEST.md').write_text(latest_text('../../candidate.md'))
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(1, result.returncode)
        self.assertIn('escaping-latest-target', result.stderr)

    def test_publish_rejects_symlink_directory(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (self.root / '.oriki').symlink_to(outside, target_is_directory=True)
        result = self.publish()
        self.assertEqual(1, result.returncode)
        self.assertEqual([], list(outside.iterdir()))

    def test_explicit_root_required_and_must_exist(self):
        result = self.run_cli('publish', '--candidate', self.candidate, '--topic', 'x')
        self.assertEqual(2, result.returncode)
        result = self.run_cli('publish', '--root', self.root / 'missing',
                              '--candidate', self.candidate, '--topic', 'x')
        self.assertEqual(1, result.returncode)
        self.assertFalse((self.root / 'missing').exists())

    def test_git_state_is_collected_without_executing_snapshot(self):
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        self.write_latest(self.directory)
        before = subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain'])
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(0, result.returncode, result.stderr)
        state = json.loads(result.stdout)['git']
        self.assertEqual('available', state['status'])
        self.assertEqual(str(self.root), state['root'])
        self.assertIsNone(state['head'])
        self.assertEqual(before.decode().strip(), state['working_tree'])
        self.assertEqual(before, subprocess.check_output(['git', '-C', str(self.root), 'status', '--porcelain']))

    def test_index_replace_failure_reports_published_snapshot_and_keeps_index(self):
        self.write_latest(self.directory)
        original = (self.directory / 'LATEST.md').read_bytes()
        with mock.patch.object(sys, 'path', [str(CLI.parent), *sys.path]):
            spec = importlib.util.spec_from_file_location('handoff_cli_test', CLI)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        args = argparse.Namespace(root=self.root, candidate=self.candidate,
                                  topic='example', timestamp='2026-09-08-1200')
        with mock.patch.object(module.os, 'replace', side_effect=OSError('index update failed')):
            with self.assertRaises(module.HandoffError) as raised:
                module.publish(args)
        snapshot = Path(raised.exception.snapshot)
        self.assertEqual(valid_snapshot(), snapshot.read_text())
        self.assertEqual(original, (self.directory / 'LATEST.md').read_bytes())
        self.assertEqual(3, len(list(self.directory.iterdir())))

    def test_existing_publication_lock_preserves_files(self):
        self.write_latest(self.directory)
        (self.directory / '.publish-lock').mkdir()
        result = self.publish()
        self.assertEqual(1, result.returncode)
        self.assertIn('publication-locked', result.stderr)
        self.assertEqual(3, len(list(self.directory.iterdir())))

    def test_symlink_index_is_rejected(self):
        self.directory.mkdir(parents=True)
        (self.directory / 'LATEST.md').symlink_to(self.candidate)
        for result in (self.publish(), self.run_cli('resume', '--root', self.root)):
            self.assertEqual(1, result.returncode)
            self.assertIn('symlink-index', result.stderr)
        self.assertTrue((self.directory / 'LATEST.md').is_symlink())

    def test_simultaneous_publish_never_overwrites_snapshots(self):
        arguments = [sys.executable, '-B', str(CLI), 'publish', '--root', str(self.root),
                     '--candidate', str(self.candidate), '--topic', 'example',
                     '--timestamp', '2026-09-08-1200']
        processes = [subprocess.Popen(arguments, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True) for _ in range(4)]
        successes = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            if process.returncode == 0:
                successes.append(json.loads(stdout)['snapshot'])
            else:
                self.assertEqual(1, process.returncode, stderr)
                self.assertIn('publication-locked', stderr)
        self.assertGreaterEqual(len(successes), 1)
        self.assertEqual(len(successes), len(set(successes)))
        self.assertEqual(len(successes) + 1, len(list(self.directory.iterdir())))
        result = self.run_cli('resume', '--root', self.root)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(json.loads(result.stdout)['snapshot'], successes)


if __name__ == '__main__':
    unittest.main()
