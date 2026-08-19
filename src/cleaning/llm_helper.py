"""
清洗 LLM 辅助模块
=================
独立的 LLM 调用工具，专供清洗规则使用。
复用 auto 降级逻辑（优先 Ollama，失败走云端 API），
但不依赖 Agent 类，避免循环依赖。

职责：
- 接收文档正文，输出 JSON 格式的元数据
- 元数据包含：category（分类）、tags（标签列表）、description（一句话描述）
- 失败时返回 None，由调用方决定是否保留原 frontmatter
"""

import json
import re
import requests
from typing import Optional, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# ChatOpenAI 延迟导入：本地 Ollama 模式下不需要 langchain_openai 包
# 只有走 cloud 模式时才 import，避免环境里没装 cloud 包时整个模块 import 失败
def _import_chat_openai():
    """延迟导入 ChatOpenAI，未安装时抛出清晰的错误"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI

# Ollama 健康检查超时（秒）
_OLLAMA_HEALTH_TIMEOUT = 3

# 系统提示词 - 引导 LLM 输出严格的 JSON
# 设计要点：
#   - category 必须是领域感的中文名（不是英文缩写或框架名）
#   - 鼓励多篇文档归到同一领域（领域数控制在 3-7 个）
#   - tags 才是技术关键词（英文/缩写可接受）
_SYSTEM_PROMPT = """你是一个知识库目录规划助手。请从给定的 Markdown 文档内容中分析其所属技术领域，并以严格的 JSON 格式返回：

{
  "category": "技术领域中文名（2-6个字，如\"深度学习\"、\"大模型应用\"、\"知识图谱\"、\"前端开发\"、\"DevOps\"）",
  "tags": ["技术关键词1", "技术关键词2", "技术关键词3"],
  "description": "一句话描述这篇文档讲的是什么（不超过50字）"
}

【重要规则】
1. category 必须是**领域名**（如"深度学习"、"大模型应用"），不要用框架名（如"LangChain"）或缩写（如"RAG"、"GNN"）作为 category
2. category 必须是**中文**，不要用英文（如用"智能体架构"而非"AI Agent"）
3. 鼓励多篇文档归到**同一领域**：如果一篇讲 LangChain 一篇讲 RAG，都属于"大模型应用"领域
4. tags 才是技术关键词，可以用英文或缩写（如 "LangChain"、"RAG"、"Transformer"、"注意力机制"）
5. tags 数组包含 2-5 个相关关键词
6. description 是中文，不超过50字
7. 只返回 JSON，不要加任何其他文字、解释或代码块标记
8. JSON 必须能被 json.loads 解析

