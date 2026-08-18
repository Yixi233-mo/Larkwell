import { defineConfig } from 'vitepress'
import { genYuqueSideBar } from "../../utils/route.js";
import { StarSVG } from "../../utils/assists.js";

// Larkwell 项目 VitePress 配置
export default defineConfig({
  lang: "zh-CN",
  title: "Larkwell 文档中心",
  description: "Larkwell - 基于语雀的智能知识库与 AI 问答助手",
  lastUpdated: true,
  cleanUrls: false,
  ignoreDeadLinks: false,
  // GitHub Pages 部署在 https://yixi233-mo.github.io/Larkwell/ 子路径下，需配置 base
  // 注意：GitHub Pages URL 大小写敏感，必须与仓库名大小写完全一致
  base: "/Larkwell/",
  // GitHub Pages 仓库源信息（用于 lastUpdated 等功能）
  repo: "Yixi233-mo/Larkwell",
  repoBranch: "main",
  head: [
    [
      'link', { rel: 'icon', href: 'favicon.svg' }
    ]
  ],
  themeConfig: {
    search: {
      provider: 'local',
      options: {
        detailedView: true,
        miniSearch: {
          options: {
            fuzzy: 0.2,
            prefix: true,
          }
        }
      }
    },
    outline: [2, 6],
    nav: [
      { text: '首页', link: '/' },
      { text: '知识库', link: 'https://www.yuque.com/yuqueyonghu-dg6ehw/slk2dt', target: '_blank' },
      { text: '文档', link: '/docs/', activeMatch: '/docs/' }
    ],
    sidebar: {
      "/docs/": await genYuqueSideBar('/docs'),
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },
    socialLinks: [
      // Star 入口（五角星图标，指向 GitHub 仓库 star 页面）
      { icon: { svg: StarSVG }, link: "https://github.com/Yixi233-mo/Larkwell" },
      // GitHub 个人主页入口（使用 VitePress 内置图标）
      { icon: 'github', link: "https://github.com/Yixi233-mo" }
    ],
    footer: {
      message: 'Powered by <a href="https://www.yuque.com/yuqueyonghu-dg6ehw/slk2dt" target="_blank">语雀知识库</a> & <a href="https://vitepress.dev" target="_blank">VitePress</a> with <a href="https://github.com/LetTTGACO/elog" target="_blank">Elog</a>',
      copyright: 'Copyright © 2026 Larkwell'
    },
  }
})
