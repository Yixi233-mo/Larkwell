/**
 * 生成 VitePress 侧边栏配置
 * 从 elog.cache.json 读取目录结构
 */
import { readFileSync, existsSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

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
 * 生成语雀导航侧边栏
 * @param pathname 路由前缀
 * @returns 侧边栏配置
 */
export const genYuqueSideBar = async (pathname) => {
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

  // 返回默认侧边栏
  return [
    {
      text: '文档',
      items: [
        { text: '首页', link: '/' }
      ]
    }
  ]
}
