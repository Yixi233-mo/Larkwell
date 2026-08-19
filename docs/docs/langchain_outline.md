---
title: "LangChain 学习大纲"
date: "2026-08-18"
category: "大模型应用"
tags: ["LangChain", "LLM", "Agent", "RAG", "工具调用"]
description: "介绍LangChain框架开发大模型应用的核心组件和实践"
---


## LangChain 学习路线

### 第一部分：基础入门
1. **LangChain 概述** - 了解框架架构
2. **Models（模型）** - LLM 集成
3. **Prompts（提示模板）** - Prompt Engineering
4. **Parsers（解析器）** - 输出结构化

### 第二部分：核心能力
5. **Indexes（索引）** - 向量索引
6. **Memory（记忆）** - 对话上下文
7. **Chains（链）** - 组合多个步骤

### 第三部分：高级主题
8. **Agents（智能体）** - 自主决策
9. **Tools（工具）** - 外部能力扩展
10. **Retrieval（检索）** - RAG 模式

## 核心概念

### Chain 模式

```python
from langchain import LLMChain

chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run("你好")
```

### Agent 模式

```python
from langchain.agents import initialize_agent

agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
agent.run("帮我搜索最新的AI研究")
```
