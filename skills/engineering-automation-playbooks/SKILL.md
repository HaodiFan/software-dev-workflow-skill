---
name: engineering-automation-playbooks
description: Use when designing or implementing RPA, OCR, CV, LLM production pipelines, browser automation, data governance, analytics reporting, or POC/spike automation.
metadata:
  version: 0.13.0
---

# Engineering Automation Playbooks / 自动化场景

自动化先选稳定数据路径，再选模型或脚本。API/导出优先于 UI 自动化；结构化输出、trace、人审和失败重放优先于一次性 demo。

## 何时使用

- 用户提到 RPA、OCR、CV、LLM、浏览器自动化、数据分析、报表、POC/spike。
- 任务涉及第三方平台、文档识别、图片/视频、LLM pipeline、经营数据或页面自动化。
- 需要判断 API、导出、Playwright/Selenium、桌面/手机 RPA、OCR、VLM、LLM、数仓等路线。

## 工作流

1. 先拆来源：官方 API、导出、DB、页面、桌面客户端、移动端、文件、图片。
2. 定最小切片：单来源、单 schema、单指标或单任务闭环。
3. 明确合规与授权，记录账号、频率、数据保留和人工接管。
4. AI/LLM 任务先做类型分流，不默认纯 LLM。
5. 验证输出 schema、trace、失败状态、重试、回放和人审路径。

## 输出模板

```text
工程路由: Scenario | <RPA/OCR/CV/LLM/Data/POC> | Architecture/Build
当前阶段: P POC/Spike / 3 架构 / 6 实现
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

- 授权、平台 ToS、PII 或账号风控边界不清。
- 没有输出 schema，却要做 OCR/LLM 抽取。
- 没有 trace 和失败状态，却要长期运行自动化。

## References

- `references/scenario-playbooks.md`：RPA、OCR、CV、数据治理、LLM、浏览器自动化、POC。
- `references/architecture-cases-ai.md`：AI / Agent 架构选型。
- `references/architecture-cases.md`：通用数据、异步、自动化和部署架构。
- `references/checklists.md`：场景验证 checklist。
