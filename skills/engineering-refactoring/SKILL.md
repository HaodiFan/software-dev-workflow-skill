---
name: engineering-refactoring
description: Use when refactoring, cleaning up, modularizing, renaming, reducing technical debt, or preserving behavior while improving structure.
metadata:
  version: 0.13.0
---

# Engineering Refactoring / 重构治理

重构必须行为保持。先识别真实坏味道，再选手法和保护网；不要把 feature、bug fix、格式化和依赖升级混进同一个重构。

## 何时使用

- 用户说重构、清理、模块化、技术债、拆文件、改结构、rename。
- 当前代码结构阻碍理解、修改、测试或发布。
- 需要降低维护成本，但不应改变用户可见行为。

## 工作流

1. 明确重构目标：降低哪类成本，保护哪些行为。
2. 找到坏味道证据：重复、过长、耦合、隐式状态、边界混乱。
3. 先补或确认验证网：现有测试、smoke、快照、静态检查。
4. 小步改动：一类重构一组提交，不混 feature。
5. 复跑验证，并说明行为保持证据。

## 输出模板

```text
工程路由: Refactor | 行为保持型重构 | Maintenance
当前阶段: 9 维护
项目形态:
参考依据:
- 路由规则:
- 已读 reference:
- 外部/历史依据:
缺失内容:
下一步 3 个动作:
要创建/更新的文件:
验证门禁:
停止条件:
```

## 停止条件

- 没有行为保护网。
- 重构动机只是风格偏好。
- 改动会改变业务行为、数据模型或公共 API，却没有 spec/ADR。

## References

- `references/refactoring-rules.md`：坏味道、重构手法和行为保持 gate。
- `references/checklists.md`：重构与验证 checklist。
- `references/execution-pipeline.md`：PR 拆分、review pipeline、验证流程。
- `references/stage-playbook.md`：Stage 9 维护判断。
