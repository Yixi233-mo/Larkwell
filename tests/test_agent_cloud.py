"""Agent 对话测试 - Cloud 模式"""
import sys
sys.path.insert(0, 'src')

from agent import Agent

print("=" * 60)
print("  Larkwell Agent 对话测试 [Cloud 模式]")
print("=" * 60)

agent = Agent()
print(f"\n后端: {agent.backend}")
print(f"模型: {agent.model_name}")
print()

queries = [
    "你好，介绍一下你自己",
    "什么是 RAG？",
]

for q in queries:
    print(f"👤 用户: {q}")
    result = agent.run(q)
    print(f"🤖 Larkwell: {result.get('response', result)}")
    print()
