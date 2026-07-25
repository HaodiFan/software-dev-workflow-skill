---
name: engineering-skill-evolution
description: Use when evolving a skill, capturing lessons, promoting patterns, changing routes, updating references, installing skills, validating skill packages, or publishing skill releases.
metadata:
  version: 0.13.0
---

# Engineering Skill Evolution / Skill 自进化

Skill 升级不是继续堆理念，而是把纠偏分成 lesson、pattern、reference、script/gate 或 install sync，并用验证门禁收口。

## 何时使用

- 用户说“记住”“以后都这样”“自进化”“升级 skill”“拆成子 skill”“发布 skill”。
- 需要改 `SKILL.md`、routes、reference、scripts、plugin manifest 或安装路径。
- 需要比较本地安装、source repo、GitHub release 或同步 Codex/Agents 副本。

## 工作流

1. 先定位 canonical source；安装副本只作为部署目标。
2. 判断变更类型：lesson、pattern、reference、script/gate、route、install、release。
3. 主 `SKILL.md` 只做路由；新知识默认下沉 reference，重复动作进入 scripts。
4. 改结构、版本、路由或安装路径后，必须跑 self-evolve 与 doctor gates。
5. 发布前再检查 GitHub origin、release tag、安装副本和版本一致性。

## 输出模板

```text
工程路由: Learn | Skill 自进化 | Governance
当前阶段: 8 PR/发布 / 9 维护
项目形态: Library/SDK
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

## 验证门禁

- `python3 scripts/skill_doctor.py --json`
- `python3 scripts/self_evolve.py check --json`
- `python3 scripts/lesson.py validate`
- 涉及 GitHub issue、push、release 时加 `python3 scripts/self_evolve.py doctor --json`

## 停止条件

- 只改安装副本，没改 canonical source。
- 新规则适用范围不清，却写入 Skill 级运行逻辑。
- 验证脚本失败，或版本、manifest、README、安装副本不一致。

## References

- `references/self-evolution-harness.md`：Skill 自进化流程和 gate。
- `references/lessons.md`：L1 纠偏日志。
- `references/patterns-skill.md`：L2 可复用模式。
- `references/prompts-guide.md`：capture / promote 等 prompt 工作流。
