# Cross-Host Skill Portability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the three active skills use the same capability-driven core workflow in Codex and OpenCode without weakening their safety contracts.

**Architecture:** Keep every skill self-contained: `SKILL.md` and local references define host-neutral capabilities and behavior, while `agents/openai.yaml` remains optional OpenAI/Codex presentation metadata. Add a standard-library `unittest` contract suite that validates portable invocation wording, host-neutral conversation naming, local references, and documentation, then add synthetic cross-host scenarios for behavior that static checks cannot prove.

**Tech Stack:** Markdown Agent Skills, YAML frontmatter, Python 3 standard library `unittest`, DEVONthink MCP capability contracts

## Global Constraints

- Keep each skill independently installable and understandable from its own directory.
- Preserve the existing archival and destructive-action safety gates.
- Do not create separate Codex and OpenCode copies of each skill.
- Do not add a shared runtime or repository-level compatibility library.
- Do not add an OpenCode private-session parser.
- Do not migrate, rename, or merge existing DEVONthink archive groups.
- Do not provide local-file, AppleScript, Finder, or direct-database fallbacks for unavailable DEVONthink MCP operations.
- Do not weaken exact-ID checks or perform live destructive actions as automated tests.
- Existing `agents/openai.yaml` files remain optional OpenAI/Codex metadata.
- Existing Codex and ChatGPT exporter behavior remains unchanged.
- New conversation archives use `YYYY-MM-DD Archived AI Conversations` and do not reuse historical `Archived Codex Conversations` groups.
- OpenCode installation guidance must use a documented discovery path such as `~/.config/opencode/skills/<name>/SKILL.md`.

## File Map

- `tests/test_cross_host_portability.py`: deterministic contracts for skill structure, host-neutral wording, naming, installation documentation, and scenario coverage.
- `tests/cross-host-portability/evaluations.md`: non-destructive Codex/OpenCode capability scenarios and scoring rubrics.
- `archiving-to-devonthink/SKILL.md`: host-neutral conversation source, naming, import, cleanup, and optional conversation-closing workflow.
- `archiving-to-devonthink/agents/openai.yaml`: optional OpenAI/Codex display metadata with host-neutral behavior wording.
- `archiving-douyin-favorites/SKILL.md`: host-neutral explicit selection and capability preflight for Douyin.
- `archiving-douyin-favorites/references/workflow.md`: semantic browser and DEVONthink operation mapping while preserving all archive and cleanup gates.
- `archiving-douyin-favorites/agents/openai.yaml`: optional OpenAI/Codex prompt without making `$skill-name` part of the core contract.
- `archiving-bilibili-favorites/SKILL.md`: host-neutral explicit selection and capability preflight for Bilibili.
- `archiving-bilibili-favorites/references/workflow.md`: semantic browser and DEVONthink operation mapping while preserving the fixed 40-item workflow.
- `archiving-bilibili-favorites/agents/openai.yaml`: optional OpenAI/Codex prompt with host-neutral invocation wording.
- `README.md`: cross-host repository description, complete skill list, Codex/OpenCode installation, invocation, and capability requirements.

---

### Task 1: Portable Conversation Archive Contract

**Files:**
- Create: `tests/test_cross_host_portability.py`
- Modify: `archiving-to-devonthink/SKILL.md:1-61`
- Modify: `archiving-to-devonthink/agents/openai.yaml:1-4`

**Interfaces:**
- Consumes: Existing `conversation_exporter` commands `codex` and `chatgpt`; existing DEVONthink import semantics.
- Produces: Host-neutral conversation contract using readable current context first, optional source adapters, `YYYY-MM-DD Archived AI Conversations`, AI-named records, and optional exact-source closing.

- [ ] **Step 1: Write the failing conversation portability tests**

Create `tests/test_cross_host_portability.py` with reusable readers and the first contract tests:

```python
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
```

- [ ] **Step 2: Run the tests to verify the old Codex contract fails**

