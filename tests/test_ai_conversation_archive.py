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
