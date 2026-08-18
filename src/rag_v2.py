"""
Larkwell RAG 引擎 v2 - 数据分布优化版
=====================================
设计原则：
1. 按文档主题分 Collection（GNN、LangChain、RAG、Agent 等）
2. Collection 内按时间 Partition 分区
3. 统一路由层支持跨 Collection 检索
4. 元数据驱动的智能筛选
5. 索引参数随数据量自适应调整
"""

import os
import re
import hashlib
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

from pymilvus import (
    MilvusClient,
    CollectionSchema,
    FieldSchema,
    DataType,
    Partition,
)
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


# ============ 文档分类体系 ============

class DocCategory(str, Enum):
    """文档分类（对应独立的 Collection）"""
    GNN = "gnn"                    # 图神经网络
    LANGCHAIN = "langchain"        # LangChain
    RAG = "rag"                    # 检索增强生成
    AGENT = "agent"                # Agent 智能体
    KNOWLEDGE_GRAPH = "kg"         # 知识图谱
    DEV_NOTES = "dev_notes"        # 开发笔记
    PROJECT = "project"            # 项目文档
    TUTORIAL = "tutorial"          # 教程
    OTHER = "other"                # 其他

    @classmethod
    def from_title(cls, title: str) -> "DocCategory":
        """根据标题自动推断分类"""
        title_lower = title.lower()
        rules = [
            (cls.GNN, ["图神经", "gnn", "graph neural", "图卷积", "gat", "gcn"]),
            (cls.LANGCHAIN, ["langchain", "langgraph", "llm chain"]),
            (cls.RAG, ["rag", "检索增强", "retrieval augmented", "向量检索", "embedding", "milvus"]),
            (cls.AGENT, ["agent", "智能体", "chatbot", "对话机器人", "工具调用"]),
            (cls.KNOWLEDGE_GRAPH, ["知识图谱", "knowledge graph", "neo4j", "实体关系"]),
            (cls.DEV_NOTES, ["笔记", "学习", "记录", "notes", "memo"]),
            (cls.PROJECT, ["项目", "project", "规划", "计划"]),
            (cls.TUTORIAL, ["教程", "tutorial", "入门", "基础", "实战"]),
        ]
        for cat, keywords in rules:
            if any(kw in title_lower for kw in keywords):
                return cat
        return cls.OTHER

    @classmethod
    def all_categories(cls) -> List["DocCategory"]:
        return list(cls)


# ============ 数据模型 ============

@dataclass
class DocumentMeta:
    """文档元数据"""
    doc_id: str
    title: str
    category: DocCategory
    source: str
    author: str = ""
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "category": self.category.value,
            "source": self.source,
            "author": self.author,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
        }


@dataclass
class SearchResult:
    """检索结果"""
    text: str
    score: float
    source: str = ""
    doc_id: str = ""
    chunk_index: int = 0
    category: str = ""
    title: str = ""


# ============ Collection 管理器 ============