Run: `python3 tests/test_cross_host_portability.py ConversationPortabilityTests -v`

Expected: FAIL because the skill still requires Codex-specific sources and uses `Archived Codex Conversations` and Codex-named records.

- [ ] **Step 3: Rewrite the conversation skill around semantic capabilities**

Update `archiving-to-devonthink/SKILL.md` so it states these exact behavioral rules:

```markdown
## Required Capabilities

- Readable current conversation context, or an explicitly selected supported export source.
- DEVONthink MCP operations that can discover Global Inbox, find or create a group, import files, and verify record parents.
- A safe writable temporary directory.
- Optional: a conversation close or archive capability that can target the exact source conversation.
```

Replace the Codex-first source rule with this order:

```markdown
For the current conversation, build the lightweight transcript from the readable current conversation context supplied by the host. Codex rollout JSONL and official ChatGPT exports are optional source adapters for higher-fidelity input; they are not general prerequisites. Stop if neither the host context nor a selected adapter can produce a trustworthy transcript, and never present a retrospective as the original transcript.
```

Preserve the existing transcript content rules and importer command examples, but label the `codex` and `chatgpt` commands as optional adapter examples. Change the group and file contracts to:

```text
YYYY-MM-DD Archived AI Conversations
YYYY-MM-DD <对话解决的问题>（AI 对话归档）.md
YYYY-MM-DD <对话解决的问题>（AI 对话原文）.md
```

State that historical Codex-named groups are not discovered, reused, renamed, merged, or migrated. Keep source closing after verified imports and temporary-file cleanup. Describe `set_thread_archived` only as a non-normative example of a host-provided close/archive operation.

- [ ] **Step 4: Make optional OpenAI metadata match the new core behavior**

Update `archiving-to-devonthink/agents/openai.yaml` to retain the same keys but use host-neutral display and prompt text:

```yaml
interface:
  display_name: "归档 AI 对话"
  short_description: "整理当前 AI 对话并导入 DEVONthink 每日目录"
  default_prompt: "Use the archiving-to-devonthink skill to archive this AI conversation into today's DEVONthink Global Inbox folder, verify both records, clean up temporary files, and close the source conversation when the host supports it."
```

- [ ] **Step 5: Run the focused tests and the exporter CLI help checks**

Run: `python3 tests/test_cross_host_portability.py ConversationPortabilityTests -v`

Expected: all three tests PASS.

Run: `PYTHONPATH="archiving-to-devonthink/scripts" python3 -m conversation_exporter.cli codex --help`

Expected: exit 0 and help still describes Codex JSONL input.

Run: `PYTHONPATH="archiving-to-devonthink/scripts" python3 -m conversation_exporter.cli chatgpt --help`

Expected: exit 0 and help still describes official ChatGPT exports.

- [ ] **Step 6: Commit the conversation contract**

```bash
git add tests/test_cross_host_portability.py archiving-to-devonthink/SKILL.md archiving-to-devonthink/agents/openai.yaml
git commit -m "Make conversation archive skill host neutral"
```

### Task 2: Portable Douyin Capability Mapping

**Files:**
- Modify: `tests/test_cross_host_portability.py`
- Modify: `archiving-douyin-favorites/SKILL.md:1-30`
- Modify: `archiving-douyin-favorites/references/workflow.md:1-181`
- Modify: `archiving-douyin-favorites/agents/openai.yaml:1-7`

**Interfaces:**
- Consumes: Authenticated browser automation and DEVONthink MCP record operations exposed under any host-specific names.
- Produces: A host-neutral preflight and unchanged archive-before-exact-ID-cleanup contract for the default 24-item batch.

- [ ] **Step 1: Add failing Douyin portability tests**

Add this class above the `if __name__ == "__main__"` block in `tests/test_cross_host_portability.py`:

```python
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
```

- [ ] **Step 2: Run the focused tests to verify Codex invocation wording fails**

