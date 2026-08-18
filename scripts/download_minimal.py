"""快速下载少量语雀文档填充知识库（绕过限流）"""
import os, sys, json, time, hashlib, requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

YUQUE_TOKEN = os.getenv("YUQUE_TOKEN")
YUQUE_LOGIN = os.getenv("YUQUE_LOGIN")
YUQUE_REPO = os.getenv("YUQUE_REPO")
BASE_URL = "https://www.yuque.com/api/v2"
OUTPUT_DIR = Path("./docs/docs")

HEADERS = {"X-Auth-Token": YUQUE_TOKEN, "User-Agent": "Larkwell/1.0"}

def sanitize(name):
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name.strip()

def fetch_doc_list(limit=5):
    url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs"
    resp = requests.get(url, headers=HEADERS, params={"limit": limit})
    if resp.status_code != 200:
        print(f"获取文档列表失败: {resp.status_code}")
        return []
    return resp.json().get("data", [])

def fetch_doc_detail(slug):
    url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs/{slug}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print(f"获取详情失败: {resp.status_code}")
        return None
    return resp.json().get("data", {})

def main():
    print("获取语雀文档列表...")
    docs = fetch_doc_list(limit=5)
    print(f"获取到 {len(docs)} 篇文档")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    saved = []
    for doc in docs:
        slug = doc["slug"]
        title = doc["title"]
        print(f"下载: {title}", end=" ... ", flush=True)

        detail = fetch_doc_detail(slug)
        if detail:
            body = detail.get("body", "")
            body = body.replace(":::tips", ":::tip").replace(":::success", ":::tip")

            content = f"""---
title: "{title}"
date: "{detail.get('published_at', '')}"
---

{body}"""

            fname = sanitize(title) + ".md"
            fpath = OUTPUT_DIR / fname
            fpath.write_text(content, encoding="utf-8")
            print("OK")
            saved.append({"title": title, "file": fname})
        else:
            print("失败")

        time.sleep(2)

    print(f"\n下载完成: {len(saved)} 篇文档")

    # 生成侧边栏数据
    catalog = []
    for i, doc in enumerate(saved):
        catalog.append({
            "id": i + 1,
            "uuid": str(i + 1),
            "parent_uuid": "",
            "title": doc["title"],
            "type": "DOC",
            "slug": sanitize(doc["title"]),
        })

    cache = {"catalog": catalog}
    cache_file = Path("./elog.cache.json")
    cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"已生成 elog.cache.json ({len(catalog)} 条记录)")

    print("\n已下载文档列表:")
    for d in saved:
        print(f"  - {d['file']}")

if __name__ == "__main__":
    main()
