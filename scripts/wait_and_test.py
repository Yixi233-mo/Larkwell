"""等待限流冷却后测试 API"""
import time
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

WAIT_SECONDS = 300  # 5 分钟

print(f"等待 {WAIT_SECONDS}s 限流冷却...")
for i in range(WAIT_SECONDS, 0, -30):
    print(f"  倒计时 {i}s ...", flush=True)
    time.sleep(30)

print()
print("测试 API 连接...")
login = os.getenv("YUQUE_LOGIN")
repo = os.getenv("YUQUE_REPO")
token = os.getenv("YUQUE_TOKEN")

url = f"https://www.yuque.com/api/v2/repos/{login}/{repo}/docs"
headers = {"X-Auth-Token": token, "User-Agent": "Larkwell/1.0"}
resp = requests.get(url, headers=headers, params={"limit": 3})
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    total = data["meta"]["total"]
    print(f"Total docs: {total}")
    print("限流已解除，可以开始下载!")
    sys.exit(0)
elif resp.status_code == 429:
    print("仍在限流中，需要等待更长时间")
    sys.exit(1)
else:
    print(f"其他错误: {resp.text[:300]}")
    sys.exit(1)
