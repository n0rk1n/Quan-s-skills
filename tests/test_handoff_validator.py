from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = (
    ROOT
    / "creating-conversation-handoffs"
    / "scripts"
    / "validate_handoff.py"
)
SOURCE_UUID = "11111111-1111-4111-8111-111111111111"
SOURCE_REFERENCE = "opencode:session-2026-07-31"


def valid_snapshot(
    source_reference: str = SOURCE_REFERENCE,
    source_key: str = "旧会话来源",
) -> str:
    return textwrap.dedent(
        f"""\
        # 对话交接：handoff-validator

        ## 元数据

        - Schema 版本：1
        - 生成时间：2026-07-30T10:30:00+08:00
        - 任务摘要：验证交接文件
        - {source_key}：{source_reference}
        - 项目或 worktree 根目录：/private/tmp/handoff-project
        - 上一个快照：不适用

        ## 续接摘要

        验证器测试先于实现。

        ## 用户目标与验收标准

        - 校验合法快照。

        ## 必须了解的背景

        - 只使用 Python 标准库。

        ## 相对上次交接的变化

        不适用：这是首个交接快照。

        ## 事实与证据

        | 状态 | 事实 | 证据 |
        | --- | --- | --- |
        | 已验证 | 测试目录可写 | TemporaryDirectory |
        | 用户确认 | 使用固定结构 | 已批准设计 |
        | 待核实 | 宿主能否回查旧对话 | 执行时复核 |

        ## 已完成事项

        - 已写入失败测试；尚未实现脚本。

        ## 当前工作区状态

        - 当前分支：codex/creating-conversation-handoffs-design

        ## 决策与理由

        - 使用 Markdown 契约，保持跨宿主可读。

        ## 失败尝试与避坑点

        - 不适用。

        ## 未完成事项与下一步

        **首个可执行步骤：** 创建校验器脚本。

        ## 阻塞项与待确认问题

        - 无。

        ## 关键文件、命令与外部资源

        - `creating-conversation-handoffs/scripts/validate_handoff.py`

        ## 来源信息与回查

        - 旧会话来源：{source_reference}

        ## 新对话续接指令

        复核易变化事实，不重复已完成事项，然后执行首个可执行步骤。
        """
    )


def latest_text(snapshot_name: str) -> str:
    return textwrap.dedent(
        f"""\
        # 最新对话交接

        - 最新快照：[handoff-validator]({snapshot_name})
        - 生成时间：2026-07-30T10:30:00+08:00
        - 旧会话来源：{SOURCE_REFERENCE}
        - 任务摘要：验证交接文件
        """
    )


class HandoffValidatorCliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_snapshot_error(
        self,
        name: str,
        content: str,
        code: str,
    ) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / name
            path.write_text(content, encoding="utf-8")

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(1, completed.returncode, completed.stdout)
            self.assertIn(f"ERROR {code}:", completed.stderr)

    def test_valid_snapshot_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "2026-07-30-1030-validator.md"
            path.write_text(valid_snapshot(), encoding="utf-8")

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("PASS", completed.stdout)

    def test_unavailable_source_reference_with_reason_passes(self) -> None:
        content = valid_snapshot("不可用：当前宿主未提供会话标识")
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "2026-07-30-1030-validator.md"
            path.write_text(content, encoding="utf-8")

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_host_qualified_source_reference_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "2026-07-30-1030-validator.md"
            path.write_text(valid_snapshot(), encoding="utf-8")

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_legacy_uuid_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "2026-07-30-1030-validator.md"
            path.write_text(
                valid_snapshot(SOURCE_UUID, "旧对话 UUID"),
                encoding="utf-8",
            )

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_invalid_snapshot_name_fails(self) -> None:
        self.assert_snapshot_error(
            "handoff.md",
            valid_snapshot(),
            "invalid-snapshot-name",
        )

    def test_missing_section_fails(self) -> None:
        content = valid_snapshot().replace(
            "## 决策与理由",
            "## 决策记录",
        )
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "missing-section",
        )

    def test_wrong_section_order_fails(self) -> None:
        content = valid_snapshot().replace(
            "## 用户目标与验收标准",
            "## 临时章节",
            1,
        ).replace(
            "## 必须了解的背景",
            "## 用户目标与验收标准",
            1,
        ).replace(
            "## 临时章节",
            "## 必须了解的背景",
            1,
        )
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "section-order",
        )

    def test_invalid_fact_status_fails(self) -> None:
        content = valid_snapshot().replace("| 待核实 |", "| 推断 |")
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "invalid-fact-status",
        )

    def test_missing_first_step_fails(self) -> None:
        content = valid_snapshot().replace(
            "**首个可执行步骤：**",
            "**下一步：**",
        )
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "missing-first-step",
        )

    def test_invalid_uuid_fails(self) -> None:
        content = valid_snapshot("made-up-id")
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "invalid-source-reference",
        )

    def test_unresolved_template_token_fails(self) -> None:
        content = valid_snapshot().replace(
            "验证交接文件",
            "{{task_summary}}",
            1,
        )
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "unresolved-template-token",
        )

    def test_possible_secret_fails(self) -> None:
        content = valid_snapshot().replace(
            "- 无。",
            "- api_token: sk-test-secret-value",
            1,
        )
        self.assert_snapshot_error(
            "2026-07-30-1030-validator.md",
            content,
            "possible-secret",
        )

    def test_valid_latest_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            snapshot = directory / "2026-07-30-1030-validator.md"
            snapshot.write_text(valid_snapshot(), encoding="utf-8")
            latest = directory / "LATEST.md"
            latest.write_text(latest_text(snapshot.name), encoding="utf-8")

            completed = self.run_cli("latest", str(latest))

            self.assertEqual(0, completed.returncode, completed.stderr)

    def test_unsafe_latest_targets_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw) / "handoffs"
            directory.mkdir()
            cases = {
                "/private/tmp/handoff.md": "absolute-latest-target",
                "../private/handoff.md": "escaping-latest-target",
                "LATEST.md": "self-referencing-latest",
                "missing.md": "missing-latest-target",
            }
            for target, code in cases.items():
                with self.subTest(target=target):
                    latest = directory / "LATEST.md"
                    latest.write_text(latest_text(target), encoding="utf-8")
                    completed = self.run_cli("latest", str(latest))
                    self.assertEqual(1, completed.returncode)
                    self.assertIn(f"ERROR {code}:", completed.stderr)

    def test_symlink_escape_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            directory = root / "handoffs"
            directory.mkdir()
            outside = root / "2026-07-30-1030-outside.md"
            outside.write_text(valid_snapshot(), encoding="utf-8")
            link = directory / "2026-07-30-1030-linked.md"
            link.symlink_to(outside)
            latest = directory / "LATEST.md"
            latest.write_text(latest_text(link.name), encoding="utf-8")

            completed = self.run_cli("latest", str(latest))

            self.assertEqual(1, completed.returncode)
            self.assertIn("ERROR escaping-latest-target:", completed.stderr)

    def test_next_path_uses_base_name_when_free(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            completed = self.run_cli(
                "next-path",
                raw,
                "--timestamp",
                "2026-07-30-1030",
                "--topic",
                "validator",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                str(Path(raw) / "2026-07-30-1030-validator.md"),
                completed.stdout.strip(),
            )

    def test_next_path_adds_sequence_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            first = directory / "2026-07-30-1030-validator.md"
            first.write_text(valid_snapshot(), encoding="utf-8")

            completed = self.run_cli(
                "next-path",
                raw,
                "--timestamp",
                "2026-07-30-1030",
                "--topic",
                "validator",
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertEqual(
                str(directory / "2026-07-30-1030-validator-02.md"),
                completed.stdout.strip(),
            )


if __name__ == "__main__":
    unittest.main()
