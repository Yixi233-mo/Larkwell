# Larkwell

**Larkwell** 是一个将语雀笔记自动转化为本地 AI 知识库的智能助手。

## 功能特性

- 📝 **语雀文档同步** - 自动从语雀知识库同步文档，支持图片下载和格式转换
- 🔍 **智能搜索** - 基于 VitePress 的本地搜索，快速定位文档内容
- 🤖 **AI 问答助手** - 集成 LangGraph Agent，支持多轮对话和知识库检索
- 📚 **分类展示** - 自动生成文档目录结构，支持层级导航
- ⚡ **本地优先** - 所有数据本地存储，隐私安全可控
- 🔄 **增量更新** - 支持文档增量同步，不重复处理

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 文档同步 | Elog (Node.js) | 语雀官方生态，支持多知识库、图片下载 |
| 前端文档站 | VitePress | 基于 Vue 的静态文档生成器 |
| 后端服务 | FastAPI | 高性能 Python Web 框架 |
| AI 框架 | LangGraph + LangChain | Agent 编排和 RAG 流程 |
| 向量数据库 | Milvus | 高性能向量检索 |
| 大语言模型 | Ollama + qwen3:8b | 本地部署的大模型 |
| Embedding | BAAI/bge-base-zh-v1.5 | 中文语义向量模型 |

## 快速开始

### 环境要求

- Node.js >= 18
- Python >= 3.10
- Milvus 2.3+
- Ollama (本地部署 qwen3:8b)

### 安装步骤

```bash
# 1. 克隆项目
git clone <repository-url>
cd larkwell

# 2. 安装 Node.js 依赖
npm install

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入您的配置

# 5. 从语雀同步文档
npm run elog:sync

# 6. 启动服务
# Windows:
scripts\start.bat
# 或 PowerShell:
scripts\start.ps1
```

### 手动启动

```bash
# 终端 1: 启动文档站点
npm run docs:dev

# 终端 2: 启动 AI 助手
cd src
python app.py
```

## 项目结构

```
larkwell/
├── docs/                    # VitePress 文档
│   ├── .vitepress/          # VitePress 配置
│   ├── docs/                # 同步的语雀文档
│   └── images/              # 同步的图片
├── src/                     # Python 源代码
│   ├── api/                 # API 路由
│   ├── cleaning/            # 文档清洗
│   │   └── rules/           # 清洗规则
│   ├── indexing/            # 索引管理
│   ├── sync/                # 语雀同步
│   ├── utils/               # 工具模块
│   ├── agent.py             # Agent 核心
│   ├── app.py               # FastAPI 入口
│   ├── memory.py            # 对话记忆
│   ├── rag.py               # RAG 引擎
│   └── tools.py             # 工具定义
├── repos/                   # 数据仓库
│   ├── raw/                 # 原始数据
│   └── clean/               # 清洗后数据
├── static/                  # 静态资源
│   └── index.html           # Web UI
├── scripts/                 # 启动脚本
├── config/                  # 配置文件
├── .env                     # 环境变量
├── elog.config.js           # Elog 配置
└── package.json             # Node.js 配置
```

## API 接口

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | Web UI |
| `/chat` | POST | 同步聊天 |
| `/chat/stream` | POST | 流式聊天 (SSE) |
| `/history` | GET | 获取对话历史 |
| `/history` | DELETE | 清空对话历史 |
| `/sync` | POST | 触发语雀同步 |
| `/status` | GET | 系统状态 |
| `/health` | GET | 健康检查 |

## 使用示例

### Web UI

打开浏览器访问 `http://localhost:8000`，即可使用 Larkwell AI 助手。

### API 调用

```bash
# 同步语雀文档
curl -X POST http://localhost:8000/sync

# 查询知识库
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "知识库中有什么内容？"}'

# 流式对话
curl -N -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "介绍一下 RAG"}'
```

## 配置说明

### 必须配置

在 `.env` 文件中配置以下选项：

```env
# 语雀 Token
YUQUE_TOKEN="your-token"
YUQUE_LOGIN="your-login"
YUQUE_REPO="your-repo"

# Milvus 连接
MILVUS_HOST="your-milvus-host"
MILVUS_PORT="19530"

# Ollama 连接
OLLAMA_BASE_URL="http://localhost:11434"
OLLAMA_MODEL="qwen3:8b"
```

### 可选配置

```env
# Embedding 模型
EMBEDDING_MODEL="BAAI/bge-base-zh-v1.5"
EMBEDDING_DIM=768

# 文本切分
CHUNK_SIZE=512
CHUNK_OVERLAP=64

# 检索参数
TOP_K=5
SIMILARITY_THRESHOLD=0.5

# 日志
LOG_LEVEL="INFO"
```

## 开发指南

### 添加新的清洗规则

在 `src/cleaning/rules/` 下创建新文件：

```python
from typing import Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

def apply(content: str, base_dir: str = '') -> Tuple[str, dict]:
    # 实现清洗逻辑
    return content, {"processed": 0}
```

然后在 `src/cleaning/rules/__init__.py` 中注册。

### 添加新的工具

在 `src/tools.py` 中添加：

```python
from langchain_core.tools import tool

@tool("new_tool")
def new_tool(param: str) -> str:
    """工具描述"""
    return "result"
```

然后将工具添加到 `ALL_TOOLS` 列表。

## 常见问题

### Q: 如何重新同步语雀文档？
A: 执行 `npm run elog:sync` 或调用 `POST /sync` 接口。

### Q: 如何清空知识库？
A: 在 `src/rag.py` 中调用 `rag.clear()` 方法。

### Q: Milvus 连接失败怎么办？
A: 检查 `.env` 中的 `MILVUS_HOST` 和 `MILVUS_PORT` 配置，确保 Milvus 服务正在运行。

## 许可证

MIT License © 2026 Larkwell Team
