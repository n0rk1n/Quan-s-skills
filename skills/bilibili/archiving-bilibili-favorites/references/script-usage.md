# 本地归档脚本用法

依赖 Python 3.10+、`curl`、`file`。脚本仅操作真实用户的 `~/Downloads`，不访问浏览器、不登录 Bilibili、不取消关注或收藏。每个技能携带同一实现，按所属技能目录选择收藏或关注模式；单独安装完整技能目录即可运行，无需安装另一个技能。不要单独移动或重命名技能目录。

## 输入数据

浏览器负责从可见页面产生 JSON 文件，不在 shell 中拼接网页文本。顶层字段：

- `source_url`：实际观察的列表页面 HTTP(S) URL。
- `end_confirmed`：收藏短批次（1–39）必须为 true，表示浏览器确认到了当前收藏夹末尾；40 条可为 false。关注模式不使用该字段。
- `items`：固定目标数组。收藏 1–40 项，关注必须恰好 24 项，不能递补失败图片对应的身份。

每项包含字符串 `id`、`canonical_url`、`display_name`、`image_source_url`，以及可选 `metadata` 对象。缺少名称时由浏览器提供有依据的 ID 名称占位；普通缺失元数据标记 `insufficient metadata`。图片 URL 必须真实可下载，不可用占位文字替代。

收藏输入示例（示意值；实际执行必须替换为页面观察值）：

```json
{
  "source_url": "https://space.bilibili.com/123/favlist",
  "end_confirmed": true,
  "items": [{
    "id": "BV0000000001",
    "canonical_url": "https://www.bilibili.com/video/BV0000000001",
    "display_name": "页面上的视频标题",
    "image_source_url": "https://i0.hdslb.com/observed-cover.png",
    "metadata": {"作者": "页面可见作者", "备注": "insufficient metadata"}
  }]
}
```

关注每项改用数字字符串 UID、`https://space.bilibili.com/<UID>` 和实际头像 URL，metadata 保存简介、页面顺序及核验需要的可见信息；将 24 项放进 items。视频/账号 ID 是目录名，重复标题与斜线不影响文件保存。

## 命令

将 `SKILL_DIR` 设置为当前完整技能目录的绝对路径；`INPUT_JSON`、`BATCH_DIR`、`STATUS_JSON` 分别指实际输入文件、脚本返回的批次目录和浏览器核验结果文件路径。所有变量加引号。

```sh
python3 "$SKILL_DIR/scripts/archive_bilibili.py" preflight
python3 "$SKILL_DIR/scripts/archive_bilibili.py" archive --input "$INPUT_JSON"
python3 "$SKILL_DIR/scripts/archive_bilibili.py" verify --batch "$BATCH_DIR"
python3 "$SKILL_DIR/scripts/archive_bilibili.py" update --batch "$BATCH_DIR" --input "$STATUS_JSON"
```

`preflight` 在观察列表前运行，只检查依赖和 Downloads 读写，不创建批次。
`archive` 校验 JSON 后自动选择新批次编号，写记录、图片、清单和中文总结并读回核验。
`verify` 只读核验已有批次：路径、身份映射、实际 MIME、图片 SHA-256、Markdown 内容与总结一致性。锁存在时不给出可清理目标。
`update` 只记录浏览器提供的核验结果并更新 Markdown、清单和总结，不能用它代替浏览器核验。

除 preflight 返回 `ready: true` 外，成功输出为：

```json
{"batch":"绝对批次路径","cleanup_ready":true,"verified_ids":["本批全部ID"],"remaining_ids":["尚未记录为移除的ID"],"failed":[]}
```

退出码 0 才可使用结果。任何失败返回非零退出码、`cleanup_ready: false`、空 verified_ids/remaining_ids 和失败原因；已写出的有效文件保留。每次清理前重新 verify，并要求 verified_ids 与浏览器固定批次完全相等。remaining_ids 仍需浏览器新鲜观察，不代表这些 ID 当前必然仍在列表。

## 图片失败与中断恢复

同一批次图片失败后可运行：

```sh
python3 "$SKILL_DIR/scripts/archive_bilibili.py" resume --batch "$BATCH_DIR"
```

只重试该批未成功的图片，复核并复用已成功图片，不重新观察下一批，不修改原始 ID 或图片 URL。整个批次成功前不清理账号；清理已开始后禁止 resume。文件损坏、已有未核验图片或路径冲突不覆盖，报告失败供检查。临时图片不会被计为成功图片。

curl 禁用 URL 通配展开，原样请求观察到的 URL。一次 curl 使用 15 秒连接超时、60 秒单次超时、最多 2 次内置重试，并受 200 秒外层超时限制。仅当原主机精确为 i0.hdslb.com 且 curl 报 TLS 错误时，允许保持路径/查询不变改为 i1.hdslb.com 再运行一次。验证实际 PNG/JPEG/WebP/GIF 类型后确定扩展名，不信任 URL 后缀。`image_download_url` 记录交给 curl 的原始或镜像请求地址，不冒充重定向后的最终 URL。

脚本用 `.archive.lock` 排斥同批并发写入。若进程被强制终止留下锁，先确认记录 PID 的进程已结束，再人工检查本批状态后清除该锁；不能自动忽略锁或开启新批掩盖失败。跨文件更新不是数据库事务：若中途写入失败，verify 会拒绝不一致状态。清理已经发生时保留外部操作证据并报告部分完成，不盲目重试。

## 浏览器状态输入

仅把已通过工作流规定的即时／刷新后核验的 ID 写为 removed；尚未解决的写为 unresolved。例：

```json
{"items":[{"id":"BV0000000001","status":"removed","evidence":"重新加载当前收藏夹并等待加载后，已核验此 BV ID 消失；本项重试 0 次。"}]}
```

关注 evidence 应记录逐 UID 状态、起始页刷新结果、操作前后关注总数及重试次数；收藏 evidence 记录对应 ID 的刷新核验结果和重试次数。首次点击后的即时成功不能冒充最终 removed。

`update` 拒绝未知 ID、重复 ID、空证据和将已移除 ID 改回待处理。它只能检查证据字段存在，不能判断证据是否真实，浏览器必须先完成核验。每次核验操作后及时保存；写入失败时停止后续账号操作。相同批次的 summary.md 保留全部标题、链接、图片路径、状态和浏览器证据。
