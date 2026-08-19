---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "Larkwell"
  text: "智能知识库与 AI 助手"
  tagline: 语雀文档同步 · 智能检索 · AI 问答
  actions:
    - theme: brand
      text: 📚 进入知识库
      link: /docs/

features:
  - icon: 📝
    title: 语雀文档同步
    details: 自动从语雀知识库同步文档，支持图片下载和格式转换
  - icon: 🔍
    title: 智能搜索
    details: 基于 VitePress 的本地搜索，快速定位文档内容
  - icon: 🤖
    title: AI 问答助手
    details: 集成 LangGraph Agent，支持多轮对话和知识库检索
  - icon: 📚
    title: 分类展示
    details: 自动生成文档目录结构，支持层级导航
  - icon: ⚡
    title: 本地优先
    details: 所有数据本地存储，隐私安全可控
  - icon: 🔄
    title: 增量更新
    details: 支持文档增量同步，不重复处理

---

## 关于 Larkwell

**Larkwell** 是一个将语雀笔记自动转化为本地 AI 知识库的智能助手。

### 核心流程

1. **语雀云端笔记** → Elog 自动拉取
2. **Markdown 清洗** → 智能修复格式和图片
3. **向量化存储** → Milvus 向量库支持语义检索
4. **AI 智能问答** → LangGraph Agent 多轮对话

### 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 从语雀同步文档
npm run elog:sync

# 3. 启动文档站点
npm run docs:dev

# 4. 启动 AI 助手
python src/app.py
```
