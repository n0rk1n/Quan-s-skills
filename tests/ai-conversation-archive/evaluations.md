# Conversation archive artifact and SOP checks

## Scope and validation method

The agent identifies conversation deliverables and SOP subjects; Python handles the deterministic operations. Repository instructions prohibit unrequested subagents, so this change uses real script regression tests and a manual contract review, not independent agent pressure runs. Passing script tests does not prove semantic identification or agent compliance.

## Scenarios and acceptance

| Scenario | Required result |
| --- | --- |
| Conversation produced a binary report outside Git | Preserve exact bytes in the daily archive; link it and record size/SHA-256/source/destination |
| Files are tracked, ignored, and untracked in one repository | Skip only tracked files, record their repository; copy ignored and untracked files |
| Candidate resides in a linked worktree | Inspect that worktree index, not the process working directory |
| Two deliverables have the same basename; repeat or run concurrently | Keep every distinct deliverable and prior archive; use exclusive creation and collision suffixes |
| Source missing, directory, symlink, or Git inspection fails | Fail before creating the daily archive; do not infer success or silently omit a candidate |
| Copy fails, source changes, or manifest/read-back is corrupted | Preserve partial output and source; report failure and planned paths; do not close the conversation |
| Only this archiving skill's procedure is reusable | Supply title/scope only; no SOP sections or SOP file; record the exclusion |
| Archive-skill procedure and unrelated report format coexist | Exclude only the archive-skill candidate; save the unrelated SOP |
| No produced files or SOP candidates | Explicit empty arrays; preserve compatibility with old callers that omit them |

## RED / GREEN evidence

- Baseline before changes: the existing 16 archive tests passed.
- Added 10 regression tests before implementation: 26 total tests ran; the new cases produced 17 assertion failures including subtests. The old writer returned no artifact copies, accepted invalid/missing artifact input, did not surface copy failures, and generated both archive-skill and unrelated SOPs.
- Implemented script behavior: all 26 tests passed.
- Added boundary coverage for concurrency, literal Git pathspecs, Git errors, source changes, manifest corruption, scope-only exclusions, linked worktrees, and the real CLI.
- Final verification command: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests`.

## Skill review checklist

- [x] Existing trigger-only description and valid name retained.
- [x] Required `artifacts` and candidate `scope` slots documented in the workflow and input contract.
- [x] Conditional SOP exclusion defined by subject, with mixed-topic behavior explicit.
- [x] Deterministic behavior delegated to the bundled script; model responsibilities stated.
- [x] Existing archive-skill SOP example replaced by an unrelated data-report example.
- [x] Failure handling requires preserving files and keeping the conversation active.
- [x] Script regression tests and CLI scenario executed.
- [ ] Independent agent pressure/micro-tests: not run under the repository's no-unrequested-subagent policy.
- [ ] Merge/push: intentionally left to the user; task branch retained.
