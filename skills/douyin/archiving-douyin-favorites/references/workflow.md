# Douyin Favorites Archive Workflow

## Workflow Checklist

Map host tools by semantic capability, not by exact name.

1. Confirm the Skill was explicitly invoked, a signed-in browser is available, Python 3 can run the bundled archive script, and `/Users/oriki/Downloads` is writable.
2. Let `scripts/archive_douyin_favorites.py` create or reuse `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`, where `YYYY-MM-DD` is the current local date.
3. Use a default batch size of 24 unless the user explicitly specifies another size. Observe only that bounded batch and record stable content IDs, canonical URLs, visible facts, and topic labels.
4. Pass the bounded batch as JSON on standard input to `scripts/archive_douyin_favorites.py`; do not manually write archive files.
5. Require exit code 0, an empty `failed_items` list, and `verified_ids` equal to the full observed batch before any destructive action.
6. If cleanup is requested, select only the verified archived IDs, inspect Douyin's final confirmation dialog, and submit only if its displayed scope and count match the current submission ID set.
7. Reload, wait for lazy loading, and verify every archived ID submitted for cleanup.
8. Rerun the archive script with each item's final `archive_status` (`complete` or `partial/unresolved`) so the matching detail file reflects delayed verification.
9. Report the absolute destination, verified page/detail pair count, verified removals, and unresolved IDs. Stop if requested.

Never reorder these gates: `verify browser, Python, and Downloads access → observe → run archive script → accept complete verified_ids → select exact archived IDs → inspect dialog → unfavorite → delayed verify`.

## Archive Script Contract

Resolve the skill directory for the current installation, then run:

```text
python3 <skill-directory>/scripts/archive_douyin_favorites.py
```

Pass one JSON object containing a non-empty `items` array through standard input. Do not save a manifest inside the dated archive directory. Each item has this shape:

```json
{
  "id": "7530000000000000001",
  "type": "video",
  "url": "https://www.douyin.com/video/7530000000000000001",
  "title": "基于页面内容的简洁标题",
  "author": "页面可见作者",
  "caption": "页面可见文案",
  "facts": ["页面可见事实"],
  "summary": "仅根据页面可见内容写成的事实摘要",
  "inferences": ["推断：明确标记的解释"],
  "tags": ["内容主题"],
  "cautions": ["需要保留的证据限制或风险提示"],
  "archive_status": "archived; pending unfavorite"
}
```

The script validates the whole input batch before creating the dated directory. It rejects duplicate IDs, duplicate canonical URLs, mismatched content types, short links, author links, queries, fragments, and malformed dates. It sanitizes titles, creates XML `.webloc` files, renders Chinese detail Markdown, protects unrelated files and conflicting/incomplete existing pairs, writes atomically, and reads each pair back.

The script prints one JSON result:

```json
{
  "destination": "/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites",
  "verified_ids": ["7530000000000000001"],
  "failed_items": [],
  "pairs_written": 1
}
```

Exit code 0 means every item passed write/read-back verification. Exit code 1 means one or more per-item file conflicts or failures occurred; preserve successful files, report the failures, and do not clean up the batch. Exit code 2 means the JSON, batch, URL, ID, type, date, or destination precondition is invalid. Never infer success from file presence alone or add an ID to `verified_ids` outside the script result.

## Local Destination

Use this exact daily directory:

```text
/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites
```

The English phrase is fixed: `Archived DouYin Favorites`. Replace only `YYYY-MM-DD` with the current local date. Do not redirect output to a repository, Desktop, temporary directory, iCloud, or another location.

The script creates the directory if it does not exist and reuses it for the same day when safe. Never delete, truncate, rename, or overwrite an unrelated existing file. Stable content IDs in filenames make repeat invocations safe: the script updates the matching pair for the same content ID only after confirming its canonical URL and creates a new pair for a new ID.

Stop before observing favorites if the destination cannot be created, listed, written, or read back. A successful write call alone is not verification.

## Collecting a Batch

Use a batch size of 24 by default unless the user specifies another size; reduce it only when the page state cannot expose that many stable content IDs reliably. Record each card's stable content ID, content type (`video` or `note`), canonical URL, visible title/caption/author, visible facts, and 1-5 content tags grounded in the item. Do not identify a destructive target by card position, visible order, “first N,” or a broad page selection.

Do not bypass login, CAPTCHA, access controls, rate limits, or platform safeguards. Stop if the session or page state is not trustworthy. Do not pre-read another batch after the user asks to stop.

## Per-Favorite File Contract

The script turns each favorite into exactly two files in the dated folder, using the same filesystem-safe base name for both:

```text
<concise-content-title>--<content-id>.webloc
<concise-content-title>--<content-id> 详情.md
```

The `.webloc` file is an XML property list whose `URL` value is exactly one canonical URL:

```text
https://www.douyin.com/video/<id>
https://www.douyin.com/note/<id>
```

Its `<id>` must match the filename and archived content ID. Do not replace the original Douyin URL with a search result, short link, author page, or reconstructed noncanonical URL.

The title must describe the favorite's main content, not only the author, ID, index, or generic text such as `DouYin Favorite 01`. Replace `/`, `:`, and other filename separators or control characters, trim trailing periods/spaces, and keep the title concise. If visible content is sparse, use the best visible label plus the mandatory content-ID suffix.

The `详情.md` file stores all structured context that must remain available locally:

