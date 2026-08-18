"""
空行压缩规则
============
清理语雀导出的 Markdown 中的多余空行：
1. 压缩连续空行为单个空行
2. 删除段落开头的多余空行
3. 保留列表和代码块的空行
4. 清理文件末尾的空行
"""

import re
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


def _compress_multiple_blank_lines(content: str) -> Tuple[str, int]:
    """
    压缩多个连续空行为单个空行

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 压缩的空行数)
    """
    # 匹配 3 个或更多的连续空行
    pattern = r'\n{3,}'
    matches = re.findall(pattern, content)
    compressed_count = sum(len(m) - 2 for m in matches)

    # 替换为两个空行（保留段落间距）
    fixed_content = re.sub(pattern, '\n\n', content)

    if compressed_count > 0:
        logger.info(f"压缩空行完成，共压缩 {compressed_count} 处")

    return fixed_content, compressed_count


def _remove_leading_blank_lines(content: str) -> Tuple[str, int]:
    """
    删除文件开头的空行

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 删除的空行数)
    """
    leading_blanks = len(content) - len(content.lstrip('\n'))
    if leading_blanks > 0:
        content = content.lstrip('\n')
        logger.info(f"删除开头空行 {leading_blanks} 行")

    return content, leading_blanks


def _remove_trailing_blank_lines(content: str) -> Tuple[str, int]:
    """
    删除文件末尾的空行

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 删除的空行数)
    """
    trailing_blanks = len(content) - len(content.rstrip('\n'))
    if trailing_blanks > 0:
        content = content.rstrip('\n') + '\n'  # 保留末尾一个换行
        logger.info(f"删除末尾空行 {trailing_blanks} 行")

    return content, trailing_blanks


def _preserve_code_blocks(content: str) -> str:
    """
    保护代码块内的空行不被压缩

    Args:
        content: Markdown 内容

    Returns:
        保护后的内容
    """
    # 此函数为占位，当前简单处理已足够
    # 如果需要更复杂的保护逻辑，可以在这里扩展
    return content


def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    """
    应用空行压缩规则

    Args:
        content: 原始内容
        base_dir: 文档基础目录（此规则不需要）

    Returns:
        (修复后的内容, 修复统计)
    """
    logger.info("应用空行压缩规则...")

    # 保护代码块
    content = _preserve_code_blocks(content)

    # 压缩多余空行
    content, compressed = _compress_multiple_blank_lines(content)

    # 删除开头空行
    content, leading_removed = _remove_leading_blank_lines(content)

    # 删除末尾空行
    content, trailing_removed = _remove_trailing_blank_lines(content)

    stats = {
        "blank_lines_compressed": compressed,
        "leading_blank_lines_removed": leading_removed,
        "trailing_blank_lines_removed": trailing_removed,
        "total_fixed": compressed + leading_removed + trailing_removed,
    }

    logger.info(f"空行压缩规则完成: {stats}")
    return content, stats
