from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "creating-conversation-handoffs"
READER = ROOT / "resuming-from-conversation-handoff"


def read_or_empty(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


class CreatingConversationHandoffsContractTests(unittest.TestCase):
    def test_generator_files_exist(self) -> None:
        self.assertTrue((GENERATOR / "SKILL.md").is_file())
        self.assertTrue(
            (GENERATOR / "references" / "handoff-template.md").is_file()
        )
        self.assertTrue(
            (GENERATOR / "scripts" / "validate_handoff.py").is_file()
        )

    def test_description_contains_only_trigger_conditions(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        match = re.search(r"^description: (.+)$", skill, re.MULTILINE)
        self.assertIsNotNone(match)
        description = match.group(1)
        self.assertTrue(description.startswith("Use when "))
        self.assertIn("context", description.lower())
        self.assertNotIn("writes", description.lower())
        self.assertNotIn("validate", description.lower())

    def test_generator_requires_explicit_execution_but_may_recommend(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn("recommend this Skill", skill)
        self.assertIn(
            "Do not write a handoff until the user explicitly invokes",
            skill,
        )

    def test_publish_order_preserves_the_last_valid_index(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        required = (
            "safe temporary directory",
            "validate the candidate snapshot",
            "publish the timestamped snapshot",
            "validate the candidate `LATEST.md`",
            "replace `LATEST.md`",
        )
        positions = [skill.index(item) for item in required]
        self.assertEqual(sorted(positions), positions)

    def test_generator_never_archives_the_source(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn("Do not invoke or load `archiving-to-devonthink`", skill)
        self.assertIn("remind the user", skill)
        self.assertIn("after the new conversation resumes successfully", skill)

    def test_template_has_the_exact_required_sections(self) -> None:
        template = read_or_empty(
            GENERATOR / "references" / "handoff-template.md"
        )
        headings = re.findall(r"^## (.+)$", template, re.MULTILINE)
        self.assertEqual(
            [
                "元数据",
                "续接摘要",
                "用户目标与验收标准",
                "必须了解的背景",
                "相对上次交接的变化",
                "事实与证据",
                "已完成事项",
                "当前工作区状态",
                "决策与理由",
                "失败尝试与避坑点",
                "未完成事项与下一步",
                "阻塞项与待确认问题",
                "关键文件、命令与外部资源",
                "来源信息与回查",
                "新对话续接指令",
            ],
            headings,
        )
        self.assertIn("**首个可执行步骤：**", template)
        self.assertIn("{{source_thread_uuid}}", template)
