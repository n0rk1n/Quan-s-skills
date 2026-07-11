## 目标

修改 `archiving-to-devonthink`，使 DEVONthink MCP 成为不可降级的硬性依赖，并把同一天生成的 Codex 对话归档文件集中放进 DEVONthink Global Inbox 下的每日目录。

## 目录规则

- 每日目录名为 `YYYY-MM-DD Archived Codex Conversations`。
- 日期使用技能调用时的本地日期。
- 目录位于 DEVONthink Global Inbox 中。
- 每次调用先查找当天同名目录：存在时复用，不存在时创建。
- 不创建同一天的重复目录。

## MCP 门槛

- 开始生成临时 Markdown 文件前，必须确认 DEVONthink MCP 可以查询数据库、查找或创建目录并导入文件。
- DEVONthink MCP 不可用、能力不完整或调用失败时，立即停止。
- 不允许改用 AppleScript、直接写入 DEVONthink 数据库包、仅生成本地文件或跳过 DEVONthink 导入。

## 文件导入

- 继续生成原有两个独立 Markdown 文件：`（Codex 原文）`和`（Codex 归档）`。
- 两个文件都必须导入当天的每日目录，不能直接放在 Global Inbox 根目录或其他目录。
- 优先导入原文，再更新归档笔记中的原文引用并导入归档笔记。
- 原有命名、内容、校验、临时文件清理及 Codex 对话归档门槛保持不变。

## 失败处理

- 找不到 Global Inbox、无法确认或创建每日目录、无法识别目录 UUID，均视为未满足导入门槛。
- 任一文件未能导入每日目录时，不删除尚需保留的临时文件，也不归档 Codex 对话。
- 最终报告分别说明 DEVONthink MCP 状态、每日目录、两个文件的导入状态、临时文件清理状态与 Codex 对话归档状态。

## 验收标准

1. 规则明确禁止在 DEVONthink MCP 不可用时执行降级流程。
2. 目录英文固定为 `Archived Codex Conversations`。
3. 同一天已有目录时复用，没有时创建。
4. 两个生成文件都以每日目录为可识别目的地。
5. 原有工作流中与这三项变更无关的内容保持不变。