Run: `python3 tests/test_cross_host_portability.py DouyinPortabilityTests -v`

Expected: FAIL because `$archiving-douyin-favorites`, generic “available browser,” and mandatory concrete MCP names remain in the core instructions.

- [ ] **Step 3: Add host-neutral preflight to the Douyin skill**

In `archiving-douyin-favorites/SKILL.md`, replace Codex-style explicit invocation wording with:

```markdown
Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax.
```

Define required capabilities before the safety invariant:

```markdown
- Authenticated browser automation that can inspect and operate the signed-in Douyin session, match stable content IDs, inspect the final dialog, reload, and perform delayed verification.
- DEVONthink MCP operations that can discover Global Inbox and create, look up, update, tag, and verify groups and records.

Map the current host's tools to these semantic capabilities before observing favorites. Stop before observing favorites if either required capability is unavailable; do not offer a reduced fallback.
```

Do not change the default batch size of 24, the dated destination, summary requirements, or the exact-ID safety invariant.

- [ ] **Step 4: Make the detailed workflow semantic without deleting useful examples**

Update `archiving-douyin-favorites/references/workflow.md` so preflight checks capabilities rather than specific host tool names. Introduce the concrete names with wording equivalent to:

```markdown
Map host tools by semantic capability, not by exact name. Names such as `mcp__devonthink.get_databases`, `mcp__devonthink.create_record`, and `mcp__devonthink.set_record_tags` are non-normative examples; use equivalent DEVONthink MCP operations exposed by the current host.
```

Keep every existing destination, bookmark, summary, exact-ID, dialog, retry, stopping, merging, and no-fallback rule. Do not reorder the safety gates.

- [ ] **Step 5: Update optional OpenAI metadata and run focused tests**

Change only `default_prompt` in `archiving-douyin-favorites/agents/openai.yaml` so it says `Use the archiving-douyin-favorites skill` rather than `$archiving-douyin-favorites`. Keep `allow_implicit_invocation: false` because it is valid optional OpenAI policy metadata.

Run: `python3 tests/test_cross_host_portability.py DouyinPortabilityTests -v`

Expected: all three tests PASS.

- [ ] **Step 6: Commit the Douyin contract**

```bash
git add tests/test_cross_host_portability.py archiving-douyin-favorites/SKILL.md archiving-douyin-favorites/references/workflow.md archiving-douyin-favorites/agents/openai.yaml
git commit -m "Make Douyin archive skill capability driven"
```

### Task 3: Portable Bilibili Capability Mapping

**Files:**
- Modify: `tests/test_cross_host_portability.py`
- Modify: `archiving-bilibili-favorites/SKILL.md:1-28`
- Modify: `archiving-bilibili-favorites/references/workflow.md:1-45`
- Modify: `archiving-bilibili-favorites/agents/openai.yaml:1-4`

**Interfaces:**
- Consumes: Authenticated browser automation and DEVONthink MCP record operations exposed under any host-specific names.
- Produces: A host-neutral preflight and unchanged fixed 40-item archive-and-cancel workflow.

- [ ] **Step 1: Add failing Bilibili portability tests**

Add this class to `tests/test_cross_host_portability.py`:

```python
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
```

- [ ] **Step 2: Run the focused tests to verify the old wording fails**

Run: `python3 tests/test_cross_host_portability.py BilibiliPortabilityTests -v`

Expected: FAIL because the skill and optional prompt still use `$archiving-bilibili-favorites` and do not define semantic browser capabilities.

- [ ] **Step 3: Add host-neutral Bilibili preflight and workflow mapping**

Update `archiving-bilibili-favorites/SKILL.md` with the same invocation semantics as Douyin and these required capabilities:

```markdown
- Authenticated browser automation that can inspect and operate the signed-in Bilibili session, match BV IDs and canonical URLs, inspect the final dialog, reload, and verify removals.
- DEVONthink MCP operations that can discover a writable Inbox and create, look up, update, tag, and verify groups and bookmark/Markdown records.

Map the current host's tools to these semantic capabilities before observing favorites. Stop before observing favorites if either required capability is unavailable.
```

