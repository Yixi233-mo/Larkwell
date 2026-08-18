"""
文档加载器
==========
负责加载和切分 Markdown 文档，为向量化做准备。
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


class DocumentLoader:
    """文档加载器"""

    def __init__(self):
        """初始化文档加载器"""
        self.config = get_config()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "],
        )

        logger.info(f"文档加载器已初始化 (chunk_size={self.config.CHUNK_SIZE}, "
                     f"chunk_overlap={self.config.CHUNK_OVERLAP})")

    def load_file(self, file_path: str) -> Optional[Document]:
        """
        加载单个文档文件

        Args:
            file_path: 文件路径

        Returns:
            Document 对象或 None
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.warning(f"文件不存在: {file_path}")
                return None

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取元数据
            metadata = self._extract_metadata(content, file_path)

            # 移除 Frontmatter（如果有）
            clean_content = self._remove_frontmatter(content)

            doc = Document(
                page_content=clean_content,
                metadata=metadata,
            )

            logger.debug(f"加载文档: {file_path} ({len(clean_content)} 字符)")
            return doc

        except Exception as e:
            logger.error(f"加载文档失败: {file_path}, 错误: {e}")
            return None

    def load_directory(self, dir_path: str) -> List[Document]:
        """
        加载目录下的所有 Markdown 文件

        Args:
            dir_path: 目录路径

        Returns:
            Document 对象列表
        """
        documents = []
        dir_path = Path(dir_path)

        if not dir_path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return documents

        md_files = list(dir_path.rglob('*.md'))
        logger.info(f"发现 {len(md_files)} 个 Markdown 文件")

        for file_path in md_files:
            doc = self.load_file(str(file_path))
            if doc:
                documents.append(doc)

        logger.info(f"成功加载 {len(documents)} 个文档")
        return documents

    def split_document(self, doc: Document) -> List[Document]:
        """
        切分文档为多个块

        Args:
            doc: 原始文档

        Returns:
            切分后的文档块列表
        """
        try:
            chunks = self.text_splitter.split_documents([doc])
            logger.debug(f"文档切分: {doc.metadata.get('source', 'unknown')} -> {len(chunks)} 块")
            return chunks
        except Exception as e:
            logger.error(f"文档切分失败: {e}")
            return []

    def split_text(self, text: str, metadata: Dict = None) -> List[Document]:
        """
        直接切分文本

        Args:
            text: 原始文本
            metadata: 元数据

        Returns:
            切分后的文档块列表
        """
        try:
            chunks = self.text_splitter.create_documents([text], [metadata or {}])
            return chunks
        except Exception as e:
            logger.error(f"文本切分失败: {e}")
            return []

    def _extract_metadata(self, content: str, file_path: str) -> Dict:
        """
        从文档中提取元数据

        Args:
            content: 文档内容
            file_path: 文件路径

        Returns:
            元数据字典
        """
        metadata = {
            "source": file_path,
            "file_name": os.path.basename(file_path),
        }

        # 尝试提取 Frontmatter 中的元数据
        fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            # 简单解析 YAML 字段
            for line in fm_content.split('\n'):
                if ':' in line and not line.startswith(' '):
                    key, _, value = line.partition(':')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        metadata[key] = value

        return metadata

    def _remove_frontmatter(self, content: str) -> str:
        """
        移除 YAML Frontmatter

        Args:
            content: 文档内容

        Returns:
            移除 Frontmatter 后的内容
        """
        return re.sub(r'^---\n.*?\n---\n', '', content, count=1, flags=re.DOTALL)
