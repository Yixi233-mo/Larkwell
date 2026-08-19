/**
 * 生成 VitePress 侧边栏配置（扁平化版）
 * 
 * 设计原则：
 * - 目录导航展示为扁平化的文章标题列表，不按 category 分组
 * - 每篇文章标题即为可点击的入口
 * - 文章按更新时间（date）倒序排序
 * - category 仅作为后台组织手段，不出现在前台展示层
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'fs'
import { resolve, dirname, join, relative } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

/**
 * 从 md 文件中提取 frontmatter 字段
 */
function extractFrontmatter(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8')
    const match = content.match(/^---\n([\s\S]*?)\n---/)
    if (!match) return null
    
    const fm = {}
    const lines = match[1].split('\n')
    for (const line of lines) {
      const m = line.match(/^(\w+):\s*(.*)$/)
      if (m) {
        const key = m[1].trim()
        let value = m[2].trim()
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        if (value.startsWith('[') && value.endsWith(']')) {
          try {
            value = JSON.parse(value)
          } catch {
            // 保留原值
          }
        }
        fm[key] = value
      }
    }
    return fm
  } catch (e) {
    return null
  }
}

/**
 * 扫描 docs/docs/ 下的所有 md 文件
 * 返回扁平化的文章列表 [{ title, date, link }, ...]
 */
function scanMarkdownFiles(docsDir) {
  const results = []
  
  if (!existsSync(docsDir)) {
    return results
  }
  
  function scanDir(dir, relativeBase = '') {
    const entries = readdirSync(dir)
    
    for (const entry of entries) {
      const fullPath = join(dir, entry)
      const relPath = relativeBase ? `${relativeBase}/${entry}` : entry
      
      if (statSync(fullPath).isDirectory()) {
        scanDir(fullPath, relPath)
      } else if (entry.endsWith('.md') && entry !== 'index.md') {
        const fm = extractFrontmatter(fullPath) || {}
        const filename = relPath.replace(/\.md$/, '')
        
        results.push({
          filename,
          title: fm.title || filename,
          date: fm.date || '1970-01-01',
          link: `/docs/${filename}.html`,
        })
      }
    }
  }
  
  scanDir(docsDir)
  
  // 按日期倒序（最新的在前）
  results.sort((a, b) => b.date.localeCompare(a.date))
  
  return results
}

/**
 * 生成扁平化侧边栏
 * - 顶部一个「📖 知识库总览」入口
 * - 后面跟着所有文章的扁平列表（不分组）
 */
export const genYuqueSideBar = async (pathname = '/docs') => {
  const docsDir = resolve(__dirname, '../docs/docs')
  const files = scanMarkdownFiles(docsDir)
  
  // 构建扁平化的文章列表
  const articleItems = files.map(f => ({
    text: f.title,
    link: f.link,
  }))
  
  return [
    {
      text: '📖 知识库总览',
      link: `${pathname}/`,
    },
    {
      text: '📚 文章列表',
      collapsed: false,
      items: articleItems,
    },
  ]
}
