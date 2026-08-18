"""快速测试语雀 API 连接"""
import os, requests, time
from dotenv import load_dotenv
load_dotenv()

url = f'https://www.yuque.com/api/v2/repos/{os.getenv("YUQUE_LOGIN")}/{os.getenv("YUQUE_REPO")}/docs'
headers = {'X-Auth-Token': os.getenv('YUQUE_TOKEN'), 'User-Agent': 'Larkwell/1.0'}
resp = requests.get(url, headers=headers, params={'limit': 5})
print(f'Status: {resp.status_code}')
data = resp.json()
print(f'Total docs: {data["meta"]["total"]}')
print(f'First 5 titles:')
for d in data['data'][:5]:
    print(f'  - {d["title"]} (slug: {d["slug"]})')

# 测试单篇文档下载
slug = data['data'][0]['slug']
print(f'\n测试下载: {slug}')
detail_url = f'https://www.yuque.com/api/v2/repos/{os.getenv("YUQUE_LOGIN")}/{os.getenv("YUQUE_REPO")}/docs/{slug}'
resp2 = requests.get(detail_url, headers=headers)
print(f'Detail Status: {resp2.status_code}')
detail = resp2.json().get('data', {})
print(f'Title: {detail.get("title")}')
print(f'Body length: {len(detail.get("body", ""))}')
print('API 测试通过!')
