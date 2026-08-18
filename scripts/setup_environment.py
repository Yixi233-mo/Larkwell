"""
下载 Embedding 模型 + 验证 Ollama
一步到位
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("  Larkwell 环境准备")
print("=" * 60)
print()

# ============ 1. 下载 Embedding 模型 ============
print("[1/3] 下载 Embedding 模型 (BAAI/bge-base-zh-v1.5)")
print("-" * 40)

os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
print(f"  镜像源: {os.environ['HF_ENDPOINT']}")

try:
    from sentence_transformers import SentenceTransformer
    
    print("  正在加载/下载模型...")
    start = time.time()
    
    model = SentenceTransformer("BAAI/bge-base-zh-v1.5")
    
    elapsed = time.time() - start
    print(f"  ✅ 模型加载完成 ({elapsed:.1f}s)")
    
    # 测试编码
    test_texts = ["Larkwell 是一个智能知识库助手", "图神经网络学习"]
    embeddings = model.encode(test_texts)
    print(f"  ✅ 编码测试通过: {len(embeddings)} 维向量")
    
    # 测试相似度
    from sklearn.metrics.pairwise import cosine_similarity
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    print(f"  ✅ 相似度计算: {sim:.4f}")
    
except Exception as e:
    print(f"  ❌ 模型加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# ============ 2. 验证 Ollama ============
print("[2/3] 验证 Ollama 连接")
print("-" * 40)

ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "qwen3:8b")

print(f"  地址: {ollama_url}")
print(f"  模型: {ollama_model}")

try:
    # 测试连接
    resp = requests.get(f"{ollama_url}/api/tags", timeout=5)
    if resp.status_code == 200:
        models = resp.json().get("models", [])
        print(f"  ✅ Ollama 连接成功")
        print(f"  可用模型: {[m['name'] for m in models]}")
        
        # 检查目标模型是否存在
        model_exists = any(ollama_model in m["name"] for m in models)
        if not model_exists:
            print(f"  ⚠️ 模型 {ollama_model} 未找到")
            print(f"     请执行: ollama pull {ollama_model}")
        else:
            print(f"  ✅ 模型 {ollama_model} 已就绪")
    
    # 测试对话
    print("  测试对话...")
    chat_resp = requests.post(
        f"{ollama_url}/api/chat",
        json={
            "model": ollama_model,
            "messages": [{"role": "user", "content": "你好，简单介绍一下自己"}],
            "stream": False,
        },
        timeout=30,
    )
    
    if chat_resp.status_code == 200:
        result = chat_resp.json()
        reply = result.get("message", {}).get("content", "")
        print(f"  ✅ 对话测试通过")
        print(f"     回复: {reply[:80]}...")
    else:
        print(f"  ❌ 对话失败: {chat_resp.text[:200]}")

except requests.exceptions.ConnectionError:
    print(f"  ❌ Ollama 未启动")
    print(f"     请执行: ollama serve")
except Exception as e:
    print(f"  ❌ Ollama 错误: {e}")

print()

# ============ 3. RAG 集成测试 ============
print("[3/3] RAG 集成测试")
print("-" * 40)

try:
    sys.path.insert(0, "src")
    from rag import RAGEngine
    
    print("  连接 Milvus...")
    rag = RAGEngine()
    
    # 导入测试数据
    test_docs = [
        "Larkwell 是一个将语雀笔记转化为 AI 知识库的智能助手。",
        "RAG 检索增强生成结合了信息检索与文本生成。",
        "图神经网络是处理图结构数据的深度学习模型。",
    ]
    
    print("  导入测试文档...")
    for i, text in enumerate(test_docs):
        result = rag.upsert_document(
            text=text,
            source="test",
            doc_id=f"test_{i}",
        )
        print(f"    文档 {i+1}: {result['inserted']} chunks")
    
    # 语义检索
    print("  语义检索测试...")
    query = "什么是 Larkwell"
    results = rag.search(query, top_k=3)
    
    print(f"    查询: {query}")
    print(f"    结果数: {len(results)}")
    for r in results:
        print(f"      - 相似度: {r.score:.4f}, 内容: {r.text[:40]}...")
    
    # 清理
    for i in range(len(test_docs)):
        rag.delete_document(f"test_{i}")
    
    print("  ✅ RAG 集成测试通过")
    
except Exception as e:
    print(f"  ❌ RAG 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("  环境准备完成!")
print("=" * 60)
