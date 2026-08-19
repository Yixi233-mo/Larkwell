"""
重新规划所有文档的元数据
========================
一次性脚本：删除已有的 category/tags/description，调 LLM 重新生成。
用于 prompt 升级后批量重处理已有文档。

用法：
    cd E:\\plan\\qwen\\Larkwell
    set PYTHONPATH=src
    "D:\\acaconda\\envs\\agent_assistant\\python.exe" tests\\reprocess_metadata.py
"""

import sys
import re
import os
from pathlib import Path

# 加入项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cleaning.llm_helper import CleaningLLMHelper
from utils.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


def strip_metadata_fields(frontmatter: str) -> str:
    """从 frontmatter 中删除已有的 category/tags/description 字段"""
    lines = frontmatter.split('\n')
    kept = []
    for line in lines:
        # 跳过这些字段（包括数组多行格式）
        if re.match(r'^(category|tags|description)\s*:', line):
            continue
        kept.append(line)
    return '\n'.join(kept)


def extract_frontmatter(content: str):
    """提取 frontmatter 和 body"""
    if not (content.startswith('---\n') or content.startswith('---\r\n')):
        return None, content
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if match:
        return match.group(1), content[match.end():]
    return None, content


def escape_yaml_string(s: str) -> str:
    return s.replace('"', '\\"').replace('\n', ' ').strip()


def format_tags_yaml(tags: list) -> str:
    escaped = [f'"{escape_yaml_string(t)}"' for t in tags]
    return f'[{", ".join(escaped)}]'


def reprocess_file(file_path: Path, helper: CleaningLLMHelper, max_chars: int) -> dict:
    """重新处理单个文件的元数据"""
    name = file_path.name
    print(f"\n--- 处理: {name} ---")

    content = file_path.read_text(encoding='utf-8')
    fm_str, body = extract_frontmatter(content)

    if not fm_str:
        print(f"  跳过：无 frontmatter")
        return {"file": name, "status": "skipped"}

    # 1. 删除已有的 category/tags/description
    cleaned_fm = strip_metadata_fields(fm_str)
    print(f"  清理后 frontmatter 字段数: {len(cleaned_fm.split(chr(10)))}")

    # 2. 调 LLM 重新生成
    metadata = helper.generate_metadata(body, max_chars=max_chars)
    if not metadata:
        print(f"  跳过：LLM 未返回有效元数据")
        return {"file": name, "status": "llm_failed"}

    print(f"  LLM 输出: category={metadata['category']}, tags={metadata['tags']}")
    print(f"           description={metadata['description']}")

    # 3. 合并到 frontmatter
    new_lines = []
    for line in cleaned_fm.split('\n'):
        new_lines.append(line)
    new_lines.append(f'category: "{escape_yaml_string(metadata["category"])}"')
    new_lines.append(f'tags: {format_tags_yaml(metadata["tags"])}')
    new_lines.append(f'description: "{escape_yaml_string(metadata["description"])}"')

    new_fm = '\n'.join(new_lines)
    new_content = f'---\n{new_fm}\n---\n{body}'

    # 4. 写回文件
    file_path.write_text(new_content, encoding='utf-8')
    print(f"  ✅ 已更新: {file_path.name}")

    return {
        "file": name,
        "status": "updated",
        "category": metadata['category'],
        "tags": metadata['tags'],
        "description": metadata['description'],
    }


def main():
    print("=" * 60)
    print("重新规划所有文档的元数据")
    print("=" * 60)

    config = get_config()
    print(f"LLM_BACKEND: {config.LLM_BACKEND}")
    print(f"CLEANING_LLM_MODEL: {config.CLEANING_LLM_MODEL or '(用主配置)'}")
    print(f"MAX_CONTENT_CHARS: {config.CLEANING_LLM_MAX_CONTENT_CHARS}")

    # 初始化 LLM helper
    print("\n初始化 LLM helper...")
    try:
        helper = CleaningLLMHelper()
        print(f"backend={helper.backend}, model={helper.model_name}")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 扫描 docs/docs/
    docs_dir = PROJECT_ROOT / "docs" / "docs"
    if not docs_dir.exists():
        print(f"❌ 目录不存在: {docs_dir}")
        return

    md_files = sorted([f for f in docs_dir.glob('*.md') if f.name != 'index.md'])
    print(f"\n找到 {len(md_files)} 个 md 文件:")
    for f in md_files:
        print(f"  - {f.name}")

    # 逐个处理
    results = []
    for f in md_files:
        try:
            result = reprocess_file(f, helper, config.CLEANING_LLM_MAX_CONTENT_CHARS)
            results.append(result)
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            results.append({"file": f.name, "status": "error", "error": str(e)})

    # 汇总
    print(f"\n{'='*60}")
    print("处理汇总")
    print(f"{'='*60}")
    updated = [r for r in results if r['status'] == 'updated']
    print(f"成功更新: {len(updated)} / {len(results)}")
    print()
    print("新的分类分布:")
    cat_map = {}
    for r in updated:
        cat = r['category']
        if cat not in cat_map:
            cat_map[cat] = []
        cat_map[cat].append(r['file'])
    for cat, files in cat_map.items():
        print(f"  📁 {cat} ({len(files)} 篇):")
        for f in files:
            print(f"     - {f}")


if __name__ == "__main__":
    main()
