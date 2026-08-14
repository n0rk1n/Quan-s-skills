from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills" / "conversation"
GENERATOR = SKILLS_ROOT / "creating-conversation-handoffs"
READER = SKILLS_ROOT / "resuming-from-conversation-handoff"


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

    def test_generator_returns_a_complete_candidate_when_publish_is_forbidden(
        self,
    ) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn(
            "return a complete candidate snapshot using every template section",
            skill,
        )
        self.assertIn("label it as unvalidated and unpublished", skill)

    def test_generator_uses_the_exact_unavailable_uuid_form(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn(
            "must start with `不可用：` and must not carry a fact-state prefix",
            skill,
        )

    def test_generator_never_uses_its_installation_path_as_project_root(
        self,
    ) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn(
            "Never infer the project root from `SKILL_DIR`",
            skill,
        )

    def test_generator_creates_the_hidden_neutral_directory_before_publishing(
        self,
    ) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn("<root>/.oriki/handoffs/", skill)
        self.assertIn("directory when it does not exist", skill)
        self.assertIn("<root>/oriki-handoffs/", skill)
        self.assertIn("<root>/.codex/handoffs/", skill)

    def test_generator_uses_host_qualified_source_references(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn("`<host>:<conversation-id>`", skill)
        self.assertIn("legacy UUID", skill)

    def test_generator_forbids_credential_assignment_examples(self) -> None:
        skill = read_or_empty(GENERATOR / "SKILL.md")
        self.assertIn(
            "Do not emit credential-shaped assignment examples",
            skill,
        )

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
        self.assertIn("{{source_reference}}", template)


class ResumingFromConversationHandoffContractTests(unittest.TestCase):
    def test_reader_skill_exists(self) -> None:
        self.assertTrue((READER / "SKILL.md").is_file())

    def test_reader_defaults_to_latest_or_accepts_an_explicit_snapshot(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("explicit snapshot path", skill)
        self.assertIn(".oriki/handoffs/LATEST.md", skill)
        self.assertIn("oriki-handoffs/LATEST.md", skill)
        self.assertIn(".codex/handoffs/LATEST.md", skill)
        self.assertIn("legacy compatibility fallback", skill)
        self.assertIn("Do not scan unrelated directories", skill)

    def test_reader_rechecks_mutable_facts(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        for item in ("branch", "HEAD", "working tree", "tests", "external state"):
            self.assertIn(item, skill)
        self.assertIn("current evidence wins", skill)

    def test_reader_uses_source_reference_only_when_missing_detail_blocks_progress(
        self,
    ) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("source conversation reference", skill)
        self.assertIn("only when the missing detail blocks", skill)
        self.assertIn("ask the user only if the lookup is unavailable", skill)

    def test_reader_continues_without_repeating_completed_work(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("one-line resume confirmation", skill)
        self.assertIn("first executable step", skill)
        self.assertIn("Do not repeat completed work", skill)

    def test_reader_is_read_only_for_handoff_and_archive_state(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn(
            "Do not modify, replace, or delete the handoff",
            skill,
        )
        self.assertIn("Do not invoke or load `archiving-to-devonthink`", skill)
        self.assertNotIn("validate_handoff.py", skill)

    def test_reader_requests_a_safe_entry_after_malformed_input(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn(
            "request an explicit safe snapshot path or a complete handoff",
            skill,
        )
        self.assertIn(
            "Even under no-question pressure, state the required safe input",
            skill,
        )
