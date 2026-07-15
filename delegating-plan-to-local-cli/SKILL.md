---
name: delegating-plan-to-local-cli
description: Use when an implementation plan in docs/superpowers or doc/superpower must be carried out by one of several locally installed coding CLIs, and the resulting code needs independent validation and review.
---

# Delegating a Plan to a Local CLI

## Overview

Treat the implementation plan as the acceptance contract. A local CLI's exit code, prose summary, or self-reported tests are evidence—not completion. The CLI may edit only a dedicated linked Git worktree; no code reaches the target branch until both the current model approves the exact reviewed commit and the user explicitly authorizes that merge.

## Workflow

1. Find the plan with `rg --files -g '*.md' | rg '(^|/)(docs?/superpowers?)/'`. If multiple plans match, ask the user to choose; never combine plans implicitly. Obtain an explicit base branch for later integration; never infer it from the current checkout.
2. Discover the available coding CLIs, then ask the user to select one for **this run**:

   ```bash
   scripts/list-local-coding-clis.sh
   ```

   Present the detected names and paths plus a custom-command option. Do not default to Reasonix, a prior selection, or the fastest-looking CLI. Record the user-selected executable and non-interactive arguments as an argv list (for example, `reasonix run --max-steps 80` or `claude -p`). Never use `sh -c` or a shell string. If the selected CLI cannot accept a task on stdin, inspect its `--help` and ask the user to choose a supported invocation or approve a small wrapper before continuing.
3. Create a dedicated branch and linked worktree before launching the selected CLI. Do not delegate in the primary checkout, even if it is clean:

   ```bash
   scripts/create-plan-worktree.sh --repo /path/to/repo --base main \
     --branch codex/plan-20260715 --worktree /path/to/repo-plan-20260715
   ```

   Record the worktree path, branch, base commit, and `git status --short`. If the source checkout has unrelated work, preserve it; the new worktree starts from the named base ref.
4. Delegate only in that linked worktree. `run-plan-cli.sh` rejects a primary checkout and records the exact chosen command, prompt, baseline, stdout/stderr, and exit status. For example, if the user selected Reasonix:

   ```bash
   scripts/run-plan-cli.sh --repo /path/to/repo-plan-20260715 \
     --plan /absolute/path/to/docs/superpowers/plan.md -- reasonix run --max-steps 80
   ```

   The helper supplies the plan path and requires a structured execution report. It assumes the CLI accepts its task on stdin; use a small local wrapper for a CLI that does not.
5. Do **not** accept a zero exit code or `status: complete` yet. Inspect `execution.log`, `report.md`, `git diff`, and changed files. Map every plan step to concrete files, behaviour, and test evidence. A missing or malformed report means `partial`: ask the CLI once to emit the required report, then escalate if the evidence still cannot be reconstructed.
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
- avoid commits, pushes, production actions, credentials, and unrelated cleanup;
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
| Reasonix was selected before | Rediscover options and ask the user to select a CLI for this run. |
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
- The user has not explicitly approved the named commit into the named base branch