In `archiving-bilibili-favorites/references/workflow.md`, make the first preflight item explicitly map semantic capabilities. Tool names, if added for clarity, must be labeled non-normative examples. Preserve the fixed 40-item batch, fresh numbered group, BV-ID mapping, exact selection, dialog check, reload verification, retry bound, and Chinese summary.

- [ ] **Step 4: Update optional OpenAI metadata and run focused tests**

Change `archiving-bilibili-favorites/agents/openai.yaml` to:

```yaml
interface:
  display_name: "归档哔哩哔哩收藏"
  short_description: "Archive and safely unfavorite Bilibili batches."
  default_prompt: "Use the archiving-bilibili-favorites skill to archive and cancel my next 40 Bilibili favorites."
```

Run: `python3 tests/test_cross_host_portability.py BilibiliPortabilityTests -v`

Expected: all three tests PASS.

- [ ] **Step 5: Commit the Bilibili contract**

```bash
git add tests/test_cross_host_portability.py archiving-bilibili-favorites/SKILL.md archiving-bilibili-favorites/references/workflow.md archiving-bilibili-favorites/agents/openai.yaml
git commit -m "Make Bilibili archive skill capability driven"
```

### Task 4: Cross-Host Installation and Structural Validation

**Files:**
- Modify: `tests/test_cross_host_portability.py`
- Modify: `README.md:1-48`

**Interfaces:**
- Consumes: The three self-contained skill directories completed in Tasks 1-3; official OpenCode skill discovery paths.
- Produces: Verified frontmatter/link integrity and Codex/OpenCode installation and invocation instructions.

- [ ] **Step 1: Add failing repository structure and README tests**

Add these constants and classes to `tests/test_cross_host_portability.py`:

```python
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
```

- [ ] **Step 2: Run the new tests to expose current README gaps**

Run: `python3 tests/test_cross_host_portability.py SkillStructureTests ReadmePortabilityTests -v`

Expected: structure tests PASS; README tests FAIL because the README describes a personal Codex collection, omits Bilibili, and has no OpenCode installation path.

- [ ] **Step 3: Rewrite README as cross-host documentation**

Keep the clone command, then organize `README.md` into these sections:

```markdown
# Quan's Skills

Cross-host Agent Skills for Codex, OpenCode, and compatible hosts.

## Skills
## Required Capabilities
## Install for Codex
## Install for OpenCode
## Invoke a Skill
## Optional Host Metadata
```

List all three skills. Explain that the favorites skills require authenticated browser automation plus DEVONthink MCP and stop safely when either is missing. Explain that conversation archiving requires readable conversation context, DEVONthink MCP, and safe temporary files, while source closing is optional.

Show Codex installation under `~/.codex/skills/<name>` and OpenCode installation under `~/.config/opencode/skills/<name>`. Use a shell loop or one generic `<name>` command that copies the complete skill directory, not only `SKILL.md`, so references and scripts remain available. Explain that OpenCode discovers the skill and loads it through its native `skill` tool; users may explicitly name the skill in their request.

State exactly:

```markdown
Files under `agents/`, including `agents/openai.yaml`, are optional OpenAI/Codex interface metadata. OpenCode executes the host-neutral contract from `SKILL.md` and does not need those files.
```

Document that new conversation archives use `Archived AI Conversations`; existing Codex-named DEVONthink groups remain untouched.

- [ ] **Step 4: Run structure, README, and all accumulated tests**

Run: `python3 tests/test_cross_host_portability.py -v`

Expected: all tests PASS.

- [ ] **Step 5: Commit cross-host documentation**

```bash
git add tests/test_cross_host_portability.py README.md
git commit -m "Document Codex and OpenCode skill installation"
```

