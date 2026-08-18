"""创建示例文档填充 Larkwell 知识库"""
import os
import json
from pathlib import Path

OUTPUT_DIR = Path("./docs/docs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 示例文档内容
sample_docs = [
    {
        "title": "图神经网络学习大纲",
        "slug": "graph_neural_network",
        "body": """
## 一、学习路径总览

### 第一篇：基础与认知
- 数学与图论基础
- 深度学习基础
- 图神经网络概述

### 第二篇：核心技术
- 图卷积网络 GCN
- 图注意力网络 GAT
- 图采样与 Mini-batch

### 第三篇：进阶与实战
- 大规模图训练
- 异构图神经网络
- 图神经网络应用

## 二、核心概念

### 什么是图神经网络

图神经网络（Graph Neural Network, GNN）是一种专门用于处理图结构数据的深度学习模型。

### 主要类型

1. **GCN (Graph Convolutional Network)** - 基于谱域的图卷积
2. **GAT (Graph Attention Network)** - 引入注意力机制
3. **GraphSAGE** - 采样与聚合

## 三、应用场景

- 社交网络分析
- 推荐系统
- 分子性质预测
- 知识图谱推理
"""
    },
    {
        "title": "LangChain 学习大纲",
        "slug": "langchain_outline",
        "body": """
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
"""
    },
    {
        "title": "RAG 检索增强生成",
        "slug": "rag_introduction",
        "body": """
## RAG 是什么

RAG（Retrieval-Augmented Generation）是一种结合**信息检索**与**文本生成**的框架，使 LLM 能够基于外部知识库生成回答。

## RAG 架构

```
用户提问 → 向量检索 → 召回文档 → LLM 生成 → 返回答案
```

## 核心组件

### 1. 文档处理
- 文档加载与清洗
- 文本切分（Chunking）
- Embedding 向量化

### 2. 向量数据库
- Milvus / Pinecone / FAISS
- 存储文档向量
- 相似度检索

### 3. 生成模型
- 根据检索结果生成回答
- 支持引用来源

## LangChain RAG 实现

```python
from langchain.vectorstores import Milvus
from langchain.embeddings import SentenceTransformerEmbeddings
from langchain.chains import RetrievalQA

# 创建向量存储
vectorstore = Milvus.from_documents(
    documents,
    embeddings,
    connection_args={"host": "localhost", "port": 19530}
)

# 创建 RAG 链
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever()
)

# 查询
result = qa_chain.run("你的问题")
```

## 最佳实践

1. **Chunk 大小选择**：建议 300-500 token
2. **重叠度**：10-20% overlap 保持上下文
3. **Top-K 选择**：一般 3-5 条
4. **相似度阈值**：0.5-0.7

## 高级优化

- **Hybrid Search**：关键词 + 语义混合检索
- **Reranker**：重排序提升精度
- **Multi-modal RAG**：支持图片、表格
"""
    },
    {
        "title": "Agent 智能体原理",
        "slug": "agent_introduction",
        "body": """
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
"""
    },
    {
        "title": "知识图谱与向量检索",
        "slug": "knowledge_graph",
        "body": """
## 知识图谱基础

### 什么是知识图谱

知识图谱是一种以图结构组织知识的技术，由**实体**、**关系**和**属性**组成。

### 核心概念

- **Entity（实体）**：人、事、物
- **Relation（关系）**：实体间的连接
- **Property（属性）**：实体的特征

## 向量检索

### Embedding 技术

将文本转换为高维向量，用于语义相似度计算。

### 主流模型

| 模型 | 维度 | 特点 |
|------|------|------|
| BAAI/bge-base-zh | 768 | 中文优化 |
| all-MiniLM-L6 | 384 | 轻量级 |
| text-embedding-3-small | 1536 | OpenAI |

### 相似度计算

```python
from sklearn.metrics.pairwise import cosine_similarity

similarity = cosine_similarity(query_embedding, doc_embedding)
```

## Milvus 使用

### 连接

```python
from pymilvus import MilvusClient

client = MilvusClient(uri="http://localhost:19530")
```

### 创建 Collection

```python
from pymilvus import CollectionSchema, FieldSchema, DataType

schema = CollectionSchema(fields=[
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
])

client.create_collection(collection_name="knowledge", schema=schema)
```

### 索引类型

- **IVF_FLAT**：适合中等规模
- **HNSW**：高精度，适合大规模
- **ANNoy**：轻量级方案

## 混合检索

结合关键词检索与语义检索：

```python
# 关键词检索（BM25）
# 语义检索（Embedding）
# 融合排序（RRF）
```
"""
    }
]

# 写入文件
catalog = []
for i, doc in enumerate(sample_docs):
    fname = doc["slug"] + ".md"
    fpath = OUTPUT_DIR / fname

    content = f"""---
title: "{doc['title']}"
date: "2026-08-18"
---

{doc['body']}"""

    fpath.write_text(content, encoding="utf-8")
    print(f"已创建: {fname} ({len(doc['body'])} 字符)")

    catalog.append({
        "id": i + 1,
        "uuid": str(i + 1),
        "parent_uuid": "",
        "title": doc["title"],
        "type": "DOC",
        "slug": doc["slug"],
        "path": f"/docs/{doc['slug']}",
    })

# 生成 elog.cache.json
cache = {"catalog": catalog}
cache_file = Path("./elog.cache.json")
cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\n已生成 elog.cache.json ({len(catalog)} 条记录)")

print("\n知识库创建完成！")
print(f"文档目录: {OUTPUT_DIR}")
print(f"文档数量: {len(sample_docs)}")
