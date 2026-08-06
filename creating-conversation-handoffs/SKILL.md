---
name: creating-conversation-handoffs
description: Use when a long-running conversation is nearing context limits, has been compacted, is losing earlier facts, or must continue in a new conversation.
---

# Creating Conversation Handoffs

Create a durable, self-contained Markdown continuation point without treating
the handoff as a transcript or as proof that mutable state is still current.

## Invocation Gate

When context-risk symptoms are visible, recommend this Skill and stop. Signals
include host-reported compaction, a long unfinished task, unreliable recall of
earlier confirmed facts, preparation for a new conversation, or costly
uncommitted and external state.

Do not write a handoff until the user explicitly invokes or confirms this
Skill. Never claim an exact context-use percentage.

## Required Inputs

1. Resolve the current project or task worktree and obey all injected project,
   Git, and worktree instructions. Default to `<root>/oriki-handoffs/`. Create the
   directory when it does not exist. Existing `<root>/.codex/handoffs/` snapshots
   remain readable through the resume skill but do not change this publishing path.
   Ask for a root only when it is genuinely ambiguous or unwritable. Never infer the project root from `SKILL_DIR`
   or from the location of this Skill, its template, or its validator.
2. If `LATEST.md` exists, resolve only a relative target inside the same
   handoff directory and validate both index and snapshot before using them.
   Preserve malformed or untrusted existing content and report the problem.
3. Obtain the exact source conversation reference from available task, thread,
   session context, or session lookup. For new snapshots, use
   `<host>:<conversation-id>` (for example, `opencode:session-123`); retain a
   legacy UUID unchanged when continuing an older snapshot. If unavailable, record
   a concrete reason such as `不可用：当前宿主未提供会话标识`; never invent an identifier. The
   metadata value must start with `不可用：` and must not carry a fact-state prefix
   when no real reference is available.
4. Gather the current conversation plus relevant live evidence. Recheck
   mutable Git, file, test, deployment, CI, permission, connection, and
   external state in proportion to its effect on the next action.

## Fact Contract

Use `references/handoff-template.md` and replace every token.

- Produce one self-contained snapshot: merge still-valid prior facts with all
  current changes. A second handoff must never contain only a delta.
- Use exactly `已验证`, `用户确认`, or `待核实` for every fact. Give evidence or
  a last-verified time for mutable facts; keep inference as `待核实`.
- Distinguish focused tests, full suites, baseline failures, commits, merges,
  pushes, deployments, and external execution.
- State one concrete `首个可执行步骤` and preserve the ordered follow-up work.
- Keep only continuation-relevant material. Exclude secrets, tokens,
  passwords, cookies, credentials, unnecessary personal identifiers, private
  reasoning, and unfiltered logs or tool output. Record a variable name or safe
  source location instead of a secret value. Do not emit credential-shaped assignment examples,
  even when their values look like placeholders; describe the source in prose.
- Include the real source conversation reference so a new conversation can look up the source
  only if missing detail later blocks progress.

## Publish Workflow

Let `SKILL_DIR` be this Skill directory and `HANDOFF_DIR` the resolved
`<root>/oriki-handoffs/` directory.

If publication tools or file writes are unavailable but the user explicitly
asks for handoff content, return a complete candidate snapshot using every template section.
Fill unavailable facts with concrete reasons, label it as unvalidated and unpublished,
and do not invent a path or claim that `LATEST.md` changed.

1. Generate a local-time `YYYY-MM-DD-HHmm` value and a lowercase safe topic
   slug. Run:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_handoff.py" next-path \
     "$HANDOFF_DIR" --timestamp "<timestamp>" --topic "<topic-slug>"
   ```

2. Write the fully rendered candidate snapshot in a safe temporary directory.
   Semantically review its completeness, evidence labels, source-reference provenance, and
   sensitive information.
3. Run `validate the candidate snapshot` with:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_handoff.py" snapshot "<candidate>"
   ```

   Fix every error and revalidate. Confirm the selected final path still does
   not exist.
4. Atomically `publish the timestamped snapshot` to the selected path without
   overwriting any existing snapshot.
5. In the handoff directory, render a temporary candidate `LATEST.md` whose
   link is the new snapshot's filename. Then validate the candidate `LATEST.md`
   with:

   ```sh
   python3 "$SKILL_DIR/scripts/validate_handoff.py" latest "<candidate-latest>"
   ```

6. Only after both validations succeed, atomically `replace `LATEST.md`` with
   the validated candidate. If any step fails, keep the previous valid index
   unchanged and report the exact published or unpublished state.

## Completion Report

Return the published snapshot's real absolute path and a copyable prompt with
that exact path substituted:

```text
请使用 resuming-from-conversation-handoff 读取 {{snapshot_absolute_path}}，复核易变化事实，然后从首个可执行步骤继续任务。
```

Replace `{{snapshot_absolute_path}}` before showing the prompt. Report
validation results and whether `LATEST.md` was updated.

Then remind the user that, after the new conversation resumes successfully,
they may manually invoke `archiving-to-devonthink` for the old conversation.
Do not invoke or load `archiving-to-devonthink`, and do not archive, close, or
delete the source conversation.

## Common Mistakes

- Writing a one-paragraph or delta-only handoff under deadline pressure.
- Treating old Git, test, deployment, or external state as current evidence.
- Inventing a plausible source reference or retaining a pasted credential.
- Publishing before validation or replacing the last valid index after a
  partial failure.
- Claiming success without an absolute snapshot path and validated index.
