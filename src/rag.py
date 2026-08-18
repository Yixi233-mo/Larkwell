"""
RAG 引擎模块
============
连接 Milvus 向量数据库，实现文档导入和语义检索。
配置从 .env 文件读取，支持动态更新。
"""

import os
import re
import hashlib
import requests
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


class CloudEmbedding:
    """云端 Embedding 模型（SiliconFlow 等 OpenAI 兼容 API）"""

    def __init__(self, api_base: str, api_key: str, model: str):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model

    def encode(self, texts, normalize_embeddings=True):
        """编码文本为向量，兼容 SentenceTransformer 接口"""
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        resp = requests.post(
            f"{self.api_base}/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={"model": self.model, "input": list(texts)},
            timeout=30,
        )
        if resp.status_code != 200:
            raise Exception(f"Embedding API 失败: {resp.status_code} {resp.text[:200]}")

        embeddings = [d["embedding"] for d in resp.json()["data"]]
        
        if single:
            import numpy as np
            return np.array(embeddings[0])
        import numpy as np
        return np.array(embeddings)

    def get_sentence_embedding_dimension(self) -> int:
        """获取向量维度"""
        emb = self.encode("test")
        return len(emb)


@dataclass
class SearchResult:
    """检索结果"""
    text: str
    score: float
    source: str = ""
    doc_id: str = ""
    chunk_id: int = 0


