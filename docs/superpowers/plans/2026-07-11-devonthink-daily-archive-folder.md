# DEVONthink Daily Archive Folder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DEVONthink MCP mandatory, route both Codex archive Markdown records into one reusable daily Global Inbox folder, and show the skill under a Chinese name in Codex.

**Architecture:** Keep the archive/export implementation unchanged and tighten only the workflow contract in `SKILL.md`. Add `agents/openai.yaml`, following the neighboring Douyin skill, for localized Codex UI metadata while preserving the stable `archiving-to-devonthink` skill identifier.

**Tech Stack:** Markdown skill documentation, OpenAI skill interface YAML, shell-based structural checks, pressure-scenario evaluation with fresh subagents.

## Global Constraints

- DEVONthink MCP is a hard dependency with no local-only, AppleScript, direct database-package, or skipped-import fallback.
- The Global Inbox daily folder name is exactly `YYYY-MM-DD Archived Codex Conversations`, using the current local date.
- Reuse the same-day folder when it exists; create it only when missing.
- Import both `（Codex 原文）` and `（Codex 归档）` Markdown files into that folder.
- The Codex display name is exactly `归档 Codex 对话`; the internal identifier remains `archiving-to-devonthink`.
- Preserve all unrelated filename, content, validation, cleanup, and Codex-thread archive rules.

---

### Task 1: Prove the Existing Skill Leaves the New Gates Ambiguous

**Files:**
- Read: `archiving-to-devonthink/SKILL.md`
- Read: `docs/superpowers/specs/2026-07-11-devonthink-daily-archive-folder-design.md`
- Record evidence in the implementation report; do not create a permanent test fixture.

**Interfaces:**
- Consumes: the current unmodified skill text and the approved requirements.
- Produces: baseline evidence showing whether agents permit a non-MCP fallback, import into the Inbox root, or create a duplicate same-day folder.

- [ ] **Step 1: Run a no-new-guidance control for the MCP failure case**

Use a fresh subagent without supplying the proposed wording:

```text
The user invoked archiving-to-devonthink. DEVONthink MCP is unavailable, but local temp storage and AppleScript are available. The user says this is urgent and asks you to preserve progress. State exactly what you do next.
```

Expected baseline failure: the agent may offer or perform a reduced local workflow because the current skill allows an explicitly chosen reduced workflow.

- [ ] **Step 2: Run a no-new-guidance control for the destination case**

```text
The user invoked archiving-to-devonthink twice on 2026-07-11. Global Inbox already contains a group named 2026-07-11 Archived Codex Conversations. Explain where the transcript and retrospective from the second invocation are imported.
```

Expected baseline failure: the agent cannot derive the exact daily-folder reuse rule from the current skill and may import into the Inbox root or create a duplicate group.

- [ ] **Step 3: Run a no-new-guidance control for partial destination success**

```text
The transcript was imported into the dated Global Inbox group, but the retrospective was accidentally imported into the Global Inbox root. Both imports returned UUIDs. Decide whether cleanup and Codex thread archiving may proceed.
```

Expected baseline failure: the current validation checks identifiable destinations but does not require both destinations to equal the daily-folder UUID.

### Task 2: Add the Hard MCP Gate and Daily Folder Contract

**Files:**
- Modify: `archiving-to-devonthink/SKILL.md:8-110`

**Interfaces:**
- Consumes: DEVONthink MCP capabilities for database discovery, group search or creation, and file import.
- Produces: an identifiable `daily_archive_group_uuid` used as the destination for both imports and all completion checks.

- [ ] **Step 1: Add a failing structural check**

Run before editing:

```bash
rg -n "Archived Codex Conversations|same daily folder|DEVONthink MCP is unavailable" archiving-to-devonthink/SKILL.md
```

Expected: no matches, proving the new contract is absent.

- [ ] **Step 2: Replace the permissive DEVONthink capability wording**

Change Required Capabilities so it explicitly requires DEVONthink MCP tools and includes this contract:

```markdown
DEVONthink MCP is a hard requirement. Before generating either temporary Markdown file, confirm the MCP can discover the Global Inbox, find or create a group, and import files. If DEVONthink MCP is unavailable or any of those operations is unsupported, stop and name the missing capability. Do not offer or run a local-only, AppleScript, direct database-package, or skipped-import fallback, even if the user asks to preserve partial progress.
```

Keep the existing local-equivalent fallback only for Codex thread identification and reading; it must not apply to DEVONthink.

- [ ] **Step 3: Add daily group resolution before file generation**

Insert a workflow step after target-thread confirmation:

```markdown
Resolve the daily DEVONthink destination.
- Use the Global Inbox database (`is_inbox: true`). If it is unavailable, stop; do not fall back to another database or ask for another destination.
- Name the group exactly `YYYY-MM-DD Archived Codex Conversations`, using the current local date.
- Search the Global Inbox for that exact group name. Reuse its group UUID when found; create it only when absent.
- Treat the group as resolved only when DEVONthink MCP returns an identifiable group UUID. Use that UUID as `daily_archive_group_uuid` for the rest of the workflow.
```

