---
name: using-engineering-everything
description: Use when starting, resuming, or switching an Engineering Everything session before selecting the kernel router or a direct engineering sub-skill.
metadata:
  version: 0.13.0
---

## EvoZeus-CoEvolve 状态检查

本段是 Skill 入口 preflight。Agent 选中本 Skill 后、进入业务主链路前执行；它基本绑定当前 Skill，但依赖 instruction compliance，不是 native Skill invocation hook。

`.evozeus-wrapper/wrapper.json` 分开记录 capability：`repo_maintenance_hook` 只在 canonical repository 作为活动项目时原生触发；`global_session_dispatcher` 在每个任务启动时聚合检查全部 wrapped Skills；本入口仍记录为 `prompt_runtime_check`。当前 Codex 没有 `SkillInvoke` 事件，不得把前两者描述成 per-Skill native invocation hook。

若当前只是 runtime-only install，缺少维护资产时不要把安装副本当作事实源，回 canonical repo 处理 wrapper harness 或 Skill release。

1. Skill release 状态
   - 当前记录版本：`v0.13.0`
   - 检查命令：`python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything`
   - 如果 GitHub latest release 更新：先更新 canonical repo，并确认 runtime install 仍指向 canonical repo。
   - 如果本地版本领先 GitHub release：先完成 changelog、验证和 `vMAJOR.MINOR.PATCH` release，再把它当作稳定运行版本。
2. Wrapper harness 状态
   - 当前 wrapper 版本：`v0.12.1`
   - 事实源：`.evozeus-wrapper/wrapper.json`
   - 检查命令：在 EvoZeus-CoEvolve repo 运行 `python3 scripts/evozeus_wrapper.py harness upgrade-check --target <this-skill-repo> --json`
   - 如果 wrapper 落后且 `upgrade-check` 未发现冲突或不兼容：报告当前与最新版本；兼容的旧 wrapper 只作为维护提醒，不阻塞业务主链路。
   - 普通 Skill 调用不授权 Harness 升级或其他维护写入。只有用户明确请求 Harness 维护或升级后，才运行 `harness upgrade --dry-run` 生成方案；实际写入仍需单独确认。
3. Source contract 状态
   - 检查命令：`python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything`
   - 如果 `~/.evozeus/.projects`、git origin 或 runtime install 不一致：先修复为同一个 canonical repo，再继续。
4. 调用身份头
   - 检查命令：`python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py identity --json`
   - 读取 `runtime_identity.display_line`，并将其原样放在本次 Skill invocation 第一条用户可见输出的第一行。
   - 身份头固定以 `🧙🏻‍♂️` 开始；禁止使用 HTML、自定义图片或 shortcode 替代。
   - 同一次 invocation 的后续 commentary 和 final 不重复；下一次 invocation 再展示一次。

解决顺序：Source contract 损坏、manifest 无效、迁移冲突或已确认不兼容时停止业务流程并说明原因；其他情况完成只读检查后直接进入主链路。

# Using Engineering Everything / 启动器

这是 Engineering Everything 的 bootloader。它只负责决定是否进入工程化路由、恢复会话上下文、加载主路由和约束输出，不承载具体 route 表。

## 何时使用

- 用户显式使用 `$using-engineering-everything`。
- 任务是复杂工程、组织、自动化、Skill、SOP、项目交付或旧项目接手。
- 会话 resume 后需要判断是继续原 route，还是任务已经切换。
- 用户先给了模糊目标，需要先判断阶段、形态、边界、验证门禁。

## 加载顺序

1. 读取本文件，确认是否进入 Engineering Everything。
2. 读取 `references/route-contract.md`，理解 route 字段和裁决方式。
3. 读取 `references/output-contracts.md`，确定本次输出字段。
4. 读取 `references/codex-tools.md`，确认工具和收尾边界。
5. 进入 `engineering-everything` 主路由；主路由再按 `data/routes.yaml` 命中子 Skill。

## Session / Resume

- 如果用户继续同一任务，先恢复最近一次工程路由、阶段、项目形态、验证门禁和打开的文件。
- 如果用户明显换任务，重新进入主路由，不沿用旧 route。
- context compaction 后，先重建 route summary，再继续执行。
- 不确定是否切换任务时，先问一个澄清问题，不直接实现。

## 停止条件

- route 不明，且缺少足够信息判断下一步。
- 需求、合规、数据源、权限或 owner 决策缺失，却准备进入实现。
- 重构或迁移没有验证门禁。
- 用户不满意时，先 issue-first 询问是否沉淀 lesson，不把主任务默认改路由到 learn。

## Self-Evolution Handoff

只有用户明确要求 `/learn`、`/lesson`、`/pattern`、`/self-evolve`、升级 Skill，或确认要把纠偏沉淀为 lesson issue 时，才交给 `engineering-skill-evolution`。

## EvoZeus-CoEvolve 自进化治理

进入 `engineering-skill-evolution` 后，行为变更必须遵循共享 Skillware 的可追踪发布闭环：

1. 先创建或关联 Skill Feedback Issue，记录问题、期望、复现场景和证据边界。
2. 在 `.evozeus-wrapper/docs/designs/` 建立 design doc，再修改 Skill、route、reference 或 script。
3. PR 同步更新 `.evozeus-wrapper/CHANGELOG.md`，并运行 Engineering Everything 自身验证门禁。
4. 合并后创建 `vMAJOR.MINOR.PATCH` release tag 和 release notes，使兼容用户获得同一共享版本。
5. wrapper harness version 由 `.evozeus-wrapper/wrapper.json` 管理；wrapper migration 只允许 append-only 更新，并记录在 `.evozeus-wrapper/docs/migrations/`。

业务方法和工程路由继续由本 repo 维护。EvoZeus-CoEvolve 只增加证据、评估、版本和恢复治理。

## References

- `references/route-contract.md`：route 字段契约和裁决顺序。
- `references/output-contracts.md`：规划、执行、review、eval 输出契约。
- `references/codex-tools.md`：Codex 工具使用和收尾边界。

## EvoZeus-CoEvolve Migration Note: v0.3.0 -> v0.11.1

- Wrapper harness: `v0.3.0 -> v0.11.1`
- Layout: `scattered-v1 -> consolidated-v2`
- Host hook registration, status prelude, manifest integration, and managed links were refreshed.
- Target business rules were preserved.

## EvoZeus-CoEvolve Recovery Note: v0.11.1 -> v0.11.2

- The first v2 structure gate detected missing policy files and stopped before release.
- CoEvolve v0.11.2 restored the policies from public templates and added canonical sub-Skill pointer validation for this plugin-first Skillware.
- The recommended bootloader and all Engineering Everything business routes remain unchanged.

## EvoZeus-CoEvolve Version Refresh Note: v0.11.2 -> v0.11.4

- Wrapper harness: `v0.11.2 -> v0.11.4`
- Layout: `consolidated-v2 -> consolidated-v2`
- Host hook registration, status prelude, manifest integration, and managed links were refreshed.
- Target business rules were preserved.

## EvoZeus-CoEvolve Version Refresh Note: v0.11.4 -> v0.12.1

- Wrapper harness: `v0.11.4 -> v0.12.1`
- Layout: `consolidated-v2 -> consolidated-v2`
- Host hook registration, status prelude, manifest integration, and managed links were refreshed.
- Target business rules were preserved.
