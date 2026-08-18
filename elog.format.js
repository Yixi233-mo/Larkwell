/**
 * 自定义文档格式化插件
 * 处理语雀导出的 Markdown，使其适配 VitePress
 */
const format = async (doc) => {
  if (doc.body) {
    // 将语雀灰色高亮块转成 VitePress 支持的 tip 高亮块
    doc.body = doc.body?.replaceAll(':::tips', ':::tip')
    // 将语雀绿色高亮块同样转成 VitePress 支持的 tip 高亮块
    doc.body = doc.body?.replaceAll(':::success', ':::tip')
    // 将语雀警告块转换
    doc.body = doc.body?.replaceAll(':::warning', ':::warning')
    // 将语雀危险块转换
    doc.body = doc.body?.replaceAll(':::danger', ':::danger')
  }
  return doc;
};

module.exports = {
  format,
};
