"""
测试 Ollama Embedding 能力
- 检查是否支持 qwen3:8b 做 embedding
- 如果不支持，下载轻量 Embedding 模型
"""
import requests
import time

OLLAMA_URL = "http://localhost:11434"

def test_embedding(model: str, text: str):
    """测试模型 embedding 能力"""
    url = f"{OLLAMA_URL}/api/embeddings"
    payload = {"model": model, "input": text}
    
    try:
        resp = requests.post(url, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            emb = data.get("embedding", [])
            if emb and len(emb) > 0:
                return True, len(emb), emb[:3]
            else:
                return False, 0, "空 embedding"
        else:
            return False, 0, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, 0, str(e)

# 测试 qwen3:8b
print("测试 qwen3:8b embeddings...")
ok, dim, preview = test_embedding("qwen3:8b", "你好世界")
if ok:
    print(f"  ✅ 成功! 维度={dim}")
    print(f"     前3值: {preview}")
else:
    print(f"  ❌ 不支持: {preview}")

# 尝试下载轻量 Embedding 模型
print("\n检查可用 Embedding 模型...")

embedding_models = [
    ("bge-m3", "多语言支持，中文优化"),
    ("nomic-embed-text", "英文优秀，轻量"),
    ("shaw/dmeta-embedding-zh", "中文专用"),
]

for model, desc in embedding_models:
    print(f"\n尝试 {model} ({desc})...")
    ok, dim, _ = test_embedding(model, "测试文本")
    if ok:
        print(f"  ✅ {model} 可用! 维度={dim}")
        break
    else:
        print(f"  ❌ {model} 不可用 (需要下载)")
        print(f"     下载命令: ollama pull {model}")

# 列出当前所有模型
print("\n当前 Ollama 模型列表:")
resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
if resp.status_code == 200:
    for m in resp.json().get("models", []):
        print(f"  - {m['name']}")
