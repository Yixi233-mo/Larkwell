---
title: 知识库
---

<script setup>
// 仅本地开发环境显示 AI 问答入口，线上构建时 isDev=false 自动移除
const isDev = import.meta.env.MODE === 'development'
</script>

# Larkwell 知识库

欢迎来到 Larkwell 知识库——这里存放着我从语雀同步过来的所有技术笔记，经过清洗、归类和索引，形成了一个可以随时检索、对话的本地知识库。

## 这个知识库是什么

Larkwell 不是一个普通的文档站。它是我把散落在语雀里的笔记，通过自动化工具拉取下来，经过格式清洗、向量化处理后，搭建起来的一个可交互的本地知识库。

简单说：语雀是我写笔记的地方，Larkwell 是我读笔记的地方。

## 为什么会有这个知识库

我一直在语雀上写技术笔记，写了几年后，笔记越来越多，但发现几个问题：

- 想找某个知识点，要在一堆文件夹里翻半天
- 笔记之间没有关联，知识点是孤立的
- 只能在语雀内部搜索，但搜索体验不算好
- 写过的内容，后来遇到类似问题又得重查一遍

所以我把笔记全部拉下来，做了清洗、归类、建了向量索引，然后用 AI 的方式把它们重新组织起来。

## 这里有什么

这个知识库目前包含了我从语雀同步过来的全部技术笔记，主要包括：

- AI 应用开发相关的笔记（LangChain、LangGraph、RAG、Agent）
- 编程语言的踩坑记录和最佳实践
- 项目开发和部署的经验总结
- 日常阅读技术文档时摘录的要点

所有内容按技术领域做了分类，每个分类下是具体的文章和笔记。

## 怎么使用这个知识库

**方式一：直接浏览**

左边的目录树就是知识库的完整结构。点开任意分类，可以看到该领域下的所有笔记标题，点击即读。

**方式二：搜索查找**

右上角的搜索框可以快速定位到具体的内容。如果你已经知道要找什么关键词，用搜索会比翻目录更快。

**方式三：AI 问答（上线中）**

如果你不确定具体要查什么，或者想通过提问来探索知识库，可以直接在对话窗口输入问题。AI 助手会检索知识库中的相关内容，给出带来源引用的回答。

<ClientOnly>
  <a v-if="isDev" href="http://localhost:8000/" target="_blank" class="ai-entry-btn">
    🤖 进入 AI 问答 →
  </a>
</ClientOnly>

## 写在最后

Larkwell 本质上是一个为我自己打造的"第二大脑"——把写过的笔记变成可以检索、可以对话、可以反复调用的知识资产。

如果你在使用过程中有任何建议，欢迎随时告诉我。毕竟，知识库的价值不在于它存了多少内容，而在于它能帮你多快地找到你想知道的东西。

------

**Larkwell** — 让写过的笔记，真的成为记得住的知识。

<style>
.ai-entry-btn {
  display: inline-block;
  padding: 12px 28px;
  background: var(--vp-brand-color, #3451b2);
  color: #fff !important;
  border-radius: 8px;
  text-decoration: none;
  font-weight: bold;
  margin-top: 1rem;
  transition: background 0.2s;
}
.ai-entry-btn:hover {
  background: var(--vp-brand-color-dark, #56c2ff);
}
</style>
