---
name: engineering-architecture-design
description: Use when choosing technical architecture, project shape, stack, data source, boundaries, deployment model, AI/Agent architecture, or scaffold strategy.
metadata:
  version: 0.13.0
---

# Engineering Architecture Design / 架构设计

先判断项目形态和真相源，再选技术栈。架构不是偏好清单，而是对运行位置、数据来源、团队能力、退出成本和验证门禁的取舍。

## 何时使用

- 用户问技术栈、架构、选型、脚手架、从 0 搭项目、agent app。
- 项目形态不清楚：Web+Backend、Desktop+Local Agent、Python CLI、Library、Full-stack Monorepo 等。
- 涉及 AI/Agent、RAG、LLM 网关、工具调用、权限、审计、成本和延迟。

## 工作流

1. 先定项目形态：用户在哪里运行、真相源在哪里、是否跨 app 共享、是否需要本地 runtime。
2. 再定边界：前后端关系、后端形态、数据架构、协议、鉴权、异步、部署、可观测性。
3. AI 项目先做任务类型分流，不默认等于 LLM 项目。
4. 对关键决策写清推荐、反例、代价、退出成本和最小验证。
5. 触及长期边界时，要求 ADR 或 design doc 记录。

## 输出模板

```text
工程路由: Architecture | 架构设计 | Architecture
当前阶段: 3 架构 / 4 脚手架
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

- 业务需求、数据源、权限或部署约束不清楚，却准备新增架构层。
- 只凭流行技术选型，无法解释代价和退出成本。
- 没有 spec，却要新增状态机、存储、权限或公共 API。

## References

- `references/architecture-cases.md`：通用架构选型。
- `references/architecture-cases-ai.md`：AI / Agent 专项架构。
- `references/app-for-agent-design-paradigm.md`：给 agent 操作的 app 设计范式。
- `references/project-blueprints.md`：项目形态 starter。
- `references/templates-governance.md`：ADR / CONSTITUTION 等治理模板。
- `references/checklists.md`：架构和发布前 checklist。
