# 对内-未审核-Root SKILL 退场设计

## Related issue

- Issue: direct owner request in Codex thread.
- What was unsatisfactory: `v0.12.0` 已把运行时能力内化到 `skills/`，但 repo root 仍保留 `SKILL.md`，导致结构不像 `superpowers` plugin，也让 runtime entry 与 package governance 混在一起。
- Expected behavior: repo 采用 plugin-first 结构；运行时只从 `skills/*/SKILL.md` 进入，root 不再是 Skill。

## Optimization goal

删除 root `SKILL.md`，并把所有 gate 改成 plugin/library 结构：

- package version 事实源是 `.codex-plugin/plugin.json`。
- runtime entry 只来自 `skills/using-engineering-everything/SKILL.md` 和 `skills/engineering-everything/SKILL.md`。
- EvoZeus/source governance 进入 `.evozeus-wrapper/WRAPPER.md`、`.evozeus-wrapper/docs/index.md` 和 `references/self-evolution-harness.md`。
- legacy whole-repo skill install 不再作为推荐路径。

## Direction

这是结构重构，不改变 v0.12.0 的运行时行为。先让本地 gate 通过，再决定是否发布为 `v0.13.0`。

## Implementation plan

1. 删除 root `SKILL.md`。
2. 更新 `scripts/skill_doctor.py`，以 plugin manifest 为 package version source。
3. 更新 `scripts/self_evolve.py`，检查 plugin/library contract，不再要求 root Skill。
4. 更新 `.evozeus-wrapper/scripts/evozeus_wrapper_preflight.py`，检查 plugin/library wrapper contract，不再要求 root status prelude。
5. 更新 README、dashboard、WRAPPER 和 changelog，把 root Skill 从当前结构中移除。
6. 跑完整本地 gate。

## Verification plan

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure`
- `python3 scripts/eval_scenarios.py validate --json`
- `python3 scripts/sync_references.py --check --json`
- `python3 scripts/lesson.py validate`
- `python3 -m unittest discover -s tests`
- `python3 -m py_compile scripts/*.py`
- `git diff --check`

## Release plan

- Recommended next release: `v0.13.0`.
- Rationale: minor structural change to package contract; runtime entry remains compatible through `skills/engineering-everything`, and `$using-engineering-everything` remains recommended.
- Release is not part of this change until owner explicitly asks to publish.
