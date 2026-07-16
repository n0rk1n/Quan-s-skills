---
name: delegating-plan-to-local-cli
description: Use when an implementation plan in docs/superpowers or doc/superpower must be carried out by one of several locally installed coding CLIs, and the resulting code needs independent validation and review.
---

# Delegating a Plan to a Local CLI

## Overview

Treat the implementation plan as the acceptance contract. A local CLI's exit code, prose summary, or self-reported tests are evidence—not completion. The CLI may edit only a dedicated linked Git worktree; no code reaches the target branch until both the current model approves the exact reviewed commit and the user explicitly authorizes that merge.

## Workflow

1. Find the plan with `rg --files -g '*.md' | rg '(^|/)(docs?/superpowers?)/'`. If multiple plans match, ask the user to choose; never combine plans implicitly. Obtain an explicit base branch for later integration; never infer it from the current checkout.
2. Discover the available coding CLIs. A CLI explicitly named by the user is their selection for **this run**; do not ask them to select it again. If no CLI was named and `claude` is detected, use Claude Code as the default selection. Ask the user to choose from the detected names and paths plus a custom-command option only when Claude Code is unavailable:

   ```bash
   scripts/list-local-coding-clis.sh
   ```

   For selected CLIs other than Claude Code and Reasonix, record the selected executable and non-interactive arguments as an argv list. Never use `sh -c` or a shell string. If that CLI cannot accept a task on stdin, inspect its `--help` and ask the user to choose a supported invocation or approve a small wrapper before continuing.

   **Claude Code execution profile (default):** Run `claude -p --max-turns 80` through `run-plan-cli.sh`; the helper supplies the required task on stdin and retains the report/transcript. Do not add `--dangerously-skip-permissions` or `--permission-mode bypassPermissions`. If Claude blocks on a permission request, do not silently switch CLIs or widen permissions: ask the user to approve a narrow allow rule or to use an interactive Claude session.

   **Claude Code provider authorization (default):** Selecting this skill's default Claude Code route, or explicitly selecting Claude Code, authorizes its configured external provider to receive the implementation plan and source code needed from the named linked worktree for that run. Do not ask a separate provider-consent question or require a verbatim authorization sentence. This authorization excludes credentials, secrets, private keys, `.env` values, production data, and paths outside the linked worktree; if Claude needs any excluded material, stop and ask for its specific scope approval.

   **Reasonix execution profile (when selected):** If the user named or selected `reasonix`, use its interactive TTY mode, `reasonix chat` (append `--model NAME` only when the user supplied a model). Do not ask a second question about `chat` versus `run`; `reasonix chat` is the default profile for an explicit Reasonix selection. Do not use `reasonix run` as a fallback or retry after an empty/non-reporting run unless the user explicitly requests `run`.

   **Reasonix provider authorization (default):** The user's naming or selection of Reasonix also authorizes its configured external model provider (for example, DeepSeek) to receive the implementation plan and source code needed from the named linked worktree for that run. Do not ask a separate DeepSeek/provider-consent question or require a verbatim authorization sentence. This authorization excludes credentials, secrets, private keys, `.env` values, production data, and paths outside the linked worktree; if Reasonix needs any excluded material, stop and ask for its specific scope approval.
3. Create a dedicated branch and linked worktree before launching the selected CLI. Do not delegate in the primary checkout, even if it is clean:

   ```bash
   scripts/create-plan-worktree.sh --repo /path/to/repo --base main \
     --branch codex/plan-20260715 --worktree /path/to/repo-plan-20260715
   ```

   Record the worktree path, branch, base commit, and `git status --short`. If the source checkout has unrelated work, preserve it; the new worktree starts from the named base ref.
4. Delegate only in that linked worktree. For stdin-driven CLIs, `run-plan-cli.sh` rejects a primary checkout and records the exact chosen command, prompt, baseline, stdout/stderr, and exit status:

   ```bash
   scripts/run-plan-cli.sh --repo /path/to/repo-plan-20260715 \
     --plan /absolute/path/to/docs/superpowers/plan.md -- claude -p --max-turns 80
   ```

   The helper supplies the plan path and requires a structured execution report. It assumes the CLI accepts its task on stdin.

   **For Reasonix, do not invoke `run-plan-cli.sh`:** it pipes a task over stdin, while `reasonix chat` requires a TTY. In the linked worktree, create an evidence directory and launch the default profile through a terminal that supports interactive input:

   ```bash
   evidence_dir=$(mktemp -d "${TMPDIR:-/tmp}/plan-cli.XXXXXX")
   /usr/bin/script -q "$evidence_dir/reasonix-chat.typescript" reasonix chat
   ```

   Send this as the first chat message, replacing the placeholders without changing its constraints:

   ```text
   You are implementing exactly one approved plan in a local Git repository.

   Repository: /absolute/path/to/linked-worktree
   Plan (read it before editing): /absolute/path/to/docs/superpowers/plan.md

   First inspect the plan and repository. Implement every plan step within scope. You may process the plan and source code needed from this linked worktree through Reasonix's configured external provider. Do not read, transmit, print, or change credentials, secrets, private keys, `.env` values, production data, or paths outside this linked worktree. Do not commit, push, change credentials, access production, run destructive data operations, or make unrelated cleanup changes. If a step conflicts with the repository or cannot be completed, leave the code safe and record it as blocked rather than claiming completion.

   Run the most relevant tests/build checks. Before exiting, print a report using this exact shape:

   <plan-execution-report>
   status: complete | partial | blocked
   plan_steps:
     - step: <plan section or checklist item>
       status: implemented | deferred | blocked
       evidence: <files changed and test/behaviour evidence>
   tests:
     - command: <exact command>
       result: pass | fail | not-run
   deviations:
     - <none, or explanation>
   </plan-execution-report>
   ```

   Keep the chat open until the report is visible, then copy the report verbatim to `$evidence_dir/report.md`. The `script` transcript is the execution log. This is a TTY interaction, not an additional user choice; the current model remains responsible for all inspection, validation, and review.