示例输出：
{"category": "大模型应用", "tags": ["LangChain", "LLM", "Agent", "工具调用"], "description": "介绍LangChain框架开发大模型应用的核心组件和实践"}"""


class CleaningLLMHelper:
    """清洗专用 LLM 调用器（独立于 Agent 类）"""

    def __init__(self, model_override: str = ""):
        """
        初始化清洗 LLM 调用器

        Args:
            model_override: 模型名覆盖（优先于 config.CLEANING_LLM_MODEL）
        """
        config = get_config()
        self.backend = config.LLM_BACKEND
        self.llm = None
        self.model_name = ""

        # 模型优先级：参数覆盖 > CLEANING_LLM_MODEL > 主配置
        if model_override:
            effective_model = model_override
        elif config.CLEANING_LLM_MODEL:
            effective_model = config.CLEANING_LLM_MODEL
        else:
            effective_model = ""  # 空字符串表示用主配置默认值

        # 显式 cloud
        if self.backend == "cloud":
            self._init_cloud(config, effective_model)

        # 显式 ollama
        elif self.backend == "ollama":
            self._init_ollama(config, effective_model)

        # auto / 未知
        else:
            ollama_ok = self._check_ollama_available(
                config.OLLAMA_BASE_URL,
                effective_model or config.OLLAMA_MODEL,
            )
            if ollama_ok:
                try:
                    self._init_ollama(config, effective_model)
                except Exception as e:
                    logger.warning(f"Ollama 初始化失败，降级到云端 API - {e}")
                    self._fallback_to_cloud(config, effective_model)
            else:
                self._fallback_to_cloud(config, effective_model)

        logger.info(f"CleaningLLMHelper 已初始化 [backend={self.backend}] 模型: {self.model_name}")

    def _init_ollama(self, config, model_override: str) -> None:
        """初始化 Ollama"""
        self.model_name = model_override or config.OLLAMA_MODEL
        self.base_url = config.OLLAMA_BASE_URL
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=0.1,  # 低温度保证元数据稳定
            base_url=self.base_url,
        )
        self.backend = "ollama"

    def _init_cloud(self, config, model_override: str) -> None:
        """初始化云端 API"""
        if not config.CLOUD_API_KEY:
            raise ValueError("LLM_BACKEND=cloud/auto 但未配置 CLOUD_API_KEY")
        try:
            ChatOpenAI = _import_chat_openai()
        except ImportError as e:
            raise RuntimeError(
                "LLM_BACKEND=cloud/auto 需要走云端 API，但未安装 langchain_openai。"
                f"请运行: pip install langchain_openai  (原因: {e})"
            )
        self.model_name = model_override or config.CLOUD_MODEL
        self.base_url = config.CLOUD_API_BASE
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.1,
            api_key=config.CLOUD_API_KEY,
            base_url=self.base_url,
        )
        self.backend = "cloud"

    def _fallback_to_cloud(self, config, model_override: str) -> None:
        """从 Ollama 降级到云端 API"""
        logger.warning("清洗 LLM: 本地 Ollama 不可用，自动降级到云端 API")
        cloud_model = model_override or config.CLOUD_MODEL
        self._init_cloud(config, cloud_model)

    @staticmethod
    def _check_ollama_available(base_url: str, model_name: str) -> bool:
        """检查 Ollama 服务和模型可用性"""
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/api/tags",
                timeout=_OLLAMA_HEALTH_TIMEOUT,
            )
            if resp.status_code != 200:
                return False
            tags = resp.json().get("models", [])
            if not tags:
                return False
            available = [m.get("name", "") for m in tags]
            if model_name not in available:
                logger.warning(f"Ollama 未找到模型 '{model_name}'，可用: {available}")
                return False
            return True
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return False
        except Exception as e:
            logger.warning(f"Ollama 健康检查异常: {e}")
            return False

    def generate_metadata(self, content: str, max_chars: int = 2000) -> Optional[Dict[str, Any]]:
        """
        调用 LLM 生成文档元数据

        Args:
            content: 文档正文（已去掉 frontmatter）
            max_chars: 截断长度，避免 token 爆炸

        Returns:
            {"category": str, "tags": list, "description": str}
            失败返回 None
        """
        if not self.llm:
            logger.warning("清洗 LLM 未初始化")
            return None

        # 截断正文
        truncated = content[:max_chars]
        if len(content) > max_chars:
            truncated += "\n...(文档已截断)"

        try:
            messages = [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=f"请分析以下文档并返回 JSON 元数据：\n\n{truncated}"),
            ]
            response = self.llm.invoke(messages)
            raw_text = response.content if hasattr(response, "content") else str(response)

            # 提取 JSON（容错：LLM 可能包了 ```json ... ```）
            parsed = self._extract_json(raw_text)
            if not parsed:
                logger.warning(f"LLM 输出无法解析为 JSON: {raw_text[:200]}")
                return None

            # 字段校验与规范化
            category = str(parsed.get("category", "")).strip()
            tags_raw = parsed.get("tags", [])
            tags = [str(t).strip() for t in tags_raw if str(t).strip()] if isinstance(tags_raw, list) else []
            description = str(parsed.get("description", "")).strip()

            if not category or not tags:
                logger.warning(f"LLM 元数据字段不完整: category={category}, tags={tags}")
                return None

            return {
                "category": category,
                "tags": tags[:5],  # 最多 5 个
                "description": description[:100],  # 最多 100 字
            }

        except Exception as e:
            logger.warning(f"LLM 生成元数据失败: {e}")
            return None

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict]:
        """从可能包含 markdown 代码块或多余文字的输出中提取 JSON"""
        # 1. 直接尝试解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. 尝试提取 ```json ... ``` 代码块
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. 尝试提取第一个 {...} 块
        match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None
