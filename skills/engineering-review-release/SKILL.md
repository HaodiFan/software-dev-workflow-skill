---
name: engineering-review-release
description: Use when reviewing code, PRs, merge readiness, CI failures, release risk, rollback plans, or deciding whether a change is safe to ship.
metadata:
  version: 0.13.0
---

# Engineering Review Release / Review 与发布

默认 code-review 立场：问题先行，按严重度列 bugs、风险、回归、缺测试和发布阻断。摘要永远次要。

## 何时使用

- 用户要求 review、PR、merge、release、发布、CI、是否 ready。
- 需要判断行为风险、测试证据、回滚和发布门禁。
- 需要修 CI 或检查发布流程。

## 工作流

1. 先看 diff、相关上下文和测试证据。
2. 按严重度列 findings，必须有文件/行号或明确证据。
3. 区分阻断、建议、开放问题和残余风险。
4. 发布前检查：配置、迁移、回滚、监控、兼容、数据风险。
5. 没有问题就明确说无发现，并说明测试缺口。

## 输出模板

```text
Findings:
Open questions:
Change summary:
Tests / release gates:
Residual risk:
```

## 停止条件

- 没有 diff、PR、分支或变更范围，无法 review。
- 用户要求“批准”但缺运行时验证，只能做静态 review。
- 发现 P0/P1 行为风险、数据风险或安全风险未处理。

## References

- `references/code-review-standards.md`：代码审查口径。
- `references/checklists.md`：PR readiness 与发布 checklist。
- `references/execution-pipeline.md`：review roles 和 release gates。
- `references/stage-playbook.md`：Stage 7-8 判断。
