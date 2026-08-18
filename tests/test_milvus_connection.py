"""测试 Milvus 连接 - 非交互式"""
import os
from dotenv import load_dotenv

load_dotenv()

from pymilvus import MilvusClient

host = os.getenv("MILVUS_HOST", "192.168.2.169")
port = os.getenv("MILVUS_PORT", "19530")
collection_name = os.getenv("MILVUS_COLLECTION", "larkwell_knowledge")

uri = f"http://{host}:{port}"
print(f"测试 Milvus 连接: {uri}")
print("-" * 40)

try:
    client = MilvusClient(uri=uri)
    print(f"✅ Milvus 连接成功!")

    # 检查 collections
    collections = client.list_collections()
    print(f"📚 现有 Collections: {collections}")

    # 获取统计信息
    if collection_name in collections:
        stats = client.aggregate(
            collection_name=collection_name,
            group_by="doc_id",
        )
        print(f"📊 Collection '{collection_name}' 统计: {len(stats)} 个文档")

        # 删除旧 Collection 并重建（测试用）
        print(f"🗑️ 清理旧 Collection...")
        client.drop_collection(collection_name=collection_name)
        print(f"   已删除")

    # 创建测试 Collection
    from pymilvus import CollectionSchema, FieldSchema, DataType
    schema = CollectionSchema(
        fields=[
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
        ],
        description="Larkwell 测试 Collection"
    )
    client.create_collection(
        collection_name=collection_name,
        schema=schema,
    )
    print(f"✅ 已创建 Collection: {collection_name}")

    # 插入测试数据
    import time
    test_data = [
        {
            "doc_id": "test_001",
            "embedding": [0.1] * 768,
            "text": "Larkwell 是一个将语雀笔记转化为 AI 知识库的智能助手。",
            "source": "test",
            "chunk_index": 0,
        }
    ]
    client.insert(
        collection_name=collection_name,
        data=test_data,
    )
    print(f"✅ 已插入测试数据")

    # 创建索引
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        index_type="IVF_FLAT",
        metric_type="COSINE",
        params={"nlist": 128},
    )
    client.create_index(
        collection_name=collection_name,
        index_params=index_params,
    )
    print(f"✅ 已创建索引")

    # 加载 Collection
    client.load_collection(collection_name=collection_name)
    print(f"✅ 已加载 Collection")

    # 搜索
    results = client.search(
        collection_name=collection_name,
        data=[[0.1] * 768],
        anns_field="embedding",
        limit=1,
        output_fields=["text", "source", "doc_id"],
    )
    print(f"🔍 搜索测试: 共 {len(results)} 组结果")
    for hits in results:
        print(f"   命中 {len(hits)} 条")
        for hit in hits:
            entity = hit.get("entity", {})
            print(f"   - doc_id: {entity.get('doc_id', 'N/A')}, text: {entity.get('text', 'N/A')[:50]}...")

    # 统计
    entity_count = client.num_entities(collection_name=collection_name)
    print(f"📊 实体数量: {entity_count}")

    # 清理
    client.drop_collection(collection_name=collection_name)
    print(f"🗑️ 已删除测试 Collection")

    print(f"\n✨ Milvus 功能测试完成!")
    print(f"\n接下来需要:")
    print(f"  1. 设置 HF_ENDPOINT=https://hf-mirror.com 解决模型下载")
    print(f"  2. 下载语雀文档")
    print(f"  3. 导入文档到 Milvus")
    print(f"  4. 测试 RAG 检索")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
