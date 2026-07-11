# Douyin Favorites Archive Workflow

## Workflow Checklist

1. Confirm the Skill was explicitly invoked, a signed-in browser is available, and the DEVONthink MCP server is usable. If DEVONthink MCP is missing or cannot operate, stop; do not offer or run a reduced local-only workflow.
2. Use DEVONthink MCP tools to locate the Global Inbox database, then create a fresh invocation folder named exactly `YYYY-MM-DD Archived DouYin Favorites`, where `YYYY-MM-DD` is the current local date.
3. Use a default batch size of 24 unless the user explicitly specifies another size. Observe only that bounded batch and record stable content IDs, canonical URLs, visible facts, and topic labels.
4. Create or update one DEVONthink bookmark record per favorite in the dated Inbox folder before any destructive action.
5. Verify bookmark count, ID count, canonical-URL count, unique URL count, record comments, tags, and one-to-one ID/URL mapping.
6. If cleanup is requested, select only the verified archived IDs, inspect Douyin's final confirmation dialog, and submit only if its displayed scope and count match the current submission ID set.
7. Reload, wait for lazy loading, and verify every archived ID submitted for cleanup.
8. Create a Chinese Markdown summary record in the same DEVONthink folder and verify it is present.
9. Report DEVONthink destination, archived bookmark count, summary record, verified removals, and unresolved IDs. Stop if requested.

Never reorder these gates: `verify DEVONthink MCP → create fresh Inbox group → observe → create bookmarks → verify bookmarks → select exact archived IDs → inspect dialog → unfavorite → delayed verify → write Chinese summary → verify summary`.

## DEVONthink Setup

Use only DEVONthink MCP tools such as `mcp__devonthink.get_databases`, `mcp__devonthink.get_record_children`, `mcp__devonthink.lookup_records`, `mcp__devonthink.create_record`, `mcp__devonthink.update_record`, and `mcp__devonthink.set_record_tags`.

Before reading Douyin favorites, confirm that DEVONthink MCP can list databases and that one available database has `is_inbox: true`. Use that Global Inbox database. If no writable Global Inbox is exposed, stop and report the blocker.

Create a fresh destination group with:

```text
<current local date YYYY-MM-DD> Archived DouYin Favorites
```

The English phrase is fixed: `Archived DouYin Favorites`. Do not translate it differently, add time of day, or create a per-batch suffix. Do not reuse an existing same-day group from a prior invocation.

Do not use `create_group_path` for this dated invocation group because that operation can behave like `mkdir -p` and return an existing group. Instead:

1. List existing Global Inbox children with DEVONthink MCP before creation.
2. If a group with the exact destination name already exists, stop and report that a fresh exact-name folder cannot be created safely.
3. Create the group with `mcp__devonthink.create_record` using `type: "group"` and the exact destination name.
4. Verify the returned UUID was not present in the pre-creation same-name set.
5. Use the returned group UUID as this invocation's destination and verification scope.

If DEVONthink refuses to create the exact-name group or returns an existing UUID, stop and report the blocker rather than reusing the old group or inventing a different folder name.

Do not write inside `.dtBase2`, `.dtSparse`, or `.dtArchive` packages. Do not use Finder, AppleScript, browser bookmarks, filesystem folders, or local Markdown files as a fallback. If DEVONthink MCP cannot create records or verify records in the destination group, stop.

## Collecting a Batch

Use a batch size of 24 by default unless the user specifies another size; reduce it only when the page state cannot expose that many stable content IDs reliably. Record each card's stable content ID, content type (`video` or `note`), canonical URL, visible title/caption/author, visible facts, and 1-5 content tags grounded in the item. Do not identify a destructive target by card position, visible order, “first N,” or a broad page selection.

Do not bypass login, CAPTCHA, access controls, rate limits, or platform safeguards. Stop if the session or page state is not trustworthy. Do not pre-read another batch after the user asks to stop.

## Bookmark Contract

Each favorite becomes exactly one DEVONthink bookmark record in the dated Inbox folder:

```text
type: bookmark
name: <concise title based on the favorite's main content>
url: https://www.douyin.com/video/<id> or https://www.douyin.com/note/<id>
comment: <content details, source metadata, evidence limits, and useful context>
tags: [DouYin, DouYin Favorites, <main content tags>]
destination: <YYYY-MM-DD Archived DouYin Favorites group>
```

