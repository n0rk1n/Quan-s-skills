# Bilibili 收藏归档与取消收藏流程

## 必经检查

Map host tools by semantic capability, not exact name. 需要已登录浏览器自动化，以及 Python 3.10+、curl、file 和 Downloads 读写能力。所有文件操作使用随附脚本，完整阅读 [script-usage.md](script-usage.md)；下文规定脚本应满足的格式和核验边界，不要求代理重写文件操作。

1. 确认技能被显式调用、浏览器已登录，并运行脚本 `preflight` 验证 Downloads 读写及依赖。失败即停止，不观察列表，不操作账号。遇登录验证、验证码或限流时停止，不绕过平台限制。
2. 记录来源页面，准备本批 JSON；不要提前创建归档目录。脚本 `archive` 在输入核验通过后排他创建 `~/Downloads/YYYY-MM-DD Archived Bilibili Favorites Batch NN/`，日期取当前本地日期，冲突递增 NN，不覆盖或合并历史目录。
3. 按页面顺序读取当前收藏夹，直到取得 40 个唯一且稳定的 BV ID/canonical URL 对，或确认到达当前收藏夹末尾。不得把懒加载误判为末尾。令 `batch_size = min(40, available_stable_items)`；1–39 条也继续，0 条停止且不改变收藏状态。不从其他收藏夹或不稳定卡片补齐。记录可见标题、封面 URL、可见元数据及页面顺序。
4. 固定本批身份清单；标题、账号名、图片和卡片索引均不是身份键。图片失败不递补，不扩大本批范围。

## 本地归档格式

批次根目录保存 `archive.json` 和最终的 `summary.md`。每条使用稳定 BV ID 建立独立子目录：

```text
YYYY-MM-DD Archived Bilibili Favorites Batch NN/
  archive.json
  <BV_ID>/
    record.md
    cover.<ext>
  summary.md
```

视频身份必须符合 `BV[0-9A-Za-z]{10}`；拒绝路径分隔符、点目录和越界路径。目录名不采用标题，重复标题或非法文件名字符不会覆盖记录；Markdown 中保留原始显示名。每个技能目录独立可安装，无需其他技能。

`archive.json` 是 UTF-8 JSON，包含来源页面、创建时间、固定的 `archived_ids` 和 `items` 数组。每项包含 `id`、`canonical_url`、`display_name`、可见元数据、`tags`（`Bilibili`、`Bilibili Favorites`）、`image_source_url`、实际下载 URL、`image_path`、`image_mime`、`record_path`、`archive_status`、`cleanup_status` 和失败原因。图片路径、记录路径均相对批次目录。`archived_ids` 只记录固定目标集，不代表核验已通过；仅在整个批次归档闸门通过后才可用于清理。

每个 `record.md` 写入来源、BV ID、canonical URL `https://www.bilibili.com/video/<BV_ID>`、显示名、可见元数据、标签、原始封面 URL、实际本地图片相对链接及状态。缺失普通元数据写 `insufficient metadata`；缺少真实封面 URL 则是归档失败。用 Markdown 编码/转义处理名称和 URL，使本地图片链接可解析。保存临时文件后在同目录原子重命名，读回最终文件。首次写入不能覆盖已有文件；重试仅可复用本批且 ID/URL 完全匹配的记录。

## 下载与图片验证（归档内执行）

1. 从已观察页面的对应卡片读取实际封面地址（例如已加载图片的 `currentSrc`）；懒加载占位图不算。仅使用该条已观察到的真实 HTTP(S) URL，协议相对地址补为 HTTPS。不猜测资源路径，不把 `insufficient metadata` 当 URL。此处只下载封面，不下载视频媒体。
2. 下载到对应 ID 子目录的临时文件。使用 `curl --fail --location --globoff --connect-timeout 15 --max-time 60 --retry 2 --proto '=http,https' --proto-redir '=http,https' --output "$temporary_image" "$observed_image_url"`。这些参数已由脚本实现，代理不单独执行下载命令。变量来自结构化数据，按参数传递，不将网页文本拼成可执行 shell 代码。
3. 只有 `i0.hdslb.com` 的 TLS 失败才允许用 URL 解析器将主机精确替换为 `i1.hdslb.com`，保留路径和查询字符串后再尝试一次，并记录实际下载地址；禁止关闭 TLS 校验。其他失败按失败项处理。
4. 要求文件非空，用 `file --mime-type` 检查实际内容；只接受 `image/jpeg`、`image/png`、`image/webp`、`image/gif`，对应扩展名 `jpg`、`png`、`webp`、`gif`。不相信 URL 扩展名或响应 Content-Type，不接受 HTML 错误页。
5. 验证后原子重命名为 `cover.<ext>`，读回最终文件并再次核对 MIME 和非空大小；记录路径必须在本条 ID 目录内。已有已验证图片可在本批重试时复用，不产生第二张配对图片，不覆盖身份不符的文件。
6. 图片失败时保留已完成的有效文件，将失败原因写入 `archive.json`，不把临时文件当图片成功，不用后续条目递补。整批停止在归档闸门前，绝不取消收藏；报告 partial/unresolved。

