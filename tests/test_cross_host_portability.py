from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise ValueError("missing YAML frontmatter")

    fields: dict[str, str] = {}
    recognized_fields = {"name", "description", "license", "compatibility"}
    for line in match.group(1).splitlines():
        if line != line.lstrip():
            raise ValueError(f"nested frontmatter is unsupported: {line}")
        if ":" not in line:
            raise ValueError(f"malformed frontmatter line: {line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", key):
            raise ValueError(f"invalid frontmatter key: {key}")
        if key not in recognized_fields:
            raise ValueError(f"unrecognized frontmatter key: {key}")
        if key in fields:
            raise ValueError(f"duplicate frontmatter key: {key}")
        if not value:
            raise ValueError(f"empty frontmatter value: {key}")
        if value[0] in "'\"[{|>&*!%@`":
            raise ValueError(f"only plain scalar frontmatter is supported: {key}")
        fields[key] = value
    return fields


def scenario(text: str, name: str) -> str:
    match = re.search(
        rf"^## Scenario: {re.escape(name)}\n(.*?)(?=^---$|^## Scenario:|\Z)",
        text,
        re.DOTALL | re.MULTILINE,
    )
    if match is None:
        return ""
    return match.group(1)


class ConversationPortabilityTests(unittest.TestCase):
    def test_conversation_skill_uses_host_neutral_source_and_names(self) -> None:
        text = read("archiving-to-devonthink/SKILL.md")

        self.assertIn("readable current conversation context", text)
        self.assertIn("optional source adapter", text)
        self.assertIn("YYYY-MM-DD Archived AI Conversations", text)
        self.assertIn("（AI 对话归档）.md", text)
        self.assertIn("（AI 对话原文）.md", text)
        self.assertNotIn("YYYY-MM-DD Archived Codex Conversations", text)

    def test_codex_sources_and_closing_are_optional_capabilities(self) -> None:
        text = read("archiving-to-devonthink/SKILL.md")

        self.assertRegex(text, r"Codex.+optional|optional.+Codex")
        self.assertIn("conversation close or archive capability", text)
        self.assertIn("manual", text.lower())

    def test_openai_metadata_describes_an_ai_conversation(self) -> None:
        text = read("archiving-to-devonthink/agents/openai.yaml")

        self.assertIn("AI 对话", text)
        self.assertNotIn("archive this Codex conversation", text)

    def test_preflight_stops_before_generation_without_devonthink_mcp(self) -> None:
        text = read("archiving-to-devonthink/SKILL.md")
        fields = parse_frontmatter(text)

        self.assertIn("explicitly names or invokes", fields["description"])
        self.assertIn("explicitly names or invokes this skill", text)
        self.assertIn("Stop before generating temporary files", text)
        self.assertIn("AppleScript", text)
        self.assertIn("direct DEVONthink package", text)

    def test_optional_export_adapters_have_executable_commands(self) -> None:
        text = read("archiving-to-devonthink/SKILL.md")

        self.assertIn(
            'PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli codex',
            text,
        )
        self.assertIn(
            'PYTHONPATH="$SKILL_DIR/scripts" python3 -m conversation_exporter.cli chatgpt',
            text,
        )


class DouyinPortabilityTests(unittest.TestCase):
    def test_core_invocation_is_not_codex_syntax(self) -> None:
        skill = read("archiving-douyin-favorites/SKILL.md")
        workflow = read("archiving-douyin-favorites/references/workflow.md")

        self.assertNotIn("$archiving-douyin-favorites", skill)
        self.assertNotIn("$archiving-douyin-favorites", workflow)
        self.assertIn("explicitly names or invokes this skill", skill)

    def test_required_capabilities_and_safe_stop_are_explicit(self) -> None:
        skill = read("archiving-douyin-favorites/SKILL.md")

        self.assertIn("authenticated browser automation", skill)
        self.assertIn("DEVONthink MCP", skill)
        self.assertIn("map", skill.lower())
        self.assertIn("Stop before observing favorites", skill)

    def test_tool_names_are_examples_not_requirements(self) -> None:
        workflow = read("archiving-douyin-favorites/references/workflow.md")

        self.assertIn("semantic capability", workflow)
        self.assertIn("non-normative examples", workflow)
        self.assertIn("mcp__devonthink.create_record", workflow)
        self.assertNotIn("use `mcp__devonthink.create_record`", workflow.lower())
        self.assertNotIn("do not use `create_group_path`", workflow.lower())
        self.assertNotIn("use `lookup_records`", workflow.lower())

    def test_summary_failure_is_reported_as_partial_completion(self) -> None:
        workflow = read("archiving-douyin-favorites/references/workflow.md")

        self.assertIn("summary creation or verification fails", workflow)
        self.assertIn("preserve verified bookmarks and cleanup state", workflow)
        self.assertIn("do not claim full completion", workflow)


