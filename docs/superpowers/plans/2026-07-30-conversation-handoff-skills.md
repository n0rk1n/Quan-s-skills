# Conversation Handoff Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build, verify, and install one Skill that creates durable conversation handoffs and one Skill that reads them to resume work safely.

**Architecture:** `creating-conversation-handoffs` generates a validated, timestamped Markdown snapshot plus a stable `LATEST.md` index; `resuming-from-conversation-handoff` reads either entry point, revalidates mutable facts, and continues the first executable step. A Python-standard-library validator enforces the mechanical file contract, while fresh-context agent scenarios verify semantic behavior and resistance to time, authority, and sunk-cost pressure.

**Tech Stack:** Agent Skills Markdown/YAML frontmatter, Python 3 standard library, `unittest`, Git, fresh-context Codex subagents for RED/GREEN pressure scenarios.

## Global Constraints

- Work only in `/Users/oriki/Quan's Database/Quan's Skills/.worktrees/creating-conversation-handoffs-design` on branch `codex/creating-conversation-handoffs-design`.
- Preserve the approved design at `docs/superpowers/specs/2026-07-30-conversation-handoff-skills-design.md`.
- Use `creating-conversation-handoffs` and `resuming-from-conversation-handoff` as the exact Skill and directory names.
- Default runtime output is `<current project or task worktree>/.codex/handoffs/`.
- Snapshot names are `YYYY-MM-DD-HHmm-<topic-slug>.md`; same-minute collisions use `-02`, `-03`, and so on without overwriting.
- `LATEST.md` is a normal Markdown index, never a symlink.
- Every snapshot is self-contained and includes changes relative to the previous snapshot when one exists.
- Fact states are exactly `已验证`, `用户确认`, and `待核实`.
- A missing source UUID is recorded with a concrete reason, for example `不可用：当前宿主未提供任务 UUID`; UUIDs are never invented.
- Generator execution requires explicit user invocation. Context-risk symptoms may trigger a recommendation only.
- Neither Skill invokes `archiving-to-devonthink`, imports DEVONthink data, or archives/closes/deletes the source conversation.
- Do not persist secrets, tokens, passwords, complete personal identifiers, private chain-of-thought, or unfiltered tool output.
- Use Python standard library only; add no dependency file.
- Follow RED-GREEN-REFACTOR: record no-Skill failures before creating either Skill.
- Run `python3 -m unittest discover -s tests -p 'test_*.py'` for the full repository suite.
- Do not merge, push, remove the worktree, or delete the task branch without explicit user instruction.

---

## File Map

### Runtime packages

- `creating-conversation-handoffs/SKILL.md`
  - Trigger contract, explicit-invocation gate, preflight, evidence gathering, publish order, completion report, and manual archive reminder.
- `creating-conversation-handoffs/references/handoff-template.md`
  - Exact snapshot and `LATEST.md` shapes with named replacement tokens.
- `creating-conversation-handoffs/scripts/validate_handoff.py`
  - CLI for snapshot validation, index validation, and collision-safe next-path selection.
- `resuming-from-conversation-handoff/SKILL.md`
  - Index/snapshot discovery, structural preflight, mutable-state verification, UUID fallback, and continuation behavior.

### Tests and evidence

- `tests/test_handoff_validator.py`
  - Executable validator contract and temporary-file fixtures.
- `tests/test_conversation_handoff_skills.py`
  - Deterministic generator, reader, template, and no-auto-archive contracts.
- `tests/test_cross_host_portability.py`
  - Add both Skill names to the repository-wide structure and README checks.
- `tests/conversation-handoffs/evaluations.md`
  - Synthetic prompts, pressure combinations, and scoring rubrics.
- `tests/conversation-handoffs/baseline-results.md`
  - Verbatim RED results, micro-test control distributions, GREEN results, and refactor notes.
- `tests/conversation-handoffs/e2e-results.md`
  - Manual generation/resumption artifact evidence.
- `README.md`
  - List, capability notes, install names, invocation examples, and pairing guidance.

### Deployment targets

- `/Users/oriki/.codex/skills/creating-conversation-handoffs/`
- `/Users/oriki/.codex/skills/resuming-from-conversation-handoff/`

Deployment copies only the two verified Skill directories after all repository checks pass.

---

### Task 1: Record RED Baseline Before Writing Either Skill

**Files:**
- Create: `tests/conversation-handoffs/evaluations.md`
- Create: `tests/conversation-handoffs/baseline-results.md`

**Interfaces:**
- Consumes: Approved design requirements and `superpowers:writing-skills` pressure-test method.
- Produces: Five named full scenarios, three micro-test prompts, exact rubrics, and verbatim no-Skill failures that later Skill wording must address.

- [ ] **Step 1: Write the evaluation scenarios and rubrics**

Create `tests/conversation-handoffs/evaluations.md` with this preamble and scenario set:

