# 对内-未审核-Engineering Everything AgentOS Bootloader 重构设计

> Update 2026-06-28: root `SKILL.md` 已由 `2026-06-28-root-skill-demotion.md` 设计退场；本文件中 root entry 相关描述仅保留为 v0.12.0 历史背景。

## Related issue

- Issue: direct owner request in Codex thread.
- What was unsatisfactory: Engineering Everything 已经具备通用工程 AgentOS 的路由内核和子 Skill 库，但“如何使用这套体系”仍依赖用户显式调用 `$engineering-everything`、README 或口头约定。
- Expected behavior: 新增轻量 bootloader Skill，让 agent 在进入复杂工程任务前知道何时调用 Engineering Everything、如何进入 kernel router、如何保持输出和停止条件。

## Optimization goal

把“如何使用 Engineering Everything 体系”从说明文字升级成可加载、可测试、可发布的 Skill，同时避免新增第二套路由事实源。

成功标准：

- agent 不跳过 kernel router 直接凭感觉调用子 Skill。
- route、output、reference、eval 各自只有一个 canonical source。
- 当前可执行 gate 与未来 release gate 明确分开。
- 安装脚本不会误删 canonical repo 或 runtime pointer。
- bootloader 行为有结构化 eval 证据。

## Implementation status - 2026-06-28

本轮已开始落地 Phase 0/1 的可验证最小集：

- 已新增 `using-engineering-everything` bootloader，保持 `$engineering-everything` 直达主路由兼容。
- 已新增 output/route/tool contracts、reference 分发 manifest、eval scenario schema、testing doc 和单元测试。
- 已把 `scripts/install.py` 扩展为 install/update/relink/uninstall/list，并增加 canonical repo 删除保护。
- 已让 `scripts/skill_doctor.py` 聚合 route contract、reference distribution 和 eval scenario gate。
- 已规划并准备发布 `v0.12.0`；release 前版本元数据统一 bump 到 `0.12.0`。

本轮未做：

- 不启用 SessionStart hook。
- 发布 `v0.12.0` 前必须完成 release gates；SessionStart hook 不随本次发布启用。
- 不替 owner 决定 license；`.codex-plugin/plugin.json` 仍保持 `UNLICENSED`。
- 不新增 `data/route_fixtures.yaml`；当前先用 `evals/scenarios/*.md` 作为行为契约骨架。

## Direction / 优化方向

采用“先收束事实源，再新增 bootloader”的方向：先修安装安全、license/status、reference 分发和版本审计，再新增 `using-engineering-everything`。不把 bootloader 做成第二个 router；route、output、reference、eval 都必须各自有唯一 canonical source。

## Core decisions

### 1. 分层命名

| 层 | 负责 | 不负责 |
|---|---|---|
| `repo root SKILL.md` | source/package entry；EvoZeus-wrapper 状态检查；legacy install 兼容 | 不作为日常 runtime router 的唯一入口 |
| `skills/using-engineering-everything/SKILL.md` | bootloader；判断是否进入体系、加载顺序、session/resume 策略、停止条件提醒 | 不最终判定具体 route；不复制场景 playbook |
| `skills/engineering-everything/SKILL.md` | kernel router；工程路由、阶段、项目形态、子 Skill/reference 选择 | 不承载场景执行细节 |
| `skills/engineering-*` | system services；对应场景执行、handoff、停止条件和 reference 索引 | 不改全局 route priority |
| `references/` | authoring canonical knowledge base | 不作为运行时全量加载入口 |
| `skills/*/references/` | runtime distribution copies | 不接受手工漂移修改 |

### 2. 单一事实源

- Route canonical：`data/routes.yaml`。升级为 route contract，增加 `priority`、`conflicts`、`fallback`、`handoff_to`、`direct_call_allowed`、`eval_cases`。`route-contract.md` 只做解释性索引，不手写 normative route 数据。
- Output canonical：root `references` 下的 `output-contracts.md`。bootloader、root SKILL、kernel SKILL、README 只保留字段名和短引用；运行时副本由 `data/reference_distribution.yaml` 分发给需要的 Skill。不要把 output contract 放在 bootloader 目录下，否则 `$engineering-everything` 直达 kernel router 时会形成层级倒挂。
- Reference canonical：根 `references/`。`skills/*/references/` 只由 `data/reference_distribution.yaml` 分发。现存未声明副本必须先清点并标记 `keep/remove/legacy/owned-by`。
- Eval canonical：`evals/scenarios/*.md`。人工行为检查只引用 scenario ID，不重复维护 prompt 和 expected behavior。

