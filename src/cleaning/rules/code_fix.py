"""
代码块修复规则
==============
修复语雀导出的 Markdown 中的代码块格式问题：
1. 补全代码块语言标记
2. 修复嵌套代码块
3. 处理缩进问题
4. 修复 YAML 代码块
"""

import re
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

# 常见的编程语言关键字
LANGUAGE_KEYWORDS = {
    'python': ['def ', 'import ', 'from ', 'class ', 'try:', 'elif ', 'except', 'lambda ', 'print('],
    'javascript': ['function ', 'const ', 'let ', 'var ', '=>', 'require(', 'module.exports'],
    'typescript': ['interface ', 'type ', 'implements ', 'extends ', ': string', ': number'],
    'java': ['public ', 'private ', 'class ', 'void ', 'System.out', 'String ', 'int ', 'return '],
    'go': ['package ', 'func ', 'import ', 'var ', ':=', 'fmt.'],
    'rust': ['fn ', 'let ', 'impl ', 'trait ', 'use ', 'mod '],
    'sql': ['SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'FROM ', 'WHERE ', 'CREATE TABLE'],
    'bash': ['#!/bin/bash', '#!/bin/sh', 'echo ', 'export ', 'if [', 'for ', 'while '],
    'yaml': [': ', '- ', '  ', 'key: ', 'name: '],
    'json': ['{', '}', '"key"', '"name"'],
    'html': ['<html', '<div', '<head', '<body', '<script', '<style'],
    'css': ['{', '}', '#', '.', '@media', 'color:', 'font-', 'margin:', 'padding:'],
    'markdown': ['# ', '## ', '### ', '- ', '* ', '> ', '```'],
}


def _detect_language(code: str) -> str:
    """
    检测代码语言

    Args:
        code: 代码内容

    Returns:
        检测到的语言名称
    """
    code_lower = code.lower()

    scores = {}
    for lang, keywords in LANGUAGE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in code_lower)
        if score > 0:
            scores[lang] = score

    if scores:
        return max(scores, key=scores.get)
    return ''


def _fix_fenced_code_blocks(content: str) -> Tuple[str, int]:
    """
    修复围栏代码块

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 修复数量)
    """
    fixed_count = 0

    # 匹配 ```code ... ``` 格式
    pattern = r'```(?:\w+)?\n(.*?)```'

    def replace_code(match: re.Match) -> str:
        nonlocal fixed_count
        full_match = match.group(0)
        code_content = match.group(1)

        # 检测语言
        lang = _detect_language(code_content)

        if lang:
            fixed_count += 1
            return f'```{lang}\n{code_content}```'
        else:
            # 没有检测到语言，保持原样
            return full_match

    fixed_content = re.sub(pattern, replace_code, content, flags=re.DOTALL)

    if fixed_count > 0:
        logger.info(f"代码块语言标记修复完成，共修复 {fixed_count} 个")

    return fixed_content, fixed_count


def _fix_indentation(content: str) -> Tuple[str, int]:
    """
    修复代码块缩进

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 修复数量)
    """
    fixed_count = 0
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # 将 tab 替换为 4 空格
        if '\t' in line:
            line = line.replace('\t', '    ')
            fixed_count += 1
        fixed_lines.append(line)

    if fixed_count > 0:
        logger.info(f"缩进修复完成，共修复 {fixed_count} 处")

    return '\n'.join(fixed_lines), fixed_count


def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    """
    应用代码块修复规则

    Args:
        content: 原始内容
        base_dir: 文档基础目录（此规则不需要）

    Returns:
        (修复后的内容, 修复统计)
    """
    logger.info("应用代码块修复规则...")

    # 修复围栏代码块
    content, blocks_fixed = _fix_fenced_code_blocks(content)

    # 修复缩进
    content, indent_fixed = _fix_indentation(content)

    stats = {
        "code_blocks_fixed": blocks_fixed,
        "indentation_fixed": indent_fixed,
        "total_fixed": blocks_fixed + indent_fixed,
    }

    logger.info(f"代码块修复规则完成: {stats}")
    return content, stats
