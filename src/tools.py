"""
工具定义模块
============
扩展 Agent 的工具能力：文件读取、Shell 执行、网络搜索、知识库检索、语雀同步
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field
import requests
from duckduckgo_search import DDGS

from utils.logger import get_logger
from utils.config import get_config
from rag import RAGEngine

logger = get_logger(__name__)


# ========== 1. 文件读取工具 ==========

class ReadFileInput(BaseModel):
    """read_file 工具的输入参数"""
    file_path: str = Field(description="要读取的文件绝对路径或相对路径")


@tool("read_file")
def read_file(file_path: str) -> str:
    """
    读取本地文本文件内容。

    Args:
        file_path: 文件路径（绝对路径或相对路径）

    Returns:
        文件内容字符串，或错误信息
    """
    try:
        # 安全检查：禁止读取敏感路径
        sensitive_paths = ["/etc/passwd", "/etc/shadow", "~/.ssh", "~/.aws"]
        abs_path = os.path.abspath(file_path)
        for sensitive in sensitive_paths:
            if sensitive in abs_path:
                return f"错误：禁止读取敏感路径 {sensitive}"

        # 使用 pathlib 处理路径（支持中文和空格）
        path = Path(file_path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return f"文件内容（{len(content)} 字符）：\n{content}"

    except FileNotFoundError:
        return f"错误：文件不存在 {file_path}"
    except UnicodeDecodeError:
        return f"错误：文件编码不是 UTF-8，无法读取 {file_path}"
    except Exception as e:
        return f"错误：读取文件失败 - {str(e)}"


# ========== 2. Shell 执行工具 ==========

class ExecuteShellInput(BaseModel):
    """execute_shell 工具的输入参数"""
    command: str = Field(description="要执行的 Shell 命令")


@tool("execute_shell")
def execute_shell(command: str) -> str:
    """
    执行终端命令并返回输出。

    安全限制：
    - 超时 30 秒
    - 禁止危险命令（rm -rf /, format 等）

    Args:
        command: Shell 命令字符串

    Returns:
        标准输出和标准错误
    """
    dangerous_commands = [
        "rm -rf /",
        "rm -rf /*",
        "format",
        "mkfs",
        "dd if=/dev/zero",
        ":(){ :|:& };:",
        "chmod -R 777 /",
        "chown -R",
    ]

    command_lower = command.lower()
    for dangerous in dangerous_commands:
        if dangerous in command_lower:
            return f"错误：禁止执行危险命令 '{dangerous}'"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd(),
        )

        output = ""
        if result.stdout:
            output += f"标准输出：\n{result.stdout}\n"
        if result.stderr:
            output += f"标准错误：\n{result.stderr}\n"

        if not output:
            output = "命令执行成功，无输出"

        return output

    except subprocess.TimeoutExpired:
        return "错误：命令执行超时（30秒）"
    except Exception as e:
        return f"错误：命令执行失败 - {str(e)}"


# ========== 3. 网络搜索工具 ==========

class SearchInput(BaseModel):
    """web_search 工具的输入参数"""
    query: str = Field(description="搜索关键词")
    num_results: int = Field(default=5, description="返回结果数量（默认5）")


@tool("web_search")
def web_search(query: str, num_results: int = 5) -> str:
    """
    使用 DuckDuckGo 搜索互联网信息。

    Args:
        query: 搜索关键词
        num_results: 返回结果数量（默认5）

    Returns:
        搜索结果列表（标题+链接+摘要）
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

        if not results:
            return f"未找到关于 '{query}' 的搜索结果"

        output = f"搜索 '{query}' 的结果：\n\n"
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            link = result.get("href", "无链接")
            body = result.get("body", "无摘要")
            output += f"{i}. {title}\n   链接：{link}\n   摘要：{body}\n\n"

        return output

    except Exception as e:
        return f"错误：搜索失败 - {str(e)}"


# ========== 4. 知识库检索工具 ==========

_rag_engine: RAGEngine = None


