# Bilibili 关注归档与取消关注流程

## Workflow Checklist

Map tools by semantic capability, not exact name. Names such as
`mcp__devonthink.get_databases`, `mcp__devonthink.create_record`, and
`mcp__devonthink.lookup_records` are non-normative examples; use equivalent
authenticated-browser and DEVONthink MCP operations exposed by the current
host.

## 必经检查

1. 确认技能被显式调用、浏览器已登录 Bilibili、DEVONthink MCP 可列出可写的
   Global Inbox。任一项失败即停止；不得使用本地文件、AppleScript 或直接修改
   DEVONthink 数据库包作为替代。
2. 记录操作前的关注总数 `initial_follow_count`。在 Global Inbox 中列出现有子项，
   计算下一个 `NN`，创建本次专用的新分组：
   `YYYY-MM-DD Archived Bilibili Following Batch NN`。必须确认返回的 UUID 属于
   fresh group，不得以更新历史 bookmark 代替本次新归档。
3. 在“最近关注”顺序下，只读取当前页前 24 个能取得稳定 UID 和 canonical URL
   的账号。记录 UID、`https://space.bilibili.com/<UID>`、可见账号名、可见简介、
   可见头像 URL 和页面顺序。账号名、头像或卡片索引都不能作为身份键。
4. 要求 UID 数、URL 数、唯一 UID 数、唯一 URL 数均为 24。若 fewer than 24
   stable identities are present，报告短缺并停止；不得翻到下一页补齐，也不得创建
   bookmark 或取消任何关注。

## 归档闸门

为每个账号在 fresh group 中创建一个 DEVONthink `bookmark`：

- `url`：`https://space.bilibili.com/<UID>`；
- `name`：可见账号名，缺失时使用 `Bilibili UID <UID>`；
- `tags`：`Bilibili`、`Bilibili Following`；
- `comment`：来源、UID、canonical URL、可见账号名、可见简介、可见头像 URL；
  缺失字段写 `insufficient metadata`；初始状态写
  `状态：已归档；待取消关注`。

创建前按 URL 查询本次 fresh group，防止本批内重复。创建后必须验证：
`bookmark count = UID count = canonical URL count = unique canonical URL count = 24`，
且每个 bookmark 的 URL、UID、备注、标签和账号名形成 one-to-one mapping。
任一项不等即停止，绝不取消关注。

若 MCP 没有写入 bookmark thumbnail 的能力，不得声称已设置缩略图；只把可见
头像 URL 保存到备注。

## 取消关注闸门

显式调用本技能即授权取消关注。只有归档闸门完整通过后，才可处理完全相同的 24 个
UID，无需再次确认：

1. `archived_ids` 必须等于已通过归档验证的 24 个 UID。第一次操作设置
   `submission_ids = archived_ids`；部分成功后的重试设置
   `submission_ids = remaining_ids`。每次都要求 `submission_ids` 是
   `archived_ids` 的子集，绝不加入新 UID。
2. Bilibili 的“批量操作”只提供“复制至”分组，does not provide bulk unfollow；
   不得把它当成取消关注入口。
3. 逐项按账号主页链接中的 stable UID 定位卡片。卡片上的已关注状态触发器
   （常见可见文字为 `已关注`）immediately cancels the follow；点击不是打开预览
   菜单，而是破坏性操作。只有当卡片 UID 属于 `submission_ids` 时才点击。
4. 每次点击后立即核验该卡片变为未关注状态，例如 text `关注`，并记录结果。
   将通过即时状态核验的 UID 加入 `immediate_success_ids`。若无法证明卡片 UID
   或无法证明状态变化，停止该 UID 的操作并报告。已经核验移除的 UID 不得再次
   点击：never click the same verified-removed UID again。

## 延迟核验与重试

1. 第一轮完成后 reload only the starting page。核验只覆盖本次起始页和关注总数；
   do not traverse every page，也不要求访问其余分页。
2. 若 `immediate_success_ids = archived_ids`，要求重新加载后的关注总数严格等于
   `initial_follow_count - 24`。同时检查起始页中仍可见且仍显示“已关注”的目标
   UID，记为 `visible_remaining_ids`。24 次即时状态变化加精确总数差即构成本批
   完成证据；成功提示本身不构成证据。
3. 若存在未通过即时状态核验的 UID，或 `visible_remaining_ids` 非空，只把这些
   已知未解决 UID 记为 `remaining_ids` 并重试。若所有 UID 均通过即时核验但关注
   总数差不是 24，停止并报告 `partial/unresolved`，不得猜测 UID 或扩大重试范围。
4. 重试仍设置 `submission_ids = remaining_ids`；每轮只重新加载起始页并复核总数。
   若同一 remaining set 在 three consecutive attempts 中没有进展，停止并报告
   unresolved。

将已通过逐项状态变化及重新加载后总数核验的 bookmark 更新为
`状态：已归档；已取消关注（逐项状态及重新加载后关注总数核验）`；仍出现或无法
核验的账号写明 `partial/unresolved`。

## 总结与交付

在同一 fresh group 中创建一份简体中文 Markdown 总结，包含：

- DEVONthink 目标位置、分组名和处理数量；
- 操作前后关注总数、`immediate_success_ids` 数量与
  `visible_remaining_ids`；
- 24 account names and canonical URLs；
- 每个 UID 的取消关注结果、未解决项和重试次数；
- 可见证据、限制，以及 thumbnail 只能保存头像 URL 的能力边界。

验证总结位于同一分组、覆盖全部 24 个 URL，并且与 bookmark 状态一致后才可报告
完整完成。If summary creation or verification fails, preserve verified bookmarks
and cleanup state, report partial completion, and do not claim full completion.

## 常见错误与抗压规则

| 错误或借口 | 必须执行的规则 |
| --- | --- |
| “24 是配额，可以从下一页补齐” | 24 是固定当前页批次；稳定身份不足即停止。 |
| “已有 bookmark 就更新，避免重复” | 每次调用创建 fresh group，并在其中为 24 个 UID 建立一一对应记录。 |
| “批量操作更快” | 批量操作只复制至分组，不会批量取消关注。 |
| “先点已关注看看菜单” | 该控件会立即取消关注，只能在归档闸门后按 UID 点击。 |
| “为了严谨必须遍历全部分页” | 不需要；只重新加载起始页，并结合逐 UID 即时状态与精确总数差核验。 |
| “成功提示已经足够” | 还需逐 UID 即时状态变化和重新加载后的关注总数。 |
| “重试全部 24 个最稳” | 只提交 `remaining_ids`，不得再次点击已核验移除的 UID。 |
