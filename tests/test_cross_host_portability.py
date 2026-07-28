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


SKILLS = (
    "archiving-to-devonthink",
    "archiving-douyin-favorites",
    "archiving-bilibili-favorites",
)


class SkillStructureTests(unittest.TestCase):
    def test_frontmatter_names_match_directories(self) -> None:
        for name in SKILLS:
            with self.subTest(skill=name):
                text = read(f"{name}/SKILL.md")
                match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
                self.assertIsNotNone(match)
                self.assertIn(f"name: {name}", match.group(1))

    def test_relative_markdown_links_resolve_inside_each_skill(self) -> None:
        link_pattern = re.compile(r"\[[^]]+\]\(([^)]+)\)")
        for name in SKILLS:
            skill_path = ROOT / name / "SKILL.md"
            for target in link_pattern.findall(skill_path.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(skill=name, target=target):
                    self.assertTrue((skill_path.parent / target).resolve().is_file())


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
