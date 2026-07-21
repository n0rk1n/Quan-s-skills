# Codex Global Superpowers Lite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply the approved Superpowers Lite policy globally on this Mac while preserving all unrelated Codex settings.

**Architecture:** Add three exact `[[skills.config]]` disable entries to the existing Codex TOML and install a global `AGENTS.md` policy that routes remaining Superpowers skills by task risk. Build and validate candidate files first, back up the current global files, then install and verify byte-for-byte.

**Tech Stack:** TOML, Markdown, Codex global configuration, Python 3.12 `tomllib`, POSIX `cmp` and `install`

## Global Constraints

- Disable only `using-superpowers`, `dispatching-parallel-agents`, and `subagent-driven-development`.
- Preserve every existing setting in `~/.codex/config.toml`.
- Keep all other Superpowers skills available for explicit or risk-based use.
- Do not enable default subagent or parallel-agent behavior.
- Back up global files before installation.
- Treat restart-time behavior as unverified until Codex is restarted and a new task is opened.

---

### Task 1: Build and statically validate candidate files

**Files:**
- Read: `/Users/oriki/.codex/config.toml`
- Read: `/Users/oriki/.codex/AGENTS.md`
- Create: `/private/tmp/codex-superpowers-lite/config.toml`
- Create: `/private/tmp/codex-superpowers-lite/AGENTS.md`

**Interfaces:**
- Consumes: the current global Codex configuration and the installed Superpowers 6.1.1 Skill paths.
- Produces: two reviewed candidate files ready for installation.

- [x] **Step 1: Create the candidate TOML**

Copy the current `/Users/oriki/.codex/config.toml` unchanged, then append these exact entries:

```toml
[[skills.config]]
path = "/Users/oriki/.codex/plugins/cache/openai-curated-remote/superpowers/6.1.1/skills/using-superpowers/SKILL.md"
enabled = false

[[skills.config]]
path = "/Users/oriki/.codex/plugins/cache/openai-curated-remote/superpowers/6.1.1/skills/dispatching-parallel-agents/SKILL.md"
enabled = false

[[skills.config]]
path = "/Users/oriki/.codex/plugins/cache/openai-curated-remote/superpowers/6.1.1/skills/subagent-driven-development/SKILL.md"
enabled = false
```

- [x] **Step 2: Create the candidate global policy**

Write `/private/tmp/codex-superpowers-lite/AGENTS.md` with this exact policy:

```markdown
# Superpowers Lite

Treat Superpowers as an on-demand engineering toolbox, not a mandatory workflow for every task.

- Handle ordinary questions, explanations, read-only inspection, simple configuration, and small localized edits directly.
- Use `superpowers:systematic-debugging` for an actual bug, test failure, or unexpected behavior before proposing a fix.
- After changing code or configuration, use `superpowers:verification-before-completion` and obtain fresh evidence before claiming completion.
- Use `superpowers:brainstorming`, `superpowers:test-driven-development`, `superpowers:writing-plans`, and `superpowers:using-git-worktrees` only when the task is complex, high-risk, spans multiple components, or the user explicitly requests the workflow.
- Use subagents or parallel agents only when the user explicitly requests them.
- A `MUST` or `ALWAYS` inside a Superpowers skill does not by itself escalate a lightweight task into a full engineering workflow.
- The user's explicit instruction for the current task takes precedence. If the user asks for a quick treatment or asks not to use Superpowers, comply while preserving necessary safety and verification.
```

- [x] **Step 3: Validate TOML syntax and exact disabled paths**

Run a Python 3.12 script using `tomllib` that loads the candidate and asserts that the disabled Superpowers path set equals the three paths above.

Expected: exit code 0 and output `candidate TOML valid: 3 expected disabled skills`.

- [x] **Step 4: Review candidate differences**

Run:

```bash
diff -u /Users/oriki/.codex/config.toml /private/tmp/codex-superpowers-lite/config.toml
diff -u /Users/oriki/.codex/AGENTS.md /private/tmp/codex-superpowers-lite/AGENTS.md
```

Expected: the TOML diff contains only the three appended disable entries; the `AGENTS.md` diff contains only the approved Lite policy.

### Task 2: Back up and install the global configuration

**Files:**
- Create: `/private/tmp/codex-superpowers-lite-backup/config.toml`
- Create: `/private/tmp/codex-superpowers-lite-backup/AGENTS.md`
- Modify: `/Users/oriki/.codex/config.toml`
- Modify: `/Users/oriki/.codex/AGENTS.md`

**Interfaces:**
- Consumes: validated candidates from Task 1.
- Produces: installed global Codex configuration plus a recoverable backup.

- [x] **Step 1: Back up current global files**

Create `/private/tmp/codex-superpowers-lite-backup`, then copy the current `config.toml` and `AGENTS.md` into it without modifying their contents.

Expected: `cmp` confirms both backups are identical to their sources before installation.

- [x] **Step 2: Install both candidates**

Use `install -m 600` for `config.toml` and `install -m 644` for `AGENTS.md`.

Expected: both commands exit 0; no other file under `/Users/oriki/.codex` is modified by this task.

### Task 3: Verify the installed state and record the restart boundary

**Files:**
- Read: `/Users/oriki/.codex/config.toml`
- Read: `/Users/oriki/.codex/AGENTS.md`
- Modify: `docs/superpowers/plans/2026-07-21-codex-global-superpowers-lite.md`

**Interfaces:**
- Consumes: installed global files from Task 2.
- Produces: fresh static verification evidence and checked plan steps.

- [x] **Step 1: Re-parse the installed TOML**

Run the same Python 3.12 assertion against `/Users/oriki/.codex/config.toml`.

Expected: exit code 0 and output `installed TOML valid: 3 expected disabled skills`.

- [x] **Step 2: Compare installed files with candidates**

Run `cmp` for both candidate/installed pairs.

Expected: exit code 0 for both comparisons.

- [x] **Step 3: Confirm the Codex CLI accepts the configuration**

Run `/Applications/ChatGPT.app/Contents/Resources/codex --version`.

Expected: exit code 0 and a Codex version string.

- [x] **Step 4: Verify repository hygiene**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; repository changes are limited to this implementation plan before its commit.

- [x] **Step 5: Mark completed checkboxes and commit the plan**

Update only completed steps from `- [ ]` to `- [x]`, then commit this plan separately:

```bash
git add docs/superpowers/plans/2026-07-21-codex-global-superpowers-lite.md
git commit -m "docs: record Superpowers Lite implementation"
```

Expected: the commit contains only the implementation plan.

- [x] **Step 6: Report the dynamic verification boundary**

State explicitly that static installation is verified, but Skill availability and routing behavior require restarting Codex and opening a new task. Do not claim those dynamic checks have passed in the current task.
