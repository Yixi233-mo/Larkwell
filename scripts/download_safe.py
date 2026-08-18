"""
等待限流冷却后启动下载（10分钟冷却 + 5秒间隔）
"""
import time
import os
import sys
import json
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

# 更保守的限流参数
BASE_DELAY = 5.0          # 每篇间隔 5 秒
BATCH_SIZE = 10           # 每 10 篇暂停
BATCH_PAUSE = 30          # 批次间暂停 30 秒
COOLDOWN = 600            # 先冷却 10 分钟


def request_with_retry(url, params=None):
    """带指数退避的请求"""
    for attempt in range(10):
        resp = requests.get(url, headers=HEADERS, params=params)

        if resp.status_code == 200:
            return resp

        if resp.status_code == 429:
            wait = 120 * (attempt + 1)
            print(f"\n  限流(429)，等待 {wait}s 后重试 ({attempt+1}/10)...", flush=True)
            time.sleep(wait)
            continue

        if resp.status_code == 401:
            print(f"\n  认证失败(401)，Token 可能无效", flush=True)
            sys.exit(1)

        print(f"\n  HTTP {resp.status_code}: {resp.text[:200]}", flush=True)
        if attempt < 9:
            time.sleep(60)
            continue

    raise Exception(f"请求失败，超过最大重试次数: {url}")


def get_doc_list():
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
        print(f"  获取文档列表: {len(docs)}/{total}", flush=True)
        if len(docs) >= total:
            break
        offset += limit
        time.sleep(BASE_DELAY)

    return docs


def get_doc_detail(slug):
    """获取文档详情"""
    url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs/{slug}"
    resp = request_with_retry(url)
    return resp.json().get("data", {})


def sanitize_filename(name):
    """清理文件名"""
    for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
        name = name.replace(ch, '_')
    return name.strip()


def download_images(content, doc_name):
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
                    time.sleep(1)
            except Exception as e:
                print(f"  图片下载失败: {url[:60]}... - {e}", flush=True)

    return content


def format_markdown(content):
    """格式化 Markdown"""
    if not content:
        return content
    content = content.replace(':::tips', ':::tip')
    content = content.replace(':::success', ':::tip')
    return content


def main():
    print("=" * 60, flush=True)
    print("  Larkwell 语雀文档下载 (保守限流模式)", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    if not all([YUQUE_TOKEN, YUQUE_LOGIN, YUQUE_REPO]):
        print("错误: 请在 .env 中配置语雀参数", flush=True)
        sys.exit(1)

    # 第一阶段：限流冷却
    print(f"阶段 1: 限流冷却 {COOLDOWN}s ({COOLDOWN//60} 分钟)...", flush=True)
    for i in range(COOLDOWN, 0, -60):
        print(f"  倒计时 {i}s ...", flush=True)
        time.sleep(60)
    print("冷却完成!", flush=True)

    # 测试 API
    print("\n测试 API 连接...", flush=True)
    test_url = f"{BASE_URL}/repos/{YUQUE_LOGIN}/{YUQUE_REPO}/docs"
    test_resp = requests.get(test_url, headers=HEADERS, params={"limit": 1})

    if test_resp.status_code == 429:
        print("仍在限流中! 再等 10 分钟...", flush=True)
        for i in range(600, 0, -60):
            print(f"  倒计时 {i}s ...", flush=True)
            time.sleep(60)
        # 再试一次
        test_resp = requests.get(test_url, headers=HEADERS, params={"limit": 1})
        if test_resp.status_code == 429:
            print("限流未解除，请稍后再试", flush=True)
            sys.exit(1)

    if test_resp.status_code != 200:
        print(f"API 错误: {test_resp.status_code}", flush=True)
        sys.exit(1)

    print(f"API 连接正常! Status: {test_resp.status_code}", flush=True)

    # 第二阶段：下载文档
    print(f"\n阶段 2: 下载文档 (间隔 {BASE_DELAY}s, 每 {BATCH_SIZE} 篇暂停 {BATCH_PAUSE}s)", flush=True)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    # 加载缓存
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        print(f"缓存: 已有 {len(cache)} 篇文档", flush=True)

    # 获取文档列表
    print("\n正在获取文档列表...", flush=True)
    docs = get_doc_list()
    print(f"文档总数: {len(docs)}", flush=True)

    # 过滤已缓存
    to_download = []
    for doc in docs:
        slug = doc.get("slug", "")
        if slug in cache:
            cached = cache[slug]
            if cached.get("content_updated_at") == doc.get("content_updated_at"):
                continue
        to_download.append(doc)

    print(f"需要下载: {len(to_download)} 篇 (跳过 {len(docs) - len(to_download)} 篇已缓存)", flush=True)

    if not to_download:
        print("所有文档已下载完成!", flush=True)
        return

    # 下载
    success = 0
    failed = 0
    total = len(to_download)

    for i, doc in enumerate(to_download, 1):
        slug = doc.get("slug", "")
        title = doc.get("title", f"untitled_{i}")
        title_clean = sanitize_filename(title)

        print(f"[{i}/{total}] {title} ... ", end="", flush=True)

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

            if i % 5 == 0:
                CACHE_FILE.write_text(
                    json.dumps(cache, indent=2, ensure_ascii=False),
                    encoding='utf-8'
                )

            print("OK", flush=True)
            success += 1

        except Exception as e:
            print(f"失败: {e}", flush=True)
            failed += 1

        if i < total:
            time.sleep(BASE_DELAY)

        if i % BATCH_SIZE == 0 and i < total:
            print(f"  --- 批次暂停 {BATCH_PAUSE}s ---", flush=True)
            time.sleep(BATCH_PAUSE)

    CACHE_FILE.write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    print(flush=True)
    print("=" * 60, flush=True)
    print(f"  下载完成: 成功 {success}, 失败 {failed}, 总计 {total}", flush=True)
    print(f"  文档目录: {OUTPUT_DIR}", flush=True)
    print(f"  图片目录: {IMAGE_DIR}", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