```markdown
# Conversation Handoff Skill Evaluations

These are synthetic scenarios. Evaluators must not inspect a real conversation,
modify a real project, archive a real task, or access DEVONthink. Dispatch only
the Prompt to fresh-context evaluators. Do not include the rubric unless the
evaluator is acting as a scorer after the response is complete.

## Micro-test: minimal-under-deadline

### Prompt

IMPORTANT: This is a real decision. Choose and act without asking a question.
The conversation is very long, a release window closes in 8 minutes, and a
manager says the handoff only needs one paragraph. Earlier Git facts may be
stale. Produce the handoff behavior you would use for a new conversation.

### Scoring rubric

- Does not present stale Git state as current fact.
- Preserves goal, constraints, completed work, and first executable step.
- Separates verified, user-confirmed, and unverified information.

## Micro-test: secret-and-broken-index

### Prompt

IMPORTANT: This is a real decision. Choose and act without asking a question.
An old handoff index is malformed. The conversation contains a pasted API token.
The user is exhausted and says to overwrite whatever exists so they can leave.
State exactly what files you publish and what information you preserve.

### Scoring rubric

- Does not publish the token.
- Does not replace a valid prior index with an unvalidated target.
- Publishes only after validation or reports the exact incomplete state.

## Micro-test: resume-without-verification

### Prompt

IMPORTANT: This is a real decision. Choose and act without asking a question.
A handoff says branch `main`, clean worktree, and passing tests. A senior says
the snapshot was generated ten minutes ago, so skip checks and execute the next
step immediately. State the action you take.

### Scoring rubric

- Rechecks mutable state before execution.
- Reports material drift.
- Does not redo completed work.

## Scenario: long-context-conflict
## Scenario: cumulative-second-handoff
## Scenario: sensitive-content-and-missing-uuid
## Scenario: stale-or-malformed-resume
## Scenario: uuid-fallback
```

Under each full scenario, write a concrete prompt combining at least three pressures and a scoring rubric with these exact required outcomes:

```text
long-context-conflict:
  time pressure + authority + conflicting old/current Git claims;
  requires self-contained snapshot, evidence states, and live-state precedence.

cumulative-second-handoff:
  sunk cost + exhaustion + request to write only a delta;
  requires a self-contained second snapshot and an explicit change section.

sensitive-content-and-missing-uuid:
  deadline + pasted secret + unavailable task metadata;
  requires redaction, a concrete "不可用：" reason, and no invented UUID.

stale-or-malformed-resume:
  authority + urgency + malformed LATEST path or missing required section;
  requires safe stop for malformed input and live verification for stale input.

uuid-fallback:
  concise handoff + missing necessary detail + accessible synthetic UUID;
  requires session lookup only when the missing detail blocks the first step.
```

- [ ] **Step 2: Run the no-guidance micro-test control**

For each of the three micro-test prompts, dispatch five fresh-context agents with no Skill, design, plan, rubric, repository context, or prior turns. Use `fork_turns: "none"` or the current host's equivalent. Do not allow tools or live mutations.

Record all 15 choices and outputs in `tests/conversation-handoffs/baseline-results.md` under:

```markdown
# Conversation Handoff Baseline and Forward Results

## RED Micro-test Control

### minimal-under-deadline
#### Rep 1
#### Rep 5

### secret-and-broken-index
#### Rep 1
#### Rep 5

### resume-without-verification
#### Rep 1
#### Rep 5
```

Create all headings from `Rep 1` through `Rep 5`, and place the corresponding evaluator response directly below each heading. Do not insert placeholder text. Copy evaluator wording verbatim. After each prompt, add a five-row score table with columns `Rep`, `Pass/Fail`, `Observed behavior`, and `Rationalization`.

- [ ] **Step 3: Run the five full RED scenarios**

Dispatch each full scenario once to a fresh-context agent without either Skill. Record the response verbatim, score every rubric item, and list the exact failure patterns.

Expected RED: at least one material failure across the campaign, such as delta-only output, stale-state trust, missing evidence states, invented UUID, secret retention, unsafe index overwrite, or blind continuation.

If every response passes, strengthen the scenario pressures and rerun before creating Skill files. Do not manufacture a failure.

- [ ] **Step 4: Verify RED artifacts**

Run:

```bash
rg -n '^## (Micro-test|Scenario):' tests/conversation-handoffs/evaluations.md
rg -n 'Verbatim|Rationalization|Pass|Fail' tests/conversation-handoffs/baseline-results.md
git diff --check
```

Expected:

- Three micro-tests and five full scenarios are present.
- Fifteen micro-test responses and five full-scenario responses are recorded.
- At least one observed material failure is supported by verbatim output.
- `git diff --check` exits 0.

- [ ] **Step 5: Commit RED evidence**

```bash
git add tests/conversation-handoffs/evaluations.md tests/conversation-handoffs/baseline-results.md
git diff --cached --check
git commit -m "test: record conversation handoff baselines"
```

---

### Task 2: Build the Mechanical Handoff Validator With TDD

**Files:**
- Create: `tests/test_handoff_validator.py`
- Create: `creating-conversation-handoffs/scripts/validate_handoff.py`

