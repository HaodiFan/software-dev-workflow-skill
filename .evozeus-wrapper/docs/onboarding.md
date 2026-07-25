# 安装、初始化与子 Skill 接入

本页是 wrapper 的通用接入契约。实际命令以 `.evozeus-wrapper/wrapper.json` 的 `onboarding` 字段为准。

## 安装

1. 在 EvoZeus-CoEvolve repo 中运行 `onboarding.installation.command`，把 runtime install 建成指向 canonical repo 的 symlink。
2. 真实目录不会被删除。先用 `--dry-run` 查看计划；确认归档后显式增加 `--approve-archive`。原目录归档到 `~/.evozeus/archives/runtime-installs/`。
3. 运行 `onboarding.installation.verification`，确认 runtime pointer 和 canonical repo 一致。
4. runtime Skill 安装与全局 hook 安装是两个状态；软链接成功不代表 `global_session_dispatcher` 已安装或已信任。

## 全局 Dispatcher

- 在 EvoZeus-CoEvolve repo 先运行 `python3 scripts/evozeus_wrapper.py hook global plan --json`。
- 用户明确确认后运行 `hook global install --approve --json`，结构化合并 `~/.codex/hooks.json`。
- 安装后通过 `/hooks` 审核，再用 `hook global trust --status trusted --approve --json` 记录审核结果。
- global dispatcher 在 `SessionStart` 聚合检查全部 registered wrapped Skills，不精确绑定随后被选中的某个 Skill。

## 调用

- 调用触发词和业务入口归目标 Skill 的 canonical `SKILL.md` 所有，wrapper 不猜测业务调用方式。
- 按 `onboarding.invocation.instruction` 在新的消费项目会话中调用 Skill。
- 运行 `onboarding.invocation.verification`，确认宿主加载的是 canonical repo，并通过 consumer-project smoke test。
- Skill 被选中后，instruction surface 的 `skill_entry_preflight` 在业务主链路前检查当前 Skill；该步骤不是 native hook。

## 初始化

- 初始化逻辑归目标 Skill 所有，wrapper 不实现 company 或业务专用初始化。
- 当 `onboarding.initialization.required` 为 `true` 时，必须运行其中的 `command`，再运行 `verification`；两者缺一不可。
- 当 `required` 为 `false` 时，不额外推断或执行初始化。

## 生成的子 Skill

- 子 Skill 不继承父级 `.codex/hooks.json`，契约固定为 `hooks_inherited: false`。
- 每个子 Skill 必须单独运行 EvoZeus-CoEvolve lifecycle，生成自己的 manifest、hook 配置和验证材料。
- 在 Codex 中通过 `/hooks` 审核并信任新建或变更的 hook。
- 完成条件包括子 Skill structure preflight 和 consumer-project smoke test；只有文件生成成功不算完成。

## Dashboard

- repo-local dashboard 始终保留在 `.evozeus-wrapper/docs/`。
- workflow validation 不依赖 GitHub Pages。
- 只有确认仓库和当前 plan 支持 Pages 后，才设置 repository variable `EVOZEUS_PAGES_ENABLED=true`；否则保持 repository-only mode。
