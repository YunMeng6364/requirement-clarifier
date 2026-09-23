<div align="center">

**中文** · [English](./README.en.md)

# 🎯 Requirement Clarifier

#### 把一句模糊的想法，聊成一份能直接拿去执行的清晰需求

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-1-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)

</div>

这是我自己每天在用的一个 AI Skill，开源出来分享。

这里的每个 Skill 都是 Agent 能直接加载的结构化指令集，遵循 [Agent Skills](https://agentskills.io) 开放标准。Claude Code、Codex、CodeBuddy、Cursor 等 40+ 支持该标准的 Agent 都能装。

---

## 📋 目录

| 名字 | 一句话 | 讲解 |
|---|---|---|
| 🎯 [**requirement-clarifier（需求澄清器）**](#-requirement-clarifier需求澄清器) | 把模糊的诉求，聊成「目标 / 已确定 / 拿不准 / 产出要求」四段式清晰需求 | — |

---

## 📦 安装方式

在 Claude Code、Codex 等支持 Agent Skills 的工具里，直接说：

```
帮我安装这个 skill：https://github.com/YunMeng6364/requirement-clarifier/tree/main/requirement-clarifier
```

你的 Agent 不支持 Skill 也没关系：把对应目录的 `SKILL.md` 全文下载下来，当成项目规则文件（或直接贴进对话）让 Agent 照着执行，效果一致。

---

## ✨ Skills

<a id="-skills"></a>

### 🎯 requirement-clarifier（需求澄清器）

> *"你不是说不清需求，你只是还没被问到点子上。"*

**它只解决一件事：帮你把模糊的诉求聊清楚。**

你有过一个想法，但自己都还没想明白，更不知道怎么让 AI 或开发去实现——这个 Skill 会通过**有边界、有优先级、可收敛**的多轮提问，把它梳理成一份「目标 / 已确定 / 拿不准 / 产出要求」四段式需求文档。你最后拿到的是一段可以直接复制、拿去继续和 AI 对话、或交给开发的干净文本。

**为什么是「四段式」**

人和 AI 协作最大的坑，是双方对「要做什么」的理解不一致。四段式把话说清楚：**目标**回答「最终要达成什么、怎样算完成」，**已确定**写死已知的事实和约束，**拿不准**显式列出所有不确定点并按优先级排，**产出要求**约定交付物、格式和验收标准。它不帮你写代码，它帮你把「写代码之前的那些话」说对。

**怎么触发**

```
帮我梳理需求
我有个想法但说不清
帮我分析一下我要做什么
帮我理清思路
帮我把需求整理出来
```

**适合**

- 脑子里有想法，但一开口就乱、说不完整
- 想开工前先把需求对齐，避免做了一半返工
- 需要一份能直接复制给 AI / 开发的结构化需求文档

**不适合**

- 需求已经很完整，只想让 AI 直接开干
- 单纯问事实、闲聊、查资料

→ [SKILL.md](./requirement-clarifier/SKILL.md)

---

## 🌟 关于

开源出来如果对你有帮助，给个 ⭐ 就行。有问题或建议，欢迎在 Issues / Discussions 里说一声。

---

<div align="center">

[MIT License](./LICENSE) · 自由使用 / 修改 / 再分发

Made by [@YunMeng6364](https://github.com/YunMeng6364)

</div>
