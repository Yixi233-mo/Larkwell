"""
索引模块包
==========
提供文档索引和 Git 变更监听功能。
"""

from indexing.git_watcher import GitWatcher, scan_clean_changes
from indexing.document_loader import DocumentLoader

__all__ = [
    "GitWatcher",
    "scan_clean_changes",
    "DocumentLoader",
]
