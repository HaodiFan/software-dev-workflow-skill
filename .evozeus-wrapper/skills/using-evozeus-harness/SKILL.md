---
name: using-evozeus-harness
description: Use when a wrapped Skill entry activates the canonical EvoZeus-CoEvolve Harness contract before its business flow.
metadata:
  version: "v1.1.0"
---

# Using EvoZeus Harness

本 Skill 是 EvoZeus-CoEvolve 在目标仓库内唯一的 Harness 指令事实源。目标业务入口只保留指向本文件的强制 Read 块；读取完成后，先确认状态，再进入业务主链路。

## 运行时契约

1. 读取同一仓库的 `.evozeus-wrapper/wrapper.json`，以 `canonical_repo`、`instruction_surface`、`wrapper_version`、`harness_skill_path`、`harness_skill_version`、`integration.mode` 和 `integration.capabilities` 为事实。
2. 定位 manifest 所属的本地 canonical Repo 根目录并在该目录执行只读检查。`canonical_repo` 是 `OWNER/REPO` 标识，禁止把它当作 `--target` 路径：
   - `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure --target .`
   - `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --target .`
   - `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py identity --target . --json`
3. 将 `identity --json` 返回的 `runtime_identity.display_line` 放在本次调用第一条用户可见消息首行，同一次调用只显示一次。
4. identity 由 `.evozeus-wrapper/policies/notice-policy.json` 渲染；普通业务输出不展示额外 EvoZeus Notice。
5. 检查通过后进入业务主链路。兼容旧 Harness 产生维护提醒；路径越界、manifest 损坏、canonical Harness Skill 缺失或版本不兼容会阻断执行。

按 manifest 解释 integration 事实，不根据模板文字推断当前模式：

- `prompt_runtime_check`：instruction surface 提供检查入口，执行依赖指令遵循。
- `bootstrap_skill`：Plugin lifecycle 可加载控制 Skill；具体覆盖范围以 `plugin_lifecycle_hook` capability 和实际 hook/plugin 文件为准。
- `manual_only`：没有已证明的自动入口，按需运行只读命令。
- 其他 mode：逐项核对 `capabilities` 与实际文件后再说明覆盖范围。

任何 mode 都不能自行宣称存在 native `SkillInvoke`。仅当 manifest capability 与宿主实际证据共同证明 `skill_invocation_hook` supported、installed 且 native enforced 时，才能报告原生单次 Skill invocation 覆盖；repo maintenance hook 与全局 session dispatcher 仍各自遵守 manifest 中的 scope。

若当前目录属于 runtime-only install，所有维护动作回到 `canonical_repo` 执行。安装副本只用于运行和定位事实源。

## 意图路由与授权边界

正常业务调用只执行上面的运行时契约。以下低频资料在对应意图出现后再读取：

- 业务调用：完成上述只读检查，继续目标 Skill 的业务流程。
- Feedback Issue：按需读取 `.evozeus-wrapper/policies/feedback-policy.json` 与 `.evozeus-wrapper/policies/audit-rule.md`；先纠正当前结果并形成脱敏 Lesson，仅在用户确认记录后创建 Skill Feedback Issue。
- Issue-to-PR：按需读取 EvoZeus-CoEvolve 的相关流程 Skill；创建或修复分支、提交、推送与 PR 均需要对应授权。贡献分支契约消费 #36 的最终规范，本 Skill 不重复定义该契约。
- Harness 维护：回到 EvoZeus-CoEvolve canonical Repo，按需读取 `skills/harness-upgrade/SKILL.md`、`.evozeus-wrapper/WRAPPER.md` 与 `.evozeus-wrapper/docs/migrations/README.md`。维护流程固定为 inspect → plan → approve → apply → verify → rollback；普通 Skill 调用不授权 Harness 写入、升级或发布。
- UAT：按需读取 `.evozeus-wrapper/WRAPPER.md` 的验收门禁，仅在用户要求验收时进入并记录证据与结论。
- Release：按需读取 `.evozeus-wrapper/CHANGELOG.md` 与 preflight release 合同，仅在用户授权发布后执行，要求版本、tag 与 release notes 一致。
- rollback：出现验证失败或不兼容时停止写入；按迁移计划记录的 repo 外 snapshot 恢复完整 write set，再验证 preimage hash。Git commit revert 只作为 snapshot 回滚后的版本控制动作。

私有会话、客户资料、secret 与未脱敏商业上下文不得进入公开 Issue、设计文档、PR 或 Release 记录。

## 维护闭环

Harness 维护采用 Issue → design doc → focused implementation → tests → UAT → Release → rollback record。目标业务规则始终由业务入口拥有。历史标题、frontmatter、regex 命中或 terminal signature 只形成只读 discovery candidate。已安装 canonical v1.1 的 activation block 缺失或损坏时进入 manual repair。对于本 Skill 尚未存在的 reviewed v0.14→v1.1 transition，block absent 只能作为 CoEvolve external supervised profile 的受信 precondition；冻结 envelope、CommonMark AST、完整 `SKILL.md` preimage、retained complement 与 exact operation approval 全部通过后才可插入。其他证据缺失场景保持零写入并进入 manual review。
