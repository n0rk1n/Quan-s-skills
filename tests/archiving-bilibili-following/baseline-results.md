# Baseline Results

The RED scenario was run in a fresh context without access to the new Skill.
The evaluator was forbidden from touching live Bilibili or DEVONthink data.

## Scenario: fixed-current-page-batch

- Result: FAIL
- Correct baseline behavior:
  - Chose numeric Bilibili UID and canonical space URL as identity.
  - Required archive verification before unfollow.
- Missed intended rules:
  - Treated 24 as a quota to fill across pages instead of one bounded current-page
    batch.
  - Updated existing records instead of requiring a fresh invocation group.
  - Did not require the exact dated sequential Global Inbox group.
  - Did not require a same-folder Chinese Markdown summary.
  - Did not describe that the batch UI only copies group membership and that
    the per-card followed-state trigger immediately unfollows.
  - Did not require exact follow-count delta plus an exhaustive all-page UID
    traversal after reload.

Verbatim rationalizations:

> 目标是最终成功处理 24 个账号，而不是机械处理当前页面的 24 个条目。

> 从下一页按顺序补入候选，直到得到 24 个有效且互不重复的账号。

> 已有记录时更新或补充批次信息，不创建重复记录。

> Bilibili 页面出现“成功”提示只作为初步结果，不作为唯一证据。至少通过重新读取账号关系状态或刷新后的账号状态确认。

The last statement improved on trusting a toast, but still left the exhaustive
all-page UID proof and exact `initial_follow_count - 24` invariant unspecified.

## Forward-test results

The same synthetic scenarios were then run in fresh contexts with the completed
Skill and its required workflow loaded.

### Scenario: fixed-current-page-batch

- Result: PASS
- The executor rejected cross-page filling when any stable UID/canonical URL
  was missing.
- It required a fresh dated sequential Global Inbox group, 24 one-to-one
  bookmarks, UID-scoped per-card unfollowing, exact count delta, exhaustive
  all-page UID traversal, and a verified same-folder Chinese summary.
- It distinguished missing optional profile metadata from missing stable
  identity and treated only the latter as a batch-stopping shortfall.

### Scenario: partial-unfollow-retry

- Result: PASS
- The executor set the next `submission_ids` to only the two remaining archived
  UIDs, rejected two newly seen accounts, and refused to retry the 22 verified
  removals.
- It kept the two unresolved bookmarks partial until a reload plus exhaustive
  traversal proved them absent, and enforced the three-no-progress cutoff.
