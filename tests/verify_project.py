"""Larkwell 项目综合验证脚本"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, 'src')


def verify_larkwell():
    """Larkwell 项目综合验证"""
    results = {
        "project": "Larkwell",
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "passed": 0,
        "failed": 0,
    }

    def check(name: str, condition: bool, message: str = ""):
        status = "PASS" if condition else "FAIL"
        results["checks"].append({
            "name": name,
            "status": status,
            "message": message,
        })
        if condition:
            results["passed"] += 1
        else:
            results["failed"] += 1
        icon = "✅" if condition else "❌"
        print(f"  {icon} {name}: {message}")

    print("=" * 60)
    print("  Larkwell 项目综合验证")
    print("=" * 60)
    print()

    # 1. 检查项目结构
    print("1. 项目结构检查")
    print("-" * 40)
    project_root = Path('.')
    check("项目根目录", project_root.exists(), str(project_root.resolve()))
    check("src 目录", (project_root / 'src').exists())
    check("docs 目录", (project_root / 'docs').exists())
    check("static 目录", (project_root / 'static').exists())
    check("scripts 目录", (project_root / 'scripts').exists())
    print()

    # 2. 检查核心文件
    print("2. 核心文件检查")
    print("-" * 40)
    check("package.json", (project_root / 'package.json').exists())
    check("requirements.txt", (project_root / 'requirements.txt').exists())
    check(".env", (project_root / '.env').exists(), "环境配置文件")
    check("elog.config.js", (project_root / 'elog.config.js').exists())
    check("README.md", (project_root / 'README.md').exists())
    check("启动脚本 (Windows)", (project_root / 'scripts' / 'start.bat').exists())
    check("启动脚本 (PowerShell)", (project_root / 'scripts' / 'start.ps1').exists())
    print()

    # 3. 检查 Python 模块
    print("3. Python 模块检查")
    print("-" * 40)
    try:
        from utils.logger import get_logger
        logger = get_logger('verify')
        check("utils.logger 模块", True)
    except Exception as e:
        check("utils.logger 模块", False, str(e))

    try:
        from utils.config import get_config
        config = get_config()
        check("utils.config 模块", True)
        check(f"   - Collection 配置", config.MILVUS_COLLECTION == "larkwell_knowledge",
              f"当前值: {config.MILVUS_COLLECTION}")
    except Exception as e:
        check("utils.config 模块", False, str(e))

    try:
        from memory import ConversationMemory
        mem = ConversationMemory()
        mem.add_user_message('test')
        check("memory 模块", True)
    except Exception as e:
        check("memory 模块", False, str(e))

    try:
        from cleaning.rules import CLEANING_RULES
        check("cleaning.rules 模块", len(CLEANING_RULES) == 5,
              f"规则数量: {len(CLEANING_RULES)}")
    except Exception as e:
        check("cleaning.rules 模块", False, str(e))

    try:
        from tools import ALL_TOOLS
        check("tools 模块", len(ALL_TOOLS) >= 5,
              f"工具数量: {len(ALL_TOOLS)}")
    except Exception as e:
        check("tools 模块", False, str(e))

    try:
        from indexing.document_loader import DocumentLoader
        check("indexing.document_loader 模块", True)
    except Exception as e:
        check("indexing.document_loader 模块", False, str(e))

    try:
        from indexing.git_watcher import GitWatcher
        check("indexing.git_watcher 模块", True)
    except Exception as e:
        check("indexing.git_watcher 模块", False, str(e))

    try:
        from rag import RAGEngine
        check("rag 模块", True)
    except Exception as e:
        check("rag 模块", False, str(e))

    try:
        from agent import Agent
        check("agent 模块", True)
    except Exception as e:
        check("agent 模块", False, str(e))

    try:
        from app import app
        check("app 模块 (FastAPI)", True)
    except Exception as e:
        check("app 模块 (FastAPI)", False, str(e))

    print()

    # 4. 检查 VitePress 配置
    print("4. VitePress 配置检查")
    print("-" * 40)
    vitepress_config = project_root / 'docs' / '.vitepress' / 'config.mts'
    check("VitePress config.mts", vitepress_config.exists())

    index_md = project_root / 'docs' / 'index.md'
    check("docs/index.md", index_md.exists())

    # 检查标题是否为 Larkwell
    if index_md.exists():
        content = index_md.read_text(encoding='utf-8')
        check("   - 标题为 Larkwell", 'Larkwell' in content)

    print()

    # 5. 检查品牌一致性
    print("5. 品牌一致性检查")
    print("-" * 40)
    brand_files = [
        project_root / 'package.json',
        project_root / 'README.md',
        project_root / 'static' / 'index.html',
    ]
    all_consistent = True
    for f in brand_files:
        if f.exists():
            content = f.read_text(encoding='utf-8')
            if '知雀' in content or 'zhique' in content.lower():
                all_consistent = False
                check(f"品牌一致性 - {f.name}", False, f"包含旧品牌引用")
            else:
                check(f"品牌一致性 - {f.name}", True)

    print()

    # 输出总结
    print("=" * 60)
    print("  验证总结")
    print("=" * 60)
    total = results["passed"] + results["failed"]
    print(f"  总检查项: {total}")
    print(f"  通过: {results['passed']}")
    print(f"  失败: {results['failed']}")
    print(f"  通过率: {results['passed']/total*100:.1f}%")

    if results["failed"] == 0:
        print()
        print("  🎉 Larkwell 项目验证通过!")
    else:
        print()
        print("  ⚠️ 有部分检查未通过，请查看上方详情")

    return results


if __name__ == "__main__":
    results = verify_larkwell()

    # 保存结果
    with open('tests/verification_result.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
