---
title: "知识图谱与向量检索"
date: "2026-08-18"
category: "大模型应用"
tags: ["知识图谱", "向量检索", "Milvus", "Embedding"]
description: "介绍知识图谱与向量检索技术在大模型应用中的实现"
---


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
