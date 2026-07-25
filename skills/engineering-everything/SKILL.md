---
name: engineering-everything
description: Use when a task needs engineering-route judgment before choosing product definition, project inheritance, architecture, execution, build, refactor, review, release, organization, automation, or skill-evolution work.
metadata:
  version: 0.13.0
---

# Engineering Everything / 工程化万物

Engineering Everything 是主路由 Skill。它不承载所有场景细节，只负责先判断任务属于哪条工程路径，再加载对应子 skill 或 reference。

## 使用原则

新会话推荐先用 `$using-engineering-everything` 进入 bootloader；`$engineering-everything` 仍可作为直达主路由。

先判断，再行动。不要在路由未明时直接写代码、重构、补架构或编造业务需求。

用户不满意是全局捕获信号，不是 Learn 主路由。只要用户在使用 Engineering Everything 时表达否定、纠偏或不满意（如“不对”“不是”“这部分好乱”“你没有参考”“方案不行”），agent 必须先承认具体偏差，并主动询问是否要把这次纠偏创建为 GitHub lesson issue；用户确认后再按 issue-first 流程处理，不能默认直接写 `lessons.md`。当前任务仍按原本命中的工程路由继续，不因为用户不满意就把主任务改路由到 `engineering-skill-evolution`。

规划类回答必须使用 `references/output-contracts.md` 的规划 / 路由输出契约。不能只说“用了 Engineering Everything”；必须把关键判断和已读取的 reference 对上，至少覆盖路由、阶段、项目形态、验证门禁这 4 类判断。未读取的候选 reference 不要伪装成依据。

执行类回答收尾必须包含：变更文件 / 已运行验证 / 未运行检查及原因 / 剩余风险。

## 子 Skill 路由

先按优先级判断，再选择目标路线：

`接手项目 > 安全/合规 > 用户明确执行 > 用户明确重构 > 业务场景 > 项目形态 Unknown > 组织/非软件 > 显式 learn/evolution`

### 已拆出的场景子 Skill

- `engineering-project-inheritance`：接手、老项目、现有 repo、继续迭代。
- `engineering-product-definition`：需求、PRD、产品定义、PSPS、想法澄清。
- `engineering-architecture-design`：技术栈、架构、选型、脚手架、agent app。
- `engineering-execution-planning`：feature 拆解、implementation plan、worktree、review roles。
- `engineering-build-verify`：实现、修 bug、迁移、接接口、验证命令。
- `engineering-refactoring`：重构、清理、模块化、技术债。
- `engineering-review-release`：review、PR、merge、release、发布。
- `engineering-automation-playbooks`：RPA、OCR、CV、LLM、浏览器自动化、数据分析。
- `engineering-organization-systems`：面试、入职、组织、企业、SOP、非工程项目估算、非软件产物。
- `engineering-skill-evolution`：用户明确要求记录 lesson、创建 lesson issue、沉淀 pattern、自进化或升级 skill。

## 不可突破的规则

- 业务需求必须来自用户或 owner；agent 只负责结构化、校验和追问。
- 没有 spec，不新增架构层、状态机、存储、权限、全局依赖或公共 API。
- 接手项目默认尊重现状，不擅自重构。
- 重构必须行为保持，有验证门禁，不混 feature / bug fix / format / dependency upgrade。
- 改 Skill 结构、版本、引用或安装路径后必须跑 `scripts/self_evolve.py check` 与 `scripts/skill_doctor.py`；涉及线上 repo 或发布时加跑 `scripts/self_evolve.py doctor`。

## References

- 源仓库的 `data/routes.yaml` 是机器可读路由 seed。
- `references/output-contracts.md` 是规划、执行、review 和 eval 输出契约。
- 源仓库的旧版 route map 仅作为 legacy/source 校准；运行时 route seed 已指向子 skill。
- 源仓库的 `references/self-evolution-harness.md` 定义 GitHub lesson issue-first 的自进化门禁。
