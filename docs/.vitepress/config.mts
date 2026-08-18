import { defineConfig } from 'vitepress'
import { genYuqueSideBar } from "../../utils/route.js";
import { YuQueSVG } from "../../utils/assists.js";

// Larkwell 项目 VitePress 配置
export default defineConfig({
  lang: "zh-CN",
  title: "Larkwell 文档中心",
  description: "Larkwell - 基于语雀的智能知识库与 AI 问答助手",
  lastUpdated: true,
  cleanUrls: false,
  ignoreDeadLinks: false,
  // GitHub Pages 部署在 https://yixi233-mo.github.io/larkwell/ 子路径下，需配置 base
  base: "/larkwell/",
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
      { text: '知识库', link: '/docs/', activeMatch: '/docs/' }
    ],
    sidebar: {
      "/docs/": await genYuqueSideBar('/docs'),
    },
    docFooter: {
      prev: '上一篇',
      next: '下一篇'
    },
    socialLinks: [
      { icon: { svg: YuQueSVG }, link: "https://www.yuque.com/yuqueyonghu-dg6ehw/slk2dt" },
      { icon: 'github', link: "https://github.com/Yixi233-mo" }
    ],
    footer: {
      message: 'Powered by <a href="https://www.yuque.com/yuqueyonghu-dg6ehw/slk2dt" target="_blank">语雀知识库</a> & <a href="https://vitepress.dev" target="_blank">VitePress</a> with <a href="https://github.com/LetTTGACO/elog" target="_blank">Elog</a>',
      copyright: 'Copyright © 2026 Larkwell'
    },
  }
})
