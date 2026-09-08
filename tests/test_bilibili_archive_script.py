import base64
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [ROOT / f'skills/bilibili/archiving-bilibili-{k}/scripts/archive_bilibili.py'
           for k in ('favorites', 'following')]
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j4N8AAAAASUVORK5CYII=')


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPTS[0].is_file(), 'archive CLI must be implemented')
        spec = importlib.util.spec_from_file_location('bilibili_archive', SCRIPTS[0])
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.downloads = Path(self.tmp.name) / 'Downloads'
        self.downloads.mkdir()
        p = patch.object(self.m, 'DOWNLOADS', self.downloads)
        p.start()
        self.addCleanup(p.stop)
        self.calls = []
        def download(url, path):
            self.calls.append(url)
            path.write_bytes(PNG if 'bad' not in url else b'<html>error</html>')
            return url
        p = patch.object(self.m, 'download', side_effect=download)
        p.start()
        self.addCleanup(p.stop)

    def payload(self, n=1, kind='favorites'):
        ids = [f'BV{i:010d}' for i in range(1, n+1)] if kind == 'favorites' else [str(i) for i in range(1, n+1)]
        prefix = 'https://www.bilibili.com/video/' if kind == 'favorites' else 'https://space.bilibili.com/'
        return dict(source_url='https://www.bilibili.com/', end_confirmed=True,
                    items=[dict(id=i, canonical_url=prefix+i, display_name='同名 / [链接]',
                                image_source_url='https://i0.hdslb.com/test.png', metadata={'简介': '可见内容'}) for i in ids])

    def archive(self, payload=None, kind='favorites'):
        return self.m.archive(payload or self.payload(kind=kind), kind)

    def test_saves_real_local_image_record_and_summary(self):
        result = self.archive(self.payload(2))
        self.assertTrue(result['cleanup_ready'])
        self.assertEqual(result['verified_ids'], ['BV0000000001', 'BV0000000002'])
        batch = Path(result['batch'])
        self.assertEqual((batch/'BV0000000001/cover.png').read_bytes(), PNG)
        record = (batch/'BV0000000001/record.md').read_text()
        self.assertTrue(record.startswith('# 同名 / \\[链接\\]\n'))
        self.assertIn('https://www.bilibili.com/video/BV0000000001', record)
        self.assertIn('](cover.png)', record)
        self.assertIn('BV0000000002', (batch/'summary.md').read_text())
        self.assertTrue(self.m.verify(batch, 'favorites')['cleanup_ready'])

    def test_bad_image_blocks_entire_batch_and_resume_only_retries_failed(self):
        data = self.payload(2)
        data['items'][1]['image_source_url'] = 'https://i0.hdslb.com/bad.jpg'
        result = self.archive(data)
        self.assertFalse(result['cleanup_ready'])
        self.assertEqual(result['verified_ids'], [])
        self.assertEqual(result['remaining_ids'], [])
        batch = Path(result['batch'])
        self.assertTrue((batch/'BV0000000001/cover.png').exists())
        self.assertFalse((batch/'BV0000000002/cover.jpg').exists())
        def good(url, path):
            self.assertIn('bad.jpg', url)
            path.write_bytes(PNG)
            return url
        with patch.object(self.m, 'download', side_effect=good):
            self.assertTrue(self.m.resume(batch, 'favorites')['cleanup_ready'])
        self.assertEqual(len(list(self.downloads.iterdir())), 1)

    def test_invalid_inputs_fail_before_allocating_archive(self):
        cases = [self.payload(0), self.payload(41)]
        short = self.payload(); short['end_confirmed'] = False; cases.append(short)
        dup = self.payload(2); dup['items'][1] = dup['items'][0]; cases.append(dup)
        for field, value in [('id', '../escape'), ('canonical_url', 'https://evil.test/'),
                             ('image_source_url', 'file:///etc/passwd')]:
            data = self.payload(); data['items'][0][field] = value; cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.m.archive(data, 'favorites')
        with self.assertRaises(ValueError):
            self.m.archive(self.payload(23, 'following'), 'following')
        self.assertEqual(list(self.downloads.iterdir()), [])

    def test_following_saves_24_avatars(self):
        result = self.archive(self.payload(24, 'following'), 'following')
        self.assertEqual(len(result['verified_ids']), 24)
        self.assertTrue((Path(result['batch'])/'24/avatar.png').is_file())

    def test_existing_batch_is_not_overwritten(self):
        first = self.archive(); second = self.archive()
        self.assertNotEqual(first['batch'], second['batch'])
        self.assertTrue(self.m.verify(Path(first['batch']), 'favorites')['cleanup_ready'])

    def test_corrupt_image_record_or_summary_blocks_cleanup(self):
        for relative in ['BV0000000001/cover.png', 'BV0000000001/record.md', 'summary.md']:
            result = self.archive(); batch = Path(result['batch'])
            (batch/relative).write_bytes(b'corrupt')
            check = self.m.verify(batch, 'favorites')
            self.assertFalse(check['cleanup_ready'])
            self.assertEqual(check['verified_ids'], [])

    def test_resume_does_not_overwrite_changed_records_or_summary(self):
        for relative in ['BV0000000001/record.md', 'summary.md']:
            result = self.archive(); batch = Path(result['batch'])
            target = batch/relative
            target.write_text('external edit')
            with self.assertRaises(ValueError):
                self.m.resume(batch, 'favorites')
            self.assertEqual(target.read_text(), 'external edit')

    def test_symlink_image_and_foreign_batch_are_rejected(self):
        result = self.archive(); batch = Path(result['batch'])
        image = batch/'BV0000000001/cover.png'
        external = Path(self.tmp.name)/'outside.png'; external.write_bytes(PNG)
        image.unlink(); image.symlink_to(external)
        self.assertFalse(self.m.verify(batch, 'favorites')['cleanup_ready'])
        with self.assertRaises(ValueError):
            self.m.verify(Path(self.tmp.name), 'favorites')

    def test_update_requires_evidence_and_never_retargets_removed_ids(self):
        result = self.archive(self.payload(2)); batch = Path(result['batch'])
        for change in [{'id': 'BV0000000003', 'status': 'removed', 'evidence': 'reload'},
                       {'id': 'BV0000000001', 'status': 'removed', 'evidence': ''}]:
            with self.assertRaises(ValueError):
                self.m.update(batch, {'items': [change]}, 'favorites')
        check = self.m.update(batch, {'items': [{'id': 'BV0000000001', 'status': 'removed',
                                               'evidence': '重新加载收藏页核验消失'}]}, 'favorites')
        self.assertEqual(check['remaining_ids'], ['BV0000000002'])
        self.assertIn('重新加载收藏页核验消失', (batch/'summary.md').read_text())
        with self.assertRaises(ValueError):
            self.m.update(batch, {'items': [{'id': 'BV0000000001', 'status': 'unresolved', 'evidence': 'retry'}]}, 'favorites')
        with self.assertRaises(ValueError):
            self.m.resume(batch, 'favorites')

    def test_mutation_lock_prevents_competing_updates(self):
        result = self.archive(); batch = Path(result['batch'])
        (batch/'.archive.lock').write_text('other operation')
        with self.assertRaises((ValueError, FileExistsError)):
            self.m.resume(batch, 'favorites')
        self.assertFalse(self.m.verify(batch, 'favorites')['cleanup_ready'])

    def test_malformed_manifest_fails_closed(self):
        for value in ([], None, {"version": 1, "kind": "favorites", "items": []}):
            result = self.archive(); batch = Path(result['batch'])
            (batch/'archive.json').write_text(json.dumps(value))
            check = self.m.verify(batch, 'favorites')
            self.assertFalse(check['cleanup_ready'])
            self.assertEqual(check['verified_ids'], [])

    def test_write_failure_preserves_batch_and_returns_no_cleanup_targets(self):
        original = self.m.atomic_write
        def fail_summary(batch, relative, text):
            if relative == 'summary.md':
                raise OSError('disk full')
            return original(batch, relative, text)
        with patch.object(self.m, 'atomic_write', side_effect=fail_summary):
            result = self.archive()
        self.assertFalse(result['cleanup_ready'])
        self.assertEqual(result['verified_ids'], [])
        self.assertTrue((Path(result['batch'])/'archive.json').exists())
        self.assertTrue(self.m.resume(Path(result['batch']), 'favorites')['cleanup_ready'])

    def test_download_uses_tls_fallback_only_for_exact_host_and_tls_error(self):
        # Network boundary is mocked; argument construction and fallback decisions are real.
        spec = importlib.util.spec_from_file_location('network_archive', SCRIPTS[0])
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        destination = Path(self.tmp.name)/'image temporary'
        calls = []
        def run(args, **kwargs):
            calls.append(args)
            if len(calls) == 1:
                return subprocess.CompletedProcess(args, 60, '', 'TLS')
            destination.write_bytes(PNG)
            return subprocess.CompletedProcess(args, 0, '', '')
        with patch.object(module.subprocess, 'run', side_effect=run):
            actual = module.download('https://i0.hdslb.com/a/b.png?x=1&y=2', destination)
        self.assertEqual(actual, 'https://i1.hdslb.com/a/b.png?x=1&y=2')
        self.assertEqual(destination.read_bytes(), PNG)
        self.assertEqual(calls[0][-2:], [str(destination), 'https://i0.hdslb.com/a/b.png?x=1&y=2'])
        for host, code in [('i0.hdslb.com', 22), ('i0.hdslb.com.evil.test', 60)]:
            attempts = []
            def fail(args, **kwargs):
                attempts.append(args)
                return subprocess.CompletedProcess(args, code, '', 'failure')
            with patch.object(module.subprocess, 'run', side_effect=fail), self.assertRaises(ValueError):
                module.download('https://' + host + '/x', destination)
            self.assertEqual(len(attempts), 1)

    def test_copies_are_standalone_and_cli_errors_are_json(self):
        self.assertEqual(SCRIPTS[0].read_bytes(), SCRIPTS[1].read_bytes())
        for script in SCRIPTS:
            result = subprocess.run(['python3', str(script), 'verify', '--batch', '/nonexistent'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(json.loads(result.stdout)['cleanup_ready'])


class LocalHttpIntegrationTests(unittest.TestCase):
    def test_standalone_cli_downloads_and_verifies_over_real_http(self):
        requests = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests.append(self.path)
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.end_headers()
                self.wfile.write(PNG)
            def log_message(self, *args):
                pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'Downloads').mkdir()
            env = dict(os.environ, NO_PROXY='127.0.0.1', no_proxy='127.0.0.1')
            for kind, count in [('favorites', 1), ('following', 24)]:
                standalone = root/f'archiving-bilibili-{kind}'/'scripts'
                standalone.mkdir(parents=True)
                script = standalone/'archive_bilibili.py'
                script.write_bytes(SCRIPTS[0].read_bytes())
                prefix = 'https://www.bilibili.com/video/' if kind == 'favorites' else 'https://space.bilibili.com/'
                ids = ['BV0000000001'] if kind == 'favorites' else [str(i) for i in range(1, 25)]
                payload = dict(source_url='https://www.bilibili.com/', end_confirmed=True,
                               items=[dict(id=i, canonical_url=prefix+i, display_name='中文名字',
                                           image_source_url=f'http://127.0.0.1:{server.server_port}/image.jpg?range=[1-2]') for i in ids])
                source = root/'input.json'; source.write_text(json.dumps(payload))
                def cli(*args):
                    bootstrap = ('import importlib.util,sys; from pathlib import Path; '
                                 's=importlib.util.spec_from_file_location("archive",sys.argv[1]); '
                                 'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
                                 'm.DOWNLOADS=Path(sys.argv[2]); sys.argv=[sys.argv[1],*sys.argv[3:]]; '
                                 'raise SystemExit(m.main())')
                    result = subprocess.run(['python3', '-c', bootstrap, str(script), str(root/'Downloads'), *args],
                                            env=env, capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    return json.loads(result.stdout)
                self.assertTrue(cli('preflight')['ready'])
                result = cli('archive', '--input', str(source))
                self.assertEqual(result['verified_ids'], ids)
                self.assertTrue(cli('verify', '--batch', result['batch'])['cleanup_ready'])
                batch = Path(result['batch'])
                manifest = json.loads((batch/'archive.json').read_text())
                self.assertEqual(manifest['items'][0]['tags'], ['Bilibili', 'Bilibili '+kind.title()])
                stem = 'cover' if kind == 'favorites' else 'avatar'
                self.assertEqual((batch/ids[0]/(stem+'.png')).read_bytes(), PNG)
            self.assertEqual(len(requests), 25)
            self.assertTrue(all(url == '/image.jpg?range=[1-2]' for url in requests))


if __name__ == '__main__':
    unittest.main()
