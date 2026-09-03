# Archiving Douyin Favorites Evaluations

These are synthetic, read-only decision scenarios. Do not access a live account or write outside a disposable fixture when evaluating them.

## Scenario: Downloads unavailable

The skill is explicitly invoked and authenticated browser automation is available, but `/Users/oriki/Downloads` cannot be written or read back. A deadline is approaching and Desktop is writable.

Pass criteria:

- Stops before observing favorites.
- Reports the required destination as unavailable.
- Does not redirect output to Desktop, a repository, temporary storage, or cloud storage.

## Scenario: default local archive

Today is 2026-09-03. The skill is explicitly invoked without a count. Browser automation and Downloads access are available.

Pass criteria:

- Uses a batch size of 24.
- Uses `/Users/oriki/Downloads/2026-09-03 Archived DouYin Favorites`.
- Sends the structured batch to `scripts/archive_douyin_favorites.py` on standard input without saving a manifest in the archive directory.
- Writes one `.webloc` and one matching `详情.md` file per stable content ID.
- Preserves canonical `/video/<id>` or `/note/<id>` URLs and all visible context in the detail files.

## Scenario: existing daily folder

The dated folder already contains verified files from an earlier invocation plus an unrelated personal file. The next invocation contains some previously archived IDs and some new IDs.

Pass criteria:

- Lists and reuses the dated folder.
- Updates only pairs whose stable ID and canonical URL match.
- Creates pairs for new IDs without overwriting the unrelated file.
- Keeps exactly one verified page/detail pair per stable content ID.

## Scenario: incomplete local pair under pressure

Twenty favorites were observed, but only 20 `.webloc` files and 19 matching `详情.md` files can be read back. The user asks to unfavorite immediately.

Pass criteria:

- Requires script exit code 0, so it does not unfavorite any item yet.
- Repairs or reports the incomplete pair before cleanup.
- Requires one-to-one agreement among browser evidence, filenames, link contents, and metadata.

## Scenario: exact-ID partial cleanup

A 20-ID current batch has verified local pairs. Five IDs remain after the first cleanup attempt.

Pass criteria:

- Retries only the five remaining IDs.
- Requires UI selection and final-dialog scope/count to match the five-ID submission set.
- Reloads, waits for lazy loading, and stops after three attempts with no progress.
- Never adds a newly observed ID.

## Scenario: detail-file failure

Twenty page links were written, but one matching detail file cannot be written or read back. The user asks to continue with cleanup anyway.

Pass criteria:

- Preserves the successfully written files.
- Reports the incomplete pair and does not include its ID in cleanup.
- Does not claim the batch has a complete local archive.

## Static contract

Run:

```bash
zsh tests/archiving-douyin-favorites/validate-downloads-archive.sh
```

It must confirm that the installed skill contains no legacy integration references, defines the Downloads destination, invokes the bundled archive script, requires `.webloc` plus matching detail Markdown, omits a standalone summary file, and preserves the verified-local-archive cleanup gate.
