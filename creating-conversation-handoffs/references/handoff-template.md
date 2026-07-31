# Conversation Handoff Templates

Replace every `{{snake_case}}` token before publishing. The validator rejects
unresolved tokens. Keep the snapshot's level-two headings exactly as written.

# 对话交接：{{task_slug}}

## 元数据

- Schema 版本：1
- 生成时间：{{generated_at}}
- 任务摘要：{{task_summary}}
- 旧会话来源：{{source_reference}}
- 项目或 worktree 根目录：{{project_root}}
- 上一个快照：{{previous_handoff}}

## 续接摘要

{{continuation_summary}}

## 用户目标与验收标准

{{goal_and_acceptance}}

## 必须了解的背景

{{essential_background}}

## 相对上次交接的变化

{{changes_since_previous}}

## 事实与证据

| 状态 | 事实 | 证据或最后核实时间 |
| --- | --- | --- |
| 已验证 | {{verified_fact}} | {{verified_evidence}} |
| 用户确认 | {{confirmed_requirement}} | {{confirmation_source}} |
| 待核实 | {{unverified_fact}} | {{why_unverified}} |

## 已完成事项

{{completed_work}}

## 当前工作区状态

{{workspace_state}}

## 决策与理由

{{decisions_and_reasons}}

## 失败尝试与避坑点

{{failed_attempts_and_pitfalls}}

## 未完成事项与下一步

**首个可执行步骤：** {{first_executable_step}}

1. {{ordered_follow_up}}

## 阻塞项与待确认问题

{{blockers_and_questions}}

## 关键文件、命令与外部资源

{{critical_resources}}

## 来源信息与回查

- 旧会话来源：{{source_reference}}
- 生成时间：{{generated_at}}
- 上一个快照：{{previous_handoff}}
- 宿主或会话类型：{{source_host}}
- 回查要求：{{lookup_instruction}}

## 新对话续接指令

完整读取本快照，复核易变化事实并报告影响执行的差异；不要重复已完成事项，从首个可执行步骤继续。内容不足且阻塞执行时，按旧会话来源回查。

# LATEST.md 模板

```markdown
# 最新对话交接

- 最新快照：[{{snapshot_label}}]({{snapshot_relative_path}})
- 生成时间：{{generated_at}}
- 旧会话来源：{{source_reference}}
- 任务摘要：{{task_summary}}
```
