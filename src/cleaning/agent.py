"""
文档清洗 Agent
==============
实现文档清洗的主流程，按顺序应用清洗规则：
1. 图片修复
2. 表格修复
3. 代码块修复
4. Frontmatter 修复
5. 空行压缩

支持：
- 单文件处理
- 目录批量处理
- 增量更新
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from utils.logger import get_logger
from utils.config import get_config
from cleaning.rules import CLEANING_RULES

logger = get_logger(__name__)


class CleaningAgent:
    """文档清洗 Agent"""

    def __init__(self):
        """初始化清洗 Agent"""
        self.config = get_config()
        self.project_root = Path(self.config.BASE_DIR).resolve()
        self.input_dir = Path(self.config.get_raw_repo_absolute_path())
        self.output_dir = Path(self.config.get_clean_repo_absolute_path())
        self.cleaning_rules = CLEANING_RULES

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "total_rules_applied": 0,
            "start_time": None,
            "end_time": None,
        }

        logger.info(f"清洗 Agent 已初始化")
        logger.info(f"输入目录: {self.input_dir}")
        logger.info(f"输出目录: {self.output_dir}")

    def clean_single_file(self, input_path: Path, output_path: Path) -> Dict:
        """
        清洗单个文件

        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径

        Returns:
            处理结果
        """
        result = {
            "file": str(input_path),
            "status": "unknown",
            "rules_applied": [],
            "error": None,
        }

        try:
            # 读取原始内容
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            base_dir = str(input_path.parent)
            original_length = len(content)

            # 按顺序应用清洗规则
            for rule_name, rule_func in self.cleaning_rules:
                try:
                    content, rule_stats = rule_func(content, base_dir)
                    result["rules_applied"].append({
                        "rule": rule_name,
                        "stats": rule_stats,
                    })
                    self.stats["total_rules_applied"] += 1

                except Exception as e:
                    logger.warning(f"规则 {rule_name} 执行失败: {e}")
                    result["rules_applied"].append({
                        "rule": rule_name,
                        "error": str(e),
                    })

            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入清洗后的内容
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result["status"] = "success"
            result["original_length"] = original_length
            result["cleaned_length"] = len(content)
            result["output_file"] = str(output_path)

            logger.info(f"清洗成功: {input_path.name} ({original_length} -> {len(content)} 字符)")

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.stats["files_failed"] += 1
            logger.error(f"清洗失败: {input_path}, 错误: {e}")

        return result

    def clean_directory(self, input_dir: Path = None, output_dir: Path = None) -> Dict:
        """
        清洗整个目录

        Args:
            input_dir: 输入目录（默认使用配置中的原始仓库路径）
            output_dir: 输出目录（默认使用配置中的清洗仓库路径）

        Returns:
            批量处理结果
        """
        if input_dir is None:
            input_dir = self.input_dir
        if output_dir is None:
            output_dir = self.output_dir

        logger.info("=" * 60)
        logger.info(f"开始批量清洗目录: {input_dir}")
        logger.info("=" * 60)

        self.stats["start_time"] = time.time()
        self.stats["files_processed"] = 0
        self.stats["files_failed"] = 0
        results = []

        # 查找所有 Markdown 文件
        md_files = list(input_dir.rglob('*.md'))
        logger.info(f"发现 {len(md_files)} 个 Markdown 文件需要处理")

        for input_file in md_files:
            # 计算相对路径，保持目录结构
            relative_path = input_file.relative_to(input_dir)
            output_file = output_dir / relative_path

            # 清洗文件
            result = self.clean_single_file(input_file, output_file)
            results.append(result)

            if result["status"] == "success":
                self.stats["files_processed"] += 1

        self.stats["end_time"] = time.time()
        elapsed = self.stats["end_time"] - self.stats["start_time"]

        summary = {
            "total_files": len(md_files),
            "successful": self.stats["files_processed"],
            "failed": self.stats["files_failed"],
            "elapsed_seconds": round(elapsed, 2),
            "results": results,
        }

        logger.info("=" * 60)
        logger.info(f"批量清洗完成")
        logger.info(f"  总文件数: {summary['total_files']}")
        logger.info(f"  成功: {summary['successful']}")
        logger.info(f"  失败: {summary['failed']}")
        logger.info(f"  耗时: {summary['elapsed_seconds']}秒")
        logger.info("=" * 60)

        return summary

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


def run_clean_agent(input_dir: str = None, output_dir: str = None) -> Dict:
    """
    执行清洗 Agent 的便捷函数

    Args:
        input_dir: 输入目录
        output_dir: 输出目录

    Returns:
        处理结果摘要
    """
    agent = CleaningAgent()

    input_path = Path(input_dir) if input_dir else None
    output_path = Path(output_dir) if output_dir else None

    return agent.clean_directory(input_path, output_path)


if __name__ == "__main__":
    # 测试清洗
    result = run_clean_agent()
    print(json.dumps({
        "total_files": result["total_files"],
        "successful": result["successful"],
        "failed": result["failed"],
        "elapsed_seconds": result["elapsed_seconds"],
    }, indent=2, ensure_ascii=False))
