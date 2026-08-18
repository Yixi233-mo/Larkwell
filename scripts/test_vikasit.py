"""测试 Vikasit API - 使用 vikasit-nova 模型"""
import requests

API_KEY = "sk-WFEkaBGEB7oiTHp1JSGdvMqXFuZFvsJrB2ELWYXBgev7DfVRiclIk6Qw6bNEFQnI"
BASE_URL = "https://api.vikasit.ai/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# 1. 对话测试 - vikasit-nova
print("1. Vikasit 对话测试 (vikasit-nova)")
print("-" * 40)
resp = requests.post(
    f"{BASE_URL}/chat/completions",
    headers=headers,
    json={
        "model": "vikasit-nova",
        "messages": [{"role": "user", "content": "Hello!"}],
    },
    timeout=30,
)

if resp.status_code == 200:
    result = resp.json()
    reply = result["choices"][0]["message"]["content"]
    model_used = result.get("model", "unknown")
    usage = result.get("usage", {})
    print(f"✅ 对话成功! 模型: {model_used}")
    print(f"回复: {reply}")
    print(f"Token 用量: {usage}")
else:
    print(f"❌ 失败 {resp.status_code}: {resp.text[:300]}")

# 2. 列出模型
print("\n2. 可用模型列表")
print("-" * 40)
resp2 = requests.get(f"{BASE_URL}/models", headers=headers, timeout=10)
if resp2.status_code == 200:
    models = [m.get("id", "") for m in resp2.json().get("data", [])]
    print(f"✅ 共 {len(models)} 个模型:")
    for m in models:
        print(f"  - {m}")
else:
    print(f"❌ {resp2.status_code}: {resp2.text[:200]}")

# 3. Embedding 测试
print("\n3. Embedding 测试")
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
    # 尝试其他 embedding 模型名
    for emb_model in ["vikasit-embedding", "text-embedding-3-small", "text-embedding-ada-002"]:
        r = requests.post(
            f"{BASE_URL}/embeddings",
            headers=headers,
            json={"model": emb_model, "input": "测试"},
            timeout=10,
        )
        if r.status_code == 200:
            dim = len(r.json()["data"][0]["embedding"])
            print(f"✅ {emb_model} 成功! 维度: {dim}")
            break
    else:
        print(f"❌ Embedding 不可用: {embed_resp.text[:200]}")
