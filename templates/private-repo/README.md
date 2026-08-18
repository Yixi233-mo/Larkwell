# Larkwell 私有内容仓库

从语雀同步的文档内容，仅用于公共仓库 [larkwell](https://github.com/Yixi233-mo/larkwell) 的 GitHub Pages 构建。

## 配置

### 1. 配置 Secrets

仓库 Settings → Secrets and variables → Actions → New repository secret：

| Secret 名 | 值 | 用途 |
|----------|-----|------|
| `YUQUE_TOKEN` | 你的语雀 Token | elog 拉取文档 |
| `DISPATCH_TOKEN` | 你的 GitHub PAT（需 repo 权限） | 同步完成后触发公共仓库重新部署 |

### 2. YUQUE_TOKEN 获取

语雀 → 头像 → 设置 → Token → 新建应用 → 复制 Token

### 3. DISPATCH_TOKEN 获取（GitHub PAT）

1. https://github.com/settings/tokens → Generate new token (classic)
2. 勾选 `repo` 权限（访问公共仓库触发 repository_dispatch）
3. 复制 token 填入私有仓库的 `DISPATCH_TOKEN` secret

同时把同一个 PAT 填入公共仓库 [larkwell](https://github.com/Yixi233-mo/larkwell) 的 `ACCESS_TOKEN` secret（用于 checkout 私有仓库）。

## 同步流程

```
语雀云端
   │ elog:sync (workflow 每天 03:00 自动执行)
   ▼
docs/ (markdown 文件)
images/ (图片资源)
   │ git push
   ▼
私有仓库 larkwell-content
   │ repository_dispatch 触发公共仓库
   ▼
公共仓库 larkwell 重新构建 Pages
```

## 手动触发同步

Actions → Sync from Yuque → Run workflow