5. Do **not** accept a zero exit code or `status: complete` yet. Inspect `execution.log` for stdin-driven CLIs, or `reasonix-chat.typescript` for Reasonix; also inspect `report.md`, `git diff`, and changed files. Map every plan step to concrete files, behaviour, and test evidence. A missing or malformed report means `partial`: ask the CLI once to emit the required report, then escalate if the evidence still cannot be reconstructed.
6. Run the plan's specified checks. Then select the changed module's documented unit/test/build command from its manifest or README; if none exists, run the smallest command that executes the changed behaviour and record why it was selected. A CLI-provided test transcript is not a substitute for this run.
7. Conduct two independent reviews with the current model:
   - **Plan-compliance review:** compare each step and acceptance criterion against the diff and test evidence.
   - **Code-quality review:** identify correctness, regressions, security/privacy, error handling, migrations/data safety, concurrency, and missing tests. Findings need severity, file/line, impact, and a concrete remedy.
8. If review finds an actionable issue, return the exact findings and failing command output to the CLI for repair, then repeat steps 5–7. Stop and ask the user if a plan conflict, destructive data action, or unresolved high-severity finding remains. Do not silently loop more than twice; report the remaining blocker.
9. When both reviews approve, make one reviewable commit on the worktree branch, then report its full commit ID, base branch, validation output, review verdict, and diff summary. This is the **model approval**; it is not merge authorization.
10. Request an explicit user confirmation naming the exact commit, worktree branch, and destination base branch. Only after that confirmation may the model merge. General approval of the plan, tests, or review is insufficient. If the base branch moved, a merge conflicts, or any code changes after the approval, return to steps 5–9 and request fresh user confirmation.

## Delegation Contract

The CLI must:

- read the plan at the supplied absolute path before editing;
- edit only the named linked worktree and its dedicated branch;
- implement only its stated scope; record every deviation and blocked item;
- avoid commits, pushes, production actions, credentials, secrets, private keys, `.env` values, and unrelated cleanup;
- run relevant tests and finish with a plan-step-to-evidence report.

## Completion Report

Report only after independent verification:

| Field | Required evidence |
|---|---|
| Plan coverage | Every step: implemented / deferred / blocked, with files |
| Validation | Commands and real exit results |
| Review verdict | Approved, or findings grouped by severity |
| Isolation | Worktree path, branch, base commit, and reviewed commit |
| Merge authority | Model approval plus the user's explicit commit-to-base authorization |
| Residual risk | Explicit deviations, skips, and user decisions needed |

## Common Mistakes

| Mistake | Required response |
|---|---|
| `reasonix` exited 0 | Inspect the diff and plan mapping; exit status only means the process ended. |
| CLI says all tests pass | Re-run relevant checks yourself and retain the output. |
| Review finds a problem during a deadline | Classify/reproduce it; do not label work complete while a plausible high-severity issue is open. |
| Dirty worktree | Preserve it; obtain direction or isolate the work before delegation. |
| CLI changed scope | Mark the matching plan step unresolved unless the user explicitly accepts the deviation. |
| CLI was run in the primary checkout | Do not treat it as a valid delegated run; recreate the worktree and run there. |
| No CLI was named and Claude Code is available | Use the default `claude -p --max-turns 80` profile; do not ask a tool-choice question. |
| Claude Code stops on a permission prompt | Keep its narrow permission boundary; ask the user to approve the specific rule or use an interactive Claude session. Never add a dangerous global bypass. |
| Default Claude Code route uses an external provider | Treat this run as scope-limited authorization to send the plan and necessary linked-worktree source code to that configured provider; do not ask a separate provider-consent question. |
| User explicitly named Reasonix | Treat that as this run's CLI selection; use the default `reasonix chat` profile without a second chat-mode question. |
| User explicitly named Reasonix and its provider is external | Treat that as scope-limited authorization to send the plan and necessary linked-worktree source code to that configured provider; do not ask a separate DeepSeek/provider-consent question. |
| `reasonix run` exited 0 but emitted no report | Do not retry it through the stdin helper; launch the default `reasonix chat` profile in a TTY and retain its transcript. |
| `reasonix chat` was passed to `run-plan-cli.sh` | Stop that invocation; the helper pipes stdin and is incompatible with the TTY chat UI. Launch `reasonix chat` directly in the linked worktree. |
| Custom CLI command is a shell snippet | Ask for an executable plus arguments; never evaluate it with a shell. |
| Model approved the code | Prepare the commit and request the user's explicit authorization; never merge on model approval alone. |

## Red Flags — Stop Completion Claims

- No plan-step-to-evidence mapping
- Only a prose CLI summary or an exit code
- Tests were not independently run
- Review findings have not been addressed or explicitly accepted
- The CLI committed, pushed, touched secrets, or performed a production/data action
- The CLI is not in a linked worktree
- A CLI was selected without this user's explicit choice for the run
- Claude Code is available but the model asks the user to choose a CLI, widens permissions, or asks again for provider consent
- Reasonix was explicitly named but the model asks the user to choose `chat` or retries silent `run`
- Reasonix was explicitly named but the model asks again for provider consent, or sends excluded material to its provider
- The user has not explicitly approved the named commit into the named base branch
