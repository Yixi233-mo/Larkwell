"""Larkwell 模块验证脚本"""
import sys
sys.path.insert(0, 'src')

# 测试日志模块
from utils.logger import get_logger
logger = get_logger('test')
logger.info('Larkwell 日志模块测试通过')

# 测试配置模块
from utils.config import get_config
config = get_config()
print(f'配置加载成功: Collection={config.MILVUS_COLLECTION}')

# 测试清洗规则
from cleaning.rules import CLEANING_RULES
print(f'清洗规则数量: {len(CLEANING_RULES)}')

# 测试记忆模块
from memory import ConversationMemory
mem = ConversationMemory()
mem.add_user_message('Larkwell 测试')
print(f'记忆模块: 消息数={len(mem.messages)}')

# 测试工具模块
from tools import ALL_TOOLS
print(f'工具模块: 工具数量={len(ALL_TOOLS)}')

# 测试 Git 监听器
from indexing.git_watcher import GitWatcher
watcher = GitWatcher()
stats = watcher.get_stats()
print(f'Git监听器: 追踪文件数={stats["tracked_files"]}')

# 测试文档加载器
from indexing.document_loader import DocumentLoader
loader = DocumentLoader()
print('文档加载器初始化成功')

# 测试 RAG 引擎（仅测试初始化配置）
from rag import RAGEngine
print('RAG 引擎模块导入成功')

# 测试 Agent
from agent import Agent
print('Agent 模块导入成功')

print()
print('=' * 50)
print('  Larkwell 所有核心模块验证通过!')
print('=' * 50)