### 3. Trigger policy

Phase 1 只承诺显式入口，不承诺自然语言自动触发：

- 显式 `$using-engineering-everything`：先 bootloader，再 kernel router。
- 显式 `$engineering-everything`：允许直接进入 kernel router，但输出必须保留 route summary。
- Slash alias：先按 `data/routes.yaml` 映射，再进入对应子 Skill。
- 自然语言复杂任务自动触发：属于 host adapter / SessionStart hook 能力，推迟到 Phase 3。

Session/resume 策略：

- “继续/接着”已有工程路由：恢复 route、phase、verification gate，不重置。
- 明显换任务：重新 route。
- context compaction 后：先恢复最近 route summary，再判断是否重路由。

## Proposed structure

```text
data/
  reference_distribution.yaml
skills/
  using-engineering-everything/
    SKILL.md
    references/
      output-contracts.md        # exact managed copy
      route-contract.md          # explanatory only; checked from manifest
      codex-tools.md
  engineering-everything/
    references/
      output-contracts.md        # direct router runtime copy
references/
  output-contracts.md
  route-contract.md
  codex-tools.md
docs/
  testing.md
evals/
  scenarios/
    route-before-building.md
    no-spec-no-architecture.md
    no-validation-no-refactor.md
    dissatisfaction-issue-first.md
    review-findings-first.md
    session-resume.md
    task-switch-reroute.md
scripts/
  eval_scenarios.py
  sync_references.py
tests/
  test_eval_scenarios.py
  test_install_safety.py
  test_sync_references.py
```

## Implementation plan

### Phase 0 - Safety and source contracts

必须先完成，不能和 bootloader 行为混在同一风险面。

- Fix `scripts/install.py` symlink/canonical repo safety:
  - deletion uses unresolved install path;
  - symlink replacement uses `unlink()`;
  - reject deleting resolved target equal to or inside canonical repo;
  - define explicit `install/update/relink/uninstall/list --dry-run` contract.
- Ensure install lifecycle discovers future library skills:
  - `discover_skill_packages()` must include `using-engineering-everything`;
  - install, update, relink, uninstall, and list must operate from discovered packages, not hardcoded README lists;
  - uninstall dry-run must cover every installed `engineering-*` and `using-engineering-everything` skill.
- License is a blocking owner decision:
  - owner decision remains required before public distribution positioning changes;
  - before decision, README/manifest must not imply permissive open-source distribution;
  - local Phase 0/1 refactor can proceed while keeping manifest license as `UNLICENSED`.
- Add version audit plan:
  - define `package_version` source;
  - keep `wrapper_harness_version`, future `hook_schema_version`, and future `eval_schema_version` separate.
- Add `data/reference_distribution.yaml` and `scripts/sync_references.py --check`.
- Inventory existing `skills/*/references/*` copies and mark each as `keep/remove/legacy/owned-by`.

### Phase 1 - Bootloader and contracts

- Add `skills/using-engineering-everything/SKILL.md` with only:
  - when to enter Engineering Everything;
  - loading order;
  - session/resume rules;
  - stop conditions;
  - self-evolution handoff.
- Add root `references` `output-contracts.md` as the only full output template source, then distribute runtime copies through `data/reference_distribution.yaml`.
- Upgrade `data/routes.yaml` into the route contract; keep `route-contract.md` explanatory only.
- Add `evals/scenarios/*.md` with structured frontmatter.
- Add `scripts/eval_scenarios.py validate`.
- Add `docs/testing.md`.
- Add route fixtures for known overlap cases:
  - Architecture vs Automation;
  - Build Verify vs Review Release;
  - Product Definition vs Organization Systems.
- Update `skill_doctor.py` to validate new contracts without hardcoding the old `$engineering-everything` default prompt.
- Update `skill_doctor.py` required skill list and README checks so `using-engineering-everything` is recognized as an installed library skill while `$engineering-everything` remains a supported direct router entry.

### Phase 2 - Productization and CI gates

- Update `.codex-plugin/plugin.json` and `agents/openai.yaml` only after manifest contract is updated to allow bootloader entry.
- Update README first screen:
  - what this AgentOS is;
  - 30-second use;
  - supported/experimental/not-yet harness matrix;
  - install/update/uninstall lifecycle;
  - current limitations.
- Move maintainer dashboard content out of `.evozeus-wrapper/docs/index.md` or make it clearly maintainer-only.
- Add PR template Behavior Evaluation fields:
  - scenario IDs;
  - entrypoint;
  - expected/actual;
  - pass/fail;
  - harness/model/date.
