"""重建 Milvus Collection（维度从 768 → 1024）"""
import sys
sys.path.insert(0, 'src')

from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)
config = get_config()

host = config.MILVUS_HOST
port = config.MILVUS_PORT
col_name = config.MILVUS_COLLECTION
dim = config.EMBEDDING_DIM

print(f"连接 Milvus: {host}:{port}")
connections.connect(alias="default", host=host, port=port)
print("✅ 已连接")

# 删除旧 Collection
if utility.has_collection(col_name):
    print(f"删除旧 Collection: {col_name}")
    utility.drop_collection(col_name)
    print("✅ 已删除")

# 创建新 Collection (dim=1024)
print(f"创建新 Collection: {col_name} (dim={dim})")
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
    FieldSchema(name="chunk_id", dtype=DataType.INT64),
    FieldSchema(name="chunk_index", dtype=DataType.INT64),
]
schema = CollectionSchema(fields, description="Larkwell 知识库 (bge-m3 1024维)")
collection = Collection(col_name, schema)

# 创建索引
index_params = {
    "index_type": "IVF_FLAT",
    "metric_type": "COSINE",
    "params": {"nlist": 128},
}
collection.create_index("embedding", index_params)
collection.load()

print(f"✅ Collection 创建完成: {col_name} (dim={dim})")
print(f"   索引: IVF_FLAT, COSINE, nlist=128")