class BilibiliPortabilityTests(unittest.TestCase):
    def test_core_invocation_is_not_codex_syntax(self) -> None:
        skill = read("archiving-bilibili-favorites/SKILL.md")

        self.assertNotIn("$archiving-bilibili-favorites", skill)
        self.assertIn("explicitly names or invokes this skill", skill)

    def test_required_capabilities_and_fixed_batch_are_explicit(self) -> None:
        skill = read("archiving-bilibili-favorites/SKILL.md")

        self.assertIn("authenticated browser automation", skill)
        self.assertIn("DEVONthink MCP", skill)
        self.assertIn("Stop before observing favorites", skill)
        self.assertIn("exactly one bounded batch of 40", skill)

    def test_openai_prompt_does_not_define_core_invocation_syntax(self) -> None:
        metadata = read("archiving-bilibili-favorites/agents/openai.yaml")

        self.assertNotIn("$archiving-bilibili-favorites", metadata)
        self.assertIn("Use the archiving-bilibili-favorites skill", metadata)

    def test_platform_safeguards_are_explicit(self) -> None:
        skill = read("archiving-bilibili-favorites/SKILL.md")

        self.assertIn("Never attempt to bypass login", skill)
        self.assertIn("CAPTCHA", skill)
        self.assertIn("access controls", skill)
        self.assertIn("rate limits", skill)
        self.assertIn("platform safeguards", skill)

    def test_partial_retry_uses_current_submission_set_at_every_gate(self) -> None:
        workflow = read("archiving-bilibili-favorites/references/workflow.md")

        self.assertIn("submission_ids = archived_ids", workflow)
        self.assertIn("submission_ids = remaining_ids", workflow)
        self.assertIn("selected_ids = submission_ids", workflow)
        self.assertIn("dialog count must equal the size of `submission_ids`", workflow)
        self.assertNotIn("显示数量为 40", workflow)

    def test_summary_failure_is_reported_as_partial_completion(self) -> None:
        workflow = read("archiving-bilibili-favorites/references/workflow.md")

        self.assertIn("summary creation or verification fails", workflow)
        self.assertIn("preserve verified bookmarks and cleanup state", workflow)
        self.assertIn("do not claim full completion", workflow)


