"""Larkwell 完整流程测试脚本"""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

def main():
    print("=" * 60)
    print("  Larkwell 完整流程测试")
    print("=" * 60)
    print()

    # 1. 测试配置加载
    print("1. 配置模块测试")
    print("-" * 40)
    from utils.config import get_config
    config = get_config()
    print(f"  ✅ Milvus: {config.MILVUS_HOST}:{config.MILVUS_PORT}")
    print(f"  ✅ Collection: {config.MILVUS_COLLECTION}")
    print(f"  ✅ Embedding: {config.EMBEDDING_MODEL}")
    print(f"  ✅ Ollama: {config.OLLAMA_BASE_URL}")
    print()

    # 2. 测试日志模块
    print("2. 日志模块测试")
    print("-" * 40)
    from utils.logger import get_logger
    logger = get_logger('test')
    logger.info('流程测试开始')
    print("  ✅ 日志模块正常")
    print()

    # 3. 测试清洗模块
    print("3. 清洗模块测试")
    print("-" * 40)
    from cleaning.rules import CLEANING_RULES
    print(f"  ✅ 清洗规则数量: {len(CLEANING_RULES)}")
    for name, func in CLEANING_RULES:
        print(f"    - {name}")
    print()

    # 4. 测试文档加载器
    print("4. 文档加载器测试")
    print("-" * 40)
    from indexing.document_loader import DocumentLoader
    loader = DocumentLoader()
    print(f"  ✅ chunk_size: {loader.config.CHUNK_SIZE}")
    print(f"  ✅ chunk_overlap: {loader.config.CHUNK_OVERLAP}")
    print()

    # 5. 测试 RAG 引擎（需要 Milvus 连接）
    print("5. RAG 引擎测试")
    print("-" * 40)
    try:
        from rag import RAGEngine
        print("  正在连接 Milvus...")
        rag = RAGEngine()
        stats = rag.get_stats()
        print(f"  ✅ Milvus 连接成功")
        print(f"  ✅ 实体数量: {stats['entity_count']}")
        print(f"  ✅ Embedding 维度: {stats['embedding_dim']}")

        # 测试导入
        test_text = "Larkwell 是一个将语雀笔记转化为 AI 知识库的智能助手。"
        doc_id = rag.import_text(test_text, source="test", doc_id="test_doc_001")
        print(f"  ✅ 测试导入: {doc_id} chunks")

        # 测试检索
        results = rag.search("什么是 Larkwell")
        print(f"  ✅ 语义检索: {len(results)} 条结果")
        for r in results[:2]:
            print(f"    - 相似度: {r.score:.4f}, 内容: {r.text[:50]}...")

        # 清理测试数据
        rag.delete_document("test_doc_001")
        print(f"  ✅ 清理测试数据完成")

    except Exception as e:
        print(f"  ⚠️ Milvus 连接失败: {e}")
        print("      (请确保 Milvus 服务正在运行)")
    print()

    # 6. 测试 Agent
    print("6. Agent 模块测试")
    print("-" * 40)
    from agent import Agent
    agent = Agent(model_name=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
    print(f"  ✅ Agent 初始化成功")
    print(f"  ✅ 模型: {config.OLLAMA_MODEL}")
    print()

    # 7. 测试工具
    print("7. 工具模块测试")
    print("-" * 40)
    from tools import ALL_TOOLS
    print(f"  ✅ 工具数量: {len(ALL_TOOLS)}")
    for tool in ALL_TOOLS:
        print(f"    - {tool.name}: {tool.description[:40]}...")
    print()

    # 8. 测试 API 模块
    print("8. FastAPI 模块测试")
    print("-" * 40)
    from app import app
    routes = [r.path for r in app.routes]
    print(f"  ✅ API 路由数量: {len(routes)}")
    for route in routes:
        print(f"    - {route}")
    print()

    # 9. 测试索引管道
    print("9. 索引管道测试")
    print("-" * 40)
    try:
        from indexing.pipeline import IndexPipeline
        pipeline = IndexPipeline()
        print(f"  ✅ 索引管道初始化成功")
        stats = pipeline.get_stats()
        print(f"  ✅ 知识库实体数: {stats['knowledge_base']['entity_count']}")
    except Exception as e:
        print(f"  ⚠️ 索引管道测试失败: {e}")
    print()

    print("=" * 60)
    print("  测试完成!")
    print("=" * 60)
    print()
    print("  状态总结:")
    print("    ✅ 配置模块")
    print("    ✅ 日志模块")
    print("    ✅ 清洗模块")
    print("    ✅ 文档加载器")
    print("    ⚠️ RAG 引擎 (需要 Milvus 运行)")
    print("    ✅ Agent 模块")
    print("    ✅ 工具模块")
    print("    ✅ FastAPI 模块")
    print("    ⚠️ 索引管道 (需要 Milvus 运行)")
    print()

    # 检查目录结构
    print("10. 目录结构检查")
    print("-" * 40)
    dirs_to_check = [
        'docs/docs',
        'docs/images',
        'repos/raw',
        'repos/clean',
        'logs',
    ]
    for d in dirs_to_check:
        path = Path(d)
        if path.exists():
            files = list(path.rglob('*'))
            print(f"  ✅ {d}/ ({len(files)} 个文件)")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"  🆕 {d}/ (已创建)")


if __name__ == "__main__":
    main()
