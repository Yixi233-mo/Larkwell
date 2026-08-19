"""
清洗规则包
==========
导出所有清洗规则。
"""

from cleaning.rules.image_fix import apply as fix_images
from cleaning.rules.table_fix import apply as fix_tables
from cleaning.rules.code_fix import apply as fix_code_blocks
from cleaning.rules.frontmatter_fix import apply as fix_frontmatter
from cleaning.rules.metadata_enrich import apply as enrich_metadata
from cleaning.rules.newline_fix import apply as fix_newlines

# 规则执行顺序：
# 1. 图片修复   - 下载 CDN 图片到本地，修复相对路径
# 2. 表格修复   - 修复语雀表格语法
# 3. 代码块修复 - 修复代码块围栏
# 4. Frontmatter 基础修复 - 补全/修复基础 frontmatter（title/date/source）
# 5. 智能元数据增强 - 调 LLM 生成 category/tags/description（可配置开关，幂等）
# 6. 空行压缩   - 压缩多余空行
#
# 注意：metadata_enrich 必须在 frontmatter_fix 之后（依赖 frontmatter 已存在）
#       必须在 newline_fix 之前（避免空行压缩破坏 frontmatter 结构）
CLEANING_RULES = [
    ("图片修复", fix_images),
    ("表格修复", fix_tables),
    ("代码块修复", fix_code_blocks),
    ("Frontmatter修复", fix_frontmatter),
    ("智能元数据增强", enrich_metadata),
    ("空行压缩", fix_newlines),
]

__all__ = [
    "fix_images",
    "fix_tables",
    "fix_code_blocks",
    "fix_frontmatter",
    "enrich_metadata",
    "fix_newlines",
    "CLEANING_RULES",
]
