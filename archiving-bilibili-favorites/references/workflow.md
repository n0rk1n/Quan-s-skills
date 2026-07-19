# Bilibili 收藏归档与取消收藏流程

## 必经检查

1. 确认技能被显式调用、浏览器已登录 Bilibili、DEVONthink MCP 可列出可写 Inbox 数据库。任一项失败即停止；不得使用本地文件、AppleScript 或数据库包作为替代。
2. 在 Inbox 中创建本次专用分组：`YYYY-MM-DD Archived Bilibili Favorites Batch NN`。先列出现有子项，计算下一个 `NN`，创建后确认返回的 UUID 是新分组。
3. 只读取当前按页面顺序的前 40 个、能取得稳定 BV ID 和 canonical URL 的视频卡片。记录 BV ID、URL、可见标题、可见封面 URL 与可见元数据。不可把卡片索引当作取消收藏的身份。

## 归档闸门

为每一条创建一个 DEVONthink `bookmark`：

- `url`：`https://www.bilibili.com/video/<BV_ID>`；
- `name`：可见视频标题；
- `tags`：`Bilibili`、`Bilibili Favorites`，可加有依据的主题标签；
- `comment`：来源、BV ID、canonical URL、可见标题、可见封面 URL、缺失字段标为 `insufficient metadata`，以及状态 `已归档；待取消收藏`。

创建前按 URL 查询本分组，避免重复。创建后必须验证：bookmark 数、BV ID 数、URL 数和唯一 URL 数均为 40；每个 bookmark 的 URL、备注、标签和 BV ID 一一对应。任一项不等即停止，绝不取消收藏。

若 MCP 没有写入 bookmark 缩略图的操作，不得声称已设置缩略图；仅在备注保存可见封面 URL。

## 取消收藏闸门（仅当用户明确要求）

1. `archived_ids` 必须等于已通过归档验证的 40 个 BV ID。
2. 仅按 BV ID/视频 URL 定位卡片并勾选。读取已选 ID 集；它必须与 `archived_ids` 完全相等，不能多也不能少。
3. 点击“取消收藏”后，检查最终弹窗：动作是取消收藏，显示数量为 40，且无额外范围或异常提示。任何不匹配都取消操作并报告。
4. 提交后重新加载收藏页，等待懒加载，检查 40 个 `archived_ids` 都不再出现。成功提示或数字变化不构成最终验证。
5. 若部分仍在，最多只对同一已验证 ID 集中的剩余项重试；三次无进展即停止。不得带入新卡片或下一批。

将已验证移除的 bookmark 状态改为 `已归档；已取消收藏（页面重新加载后核验）`；未移除项标明 `partial/unresolved`。

## 总结与交付

在相同分组创建一份简体中文 Markdown 总结，包含：目标位置、处理数量、可见证据与限制、40 条标题及 URL、取消收藏结果、未解决项，以及缩略图能力限制。验证总结位于同一分组、覆盖全部 40 条 URL，并且状态与 bookmark 一致后再报告完成。

## 常见错误

| 错误 | 正确做法 |
| --- | --- |
| 直接勾选“本页全选” | 先证明页面 40 个 URL 与 `archived_ids` 完全一致；否则按 BV ID 逐项选择。 |
| 先取消、后归档 | 先完成 40 个 bookmark 的一对一核验。 |
| 相信取消成功提示 | 重新加载并核验全部 40 个 BV ID。 |
| 扩大到下一页或下一批 | 单次调用严格只处理 40 条。 |