### Task 5: Non-Destructive Cross-Host Scenario Matrix

**Files:**
- Modify: `tests/test_cross_host_portability.py`
- Create: `tests/cross-host-portability/evaluations.md`

**Interfaces:**
- Consumes: Final host-neutral contracts from Tasks 1-4.
- Produces: Synthetic evaluation prompts covering full capability, missing capability, optional closing, and insufficient transcript context without accessing live accounts or DEVONthink.

- [ ] **Step 1: Add a failing scenario coverage test**

Add this class to `tests/test_cross_host_portability.py`:

```python
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
```

- [ ] **Step 2: Run the scenario test to verify the matrix is absent**

Run: `python3 tests/test_cross_host_portability.py ScenarioCoverageTests -v`

Expected: ERROR with `FileNotFoundError` for `tests/cross-host-portability/evaluations.md`.

- [ ] **Step 3: Create the six-scenario evaluation matrix**

Create `tests/cross-host-portability/evaluations.md`. Begin with this shared safety instruction:

```markdown
These are synthetic decision scenarios. Dispatch each prompt to a fresh-context evaluator with the named skill directory available. Do not access a live browser, filesystem outside a disposable fixture, DEVONthink database, or personal data. Do not modify a real account or submit a real unfavorite action.
```

For each required scenario, include `Prompt` and `Scoring rubric` sections with these concrete expectations:

1. `codex-all-capabilities`: current Codex context, DEVONthink MCP, temporary files, and conversation archive operation are available; expect the AI-named group and records, verified import/cleanup, then exact-source closing.
2. `opencode-all-capabilities`: OpenCode current context, configured DEVONthink MCP, and authenticated browser automation are available; expect the same core workflow without requesting Codex paths or `$skill-name` syntax.
3. `missing-browser-automation`: invoke either favorites skill with DEVONthink available but no authenticated browser automation; expect a stop before observing favorites and no fallback or destructive action.
4. `missing-devonthink-mcp`: invoke a favorites skill with browser automation available but no DEVONthink MCP; expect a stop before observing favorites and no local, Finder, AppleScript, or direct-package fallback.
5. `missing-conversation-closing`: conversation context and DEVONthink import work, but source closing is unavailable; expect successful verified archive and temporary cleanup followed by an accurate manual-close request, not rollback.
6. `insufficient-conversation-context`: current context is truncated and no selected export adapter is available; expect a stop before creating misleading transcript files and no retrospective mislabeled as original text.

- [ ] **Step 4: Run all deterministic tests**

Run: `python3 tests/test_cross_host_portability.py -v`

Expected: all tests PASS, including all six scenario headings and safety language.

- [ ] **Step 5: Perform final non-destructive contract checks**

Run: `rg -n '\$archiving-(to-devonthink|douyin-favorites|bilibili-favorites)' README.md archiving-to-devonthink archiving-douyin-favorites archiving-bilibili-favorites`

Expected: no matches in core skill, workflow, README, or optional prompt text.

Run: `rg -n 'Archived Codex Conversations|（Codex (归档|原文)）' archiving-to-devonthink README.md`

Expected: matches only in an explicit historical-data statement, if that exact old name is retained for clarity; no active destination or filename rule uses it.

Run: `git diff --check`

Expected: exit 0 with no whitespace errors.

- [ ] **Step 6: Commit the evaluation matrix**

```bash
git add tests/test_cross_host_portability.py tests/cross-host-portability/evaluations.md
git commit -m "Add cross-host skill portability evaluations"
```

- [ ] **Step 7: Verify the final commit range and implementation worktree**

Run: `python3 tests/test_cross_host_portability.py -v`

Expected: all tests PASS.

Run: `git status --short`

Expected: no modified or untracked implementation files. The saved plan itself may remain untracked if the handoff did not commit planning documents.

Run: `git log --oneline -6`

Expected: the four implementation commits and the evaluation commit appear above `99c0858 Design cross-host skill portability`.
