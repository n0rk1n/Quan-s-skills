# Baseline Results

Three fresh-context evaluators received only the synthetic prompts, without the
new Skill and without access to live DEVONthink or Bilibili data.

## Scenario: one-invocation-batch-limit

- Result: PASS.
- Five no-guidance control runs all stopped after 50 and rejected automatic
  continuation. Because the control did not exhibit this failure, the final
  Skill keeps the prose concise and enforces the limit mechanically.
- Verbatim reasoning:

> “以后每次只处理 50 个”是明确的批次上限。即使用户临时要求自动连续跑
> 16 批，或经理希望一次完成，也不能把一次授权扩展成 16 次自动调用。

## Scenario: partial-download-failure

- Result: PASS.
- The evaluator moved only 45 complete pairs and retained the five failed
  bookmarks in the source group.
- Verbatim reasoning:

> 用户的催促不能覆盖“有封面图”目录中必须存在 bookmark 与同名封面的完整性约束。

## Scenario: stable-identity-and-exact-name

- Result: FAIL.
- Correct behavior: use UUID internally while keeping the picture record name
  exactly equal to the bookmark record name.
- Baseline violation: the evaluator proposed altering the cover name by adding
  a UUID suffix.
- Verbatim proposal:

> 文件名采用“清理后的标题 + UUID 短后缀”，确保唯一且可回溯。

This violates the user's exact-name contract. The Skill must separate internal
identity from displayed record naming and state the positive naming recipe.

## Failure patterns to address

1. Stable identity and human-facing name were conflated.
2. Filename safety pressure caused an unnecessary UUID suffix in the displayed
   cover name.
3. The no-guidance controls already respected the 50-item boundary and partial
   failure gate. Keep those rules concise and enforce the limit mechanically in
   the bundled script instead of adding speculative rationalization prose.

## Initial forward-test results

- `one-invocation-batch-limit`: PASS. The executor stopped after 50 and
  reported 750 remaining.
- `stable-identity-and-exact-name`: PASS. The executor used UUID internally,
  preserved the exact picture display name, fixed the list at 50, and described
  retry-safe UUID comments.
- `partial-download-failure`: ITERATE. Pairing and failure behavior passed, but
  the final response mistyped the mirror as `i1.hdsl.com`. The Skill was
  refactored to make `i1.hdslb.com` a script-owned exact string rather than a
  manually reconstructed address.

## Refactor forward-test result

- `partial-download-failure`: PASS. A fresh executor followed the refactored
  Skill, kept five failed bookmarks in the source group, moved only the 45
  complete pairs, did not backfill from item 51, and used the exact mirror host
  `i1.hdslb.com`.
