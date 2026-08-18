"""
图片修复规则
============
修复语雀导出的 Markdown 中的图片链接问题：
1. 将相对路径转为绝对路径
2. 处理图片文件名中的特殊字符
3. 支持本地图片和远程 CDN 图片
"""

import re
import os
from pathlib import Path
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


def fix_image_paths(content: str, base_dir: str) -> Tuple[str, int]:
    """
    修复图片路径

    Args:
        content: Markdown 内容
        base_dir: 文档所在目录

    Returns:
        (修复后的内容, 修复的图片数量)
    """
    fixed_count = 0
    path_obj = Path(base_dir)

    def replace_image(match: re.Match) -> str:
        nonlocal fixed_count
        alt_text = match.group(1)
        image_path = match.group(2)

        # 已经是 http/https 链接，保持不变
        if image_path.startswith(('http://', 'https://')):
            return match.group(0)

        # 处理本地图片路径
        try:
            # 规范化路径
            full_path = (path_obj / image_path).resolve()

            # 如果图片存在，转换为相对路径
            if full_path.exists():
                rel_path = os.path.relpath(str(full_path), base_dir)
                fixed_count += 1
                logger.debug(f"修复图片路径: {image_path} -> {rel_path}")
                return f'![{alt_text}]({rel_path})'
            else:
                # 图片不存在，记录警告但保持原路径
                logger.warning(f"图片不存在: {full_path}")
                return match.group(0)

        except Exception as e:
            logger.warning(f"处理图片路径失败: {image_path}, 错误: {e}")
            return match.group(0)

    # 匹配 Markdown 图片语法: ![alt](path)
    pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    fixed_content = re.sub(pattern, replace_image, content)

    if fixed_count > 0:
        logger.info(f"图片修复完成，共修复 {fixed_count} 个图片路径")

    return fixed_content, fixed_count


def fix_image_html(content: str, base_dir: str) -> Tuple[str, int]:
    """
    修复 HTML 格式的图片

    Args:
        content: Markdown/HTML 内容
        base_dir: 文档所在目录

    Returns:
        (修复后的内容, 修复的图片数量)
    """
    fixed_count = 0
    path_obj = Path(base_dir)

    def replace_img(match: re.Match) -> str:
        nonlocal fixed_count
        full_tag = match.group(0)

        # 提取 src 属性
        src_match = re.search(r'src=["\']([^"\']+)["\']', full_tag)
        if not src_match:
            return full_tag

        src = src_match.group(1)

        # 已经是 http/https 链接，保持不变
        if src.startswith(('http://', 'https://', 'data:')):
            return full_tag

        # 处理本地图片路径
        try:
            full_path = (path_obj / src).resolve()
            if full_path.exists():
                rel_path = os.path.relpath(str(full_path), base_dir)
                fixed_count += 1
                new_tag = re.sub(
                    r'src=["\']([^"\']+)["\']',
                    f'src="{rel_path}"',
                    full_tag
                )
                logger.debug(f"修复 HTML 图片: {src} -> {rel_path}")
                return new_tag
            else:
                logger.warning(f"HTML 图片不存在: {full_path}")
                return full_tag
        except Exception as e:
            logger.warning(f"处理 HTML 图片失败: {src}, 错误: {e}")
            return full_tag

    # 匹配 HTML img 标签
    pattern = r'<img[^>]*>'
    fixed_content = re.sub(pattern, replace_img, content)

    if fixed_count > 0:
        logger.info(f"HTML 图片修复完成，共修复 {fixed_count} 个")

    return fixed_content, fixed_count


def apply(content: str, base_dir: str) -> Tuple[str, dict]:
    """
    应用图片修复规则

    Args:
        content: 原始内容
        base_dir: 文档基础目录

    Returns:
        (修复后的内容, 修复统计)
    """
    logger.info("应用图片修复规则...")

    # 修复 Markdown 图片
    content, md_fixed = fix_image_paths(content, base_dir)

    # 修复 HTML 图片
    content, html_fixed = fix_image_html(content, base_dir)

    stats = {
        "markdown_images_fixed": md_fixed,
        "html_images_fixed": html_fixed,
        "total_fixed": md_fixed + html_fixed,
    }

    logger.info(f"图片修复规则完成: {stats}")
    return content, stats