class CollectionManager:
    """Collection 管理器 - 按分类管理多个 Collection"""

    COLLECTION_PREFIX = "larkwell"

    # Collection 配置模板
    COLLECTION_CONFIGS = {
        # 分类: (数据规模预期, nlist, 描述)
        DocCategory.GNN:             ("small", 64, "图神经网络文档"),
        DocCategory.LANGCHAIN:       ("medium", 128, "LangChain 文档"),
        DocCategory.RAG:             ("large", 256, "RAG 技术文档"),
        DocCategory.AGENT:           ("medium", 128, "Agent 智能体文档"),
        DocCategory.KNOWLEDGE_GRAPH: ("small", 64, "知识图谱文档"),
        DocCategory.DEV_NOTES:       ("large", 256, "开发笔记"),
        DocCategory.PROJECT:         ("small", 64, "项目文档"),
        DocCategory.TUTORIAL:        ("medium", 128, "教程文档"),
        DocCategory.OTHER:           ("medium", 128, "其他文档"),
    }

    def __init__(self, client: MilvusClient, embedding_dim: int):
        self.client = client
        self.embedding_dim = embedding_dim
        self._ensure_all_collections()

    def _get_collection_name(self, category: DocCategory) -> str:
        return f"{self.COLLECTION_PREFIX}_{category.value}"

    def _get_collection_names(self) -> List[str]:
        """获取所有 Larkwell 相关的 Collection"""
        collections = self.client.list_collections()
        return [c for c in collections if c.startswith(self.COLLECTION_PREFIX)]

    def _ensure_all_collections(self):
        """确保所有分类的 Collection 存在"""
        for category in DocCategory.all_categories():
            col_name = self._get_collection_name(category)
            if not self.client.has_collection(col_name):
                self._create_collection(col_name, category)
            else:
                logger.info(f"加载 Collection: {col_name}")

        # 加载所有 Collection
        self._load_all_collections()

    def _create_collection(self, col_name: str, category: DocCategory):
        """创建 Collection"""
        scale, nlist, desc = self.COLLECTION_CONFIGS.get(
            category, ("medium", 128, "Larkwell 文档")
        )

        schema = CollectionSchema(
            fields=[
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=128),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="updated_at", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024),
                FieldSchema(name="chunk_index", dtype=DataType.INT64),
                FieldSchema(name="chunk_count", dtype=DataType.INT64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            ],
            description=f"Larkwell {desc} (scale: {scale})",
        )

        self.client.create_collection(
            collection_name=col_name,
            schema=schema,
        )

        # 创建索引
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="embedding",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": nlist},
        )
        self.client.create_index(
            collection_name=col_name,
            index_params=index_params,
        )

        logger.info(f"创建 Collection: {col_name} (nlist={nlist}, scale={scale})")

    def _load_all_collections(self):
        """加载所有 Collection 到内存"""
        for col_name in self._get_collection_names():
            try:
                self.client.load_collection(col_name)
            except Exception as e:
                logger.warning(f"加载 {col_name} 失败: {e}")

    def get_or_create_partition(self, col_name: str, partition_name: str):
        """获取或创建 Partition"""
        if not self.client.has_partition(col_name, partition_name):
            self.client.create_partition(col_name, partition_name)
        return partition_name

    def get_stats(self) -> Dict:
        """获取所有 Collection 统计"""
        stats = {}
        for col_name in self._get_collection_names():
            try:
                entity_count = self.client.num_entities(col_name)
                partitions = self.client.list_partitions(col_name)
                stats[col_name] = {
                    "entities": entity_count,
                    "partitions": len(partitions),
                }
            except Exception:
                stats[col_name] = {"entities": 0, "partitions": 0}
        return stats

    def drop_collection(self, category: DocCategory):
        """删除某个分类的 Collection"""
        col_name = self._get_collection_name(category)
        if self.client.has_collection(col_name):
            self.client.drop_collection(col_name)
            logger.info(f"已删除 Collection: {col_name}")


# ============ RAG 引擎 v2 ============

