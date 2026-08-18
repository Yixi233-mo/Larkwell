"""
Git 变更监听器
==============
监听 repos/clean 目录的 Git 变更，检测新增、修改、删除的文件，
用于触发向量库的增量更新。
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


class GitWatcher:
    """Git 变更监听器"""

    def __init__(self):
        """初始化 Git 监听器"""
        self.config = get_config()
        self.project_root = Path(self.config.BASE_DIR).resolve()
        self.clean_repo_path = Path(self.config.get_clean_repo_absolute_path())
        self.state_file = self.project_root / ".sync_state.json"

        # 加载上次同步状态
        self.last_state = self._load_state()

        logger.info(f"Git 监听器已初始化")
        logger.info(f"监听目录: {self.clean_repo_path}")

    def _load_state(self) -> Dict:
        """加载上次同步状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")

        return {
            "last_sync_time": None,
            "file_hashes": {},
        }

    def _save_state(self) -> None:
        """保存当前状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.last_state, f, indent=2, ensure_ascii=False)
            logger.debug(f"状态已保存: {self.state_file}")
        except Exception as e:
            logger.error(f"保存状态文件失败: {e}")

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        计算文件的 MD5 哈希值

        Args:
            file_path: 文件路径

        Returns:
            MD5 哈希值
        """
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""

    def scan_changes(self) -> Dict:
        """
        扫描变更的文件

        Returns:
            变更摘要，包含 added, modified, deleted 文件列表
        """
        logger.info("开始扫描文件变更...")

        current_files = {}
        added_files = []
        modified_files = []
        deleted_files = []

        # 扫描当前目录下的所有 Markdown 文件
        if self.clean_repo_path.exists():
            for file_path in self.clean_repo_path.rglob('*.md'):
                relative_path = str(file_path.relative_to(self.clean_repo_path))
                file_hash = self._compute_file_hash(file_path)
                current_files[relative_path] = {
                    "hash": file_hash,
                    "path": str(file_path),
                }

                # 检查是否为新增或修改
                if relative_path not in self.last_state.get("file_hashes", {}):
                    added_files.append(relative_path)
                elif self.last_state["file_hashes"][relative_path]["hash"] != file_hash:
                    modified_files.append(relative_path)

        # 检查删除的文件
        old_files = self.last_state.get("file_hashes", {})
        for old_path in old_files:
            if old_path not in current_files:
                deleted_files.append(old_path)

        # 更新状态
        self.last_state["file_hashes"] = current_files
        self.last_state["last_sync_time"] = datetime.now().isoformat()
        self._save_state()

        summary = {
            "scan_time": self.last_state["last_sync_time"],
            "total_files": len(current_files),
            "added": added_files,
            "modified": modified_files,
            "deleted": deleted_files,
            "has_changes": bool(added_files or modified_files or deleted_files),
        }

        logger.info(f"扫描完成: 总计 {summary['total_files']} 个文件, "
                     f"新增 {len(added_files)}, 修改 {len(modified_files)}, 删除 {len(deleted_files)}")

        return summary

    def get_file_paths(self, changes: Dict) -> Dict[str, List[str]]:
        """
        获取变更文件的完整路径

        Args:
            changes: scan_changes 返回的变更摘要

        Returns:
            分类的文件路径字典
        """
        result = {
            "added": [],
            "modified": [],
            "deleted": [],
        }

        for change_type in ["added", "modified", "deleted"]:
            for relative_path in changes.get(change_type, []):
                full_path = str(self.clean_repo_path / relative_path)
                result[change_type].append(full_path)

        return result

    def get_stats(self) -> Dict:
        """获取状态统计"""
        return {
            "clean_repo_path": str(self.clean_repo_path),
            "tracked_files": len(self.last_state.get("file_hashes", {})),
            "last_sync_time": self.last_state.get("last_sync_time"),
        }


def scan_clean_changes() -> Dict:
    """
    扫描清洗仓库变更的便捷函数

    Returns:
        变更摘要
    """
    watcher = GitWatcher()
    return watcher.scan_changes()