SKILLS = (
    "archiving-to-devonthink",
    "archiving-douyin-favorites",
    "archiving-bilibili-favorites",
)


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter_has_recognized_required_fields(self) -> None:
        for name in SKILLS:
            with self.subTest(skill=name):
                fields = parse_frontmatter(read(f"{name}/SKILL.md"))
                self.assertEqual(name, fields.get("name"))
                self.assertRegex(fields["name"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
                self.assertTrue(fields.get("description"))
                self.assertLessEqual(len(fields["description"]), 1024)

    def test_frontmatter_parser_rejects_malformed_lines(self) -> None:
        malformed = "---\nname: valid-name\nnot yaml\ndescription: Use when testing\n---\n"

        with self.assertRaises(ValueError):
            parse_frontmatter(malformed)

    def test_frontmatter_parser_rejects_duplicate_keys(self) -> None:
        duplicate = "---\nname: first\nname: second\ndescription: Use when testing\n---\n"

        with self.assertRaises(ValueError):
            parse_frontmatter(duplicate)

    def test_frontmatter_parser_rejects_unterminated_quoted_scalars(self) -> None:
        unterminated = '---\nname: valid-name\ndescription: "Use when testing\n---\n'

        with self.assertRaises(ValueError):
            parse_frontmatter(unterminated)

    def test_relative_markdown_links_resolve_inside_each_skill(self) -> None:
        link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
        for name in SKILLS:
            skill_root = (ROOT / name).resolve()
            for markdown_path in skill_root.rglob("*.md"):
                for target in link_pattern.findall(markdown_path.read_text(encoding="utf-8")):
                    if "://" in target or target.startswith("#"):
                        continue
                    with self.subTest(skill=name, file=markdown_path.name, target=target):
                        resolved = (markdown_path.parent / target).resolve()
                        self.assertTrue(resolved.is_relative_to(skill_root))
                        self.assertTrue(resolved.is_file())


class FavoritesSafetyContractTests(unittest.TestCase):
    def test_douyin_preserves_exact_id_and_delayed_verification_gates(self) -> None:
        workflow = read("archiving-douyin-favorites/references/workflow.md")

        self.assertIn("one-to-one ID/URL mapping", workflow)
        self.assertIn("submission_ids = archived_ids", workflow)
        self.assertIn("submission_ids = remaining_ids", workflow)
        self.assertIn("UI-selected ID set to equal `submission_ids`", workflow)
        self.assertIn("confirmation dialog", workflow)
        self.assertIn("reload the favorites view and wait for lazy-loaded", workflow)
        self.assertIn("persists across three attempts", workflow)

    def test_bilibili_preserves_exact_id_and_delayed_verification_gates(self) -> None:
        workflow = read("archiving-bilibili-favorites/references/workflow.md")

        self.assertIn("一一对应", workflow)
        self.assertIn("submission_ids = archived_ids", workflow)
        self.assertIn("submission_ids = remaining_ids", workflow)
        self.assertIn("selected_ids = submission_ids", workflow)
        self.assertIn("最终弹窗", workflow)
        self.assertIn("重新加载收藏页", workflow)
        self.assertIn("连续三次无进展", workflow)

    def test_both_favorites_skills_fail_closed_without_required_capabilities(self) -> None:
        for name in ("archiving-douyin-favorites", "archiving-bilibili-favorites"):
            with self.subTest(skill=name):
                skill = read(f"{name}/SKILL.md")
                self.assertIn("Stop before observing favorites", skill)
                self.assertIn("do not offer a reduced fallback", skill)


class ReadmePortabilityTests(unittest.TestCase):
    def test_readme_documents_both_hosts_and_all_skills(self) -> None:
        text = read("README.md")

        self.assertNotIn("Personal Codex skills collection", text)
        self.assertIn("Codex", text)
        self.assertIn("OpenCode", text)
        self.assertIn("~/.codex/skills", text)
        self.assertIn("~/.config/opencode/skills", text)
        for name in SKILLS:
            self.assertIn(f"`{name}`", text)

    def test_readme_explains_capabilities_and_optional_metadata(self) -> None:
        text = read("README.md")

        self.assertIn("DEVONthink MCP", text)
        self.assertIn("browser automation", text.lower())
        self.assertIn("optional OpenAI/Codex interface metadata", text)

    def test_readme_requires_explicit_skill_selection_on_both_hosts(self) -> None:
        text = read("README.md")

        self.assertNotIn("triggers automatically", text)
        self.assertIn("explicitly name or invoke the skill", text)


class ScenarioCoverageTests(unittest.TestCase):
    def test_cross_host_matrix_covers_required_scenarios(self) -> None:
        text = read("tests/cross-host-portability/evaluations.md")
        scenarios = (
            "codex-all-capabilities",
            "opencode-all-capabilities",
            "missing-browser-automation",
            "missing-devonthink-mcp",
            "missing-conversation-closing",
            "insufficient-conversation-context",
        )

        for scenario in scenarios:
            self.assertIn(f"## Scenario: {scenario}", text)

        self.assertIn("Do not access a live browser", text)
        self.assertIn("Do not modify a real account", text)


if __name__ == "__main__":
    unittest.main()
