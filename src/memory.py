"""
对话记忆管理模块
================
实现多轮对话的上下文追踪，支持：
- 滑动窗口：保留最近 N 轮对话
- 摘要压缩：超出窗口时生成历史摘要
"""

from typing import List, Dict, Any
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)


class ConversationMemory:
    """对话记忆管理器"""

    def __init__(self, max_turns: int = 10):
        """
        初始化记忆管理器

        Args:
            max_turns: 最大保留对话轮数（默认10轮）
        """
        self.max_turns = max_turns
        self.messages: List[Dict[str, Any]] = []
        self.summary: str = ""
        logger.info(f"对话记忆管理器已初始化，最大轮数: {max_turns}")

    def add_user_message(self, content: str) -> None:
        """
        添加用户消息

        Args:
            content: 用户输入内容
        """
        self.messages.append({
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self._check_and_compress()
        logger.debug(f"已添加用户消息，当前消息数: {len(self.messages)}")

    def add_assistant_message(self, content: str, tool_calls: List[Dict] = None) -> None:
        """
        添加助手回复

        Args:
            content: 助手回复内容
            tool_calls: 工具调用记录（可选）
        """
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if tool_calls:
            message["tool_calls"] = tool_calls
        self.messages.append(message)
        self._check_and_compress()
        logger.debug(f"已添加助手消息，当前消息数: {len(self.messages)}")

    def _check_and_compress(self) -> None:
        """检查消息数量，超出限制时进行压缩"""
        turns = len([m for m in self.messages if m["role"] == "user"])

        if turns > self.max_turns:
            self._compress_old_messages()

    def _compress_old_messages(self) -> None:
        """压缩旧消息为摘要"""
        user_messages = [m for m in self.messages if m["role"] == "user"]

        if len(user_messages) > self.max_turns:
            keep_from_index = len(self.messages) - (self.max_turns * 2)
            old_messages = self.messages[:keep_from_index]
            self.messages = self.messages[keep_from_index:]

            if old_messages:
                summary_parts = []
                for msg in old_messages[:10]:
                    summary_parts.append(f"{msg['role']}: {msg['content'][:50]}...")

                new_summary = "\n".join(summary_parts)
                if self.summary:
                    self.summary = f"{self.summary}\n\n[更早的历史]\n{new_summary}"
                else:
                    self.summary = f"[历史对话摘要]\n{new_summary}"

                logger.info(f"已压缩 {len(old_messages)} 条历史消息为摘要")

    def get_context_messages(self) -> List[Dict[str, str]]:
        """
        获取用于 LLM 的上下文消息列表

        Returns:
            格式化的消息列表（包含摘要和最近对话）
        """
        context = []

        if self.summary:
            context.append({
                "role": "system",
                "content": f"以下是之前的对话摘要：\n{self.summary}"
            })

        for msg in self.messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        return context

    def get_history(self) -> List[Dict[str, Any]]:
        """
        获取完整的对话历史（包含元数据）

        Returns:
            完整的消息列表
        """
        return self.messages.copy()

    def clear(self) -> None:
        """清空所有对话历史"""
        self.messages = []
        self.summary = ""
        logger.info("对话历史已清空")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            统计字典
        """
        return {
            "total_messages": len(self.messages),
            "user_messages": len([m for m in self.messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in self.messages if m["role"] == "assistant"]),
            "has_summary": bool(self.summary),
            "max_turns": self.max_turns
        }
