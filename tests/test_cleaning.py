"""Larkwell 端到端清洗测试"""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, 'src')

from utils.logger import get_logger
from utils.config import get_config

logger = get_logger('test_cleaning')

# 创建测试目录结构
test_dir = Path('tests') / 'sample_data'
test_dir.mkdir(exist_ok=True)

# 创建测试用的 Markdown 文件
sample_md = '''---
title: "Larkwell 测试文档"
date: "2026-08-18 15:00:00"
---

# Larkwell 知识库测试文档

## 1. 介绍

这是一个测试文档，用于验证 Larkwell 的清洗流程是否正常工作。

### 1.1 功能列表

- 语雀文档同步
- 智能清洗
- 向量索引
- AI 问答

## 2. 代码示例

```python
def hello():
    print("Hello, Larkwell!")
    return True
```

```javascript
const greet = (name) => {
    return `Hello, ${name}!`;
};
```

## 3. 表格测试

| 功能 | 状态 | 描述 |
|------|------|------|
| 语雀同步 | ✅ | 支持 Token 模式 |
| 文档清洗 | ✅ | 5 种清洗规则 |
| 向量索引 | ✅ | Milvus 增量更新 |

## 4. 图片测试

![测试图片](assets/test.png)

## 5. 总结

Larkwell 是一个强大的知识库工具。


'''

test_file = test_dir / 'test_document.md'
test_file.write_text(sample_md, encoding='utf-8')

print('=' * 50)
print('Larkwell 端到端清洗测试')
print('=' * 50)

# 测试清洗 Agent
from cleaning.agent import CleaningAgent

cleaning_agent = CleaningAgent()

# 创建输出目录
output_dir = Path('tests') / 'cleaned_data'
output_dir.mkdir(exist_ok=True)

# 清洗单个文件
result = cleaning_agent.clean_single_file(test_file, output_dir / 'test_document.md')

print(f'\n清洗结果: {json.dumps(result, indent=2, ensure_ascii=False, default=str)[:500]}')

# 检查输出
cleaned_file = output_dir / 'test_document.md'
if cleaned_file.exists():
    cleaned_content = cleaned_file.read_text(encoding='utf-8')
    print(f'\n清洗后内容预览:')
    print(cleaned_content[:500])

print('\n' + '=' * 50)
print('测试完成!')
print('=' * 50)
