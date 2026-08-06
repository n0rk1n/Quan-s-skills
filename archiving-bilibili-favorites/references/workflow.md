# Bilibili 收藏归档与取消收藏流程

## 必经检查

1. 确认技能被显式调用、浏览器已登录 Bilibili、DEVONthink MCP 可列出可写 Inbox 数据库。任一项失败即停止；不得使用本地文件、AppleScript 或数据库包作为替代。
2. 在 Inbox 中创建本次专用分组：`YYYY-MM-DD Archived Bilibili Favorites Batch NN`。先列出现有子项，计算下一个 `NN`，创建后确认返回的 UUID 是新分组。
3. 按页面顺序读取视频卡片，直到取得 40 个唯一且稳定的 BV ID/canonical URL 对，或确认已到当前收藏夹末尾。不得把尚未完成懒加载误判为末尾。令 `available_stable_items` 为已取得的稳定身份数，`batch_size = min(40, available_stable_items)`。若 `batch_size` 为 1–39，继续归档当前全部稳定条目；若为 0，停止且不更改收藏状态。记录每条的 BV ID、URL、可见标题、可见封面 URL 与可见元数据。不可把卡片索引当作取消收藏的身份，也不可用身份不稳定的卡片补足数量。

## 归档闸门

为每一条创建一个 DEVONthink `bookmark`：

- `url`：`https://www.bilibili.com/video/<BV_ID>`；
- `name`：可见视频标题；
- `tags`：`Bilibili`、`Bilibili Favorites`，可加有依据的主题标签；
- `comment`：来源、BV ID、canonical URL、可见标题、可见封面 URL、缺失字段标为 `insufficient metadata`，以及状态 `已归档；待取消收藏`。

创建前按 URL 查询本分组，避免重复。创建后必须验证：bookmark 数、BV ID 数、URL 数和唯一 URL 数均为 `batch_size`；每个 bookmark 的 URL、备注、标签和 BV ID 一一对应。任一项不等即停止，绝不取消收藏。

若 MCP 没有写入 bookmark 缩略图的操作，不得声称已设置缩略图；仅在备注保存可见封面 URL。

## 取消收藏闸门（归档核验通过后自动执行）

显式调用本技能即授权取消收藏；归档闸门完整通过后，直接处理本次 `batch_size` 个 `archived_ids`，不得再次要求用户确认。归档闸门未通过、`batch_size` 为 0 或映射不一致时，必须停止，绝不取消收藏。

1. `archived_ids` 必须等于已通过归档验证的 `batch_size` 个 BV ID。
2. 仅按 BV ID/视频 URL 定位卡片并勾选。读取已选 ID 集；它必须与 `archived_ids` 完全相等，不能多也不能少。
3. 点击“取消收藏”后，检查最终弹窗：动作是取消收藏，显示数量等于 `batch_size`，且无额外范围或异常提示。任何不匹配都取消操作并报告。
4. 提交后重新加载收藏页，等待懒加载，检查全部 `archived_ids` 都不再出现。成功提示或数字变化不构成最终验证。
5. 若部分仍在，最多只对同一已验证 ID 集中的剩余项重试；三次无进展即停止。不得带入新卡片或下一批。

将已验证移除的 bookmark 状态改为 `已归档；已取消收藏（页面重新加载后核验）`；未移除项标明 `partial/unresolved`。

## 总结与交付

在相同分组创建一份简体中文 Markdown 总结，包含：目标位置、`batch_size`、可见证据与限制、本批全部标题及 URL、取消收藏结果、未解决项，以及缩略图能力限制。验证总结位于同一分组、覆盖本批全部 URL，并且状态与 bookmark 一致后再报告完成。

## 常见错误

| 错误 | 正确做法 |
| --- | --- |
| 直接勾选“本页全选” | 先证明页面所选 URL 集与 `archived_ids` 完全一致且数量等于 `batch_size`；否则按 BV ID 逐项选择。 |
| 先取消、后归档 | 先完成 `batch_size` 个 bookmark 的一对一核验。 |
| 相信取消成功提示 | 重新加载并核验全部 `archived_ids`。 |
| 不足 40 条就停止 | 已确认到达收藏夹末尾且 `batch_size` 为 1–39 时，处理当前全部稳定条目。 |
| 扩大到下一批 | 单次调用最多处理 40 条；不足 40 时不得从其他收藏夹或不稳定卡片补足。 |
