"""测试 SiliconFlow API"""
import requests

API_KEY = "sk-smcazoaveziknqjtprjhdgdirzzmzlprfdcencxhgrpiwlin"
BASE_URL = "https://api.siliconflow.cn/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 1. 列出模型
print("1. SiliconFlow 可用模型")
print("-" * 40)
resp = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10)
if resp.status_code == 200:
    models = [m.get("id", "") for m in resp.json().get("data", [])]
    print(f"✅ 认证成功! 共 {len(models)} 个模型")
    for m in models[:15]:
        print(f"  - {m}")
else:
    print(f"❌ {resp.status_code}: {resp.text[:200]}")

# 2. 对话测试
print("\n2. 对话测试 (Qwen/Qwen2.5-7B-Instruct)")
print("-" * 40)
chat_resp = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=headers,
    json={
        "model": "Qwen/Qwen2.5-7B-Instruct",
        "messages": [{"role": "user", "content": "你好，简单介绍一下自己"}],
        "max_tokens": 100,
    },
    timeout=30,
)
if chat_resp.status_code == 200:
    result = chat_resp.json()
    reply = result["choices"][0]["message"]["content"]
    usage = result.get("usage", {})
    print(f"✅ 对话成功!")
    print(f"回复: {reply}")
    print(f"Token: {usage}")
else:
    print(f"❌ {chat_resp.status_code}: {chat_resp.text[:300]}")

# 3. Embedding 测试
print("\n3. Embedding 测试 (BAAI/bge-m3)")
print("-" * 40)
embed_resp = requests.post(
    f"{BASE_URL}/embeddings",
    headers=headers,
    json={"model": "BAAI/bge-m3", "input": "测试文本"},
    timeout=15,
)
if embed_resp.status_code == 200:
    emb = embed_resp.json()["data"][0]["embedding"]
    print(f"✅ Embedding 成功! 维度: {len(emb)}")
else:
    print(f"❌ {embed_resp.status_code}: {embed_resp.text[:200]}")
