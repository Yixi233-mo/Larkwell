"""完整 RAG 测试 - Cloud 模式 (SiliconFlow + Milvus)"""
import sys
sys.path.insert(0, 'src')

from rag import RAGEngine
from utils.config import get_config

config = get_config()

print("=" * 60)
print("  Larkwell RAG 完整测试 [Cloud 模式]")
print("=" * 60)

print(f"\n配置:")
print(f"  后端: {config.LLM_BACKEND}")
print(f"  LLM: {config.CLOUD_MODEL}")
print(f"  Embedding: {config.CLOUD_EMBED_MODEL}")
print(f"  Milvus: {config.MILVUS_HOST}:{config.MILVUS_PORT}")
print()

# 初始化 RAG
print("初始化 RAG 引擎...")
rag = RAGEngine()
print(f"✅ RAG 引擎就绪 (dim={rag.embedding_dim})")
print()

# 导入测试文档
print("导入测试文档...")
test_docs = [
    ("Larkwell 是一个将语雀笔记转化为 AI 知识库的智能助手，支持语义检索和问答。", "larkwell_intro"),
    ("RAG 检索增强生成结合了信息检索与文本生成，核心流程包括文档切分、Embedding 向量化、向量存储和相似度检索。", "rag_intro"),
    ("图神经网络是处理图结构数据的深度学习模型，主要类型包括 GCN、GAT 和 GraphSAGE。", "gnn_intro"),
    ("Milvus 是开源向量数据库，支持 IVF_FLAT、HNSW 等索引类型，适合大规模语义检索。", "milvus_intro"),
]

for text, source in test_docs:
    result = rag.upsert_document(text=text, source=source)
    print(f"  ✅ {source}: {result['inserted']} chunks")

print()

# 语义检索
print("语义检索测试...")
queries = [
    "什么是 Larkwell",
    "RAG 的核心流程是什么",
    "图神经网络有哪些类型",
    "Milvus 支持什么索引",
]

for query in queries:
    results = rag.search(query, top_k=2)
    print(f"\n  查询: {query}")
    print(f"  结果: {len(results)} 条")
    for r in results:
        print(f"    score={r.score:.4f} | {r.text[:50]}...")

# 统计
print(f"\n📊 知识库统计:")
stats = rag.get_stats()
print(f"  Collection: {stats['collection']}")
print(f"  实体数: {stats['entity_count']}")
print(f"  维度: {stats['embedding_dim']}")

# 清理测试数据
print("\n清理测试数据...")
for _, source in test_docs:
    import hashlib
    doc_id = hashlib.md5(source.encode()).hexdigest()
    rag.delete_document(doc_id)
print("✅ 清理完成")

print("\n" + "=" * 60)
print("  ✅ RAG 完整测试通过!")
print("=" * 60)
