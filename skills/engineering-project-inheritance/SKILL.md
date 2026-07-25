---
name: engineering-project-inheritance
description: Use when taking over an existing repository, auditing an old project, deciding whether to refactor, or planning how to continue work from current code and documents.
metadata:
  version: 0.13.0
---

# Engineering Project Inheritance / 接手已有项目

默认尊重现状，不擅自重构。先得到 as-is 证据，再判断走遵循现状、补齐缺失、稳定治理，还是必须重构。

## 何时使用

- 用户给出已有 repo URL 或本地项目路径。
- 用户说“接手”“老项目”“现有项目”“项目很乱”“继续迭代”“该不该重构”。
- 用户要求先判断项目现状、第一周怎么做、下一步怎么继续。

## 工作流

1. 先读取 `references/inheriting-projects.md`。
2. 运行自动识别：文件结构、工具链、项目形态、AI/Agent 痕迹、legacy 文档、git 活跃度。
3. 只在机器看不出的地方做人工作业：业务真相源、生产状态、真实分支模型、owner 和暗坑。
4. 先输出现状报告，再给路径建议。
5. 未完成现状报告前，不做架构重命名、大版本升级、目录重排或泛清理。

## 输出模板

```text
工程路由: Inherit | 接手已有项目 | Review/Governance
当前阶段: I 接手盘点
项目形态: <推断结果>
缺失内容: <文档、运行、测试、业务真相源、owner 等缺口>
下一步 3 个动作:
要创建/更新的文件:
验证门禁: <本地启动 / 现有测试 / smoke / 静态检查>
停止条件: <现状报告完成且路径选定>
```

## 路径判断

| 路径 | 适用条件 | 下一步 |
|---|---|---|
| A 遵循现状，仅补关键缺口 | 结构尚可，本地可跑，CI 或 smoke 有保护 | 补 README / ARCHITECTURE / AGENTS 等缺口 |
| B 稳定 + 治理优先 | 生产在跑但文档或结构薄弱 | 冻结架构变更，补 smoke、as-is 架构和 changelog |
| C 先建文档骨架，再有限演进 | 文档极少、原作者不可达、需要考古 | 代码考古、as-is 架构、风险列表 |
| D 必须重构 | 现状明确阻碍业务推进，且有 owner 授权和验证手段 | 先写目标架构和迁移计划，再小步重构 |

## 反模式

- 第一周直接提重构 PR。
- 把自己的目录偏好套到旧项目。
- 没跑本地环境就写 ARCHITECTURE。
- 删除 TODO/FIXME/HACK 来制造“干净”。
- 跳过业务 owner 同步，只凭代码判断业务意图。

## References

- `references/inheriting-projects.md`：完整盘点 checklist、现状报告模板和路径选择规则。
