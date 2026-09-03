# Douyin Favorites Archive Workflow

## Workflow Checklist

Map host tools by semantic capability, not by exact name.

1. Confirm the Skill was explicitly invoked, a signed-in browser is available, Python 3 can run the bundled archive script, and `/Users/oriki/Downloads` is writable.
2. Let `scripts/archive_douyin_favorites.py` create or reuse `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`, where `YYYY-MM-DD` is the current local date.
3. Use a default batch size of 24 unless the user explicitly specifies another size. Observe only that bounded batch and record each stable content ID, content type, canonical URL, concise title, visible author, and visible page caption.
4. Pass the bounded batch as JSON on standard input to `scripts/archive_douyin_favorites.py`, or use `--input <batch-json>` for a large batch or an interactive terminal. Keep any input file outside the dated archive directory; do not manually write archive files.
5. Require exit code 0, an empty `failed_items` list, and `verified_ids` equal to the full observed batch before any destructive action.
6. Unfavorite the exact verified archived IDs: select only those IDs, inspect Douyin's final confirmation dialog, and submit only if its displayed scope and count match the current submission ID set.
7. Reload, wait for lazy loading, and verify every archived ID submitted for cleanup.
8. Report the absolute destination, verified page/detail pair count, verified removals, and unresolved IDs. Stop if requested.

Never reorder these gates: `verify browser, Python, and Downloads access → observe → run archive script → accept complete verified_ids → select exact archived IDs → inspect dialog → unfavorite → delayed verify`.

## Archive Script Contract

Resolve the skill directory for the current installation, then run:

```text
python3 <skill-directory>/scripts/archive_douyin_favorites.py
```

Pass one JSON object containing a non-empty `items` array through standard input. For a large batch or an interactive terminal, use:

```text
python3 <skill-directory>/scripts/archive_douyin_favorites.py --input <batch-json>
```

The file and stdin forms have the same validation and result contract. Do not save an input manifest inside the dated archive directory. Each item has this shape:

```json
{
  "id": "7530000000000000001",
  "type": "video",
  "url": "https://www.douyin.com/video/7530000000000000001",
  "title": "基于页面内容的简洁标题",
  "author": "页面可见作者",
  "caption": "页面可见文案"
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

The script creates the directory if it does not exist and reuses it for the same day when safe. Never delete, truncate, rename, or overwrite an unrelated existing file. Repeat invocations identify an existing item through the canonical URL in its `.webloc` file and the matching content ID and URL in its detail file. Legacy pairs whose filenames contain `--<content-id>` remain readable and reusable, but new files never use that suffix.

Stop before observing favorites if the destination cannot be created, listed, written, or read back. A successful write call alone is not verification.

## Collecting a Batch

Use a batch size of 24 by default unless the user specifies another size; reduce it only when the page state cannot expose that many stable content IDs reliably. Record each card's stable content ID, content type (`video` or `note`), canonical URL, concise title, visible author, and visible caption. Do not identify a destructive target by card position, visible order, “first N,” or a broad page selection.

Do not bypass login, CAPTCHA, access controls, rate limits, or platform safeguards. Stop if the session or page state is not trustworthy. Do not pre-read another batch after the user asks to stop.

## Per-Favorite File Contract

The script turns each favorite into exactly two files in the dated folder, using the same filesystem-safe base name for both:

```text
<concise-content-title>.webloc
<concise-content-title> 详情.md
```

If another item already uses the same safe title, append a short numeric suffix to both files, beginning with ` (2)`, then ` (3)`, while keeping their base names identical.

The `.webloc` file is an XML property list whose `URL` value is exactly one canonical URL:

```text
https://www.douyin.com/video/<id>
https://www.douyin.com/note/<id>
```

Its `<id>` must match the archived content ID recorded in the detail file. The filename does not contain the content ID. Do not replace the original Douyin URL with a search result, short link, author page, or reconstructed noncanonical URL.

The title must describe the favorite's main content, not only the author, ID, index, or generic text such as `DouYin Favorite 01`. Replace `/`, `:`, and other filename separators or control characters, trim trailing periods/spaces, and keep the title concise. If visible content is sparse, use the best visible label. Resolve a same-title collision with the short numeric suffix; never expose the long content ID in a new filename.

The `详情.md` file has no level-one heading. It contains exactly these fields and no additional sections:

- content ID;
- content type;
- canonical URL;
- visible author; and
- a `## 页面文案` section containing the visible caption.

Write detail-file labels in Simplified Chinese. Preserve identifiers and URLs exactly, and label a missing author or caption as `insufficient metadata`.

Before cleanup, require the archive script's exit code 0 and compare its `verified_ids` with the browser-observed batch IDs. Preserve a one-to-one ID/URL mapping: every current-batch ID must map to exactly one readable `.webloc` and one readable metadata file with the same base name, and the URL and ID must agree across browser evidence, link file, and metadata. The verified count must equal the batch size. Stop on any mismatch.

## Cleanup Gate

Cleanup proceeds only after the current batch's local archive passes all checks. An ID is archived only when its `.webloc` and matching `详情.md` file both exist, are readable, and preserve the matching content ID, content type, canonical URL, author, and page caption.

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

## Stopping

When the user says not to continue, stop before collecting or acting on another batch. Keep already written files and distinguish complete, partially successful, and unresolved batches. A later unrelated request must not implicitly resume this Skill.

## Quick Reference

| Need | Required action |
| --- | --- |
| Downloads unavailable | Stop before observing favorites. |
| Default count omitted | Archive 24 favorites. |
| Destination | `/Users/oriki/Downloads/YYYY-MM-DD Archived DouYin Favorites`. |
| Per favorite | One `.webloc` plus one matching `详情.md` file. |
| Detail contents | ID, type, URL, author, and page caption only. |
| Archive implementation | `scripts/archive_douyin_favorites.py` with batch JSON on stdin or `--input`. |
| Cleanup | Only after verifying both local files for every exact archived ID. |

## Common Mistakes

- Redirecting output to another convenient directory when Downloads is unavailable.
- Reimplementing filename, write, or verification logic instead of using the bundled script.
- Treating exit code 1, `failed_items`, or a partial `verified_ids` list as permission to clean up.
- Writing only `.webloc` links instead of a complete pair per favorite.
- Adding headings, filenames, tags, status, summaries, facts, inferences, or cautions to `详情.md`.
- Adding `--<content-id>` or another long content-ID suffix to a new filename.
- Overwriting unrelated files already present in the daily directory.
- Naming files by index or author only instead of the main content title.
- Putting details in chat only instead of the matching detail file.
- Unfavoriting first because cached data appears sufficient to rebuild the archive.
- Selecting “the first N cards” instead of matching archived content IDs.
- Counting files or unique URLs only after the destructive action.
- Expanding cleanup to a newly observed ID that does not yet have a verified local pair.
- Trusting a toast or immediate viewport without reload and lazy-loading delay.
- Retrying all items, or adding newly observed IDs, after partial success.
- Repeating an unfavorite action after delayed verification already shows the ID absent.
- Continuing or pre-reading the next batch after the user says to stop.
