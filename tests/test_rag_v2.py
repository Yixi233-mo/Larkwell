"""
测试 RAG 引擎 v2 数据分布
"""
import sys
import time
sys.path.insert(0, 'src')

from rag_v2 import RAGEngineV2, DocCategory, DocumentMeta

print("=" * 60)
print("  Larkwell RAG v2 - 数据分布测试")
print("=" * 60)
print()

# 初始化
print("初始化 RAG 引擎 v2...")
engine = RAGEngineV2()
print("✅ 引擎已就绪")
print()

# 测试数据
test_documents = [
    {
        "title": "图神经网络基础",
        "text": "图神经网络（GNN）是处理图结构数据的深度学习模型。GCN 基于谱域卷积，GAT 引入注意力机制，GraphSAGE 支持大规模图训练。",
        "category": DocCategory.GNN,
        "tags": ["GNN", "深度学习", "图"],
    },
    {
        "title": "LangChain Agent 开发",
        "text": "LangChain Agent 使用 ReAct 模式：Thought → Action → Observation 循环。支持工具调用、记忆管理、多步推理。",
        "category": DocCategory.LANGCHAIN,
        "tags": ["LangChain", "Agent", "LLM"],
    },
    {
        "title": "RAG 检索增强生成",
        "text": "RAG 结合信息检索与文本生成。核心流程：文档切分 → Embedding 向量化 → 向量存储 → 相似度检索 → LLM 生成。",
        "category": DocCategory.RAG,
        "tags": ["RAG", "向量检索", "Embedding"],
    },
    {
        "title": "Agent 智能体架构",
        "text": "Agent 由 LLM 核心、Tools 工具集、Memory 记忆、Planner 规划器组成。支持自主规划、决策和多步骤执行。",
        "category": DocCategory.AGENT,
        "tags": ["Agent", "架构", "工具调用"],
    },
    {
        "title": "Milvus 向量数据库",
        "text": "Milvus 是开源向量数据库。支持 IVF_FLAT、HNSW、Annoy 等索引类型。Collection 可按主题分库，内部按时间分区。",
        "category": DocCategory.RAG,
        "tags": ["Milvus", "向量数据库", "索引"],
    },
]

# 导入测试文档
print("导入测试文档...")
for i, doc in enumerate(test_documents):
    meta = DocumentMeta(
        doc_id=f"test_doc_{i}",
        title=doc["title"],
        category=doc["category"],
        source=f"test_{i}.md",
        tags=doc["tags"],
        updated_at="2026-08-18T10:00:00Z",
    )
    result = engine.import_document(doc["text"], meta)
    print(f"  [{i+1}] {doc['title']}: {result['inserted']} chunks → {result['collection']}")
print()

# 统计信息
print("📊 Collection 统计:")
stats = engine.get_statistics()
print(f"  总实体数: {stats['total_entities']}")
print(f"  活跃 Collection: {stats['active_collections']}")
print(f"  详细信息:")
for col_name, info in stats["collection_details"].items():
    if info["entities"] > 0:
        print(f"    - {col_name}: {info['entities']} 实体, {info['partitions']} 分区")
print()

# 跨 Collection 检索测试
print("🔍 跨 Collection 检索测试:")
queries = [
    "什么是图神经网络",
    "Agent 如何工作",
    "RAG 和 Milvus 的关系",
    "LangChain 有哪些功能",
]

for query in queries:
    results = engine.search(query, top_k=3)
    print(f"\n  查询: {query}")
    print(f"  结果数: {len(results)}")
    for r in results:
        print(f"    [{r.category}] {r.title} | score={r.score:.4f}")
        print(f"      {r.text[:60]}...")

print()

# 分类限定检索
print("🎯 分类限定检索:")
rag_results = engine.search("向量数据库", categories=[DocCategory.RAG], top_k=2)
print(f"  在 RAG 分类中搜索 '向量数据库': {len(rag_results)} 条结果")
for r in rag_results:
    print(f"    - {r.title}: {r.text[:50]}...")

print()

# 文档列表
print("📚 已索引文档:")
all_docs = engine.list_documents()
for doc in all_docs:
    print(f"  [{doc['category']}] {doc['title']}")

print()
print("=" * 60)
print("  ✅ RAG v2 数据分布测试完成!")
print("=" * 60)
print()
print("数据分布策略:")
print("  1. 按主题分 Collection (GNN, LangChain, RAG, Agent...)")
print("  2. Collection 内按时间 Partition (p_202608)")
print("  3. 跨 Collection 全局检索 + 去重")
print("  4. 分类限定精确检索")
print("  5. 索引参数自适应 (nlist 随数据量调整)")
