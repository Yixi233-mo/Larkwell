"""
配置管理模块
==========
统一管理项目配置，从 .env 文件读取，支持类型转换。
"""

import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)

# 加载 .env 文件
_ENV_LOADED = False


def _ensure_env_loaded() -> None:
    """确保 .env 文件已加载"""
    global _ENV_LOADED
    if not _ENV_LOADED:
        # 先尝试 BASE_DIR 指定的路径
        env_path = Path(os.getenv("BASE_DIR", ".")) / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"已加载环境配置: {env_path}")
        else:
            # 向上查找 .env 文件（支持从 src/ 子目录运行）
            current = Path(__file__).resolve().parent  # src/utils/
            for _ in range(5):
                candidate = current / ".env"
                if candidate.exists():
                    load_dotenv(candidate)
                    logger.info(f"已加载环境配置: {candidate}")
                    break
                if current.parent == current:
                    break
                current = current.parent
            else:
                logger.warning("未找到 .env 文件，将使用默认配置")
        _ENV_LOADED = True


# 在模块加载时初始化
_ensure_env_loaded()


class Config:
    """
    配置管理类，提供类型安全的配置读取。
    """

    # ==================== 语雀配置 ====================
    YUQUE_TOKEN: str = os.getenv("YUQUE_TOKEN", "")
    YUQUE_LOGIN: str = os.getenv("YUQUE_LOGIN", "")
    YUQUE_REPO: str = os.getenv("YUQUE_REPO", "")

    # ==================== Milvus 配置 ====================
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_COLLECTION: str = os.getenv("MILVUS_COLLECTION", "yuque_knowledge")

    # ==================== Ollama 配置（本地模式） ====================
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen3:8b")
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "bge-m3")

    # ==================== Cloud API 配置（公开模式） ====================
    # LLM_BACKEND 后端模式：ollama | cloud | auto
    #   - ollama: 强制本地 Ollama（失败抛错）
    #   - cloud : 强制云端 API
    #   - auto  : 优先本地 Ollama，连接失败自动降级到云端 API（默认推荐）
    LLM_BACKEND: str = os.getenv("LLM_BACKEND", "auto")
    CLOUD_API_BASE: str = os.getenv("CLOUD_API_BASE", "https://api.siliconflow.cn/v1")
    CLOUD_API_KEY: str = os.getenv("CLOUD_API_KEY", "")
    CLOUD_MODEL: str = os.getenv("CLOUD_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    CLOUD_EMBED_MODEL: str = os.getenv("CLOUD_EMBED_MODEL", "BAAI/bge-m3")

    # ==================== Embedding 配置 ====================
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "768"))
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-zh-v1.5")

    # ==================== 文本切分配置 ====================
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "512"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "64"))

    # ==================== 检索配置 ====================
    TOP_K: int = int(os.getenv("TOP_K", "5"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.5"))

    # ==================== 路径配置 ====================
    BASE_DIR: str = os.getenv("BASE_DIR", ".")
    RAW_REPO_PATH: str = os.getenv("RAW_REPO_PATH", "./repos/raw")
    CLEAN_REPO_PATH: str = os.getenv("CLEAN_REPO_PATH", "./repos/clean")
    DOCS_OUTPUT_PATH: str = os.getenv("DOCS_OUTPUT_PATH", "./docs/docs")

    @classmethod
    def get_raw_repo_absolute_path(cls) -> str:
        """获取原始仓库的绝对路径"""
        return str(Path(cls.BASE_DIR) / cls.RAW_REPO_PATH)

    @classmethod
    def get_clean_repo_absolute_path(cls) -> str:
        """获取清洗仓库的绝对路径"""
        return str(Path(cls.BASE_DIR) / cls.CLEAN_REPO_PATH)

    @classmethod
    def get_docs_output_absolute_path(cls) -> str:
        """获取文档输出的绝对路径"""
        return str(Path(cls.BASE_DIR) / cls.DOCS_OUTPUT_PATH)

    @classmethod
    def validate(cls) -> dict[str, bool]:
        """
        验证必要配置是否存在

        Returns:
            配置项验证结果字典
        """
        results = {
            "YUQUE_TOKEN": bool(cls.YUQUE_TOKEN),
            "YUQUE_LOGIN": bool(cls.YUQUE_LOGIN),
            "YUQUE_REPO": bool(cls.YUQUE_REPO),
            "MILVUS_HOST": bool(cls.MILVUS_HOST),
            "MILVUS_PORT": cls.MILVUS_PORT > 0,
            "OLLAMA_BASE_URL": bool(cls.OLLAMA_BASE_URL),
        }

        for key, valid in results.items():
            status = "✅" if valid else "❌"
            logger.info(f"配置验证 {status} {key}: {'已配置' if valid else '未配置'}")

        return results


def get_config() -> Config:
    """
    获取全局配置实例

    Returns:
        Config 实例
    """
    return Config()
