# Bilibili Downloads scripting implementation plan

Goal: Make the agreed Downloads archive workflow executable without automating account actions in a shell script.
Architecture: Each independently installable skill bundles an identical Python CLI; the containing skill selects favorites or following. Python standard library plus curl and file handle persistent artifacts. Browser automation supplies observed JSON and verified cleanup evidence.
Spec: The two Bilibili SKILL.md files and references/workflow.md, plus the user's approved browser/script split in this task.
Execution: Inline in this isolated worktree; no subagents, merge, push, or live account actions.

## Interfaces and constraints

- `preflight`: check ~/Downloads read/write and curl/file availability.
- `archive --input JSON`: validate fixed identities/counts, allocate dated sequential directory, download images, write manifest/records/summary, read back. Favorites 1–40; following exactly 24. Short favorites require `end_confirmed: true`.
- `verify --batch PATH`: read-only complete verification; return cleanup_ready, verified_ids, remaining_ids, failed items. Failure returns no cleanup targets.
- `resume --batch PATH`: retry failed images only, preserving the original batch, with an exclusive mutation lock. Do not resume after cleanup begins.
- `update --batch PATH --input JSON`: accept only existing IDs, removed/unresolved statuses and nonempty browser evidence, preserve removed identities, update records/manifest/summary atomically per file and verify consistency.
- Validate canonical URLs, safe stable ID paths, image MIME and SHA-256, no symlink escape or overwrite of other batches. Never claim account state was verified by the script.
- Identical script copies preserve independent skill installation; test equality to prevent drift.

## Steps

- [x] Add behavior tests in tests/test_bilibili_archive_script.py and run red: valid archive, invalid counts/IDs, image failure, collision, corruption, retry, status update, symlink and standalone CLI.
- [x] Implement scripts/archive_bilibili.py in both skill directories. Use subprocess argument arrays for curl with timeouts, bounded retries, MIME checking and exact-host TLS fallback; return structured JSON on failure.
- [x] Update skill entry points and add references/script-usage.md with input schemas, commands and the browser cleanup gate.
- [x] Run behavioral tests, existing portability/batch checks, inspect diff, then commit only this task's changes.

Validation: 15 behavioral/integration tests and 39 existing portability tests, plus variable-batch and git diff checks. Integration uses a disposable localhost HTTP server and synthetic images; no live Bilibili account is accessed.
