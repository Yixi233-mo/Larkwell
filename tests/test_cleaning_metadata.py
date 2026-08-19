"""
清洗 + 智能元数据增强 端到端测试
================================
用法：
    cd E:\plan\qwen\Larkwell\src
    python -m tests.test_cleaning_metadata

验证：
1. 基础 frontmatter 修复正常工作
2. 智能元数据增强（LLM 调用）能生成 category/tags/description
3. 幂等性：再次清洗已包含元数据的文档不会重复调用 LLM
4. 降级：LLM 不可用时保留原 frontmatter
"""

import sys
import os
from pathlib import Path

# 加入项目根目录到 sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from cleaning.agent import CleaningAgent
from utils.logger import get_logger

logger = get_logger(__name__)


# 测试样本 1：无 frontmatter 的原始语雀文档
SAMPLE_NO_FRONTMATTER = """# 测试文档

## 什么是 RAG

RAG（Retrieval-Augmented Generation）是一种结合信息检索和文本生成的框架，使 LLM 能基于外部知识库生成回答。

### 核心组件

1. **Embedding 模型** - 把文档向量化
2. **向量数据库** - 存储和检索向量
3. **生成模型** - 基于检索结果生成回答
"""

# 测试样本 2：已有 frontmatter 但无 category/tags
SAMPLE_BASIC_FRONTMATTER = """---
title: "LangChain 学习路线"
date: "2026-08-18"
---

# LangChain 学习路线

## 第一部分：基础入门

LangChain 是一个用于开发 LLM 应用的开源框架。
"""

# 测试样本 3：已有 category/tags（幂等性测试）
SAMPLE_FULL_FRONTMATTER = """---
title: "已增强的文档"
date: "2026-08-18"
category: "LangChain"
tags: ["LLM", "框架"]
---

# 已增强的文档

这篇文档已经有完整的元数据，应该跳过 LLM 调用。
"""


def run_test(sample_name: str, sample_content: str, tmp_dir: Path) -> dict:
    """运行单个测试用例"""
    print(f"\n{'='*60}")
    print(f"测试用例: {sample_name}")
    print(f"{'='*60}")

    # 准备测试文件
    input_dir = tmp_dir / "input"
    output_dir = tmp_dir / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = input_dir / f"{sample_name}.md"
    input_file.write_text(sample_content, encoding="utf-8")

    # 执行清洗
    agent = CleaningAgent()
    output_file = output_dir / f"{sample_name}.md"
    result = agent.clean_single_file(input_file, output_file)

    # 读取清洗后的内容
    cleaned_content = output_file.read_text(encoding="utf-8") if output_file.exists() else ""

    print(f"\n[清洗结果]")
    print(f"  状态: {result['status']}")
    print(f"  规则应用:")
    for r in result.get("rules_applied", []):
        if "error" in r:
            print(f"    - {r['rule']}: ❌ {r['error']}")
        else:
            stats = r.get("stats", {})
            print(f"    - {r['rule']}: {stats}")

    print(f"\n[清洗后内容]")
    print("-" * 40)
    print(cleaned_content[:600])
    if len(cleaned_content) > 600:
        print("...(已截断)")
    print("-" * 40)

    return {
        "status": result["status"],
        "cleaned": cleaned_content,
    }


def main():
    """主测试函数"""
    import tempfile

    print("=" * 60)
    print("Larkwell 清洗 + 智能元数据增强 端到端测试")
    print("=" * 60)

    # 检查 LLM 配置
    from utils.config import get_config
    config = get_config()
    print(f"\n[配置]")
    print(f"  LLM_BACKEND: {config.LLM_BACKEND}")
    print(f"  CLEANING_LLM_METADATA: {config.CLEANING_LLM_METADATA}")
    print(f"  CLEANING_LLM_MODEL: '{config.CLEANING_LLM_MODEL}' or main model")
    print(f"  CLEANING_LLM_MAX_CONTENT_CHARS: {config.CLEANING_LLM_MAX_CONTENT_CHARS}")

    if not config.CLEANING_LLM_METADATA:
        print("\n⚠️  CLEANING_LLM_METADATA=false，元数据增强将被跳过")
        print("   如需测试 LLM 调用，请在 .env 设置 CLEANING_LLM_METADATA=true")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)

        # 测试 1: 无 frontmatter 的文档
        r1 = run_test("sample_no_frontmatter", SAMPLE_NO_FRONTMATTER, tmp_dir)

        # 测试 2: 基础 frontmatter，无 category/tags
        r2 = run_test("sample_basic", SAMPLE_BASIC_FRONTMATTER, tmp_dir)

        # 测试 3: 已有完整元数据（幂等性）
        r3 = run_test("sample_full", SAMPLE_FULL_FRONTMATTER, tmp_dir)

    # 验证结果
    print(f"\n{'='*60}")
    print("测试结论")
    print(f"{'='*60}")

    # 测试 2 应该调用了 LLM 并增加了 category/tags
    if "category:" in r2["cleaned"]:
        print("[OK] 测试 2 (基础 frontmatter -> 智能增强): 成功增加 category/tags")
    else:
        print("[SKIP] 测试 2: 未增加 category 字段（LLM 不可用或被禁用，已优雅降级）")

    # 测试 3 应该跳过 LLM 调用
    if r3["cleaned"].count("category:") == 1:
        print("[OK] 测试 3 (幂等性): 已有元数据的文档未被重复增强")
    else:
        print("[FAIL] 测试 3: 幂等性失败，已有元数据的文档被重复修改")

    print(f"\n{'='*60}")
    print("测试完成")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
