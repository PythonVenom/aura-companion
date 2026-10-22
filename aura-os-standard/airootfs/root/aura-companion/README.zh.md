# Aura — 本地家庭 AI 伙伴

> 一个本地优先、面向家庭的 AI，会说话、会行动、会记忆。
> 不是语音助手——**世界中介**。

![Tests](https://img.shields.io/badge/tests-1339_passed-green)
![Evals](https://img.shields.io/badge/evals-44%2F44_100%25-green)
![ADR](https://img.shields.io/badge/ADR-99-blue)
![Handlers](https://img.shields.io/badge/handlers-22-orange)
![Routes](https://img.shields.io/badge/routes-7-purple)

## Aura 是什么

Aura 是一个**本地家庭 AI 中介**，连接人与数字世界：

- 语音优先（ASR + TTS，ru）
- 本地 LLM（Ollama，无云）
- 22 个能力处理器（music / time / app / browser / power / control / care / journal）
- 行为树路由（7 个叶子）
- i18n：ru / en / zh / es
- 99 个 ADR——所有决策都有文档
- 1339 个单元测试 + 44 个 golden evals
- Honeypots、threat model、backup

## 快速开始

    git clone https://github.com/PythonVenom/aura-companion.git
    cd aura-companion
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m aura

## 理念

- **本地优先**：数据不离开你的机器
- **面向家庭**：关怀代理、语音日记、老年人友好
- **等离子自适应**：幂等补丁、代码后 ADR、发布门
- **反脆弱**：每个红色漏洞都变成绿色优势

## 语言

- [English](README.md)
- [Русский](README.ru.md)
- [中文](README.zh.md)
- [Español](README.es.md)

## 许可证

MIT