Renumber later workflow steps without changing their unrelated content.

- [ ] **Step 4: Bind both imports and validation to the same group UUID**

Add these requirements to the import and validation steps:

```markdown
- Import both files with destination `daily_archive_group_uuid`; importing either file into the Global Inbox root or another group is not success.
- Confirm both imported record parents equal `daily_archive_group_uuid` before deleting temporary files.
```

Update the thread archive gate so both records being in that identified group is required.

- [ ] **Step 5: Add common-mistake coverage**

Add rows covering these exact failures:

```markdown
| DEVONthink MCP unavailable but another automation path exists | Stop; DEVONthink MCP has no fallback. |
| Same-day archive group already exists | Reuse its UUID; do not create a duplicate group. |
| One file imported into the Global Inbox root | Treat the workflow as incomplete; both files must be children of the daily group. |
```

- [ ] **Step 6: Run structural checks**

```bash
rg -n "Archived Codex Conversations|daily_archive_group_uuid|hard requirement|local-only|AppleScript|duplicate group|Global Inbox root" archiving-to-devonthink/SKILL.md
git diff --check -- archiving-to-devonthink/SKILL.md
```

Expected: all contract concepts appear and `git diff --check` exits 0.

### Task 3: Add Chinese Codex Interface Metadata

**Files:**
- Create: `archiving-to-devonthink/agents/openai.yaml`

**Interfaces:**
- Consumes: OpenAI skill interface metadata schema used by `archiving-douyin-favorites/agents/openai.yaml`.
- Produces: Chinese display metadata while retaining `$archiving-to-devonthink` in the default prompt.

- [ ] **Step 1: Add a failing existence check**

```bash
test -f archiving-to-devonthink/agents/openai.yaml
```

Expected: exit 1 because the file does not exist.

- [ ] **Step 2: Create the interface metadata**

Create exactly:

```yaml
interface:
  display_name: "归档 Codex 对话"
  short_description: "整理 Codex 对话并归档到 DEVONthink 每日目录"
  default_prompt: "Use $archiving-to-devonthink to archive this Codex conversation into today's reusable DEVONthink Global Inbox folder. Stop if DEVONthink MCP is unavailable."
```

- [ ] **Step 3: Validate the localized metadata**

```bash
test -f archiving-to-devonthink/agents/openai.yaml
rg -n 'display_name: "归档 Codex 对话"|\$archiving-to-devonthink|DEVONthink MCP is unavailable' archiving-to-devonthink/agents/openai.yaml
```

Expected: file check exits 0 and all three patterns match.

### Task 4: GREEN and REFACTOR Pressure Verification

**Files:**
- Read: `archiving-to-devonthink/SKILL.md`
- Read: `archiving-to-devonthink/agents/openai.yaml`

**Interfaces:**
- Consumes: the modified skill and the three baseline scenarios from Task 1.
- Produces: evidence that fresh agents enforce the MCP gate, reuse the daily group, and require both records in the same group.

- [ ] **Step 1: Re-run the three Task 1 scenarios with the modified skill**

Expected results:

```text
MCP unavailable -> stop before file generation; no fallback offered.
Same-day group exists -> reuse its UUID; do not create a duplicate.
One file in Inbox root -> do not delete temp files or archive the Codex thread.
```

- [ ] **Step 2: Run five fresh-context micro-tests for the hard-gate wording**

Use the full modified skill as system context and repeat the MCP failure scenario five times. Manually inspect every answer.

Expected: all five stop before generation and none proposes AppleScript, local-only output, direct database writes, or deferred import.

- [ ] **Step 3: Run five fresh-context micro-tests for the folder wording**

Use the full modified skill as system context and repeat the existing-same-day-folder scenario five times. Manually inspect every answer.

Expected: all five reuse the existing exact-name group and route both Markdown records to its UUID.

- [ ] **Step 4: Close any observed loophole and re-run the affected scenario**

If an answer violates a requirement, add only the smallest explicit counter to `SKILL.md`, then repeat that exact scenario until it complies. Do not change unrelated archive behavior.

- [ ] **Step 5: Run final repository checks**

```bash
git diff --check
git status --short
git diff -- archiving-to-devonthink/SKILL.md archiving-to-devonthink/agents/openai.yaml
```

Expected: no whitespace errors; only the two intended skill files plus pre-existing unrelated user changes are shown.

- [ ] **Step 6: Commit only this skill implementation**

```bash
git add archiving-to-devonthink/SKILL.md archiving-to-devonthink/agents/openai.yaml
git commit -m "feat: archive Codex conversations into daily DEVONthink folder"
```

Do not stage or commit changes under `archiving-douyin-favorites`.
