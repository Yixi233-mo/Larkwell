"""
Larkwell 语雀文档下载脚本 v2
限流解决措施：
1. 指数退避重试（429 时等待 60s → 120s → 180s）
2. 断点续传（已下载文档跳过）
3. 自适应延迟（正常 2s，遇到 429 自动加大）
4. 分批下载（每 20 篇暂停 10s）
"""
import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

YUQUE_TOKEN = os.getenv("YUQUE_TOKEN")
YUQUE_LOGIN = os.getenv("YUQUE_LOGIN")
YUQUE_REPO = os.getenv("YUQUE_REPO")

BASE_URL = "https://www.yuque.com/api/v2"
OUTPUT_DIR = Path("./docs/docs")
IMAGE_DIR = Path("./docs/images")
CACHE_FILE = Path("./elog.cache.json")

HEADERS = {
    "X-Auth-Token": YUQUE_TOKEN,
    "User-Agent": "Larkwell/1.0",
}

# 限流参数
BASE_DELAY = 2.0          # 正常请求间隔
BATCH_SIZE = 20           # 每批数量
BATCH_PAUSE = 10          # 批次间暂停
MAX_RETRIES = 5           # 最大重试次数
RETRY_BASE_WAIT = 60      # 429 初始等待秒数


def request_with_retry(url, params=None):
    """带指数退避的请求"""
    for attempt in range(MAX_RETRIES):
        resp = requests.get(url, headers=HEADERS, params=params)

        if resp.status_code == 200:
            return resp

        if resp.status_code == 429:
            wait = RETRY_BASE_WAIT * (attempt + 1)
            print(f"\n  限流(429)，等待 {wait}s 后重试 ({attempt+1}/{MAX_RETRIES})...")
            time.sleep(wait)
            continue

        if resp.status_code == 401:
            print(f"\n  认证失败(401)，Token 可能无效")
            sys.exit(1)

        # 其他错误
        print(f"\n  HTTP {resp.status_code}: {resp.text[:200]}")
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_BASE_WAIT)
            continue

    raise Exception(f"请求失败，超过最大重试次数: {url}")


def get_doc_list() -> list:
    """获取文档列表"""
    url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs"
    docs = []
    offset = 0
    limit = 100

    while True:
        params = {"offset": offset, "limit": limit}
        resp = request_with_retry(url, params)
        data = resp.json()
        page_docs = data.get("data", [])
        if not page_docs:
            break
        docs.extend(page_docs)
        meta = data.get("meta", {})
        total = meta.get("total", 0)
        print(f"  获取文档列表: {len(docs)}/{total}")
        if len(docs) >= total:
            break
        offset += limit
        time.sleep(BASE_DELAY)

    return docs


def get_doc_detail(slug: str) -> dict:
    """获取文档详情"""
    url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs/{slug}"
    resp = request_with_retry(url)
    return resp.json().get("data", {})


def sanitize_filename(name: str) -> str:
    """清理文件名"""
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name.strip()


def download_images(content: str, doc_name: str) -> str:
    """下载文档中的图片到本地"""
    import re
    pattern = r'!\[([^\]]*)\]\((https?://[^)]+)\)'
    matches = re.findall(pattern, content)

    for alt, url in matches:
        if 'cdn.nlark.com' in url or 'yuque' in url:
            try:
                img_resp = requests.get(url, timeout=30)
                if img_resp.status_code == 200:
                    ext = url.split('.')[-1].split('?')[0] if '.' in url.split('/')[-1] else 'png'
                    if ext not in ['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp']:
                        ext = 'png'
                    img_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                    img_name = f"{img_hash}.{ext}"

                    img_dir = IMAGE_DIR / doc_name
                    img_dir.mkdir(parents=True, exist_ok=True)
                    img_path = img_dir / img_name
                    img_path.write_bytes(img_resp.content)

                    local_path = f"../images/{doc_name}/{img_name}"
                    content = content.replace(url, local_path)
                    time.sleep(0.5)
            except Exception as e:
                print(f"  图片下载失败: {url[:60]}... - {e}")

    return content


def format_markdown(content: str) -> str:
    """格式化 Markdown"""
    if not content:
        return content
    content = content.replace(':::tips', ':::tip')
    content = content.replace(':::success', ':::tip')
    return content


def main():
    print("=" * 60)
    print("  Larkwell 语雀文档下载 v2 (限流保护)")
    print("=" * 60)
    print()

    if not all([YUQUE_TOKEN, YUQUE_LOGIN, YUQUE_REPO]):
        print("错误: 请在 .env 中配置语雀参数")
        sys.exit(1)

    print(f"知识库: {YUQUE_LOGIN}/{YUQUE_REPO}")
    print(f"输出到: {OUTPUT_DIR}")
    print(f"限流策略: 间隔{BASE_DELAY}s, 每{BATCH_SIZE}篇暂停{BATCH_PAUSE}s")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 加载缓存（断点续传）
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        print(f"缓存: 已有 {len(cache)} 篇文档，将跳过已下载")

    # 获取文档列表
    print("\n正在获取文档列表...")
    docs = get_doc_list()
    print(f"文档总数: {len(docs)}")

    # 过滤需要下载的文档
    to_download = []
    for doc in docs:
        slug = doc.get("slug", "")
        cache_key = slug
        if cache_key in cache:
            cached = cache[cache_key]
            if cached.get("content_updated_at") == doc.get("content_updated_at"):
                continue
        to_download.append(doc)

    print(f"需要下载: {len(to_download)} 篇 (跳过 {len(docs) - len(to_download)} 篇已缓存)")
    print()

    if not to_download:
        print("所有文档已下载完成!")
        return

    # 分批下载
    success = 0
    failed = 0
    total = len(to_download)

    for i, doc in enumerate(to_download, 1):
        slug = doc.get("slug", "")
        title = doc.get("title", f"untitled_{i}")
        title_clean = sanitize_filename(title)

        print(f"[{i}/{total}] {title}", end=" ... ", flush=True)

        try:
            detail = get_doc_detail(slug)
            body = detail.get("body", "")
            body = format_markdown(body)
            body = download_images(body, title_clean)

            frontmatter = f"""---
title: "{title}"
date: "{detail.get("published_at", "")}"
---

"""
            content = frontmatter + body

            out_file = OUTPUT_DIR / f"{title_clean}.md"
            out_file.write_text(content, encoding='utf-8')

            cache[slug] = {
                "title": title,
                "slug": slug,
                "content_updated_at": doc.get("content_updated_at"),
                "file": str(out_file),
            }

            # 每 10 篇保存一次缓存
            if i % 10 == 0:
                CACHE_FILE.write_text(
                    json.dumps(cache, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )

            print("OK")
            success += 1

        except Exception as e:
            print(f"失败: {e}")
            failed += 1

        # 限流保护
        if i < total:
            time.sleep(BASE_DELAY)

        # 批次暂停
        if i % BATCH_SIZE == 0 and i < total:
            print(f"  --- 批次暂停 {BATCH_PAUSE}s ---")
            time.sleep(BATCH_PAUSE)

    # 保存缓存
    CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    print()
    print("=" * 60)
    print(f"  下载完成: 成功 {success}, 失败 {failed}, 总计 {total}")
    print(f"  文档目录: {OUTPUT_DIR}")
    print(f"  图片目录: {IMAGE_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
