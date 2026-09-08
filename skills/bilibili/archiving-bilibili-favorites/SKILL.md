---
name: archiving-bilibili-favorites
description: Use when explicitly invoked to archive a signed-in user's Bilibili favorites to Downloads in one bounded batch of up to 40.
---

# Archiving Bilibili Favorites

## Manual-Only Operation

Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax.

## Required Capabilities

- authenticated browser automation for the signed-in Bilibili session, BV ID/URL matching, dialog inspection, reload, and removal verification.
- writable local filesystem access to `~/Downloads/`, UTF-8/JSON read-back, and image download and MIME verification (`curl` and `file`, or equivalent host capabilities).

Map the current host's tools to these semantic capabilities before observing favorites. Stop before observing favorites if either required capability is unavailable; do not offer a reduced fallback.

Never attempt to bypass login, CAPTCHA, access controls, rate limits, or platform safeguards. If the session is unavailable or blocked by a challenge, stop and report it.

Before observing or acting on favorites, read [references/workflow.md](references/workflow.md) completely and follow every checklist item.

## Safety Invariant

Preserve this order without exception:

`verify Downloads and image capabilities → create fresh Downloads directory → determine batch_size → save batch_size records and cover images → read back and verify one-to-one mapping → select exact BV IDs → verify confirmation dialog count → cancel → reload and verify → write Chinese summary`

Set `batch_size = min(40, available_stable_items)`, where `available_stable_items` is the number of unique, stable BV ID/canonical URL pairs in the current favorites folder after reaching either 40 pairs or the confirmed end of the folder. If `batch_size` is 1–39, continue with all currently available stable items. If it is 0, stop without changing Bilibili. Never expand scope or use unstable cards to fill the batch.

Each invocation archives one bounded batch of up to 40 favorites. Use the `~/Downloads/` folder `YYYY-MM-DD Archived Bilibili Favorites Batch NN`, with the current local date and next sequential NN.

Deadline pressure, cached page state, or assumed reconstructability never permits canceling before a one-to-one local record and downloaded cover image archive for the batch is written and verified. The same-folder summary is still required for completion, but it is not a gate before cleanup. Treat archived BV IDs, not card positions or visible order, as the only destructive-action target.

Once the local archive is verified, only cancel the exact BV IDs from that verified batch. Never extend cleanup to an ID outside the verified local archive. If delayed verification already shows an archived BV ID absent, do not submit another unfavorite action for it.

Stop immediately when the user says not to continue. Preserve completed archive work, report exact verified and unresolved IDs, and do not collect another batch unless the user explicitly invokes the Skill again.

## Completion

Report the absolute Downloads batch path, `batch_size` record count, verified cover count, `summary.md`, verified removed IDs/URLs, and unresolved IDs. Each item contains `record.md` and a real local cover image; storing only an image URL does not pass the archive gate. If any image fails, retain partial files and stop before unfavoriting anything.
