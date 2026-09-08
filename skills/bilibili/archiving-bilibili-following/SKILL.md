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
  and image download and MIME verification (`curl` and `file`, or equivalent host capabilities).

If either capability is unavailable, stop before observing following records
and do not offer a reduced fallback. Never attempt to bypass login, CAPTCHA,
access controls, rate limits, or other platform safeguards.

## Mandatory Workflow

Read [references/workflow.md](references/workflow.md) completely before
observing the list.

The safety order is:

1. Verify Downloads, image download, and authenticated browser capabilities.
2. Create fresh Downloads directory `YYYY-MM-DD Archived Bilibili Following Batch NN`.
3. Observe exactly 24 accounts from the current page in its visible order,
   using stable UID and `https://space.bilibili.com/<UID>` identity.
4. Create and read back 24 one-to-one local records and downloaded avatar images.
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

## Completion

Report the absolute Downloads batch path, 24 verified records and avatar images, `summary.md`, removed UIDs, and unresolved UIDs. Each item contains `record.md` and a real local avatar image. Storing only an avatar URL does not pass the archive gate. If any image fails, retain partial files and stop before unfollowing anything.
