---
name: archiving-bilibili-following
description: Use when the user explicitly names or invokes this skill to archive a signed-in Bilibili following list to Downloads.
---

# Archiving Bilibili Following

Archive exactly one bounded batch of 24 accounts from the current Bilibili
following page, verify the archive, then unfollow only those same accounts.

## Required Capabilities

Before observing following records, map the current host's tools to both:

- authenticated browser automation that can inspect the signed-in Bilibili
  following list, identify accounts by stable UID and canonical space URL,
  operate each account's followed-state control, reload the starting page, and
  read the following count; and
- writable local filesystem access to `~/Downloads/`, UTF-8/JSON read-back,
  and image download and MIME verification (Python 3.10+, `curl`, and `file`).

If either capability is unavailable, stop before observing following records
and do not offer a reduced fallback. Never attempt to bypass login, CAPTCHA,
access controls, rate limits, or other platform safeguards.

## Mandatory Workflow

Read [references/workflow.md](references/workflow.md) completely before
observing the list.

The safety order is:

1. Verify Downloads, image download, and authenticated browser capabilities.
2. Prepare the observed JSON for a fresh `YYYY-MM-DD Archived Bilibili Following Batch NN` batch.
3. Observe exactly 24 accounts from the current page in its visible order,
   using stable UID and `https://space.bilibili.com/<UID>` identity.
4. Create fresh Downloads directory via the bundled script, save and read back 24 one-to-one local records and downloaded avatar images.
5. Unfollow only the exact archived UIDs.
6. Verify each immediate state change, reload the starting page, and confirm
   the following count decreased by 24.
7. Update local record statuses and create a same-folder Chinese Markdown summary.

One invocation processes exactly one bounded batch of 24. If the current page
contains fewer than 24 accounts with stable UID and canonical URL, stop and
report the shortfall; do not continue to another page, fill the quota, or
perform any destructive action.

Explicit invocation authorizes unfollowing the exact 24 accounts only after the
archive gate passes. Do not ask for a second confirmation. Stop immediately if
the user asks to stop, and never begin another batch in the same invocation.

## Scripted Local Archive

Use the bundled `scripts/archive_bilibili.py` for all local archive writes,
image downloads, retries, verification, and status/summary updates. Read
[references/script-usage.md](references/script-usage.md) for the JSON contract
and commands. Do not rewrite these operations ad hoc.

Run `preflight` before observing the list. The browser supplies observed JSON;
`archive` creates the batch only after validating it. Immediately before any
account cleanup, run `verify` and require exit code 0, `cleanup_ready: true`,
and `verified_ids` equal to the entire fixed browser batch. Target only
`remaining_ids`, further narrowed by fresh browser observations. Failed commands
return no cleanup targets. The script never performs or independently verifies
an unfavorite/unfollow action; supply browser evidence to `update` after each
verified action or retry, stopping if persistence fails.

## Completion

Report the absolute Downloads batch path, 24 verified records and avatar images, `summary.md`, removed UIDs, and unresolved UIDs. Each item contains `record.md` and a real local avatar image. Storing only an avatar URL does not pass the archive gate. If any image fails, retain partial files and stop before unfollowing anything.
