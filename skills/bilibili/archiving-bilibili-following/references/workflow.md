# Bilibili 关注归档与取消关注流程

## 必经检查

Map host tools by semantic capability, not exact name. 需要已登录浏览器自动化，以及 Python 3.10+、curl、file 和 Downloads 读写能力。所有文件操作使用随附脚本，完整阅读 [script-usage.md](script-usage.md)；下文规定脚本应满足的格式和核验边界，不要求代理重写文件操作。

1. 确认技能被显式调用、浏览器已登录，并运行脚本 `preflight` 验证 Downloads 读写及依赖。失败即停止，不观察列表，不操作账号。遇登录验证、验证码或限流时停止，不绕过平台限制。
2. 记录来源页面，准备本批 JSON；不要提前创建归档目录。脚本 `archive` 在输入核验通过后排他创建 `~/Downloads/YYYY-MM-DD Archived Bilibili Following Batch NN/`，日期取当前本地日期，冲突递增 NN，不覆盖或合并历史目录。
3. 记录操作前关注总数 `initial_follow_count`。按“最近关注”顺序，只取当前页前 24 个稳定 UID/canonical URL 对，记录可见账号名、简介、头像 URL 和页面顺序。若 fewer than 24 stable identities are present，报告短缺并停止；不翻页补齐，不创建账号记录，不取消关注。
4. 固定本批身份清单；标题、账号名、图片和卡片索引均不是身份键。图片失败不递补，不扩大本批范围。

## 本地归档格式

批次根目录保存 `archive.json` 和最终的 `summary.md`。每条使用稳定 UID 建立独立子目录：

```text
YYYY-MM-DD Archived Bilibili Following Batch NN/
  archive.json
  <UID>/
    record.md
    avatar.<ext>
  summary.md
```

账号身份必须为纯数字 UID；拒绝路径分隔符、点目录和越界路径。目录名不采用标题，重复标题或非法文件名字符不会覆盖记录；Markdown 中保留原始显示名。每个技能目录独立可安装，无需其他技能。

`archive.json` 是 UTF-8 JSON，包含来源页面、创建时间、固定的 `archived_ids` 和 `items` 数组。每项包含 `id`、`canonical_url`、`display_name`、可见元数据、`tags`（`Bilibili`、`Bilibili Following`）、`image_source_url`、实际下载 URL、`image_path`、`image_mime`、`record_path`、`archive_status`、`cleanup_status` 和失败原因。图片路径、记录路径均相对批次目录。`archived_ids` 只记录固定目标集，不代表核验已通过；仅在整个批次归档闸门通过后才可用于清理。

每个 `record.md` 写入来源、UID、canonical URL `https://space.bilibili.com/<UID>`、显示名、可见元数据、标签、原始头像 URL、实际本地图片相对链接及状态。缺失普通元数据写 `insufficient metadata`；缺少真实头像 URL 则是归档失败。用 Markdown 编码/转义处理名称和 URL，使本地图片链接可解析。保存临时文件后在同目录原子重命名，读回最终文件。首次写入不能覆盖已有文件；重试仅可复用本批且 ID/URL 完全匹配的记录。

## 下载与图片验证（归档内执行）

1. 从已观察页面的对应卡片读取实际头像地址（例如已加载图片的 `currentSrc`）；懒加载占位图不算。仅使用该条已观察到的真实 HTTP(S) URL，协议相对地址补为 HTTPS。不猜测资源路径，不把 `insufficient metadata` 当 URL。保存对应账号的头像文件。
2. 下载到对应 ID 子目录的临时文件。使用 `curl --fail --location --globoff --connect-timeout 15 --max-time 60 --retry 2 --proto '=http,https' --proto-redir '=http,https' --output "$temporary_image" "$observed_image_url"`。这些参数已由脚本实现，代理不单独执行下载命令。变量来自结构化数据，按参数传递，不将网页文本拼成可执行 shell 代码。
3. 只有 `i0.hdslb.com` 的 TLS 失败才允许用 URL 解析器将主机精确替换为 `i1.hdslb.com`，保留路径和查询字符串后再尝试一次，并记录实际下载地址；禁止关闭 TLS 校验。其他失败按失败项处理。
4. 要求文件非空，用 `file --mime-type` 检查实际内容；只接受 `image/jpeg`、`image/png`、`image/webp`、`image/gif`，对应扩展名 `jpg`、`png`、`webp`、`gif`。不相信 URL 扩展名或响应 Content-Type，不接受 HTML 错误页。
5. 验证后原子重命名为 `avatar.<ext>`，读回最终文件并再次核对 MIME 和非空大小；记录路径必须在本条 ID 目录内。已有已验证图片可在本批重试时复用，不产生第二张配对图片，不覆盖身份不符的文件。
6. 图片失败时保留已完成的有效文件，将失败原因写入 `archive.json`，不把临时文件当图片成功，不用后续条目递补。整批停止在归档闸门前，绝不取消关注；报告 partial/unresolved。

