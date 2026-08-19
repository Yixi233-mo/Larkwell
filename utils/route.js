/**
 * 生成 VitePress 侧边栏配置
 * 
 * 优先级：
 * 1. 扫描 docs/docs/ 下的实际 .md 文件，按 frontmatter 的 category 分组
 * 2. 读取 elog.cache.json（如果存在）
 * 3. 兜底：返回基础结构
 */
import { readFileSync, existsSync, readdirSync, statSync } from 'fs'
import { resolve, dirname, join, basename, relative } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

/**
 * 从 md 文件中提取 frontmatter 字段
 * 支持：title, category, tags, date, description
 */
function extractFrontmatter(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8')
    const match = content.match(/^---\n([\s\S]*?)\n---/)
    if (!match) return null
    
    const fm = {}
    const lines = match[1].split('\n')
    for (const line of lines) {
      // 简单解析 key: value 格式
      const m = line.match(/^(\w+):\s*(.*)$/)
      if (m) {
        const key = m[1].trim()
        let value = m[2].trim()
        // 去掉引号
        if (value.startsWith('"') && value.endsWith('"')) {
          value = value.slice(1, -1)
        }
        // 处理数组格式 ["a", "b"]
        if (value.startsWith('[') && value.endsWith(']')) {
          try {
            value = JSON.parse(value)
          } catch {
            // 解析失败保留原值
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
 * 返回 [{ filename, title, category, date, link }, ...]
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
        // 递归扫描子目录
        scanDir(fullPath, relPath)
      } else if (entry.endsWith('.md') && entry !== 'index.md') {
        // 跳过 index.md（那是总览页）
        const fm = extractFrontmatter(fullPath) || {}
        const filename = relPath.replace(/\.md$/, '')
        
        results.push({
          filename,
          title: fm.title || filename,
          category: fm.category || '未分类',
          date: fm.date || '1970-01-01',
          link: `/docs/${filename}.html`,
          description: fm.description || '',
        })
      }
    }
  }
  
  scanDir(docsDir)
  
  // 按日期倒序
  results.sort((a, b) => b.date.localeCompare(a.date))
  
  return results
}

/**
 * 按分类分组文档
 */
function groupByCategory(docs) {
  const groups = {}
  
  for (const doc of docs) {
    if (!groups[doc.category]) {
      groups[doc.category] = []
    }
    groups[doc.category].push({
      text: doc.title,
      link: doc.link,
    })
  }
  
  // 转换成 VitePress sidebar 格式
  return Object.entries(groups).map(([category, items]) => ({
    text: category,
    collapsed: false,
    items,
  }))
}

/**
 * 语雀 cache 目录结构生成侧边栏（保留兼容性）
 */
function genYuqueRoute(arr, pathname) {
  function loop(parId) {
    return arr.reduce((acc, cur) => {
      if (cur.parent_uuid === parId) {
        const parent = arr.find(item => item.uuid === parId)
        cur.path = (parent?.path || '') + '/' + (cur.slug || cur.title)
        cur.items = loop(cur.uuid)
        let route
        if (cur.items.length) {
          route = {
            text: cur.title,
            collapsed: false,
            items: cur.items
          }
          acc.push(route)
        } else {
          if (cur.type === 'DOC') {
            route = {
              text: cur.title,
              link: `${pathname ? pathname : ''}${cur.path}.html`,
            }
            acc.push(route)
          }
        }
      }
      return acc
    }, [])
  }
  return loop('')
}

/**
 * 生成侧边栏
 * @param pathname 路由前缀（如 '/docs'）
 * @returns 侧边栏配置
 */
export const genYuqueSideBar = async (pathname = '/docs') => {
  // 优先级 1: 扫描 docs/docs/ 实际文件
  const docsDir = resolve(__dirname, '../docs/docs')
  const files = scanMarkdownFiles(docsDir)
  
  if (files.length > 0) {
    const grouped = groupByCategory(files)
    
    // 加入"总览"入口在顶部
    return [
      {
        text: '📖 知识库总览',
        link: `${pathname}/`,
      },
      ...grouped,
    ]
  }
  
  // 优先级 2: 读取 elog.cache.json
  try {
    const cachePath = resolve(__dirname, '../elog.cache.json')
    if (existsSync(cachePath)) {
      const content = readFileSync(cachePath, 'utf-8')
      const cache = JSON.parse(content)
      const { catalog } = cache
      if (catalog && catalog.length > 0) {
        return genYuqueRoute(catalog, pathname)
      }
    }
  } catch (e) {
    console.warn('读取 elog.cache.json 失败:', e.message)
  }
  
  // 优先级 3: 兜底
  return [
    {
      text: '📖 知识库总览',
      link: `${pathname}/`,
    },
    {
      text: '🗂️ 文档',
      items: [
        { text: '首页', link: '/' }
      ]
    }
  ]
}
