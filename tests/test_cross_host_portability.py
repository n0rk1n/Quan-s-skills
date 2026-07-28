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


if __name__ == "__main__":
    unittest.main()
