# Design Doc: Engineering Everything 多 Skill 拆分 v0.1

> Update 2026-06-28: 本设计中的根 `SKILL.md` 和 `--layout legacy` 兼容策略已由 `.evozeus-wrapper/docs/designs/2026-06-28-root-skill-demotion.md` 取代。当前结构为 plugin-first，运行时入口只在 `skills/*/SKILL.md`。

## TLDR

把 Engineering Everything 从单个超大 Skill 拆成 plugin-style skill library：主 `engineering-everything` 只做路由和协作纪律，场景能力下沉到独立子 skill。Phase 1 迁移 `engineering-project-inheritance` 作为 pilot；Phase 2 补齐各场景薄子 skill；Phase 3 已把各场景 reference 迁入对应子 skill，并由 route seed 指向 skill-local references。

## 背景

当前根 `SKILL.md` 已到 200 行软上限，同时 `references/architecture-cases.md`、`architecture-cases-ai.md`、`prompts-guide.md` 等 reference 很大。继续把所有场景塞进一个入口，会让 agent 每次加载过多上下文，也让路由、内容、验证、治理混在同一个文件里。

参考 `superpowers` 的方式，正确方向是一个 repo 暴露多个可独立发现的 skill，而不是一个主 skill 内部维护所有流程。

## 目标

- 主 skill 变薄：只负责判断工程路由、选择子 skill、定义输出契约。
- 子 skill 独立触发：每个场景有自己的 `name`、`description`、正文和必要 reference。
- 安装兼容：`scripts/install.py --target both` 默认安装所有 `skills/*` 子 skill。
- 验证可重复：`scripts/skill_doctor.py` 同时检查根兼容入口、plugin manifest、子 skill frontmatter、路由 seed 和 reference 链接。
- 行为保持：`$engineering-everything` 仍然可用，只是变成薄路由器。

## 非目标

- 不重写架构、自动化、组织和发布 reference 的业务内容；本次只做归属迁移和路由收敛。
- 不改变 lesson/pattern/self-evolution 的业务规则。
- 不引入 Python 包管理、测试框架或新依赖。

## 目标结构

```text
engineering-everything/
├── .codex-plugin/plugin.json
├── SKILL.md                         # 兼容入口，内容与主路由保持一致
├── skills/
│   ├── engineering-everything/              # 主路由 skill
│   ├── engineering-product-definition/      # 产品定义
│   ├── engineering-architecture-design/     # 架构设计
│   ├── engineering-execution-planning/      # 执行规划
│   ├── engineering-build-verify/            # 构建验证
│   ├── engineering-refactoring/             # 重构治理
│   ├── engineering-review-release/          # Review / 发布
│   ├── engineering-automation-playbooks/    # 自动化场景
│   ├── engineering-organization-systems/    # 组织 / 非软件系统
│   ├── engineering-project-inheritance/     # 接手已有项目
│   └── engineering-skill-evolution/         # Skill 自进化
├── references/                      # legacy/source 兼容副本；运行时以子 skill references 为准
├── scripts/
└── schemas/
```

## 子 Skill 拆分候选

| 子 skill | 状态 | 内容来源 |
|---|---|---|
| `engineering-project-inheritance` | 已拆出 | `references/inheriting-projects.md` |
| `engineering-product-definition` | 已自包含 | `psps-framework.md`、`spec-templates.md`、Stage 0-2 |
| `engineering-architecture-design` | 已自包含 | `architecture-cases*.md`、`project-blueprints.md` |
| `engineering-execution-planning` | 已自包含 | `execution-pipeline.md`、review roles |
| `engineering-build-verify` | 已自包含 | Stage 6、validation commands、agent standards |
| `engineering-refactoring` | 已自包含 | `refactoring-rules.md` |
| `engineering-review-release` | 已自包含 | `code-review-standards.md`、PR readiness |
| `engineering-automation-playbooks` | 已自包含 | `scenario-playbooks.md` |
| `engineering-organization-systems` | 已自包含 | `engineering-scenarios.md` |
| `engineering-skill-evolution` | 已自包含 | `lessons.md`、`patterns-skill.md`、self-evolution harness |

## Phase 1 方案

1. 新增 plugin manifest，声明 `skills: ./skills/`。
2. 新增薄主路由 skill：`skills/engineering-everything/SKILL.md`。
3. 将根 `SKILL.md` 收缩为同一薄路由，保留旧安装兼容。
4. 新增 pilot 子 skill：`skills/engineering-project-inheritance/SKILL.md`。
5. 复制 `references/inheriting-projects.md` 到 pilot 子 skill 内，使其可独立安装。
6. 更新 `install.py`：默认安装 `skills/*` 到本地 skill 根目录；提供 `--layout legacy` 保留旧整包安装。
7. 更新 `skill_doctor.py`：检查 plugin manifest、子 skill frontmatter、重复 skill 名、重复 aliases、skill reference 链接和 README 说明。

## Phase 2 方案

1. 为剩余 9 条路线新增薄 `skills/<name>/SKILL.md`。
2. 更新 `data/routes.yaml`，让每条 route 的 `skill` 字段指向对应子 skill。
3. 更新 `skill_doctor.py` 的必需 skill 列表，避免后续回退到半拆状态。
4. 当时暂不复制大型 root references 到每个子 skill；Phase 3 已完成自包含迁移。

## Phase 3 方案

1. 将每个子 skill 需要的 reference 复制到 `skills/<skill>/references/`。
2. 为每个子 skill 的 `SKILL.md` 补充本地 `References` 列表。
3. 将 `data/routes.yaml` 的 `references` 改为 `skills/<skill>/references/*.md`。
4. 更新 `skill_doctor.py`：route 有 `skill:` 时，所有 reference 必须位于该 skill 的 `references/` 下。
5. 保留根 `references/` 作为 legacy/source 兼容副本，避免破坏 `--layout legacy`。

## 验证门禁

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/self_evolve.py doctor --json`
- `python3 scripts/lesson.py validate`
- `python3 scripts/install.py --target both --dry-run`
- `python3 scripts/install.py --target both --layout legacy --dry-run`

## 风险与处理

| 风险 | 处理 |
|---|---|
| 子 skill 装到本地后找不到根 `references/` | Phase 3 已把运行时 reference 迁入各子 skill；doctor 禁止 route 回指 root reference |
| 根 `SKILL.md` 与 `skills/engineering-everything/SKILL.md` 漂移 | doctor 检查两者版本和主入口存在；后续可加强文本同步 |
| 一次迁移太多导致行为变化不可控 | Phase 3 只迁移 reference 归属和路由引用，不重写 reference 内容 |
| 旧用户依赖整包安装 | `install.py --layout legacy` 保留旧整包安装 |

## 后续优化顺序

1. 去重各子 skill 中重复的通用 reference，抽成共享包或保留 legacy source。
2. 将大型 reference 继续拆小，例如 architecture 和 automation 按主题拆分。
3. 为每个子 skill 增加专项 doctor 规则，检查必要 reference 是否存在。
4. 发布前对比本地 `0.9.9` 与 GitHub release，并决定是否打新 tag。