## 归档闸门

运行脚本 `verify`，逐项从磁盘重新读取 `archive.json`、`record.md` 与最终图片，要求：

`record count = BV ID count = canonical URL count = unique canonical URL count = verified image count = batch_size`。

固定身份集、清单、记录内身份与 URL、图片来源及本地路径必须一一对应（one-to-one mapping），所有路径存在且在本批目录内，图片通过非空和实际 MIME 核验；不得只凭工具返回成功或 URL 已写入宣称完成。任一项不等即停止，整批不得取消收藏。使用各自独立的身份、canonical URL 与图片来源逐项核验；即使两条记录的图片 URL 相同，也各自保留一份本地图片。完整核验后使用脚本状态 `archive_status: verified`、`cleanup_status: pending`（即 `状态：已归档；待取消收藏`）并读回确认，再进入清理闸门。图片下载前不能使用“已归档”状态。

## 取消收藏闸门（归档核验通过后自动执行）

显式调用本技能即授权取消收藏；归档闸门完整通过后，直接处理本次 `batch_size` 个 `archived_ids`，不得再次要求用户确认。归档闸门未通过、`batch_size` 为 0 或映射不一致时，必须停止，绝不取消收藏。

1. `archived_ids` 必须等于已通过归档验证的 `batch_size` 个 BV ID。首次提交设置 `submission_ids = archived_ids`；部分成功后的重试设置 `submission_ids = remaining_ids`。每次都要求 `submission_ids` 是 `archived_ids` 的子集，绝不加入未归档 ID。
2. 仅按 BV ID/视频 URL 定位卡片并勾选。读取已选 ID 集并要求 `selected_ids = submission_ids`，不能多也不能少。
3. 点击“取消收藏”后检查最终弹窗：动作必须是取消收藏，dialog count must equal the size of `submission_ids`，且无额外范围或异常提示。任何不匹配都取消操作并报告。
4. 提交后重新加载收藏页，等待懒加载，并重新计算 `remaining_ids = archived_ids` 中仍出现的 ID。成功提示或数字变化不构成最终验证；已经核验消失的 ID 不得再次提交。
5. 若 `remaining_ids` 非空，最多只对同一已验证归档集中的剩余项重试；同一剩余集连续三次无进展即停止。不得带入新卡片或下一批。

将已验证移除的本地记录 状态改为 `已归档；已取消收藏（页面重新加载后核验）`；未移除项标明 `partial/unresolved`。

## 总结与交付

在相同批次目录创建一份简体中文 Markdown 总结 `summary.md`，包含：目标位置、`batch_size`、可见证据与限制、本批全部标题及 URL、取消收藏结果、未解决项，以及本地封面路径、下载与 MIME 核验结果。验证总结位于同一批次目录、覆盖本批全部 URL，并且状态与本地记录一致后再报告完成。

If summary creation or verification fails, preserve verified files and cleanup state, report partial completion, and do not claim full completion.

## 常见错误

| 错误 | 正确做法 |
| --- | --- |
| 直接勾选“本页全选” | 先证明页面所选 URL 集与 `archived_ids` 完全一致且数量等于 `batch_size`；否则按 BV ID 逐项选择。 |
| 先取消、后归档 | 先完成 `batch_size` 个本地记录的一对一核验。 |
| 相信取消成功提示 | 重新加载并核验全部 `archived_ids`。 |
| 不足 40 条就停止 | 已确认到达收藏夹末尾且 `batch_size` 为 1–39 时，处理当前全部稳定条目。 |
| 扩大到下一批 | 单次调用最多处理 40 条；不足 40 时不得从其他收藏夹或不稳定卡片补足。 |

## 状态一致性

每次清理及重试后，用同目录临时文件加原子替换更新 `archive.json` 和对应 `record.md` 的状态，并读回检查一致性。仅使用 `update` 保存浏览器核验后的 `removed` / `unresolved` 及 evidence，不手工修改文件。写入或核验失败时立即停止后续清理，保留文件，报告已发生的账号操作和未解决 ID。总结必须覆盖固定批次全部 ID、链接、图片路径、成功/失败状态和重试次数；总结失败仅能报告部分完成。用户叫停时不继续下载或清理；单次调用结束后不自动开始下一批。

## 脚本与浏览器交接

`archive` 或 `resume` 输出成功仍不替代取消操作前的 `verify`。只有退出码 0、`cleanup_ready: true`、`verified_ids` 与固定清单完全一致，才可开始浏览器清理；`remaining_ids` 排除已记录为移除的身份。脚本的 `failed` 是本地文件失败，不是账号移除结果。浏览器刷新后的观察才是账号状态证据。

`summary.md` 会在归档时生成并由每次 `update` 更新；它必须通过读回核验。脚本的 verified/pending 表示已归档待清理，verified/removed 表示已归档且浏览器报告核验移除，unresolved 表示清理未解决。图片不完整时 archive_status 为 failed，禁止把部分成功 ID 用于清理。
