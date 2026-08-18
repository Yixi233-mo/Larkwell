"""验证 Agent 双模式配置"""
import sys
sys.path.insert(0, 'src')

from utils.config import get_config
config = get_config()

print("=" * 50)
print("  Larkwell 双模式配置验证")
print("=" * 50)

print(f"\n当前后端: {config.LLM_BACKEND}")
print(f"\n[Ollama 本地模式]")
print(f"  地址: {config.OLLAMA_BASE_URL}")
print(f"  对话模型: {config.OLLAMA_MODEL}")
print(f"  Embedding: {config.OLLAMA_EMBED_MODEL}")

print(f"\n[Cloud 公开模式]")
print(f"  API: {config.CLOUD_API_BASE}")
print(f"  对话模型: {config.CLOUD_MODEL}")
print(f"  Embedding: {config.CLOUD_EMBED_MODEL}")
print(f"  API Key: {'已配置' if config.CLOUD_API_KEY else '未配置（需要填写）'}")

# 测试 Agent 初始化
print(f"\n[Agent 初始化测试]")
try:
    from agent import Agent
    agent = Agent()
    print(f"  ✅ Agent 初始化成功")
    print(f"  后端: {agent.backend}")
    print(f"  模型: {agent.model_name}")
except Exception as e:
    print(f"  ❌ 失败: {e}")

print(f"\n切换方式:")
print(f"  本地模式: .env 中设 LLM_BACKEND=ollama")
print(f"  公开模式: .env 中设 LLM_BACKEND=cloud + CLOUD_API_KEY=your_key")