- content ID and content type;
- canonical URL and matching `.webloc` filename;
- visible author, title, caption, and source facts;
- a factual summary grounded only in visible material;
- reusable takeaways or interpretation clearly labeled as inference;
- 1-5 grounded topic tags, plus `DouYin` and `DouYin Favorites`;
- missing fields labeled `insufficient metadata`;
- caution for medical, financial, benchmark, income, popularity, or product claims; and
- archive status such as `archived; pending unfavorite`, `complete`, or `partial/unresolved`.

Write detail-file text in Simplified Chinese by default. Preserve fixed identifiers, URLs, filenames, and tag strings exactly when needed.

Before cleanup, require the archive script's exit code 0 and compare its `verified_ids` with the browser-observed batch IDs. Preserve a one-to-one ID/URL mapping: every current-batch ID must map to exactly one readable `.webloc` and one readable metadata file, and the URL and ID must agree across browser evidence, filename, link file, and metadata. The verified count must equal the batch size. Stop on any mismatch.

Label visible facts as facts. Clearly mark any synthesis, takeaway, interpretation, or inferred context as inference, and do not invent missing details. Add explicit caution rather than endorsement when recording medical, financial, benchmark, income, popularity, or product claims; visible engagement counts and creator assertions are not independent verification.

## Cleanup Gate

Cleanup may proceed only after the current batch's local archive passes all checks. An ID is archived only when its `.webloc` and matching `详情.md` file both exist, are readable, contain the matching canonical URL and content ID, and preserve the required visible context and tags.

Cleanup scope is the verified archived ID set from the current invocation. Do not ask for an extra confirmation solely because the cleanup step is destructive, but stop if the user says not to continue. A later batch or newly observed ID requires its own verified local files before it can be unfavorited.

## Exact-ID Unfavorite Procedure

Set `archived_ids` to the script's complete-batch `verified_ids`. For the initial submit, set `submission_ids = archived_ids`. For each partial-success retry, set `submission_ids = remaining_ids`. Require `submission_ids` to be a subset of `archived_ids`; never add an ID outside the verified local archive.

Locate and select items by matching `submission_ids`, never by card index or position. Require the UI-selected ID set to equal `submission_ids` for that submit; stop on any extra or missing ID.

Before the final destructive submit, inspect Douyin's confirmation dialog. Verify that its displayed destructive scope and count match the current `submission_ids`; if the dialog exposes item identifiers, verify those identifiers too. Abort before final submission on any mismatch, extra item, unverifiable scope, or unexpected count.

Submit only after both the selection and dialog gates match. If delayed verification has already established that an ID is absent, treat it as verified removed and do not submit another action for it. Record the submitted ID set and platform result without treating a success toast or changed visible count as final verification.

## Delayed Verification and Partial Success

After each submission, reload the favorites view and wait for lazy-loaded favorite cards before checking every archived ID submitted for cleanup:

```text
archived_ids = IDs from verified local archive pairs
submit exact IDs
reload and wait for lazy-loaded favorite cards
remaining_ids = archived_ids still present
while remaining_ids is non-empty and progress is being made:
    submit only remaining_ids from the same verified local batch
    reload, wait, and recompute remaining_ids
```

If the same remaining set persists across three attempts, stop and report it. Never expand cleanup to new IDs. Report partial success with exact verified-absent IDs and exact remaining IDs; mark the batch complete only when delayed verification finds none of `archived_ids` present.

After delayed verification, pass the same batch through the archive script again with an updated `archive_status` for each item. This update reuses the verified ID/URL pair and must not rename it. If the status update fails, preserve the existing files and cleanup result, and report the detail metadata as unresolved rather than repeating the destructive action.

## Stopping

When the user says not to continue, stop before collecting or acting on another batch. Keep already written files and distinguish complete, partially successful, and unresolved batches. A later unrelated request must not implicitly resume this Skill.

## Quick Reference

| Need | Required action |
| --- | --- |
| Downloads unavailable | Stop before observing favorites. |
| Default count omitted | Archive 24 favorites. |
| Destination | `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`. |
| Per favorite | One `.webloc` plus one matching `详情.md` file. |
| Detailed context | Store it in the matching `详情.md` file. |
| Archive implementation | `scripts/archive_douyin_favorites.py` with batch JSON on stdin. |
| Cleanup | Only after verifying both local files for every exact archived ID. |

## Common Mistakes

- Redirecting output to another convenient directory when Downloads is unavailable.
- Reimplementing filename, write, or verification logic instead of using the bundled script.
- Treating exit code 1, `failed_items`, or a partial `verified_ids` list as permission to clean up.
- Writing only `.webloc` links instead of a complete pair per favorite.
- Overwriting unrelated files already present in the daily directory.
- Naming files by index or author only instead of main content plus stable content ID.
- Putting details in chat only instead of the matching detail file.
- Unfavoriting first because cached data appears sufficient to rebuild the archive.
- Selecting “the first N cards” instead of matching archived content IDs.
- Counting files or unique URLs only after the destructive action.
- Expanding cleanup to a newly observed ID that does not yet have a verified local pair.
- Trusting a toast or immediate viewport without reload and lazy-loading delay.
- Retrying all items, or adding newly observed IDs, after partial success.
- Repeating an unfavorite action after delayed verification already shows the ID absent.
- Continuing or pre-reading the next batch after the user says to stop.
