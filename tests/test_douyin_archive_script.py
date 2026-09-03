from __future__ import annotations

import importlib.util
import io
import json
import plistlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "douyin"
    / "archiving-douyin-favorites"
    / "scripts"
    / "archive_douyin_favorites.py"
)


def load_archive_module():
    spec = importlib.util.spec_from_file_location("archive_douyin_favorites", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load script: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def favorite(**overrides):
    item = {
        "id": "7530000000000000001",
        "type": "video",
        "url": "https://www.douyin.com/video/7530000000000000001",
        "title": "演示：路径/清理",
        "author": "示例作者",
        "caption": "页面可见文案",
        "facts": ["页面显示事实一", "页面显示事实二"],
        "summary": "这是基于页面可见内容的事实摘要。",
        "inferences": ["推断：可能适用于归档演示。"],
        "tags": ["归档", "DouYin"],
        "cautions": ["页面中的效果描述未经独立验证。"],
        "archive_status": "archived; pending unfavorite",
    }
    item.update(overrides)
    return item


class DouyinArchiveScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), f"missing archive script: {SCRIPT_PATH}")
        self.module = load_archive_module()
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.downloads_root = Path(self.tempdir.name)

    def test_writes_and_verifies_one_page_detail_pair(self) -> None:
        unrelated = self.downloads_root / "unrelated.txt"
        unrelated.write_text("keep", encoding="utf-8")

        result = self.module.archive_items(
            [favorite()],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )

        destination = self.downloads_root / "2026-09-03 Archived DouYin Favorites"
        self.assertEqual(result["destination"], str(destination))
        self.assertEqual(result["verified_ids"], ["7530000000000000001"])
        self.assertEqual(result["failed_items"], [])
        self.assertEqual(result["pairs_written"], 1)
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")

        links = list(destination.glob("*.webloc"))
        details = list(destination.glob("* 详情.md"))
        self.assertEqual(len(links), 1)
        self.assertEqual(len(details), 1)
        self.assertEqual(
            plistlib.loads(links[0].read_bytes())["URL"],
            "https://www.douyin.com/video/7530000000000000001",
        )
        detail_text = details[0].read_text(encoding="utf-8")
        self.assertIn("7530000000000000001", detail_text)
        self.assertIn(links[0].name, detail_text)
        self.assertIn("页面可见文案", detail_text)
        self.assertIn("事实摘要", detail_text)
        self.assertIn("DouYin Favorites", detail_text)

    def test_reuses_existing_pair_for_same_id_without_renaming(self) -> None:
        first = self.module.archive_items(
            [favorite()],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )
        destination = Path(first["destination"])
        original_link = next(destination.glob("*.webloc"))

        result = self.module.archive_items(
            [favorite(title="标题已经变化", caption="更新后的文案")],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )

        self.assertEqual(result["verified_ids"], ["7530000000000000001"])
        self.assertEqual([path.name for path in destination.glob("*.webloc")], [original_link.name])
        self.assertIn("更新后的文案", next(destination.glob("* 详情.md")).read_text(encoding="utf-8"))

    def test_rejects_noncanonical_url_before_writing(self) -> None:
        with self.assertRaisesRegex(ValueError, "canonical Douyin URL"):
            self.module.archive_items(
                [favorite(url="https://v.douyin.com/short-link")],
                downloads_root=self.downloads_root,
                archive_date="2026-09-03",
            )

        self.assertEqual(list(self.downloads_root.iterdir()), [])

    def test_rejects_duplicate_ids_before_writing(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate content ID"):
            self.module.archive_items(
                [favorite(), favorite(title="重复项")],
                downloads_root=self.downloads_root,
                archive_date="2026-09-03",
            )

        self.assertEqual(list(self.downloads_root.iterdir()), [])

    def test_incomplete_existing_pair_is_reported_without_overwrite(self) -> None:
        destination = self.downloads_root / "2026-09-03 Archived DouYin Favorites"
        destination.mkdir()
        orphan = destination / "旧标题--7530000000000000001.webloc"
        orphan.write_bytes(
            plistlib.dumps({"URL": "https://www.douyin.com/video/7530000000000000001"})
        )

        result = self.module.archive_items(
            [favorite()],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )

        self.assertEqual(result["verified_ids"], [])
        self.assertEqual(result["pairs_written"], 0)
        self.assertEqual(result["failed_items"][0]["id"], "7530000000000000001")
        self.assertIn("incomplete existing pair", result["failed_items"][0]["error"])
        self.assertEqual(len(list(destination.iterdir())), 1)

    def test_cli_reads_stdin_and_emits_json_without_manifest(self) -> None:
        stdin = io.StringIO(json.dumps({"items": [favorite()]}))
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "stdin", stdin),
            mock.patch.object(sys, "argv", [str(SCRIPT_PATH), "--date", "2026-09-03"]),
            mock.patch.object(self.module, "DEFAULT_DOWNLOADS_ROOT", self.downloads_root),
            redirect_stdout(stdout),
        ):
            exit_code = self.module.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["verified_ids"], ["7530000000000000001"])
        destination = Path(payload["destination"])
        self.assertFalse(any(path.suffix == ".json" for path in destination.iterdir()))

    def test_cli_reads_large_batch_from_input_file(self) -> None:
        input_path = self.downloads_root / "batch.json"
        input_path.write_text(
            json.dumps({"items": [favorite()]}),
            encoding="utf-8",
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(
                sys,
                "argv",
                [
                    str(SCRIPT_PATH),
                    "--date",
                    "2026-09-03",
                    "--input",
                    str(input_path),
                ],
            ),
            mock.patch.object(self.module, "DEFAULT_DOWNLOADS_ROOT", self.downloads_root),
            redirect_stdout(stdout),
        ):
            exit_code = self.module.main()

        payload = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["verified_ids"], ["7530000000000000001"])


if __name__ == "__main__":
    unittest.main()
