"""
Milvus 索引管道
==============
将清洗后的文档批量导入 Milvus 向量数据库。
支持：
- 批量导入目录下所有 Markdown 文件
- 增量更新（基于文件修改时间）
- 进度显示
"""

import os
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from utils.logger import get_logger
from utils.config import get_config
from rag import RAGEngine

logger = get_logger(__name__)


class IndexPipeline:
    """索引管道：文档 → 清洗 → 向量化 → Milvus"""

    def __init__(self, clean_dir: str = None):
        """
        初始化索引管道

        Args:
            clean_dir: 清洗后文档的目录路径
        """
        self.config = get_config()
        self.clean_dir = Path(clean_dir or self.config.get_clean_repo_absolute_path())
        self.rag = RAGEngine()

        # 确保目录存在
        self.clean_dir.mkdir(parents=True, exist_ok=True)

        # 处理状态
        self.stats = {
            "total_files": 0,
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None,
        }

        logger.info(f"索引管道已初始化")
        logger.info(f"文档目录: {self.clean_dir}")
        logger.info(f"Milvus: {self.config.MILVUS_HOST}:{self.config.MILVUS_PORT}")
        logger.info(f"Collection: {self.config.MILVUS_COLLECTION}")

    def _generate_doc_id(self, file_path: str) -> str:
        """根据文件路径生成 doc_id"""
        return hashlib.md5(file_path.encode()).hexdigest()

    def import_file(self, file_path: Path) -> Dict:
        """
        导入单个文件到索引

        Args:
            file_path: 文件路径

        Returns:
            导入结果
        """
        result = {
            "file": str(file_path),
            "status": "unknown",
            "doc_id": "",
            "chunks": 0,
            "error": None,
        }

        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                result["status"] = "skipped"
                result["error"] = "空文件"
                self.stats["skipped"] += 1
                return result

            # 生成 doc_id
            doc_id = self._generate_doc_id(str(file_path))
            result["doc_id"] = doc_id

            # 增量更新
            upsert_result = self.rag.upsert_document(
                text=content,
                source=str(file_path),
                doc_id=doc_id,
            )

            result["status"] = "success"
            result["chunks"] = upsert_result["inserted"]
            self.stats["indexed"] += 1

            logger.debug(f"已索引: {file_path.name} ({upsert_result['inserted']} chunks)")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.stats["failed"] += 1
            logger.error(f"索引失败: {file_path}, 错误: {e}")

        return result

    def import_directory(self, directory: Path = None) -> Dict:
        """
        批量导入目录下所有 Markdown 文件

        Args:
            directory: 目录路径（默认使用清洗目录）

        Returns:
            批量导入结果
        """
        if directory is None:
            directory = self.clean_dir

        logger.info("=" * 60)
        logger.info(f"开始批量索引: {directory}")
        logger.info("=" * 60)

        self.stats["start_time"] = time.time()
        self.stats["indexed"] = 0
        self.stats["skipped"] = 0
        self.stats["failed"] = 0

        # 查找所有 Markdown 文件
        md_files = list(directory.rglob('*.md'))
        self.stats["total_files"] = len(md_files)

        logger.info(f"发现 {len(md_files)} 个 Markdown 文件")

        results = []
        for i, file_path in enumerate(md_files, 1):
            # 显示进度
            progress = f"[{i}/{len(md_files)}]"
            logger.info(f"{progress} 处理: {file_path.name}")

            result = self.import_file(file_path)
            results.append(result)

        self.stats["end_time"] = time.time()
        elapsed = self.stats["end_time"] - self.stats["start_time"]

        summary = {
            "total_files": self.stats["total_files"],
            "indexed": self.stats["indexed"],
            "skipped": self.stats["skipped"],
            "failed": self.stats["failed"],
            "elapsed_seconds": round(elapsed, 2),
            "results": results,
        }

        logger.info("=" * 60)
        logger.info(f"批量索引完成")
        logger.info(f"  总文件数: {summary['total_files']}")
        logger.info(f"  成功索引: {summary['indexed']}")
        logger.info(f"  跳过: {summary['skipped']}")
        logger.info(f"  失败: {summary['failed']}")
        logger.info(f"  耗时: {summary['elapsed_seconds']}秒")
        logger.info(f"  知识库状态: {self.rag.get_stats()}")
        logger.info("=" * 60)

        return summary

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "processing": self.stats.copy(),
            "knowledge_base": self.rag.get_stats(),
        }


def run_index_pipeline(clean_dir: str = None) -> Dict:
    """
    执行索引管道的便捷函数

    Args:
        clean_dir: 清洗后文档目录

    Returns:
        索引结果摘要
    """
    pipeline = IndexPipeline(clean_dir)
    return pipeline.import_directory()


if __name__ == "__main__":
    # 测试索引管道
    result = run_index_pipeline()
    print(f"索引完成: {result['indexed']} 个文件成功索引")
