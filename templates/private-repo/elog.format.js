/**
 * Larkwell 私有内容仓库 - elog 文档处理拓展点
 *
 * elog 规范：require(formatExtPath) 后解构 { format } 方法
 * format(doc) 接收文档对象，返回处理后的文档对象
 */
module.exports = {
  format: function (doc) {
    // 默认不做额外处理，保持 elog 原生输出
    return doc;
  }
};
