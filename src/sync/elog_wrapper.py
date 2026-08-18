"""
Elog 同步包装器
==============
封装 Elog CLI 调用，实现从语雀拉取文档的功能。
支持 Token 模式和账号密码模式。
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


class ElogWrapper:
    """
    Elog 同步工具包装类

    负责：
    1. 调用 Elog CLI 从语雀拉取文档
    2. 处理同步后的文件路径
    3. 记录同步日志
    """

    def __init__(self):
        """初始化 Elog 包装器"""
        self.config = get_config()
        self.project_root = Path(self.config.BASE_DIR).resolve()
        self.elog_config_path = self.project_root / "elog.config.js"

    def _check_elog_available(self) -> bool:
        """
        检查 Elog CLI 是否可用

        Returns:
            是否可用
        """
        try:
            result = subprocess.run(
                ["npx", "elog", "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.project_root),
            )
            if result.returncode == 0:
                logger.info(f"Elog 版本: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Elog 检查失败: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("Elog 检查超时")
            return False
        except Exception as e:
            logger.error(f"Elog 检查异常: {e}")
            return False

    def sync_from_yuque(self, force: bool = False) -> dict:
        """
        从语雀同步文档

        Args:
            force: 是否强制同步（忽略增量）

        Returns:
            同步结果字典
        """
        logger.info("=" * 60)
        logger.info("开始从语雀同步文档")
        logger.info("=" * 60)

        # 检查配置
        if not self.config.YUQUE_TOKEN:
            logger.error("语雀 Token 未配置")
            return {"status": "error", "message": "语雀 Token 未配置"}

        # 确保输出目录存在
        raw_repo_path = Path(self.config.get_raw_repo_absolute_path())
        raw_repo_path.mkdir(parents=True, exist_ok=True)

        # 构建 Elog 同步命令
        cmd = [
            "npx",
            "elog",
            "sync",
            "-c",
            str(self.elog_config_path),
        ]

        if force:
            cmd.append("--force")

        logger.info(f"执行命令: {' '.join(cmd)}")
        logger.info(f"工作目录: {self.project_root}")

        # 设置环境变量
        env = os.environ.copy()
        env["YUQUE_TOKEN"] = self.config.YUQUE_TOKEN
        env["YUQUE_LOGIN"] = self.config.YUQUE_LOGIN
        env["YUQUE_REPO"] = self.config.YUQUE_REPO

        try:
            # 执行同步
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=str(self.project_root),
                env=env,
            )

            logger.info(f"同步输出:\n{process.stdout}")

            if process.returncode == 0:
                logger.info("✅ 语雀同步成功")

                # 检查输出文件
                output_path = Path(self.config.get_docs_output_absolute_path())
                if output_path.exists():
                    md_files = list(output_path.glob("**/*.md"))
                    logger.info(f"📄 同步完成，共 {len(md_files)} 个 Markdown 文件")

                    # 输出统计
                    return {
                        "status": "success",
                        "message": "同步成功",
                        "file_count": len(md_files),
                        "output_path": str(output_path),
                        "stdout": process.stdout,
                    }
                else:
                    logger.warning("输出目录不存在或为空")
                    return {
                        "status": "success",
                        "message": "同步完成但未发现文档",
                        "file_count": 0,
                        "output_path": str(output_path),
                        "stdout": process.stdout,
                    }
            else:
                logger.error(f"❌ 语雀同步失败:\n{process.stderr}")
                return {
                    "status": "error",
                    "message": f"同步失败: {process.stderr}",
                    "returncode": process.returncode,
                    "stderr": process.stderr,
                }

        except subprocess.TimeoutExpired:
            logger.error("❌ 语雀同步超时（超过5分钟）")
            return {
                "status": "error",
                "message": "同步超时",
            }
        except Exception as e:
            logger.error(f"❌ 语雀同步异常: {e}")
            return {
                "status": "error",
                "message": f"同步异常: {str(e)}",
            }

    def clean_cache(self) -> dict:
        """
        清理 Elog 缓存

        Returns:
            清理结果
        """
        logger.info("清理 Elog 缓存")

        cmd = [
            "npx",
            "elog",
            "clean",
            "-c",
            str(self.elog_config_path),
        ]

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.project_root),
            )

            if process.returncode == 0:
                logger.info("✅ 缓存清理成功")
                return {"status": "success", "message": "缓存清理成功"}
            else:
                return {
                    "status": "error",
                    "message": f"清理失败: {process.stderr}",
                }

        except Exception as e:
            logger.error(f"缓存清理异常: {e}")
            return {"status": "error", "message": f"清理异常: {str(e)}"}

    def get_sync_status(self) -> dict:
        """
        获取同步状态信息

        Returns:
            状态字典
        """
        raw_repo_path = Path(self.config.get_raw_repo_absolute_path())
        docs_output_path = Path(self.config.get_docs_output_absolute_path())

        status = {
            "raw_repo_exists": raw_repo_path.exists(),
            "raw_repo_files": len(list(raw_repo_path.glob("**/*"))) if raw_repo_path.exists() else 0,
            "docs_output_exists": docs_output_path.exists(),
            "docs_files": len(list(docs_output_path.glob("**/*.md"))) if docs_output_path.exists() else 0,
        }

        logger.info(f"同步状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        return status


def run_sync(force: bool = False) -> dict:
    """
    执行语雀同步的便捷函数

    Args:
        force: 是否强制同步

    Returns:
        同步结果
    """
    wrapper = ElogWrapper()
    return wrapper.sync_from_yuque(force=force)


if __name__ == "__main__":
    # 测试同步
    result = run_sync(force=False)
    print(json.dumps(result, indent=2, ensure_ascii=False))