def _get_rag_engine() -> RAGEngine:
    """延迟初始化 RAG 引擎"""
    global _rag_engine
    if _rag_engine is None:
        try:
            _rag_engine = RAGEngine()
        except Exception as e:
            logger.warning(f"RAG 引擎初始化失败 - {e}")
            return None
    return _rag_engine


@tool("knowledge_search")
def knowledge_search(query: str, top_k: int = 5) -> str:
    """
    从本地知识库（Milvus 向量数据库）中检索相关信息。
    知识库包含从语雀同步的文档内容。

    Args:
        query: 查询问题或关键词
        top_k: 返回结果数量（默认5）

    Returns:
        检索到的相关文档片段列表（含相似度分数）
    """
    rag = _get_rag_engine()
    if rag is None:
        return "错误：无法连接到知识库（Milvus 可能未启动）"

    try:
        results = rag.search(query, top_k=top_k)

        if not results:
            return f"知识库中未找到与 '{query}' 相关的信息"

        output = f"从知识库检索到 {len(results)} 条相关信息：\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. [相似度: {r.score:.2f}] 来源: {r.source}\n"
            output += f"   内容: {r.text[:300]}...\n\n"

        return output

    except Exception as e:
        return f"错误：知识库检索失败 - {str(e)}"


# ========== 5. 语雀同步工具 ==========

@tool("yuque_sync")
def yuque_sync(force: bool = False) -> str:
    """
    从语雀同步最新文档。
    执行 Elog 同步命令，拉取语雀知识库的最新内容。

    Args:
        force: 是否强制同步（默认 False，使用增量同步）

    Returns:
        同步结果信息
    """
    try:
        from sync.elog_wrapper import run_sync
        result = run_sync(force=force)

        if result["status"] == "success":
            return f"✅ 语雀同步成功！\n同步文件数: {result.get('file_count', 0)}"
        else:
            return f"❌ 语雀同步失败: {result.get('message', '未知错误')}"

    except ImportError:
        return "错误：同步模块未安装"
    except Exception as e:
        return f"错误：语雀同步异常 - {str(e)}"


# ========== 6. 知识库状态查询工具 ==========

@tool("knowledge_status")
def knowledge_status() -> str:
    """
    查询知识库状态，包括已索引文档数量、统计信息等。

    Returns:
        知识库状态信息
    """
    try:
        rag = _get_rag_engine()
        if rag is None:
            return "错误：无法连接到知识库（Milvus 可能未启动）"

        stats = rag.get_stats()
        docs = rag.list_documents()

        output = f"📊 知识库状态:\n\n"
        output += f"Collection: {stats['collection']}\n"
        output += f"实体数量: {stats['entity_count']}\n"
        output += f"嵌入模型: {stats['embedding_model']}\n"
        output += f"嵌入维度: {stats['embedding_dim']}\n"
        output += f"已索引文档数: {len(docs)}\n\n"

        if docs:
            output += "📚 文档列表:\n"
            for i, doc in enumerate(docs[:10], 1):
                source = doc['source'][:60]
                output += f"{i}. {source}\n"
            if len(docs) > 10:
                output += f"... 还有 {len(docs) - 10} 个文档\n"

        return output

    except Exception as e:
        return f"错误：获取知识库状态失败 - {str(e)}"


# ========== 工具注册 ==========

ALL_TOOLS = [
    read_file,
    execute_shell,
    web_search,
    knowledge_search,
    yuque_sync,
    knowledge_status,
]


def get_tool_descriptions() -> str:
    """
    生成工具描述文本，供 LLM 理解。

    Returns:
        格式化的工具描述字符串
    """
    descriptions = []
    for tool in ALL_TOOLS:
        desc = f"- {tool.name}: {tool.description}"
        descriptions.append(desc)
    return "\n".join(descriptions)


def get_tool_by_name(name: str):
    """
    根据名称获取工具对象。

    Args:
        name: 工具名称

    Returns:
        工具对象，或 None
    """
    for tool in ALL_TOOLS:
        if tool.name == name:
            return tool
    return None