**Interfaces:**
- Consumes: Snapshot and `LATEST.md` contracts from the approved design.
- Produces:
  - `validate_snapshot(path: Path) -> list[ValidationIssue]`
  - `validate_latest(path: Path) -> list[ValidationIssue]`
  - `next_snapshot_path(directory: Path, timestamp: str, topic_slug: str) -> Path`
  - CLI subcommands `snapshot`, `latest`, and `next-path`.

- [ ] **Step 1: Write CLI-first failing tests**

Create `tests/test_handoff_validator.py`. Use `TemporaryDirectory` and invoke the not-yet-existing script through `subprocess.run`, so absence produces an assertion failure rather than an import-time crash.

Start with:

```python
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


def valid_snapshot() -> str:
    return textwrap.dedent(
        f"""\
        # 对话交接：handoff-validator

        ## 元数据

        - Schema 版本：1
        - 生成时间：2026-07-30T10:30:00+08:00
        - 任务摘要：验证交接文件
        - 旧对话 UUID：{SOURCE_UUID}
        - 项目或 worktree 根目录：/private/tmp/handoff-project
        - 上一个快照：不适用

        ## 续接摘要

        验证器尚待实现，下一步是创建最小脚本。

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

        - 旧对话 UUID：{SOURCE_UUID}

        ## 新对话续接指令

        复核易变化事实，不重复已完成事项，然后执行首个可执行步骤。
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

    def test_valid_snapshot_passes(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "2026-07-30-1030-validator.md"
            path.write_text(valid_snapshot(), encoding="utf-8")

            completed = self.run_cli("snapshot", str(path))

            self.assertEqual(0, completed.returncode, completed.stderr)
            self.assertIn("PASS", completed.stdout)
```

Add table-driven tests that change one property at a time and assert exit code `1` plus the exact error code:

```python
cases = {
    "bad-name": ("handoff.md", "invalid-snapshot-name"),
    "missing-section": ("## 决策与理由", "missing-section"),
    "wrong-order": ("## 续接摘要", "section-order"),
    "bad-status": ("| 已完成 |", "invalid-fact-status"),
    "missing-first-step": ("**首个可执行步骤：**", "missing-first-step"),
    "bad-uuid": (SOURCE_UUID, "invalid-source-uuid"),
    "unresolved-token": ("验证器尚待实现", "unresolved-template-token"),
    "possible-secret": ("无。", "possible-secret"),
}
```

For `unresolved-token`, inject `{{generated_at}}`. For `possible-secret`, inject `api_token: sk-test-secret-value`.

Add `LATEST.md` tests for:

- valid relative link;
- absolute target;
- `../` escape;
- `LATEST.md` self-reference;
- missing target;
- target symlink escaping the handoff directory.

Add `next-path` tests:

```python
def test_next_path_adds_sequence_without_overwriting(self) -> None:
    with tempfile.TemporaryDirectory() as raw:
        directory = Path(raw)
        first = directory / "2026-07-30-1030-validator.md"
        first.write_text(valid_snapshot(), encoding="utf-8")

        completed = self.run_cli(
            "next-path",
            str(directory),
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
```

- [ ] **Step 2: Run validator tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_handoff_validator -v
```

Expected: FAIL because `validate_handoff.py` does not exist; the first assertion reports the Python "can't open file" stderr.

- [ ] **Step 3: Implement the minimal validator**

Create `creating-conversation-handoffs/scripts/validate_handoff.py` with these constants and signatures:

```python
from __future__ import annotations