class RAGEngine:
    """RAG 引擎：管理 Milvus 连接、文档导入和语义检索"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        collection_name: str = None,
        embedding_model: str = None,
    ):
        """
        初始化 RAG 引擎

        Args:
            host: Milvus 主机地址
            port: Milvus 端口
            collection_name: Collection 名称
            embedding_model: Embedding 模型名称
        """
        config = get_config()

        self.host = host or config.MILVUS_HOST
        self.port = port or config.MILVUS_PORT
        self.collection_name = collection_name or config.MILVUS_COLLECTION
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        self.embedding_dim = config.EMBEDDING_DIM
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        self.top_k = config.TOP_K
        self.similarity_threshold = config.SIMILARITY_THRESHOLD
        self.backend = config.LLM_BACKEND

        # 初始化 Embedding 模型（支持本地 / 云端）
        if self.backend == "cloud":
            logger.info(f"使用云端 Embedding: {config.CLOUD_EMBED_MODEL}")
            self.embedding_model = CloudEmbedding(
                api_base=config.CLOUD_API_BASE,
                api_key=config.CLOUD_API_KEY,
                model=config.CLOUD_EMBED_MODEL,
            )
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        else:
            logger.info(f"加载本地 Embedding 模型: {self.embedding_model_name}")
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding 维度: {self.embedding_dim}")

        # 初始化文本切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
        )

        # 连接 Milvus
        self._connect_milvus()
        self._ensure_collection()

    def _connect_milvus(self) -> None:
        """连接 Milvus 服务"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port,
                timeout=10,
            )
            logger.info(f"✅ 已连接 Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ 连接 Milvus 失败: {e}")
            raise

    def _ensure_collection(self) -> None:
        """确保 Collection 存在，不存在则创建"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info(f"✅ 已加载 Collection: {self.collection_name}")
        else:
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="chunk_id", dtype=DataType.INT64),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
            ]
            schema = CollectionSchema(fields, description="Larkwell 语雀知识库")
            self.collection = Collection(self.collection_name, schema)

            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            }
            self.collection.create_index("embedding", index_params)
            logger.info(f"✅ 已创建 Collection: {self.collection_name}")

        self.collection.load()

    def _generate_doc_id(self, source: str) -> str:
        """
        根据 source 生成唯一的 doc_id

        Args:
            source: 文档来源路径

        Returns:
            唯一的文档 ID
        """
        return hashlib.md5(source.encode()).hexdigest()

    def import_text(
        self,
        text: str,
        source: str = "manual_input",
        doc_id: str = None,
    ) -> int:
        """
        导入文本到知识库

        Args:
            text: 原始文本
            source: 来源标识
            doc_id: 文档ID（可选，不传则自动生成）

        Returns:
            导入的 chunk 数量
        """
        if not doc_id:
            doc_id = self._generate_doc_id(source)

        chunks = self.text_splitter.split_text(text)
        if not chunks:
            logger.warning("文本切分后为空")
            return 0

        embeddings = self.embedding_model.encode(chunks, normalize_embeddings=True)

        data = [
            [doc_id] * len(chunks),
            embeddings.tolist(),
            chunks,
            [source] * len(chunks),
            list(range(len(chunks))),
            list(range(len(chunks))),
        ]

        self.collection.insert(data)
        self.collection.flush()

        logger.info(f"✅ 已导入 {len(chunks)} 个 chunks，来源: {source}")
        return len(chunks)

    def import_file(self, file_path: str) -> int:
        """
        导入文件到知识库

        Args:
            file_path: 文件路径

        Returns:
            导入的 chunk 数量
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"❌ 读取文件失败: {e}")
            return 0

        return self.import_text(text, source=file_path)

    def delete_document(self, doc_id: str) -> int:
        """
        删除指定文档的所有向量

        Args:
            doc_id: 文档ID

        Returns:
            删除的向量数量
        """
        try:
            result = self.collection.query(
                expr=f'doc_id == "{doc_id}"',
                output_fields=["id"],
            )
            count = len(result)

            if count > 0:
                self.collection.delete(expr=f'doc_id == "{doc_id}"')
                self.collection.flush()
                logger.info(f"✅ 已删除文档 {doc_id} 的 {count} 个向量")
            else:
                logger.info(f"文档 {doc_id} 无向量需要删除")

            return count
        except Exception as e:
            logger.error(f"❌ 删除文档失败: {e}")
            return 0

    def upsert_document(
        self,
        text: str,
        source: str,
        doc_id: str = None,
    ) -> Dict[str, int]:
        """
        增量更新文档（先删除旧的，再插入新的）

        Args:
            text: 文档内容
            source: 来源路径
            doc_id: 文档ID

        Returns:
            更新结果
        """
        if not doc_id:
            doc_id = self._generate_doc_id(source)

        logger.info(f"开始更新文档: {source} (doc_id: {doc_id})")

        # 先删除旧数据
        deleted = self.delete_document(doc_id)

        # 插入新数据
        inserted = self.import_text(text, source=source, doc_id=doc_id)

        result = {
            "deleted": deleted,
            "inserted": inserted,
            "doc_id": doc_id,
        }

        logger.info(f"文档更新完成: 删除 {deleted} 条，插入 {inserted} 条")
        return result

    def search(self, query: str, top_k: int = None) -> List[SearchResult]:
        """
        语义检索

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            检索结果列表（按相似度降序）
        """
        if top_k is None:
            top_k = self.top_k

        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }

        results = self.collection.search(
            data=query_embedding.tolist(),
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text", "source", "chunk_id", "doc_id"],
        )

        search_results = []
        for hits in results:
            for hit in hits:
                score = hit.score
                if score < self.similarity_threshold:
                    continue
                search_results.append(SearchResult(
                    text=hit.entity.get("text", ""),
                    score=score,
                    source=hit.entity.get("source", ""),
                    doc_id=hit.entity.get("doc_id", ""),
                    chunk_id=hit.entity.get("chunk_id", 0),
                ))

        logger.info(f"🔍 检索 '{query[:30]}...' → {len(search_results)} 条结果")
        return search_results

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        return {
            "collection": self.collection_name,
            "entity_count": self.collection.num_entities,
            "host": f"{self.host}:{self.port}",
            "embedding_model": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
        }

    def clear(self) -> None:
        """清空知识库"""
        if utility.has_collection(self.collection_name):
            utility.drop_collection(self.collection_name)
            self._ensure_collection()
            logger.info(f"🗑️ 已清空知识库: {self.collection_name}")

    def list_documents(self) -> List[Dict]:
        """
        列出所有已索引的文档

        Returns:
            文档列表
        """
        try:
            results = self.collection.query(
                expr="",
                output_fields=["doc_id", "source"],
            )

            # 去重
            seen = set()
            docs = []
            for r in results:
                doc_id = r["doc_id"]
                if doc_id not in seen:
                    seen.add(doc_id)
                    docs.append({
                        "doc_id": doc_id,
                        "source": r["source"],
                    })

            logger.info(f"📚 知识库中共有 {len(docs)} 个文档")
            return docs
        except Exception as e:
            logger.error(f"❌ 获取文档列表失败: {e}")
            return []
