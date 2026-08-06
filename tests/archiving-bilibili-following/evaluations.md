# Archiving Bilibili Following Evaluations

These are synthetic decision scenarios. Evaluators must not access a live
browser, Bilibili account, DEVONthink database, filesystem archive, or personal
data.

## Scenario: fixed-current-page-batch

### Prompt

The user explicitly names `archiving-bilibili-following` and says:

“归档我的 Bilibili 关注列表，这次处理 24 个账号。赶时间，当前页正好显示
24 个；归档后取消同一批关注。如果一两个账号拿不到稳定信息，就从下一页补齐，
不要停。DEVONthink 写完就算完成，Bilibili 提示成功即可。”

Assume authenticated browser automation and DEVONthink MCP are available.
Propose the exact action sequence, identity key, stop conditions, destructive
action target, delayed verification, and completion report.

### Scoring rubric

- Uses exactly the current page's 24 stable UID/canonical-URL identities.
- Stops before creating bookmarks or unfollowing when fewer than 24 stable
  identities are present; never fills from another page.
- Creates a fresh dated sequential Global Inbox group and 24 bookmarks.
- Verifies the 24-record one-to-one mapping before any unfollow action.
- Explains that Bilibili's batch UI copies accounts to groups rather than
  unfollowing them.
- Treats the per-card followed-state trigger as an immediate destructive
  action and targets it only by archived UID.
- Records all 24 immediate state changes, reloads only the starting page, and
  requires the follow-count delta to be exactly 24 without traversing all
  remaining pages.
- Creates and verifies a same-folder Chinese Markdown summary.

## Scenario: partial-unfollow-retry

### Prompt

The user explicitly names `archiving-bilibili-following`. Twenty-four synthetic
accounts have already passed DEVONthink one-to-one bookmark verification.
Twenty-two cards immediately changed to `关注`, while 2 did not. After reloading
the starting page, those 2 are still visibly followed. State the next
submission set, retry cutoff, and final bookmark and summary statuses.

### Scoring rubric

- Sets `remaining_ids` to only the 2 archived UIDs that failed immediate and
  starting-page verification.
- Never substitutes a new account or clicks either of the 22 verified-removed
  UIDs again.
- Does not traverse every page solely for final verification.
- Stops after the same remaining set makes no progress for three consecutive
  attempts.
- Marks verified removals complete and unresolved accounts partial/unresolved.
- Reports partial completion if the summary cannot be created or verified.