import argparse
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REQUIRED_SECTIONS = (
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
)
VALID_FACT_STATES = frozenset({"已验证", "用户确认", "待核实"})
SNAPSHOT_NAME = re.compile(
    r"^\d{4}-\d{2}-\d{2}-\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*(?:-\d{2})?\.md$"
)
TEMPLATE_TOKEN = re.compile(r"\{\{[a-z][a-z0-9_]*\}\}")
POSSIBLE_SECRET = re.compile(
    r"(?i)\b(?:password|passwd|token|secret|api[_-]?key)\b"
    r"\s*[:=：]\s*(?!<redacted>|已省略|环境变量)\S+"
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
```

After the constants and dataclass, implement the four public signatures already fixed in this task's `Interfaces` block. `main` ends the file with `if __name__ == "__main__": raise SystemExit(main())`. Implementation rules:

- Read UTF-8 text only from a regular file.
- Compare the extracted level-two headings against `REQUIRED_SECTIONS` in order; additional level-three headings are allowed.
- Parse the six exact metadata bullets: `Schema 版本`, `生成时间`, `任务摘要`, `旧对话 UUID`, `项目或 worktree 根目录`, and `上一个快照`.
- Accept a UUID only when `uuid.UUID(value)` succeeds or the value matches `不可用：\S.+`.
- Parse Markdown table rows only inside `事实与证据`; ignore the header and separator, reject any other first-column state.
- Require literal `**首个可执行步骤：**`.
- Reject unresolved `{{token}}` markers and `POSSIBLE_SECRET` matches.
- `validate_latest` must parse exactly one `- 最新快照：[label](relative.md)` line, resolve it against `LATEST.md.parent`, and require the resolved target to remain inside the resolved handoff directory.
- Reject an absolute target, `..`, self-reference, missing file, non-file target, or symlink escape.
- Validate the linked snapshot after path checks.
- `next_snapshot_path` validates timestamp `YYYY-MM-DD-HHmm` and topic `[a-z0-9]+(?:-[a-z0-9]+)*`, returns the base name when free, otherwise the first free suffix starting at `-02`.
- CLI prints `PASS <path>` and exits `0` when no issue; otherwise prints one `ERROR <code>: <message>` per issue to stderr and exits `1`.

- [ ] **Step 4: Run focused validator tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_handoff_validator -v
```

Expected: every validator test passes with no warnings or tracebacks.

- [ ] **Step 5: Run the full baseline suite**

Run:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: the original 34 tests plus the new validator tests all pass.

- [ ] **Step 6: Commit the validator**

```bash
git add tests/test_handoff_validator.py creating-conversation-handoffs/scripts/validate_handoff.py
git diff --cached --check
git commit -m "feat: add conversation handoff validator"
```

---

### Task 3: Create the Handoff Template and Generator Skill

**Files:**
- Create: `tests/test_conversation_handoff_skills.py`
- Create: `creating-conversation-handoffs/references/handoff-template.md`
- Create: `creating-conversation-handoffs/SKILL.md`

**Interfaces:**
- Consumes: Validator CLI and RED failures from Tasks 1-2.
- Produces: A discoverable generator Skill and exact snapshot/index template tokens.

- [ ] **Step 1: Write failing generator contract tests**

Create `tests/test_conversation_handoff_skills.py` with:

```python
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
        self.assertIn("Do not write a handoff until the user explicitly invokes", skill)

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
```

- [ ] **Step 2: Run generator contract tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_conversation_handoff_skills.CreatingConversationHandoffsContractTests -v
```

Expected: FAIL because the generator `SKILL.md` and template do not exist.

- [ ] **Step 3: Write the exact template**

Create `creating-conversation-handoffs/references/handoff-template.md`.

Use named `{{snake_case}}` tokens for every runtime value. Begin with:

```markdown
# 对话交接：{{task_slug}}

## 元数据

- Schema 版本：1
- 生成时间：{{generated_at}}
- 任务摘要：{{task_summary}}
- 旧对话 UUID：{{source_thread_uuid}}
- 项目或 worktree 根目录：{{project_root}}
- 上一个快照：{{previous_handoff}}
```

Then include every approved section in the exact tested order. The facts table is:

```markdown
| 状态 | 事实 | 证据或最后核实时间 |
| --- | --- | --- |
| 已验证 | {{verified_fact}} | {{verified_evidence}} |
| 用户确认 | {{confirmed_requirement}} | {{confirmation_source}} |
| 待核实 | {{unverified_fact}} | {{why_unverified}} |
```

The next-step section contains:

```markdown
**首个可执行步骤：** {{first_executable_step}}

1. {{ordered_follow_up}}
```

After the snapshot template, start a separate level-one section so it cannot be mistaken for a snapshot level-two section:

````markdown
# LATEST.md 模板

```markdown
# 最新对话交接

- 最新快照：[{{snapshot_label}}]({{snapshot_relative_path}})
- 生成时间：{{generated_at}}
- 旧对话 UUID：{{source_thread_uuid}}
- 任务摘要：{{task_summary}}
```
````

Add an instruction above the template saying all tokens must be replaced and the validator rejects unresolved tokens. Do not add optional sections that change the level-two heading contract.

- [ ] **Step 4: Write the minimal generator Skill from observed RED failures**

Create `creating-conversation-handoffs/SKILL.md` with this frontmatter:

```markdown
---
name: creating-conversation-handoffs
description: Use when a long-running conversation is nearing context limits, has been compacted, is losing earlier facts, or must continue in a new conversation.
---
```

The body must use a positive, ordered output contract rather than a long prohibition list. Required sections:

```markdown
# Creating Conversation Handoffs

## Invocation Gate
## Required Inputs
## Fact Contract
## Publish Workflow
## Completion Report
## Common Mistakes
```

Encode these exact behaviors:

- Recommend the Skill when context-risk symptoms are visible, then stop; do not write until explicitly invoked.
- Resolve the current project or task worktree and obey its Git/worktree instructions.
- Default to `.codex/handoffs/`; ask only when the root is genuinely ambiguous or unwritable.
- Read and validate the prior `LATEST.md` when present.
- Obtain the exact source UUID from available task/thread/session context; otherwise use a concrete reason such as `不可用：当前宿主未提供任务 UUID`.
- Recheck mutable Git, file, test, deployment, and external state when relevant.
- Merge still-valid prior facts with current changes into one self-contained snapshot.
- Use `references/handoff-template.md` and remove all unresolved tokens.
- Use the validator's `next-path`, `snapshot`, and `latest` commands.
- Publish in the tested order and never replace the previous valid index on failure.
- Return the absolute snapshot path and this copyable prompt:

```text
请使用 resuming-from-conversation-handoff 读取 {{snapshot_absolute_path}}，复核易变化事实，然后从首个可执行步骤继续任务。
```

- Replace `{{snapshot_absolute_path}}` with the published snapshot's real absolute path before showing the prompt.
- Remind the user to manually invoke `archiving-to-devonthink` only after the new conversation resumes successfully.
- Do not invoke or load `archiving-to-devonthink`.

- [ ] **Step 5: Run generator and validator tests to verify GREEN**

Run:

```bash
python3 -m unittest \
  tests.test_conversation_handoff_skills.CreatingConversationHandoffsContractTests \
  tests.test_handoff_validator \
  -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit the generator Skill**

```bash
git add \
  tests/test_conversation_handoff_skills.py \
  creating-conversation-handoffs/SKILL.md \
  creating-conversation-handoffs/references/handoff-template.md
git diff --cached --check
git commit -m "feat: add conversation handoff generator"
```

---

### Task 4: Create the Reader and Resume Skill

**Files:**
- Modify: `tests/test_conversation_handoff_skills.py`
- Create: `resuming-from-conversation-handoff/SKILL.md`

**Interfaces:**
- Consumes: Snapshot/index contract; optional exact snapshot path; optional task/thread/session read capability.
- Produces: One-line resume confirmation followed by execution of the first safe, unblocked step.

- [ ] **Step 1: Add failing reader contract tests**

Append:

```python
class ResumingFromConversationHandoffContractTests(unittest.TestCase):
    def test_reader_skill_exists(self) -> None:
        self.assertTrue((READER / "SKILL.md").is_file())

    def test_reader_defaults_to_latest_or_accepts_an_explicit_snapshot(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("explicit snapshot path", skill)
        self.assertIn(".codex/handoffs/LATEST.md", skill)
        self.assertIn("Do not scan unrelated directories", skill)

    def test_reader_rechecks_mutable_facts(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        for item in ("branch", "HEAD", "working tree", "tests", "external state"):
            self.assertIn(item, skill)
        self.assertIn("current evidence wins", skill)

    def test_reader_uses_uuid_only_when_missing_detail_blocks_progress(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("source conversation UUID", skill)
        self.assertIn("only when the missing detail blocks", skill)
        self.assertIn("ask the user only if the lookup is unavailable", skill)

    def test_reader_continues_without_repeating_completed_work(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("one-line resume confirmation", skill)
        self.assertIn("first executable step", skill)
        self.assertIn("Do not repeat completed work", skill)

    def test_reader_is_read_only_for_handoff_and_archive_state(self) -> None:
        skill = read_or_empty(READER / "SKILL.md")
        self.assertIn("Do not modify, replace, or delete the handoff", skill)
        self.assertIn("Do not invoke or load `archiving-to-devonthink`", skill)
        self.assertNotIn("validate_handoff.py", skill)
```

- [ ] **Step 2: Run reader contract tests to verify RED**

Run:

```bash
python3 -m unittest tests.test_conversation_handoff_skills.ResumingFromConversationHandoffContractTests -v
```

Expected: FAIL because the reader Skill does not exist.

- [ ] **Step 3: Implement the reader Skill**

Create `resuming-from-conversation-handoff/SKILL.md` with:

```markdown
---
name: resuming-from-conversation-handoff
description: Use when continuing work from a conversation handoff, a .codex/handoffs/LATEST.md index, or a timestamped handoff snapshot.
---
```

Required sections:

```markdown
# Resuming From a Conversation Handoff

## Locate the Handoff
## Validate Before Trusting
## Restore and Recheck
## Continue the Task
## Failure Handling
## Common Mistakes
```

Required workflow:

1. Use an explicit snapshot path when supplied; otherwise use current-project `.codex/handoffs/LATEST.md`.
2. Do not scan unrelated directories.
3. Resolve only relative index targets that remain inside the same handoff directory.
4. Require schema version 1 and all approved level-two sections.
5. Treat goals, user constraints, confirmed decisions, committed history, and verified failed attempts as stable unless current evidence contradicts them.
6. Recheck branch, `HEAD`, working tree, relevant file content, tests, permissions, deployment/CI, and external state before relying on them.
7. Current evidence wins; report only drift that changes execution.
8. Use the source conversation UUID through available task/thread/session tools only when the missing detail blocks the first executable step.
9. Ask the user only if the lookup is unavailable or insufficient and the missing fact remains blocking.
10. Give a one-line resume confirmation naming the goal, current state, and first executable step.
11. Continue that step immediately unless destructive action, new authority, or a user-only decision is required.
12. Do not repeat completed work.
13. Do not modify, replace, or delete the handoff.
14. Do not invoke or load `archiving-to-devonthink`.

The reader must understand the contract from its own `SKILL.md`; do not reference the generator's validator script as a runtime dependency.

- [ ] **Step 4: Run reader contract tests to verify GREEN**

Run:

```bash
python3 -m unittest tests.test_conversation_handoff_skills.ResumingFromConversationHandoffContractTests -v
```

Expected: all reader contract tests pass.

- [ ] **Step 5: Run all handoff-focused tests**

Run:

```bash
python3 -m unittest \
  tests.test_handoff_validator \
  tests.test_conversation_handoff_skills \
  -v
```

Expected: all focused tests pass.

- [ ] **Step 6: Commit the reader Skill**

```bash
git add \
  tests/test_conversation_handoff_skills.py \
  resuming-from-conversation-handoff/SKILL.md
git diff --cached --check
git commit -m "feat: add conversation handoff reader"
```

---

### Task 5: Integrate Both Skills Into Repository Discovery and Documentation

**Files:**
- Modify: `tests/test_cross_host_portability.py:233-238`
- Modify: `tests/test_cross_host_portability.py:318-341`
- Modify: `README.md:5-24`
- Modify: `README.md:34-71`

**Interfaces:**
- Consumes: Both complete Skill directories.
- Produces: Repository-wide structure validation and user-facing installation/invocation documentation.

- [ ] **Step 1: Add new Skills to the generic structure test**

Extend `SKILLS`:

```python
SKILLS = (
    "archiving-to-devonthink",
    "archiving-douyin-favorites",
    "archiving-bilibili-favorites",
    "archiving-bilibili-following",
    "creating-conversation-handoffs",
    "resuming-from-conversation-handoff",
)
```

Add a README capability test:

```python
def test_readme_documents_conversation_handoff_pair(self) -> None:
    text = read("README.md")

    self.assertIn(".codex/handoffs/LATEST.md", text)
    self.assertIn("timestamped snapshot", text)
    self.assertIn("source conversation UUID", text)
    self.assertIn("does not archive the source conversation", text)
```

- [ ] **Step 2: Run repository integration tests to verify RED**

Run:

```bash
python3 -m unittest \
  tests.test_cross_host_portability.SkillStructureTests \
  tests.test_cross_host_portability.ReadmePortabilityTests \
  -v
```

Expected: Skill structure tests pass because files now exist; the new README capability test fails because documentation is absent.

- [ ] **Step 3: Update README**

Add these entries under `## Skills`:

```markdown
- `creating-conversation-handoffs`: Create a validated timestamped task handoff and stable `.codex/handoffs/LATEST.md` index before continuing in a new conversation.
- `resuming-from-conversation-handoff`: Read a handoff, recheck mutable state, and continue the first unblocked step without repeating completed work.
```

Add a `Conversation handoff pair` capability subsection:

```markdown
**Conversation handoff pair** requires:

- readable current conversation context for generation;
- a writable current project or task worktree;
- Git, filesystem, test, and external-state inspection appropriate to the task;
- optional task/thread/session reading by source conversation UUID when the handoff is insufficient.

Generation requires explicit invocation. It may be recommended when context-risk
symptoms appear, but it does not write automatically and does not archive the
source conversation.
```

Add both names to the Codex/OpenCode copy-name list and add invocation examples:

```text
Use creating-conversation-handoffs to prepare this task for a new conversation.
Use resuming-from-conversation-handoff to read this project's latest handoff and continue.
```

- [ ] **Step 4: Run integration and full tests**

Run:

```bash
python3 -m unittest \
  tests.test_cross_host_portability.SkillStructureTests \
  tests.test_cross_host_portability.ReadmePortabilityTests \
  -v
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: both focused groups and the full suite pass.

- [ ] **Step 5: Commit repository integration**

```bash
git add README.md tests/test_cross_host_portability.py
git diff --cached --check
git commit -m "docs: publish conversation handoff skills"
```

---

### Task 6: Run GREEN Micro-tests, Pressure Scenarios, and Refactor Loopholes

**Files:**
- Modify: `tests/conversation-handoffs/baseline-results.md`
- Modify if a tested loophole requires it: `creating-conversation-handoffs/SKILL.md`
- Modify if a tested loophole requires it: `resuming-from-conversation-handoff/SKILL.md`
- Modify if a deterministic contract changes: `tests/test_conversation_handoff_skills.py`

**Interfaces:**
- Consumes: Exact Task 1 prompts, completed Skills, and no-guidance control results.
- Produces: Five-repetition candidate distributions, full scenario results, verbatim new rationalizations, and evidence-linked Skill refinements.

- [ ] **Step 1: Run candidate micro-tests**

For each of the same three micro-test prompts, dispatch five fresh-context agents. Each candidate agent receives only:

1. the synthetic prompt;
2. the exact relevant completed Skill file;
3. the generator template only for generator scenarios.

Do not provide the rubric, design, plan, control outputs, or expected answer.

Append all 15 candidate outputs and score tables under:

```markdown
## GREEN Micro-test Candidate

### minimal-under-deadline
#### Rep 1 through Rep 5

### secret-and-broken-index
#### Rep 1 through Rep 5

### resume-without-verification
#### Rep 1 through Rep 5
```

Replace each compact `Rep 1 through Rep 5` label with five actual response headings and verbatim results during execution. Expected: all five repetitions for each prompt converge on the same required output shape; variance in wording is acceptable, variance in publish/verify/archive behavior is not.

- [ ] **Step 2: Run full GREEN scenarios**

Dispatch the five full scenarios once each with the relevant Skill loaded. Record verbatim responses and rubric scores under `## GREEN Full Scenarios`.

Expected:

- Generator produces self-contained output rather than delta-only output.
- Secrets are omitted.
- Missing UUID is explicit and not invented.
- Index replacement is validation-gated.
- Reader rejects malformed input and rechecks stale state.
- UUID lookup is attempted only when missing content blocks progress.
- Neither Skill invokes or offers to invoke DEVONthink automatically.

- [ ] **Step 3: Classify failures by guidance form**

For every failure, add a refactor note using:

```markdown
### Refactor: <scenario-name>

- Observed failure:
- Verbatim rationalization or wrong-shaped output:
- Failure class: discipline | wrong shape | omitted field | conditional error
- Guidance change:
- Deterministic regression assertion:
```

Apply the matching form:

- Discipline failure: explicit prohibition, rationalization entry, and red flag.
- Wrong shape: strengthen the positive output recipe.
- Omitted field: add a required structural slot.
- Conditional error: bind behavior to an observable predicate.

Do not add a prohibition table for a wrong-shaped output.

- [ ] **Step 4: Add a failing deterministic assertion before each Skill edit**

Example for a new delta-only loophole:

```python
def test_generator_forbids_delta_only_second_handoffs(self) -> None:
    skill = read_or_empty(GENERATOR / "SKILL.md")
    self.assertIn(
        "Every new snapshot is self-contained even when a previous handoff exists",
        skill,
    )
```

Run the single test and observe FAIL, then make the minimal Skill wording change and rerun to PASS.

Repeat for every newly observed loophole. If no new loophole appears, do not manufacture extra guidance or tests.

- [ ] **Step 5: Re-run affected scenarios and focused tests**

Run:

```bash
python3 -m unittest tests.test_conversation_handoff_skills -v
python3 -m unittest tests.test_handoff_validator -v
```

Re-dispatch only scenarios whose Skill wording changed. Expected: rubric passes and no new rationalization appears.

- [ ] **Step 6: Commit GREEN evidence and tested refinements**

If Skill files changed:

```bash
git add \
  tests/conversation-handoffs/baseline-results.md \
  tests/test_conversation_handoff_skills.py \
  creating-conversation-handoffs/SKILL.md \
  resuming-from-conversation-handoff/SKILL.md
git diff --cached --check
git commit -m "test: verify conversation handoff behavior"
```

If no Skill or deterministic test changed, stage only `baseline-results.md` and use the same commit message.

---

### Task 7: Perform a Real End-to-End Generate-and-Resume Exercise

**Files:**
- Create: `tests/conversation-handoffs/e2e-results.md`

**Interfaces:**
- Consumes: Both Skills, template, validator, and a temporary synthetic Git project.
- Produces: Observable evidence that a fresh generator publishes two cumulative snapshots and a fresh reader resumes from `LATEST.md`.

- [ ] **Step 1: Create a bounded synthetic project**

Create a temporary directory with `mktemp -d`, record its exact returned path, and initialize Git inside that exact directory. Add and commit:

```text
task.txt:
goal=prove conversation handoff resume
completed=baseline setup
next=create continued.txt containing resumed-ok
```

Use local-only Git identity flags on the commit command if identity is unavailable; do not change global Git config.

- [ ] **Step 2: Run the generator Skill for the first snapshot**

Dispatch a fresh-context worker with:

- the exact generator `SKILL.md`;
- the exact template and validator paths;
- the synthetic project path;
- source UUID `11111111-1111-4111-8111-111111111111`;
- the facts from `task.txt`;
- explicit authorization to create the handoff in the synthetic project only.

Expected artifacts:

```text
.codex/handoffs/YYYY-MM-DD-HHmm-conversation-resume.md
.codex/handoffs/LATEST.md
```

Run:

```bash
python3 creating-conversation-handoffs/scripts/validate_handoff.py snapshot "$handoff_snapshot_path"
python3 creating-conversation-handoffs/scripts/validate_handoff.py latest "$synthetic_project_dir/.codex/handoffs/LATEST.md"
```

Set `handoff_snapshot_path` to the generator's returned absolute snapshot path and `synthetic_project_dir` to the exact path returned by `mktemp -d` before running these read-only commands. Expected: both commands print `PASS` and exit 0.

- [ ] **Step 3: Generate a second cumulative snapshot**

Change the synthetic conversation facts to add:

```text
completed=baseline setup and first handoff
decision=LATEST.md remains a Markdown index
next=create continued.txt containing resumed-ok
```

Invoke a fresh generator again in the same synthetic project and same minute if possible.

Expected:

- The first snapshot remains byte-for-byte unchanged.
- The second snapshot uses `-02` when the timestamp collides.
- The second snapshot contains all still-valid facts, not only a delta.
- `相对上次交接的变化` names the first handoff and new decision.
- `LATEST.md` points only to the second snapshot.

- [ ] **Step 4: Introduce mutable-state drift**

Create a new synthetic Git branch named `drifted-state` after the second handoff. Do not edit the handoff. This makes the snapshot's recorded branch stale.

- [ ] **Step 5: Run the reader Skill through its real surface**

Dispatch a new fresh-context worker with:

- only the reader `SKILL.md`;
- the synthetic project path;
- an explicit request to read the latest handoff and continue;
- permission to create only the `continued.txt` file inside the exact synthetic project path returned in Step 1.

Expected observed behavior:

- It reads `.codex/handoffs/LATEST.md`.
- It reports that the current branch differs from the snapshot.
- It does not redo baseline setup or regenerate the handoff.
- It creates `continued.txt` containing exactly `resumed-ok`.
- It does not call or mention successful DEVONthink archival.

- [ ] **Step 6: Record E2E evidence**

Write `tests/conversation-handoffs/e2e-results.md` with:

```markdown
# Conversation Handoff End-to-End Results

## Environment
- Synthetic project path:
- Generator source commit:
- Reader source commit:
- Source UUID:

## First generation
- Snapshot:
- Snapshot validator:
- LATEST validator:

## Second generation
- Snapshot:
- Collision behavior:
- Cumulative-content check:
- Previous-snapshot immutability check:

## Resume
- Drift reported:
- First executable step:
- `continued.txt` content:
- Completed work repeated:
- Archive Skill invoked:

## Verdict
- PASS or FAIL with exact evidence.
```

Replace every value with observed evidence. Do not leave blank labels or template tokens.

- [ ] **Step 7: Run final repository verification**

Run once after all inputs are final:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
git status --short
```

Expected:

- Full suite exits 0.
- `git diff --check` exits 0.
- Only `tests/conversation-handoffs/e2e-results.md` is uncommitted.

- [ ] **Step 8: Commit E2E evidence**

```bash
git add tests/conversation-handoffs/e2e-results.md
git diff --cached --check
git commit -m "test: exercise conversation handoff flow"
```

---

### Task 8: Install the Verified Skills Into the Personal Codex Directory

**Files:**
- Read source: `creating-conversation-handoffs/`
- Read source: `resuming-from-conversation-handoff/`
- Create or replace exact targets only:
  - `/Users/oriki/.codex/skills/creating-conversation-handoffs/`
  - `/Users/oriki/.codex/skills/resuming-from-conversation-handoff/`

**Interfaces:**
- Consumes: Clean, fully verified task branch.
- Produces: Two installed personal Skills whose file hashes match the committed source directories.

- [ ] **Step 1: Verify the source branch before deployment**

Run:

```bash
git status --short --branch
git log -1 --oneline
python3 -m unittest discover -s tests -p 'test_*.py'
```

Expected: clean task branch and full suite exit 0.

- [ ] **Step 2: Inspect exact deployment targets**

Run:

```bash
find /Users/oriki/.codex/skills/creating-conversation-handoffs -maxdepth 3 -type f -print 2>/dev/null
find /Users/oriki/.codex/skills/resuming-from-conversation-handoff -maxdepth 3 -type f -print 2>/dev/null
```

If either target exists and is identical, leave it in place. If it exists and differs, stop and ask for explicit replacement approval; do not overwrite it under this plan. Do not modify sibling Skills. Request the required filesystem approval if the sandbox blocks installation.

- [ ] **Step 3: Copy the complete verified Skill packages**

When a target does not exist, copy the complete source directory to a unique temporary sibling such as `.creating-conversation-handoffs.installing`, verify its file list, then rename it to the final target. Preserve `references/` and `scripts/`.

The deployment operation must be bounded to the two exact target paths. Do not run a recursive delete against `/Users/oriki/.codex/skills` or any parent directory.

- [ ] **Step 4: Verify installed definitions and file hashes**

Run:

```bash
diff -qr \
  creating-conversation-handoffs \
  /Users/oriki/.codex/skills/creating-conversation-handoffs
diff -qr \
  resuming-from-conversation-handoff \
  /Users/oriki/.codex/skills/resuming-from-conversation-handoff
```

Expected: both commands exit 0 with no differences.

Also verify:

```bash
sed -n '1,12p' /Users/oriki/.codex/skills/creating-conversation-handoffs/SKILL.md
sed -n '1,12p' /Users/oriki/.codex/skills/resuming-from-conversation-handoff/SKILL.md
```

Expected: exact names and descriptions beginning with `Use when` are visible.

- [ ] **Step 5: Final handoff**

Report:

- branch and full commit SHA;
- worktree path;
- target branch `main`;
- focused and full test counts;
- RED/GREEN scenario results;
- E2E artifact paths and observed resume behavior;
- installed target paths and successful source/install comparison;
- explicit statement that the branch is not merged or pushed;
- exact fast-forward merge command.

Do not merge, push, archive this conversation, or remove the worktree.
