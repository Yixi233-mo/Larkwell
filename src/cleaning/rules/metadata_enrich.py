"""
智能元数据增强规则
==================
在基础 Frontmatter 修复之后运行，调用 LLM 为文档生成：
- category: 主分类（一个字符串）
- tags: 标签列表（2-5 个）
- description: 一句话描述

设计原则：
1. 增量添加：不覆盖已有 frontmatter 字段
2. 幂等性：已包含 category/tags 的文档跳过（避免重复调用 LLM）
3. 可降级：LLM 不可用 / JSON 解析失败 → 保留原 frontmatter，继续流程
4. 可配置：通过 CLEANING_LLM_METADATA 开关控制是否启用
"""

import re
from typing import Tuple, Dict, Optional

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# 模块级 LLM helper 单例（避免每个文件都初始化一次）
_llm_helper = None


def _get_llm_helper():
    """延迟初始化 LLM helper 单例"""
    global _llm_helper
    if _llm_helper is None:
        try:
            from cleaning.llm_helper import CleaningLLMHelper
            _llm_helper = CleaningLLMHelper()
        except Exception as e:
            logger.warning(f"CleaningLLMHelper 初始化失败: {e}")
            _llm_helper = False  # 用 False 标记初始化失败，避免反复尝试
    return _llm_helper


def _has_metadata(frontmatter: str) -> bool:
    """检查 frontmatter 是否已包含 category/tags 字段"""
    return bool(re.search(r'^category\s*:', frontmatter, re.MULTILINE)) or \
           bool(re.search(r'^tags\s*:', frontmatter, re.MULTILINE))


def _extract_frontmatter(content: str) -> Tuple[Optional[str], str]:
    """提取 frontmatter 与正文"""
    if not (content.startswith('---\n') or content.startswith('---\r\n')):
        return None, content

    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():]
    return None, content


def _escape_yaml_string(s: str) -> str:
    """转义 YAML 字符串中的特殊字符"""
    return s.replace('"', '\\"').replace('\n', ' ').strip()


def _format_tags_yaml(tags: list) -> str:
    """格式化 tags 为 YAML 行内数组格式"""
    escaped = [f'"{_escape_yaml_string(t)}"' for t in tags]
    return f'[{", ".join(escaped)}]'


def _merge_metadata(frontmatter: str, metadata: Dict) -> str:
    """把 LLM 生成的元数据合并到现有 frontmatter 中（不覆盖已有字段）"""
    lines = frontmatter.split('\n')
    new_lines = []
    has_category = False
    has_tags = False
    has_description = False

    for line in lines:
        # 检查已有字段
        if re.match(r'^category\s*:', line):
            has_category = True
        if re.match(r'^tags\s*:', line):
            has_tags = True
        if re.match(r'^description\s*:', line):
            has_description = True
        new_lines.append(line)

    # 追加缺失的字段（在末尾追加，不破坏已有顺序）
    extras = []
    if not has_category and metadata.get("category"):
        extras.append(f'category: "{_escape_yaml_string(metadata["category"])}"')
    if not has_tags and metadata.get("tags"):
        extras.append(f'tags: {_format_tags_yaml(metadata["tags"])}')
    if not has_description and metadata.get("description"):
        extras.append(f'description: "{_escape_yaml_string(metadata["description"])}"')

    if extras:
        # 在 frontmatter 最后一行（不含 ---）之前插入新字段
        # 因为 frontmatter 字符串已经不包含外层 ---
        return frontmatter + '\n' + '\n'.join(extras)
    return frontmatter


def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    """
    应用智能元数据增强规则

    Args:
        content: 原始内容（应该已经过 frontmatter_fix 处理过）
        base_dir: 文档基础目录

    Returns:
        (增强后的内容, 统计信息)
    """
    stats = {
        "metadata_enriched": 0,
        "metadata_skipped": 0,
        "llm_error": 0,
        "feature_disabled": 0,
    }

    # 1. 检查功能是否启用
    config = get_config()
    if not config.CLEANING_LLM_METADATA:
        stats["feature_disabled"] = 1
        logger.debug("智能元数据增强已禁用（CLEANING_LLM_METADATA=false）")
        return content, stats

    logger.info("应用智能元数据增强规则...")

    # 2. 提取 frontmatter 和正文
    existing_fm, body = _extract_frontmatter(content)
    if existing_fm is None:
        # 没有 frontmatter，跳过（应该先经过 frontmatter_fix）
        logger.warning("文档无 frontmatter，跳过元数据增强（请确保 frontmatter_fix 规则在前）")
        stats["metadata_skipped"] = 1
        return content, stats

    # 3. 已有 category/tags → 跳过（幂等性）
    if _has_metadata(existing_fm):
        logger.debug(f"文档已有 category/tags，跳过 LLM 调用")
        stats["metadata_skipped"] = 1
        return content, stats

    # 4. 调用 LLM 生成元数据
    helper = _get_llm_helper()
    if not helper:
        logger.warning("LLM helper 不可用，跳过元数据增强")
        stats["llm_error"] = 1
        return content, stats

    metadata = helper.generate_metadata(
        body,
        max_chars=config.CLEANING_LLM_MAX_CONTENT_CHARS,
    )

    if not metadata:
        logger.warning("LLM 未返回有效元数据，保留原 frontmatter")
        stats["llm_error"] = 1
        return content, stats

    # 5. 合并元数据到 frontmatter
    enhanced_fm = _merge_metadata(existing_fm, metadata)
    new_content = f'---\n{enhanced_fm}\n---\n{body}'

    stats["metadata_enriched"] = 1
    logger.info(
        f"元数据增强成功: category={metadata['category']}, "
        f"tags={metadata['tags']}, description={metadata['description'][:30]}..."
    )

    return new_content, stats
