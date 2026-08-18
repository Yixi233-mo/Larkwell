/**
 * Elog 配置文件 - Larkwell 私有内容仓库
 * 此文件在私有仓库中使用，从语雀拉取文档到 docs/
 */
require('dotenv').config();

module.exports = {
  write: {
    platform: 'yuque',
    yuque: {
      token: process.env.YUQUE_TOKEN,
      login: process.env.YUQUE_LOGIN,
      repo: process.env.YUQUE_REPO,
      onlyPublic: false,
      onlyPublished: true,
    }
  },
  deploy: {
    platform: 'local',
    local: {
      outputDir: './docs',
      filename: 'title',
      format: 'markdown',
      catalog: true,
      formatExt: './elog.format.js'
    }
  },
  image: {
    enable: true,
    platform: 'local',
    local: {
      outputDir: './images',
      pathFollowDoc: true,
    }
  }
}