- Update workflow to run real gates, not only wrapper PR preflight.
- Update `.evozeus-wrapper/CHANGELOG.md` Unreleased for this scope.

### Phase 3 - Optional SessionStart hook

Only after manual/eval behavior evidence passes.

- Add `hooks/hooks-codex.json`.
- Add `hooks/session-start-codex`.
- Add `.codex-plugin/plugin.json` `hooks` field.
- Hook matcher must explicitly cover startup/resume/clear or explain omissions.
- Hook must inject only `using-engineering-everything`, not full references.
- Add hook JSON output tests and token/privacy notes.

## Behavior eval schema

Each scenario uses frontmatter:

```yaml
---
schema_version: 1
id: route-before-building
harness: codex
entrypoint: explicit_bootloader
session_event: manual
introduced_in: 0.12.0
min_package_version: 0.12.0
prompt: "我想做一个电商管理系统，直接帮我搭架构。"
expected_route_ids:
  - automation
  - architecture
required_fields:
  - 工程路由
  - 当前阶段
  - 项目形态
  - 验证门禁
must:
  - 询问平台范围、数据源和合规边界
must_not:
  - 直接输出架构实现方案
forbidden_skill_ids:
  - engineering-build-verify
expected_references:
  - skills/engineering-automation-playbooks/references/scenario-playbooks.md
stop_condition: "数据源和合规边界未确认前，不进入采集实现"
---
```

## Verification plan

### Current gates

These are valid before implementation:

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/lesson.py validate`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py pr --design-doc .evozeus-wrapper/docs/designs/2026-06-28-agentos-bootloader-refactor.md`

### Phase 0 acceptance

- `python3 scripts/install.py --target both --layout library --dry-run`
- Symlink fixture: runtime pointer replacement must not delete canonical repo.
- `python3 scripts/sync_references.py --check`
- Version audit command, once implemented.
- `python3 -m unittest tests.test_sync_references`

### Phase 1 acceptance

- `python3 scripts/eval_scenarios.py validate`
- `python3 -m unittest discover -s tests`
- Route fixture validation is deferred; current minimum is route contract validation inside `scripts/skill_doctor.py`.
- Manual checks by scenario ID:
  - `route-before-building`
  - `no-spec-no-architecture`
  - `no-validation-no-refactor`
  - `dissatisfaction-issue-first`
  - `review-findings-first`
  - `session-resume`
  - `task-switch-reroute`

### Release gates

- All current gates.
- All Phase 0 and Phase 1 acceptance gates.
- PR body includes Behavior Evaluation evidence for any change under `SKILL.md`, `skills/`, `references/`, `data/routes.yaml`, manifests, or hooks.
- Release notes include behavior change, linked design doc, verification commands, known limitations, and rollback plan.

## Release plan

- Target tag: `v0.12.0`.
- Release scope: bootloader Skill, source contract cleanup, reference distribution gate, behavior eval skeleton, install safety guard.
- Do not enable SessionStart hook in `v0.12.0` unless Phase 3 tests are implemented and passed.

## Rollback and migration matrix

| Phase | New/changed files | Rollback |
|---|---|---|
| Phase 0 | `scripts/install.py`, `data/reference_distribution.yaml`, `scripts/sync_references.py`, version/license docs | Revert script and manifest changes; verify runtime pointers still resolve to canonical repo |
| Phase 1 | `skills/using-engineering-everything/`, `evals/`, `docs/testing.md`, route/output contracts, tests | Remove bootloader; keep generic safety tests only if still applicable; remove bootloader-specific evals |
| Phase 2 | README, docs/index, PR template, workflow, manifests, CHANGELOG | Restore previous entry docs and CI gates; ensure `$engineering-everything` remains valid |
| Phase 3 | hooks, plugin `hooks` field, hook tests | Remove hook manifest and scripts; verify plugin still loads skills without SessionStart injection |

Rollback success requires:

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- runtime installs point to canonical repo or are cleanly removed.

## Risks

- Bootloader/router overlap: mitigated by keeping route facts in `data/routes.yaml`.
- Output template drift: mitigated by making `output-contracts.md` the only full template source.
- Reference drift: mitigated by distribution manifest, `sync_references.py --check`, and `test_sync_references.py` fixtures for drift and undeclared copies.
- Install damage: mitigated by symlink fixture and canonical repo deletion guard.
- License ambiguity: blocked until owner chooses license/status.
