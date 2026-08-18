"""检查语雀 API 限流头信息"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

login = os.getenv("YUQUE_LOGIN")
repo = os.getenv("YUQUE_REPO")
token = os.getenv("YUQUE_TOKEN")

url = f"https://www.yuque.com/api/v2/repos/{login}/{repo}/docs"
headers = {"X-Auth-Token": token, "User-Agent": "Larkwell/1.0"}

print("发送测试请求...")
resp = requests.get(url, headers=headers, params={"limit": 1})

print(f"\nStatus: {resp.status_code}")
print(f"\n所有响应头:")
for key, value in resp.headers.items():
    print(f"  {key}: {value}")

if resp.status_code == 429:
    print("\n--- 限流分析 ---")
    retry_after = resp.headers.get("Retry-After", "未提供")
    print(f"Retry-After: {retry_after}")

    # 检查常见的限流头
    rate_limit = resp.headers.get("X-RateLimit-Limit", "未提供")
    remaining = resp.headers.get("X-RateLimit-Remaining", "未提供")
    reset = resp.headers.get("X-RateLimit-Reset", "未提供")
    print(f"X-RateLimit-Limit: {rate_limit}")
    print(f"X-RateLimit-Remaining: {remaining}")
    print(f"X-RateLimit-Reset: {reset}")
