---
name: archiving-douyin-favorites
description: Use when explicitly invoked for a signed-in user's Douyin favorites, especially when the user wants preserved original URLs, local page links, structured detail files, or controlled cleanup.
---

# Archiving Douyin Favorites

## Manual-Only Operation

Run this Skill only when the user explicitly names or invokes this skill through the current host. Do not require a particular invocation syntax.

## Required Capabilities

- authenticated browser automation that can inspect and operate the signed-in Douyin session, match stable content IDs, inspect the final dialog, reload, and perform delayed verification;
- a writable local filesystem that can create and verify files under `/Users/oriki/Downloads`.

Map the current host's tools to these semantic capabilities before observing favorites. Stop before observing favorites if either capability is unavailable; do not archive to a repository, Desktop, temporary directory, cloud drive, or another substitute destination.

Before observing or acting on favorites, read [references/workflow.md](references/workflow.md) completely and follow every checklist item.

## Safety Invariant

Preserve this order without exception:

`verify browser and Downloads access → prepare dated folder → observe → write local archive → verify local archive → unfavorite exact archived IDs → delayed verify`

Each invocation archives 24 favorites by default unless the user explicitly names a different count. The destination is exactly `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`, using the current local date. Reuse that day's folder when it already exists, while preventing duplicate or unrelated-file overwrites as defined in the workflow.

Deadline pressure, cached page state, or assumed reconstructability never permits unfavoriting before the current batch has a one-to-one verified local archive. Treat archived content IDs, not card positions, visible order, or broad selection, as the only destructive-action target.

Once the archive is verified, only unfavorite the exact archived ID set from that verified batch. Never extend cleanup to an ID outside the verified local archive. If delayed verification already shows an archived ID absent, do not submit another unfavorite action for it.

Stop immediately when the user says not to continue. Preserve completed archive files, report exact verified and unresolved IDs, and do not collect another batch unless the user explicitly invokes the Skill again.
