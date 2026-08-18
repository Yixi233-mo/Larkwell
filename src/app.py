"""
FastAPI Web 服务模块
===================
提供 RESTful API 和 Web UI：
- POST /chat - 同步聊天接口
- POST /chat/stream - 异步流式聊天接口（SSE）
- GET /history - 获取对话历史
- DELETE /history - 清空对话历史
- POST /sync - 触发语雀同步
- GET /status - 获取系统状态
- GET / - Web UI 界面
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
import os

from agent import Agent
from utils.logger import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# ========== FastAPI 应用 ==========

app = FastAPI(
    title="Larkwell AI 助手 API",
    description="Larkwell - 基于语雀知识库的智能 AI 助手",
    version="1.0.0",
)

# 全局 Agent 实例（自动根据 LLM_BACKEND 选择 ollama/cloud）
config = get_config()
agent = Agent(max_iterations=5, temperature=0.7)

# ========== 请求/响应模型 ==========

class ChatRequest(BaseModel):
    message: str
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    response: str
    tool_calls: list
    iterations: int


class HistoryResponse(BaseModel):
    messages: list
    stats: dict


class SyncResponse(BaseModel):
    status: str
    message: str
    details: Optional[dict] = None


# ========== API 端点 ==========

@app.get("/", response_class=HTMLResponse)
async def get_web_ui():
    """返回 Web UI 界面"""
    try:
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
        index_path = os.path.join(static_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            return HTMLResponse(
                content="<h1>Larkwell AI 助手</h1><p>Web UI 未找到，请确保 static/index.html 存在</p>",
                status_code=404,
            )
    except Exception as e:
        logger.error(f"加载 Web UI 失败: {e}")
        return HTMLResponse(content=f"<h1>错误</h1><p>{str(e)}</p>", status_code=500)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    同步聊天接口

    Args:
        request: 包含 message 和 stream 参数

    Returns:
        ChatResponse: 包含回复、工具调用记录和迭代次数
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    try:
        result = agent.run(request.message)
        return ChatResponse(
            response=result["response"],
            tool_calls=result["tool_calls"],
            iterations=result["iterations"],
        )
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"Agent 执行失败: {str(e)}")


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    异步流式聊天接口（Server-Sent Events）

    Args:
        request: 包含 message 参数

    Returns:
        StreamingResponse: SSE 格式的流式响应
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    async def event_generator():
        try:
            async for event in agent.run_stream(request.message):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield f"data: {json.dumps({'type': 'end'})}\n\n"
        except Exception as e:
            logger.error(f"流式响应异常: {e}")
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/history", response_model=HistoryResponse)
async def get_history():
    """
    获取对话历史

    Returns:
        HistoryResponse: 包含消息列表和统计信息
    """
    return HistoryResponse(
        messages=agent.memory.get_history(),
        stats=agent.memory.get_stats(),
    )


@app.delete("/history")
async def clear_history():
    """
    清空对话历史

    Returns:
        成功消息
    """
    agent.memory.clear()
    return {"message": "对话历史已清空"}


@app.post("/sync", response_model=SyncResponse)
async def sync_yuque(background_tasks: BackgroundTasks):
    """
    触发语雀同步

    Args:
        background_tasks: 后台任务

    Returns:
        同步触发状态
    """
    try:
        from sync.elog_wrapper import run_sync
        result = run_sync(force=False)

        if result["status"] == "success":
            return SyncResponse(
                status="success",
                message="语雀同步成功",
                details={
                    "file_count": result.get("file_count", 0),
                    "output_path": result.get("output_path", ""),
                },
            )
        else:
            return SyncResponse(
                status="error",
                message=f"语雀同步失败: {result.get('message', '未知错误')}",
                details=result,
            )
    except Exception as e:
        logger.error(f"语雀同步异常: {e}")
        raise HTTPException(status_code=500, detail=f"语雀同步异常: {str(e)}")


@app.get("/status")
async def get_status():
    """
    获取系统状态

    Returns:
        系统状态信息
    """
    try:
        from rag import RAGEngine
        rag = RAGEngine()
        rag_stats = rag.get_stats()
        docs = rag.list_documents()
    except Exception as e:
        rag_stats = {"error": str(e)}
        docs = []

    return {
        "status": "ok",
        "version": "1.0.0",
        "backend": agent.backend,
        "model": agent.model_name,
        "tools": [t.name for t in agent.tools],
        "knowledge_base": {
            "collection": config.MILVUS_COLLECTION,
            "entity_count": rag_stats.get("entity_count", 0),
            "document_count": len(docs),
        },
        "memory": agent.memory.get_stats(),
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "model": agent.model_name,
        "tools": [t.name for t in agent.tools],
    }


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("Larkwell AI 助手服务启动")
    logger.info("=" * 60)
    logger.info(f"模型: {agent.model_name}")
    logger.info(f"工具: {[t.name for t in agent.tools]}")
    logger.info(f"知识库: {config.MILVUS_COLLECTION}")
    logger.info(f"地址: http://localhost:8000")
    logger.info(f"文档: http://localhost:8000/docs")
    logger.info("=" * 60)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
