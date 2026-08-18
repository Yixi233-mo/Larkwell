"""
Frontmatter 修复规则
===================
修复语雀导出的 Markdown 中的 YAML Frontmatter 问题：
1. 补全缺失的 Frontmatter
2. 修复格式错误
3. 添加元数据字段
4. 处理特殊字符
"""

import re
from datetime import datetime
from typing import Tuple, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def _has_frontmatter(content: str) -> bool:
    """检查是否已有 Frontmatter"""
    return content.startswith('---\n') or content.startswith('---\r\n')


def _extract_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """
    提取 Frontmatter

    Args:
        content: Markdown 内容

    Returns:
        (frontmatter 内容或 None, 正文内容)
    """
    if not _has_frontmatter(content):
        return None, content

    # 匹配 --- ... --- 部分
    pattern = r'^---\n(.*?)\n---\n'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        return match.group(1), content[match.end():]

    return None, content


def _generate_frontmatter(title: str, source: str = '') -> str:
    """
    生成 Frontmatter

    Args:
        title: 文档标题
        source: 来源路径

    Returns:
        YAML Frontmatter 字符串
    """
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 清理标题中的特殊字符
    clean_title = title.replace('"', "'").replace('\n', ' ').strip()

    frontmatter = f"""---
title: "{clean_title}"
date: {now}
source: "{source}"
---"""

    return frontmatter


def _fix_existing_frontmatter(frontmatter: str) -> Tuple[str, bool]:
    """
    修复已有的 Frontmatter

    Args:
        frontmatter: 原始 Frontmatter

    Returns:
        (修复后的 Frontmatter, 是否进行了修改)
    """
    modified = False
    lines = frontmatter.split('\n')
    fixed_lines = []

    for line in lines:
        # 修复缩进（使用 2 空格）
        if line.startswith('  '):
            pass  # 已经是正确的缩进
        elif line.startswith('\t'):
            line = line.replace('\t', '  ')
            modified = True

        # 修复冒号后缺少空格
        line = re.sub(r'^(\w+):(\S)', r'\1: \2', line)
        if line != lines[len(fixed_lines)] if fixed_lines else line:
            modified = True

        fixed_lines.append(line)

    fixed = '\n'.join(fixed_lines)
    return fixed, modified


def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    """
    应用 Frontmatter 修复规则

    Args:
        content: 原始内容
        base_dir: 文档基础目录

    Returns:
        (修复后的内容, 修复统计)
    """
    logger.info("应用 Frontmatter 修复规则...")

    stats = {
        "frontmatter_added": 0,
        "frontmatter_fixed": 0,
    }

    # 提取已有的 Frontmatter
    existing_fm, body = _extract_frontmatter(content)

    if existing_fm is not None:
        # 修复已有的 Frontmatter
        fixed_fm, was_modified = _fix_existing_frontmatter(existing_fm)
        if was_modified:
            stats["frontmatter_fixed"] = 1
            logger.info("修复了已有的 Frontmatter")

        content = f'---\n{fixed_fm}\n---\n{body}'
    else:
        # 添加新的 Frontmatter
        # 从文件名或第一个标题提取标题
        title = ''
        title_match = re.match(r'^#\s+(.+)', body, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        elif base_dir:
            import os
            title = os.path.splitext(os.path.basename(base_dir))[0]
        else:
            title = '未命名文档'

        source = base_dir if base_dir else 'unknown'
        new_fm = _generate_frontmatter(title, source)
        content = f'{new_fm}\n{body}'
        stats["frontmatter_added"] = 1
        logger.info(f"添加了新的 Frontmatter, 标题: {title}")

    logger.info(f"Frontmatter 修复规则完成: {stats}")
    return content, stats
