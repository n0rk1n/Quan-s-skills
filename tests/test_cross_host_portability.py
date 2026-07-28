from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


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
        workflow = read("archiving-bilibili-favorites/references/workflow.md")

        self.assertNotIn("$archiving-bilibili-favorites", skill)
        self.assertNotIn("$archiving-bilibili-favorites", workflow)
        self.assertIn("explicitly names or invokes this skill", skill)

    def test_required_capabilities_and_safe_stop_are_explicit(self) -> None:
        skill = read("archiving-bilibili-favorites/SKILL.md")

        self.assertIn("authenticated browser automation", skill)
        self.assertIn("DEVONthink MCP", skill)
        self.assertIn("map", skill.lower())
        self.assertIn("Stop before observing favorites", skill)

    def test_tool_names_are_examples_not_requirements(self) -> None:
        workflow = read("archiving-bilibili-favorites/references/workflow.md")

        self.assertIn("semantic capability", workflow)
        self.assertIn("non-normative examples", workflow)
        self.assertIn("mcp__devonthink.create_record", workflow)


if __name__ == "__main__":
    unittest.main()
