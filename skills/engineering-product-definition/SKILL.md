---
name: engineering-product-definition
description: Use when clarifying a product idea, PRD, requirements, PSPS, user scenario, scope, non-goals, or success criteria before architecture or implementation.
metadata:
  version: 0.13.0
---

# Engineering Product Definition / 产品定义

把模糊想法变成可构建、可验证、可拒绝扩张的需求边界。业务意图必须来自用户或 owner；agent 负责结构化、校验和追问。

## 何时使用

- 用户说“我有个想法”“帮我写 PRD”“需求怎么定义”“PSPS”“用户场景不清楚”。
- 当前还没有可执行 spec、成功指标、非目标或验收标准。
- 架构、实现、排期依赖业务边界先清楚。

## 工作流

1. 明确一句话定义：用户、系统类型、核心能力、核心问题、P0 非目标。
2. 抽取 PSPS：Persona、Scenario、Pain、Solution Surface。
3. 区分事实、假设、待用户回答；不要用合理想象填业务需求。
4. 给出 P0/P1/P2 范围，P0 必须能形成最小闭环。
5. 只有需求完备性足够时，才进入 design doc、架构或实现。

## 输出模板

```text
工程路由: Product | 产品定义 | Product
当前阶段: 0 想法 / 1 需求澄清 / 2 Spec
项目形态: <候选形态，不超过 3 个>
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

- 缺少业务 owner、目标用户、核心流程或成功指标，且错误假设代价高。
- 用户要求 agent 编造业务需求，而不是结构化已知事实。
- P0 范围无法形成可验收闭环。

## References

- `references/psps-framework.md`：PSPS 构建洞察框架。
- `references/spec-templates.md`：需求、Design Doc 和模板路由。
- `references/templates-specs.md`：Requirements / Design Doc 具体模板。
- `references/checklists.md`：需求完备性与验证 checklist。
- `references/stage-playbook.md`：Stage 0-2 阶段判断。
