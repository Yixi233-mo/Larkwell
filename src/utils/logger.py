"""
统一日志模块
==========
所有模块共用的日志配置，确保日志格式一致。
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """
    日志管理器，提供统一的日志配置。
    """

    _loggers: dict = {}
    _initialized: bool = False

    @classmethod
    def _get_log_dir(cls) -> Path:
        """获取日志目录"""
        log_dir = Path(os.getenv("BASE_DIR", ".")) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @classmethod
    def _get_log_level(cls) -> str:
        """获取日志级别"""
        return os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def _get_log_format(cls) -> str:
        """获取日志格式"""
        return os.getenv(
            "LOG_FORMAT",
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )

    @classmethod
    def _setup_root_logger(cls) -> None:
        """初始化根日志配置"""
        if cls._initialized:
            return

        log_level = cls._get_log_level()
        log_format = cls._get_log_format()

        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level))
        console_handler.setFormatter(formatter)

        # 文件处理器
        log_dir = cls._get_log_dir()
        file_handler = RotatingFileHandler(
            log_dir / "larkwell.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # 配置根日志
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str = "larkwell") -> logging.Logger:
        """
        获取日志实例

        Args:
            name: 日志器名称

        Returns:
            配置好的日志器实例
        """
        cls._setup_root_logger()

        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(cls._get_log_level())
            cls._loggers[name] = logger

        return cls._loggers[name]


def get_logger(name: str = "larkwell") -> logging.Logger:
    """
    获取日志器的便捷函数

    Args:
        name: 日志器名称

    Returns:
        Logger 实例

    Examples:
        >>> from utils.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    return Logger.get_logger(name)


# 兼容旧代码的 logger 别名
logger = get_logger("larkwell")
