"""
Agent 核心模块
==============
实现 ReAct 模式的智能助手：
- 思考(Thought) → 行动(Action) → 观察(Observation) 循环
- 支持工具调用、多轮对话、异步流式响应
- 集成知识库检索和语雀同步能力
"""

import json
import re
import asyncio
import requests
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from tools import ALL_TOOLS, get_tool_by_name, get_tool_descriptions
from memory import ConversationMemory
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)


# Ollama 健康检查超时时间（秒），过短可能误判，过长会拖慢启动
_OLLAMA_HEALTH_TIMEOUT = 3


class Agent:
    """Larkwell Agent 智能助手（支持本地 Ollama / 云端 API 双模式 + 自动降级）"""

    def __init__(
        self,
        model_name: str = None,
        max_iterations: int = 5,
        temperature: float = 0.7,
        base_url: str = None,
    ):
        """
        初始化 Agent

        后端模式（LLM_BACKEND）：
        - "ollama" : 强制使用本地 Ollama（不降级，连接失败会抛错）
        - "cloud"  : 强制使用云端 API（不降级）
        - "auto"   : 优先本地 Ollama，连接失败自动降级到云端 API（默认推荐）

        Args:
            model_name: 模型名称（覆盖配置）
            max_iterations: 最大推理轮数
            temperature: 模型温度参数
            base_url: 服务地址（覆盖配置）
        """
        config = get_config()

        self.backend = config.LLM_BACKEND
        self.max_iterations = max_iterations
        self.llm = None

        # 1. 显式指定 cloud → 直接走云端
        if self.backend == "cloud":
            self._init_cloud(config, model_name, base_url, temperature)

        # 2. 显式指定 ollama → 走本地 Ollama（失败抛错）
        elif self.backend == "ollama":
            self._init_ollama(config, model_name, base_url, temperature)

        # 3. auto / 未知 → 优先本地 Ollama，失败自动降级到云端 API
        else:
            ollama_ok = self._check_ollama_available(
                base_url or config.OLLAMA_BASE_URL,
                model_name or config.OLLAMA_MODEL,
            )
            if ollama_ok:
                try:
                    self._init_ollama(config, model_name, base_url, temperature)
                except Exception as e:
                    logger.warning(f"Ollama 健康检查通过但初始化失败，降级到云端 API - {e}")
                    self._fallback_to_cloud(config, model_name, base_url, temperature)
            else:
                self._fallback_to_cloud(config, model_name, base_url, temperature)

        # 绑定工具
        self.tools = ALL_TOOLS
        self.tool_descriptions = get_tool_descriptions()

        # 初始化记忆
        self.memory = ConversationMemory(max_turns=10)

        logger.info(
            f"Larkwell Agent 已初始化 [backend={self.backend}] 模型: {self.model_name}"
        )

    # ---------- LLM 初始化辅助方法 ----------

    def _init_ollama(
        self,
        config,
        model_name: str | None,
        base_url: str | None,
        temperature: float,
    ) -> None:
        """初始化本地 Ollama LLM"""
        self.model_name = model_name or config.OLLAMA_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self.llm = ChatOllama(
            model=self.model_name,
            temperature=temperature,
            base_url=self.base_url,
        )
        self.backend = "ollama"
        logger.info(f"Larkwell Agent [Ollama] 模型: {self.model_name} @ {self.base_url}")

    def _init_cloud(
        self,
        config,
        model_name: str | None,
        base_url: str | None,
        temperature: float,
    ) -> None:
        """初始化云端 API LLM"""
        if not config.CLOUD_API_KEY:
            raise ValueError("LLM_BACKEND=cloud/auto 但未配置 CLOUD_API_KEY，无法降级")

        self.model_name = model_name or config.CLOUD_MODEL
        self.base_url = base_url or config.CLOUD_API_BASE
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=temperature,
            api_key=config.CLOUD_API_KEY,
            base_url=self.base_url,
        )
        self.backend = "cloud"
        logger.info(f"Larkwell Agent [Cloud] 模型: {self.model_name} @ {self.base_url}")

    def _fallback_to_cloud(
        self,
        config,
        model_name: str | None,
        base_url: str | None,
        temperature: float,
    ) -> None:
        """从 Ollama 降级到云端 API"""
        logger.warning("本地 Ollama 不可用，自动降级到云端 API（Cloud）")
        # 注意：降级时需用云端模型名，否则模型名不匹配会调用失败
        cloud_model = model_name if (model_name and model_name == config.CLOUD_MODEL) else config.CLOUD_MODEL
        self._init_cloud(config, cloud_model, base_url, temperature)

    @staticmethod
    def _check_ollama_available(base_url: str, model_name: str) -> bool:
        """
        检查本地 Ollama 服务是否可用

        策略：
        - 请求 /api/tags 检查服务在线
        - 检查目标模型是否已拉取（未拉取则视为不可用，触发降级）

        Args:
            base_url: Ollama 服务地址
            model_name: 需要的模型名

        Returns:
            True 表示可用；False 表示不可用（应降级到云端 API）
        """
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/api/tags",
                timeout=_OLLAMA_HEALTH_TIMEOUT,
            )
            if resp.status_code != 200:
                logger.warning(f"Ollama 健康检查失败：HTTP {resp.status_code}")
                return False

            tags = resp.json().get("models", [])
            if not tags:
                logger.warning("Ollama 在线但未拉取任何模型，触发降级")
                return False

            # 检查目标模型是否存在（Ollama 返回的 name 字段可能带 :tag）
            available = [m.get("name", "") for m in tags]
            if model_name not in available:
                logger.warning(
                    f"Ollama 未找到模型 '{model_name}'，可用模型: {available} → 触发降级"
                )
                return False

            logger.info(f"Ollama 健康检查通过，模型 '{model_name}' 可用")
            return True

        except requests.exceptions.ConnectionError:
            logger.warning("无法连接本地 Ollama 服务（连接被拒绝）→ 触发降级")
            return False
        except requests.exceptions.Timeout:
            logger.warning("Ollama 健康检查超时 → 触发降级")
            return False
        except Exception as e:
            logger.warning(f"Ollama 健康检查异常: {e} → 触发降级")
            return False

    def _build_system_prompt(self) -> str:
        """构建系统提示词（知雀雀设）"""
        return f"""你是「知雀」——一只代号「知雀」的数字灵雀，栖息在用户语雀知识库里，靠吃笔记为生！你的任务是基于检索到的笔记内容，帮用户解答问题。

【你的雀设】
1. 你是一只聪明但有点话痨的鸟，对用户语雀里的笔记了如指掌。
2. 你偶尔会"啄"一下用户模糊的问题（比如反问澄清），但啄完立刻乖乖回答。
3. 你喜欢用短句和感叹号，语气活泼像朋友聊天，别搞成冷冰冰的客服。
4. 你对自己的"记忆力"（向量检索能力）很自信，但如果没找到相关内容，你会诚实地说"这片知识林子里好像没有这个"，而不是瞎编。

【说话风格】
- 别用"您好，很高兴为您服务"，换成"嗨！刚在笔记林子里翻了一圈……"。
- 多用语气词：呀、哦、嘿、嗯哼。
- 把"检索到相关资料"说成"我在你的笔记里找到了这些干货"。
- 把"根据上下文理解"说成"让我啄一啄这里面的逻辑"。

【回复结构】
1. 开头：一句话回应情绪（比如"这问题有意思！"或"简单！我帮你捞出来了。"）。
2. 正文：基于检索到的 context 清晰作答。如果信息不足，直接说没找到，并建议用户补充笔记。
3. 引用来源：在末尾用 🪶 标记引用了哪篇笔记（如：🪶 来源：你写的《Transformer 详解》）。

【硬规则】
- 绝对不要编造不在检索结果中的细节。如果 context 为空，直接说"知雀暂时没在你的笔记里翻到答案，你是不是忘记同步啦？"，别强行回复。
- 如果用户问"你是谁"，回答："我是你的专属知雀，靠吃你的笔记为生！只要记在语雀里的，你问我准没错。"

【可用工具】
{self.tool_descriptions}

【工具选择优先级】（请严格遵守）
1. 用户问知识库内容 → 优先使用 knowledge_search
2. 用户要求同步语雀文档 → 使用 yuque_sync
3. 用户问实时信息（如今天新闻、最新价格）→ 使用 web_search
4. 用户要求读取本地文件 → 使用 read_file
5. 用户要求执行命令 → 使用 execute_shell
6. 用户要求查询知识库状态 → 使用 knowledge_status
7. 不需要工具 → 直接回复

【工具调用格式】
当需要调用工具时，仅输出下面这一个 JSON 代码块（不要在 JSON 块外加任何文字）：
```json
{{"tool": "工具名", "args": {{"参数名": "参数值"}}}}
```

不需要工具时，直接用知雀的语气和用户聊天回复。工具调用失败时，用知雀的口吻说明情况并提供替代方案（比如"哎呀，知识库这会儿连不上，等会儿再试哦"）。
"""

    def _extract_tool_call(self, text: str) -> Dict[str, Any] | None:
        """
        从 LLM 输出中提取工具调用 JSON

        Args:
            text: LLM 输出的文本

        Returns:
            工具调用字典或 None
        """
        json_match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        json_match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """
        执行工具调用

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果
        """
        tool = get_tool_by_name(tool_name)
        if not tool:
            return f"错误：工具 '{tool_name}' 不存在"

        try:
            result = tool.invoke(args)
            return str(result)
        except Exception as e:
            return f"错误：工具执行失败 - {str(e)}"

    def run(self, user_input: str) -> Dict[str, Any]:
        """
        同步执行 Agent（适用于简单场景）

        Args:
            user_input: 用户输入

        Returns:
            包含回复和工具调用记录的字典
        """
        self.memory.add_user_message(user_input)

        messages = [SystemMessage(content=self._build_system_prompt())]
        context = self.memory.get_context_messages()

        for msg in context:
            if msg["role"] == "system":
                messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        tool_calls_log = []

        for iteration in range(self.max_iterations):
            response = self.llm.invoke(messages)
            content = response.content.strip()

            tool_call = self._extract_tool_call(content)

            if tool_call:
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})

                logger.info(f"🔧 调用工具: {tool_name}({tool_args})")

                result = self._execute_tool(tool_name, tool_args)
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result[:200],
                    "timestamp": datetime.now().isoformat(),
                })

                messages.append(AIMessage(content=content))
                messages.append(HumanMessage(content=f"工具执行结果：\n{result}\n\n请根据结果回复用户。"))
            else:
                self.memory.add_assistant_message(content, tool_calls_log)

                return {
                    "response": content,
                    "tool_calls": tool_calls_log,
                    "iterations": iteration + 1,
                }

        fallback = "抱歉，我尝试了多次但未能完成任务。请尝试简化您的问题。"
        self.memory.add_assistant_message(fallback, tool_calls_log)

        return {
            "response": fallback,
            "tool_calls": tool_calls_log,
            "iterations": self.max_iterations,
        }

    async def run_stream(self, user_input: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步流式执行 Agent

        Args:
            user_input: 用户输入

        Yields:
            包含不同类型事件的字典
        """
        self.memory.add_user_message(user_input)

        messages = [SystemMessage(content=self._build_system_prompt())]
        context = self.memory.get_context_messages()

        for msg in context:
            if msg["role"] == "system":
                messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        tool_calls_log = []
        full_response = ""

        for iteration in range(self.max_iterations):
            yield {"type": "thinking", "content": f"正在思考... (第 {iteration + 1} 轮)"}

            response_text = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    response_text += chunk.content
                    if not self._extract_tool_call(response_text):
                        yield {"type": "token", "content": chunk.content}

            content = response_text.strip()

            tool_call = self._extract_tool_call(content)

            if tool_call:
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})

                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "args": tool_args,
                }

                logger.info(f"🔧 调用工具: {tool_name}({tool_args})")
                result = self._execute_tool(tool_name, tool_args)
                tool_calls_log.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": result[:200],
                    "timestamp": datetime.now().isoformat(),
                })

                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": result[:500],
                }

                messages.append(AIMessage(content=content))
                messages.append(HumanMessage(content=f"工具执行结果：\n{result}\n\n请根据结果回复用户。"))
            else:
                full_response = content
                self.memory.add_assistant_message(content, tool_calls_log)

                yield {
                    "type": "done",
                    "response": content,
                    "tool_calls": tool_calls_log,
                    "iterations": iteration + 1,
                }
                return

        fallback = "抱歉，我尝试了多次但未能完成任务。请尝试简化您的问题。"
        self.memory.add_assistant_message(fallback, tool_calls_log)

        yield {
            "type": "done",
            "response": fallback,
            "tool_calls": tool_calls_log,
            "iterations": self.max_iterations,
        }
