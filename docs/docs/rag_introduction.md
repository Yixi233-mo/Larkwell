---
title: "RAG 检索增强生成"
date: "2026-08-18"
category: "大模型应用"
tags: ["RAG", "信息检索", "文本生成", "LangChain", "向量数据库"]
description: "介绍RAG框架结合信息检索与文本生成，增强大模型回答能力"
---


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
