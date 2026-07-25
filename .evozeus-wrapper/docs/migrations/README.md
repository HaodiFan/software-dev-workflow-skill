# Wrapper Migrations

本目录记录 EvoZeus-wrapper harness version 迁移。这里只记录 wrapper-managed 结构、脚本和治理逻辑的迁移，不记录目标 Skill 的业务内容。

## 迁移原则

- `.evozeus-wrapper/wrapper.json` 是 wrapper harness version 的事实源。
- 当前仓库采用 plugin-first 结构；运行时入口在 `skills/*/SKILL.md`，repo root 不保留 `SKILL.md`。
- wrapper 状态检查由 `.codex-plugin/plugin.json`、`.evozeus-wrapper/WRAPPER.md`、`.evozeus-wrapper/docs/index.md` 和 preflight 脚本承载，不写入运行时 Skill 正文。
- wrapper-managed files 可以按迁移方案复制或合并；如果已有本地修改，必须先做 merge review。
- Skill release version 和 wrapper harness version 是两条版本轴，不能互相覆盖。

## 每次迁移必须记录

- From wrapper version。
- To wrapper version。
- 迁移原因。
- Planned files / changed files。
- plugin/library 入口处理结果。
- wrapper governance 文档处理结果。
- 验证命令和结果。
- 回滚方案。