class RAGEngineV2:
    """RAG 引擎 v2 - 数据分布优化版"""

    def __init__(self):
        config = get_config()

        self.host = config.MILVUS_HOST
        self.port = config.MILVUS_PORT
        self.embedding_model_name = config.EMBEDDING_MODEL
        self.chunk_size = config.CHUNK_SIZE
        self.chunk_overlap = config.CHUNK_OVERLAP
        self.top_k = config.TOP_K
        self.similarity_threshold = config.SIMILARITY_THRESHOLD

        # 初始化 Embedding 模型
        logger.info(f"加载 Embedding 模型: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
        logger.info(f"Embedding 维度: {self.embedding_dim}")

        # 文本切分器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
        )

        # 连接 Milvus
        uri = f"http://{self.host}:{self.port}"
        self.client = MilvusClient(uri=uri)
        logger.info(f"已连接 Milvus: {uri}")

        # 初始化 Collection 管理器
        self.collection_mgr = CollectionManager(self.client, self.embedding_dim)

    def _generate_doc_id(self, source: str) -> str:
        return hashlib.md5(source.encode()).hexdigest()

    def _determine_partition(self, meta: DocumentMeta) -> str:
        """根据更新时间确定 Partition 名称（按月分区）"""
        if meta.updated_at:
            # 提取年月: 2024-01-15T10:00:00Z -> 202401
            year_month = meta.updated_at[:7].replace("-", "")
            return f"p_{year_month}"
        return "p_unknown"

    def import_document(
        self,
        text: str,
        meta: DocumentMeta,
    ) -> Dict:
        """
        导入文档到对应分类的 Collection

        Args:
            text: 文档内容
            meta: 文档元数据

        Returns:
            导入结果
        """
        col_name = self.collection_mgr._get_collection_name(meta.category)
        partition_name = self._determine_partition(meta)

        # 确保 Partition 存在
        self.collection_mgr.get_or_create_partition(col_name, partition_name)

        # 先删除旧数据（doc_id 级别）
        try:
            self.client.delete(
                collection_name=col_name,
                filter=f'doc_id == "{meta.doc_id}"',
                partition_name=partition_name,
            )
        except Exception:
            pass

        # 文本切分
        chunks = self.text_splitter.split_text(text)
        if not chunks:
            logger.warning(f"文档 {meta.doc_id} 切分后为空")
            return {"inserted": 0, "category": meta.category.value}

        # 向量化
        embeddings = self.embedding_model.encode(chunks, normalize_embeddings=True)

        # 构建数据
        data = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            row = {
                "doc_id": meta.doc_id,
                "title": meta.title,
                "category": meta.category.value,
                "source": meta.source,
                "author": meta.author,
                "created_at": meta.created_at,
                "updated_at": meta.updated_at,
                "tags": ",".join(meta.tags) if meta.tags else "",
                "chunk_index": i,
                "chunk_count": len(chunks),
                "embedding": emb.tolist(),
                "text": chunk,
            }
            data.append(row)

        # 插入到指定 Partition
        self.client.insert(
            collection_name=col_name,
            partition_name=partition_name,
            data=data,
        )

        logger.info(
            f"✅ 导入 {meta.title}: {len(chunks)} chunks → {col_name}/{partition_name}"
        )

        return {
            "inserted": len(chunks),
            "category": meta.category.value,
            "collection": col_name,
            "partition": partition_name,
        }

    def import_file(
        self,
        file_path: str,
        category: DocCategory = None,
        title: str = None,
        tags: List[str] = None,
    ) -> Dict:
        """
        导入文件

        Args:
            file_path: 文件路径
            category: 文档分类（不传则自动推断）
            title: 文档标题（不传则使用文件名）
            tags: 标签列表
        """
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # 提取 frontmatter 中的标题
        if not title:
            title_match = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
            if title_match:
                title = title_match.group(1).strip()
            else:
                title = Path(file_path).stem

        # 确定分类
        if not category:
            category = DocCategory.from_title(title)

        # 提取日期
        date_match = re.search(r'^date:\s*["\']?(.+?)["\']?\s*$', text, re.MULTILINE)
        updated_at = date_match.group(1) if date_match else ""

        # 生成元数据
        meta = DocumentMeta(
            doc_id=self._generate_doc_id(file_path),
            title=title,
            category=category,
            source=file_path,
            author="",
            updated_at=updated_at,
            tags=tags or [],
        )

        return self.import_document(text, meta)

    def search(
        self,
        query: str,
        categories: List[DocCategory] = None,
        top_k: int = None,
        min_score: float = None,
    ) -> List[SearchResult]:
        """
        跨 Collection 检索

        Args:
            query: 查询文本
            categories: 限定分类（不传则全库搜索）
            top_k: 每个 Collection 返回数量
            min_score: 最低相似度阈值

        Returns:
            按相似度排序的检索结果
        """
        if top_k is None:
            top_k = self.top_k
        if min_score is None:
            min_score = self.similarity_threshold

        query_embedding = self.embedding_model.encode(
            [query], normalize_embeddings=True
        )

        # 确定搜索范围
        if categories:
            search_categories = categories
        else:
            search_categories = DocCategory.all_categories()

        # 各 Collection 独立检索
        all_results = []
        per_collection_k = max(top_k // len(search_categories), 3)

        for category in search_categories:
            col_name = self.collection_mgr._get_collection_name(category)
            if not self.client.has_collection(col_name):
                continue

            try:
                results = self.client.search(
                    collection_name=col_name,
                    data=query_embedding.tolist(),
                    anns_field="embedding",
                    limit=per_collection_k,
                    output_fields=["text", "source", "doc_id", "chunk_index", "title", "category"],
                    search_params={"metric_type": "COSINE", "params": {"nprobe": 10}},
                )

                for hits in results:
                    for hit in hits:
                        score = hit.score
                        if score >= min_score:
                            entity = hit.entity
                            all_results.append(SearchResult(
                                text=entity.get("text", ""),
                                score=score,
                                source=entity.get("source", ""),
                                doc_id=entity.get("doc_id", ""),
                                chunk_index=entity.get("chunk_index", 0),
                                category=entity.get("category", ""),
                                title=entity.get("title", ""),
                            ))
            except Exception as e:
                logger.warning(f"检索 {col_name} 失败: {e}")

        # 全局排序 + 去重（同一 doc_id 只保留最高分）
        all_results.sort(key=lambda x: x.score, reverse=True)
        seen_docs = set()
        deduped = []
        for r in all_results:
            if r.doc_id not in seen_docs:
                seen_docs.add(r.doc_id)
                deduped.append(r)

        return deduped[:top_k]

    def delete_document(self, doc_id: str, category: DocCategory = None) -> int:
        """
        删除文档（在指定分类或全部分类中）
        """
        categories_to_search = [category] if category else DocCategory.all_categories()
        deleted_total = 0

        for cat in categories_to_search:
            col_name = self.collection_mgr._get_collection_name(cat)
            if not self.client.has_collection(col_name):
                continue

            try:
                result = self.client.delete(
                    collection_name=col_name,
                    filter=f'doc_id == "{doc_id}"',
                )
                deleted_total += len(result) if result else 0
            except Exception:
                pass

        logger.info(f"删除文档 {doc_id}: {deleted_total} 条记录")
        return deleted_total

    def get_statistics(self) -> Dict:
        """获取全局统计"""
        collection_stats = self.collection_mgr.get_stats()

        total_entities = sum(s["entities"] for s in collection_stats.values())
        total_collections = len([
            c for c, s in collection_stats.items() if s["entities"] > 0
        ])

        return {
            "total_entities": total_entities,
            "active_collections": total_collections,
            "collection_details": collection_stats,
            "embedding_model": self.embedding_model_name,
            "embedding_dim": self.embedding_dim,
            "host": f"{self.host}:{self.port}",
        }

    def list_documents(self, category: DocCategory = None) -> List[Dict]:
        """列出文档"""
        categories_to_search = [category] if category else DocCategory.all_categories()
        docs = []

        for cat in categories_to_search:
            col_name = self.collection_mgr._get_collection_name(cat)
            if not self.client.has_collection(col_name):
                continue

            try:
                results = self.client.query(
                    collection_name=col_name,
                    filter="",
                    output_fields=["doc_id", "title", "source", "category", "tags"],
                )
                seen = set()
                for r in results:
                    if r["doc_id"] not in seen:
                        seen.add(r["doc_id"])
                        docs.append(r)
            except Exception:
                pass

        return docs

    def clear_category(self, category: DocCategory):
        """清空某个分类"""
        col_name = self.collection_mgr._get_collection_name(category)
        if self.client.has_collection(col_name):
            self.client.drop_collection(col_name)
            self.collection_mgr._ensure_all_collections()
            logger.info(f"🗑️ 已清空 {category.value}")

    def rebuild_index(self, category: DocCategory):
        """重建索引（数据量大时优化）"""
        col_name = self.collection_mgr._get_collection_name(category)
        if not self.client.has_collection(col_name):
            return

        # 根据当前数据量调整 nlist
        entity_count = self.client.num_entities(col_name)
        scale = self.collection_mgr.COLLECTION_CONFIGS.get(
            category, ("medium", 128, "")
        )[0]

        if entity_count > 100000:
            nlist = 1024  # 大规模
        elif entity_count > 10000:
            nlist = 512   # 中规模
        else:
            nlist = 256   # 小规模

        logger.info(f"重建索引 {col_name}: entities={entity_count}, nlist={nlist}")


# ============ 便捷函数 ============

def create_rag_engine() -> RAGEngineV2:
    """创建 RAG 引擎实例"""
    return RAGEngineV2()


if __name__ == "__main__":
    # 测试
    engine = create_rag_engine()
    print(f"RAG 引擎已初始化")
    print(f"Collection 统计: {engine.get_statistics()}")
