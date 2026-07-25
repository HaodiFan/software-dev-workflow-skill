# 对内-未审核-Engineering Everything 测试与验证说明

本文档说明当前仓库的本地验证门禁。它不是 release notes；发布前仍以 `.evozeus-wrapper/CHANGELOG.md` 和对应 release checklist 为准。

## 当前必跑

```bash
python3 scripts/sync_references.py --check --json
python3 scripts/eval_scenarios.py validate --json
python3 scripts/skill_doctor.py --json
python3 scripts/self_evolve.py check --json
python3 scripts/lesson.py validate
python3 -m unittest discover -s tests
python3 -m py_compile scripts/*.py
```

## Gate 分层

- Reference gate：`sync_references.py` 检查 root reference、runtime copy、route/SKILL reference 是否一致，防止 drift、orphan 和未声明 root-only。
- Behavior schema gate：`eval_scenarios.py` 检查 `evals/scenarios/*.md` 的 route、output field、entrypoint 和 reference 是否存在。
- Package gate：`skill_doctor.py` 聚合结构、metadata、README、route、reference、eval 和自进化约束。
- Evolution gate：`self_evolve.py check` 与 `lesson.py validate` 检查 lesson/pattern/schema。
- Python gate：`unittest` 和 `py_compile` 验证脚本行为与语法。

## Release 前额外检查

涉及 GitHub issue、push、tag 或 release 时，加跑：

```bash
python3 scripts/self_evolve.py doctor --json
python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py structure
python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py doctor --repo HaodiFan/engineering-everything
python3 .evozeus-wrapper/scripts/evozeus_wrapper_preflight.py version --repo HaodiFan/engineering-everything --current-tag v0.13.0
```

`v0.13.0` 是 plugin-first package 与 CoEvolve harness migration 的 release tag。发布前必须确认 changelog、版本元数据、验证记录和 GitHub release notes 一致。