## 归档闸门

运行脚本 `verify`，逐项从磁盘重新读取 `archive.json`、`record.md` 与最终图片，要求：

`record count = UID count = canonical URL count = unique canonical URL count = verified image count = 24`。

固定身份集、清单、记录内身份与 URL、图片来源及本地路径必须一一对应（one-to-one mapping），所有路径存在且在本批目录内，图片通过非空和实际 MIME 核验；不得只凭工具返回成功或 URL 已写入宣称完成。任一项不等即停止，整批不得取消关注。使用各自独立的身份、canonical URL 与图片来源逐项核验；即使两条记录的图片 URL 相同，也各自保留一份本地图片。完整核验后使用脚本状态 `archive_status: verified`、`cleanup_status: pending`（即 `状态：已归档；待取消关注`）并读回确认，再进入清理闸门。图片下载前不能使用“已归档”状态。

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

将已通过逐项状态变化及重新加载后总数核验的本地记录更新为
`状态：已归档；已取消关注（逐项状态及重新加载后关注总数核验）`；仍出现或无法
核验的账号写明 `partial/unresolved`。

## 总结与交付

在同一批次目录中创建一份简体中文 Markdown 总结 `summary.md`，包含：

- Downloads 绝对路径、目录名和处理数量；
- 操作前后关注总数、`immediate_success_ids` 数量与
  `visible_remaining_ids`；
- 24 account names and canonical URLs；
- 每个 UID 的取消关注结果、未解决项和重试次数；
- 可见证据、限制，以及本地 avatar 路径、下载与 MIME 核验结果。

验证总结位于同一批次目录、覆盖全部 24 个 URL，并且与本地记录状态一致后才可报告
完整完成。If summary creation or verification fails, preserve verified files
and cleanup state, report partial completion, and do not claim full completion.

## 常见错误与抗压规则

| 错误或借口 | 必须执行的规则 |
| --- | --- |
| “24 是配额，可以从下一页补齐” | 24 是固定当前页批次；稳定身份不足即停止。 |
| “已有本地记录就更新，避免重复” | 每次调用创建新批次目录，并在其中为 24 个 UID 建立一一对应记录。 |
| “批量操作更快” | 批量操作只复制至分组，不会批量取消关注。 |
| “先点已关注看看菜单” | 该控件会立即取消关注，只能在归档闸门后按 UID 点击。 |
| “为了严谨必须遍历全部分页” | 不需要；只重新加载起始页，并结合逐 UID 即时状态与精确总数差核验。 |
| “成功提示已经足够” | 还需逐 UID 即时状态变化和重新加载后的关注总数。 |
| “重试全部 24 个最稳” | 只提交 `remaining_ids`，不得再次点击已核验移除的 UID。 |

## 状态一致性

每次清理及重试后，用同目录临时文件加原子替换更新 `archive.json` 和对应 `record.md` 的状态，并读回检查一致性。仅使用 `update` 保存浏览器核验后的 `removed` / `unresolved` 及 evidence，不手工修改文件。写入或核验失败时立即停止后续清理，保留文件，报告已发生的账号操作和未解决 ID。总结必须覆盖固定批次全部 ID、链接、图片路径、成功/失败状态和重试次数；总结失败仅能报告部分完成。用户叫停时不继续下载或清理；单次调用结束后不自动开始下一批。

## 脚本与浏览器交接

`archive` 或 `resume` 输出成功仍不替代取消操作前的 `verify`。只有退出码 0、`cleanup_ready: true`、`verified_ids` 与固定清单完全一致，才可开始浏览器清理；`remaining_ids` 排除已记录为移除的身份。脚本的 `failed` 是本地文件失败，不是账号移除结果。浏览器刷新后的观察才是账号状态证据。

`summary.md` 会在归档时生成并由每次 `update` 更新；它必须通过读回核验。脚本的 verified/pending 表示已归档待清理，verified/removed 表示已归档且浏览器报告核验移除，unresolved 表示清理未解决。图片不完整时 archive_status 为 failed，禁止把部分成功 ID 用于清理。
