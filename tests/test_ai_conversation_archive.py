from __future__ import annotations

import concurrent.futures
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/conversation/archiving-ai-conversation/scripts/archive_conversation.py'


def payload():
    return {'title': '修复链接', 'messages': [
        {'role': 'user', 'content': '请修复。'},
        {'role': 'assistant', 'content': '# 结果\n已修复。\n```md\n## 示例\n```'}],
        'retrospective': {key: '已核对。' for key in
                          ['背景', '处理过程', '结果', '决策', '经验教训', '疑难问题', '后续事项']}}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.exists(), 'archive writer has not been implemented')
        spec = importlib.util.spec_from_file_location('archive_conversation', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.temp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self.temp.cleanup)
        self.downloads = Path(self.temp.name)

    def save(self, data=None):
        return self.module.archive(data or payload(), self.downloads, '2026-09-07')

    def test_pair_has_correct_names_content_and_encoded_link(self):
        result = self.save()
        transcript = Path(result['transcript'])
        retrospective = Path(result['retrospective'])
        self.assertTrue(result['verified'])
        self.assertEqual(transcript.parent.name, '2026-09-07 Archived AI Conversations')
        self.assertEqual(transcript.name, '2026-09-07 修复链接（AI 对话原文）.md')
        self.assertIn('## 用户\n\n请修复。', transcript.read_text())
        self.assertIn('### 结果\n\n已修复。', transcript.read_text())
        self.assertIn('```md\n## 示例\n```', transcript.read_text())
        self.assertIn('## 原文记录\n\n[原文](' + quote(transcript.name) + ')', retrospective.read_text())

    def test_collision_in_either_filename_preserves_existing_pair(self):
        first = self.save()
        old = Path(first['retrospective']).read_bytes()
        Path(first['transcript']).unlink()
        second = self.save()
        self.assertIn('修复链接 2（', Path(second['transcript']).name)
        self.assertIn('修复链接 2（', Path(second['retrospective']).name)
        self.assertEqual(Path(first['retrospective']).read_bytes(), old)

    def test_concurrent_runs_keep_distinct_complete_pairs(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.save(), range(8)))
        self.assertEqual(len({r['transcript'] for r in results}), 8)
        self.assertTrue(all(Path(r['retrospective']).is_file() for r in results))

    def test_invalid_input_creates_no_archive(self):
        cases = []
        for field, value in [('title', '../escape'), ('title', 'x' * 200),
                             ('messages', []), ('retrospective', {})]:
            data = payload(); data[field] = value; cases.append(data)
        data = payload(); data['messages'][0]['role'] = 'tool'; cases.append(data)
        data = payload(); data['messages'][0]['role'] = []; cases.append(data)
        data = payload(); data['messages'][0]['content'] = '```\nunclosed'; cases.append(data)
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                self.save(data)
        self.assertEqual(list(self.downloads.iterdir()), [])

    def sop_payload(self):
        data = payload()
        data['sops'] = [{'title': name, 'sections': {
            '目的与适用场景': '核对归档。', '前置条件与输入': '已有文件。',
            '标准步骤或格式': '1. 读取文件。\n2. 核对内容。',
            '输出与验收标准': '内容一致。', '异常处理与适用边界': '失败则保留现场。'
        }} for name in ['文件校验', '报告格式']]
        return data

    def test_each_sop_has_own_file_and_bidirectional_links(self):
        result = self.save(self.sop_payload())
        self.assertEqual(len(result.get('sops', [])), 2)
        summary = Path(result['retrospective']).read_text()
        for name, filename in zip(['文件校验', '报告格式'], result['sops']):
            path = Path(filename)
            self.assertEqual(path.name, f'2026-09-07 {name}（SOP）.md')
            self.assertIn(quote(path.name, safe=''), summary)
            self.assertIn(quote(Path(result['transcript']).name, safe=''), path.read_text())
            self.assertIn('## 输出与验收标准', path.read_text())
        self.assertEqual(len(list(self.downloads.rglob('*.md'))), 4)

    def test_no_sops_reports_empty_list_and_reason(self):
        result = self.save()
        self.assertEqual(result.get('sops'), [])
        self.assertIn('未发现可提炼的标准流程或标准格式', Path(result['retrospective']).read_text())

    def test_duplicate_sop_titles_and_repeated_runs_do_not_overwrite(self):
        data = self.sop_payload()
        data['sops'][1]['title'] = data['sops'][0]['title']
        first = self.save(data)
        before = {p: Path(p).read_bytes() for p in first.get('sops', [])}
        second = self.save(data)
        paths = first.get('sops', []) + second.get('sops', [])
        self.assertEqual(len(set(paths)), 4)
        for path, content in before.items():
            self.assertEqual(Path(path).read_bytes(), content)

    def test_concurrent_sop_runs_keep_complete_distinct_sets(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.save(self.sop_payload()), range(8)))
        paths = [path for result in results for path in result['sops']]
        self.assertEqual(len(set(paths)), 16)
        self.assertTrue(all(Path(path).is_file() for path in paths))
        self.assertEqual(len(list(self.downloads.rglob('*.md'))), 32)

    def test_invalid_sops_rejected_before_writing(self):
        for value in [None, {}, [1], [{'title': '../bad', 'sections': {}}],
                      [{'title': '步骤', 'sections': {}}]]:
            data = payload(); data['sops'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.save(data)
        self.assertEqual(list(self.downloads.iterdir()), [])

    def test_sop_write_or_readback_failure_reports_all_paths(self):
        original = self.module.write_exclusive
        for corrupt in [False, True]:
            def fail_sop(path, text):
                if '（SOP）' in path.name:
                    if not corrupt:
                        raise OSError('SOP disk full')
                    text += 'corruption'
                original(path, text)
            with patch.object(self.module, 'write_exclusive', side_effect=fail_sop):
                with self.assertRaises(self.module.ArchiveError) as caught:
                    self.save(self.sop_payload())
            self.assertEqual(len(caught.exception.paths['sops']), 2)
            self.assertTrue(Path(caught.exception.paths['transcript']).is_file())

    def artifact(self, name='report.pdf', content=b'%PDF-test\x00\xff'):
        source = self.downloads / name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(content)
        return source

    def test_untracked_artifact_is_copied_and_manifest_links_verified(self):
        import hashlib
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        result = self.save(data)
        self.assertEqual(len(result.get('artifacts', [])), 1)
        entry = result['artifacts'][0]
        destination = Path(entry['path'])
        self.assertEqual(destination.read_bytes(), source.read_bytes())
        self.assertEqual(destination.parent, Path(result['directory']))
        self.assertEqual(entry['sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertEqual(entry['size'], len(source.read_bytes()))
        manifest = json.loads(Path(result['artifact_manifest']).read_text())
        self.assertEqual(manifest['artifacts'], result['artifacts'])
        self.assertIn(quote(destination.name, safe=''), Path(result['retrospective']).read_text())

    def test_git_tracked_is_skipped_but_ignored_and_untracked_are_copied(self):
        repo = self.downloads / 'repo'; repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        (repo / '.gitignore').write_text('ignored.pdf\n')
        for name in ['tracked.pdf', 'ignored.pdf', 'new.pdf']:
            (repo / name).write_bytes(name.encode())
        subprocess.run(['git', '-C', str(repo), 'add', 'tracked.pdf', '.gitignore'], check=True)
        data = payload(); data['artifacts'] = [str(repo / n) for n in ['tracked.pdf', 'ignored.pdf', 'new.pdf']]
        result = self.save(data)
        self.assertEqual(len(result.get('artifacts', [])), 2)
        self.assertEqual([x['source'] for x in result['skipped_artifacts']], [str(repo / 'tracked.pdf')])
        self.assertEqual({Path(x['path']).read_bytes() for x in result['artifacts']}, {b'ignored.pdf', b'new.pdf'})

    def test_non_repository_artifact_is_copied(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'outside.txt'; source.write_text('outside')
            data = payload(); data['artifacts'] = [str(source)]
            result = self.save(data)
            self.assertEqual(len(result.get('artifacts', [])), 1)
            self.assertEqual(Path(result['artifacts'][0]['path']).read_text(), 'outside')

    def test_same_basename_duplicate_inputs_and_repeated_runs_preserve_files(self):
        first = self.artifact('a/report.pdf', b'first')
        second = self.artifact('b/report.pdf', b'second')
        data = payload(); data['artifacts'] = [str(first), str(second), str(first)]
        one = self.save(data); two = self.save(data)
        self.assertEqual(len(one.get('artifacts', [])), 2)
        paths = [x['path'] for r in [one, two] for x in r['artifacts']]
        self.assertEqual(len(set(paths)), 4)
        self.assertEqual([Path(p).read_bytes() for p in paths], [b'first', b'second', b'first', b'second'])
        self.assertEqual(first.read_bytes(), b'first')
        self.assertNotEqual(one['artifact_manifest'], two['artifact_manifest'])

    def test_invalid_or_missing_artifact_fails_before_archive_write(self):
        link = self.downloads / 'link'; link.symlink_to(self.artifact())
        for values in [None, {}, ['relative.txt'], [str(self.downloads / 'missing')],
                       [str(self.downloads)], [str(link)], [123]]:
            data = payload(); data['artifacts'] = values
            with self.subTest(values=values), self.assertRaises((ValueError, OSError)):
                self.save(data)
        self.assertFalse((self.downloads / '2026-09-07 Archived AI Conversations').exists())

    def test_artifact_copy_failure_preserves_markdown_and_reports_paths(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        with patch.object(self.module, 'copy_artifact', side_effect=OSError('copy failed'), create=True):
            with self.assertRaises(self.module.ArchiveError) as caught:
                self.save(data)
        self.assertTrue(Path(caught.exception.paths['transcript']).is_file())
        self.assertEqual(len(caught.exception.paths['artifacts']), 1)
        self.assertTrue(source.is_file())

    def test_artifact_readback_corruption_fails_verification(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        def corrupt(src, dest):
            dest.write_bytes(b'corrupt')
        with patch.object(self.module, 'copy_artifact', side_effect=corrupt, create=True):
            with self.assertRaises(self.module.ArchiveError):
                self.save(data)
        self.assertTrue(source.is_file())

    def test_archive_skill_sops_are_excluded_but_unrelated_sops_remain(self):
        data = self.sop_payload()
        data['sops'][0]['scope'] = 'archiving-ai-conversation'
        data['sops'][1]['scope'] = 'general'
        result = self.save(data)
        self.assertEqual(len(result['sops']), 1)
        self.assertIn('报告格式', Path(result['sops'][0]).name)
        self.assertEqual(result['skipped_sops'], ['文件校验'])
        self.assertIn('归档技能自身', Path(result['retrospective']).read_text())

    def test_only_archive_skill_sops_produce_no_sop_file(self):
        data = self.sop_payload()
        for item in data['sops']:
            item['scope'] = 'archiving-ai-conversation'
        result = self.save(data)
        self.assertEqual(result['sops'], [])
        self.assertIn('归档技能自身', Path(result['retrospective']).read_text())

    def test_invalid_sop_scope_is_not_silently_accepted(self):
        data = self.sop_payload(); data['sops'][0]['scope'] = 'typo'
        with self.assertRaises(ValueError):
            self.save(data)

    def test_excluded_sop_needs_no_sections(self):
        data = payload()
        data['sops'] = [{'title': '归档技能维护', 'scope': 'archiving-ai-conversation'}]
        result = self.save(data)
        self.assertEqual(result['sops'], [])
        self.assertEqual(result['skipped_sops'], ['归档技能维护'])

    def test_concurrent_artifact_runs_do_not_overwrite(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: self.save(data), range(4)))
        self.assertEqual(len({r['artifacts'][0]['path'] for r in results}), 4)
        for result in results:
            self.assertEqual(Path(result['artifacts'][0]['path']).read_bytes(), source.read_bytes())
            self.assertTrue(Path(result['artifact_manifest']).is_file())

    def test_git_failure_does_not_guess_untracked(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        failure = subprocess.CompletedProcess(['git'], 128, b'', b'fatal: detected dubious ownership')
        with patch.object(self.module.subprocess, 'run', return_value=failure):
            with self.assertRaises(OSError):
                self.save(data)
        self.assertFalse((self.downloads / '2026-09-07 Archived AI Conversations').exists())

    def test_source_change_during_copy_fails_verification(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        original = self.module.copy_artifact
        def mutate(src, dst):
            original(src, dst)
            src.write_bytes(b'changed')
        with patch.object(self.module, 'copy_artifact', side_effect=mutate):
            with self.assertRaises(self.module.ArchiveError):
                self.save(data)

    def test_manifest_readback_failure_is_not_success(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        original = self.module.write_exclusive
        def corrupt(path, content):
            original(path, content + ('corrupt' if path.suffix == '.json' else ''))
        with patch.object(self.module, 'write_exclusive', side_effect=corrupt):
            with self.assertRaises(self.module.ArchiveError) as caught:
                self.save(data)
        self.assertTrue(Path(caught.exception.paths['artifacts'][0]['path']).is_file())

    def test_git_literal_filename_is_not_a_pattern(self):
        repo = self.downloads / 'literal'; repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        (repo / 'a.txt').write_text('tracked')
        subprocess.run(['git', '-C', str(repo), 'add', 'a.txt'], check=True)
        source = repo / '[a].txt'; source.write_text('untracked')
        data = payload(); data['artifacts'] = [str(source)]
        result = self.save(data)
        self.assertEqual(len(result['artifacts']), 1)
        self.assertEqual(result['skipped_artifacts'], [])

    def test_cli_copies_artifact_and_excludes_archive_skill_sop(self):
        source = self.artifact()
        data = payload(); data['artifacts'] = [str(source)]
        data['sops'] = [{'title': '归档维护', 'scope': 'archiving-ai-conversation'}]
        process = subprocess.run([sys.executable, '-B', str(SCRIPT), 'save',
                                  '--downloads-dir', str(self.downloads)],
                                 input=json.dumps(data), text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        result = json.loads(process.stdout)
        self.assertTrue(result['verified'])
        self.assertEqual(Path(result['artifacts'][0]['path']).read_bytes(), source.read_bytes())
        self.assertEqual(result['sops'], [])
        self.assertEqual(result['skipped_sops'], ['归档维护'])

    def test_tracked_file_in_current_linked_worktree_is_skipped(self):
        data = payload(); data['artifacts'] = [str(SCRIPT)]
        result = self.save(data)
        self.assertEqual(result['artifacts'], [])
        self.assertEqual(result['skipped_artifacts'][0]['source'], str(SCRIPT.resolve()))
        self.assertEqual(Path(result['skipped_artifacts'][0]['repository']), ROOT.resolve())
        self.assertTrue(Path(result['artifact_manifest']).is_file())

    def test_missing_downloads_is_not_silently_created(self):
        with self.assertRaises(OSError):
            self.module.archive(payload(), self.downloads / 'missing', '2026-09-07')
        self.assertEqual(list(self.downloads.iterdir()), [])

    def test_daily_symlink_cannot_redirect_output(self):
        elsewhere = self.downloads / 'elsewhere'
        elsewhere.mkdir()
        (self.downloads / '2026-09-07 Archived AI Conversations').symlink_to(elsewhere)
        with self.assertRaises(OSError):
            self.save()
        self.assertEqual(list(elsewhere.iterdir()), [])

    def test_second_write_failure_keeps_transcript_and_reports_paths(self):
        original = self.module.write_exclusive
        def fail_second(path, text):
            if '（AI 对话归档）' in path.name:
                raise OSError('disk full')
            original(path, text)
        with patch.object(self.module, 'write_exclusive', side_effect=fail_second):
            with self.assertRaises(self.module.ArchiveError) as caught:
                self.save()
        self.assertTrue(Path(caught.exception.paths['transcript']).is_file())
        self.assertIn('disk full', str(caught.exception))

    def test_readback_mismatch_does_not_report_success(self):
        original = self.module.write_exclusive
        def corrupt(path, text):
            original(path, text + 'corruption')
        with patch.object(self.module, 'write_exclusive', side_effect=corrupt):
            with self.assertRaises(self.module.ArchiveError):
                self.save()
        self.assertEqual(len(list(self.downloads.rglob('*.md'))), 2)

    def test_cli_accepts_stdin_and_returns_json(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'save', '--downloads-dir', str(self.downloads)],
                                input=json.dumps(payload()), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['verified'])
        bad = subprocess.run([sys.executable, str(SCRIPT), 'save', '--downloads-dir', str(self.downloads)],
                             input='{}', text=True, capture_output=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertFalse(json.loads(bad.stdout)['verified'])

    def test_preflight_probes_access_without_leaving_files(self):
        result = subprocess.run([sys.executable, str(SCRIPT), 'preflight', '--downloads-dir', str(self.downloads)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)['writable'])
        self.assertEqual(list(self.downloads.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