The bookmark name must be based on the video's main content, not only the author, ID, index, or generic text such as `DouYin Favorite 01`. Keep names concise and filesystem-safe enough for DEVONthink display. If the visible content is sparse, use the best visible label plus the content ID suffix, and mark missing source fields in the comment.

The URL must be either `https://www.douyin.com/video/<id>` or `https://www.douyin.com/note/<id>` and its `<id>` must match the archived content ID. Preserve the original Douyin link as the canonical URL; do not replace it with a search result, short link, author page, or reconstructed noncanonical URL.

Before creating a bookmark, use `lookup_records` by URL to identify prior archives. Because each invocation uses a fresh group, do not update older records from another group as this run's output. If the same URL already exists in this invocation's fresh group, update that record's name, comment, URL, and tags instead of creating a duplicate. If the same URL exists elsewhere, create the fresh-group archive record unless the user explicitly asks to reuse or move older records.

Use the DEVONthink record comment field as the Finder Comment equivalent. The comment should include:

- content ID and content type;
- canonical URL;
- visible author, title, caption, and source facts;
- a factual summary grounded only in visible material;
- reusable takeaways or interpretation clearly labeled as inference;
- missing fields labeled `insufficient metadata`;
- caution for medical, financial, benchmark, income, popularity, or product claims; and
- archive status such as `archived; pending unfavorite`, `complete`, or `partial/unresolved`.

Tags should describe the main content topics, not implementation status alone. Use stable tags such as `DouYin` and `DouYin Favorites`, then add concise topical tags from visible content. Do not invent tags from invisible content.

After creating or updating records, verify the dated folder contains one bookmark per archived favorite and that every expected canonical URL is present exactly once. Verify comments and tags from DEVONthink's returned properties or follow-up reads when available.

Label visible facts as facts. Clearly mark any synthesis, takeaway, interpretation, or inferred context as inference, and do not invent missing details. Add explicit caution rather than endorsement when recording medical, financial, benchmark, income, popularity, or product claims; visible engagement counts and creator assertions are not independent verification.

Before any destructive action, count bookmark records, archived IDs, canonical URLs, unique IDs, and unique canonical URLs. All counts must equal the batch size, and every ID and canonical URL must map one-to-one. Correct any mismatch before proceeding.

## Summary Markdown Record

After bookmark verification and any requested cleanup attempt, use `mcp__devonthink.create_record` with `type: "markdown"` to create one Markdown record in the same DEVONthink folder. The summary file name and body must be written in Simplified Chinese by default. Preserve fixed identifiers such as DouYin, DEVONthink, UUIDs, canonical URLs, and tag strings exactly when needed. Keep content IDs for verification, record comments, unresolved notes, and exact cleanup matching, but do not expose them as a separate column in the archived-favorites list.

Use a Chinese record name like:

```text
YYYY-MM-DD DouYin 收藏归档总结.md
```

The summary record must include these sections in Chinese:

- destination folder name and DEVONthink database;
- processing status and batch size;
- evidence limitations, including what was and was not visible;
- cross-item synthesis grouped by topic;
- a table or list of all archived favorites with bookmark name, canonical URL, author, tags, and one-line summary;
- unresolved metadata or failed record operations, if any; and
- cleanup status if unfavoriting was requested.

All headings, synthesis, evidence-limit notes, processing status, table labels, one-line summaries, unresolved-metadata notes, and cleanup status must be Chinese. Do not write the summary in English merely because some source terms, tool names, URLs, or tags are English.

Do not include a `内容 ID` or `Content ID` column in the archived-favorites table/list. If an item has sparse metadata or later needs cleanup, mention its content ID only in verification, unresolved-metadata notes, record comments, or exact cleanup notes.

Verify the summary record exists in the same destination group and that its content covers every archived bookmark before reporting completion. At minimum, verify summary item count, content ID count, canonical URL count, unique canonical URL count, tag coverage, Chinese-language summary text, processing status, cleanup status, and unresolved/sparse metadata notes against the bookmark archive. A cross-item synthesis inside comments or chat is not a substitute for this Markdown record.

## Cleanup Gate

After the DEVONthink bookmark archive passes its checks, cleanup may proceed for that batch without waiting for the same-folder summary. A bookmark is considered archived only when the DEVONthink record exists in the invocation folder, its URL matches the content ID, its comment carries the content ID and useful context, and its tags are present.

Cleanup scope is the verified archived ID set from the current invocation. Do not ask for an extra confirmation solely because the cleanup step is destructive, but do stop if the user says not to continue. A later batch or newly observed ID requires its own bookmark archive and verification before it can be unfavorited.

