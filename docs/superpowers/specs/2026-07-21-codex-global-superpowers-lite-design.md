# Codex 全局 Superpowers Lite 设计

日期：2026-07-21

## 背景

当前电脑安装了 Superpowers 6.1.1，但所有 Skills 仍按插件默认规则暴露；`~/.codex/config.toml` 没有单项禁用设置，`~/.codex/AGENTS.md` 为空。另一台电脑已经采用混合式 Lite 配置，将 Superpowers 从每个任务都强制执行的方法论，调整为复杂或高风险工程任务按需使用的工具箱。

本次目标是把同一套全局策略同步到当前电脑，同时保留高价值的排障、验证、审查与隔离能力。

## 设计决策

采用“配置层硬禁用 + 全局行为层路由”的混合方案。

只修改 `config.toml` 虽然禁用明确，但无法继续手动调用被禁用的 Skill，并且带版本号的插件缓存路径在升级后需要维护。只修改全局 `AGENTS.md` 更稳定，但无法消除 `using-superpowers` 的强制入口。混合方案能可靠减少默认流程开销，同时保留其余 Skills 的按需使用能力。

## 配置层

在 `~/.codex/config.toml` 中通过 `[[skills.config]]` 禁用以下三个入口：

- `using-superpowers`
- `dispatching-parallel-agents`
- `subagent-driven-development`

每个条目使用当前 Superpowers 6.1.1 缓存目录中对应 `SKILL.md` 的绝对路径，并设置 `enabled = false`。

这三个 Skill 被选中是因为它们分别承担全局强制调用、默认并行代理和子代理驱动开发的入口。禁用后，其他 Superpowers Skills 仍保持可用。

## 行为层

在全局 `~/.codex/AGENTS.md` 中写入 Superpowers Lite 路由规则：

- 普通问答、解释、只读检查、范围明确的简单配置和局部修改直接处理。
- 只有遇到真实 bug、测试失败或异常行为时才使用 `systematic-debugging`。
- 发生实际代码或配置修改时，在宣称完成前使用 `verification-before-completion` 并取得最新验证证据。
- `brainstorming`、`test-driven-development`、`writing-plans` 和 `using-git-worktrees` 仅在任务复杂、高风险、跨越多个组件，或用户明确要求时使用。
- 子代理和并行代理只在用户明确要求时使用。
- 不因某个 Skill 内部出现 `MUST` 或 `ALWAYS`，自动把轻量任务升级为完整工程流程。
- 用户在当前任务中的明确指令优先；若用户要求快速处理或不用 Superpowers，则遵循该次指令，但不降低必要的安全与验证标准。

## 安装流程

1. 根据当前文件生成候选 `config.toml` 与候选 `AGENTS.md`。
2. 使用支持 `tomllib` 的 Python 解析候选 TOML。
3. 检查候选文件差异，确保只新增预期的 Skill 禁用项与 Lite 路由规则。
4. 把当前全局配置备份到独立的临时目录。
5. 将候选文件安装到 `~/.codex/config.toml` 和 `~/.codex/AGENTS.md`。
6. 重新解析安装后的 TOML，并核对三个禁用路径与预期集合完全一致。
7. 对全局文件与候选文件做逐字节比较。

## 验证与验收

静态验收标准：

- `config.toml` 能被 TOML 解析器成功读取。
- 三个且仅三个目标 Superpowers Skill 被新增为禁用状态。
- 原有 Codex 配置保持不变。
- 全局 `AGENTS.md` 完整包含 Lite 路由规则。
- 安装后的全局文件与审查过的候选文件逐字节一致。
- `git diff --check` 通过，且提交仅包含本设计文档。

动态验收需要重启 Codex 后在新任务中完成：

- 三个被禁用的 Skills 不再出现在可用列表中。
- 简单任务不会自动进入 brainstorming、计划或多代理流程。
- 真实测试失败仍会触发系统排障。
- 实际修改在完成声明前仍会执行验证。

## 风险与维护

禁用项引用包含版本号的插件缓存路径。Superpowers 升级后，旧路径可能不再匹配；因此每次升级插件后都应检查版本目录，并按需更新三个 `[[skills.config]]` 路径。全局 `AGENTS.md` 作为稳定的第二层保护，即使硬禁用路径失效，也会继续约束默认行为。

本次实施不会移除插件、修改其他 Skills、启用默认多代理，也不会改动与此目标无关的项目文件。
