---
title: "Agent 智能体原理"
date: "2026-08-18"
category: "大模型应用"
tags: ["Agent", "LLM", "工具调用", "ReAct"]
description: "介绍基于大模型的智能体开发架构与核心组件"
---


## Agent 是什么

Agent 是一个能够自主规划、决策并执行任务的智能体。

## 核心架构

### ReAct 模式
- **Thought**：思考下一步做什么
- **Action**：执行动作（调用工具）
- **Observation**：观察结果
- 循环直到完成任务

### 示例

```
Thought: 我需要查询天气
Action: search_weather("北京")
Observation: 北京今天晴，温度 25°C
Thought: 天气查询成功，我来总结
Final Answer: 北京今天晴，温度 25°C
```

## 关键组件

### 1. LLM 核心
- 理解用户意图
- 生成行动计划
- 处理反馈

### 2. Tools 工具集
- 搜索引擎
- 计算器
- 数据库查询
- API 调用

### 3. Memory 记忆
- 短期记忆：当前对话
- 长期记忆：历史知识
- 上下文窗口

### 4. Planner 规划器
- 任务分解
- 步骤排序
- 动态调整

## LangGraph 编排

```python
from langgraph.graph import StateGraph

# 定义状态
class AgentState(TypedDict):
    messages: list
    current_step: str

# 构建图
graph = StateGraph(AgentState)
graph.add_node("think", think_node)
graph.add_node("act", act_node)
graph.add_node("observe", observe_node)

# 添加边
graph.add_edge("think", "act")
graph.add_edge("act", "observe")
graph.add_edge("observe", "think")
```

## 应用场景

- 智能客服
- 数据分析助手
- 代码助手
- 研究助理
