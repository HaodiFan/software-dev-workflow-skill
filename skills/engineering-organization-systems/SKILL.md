---
name: engineering-organization-systems
description: Use when engineering an organization, company mechanism, SOP, onboarding, interview process, non-software project, WBS, estimate, workspace, knowledge base, table, or document-led operating system.
metadata:
  version: 0.13.0
---

# Engineering Organization Systems / 组织系统工程

组织、企业、SOP、培训、面试、非工程项目和知识资产都可以工程化：目标、角色、接口、节奏、指标、异常处理和复盘必须闭环。

## 何时使用

- 用户提到面试、入职、培训、组织、企业、SOP、流程、制度、协同机制。
- 用户要非工程项目方案、WBS、排期、人天、成本估算。
- 用户要文件输出、Skill、多维表、知识库或运营工作区。

## 工作流

1. 先定义目标和 owner：谁决策、谁执行、谁验收。
2. 拆流程和接口：输入、输出、状态、责任、时间、异常。
3. 定指标和验收：SMART、周验收、RACI/RAID、证据矩阵。
4. 对执行者保持低摩擦；管理字段尽量自动化或从流程生成。
5. 区分对内草案、已审核文档和正式对外材料。

## 输出模板

```text
工程路由: Organization System | <面试/入职/SOP/项目估算/知识库> | Product/Governance
当前阶段: 0 想法 / 1 需求澄清 / 5 Feature 规划 / 7 验证
项目形态: Organization System / Non-software Project
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

- 没有 owner、验收人、目标或时间边界。
- 产出面向外部，却包含内部语言、未审核状态或推测。
- 人天/成本缺单价、角色配置、范围或验收标准。

## References

- `references/engineering-scenarios.md`：面试、入职、组织/SOP、项目估算、非软件产物。
- `references/templates-core.md`：README / DEVELOPMENT / AGENTS 等核心模板。
- `references/templates-specs.md`：需求和方案模板。
- `references/checklists.md`：组织、项目和产物验证 checklist。
