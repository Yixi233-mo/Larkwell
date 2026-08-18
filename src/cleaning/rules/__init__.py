"""
清洗规则包
==========
导出所有清洗规则。
"""

from cleaning.rules.image_fix import apply as fix_images
from cleaning.rules.table_fix import apply as fix_tables
from cleaning.rules.code_fix import apply as fix_code_blocks
from cleaning.rules.frontmatter_fix import apply as fix_frontmatter
from cleaning.rules.newline_fix import apply as fix_newlines

# 规则执行顺序：图片 → 表格 → 代码 → Frontmatter → 空行压缩
CLEANING_RULES = [
    ("图片修复", fix_images),
    ("表格修复", fix_tables),
    ("代码块修复", fix_code_blocks),
    ("Frontmatter修复", fix_frontmatter),
    ("空行压缩", fix_newlines),
]

__all__ = [
    "fix_images",
    "fix_tables",
    "fix_code_blocks",
    "fix_frontmatter",
    "fix_newlines",
    "CLEANING_RULES",
]
