---
name: adding-bilibili-covers-to-devonthink
description: Use when DEVONthink contains Bilibili video bookmarks whose comments include cover image URLs and the user wants paired cover records organized between no-cover and with-cover groups.
---

# 为 DEVONthink 中的 Bilibili Bookmark 添加封面

## 核心原则

一次调用只固定并处理最多 50 个具有真实封面 URL 的视频 bookmark。图片验证并导入成功后，才把同一 UUID 的 bookmark 移到“有封面图”；失败项留在“无封面图”。

UUID 只用于内部身份和重试。封面 `picture` 的 DEVONthink 显示名称必须与 bookmark 名称完全一致，不能附加 UUID、序号或其他后缀。

## 前置条件

- macOS 已安装并可脚本控制 DEVONthink。
- 可执行 `osascript`、`jq`、`curl` 和 `file`。
- 用户提供的根组下必须且只能有同级子组 `01 - 无封面图` 与 `02 - 有封面图`。
- 根组可由 `x-devonthink-item://<UUID>` 取得 UUID。

任何前置条件不满足时停止，不创建替代目录，不猜测目标组。

## 执行

执行前完整阅读 [references/workflow.md](references/workflow.md)。使用随 Skill 提供的脚本，不要临时重写批处理逻辑。

先只读查看本批范围：

```bash
scripts/process-bilibili-covers.zsh --root <DEVONthink UUID> --plan-only
```

确认根组、两个子组以及 `selected_count <= 50` 后执行一次：

```bash
scripts/process-bilibili-covers.zsh --root <DEVONthink UUID>
```

脚本结束后停止。即使仍有可处理 bookmark，也不得在同一次调用中自动启动第二批；新一批需要用户再次调用本 Skill。

## Quick Reference

| 情况 | 处理 |
| --- | --- |
| 可处理项超过 50 | 固定前 50 个，结束后停止 |
| 可处理项不足 50 | 只处理剩余项 |
| 下载、MIME 验证或导入失败 | bookmark 留在源组，不用后续项递补 |
| `i0.hdslb.com` TLS 失败 | 由随附脚本把主机固定替换为 `i1.hdslb.com`；不要手工拼写镜像地址 |
| 标题重复或含非法文件名字符 | UUID 保持身份；临时文件使用 bookmark 已清理的文件名；picture 显示名称仍等于原标题 |
| 备注写 `insufficient metadata` | 不是 URL，跳过并留在源组 |

## Common Mistakes

- 把 50 当作并发数并继续下一批。
- 为避免重名而修改 picture 的显示名称。
- 在封面尚未导入时先移动 bookmark。
- 固定清单后用第 51 项递补失败项。
- 只相信扩展名，不用 `file` 检查实际图片 MIME。
- 手工改写 CDN 主机而写错 `i1.hdslb.com`。
- 目标组缺失或重名时自行创建、选择或猜测。

## Red Flags

- `selected_count > 50`
- picture 名称不等于 bookmark 名称
- “有封面图”出现无 picture 配对的 bookmark
- 同一次调用开始第二批
- 目标子组不是唯一匹配

出现任一项即停止，保留已完成的有效配对并报告边界，不扩大处理范围。
