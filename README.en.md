<div align="center">

[中文](./README.md) · **English**

# 🎯 Requirement Clarifier

#### Turn a vague idea into a clear, copy-pasteable requirement — by asking the right questions

[![License](https://img.shields.io/badge/License-MIT-3B82F6?style=for-the-badge)](./LICENSE)
[![Skills](https://img.shields.io/badge/Skills-1-10B981?style=for-the-badge)](#-skills)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-8B5CF6?style=for-the-badge)](https://agentskills.io)

![Claude Code](https://img.shields.io/badge/Claude_Code-Skill-D97706?style=flat-square&logo=anthropic&logoColor=white)
![Codex](https://img.shields.io/badge/Codex-Skill-10B981?style=flat-square&logo=openai&logoColor=white)

</div>

An AI skill I use myself, open-sourced to share.

This skill is a structured instruction set that agents load directly, following the [Agent Skills](https://agentskills.io) open standard. It works with Claude Code, Codex, CodeBuddy, Cursor, and 40+ other agents that support the standard.

---

## 📋 Index

| Name | One-liner | Article |
|---|---|---|
| 🎯 [**requirement-clarifier**](#-requirement-clarifier) | Turns a vague idea into a clear four-part requirement (goal / decided / unsure / deliverables) | — |

---

## 📦 Install

In any agent that supports Agent Skills (Claude Code, Codex…), just say:

```
Install this skill: https://github.com/YunMeng6364/requirement-clarifier/tree/main/requirement-clarifier
```

Agent doesn't support Skills? Download the `SKILL.md` from the skill's directory and hand it to your agent as a project rule file (or paste it into the conversation) — same effect.

---

## ✨ Skills

<a id="-skills"></a>

### 🎯 requirement-clarifier

> *"You don't have trouble describing your requirement — you just haven't been asked the right questions."*

**It solves exactly one thing: turning a vague ask into a clear requirement.**

You have an idea, but you haven't fully thought it through yourself, let alone know how to hand it to an AI or a developer. This skill asks you a bounded, prioritized, converging set of questions, then turns it into a four-part requirement document: **goal / already decided / still unsure / deliverables**. What you get is a clean block of text you can copy and hand straight to an AI or a developer.

**Why "four-part"**

The biggest failure mode of human–AI collaboration is disagreement on what "done" means. Four parts fix that: **goal** answers "what do we achieve, and how do we know it's done", **decided** pins down known facts and constraints, **unsure** explicitly lists every open question by priority, and **deliverables** fixes the output format and acceptance criteria. It doesn't write code for you — it gets the conversation before the code right.

**How to trigger** (Chinese)

```
帮我梳理需求
我有个想法但说不清
帮我分析一下我要做什么
帮我理清思路
帮我把需求整理出来
```

**Good for**

- You have an idea but it comes out messy and incomplete
- You want to align on the requirement before building, to avoid rework
- You need a structured requirement doc to hand to an AI / developer

**Not good for**

- The requirement is already complete and you just want the AI to build
- Simple fact questions, casual chat, looking things up

→ [SKILL.md](./requirement-clarifier/SKILL.md)

---

## 🌟 About

If this helps you, a ⭐ is appreciated. Questions or suggestions welcome in Issues / Discussions.

---

<div align="center">

[MIT License](./LICENSE) · Free to use, modify, and redistribute

Made by [@YunMeng6364](https://github.com/YunMeng6364)

</div>
