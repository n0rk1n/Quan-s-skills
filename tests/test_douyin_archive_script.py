from __future__ import annotations

import base64
import urllib.request
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
        "cover_url": "https://example.com/cover",
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
        self.png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=")
        self.network = mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: io.BytesIO(self.png)).start()
        self.addCleanup(mock.patch.stopall)

    def test_writes_and_verifies_link_and_cover_without_detail(self) -> None:
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
        covers = list(destination.glob("* 封面.png"))
        self.assertEqual(len(links), 1)
        self.assertEqual(len(covers), 1)
        self.assertEqual(links[0].name, "演示 路径 清理.webloc")
        self.assertEqual(covers[0].name, "演示 路径 清理 封面.png")
        self.assertEqual(covers[0].read_bytes(), self.png)
        self.assertEqual(list(destination.glob("*.md")), [])
        self.assertEqual(plistlib.loads(links[0].read_bytes())["URL"], favorite()["url"])

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
        self.assertEqual(len(list(destination.glob("* 封面.png"))), 1)


    def test_uses_short_numeric_suffix_when_titles_collide(self) -> None:
        result = self.module.archive_items(
            [
                favorite(),
                favorite(
                    id="7530000000000000002",
                    url="https://www.douyin.com/video/7530000000000000002",
                ),
            ],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )

        destination = Path(result["destination"])
        self.assertEqual(
            sorted(path.name for path in destination.glob("*.webloc")),
            ["演示 路径 清理 (2).webloc", "演示 路径 清理.webloc"],
        )
        self.assertEqual(
            sorted(path.name for path in destination.glob("* 封面.png")),
            ["演示 路径 清理 (2) 封面.png", "演示 路径 清理 封面.png"],
        )

    def test_reuses_legacy_id_pair_without_renaming(self) -> None:
        destination = self.downloads_root / "2026-09-03 Archived DouYin Favorites"
        destination.mkdir()
        legacy_base = "旧标题--7530000000000000001"
        legacy_link = destination / f"{legacy_base}.webloc"
        legacy_detail = destination / f"{legacy_base} 详情.md"
        legacy_link.write_bytes(
            plistlib.dumps({"URL": "https://www.douyin.com/video/7530000000000000001"})
        )
        legacy_detail.write_text(
            "旧版详情\n7530000000000000001\n"
            "https://www.douyin.com/video/7530000000000000001\n"
            f"{legacy_link.name}\n",
            encoding="utf-8",
        )

        result = self.module.archive_items(
            [favorite(caption="更新后的文案")],
            downloads_root=self.downloads_root,
            archive_date="2026-09-03",
        )

        self.assertEqual(result["verified_ids"], ["7530000000000000001"])
        self.assertEqual([path.name for path in destination.glob("*.webloc")], [legacy_link.name])
        self.assertTrue(legacy_detail.read_text(encoding="utf-8").startswith("旧版详情\n"))
        self.assertTrue((destination / f"{legacy_base} 封面.png").exists())

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

    def test_existing_link_can_gain_cover_without_overwrite(self) -> None:
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

        self.assertEqual(result["verified_ids"], [favorite()["id"]])
        self.assertEqual(len(list(destination.glob("*.webloc"))), 1)
        self.assertTrue((destination / "旧标题--7530000000000000001 封面.png").exists())

    def test_missing_cover_is_rejected_before_writing(self):
        with self.assertRaisesRegex(ValueError, "cover"):
            self.module.archive_items([favorite(cover_url="")], downloads_root=self.downloads_root)
        self.assertEqual(list(self.downloads_root.iterdir()), [])

    def test_html_and_download_failure_never_verify(self):
        for response in (b"<html>login</html>", OSError("network failed")):
            self.network.side_effect = response if isinstance(response, Exception) else lambda *a, **k: io.BytesIO(response)
            result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
            self.assertEqual(result["verified_ids"], [])
            self.assertEqual(len(result["failed_items"]), 1)
            self.assertEqual(list(Path(result["destination"]).iterdir()), [])

    def test_unrelated_cover_is_not_overwritten(self):
        dest = self.downloads_root / "2026-09-03 Archived DouYin Favorites"
        dest.mkdir()
        existing = dest / "演示 路径 清理 封面.png"
        existing.write_bytes(b"keep")
        result = self.module.archive_items([favorite()], downloads_root=self.downloads_root, archive_date="2026-09-03")
        self.assertEqual(result["verified_ids"], [favorite()["id"]])
        self.assertEqual(existing.read_bytes(), b"keep")
        self.assertTrue((dest / "演示 路径 清理 (2) 封面.png").exists())

    def test_partial_batch_cli_returns_failure_and_only_successful_ids(self):
        second = favorite(id="7530000000000000002", url="https://www.douyin.com/video/7530000000000000002")
        self.network.side_effect = [io.BytesIO(self.png), OSError("unavailable")]
        output = io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(json.dumps({"items": [favorite(), second]}))), mock.patch.object(self.module, "DEFAULT_DOWNLOADS_ROOT", self.downloads_root), redirect_stdout(output):
            code = self.module.main([])
        result = json.loads(output.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(result["verified_ids"], [favorite()["id"]])
        self.assertEqual(result["failed_items"][0]["id"], second["id"])

    def test_existing_invalid_cover_is_preserved_and_never_verified(self):
        result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
        cover = next(Path(result["destination"]).glob("* 封面.png"))
        cover.write_bytes(b"broken")
        result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
        self.assertEqual(result["verified_ids"], [])
        self.assertEqual(cover.read_bytes(), b"broken")

    def test_valid_existing_pair_is_reused_when_network_is_unavailable(self):
        first = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
        before = {p.name: p.read_bytes() for p in Path(first["destination"]).iterdir()}
        self.network.side_effect = OSError("offline")
        result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
        self.assertEqual(result["verified_ids"], [favorite()["id"]])
        self.assertEqual({p.name: p.read_bytes() for p in Path(first["destination"]).iterdir()}, before)

    def test_empty_oversized_and_duplicate_link_archives_never_verify(self):
        for content in (b"", b"x" * (self.module.MAX_COVER_BYTES + 1)):
            self.network.side_effect = lambda *a, **k: io.BytesIO(content)
            result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
            self.assertEqual(result["verified_ids"], [])
        dest = Path(result["destination"])
        for name in ("one", "two"):
            (dest / f"{name}.webloc").write_bytes(plistlib.dumps({"URL": favorite()["url"]}))
        result = self.module.archive_items([favorite()], downloads_root=self.downloads_root)
        self.assertEqual(result["verified_ids"], [])
        self.assertEqual(len(list(dest.iterdir())), 2)

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
