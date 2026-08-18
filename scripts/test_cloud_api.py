"""测试 Cloud API Key"""
import requests
import json

API_KEY = "sk-WFEkaBGEB7oiTHp1JSGdvMqXFuZFvsJrB2ELWYXBgev7DfVRiclIk6Qw6bNEFQnI"

# 常见的 OpenAI 兼容 API 提供商
providers = [
    ("SiliconFlow", "https://api.siliconflow.cn/v1/models"),
    ("OpenAI", "https://api.openai.com/v1/models"),
    ("DeepSeek", "https://api.deepseek.com/v1/models"),
    ("Moonshot", "https://api.moonshot.cn/v1/models"),
    ("Zhipu", "https://open.bigmodel.cn/api/paas/v4/models"),
]

headers = {"Authorization": f"Bearer {API_KEY}"}

for name, url in providers:
    print(f"测试 {name}: {url}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("id", "") for m in data.get("data", [])]
            print(f"  ✅ 认证成功! 可用模型数: {len(models)}")
            if models:
                print(f"  前5个模型: {models[:5]}")
            print(f"  → 这是 {name} 的 API Key")
            break
        elif resp.status_code == 401:
            print(f"  ❌ 认证失败 (401)")
        else:
            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ❌ 连接失败: {e}")
    print()

# 如果 SiliconFlow 可用，测试对话
print("\n--- 对话测试 ---")
chat_url = "https://api.siliconflow.cn/v1/chat/completions"
payload = {
    "model": "Qwen/Qwen2.5-7B-Instruct",
    "messages": [{"role": "user", "content": "你好，简单介绍一下自己"}],
    "max_tokens": 100,
}
try:
    resp = requests.post(chat_url, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }, json=payload, timeout=15)
    if resp.status_code == 200:
        result = resp.json()
        reply = result["choices"][0]["message"]["content"]
        print(f"✅ 对话成功!")
        print(f"回复: {reply[:100]}")
    else:
        print(f"❌ 对话失败: {resp.status_code} - {resp.text[:200]}")
except Exception as e:
    print(f"❌ 请求异常: {e}")

# 测试 Embedding
print("\n--- Embedding 测试 ---")
embed_url = "https://api.siliconflow.cn/v1/embeddings"
payload = {
    "model": "BAAI/bge-m3",
    "input": "测试文本",
}
try:
    resp = requests.post(embed_url, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }, json=payload, timeout=15)
    if resp.status_code == 200:
        result = resp.json()
        dim = len(result["data"][0]["embedding"])
        print(f"✅ Embedding 成功! 维度={dim}")
    else:
        print(f"❌ Embedding 失败: {resp.status_code} - {resp.text[:200]}")
except Exception as e:
    print(f"❌ 请求异常: {e}")
