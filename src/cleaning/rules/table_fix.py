"""
表格修复规则
============
修复语雀导出的 Markdown 中的表格格式问题：
1. 补全表格分隔行
2. 修复对齐方式
3. 处理合并单元格
4. 修复空单元格
"""

import re
from typing import Tuple

from utils.logger import get_logger

logger = get_logger(__name__)


def _is_table_line(line: str) -> bool:
    """判断是否为表格行"""
    return '|' in line and line.strip().startswith('|')


def _parse_table_row(line: str) -> list:
    """解析表格行"""
    # 移除首尾的 | 并分割
    cells = line.strip().strip('|').split('|')
    return [cell.strip() for cell in cells]


def _generate_separator(col_count: int, alignments: list = None) -> str:
    """生成分隔行"""
    if alignments is None:
        alignments = ['center'] * col_count

    cells = []
    for align in alignments:
        if align == 'left':
            cells.append(':---')
        elif align == 'right':
            cells.append('---:')
        else:  # center
            cells.append(':---:')

    return '| ' + ' | '.join(cells) + ' |'


def fix_table_format(content: str) -> Tuple[str, int]:
    """
    修复表格格式

    Args:
        content: Markdown 内容

    Returns:
        (修复后的内容, 修复的表格数量)
    """
    fixed_count = 0
    lines = content.split('\n')
    fixed_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if _is_table_line(line):
            # 收集整个表格
            table_lines = []
            while i < len(lines) and _is_table_line(lines[i]):
                table_lines.append(lines[i])
                i += 1

            # 尝试修复表格
            fixed_table = _fix_single_table(table_lines)
            if fixed_table != table_lines:
                fixed_count += 1
                logger.debug(f"修复表格: {len(table_lines)} 行")

            fixed_lines.extend(fixed_table)
        else:
            fixed_lines.append(line)
            i += 1

    if fixed_count > 0:
        logger.info(f"表格修复完成，共修复 {fixed_count} 个表格")

    return '\n'.join(fixed_lines), fixed_count


def _fix_single_table(table_lines: list) -> list:
    """修复单个表格"""
    if len(table_lines) < 2:
        return table_lines

    # 解析所有行
    rows = [_parse_table_row(line) for line in table_lines]

    # 检查是否有分隔行
    has_separator = any(
        all(re.match(r'^:?-{3,}:?$', cell) for cell in row)
        for row in rows[1:]  # 从第二行开始检查
    )

    if not has_separator:
        # 需要添加分隔行
        if len(rows) >= 1:
            col_count = len(rows[0])
            separator = _generate_separator(col_count)
            # 在标题行后插入分隔行
            fixed_lines = [table_lines[0], separator] + table_lines[1:]
            return fixed_lines

    # 修复列数不一致的问题
    max_cols = max(len(row) for row in rows)
    if any(len(row) != max_cols for row in rows):
        # 补齐列数
        for j, row in enumerate(rows):
            while len(row) < max_cols:
                row.append('')
        # 重新生成表格行
        fixed_lines = []
        for row in rows:
            fixed_lines.append('| ' + ' | '.join(row) + ' |')
        return fixed_lines

    return table_lines


def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    """
    应用表格修复规则

    Args:
        content: 原始内容
        base_dir: 文档基础目录（此规则不需要）

    Returns:
        (修复后的内容, 修复统计)
    """
    logger.info("应用表格修复规则...")

    content, fixed_count = fix_table_format(content)

    stats = {
        "tables_fixed": fixed_count,
    }

    logger.info(f"表格修复规则完成: {stats}")
    return content, stats