## Exact-ID Unfavorite Procedure

Set `archived_ids` to the IDs whose DEVONthink bookmark records passed verification in the current invocation. For the initial submit, set `submission_ids = archived_ids`. For each partial-success retry, set `submission_ids = remaining_ids`. Require `submission_ids` to be a subset of `archived_ids`; never add an ID outside the verified bookmark archive.

Locate and select items by matching `submission_ids`, never by card index or position. Require the UI-selected ID set to equal `submission_ids` for that submit; stop on any extra or missing ID.

Before the final destructive submit, inspect Douyin's confirmation dialog. Verify that its displayed destructive scope and count match the current `submission_ids`; if the dialog exposes item identifiers, verify those identifiers too. Abort before final submission on any mismatch, extra item, unverifiable scope, or unexpected count. Do not treat the earlier UI selection check as a substitute for this dialog gate.

Submit only after both the selection and dialog gates match. If delayed verification has already established that an ID is absent, treat it as verified removed and do not submit another action for it. Record the submitted ID set and the platform result without treating a success toast or changed visible count as final verification.

## Delayed Verification and Partial Success

After each submission, reload the favorites view and wait for lazy-loaded favorite cards before checking every archived ID submitted for cleanup. Use this exact retry model:

```text
archived_ids = verified archived IDs from DEVONthink bookmarks
submit exact IDs
reload and wait for lazy-loaded favorite cards
remaining_ids = archived_ids still present
while remaining_ids is non-empty and progress is being made:
    submit only remaining_ids from the same verified bookmark batch
    reload, wait, and recompute remaining_ids
```

Track the remaining set after each attempt. If the same remaining set persists across three attempts, stop and report it. Never expand cleanup to new IDs. Report partial success with exact verified-absent IDs and exact remaining IDs; mark the batch complete only when delayed verification finds none of `archived_ids` present.

## Stopping and Merging

When the user says not to continue, stop before collecting or acting on another batch. Keep already written notes and distinguish complete, partially successful, and unresolved batches. A later unrelated request must not implicitly resume this Skill.

Merge or summarize only completed DEVONthink bookmark batches whose processing status is `complete`; exclude and report every pending, partially successful, or unresolved batch. Deduplicate only by stable content ID. Preserve one bookmark record and one canonical URL per item, retain useful visible facts and cautions, and verify aggregate bookmark count, canonical-URL count, unique-ID count, and unique canonical-URL count with one-to-one ID/URL mapping. Declare a merged summary complete only when those aggregate checks pass and no pending or unresolved processing status is present. Never use merging as permission to unfavorite.

## Quick Reference

| Need | Required action |
| --- | --- |
| DEVONthink MCP unavailable | Stop; no local-only fallback. |
| Default count omitted | Archive 24 favorites. |
| Destination | Fresh Global Inbox group `YYYY-MM-DD Archived DouYin Favorites`, scoped by returned group UUID. |
| Per favorite | DEVONthink `bookmark` record with canonical URL, content-based name, comment, and tags. |
| Finder Comment | DEVONthink record `comment`. |
| Completion note | Chinese Markdown summary record in the same group. |
| Cleanup | May proceed after verified DEVONthink bookmarks for the exact archived IDs; summary follows before final completion. |

## Common Mistakes

- Proceeding when DEVONthink MCP is missing, or offering a local Markdown fallback.
- Creating a local folder or writing into a DEVONthink database package instead of using MCP.
- Reusing an older same-day DEVONthink group instead of creating a fresh invocation group.
- Writing only a Markdown archive instead of one DEVONthink bookmark per favorite.
- Forgetting the exact dated Global Inbox folder name: `YYYY-MM-DD Archived DouYin Favorites`.
- Naming bookmarks by index or author only instead of main content.
- Putting details in chat only instead of the record comment and same-folder summary.
- Writing the same-folder summary in English instead of Chinese.
- Unfavoriting first because cached data appears sufficient to rebuild the archive.
- Selecting “the first N cards” instead of matching archived content IDs.
- Counting bookmarks or unique URLs only after the destructive action.
- Waiting for the summary or an extra confirmation when the bookmark archive has already been written and verified.
- Expanding cleanup to a newly observed ID that does not yet have a verified bookmark in the invocation folder.
- Trusting a toast or immediate viewport without reload and lazy-loading delay.
- Retrying all items, or adding newly observed IDs, after partial success.
- Repeating an unfavorite action after delayed verification already shows the ID absent.
- Continuing or pre-reading the next batch after the user says to stop.
