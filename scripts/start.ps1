# Larkwell 启动脚本 (PowerShell)
# ============================================================
# 本脚本将启动 Larkwell 的所有服务组件：
#   1. Elog 语雀文档同步
#   2. VitePress 文档站点
#   3. FastAPI AI 助手
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Larkwell 智能知识库与 AI 助手" -ForegroundColor Cyan
Write-Host "  正在启动所有服务组件..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Node.js
try {
    $nodeVersion = node --version
    Write-Host "[检查] Node.js 版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 Node.js，请先安装 Node.js 18+" -ForegroundColor Red
    Write-Host "下载地址: https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

# 检查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[检查] Python 版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到 Python，请先安装 Python 3.10+" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# 安装 Node.js 依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "[安装] 正在安装 Node.js 依赖..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] Node.js 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}

# 安装 Python 依赖
Write-Host "[安装] 正在检查 Python 依赖..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] Python 依赖安装可能不完整" -ForegroundColor Yellow
}

# 检查 .env 配置
if (-not (Test-Path ".env")) {
    Write-Host "[警告] 未找到 .env 配置文件" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item .env.example .env
        Write-Host "  已从 .env.example 创建 .env，请修改其中的配置" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "[1/3] 正在从语雀同步文档..." -ForegroundColor Cyan
Write-Host "------------------------------------------------------------"
npx elog sync
if ($LASTEXITCODE -ne 0) {
    Write-Host "[警告] 语雀同步可能未完全成功" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[2/3] 启动 VitePress 文档站点..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "cd $PWD; npm run docs:dev" -WindowStyle Normal

Write-Host "[3/3] 启动 FastAPI AI 助手..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-Command", "cd '$PWD\src'; python app.py" -WindowStyle Normal

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Larkwell 服务启动完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  文档站点: http://localhost:5173" -ForegroundColor White
Write-Host "  AI 助手:  http://localhost:8000" -ForegroundColor White
Write-Host "  API 文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  请在新打开的窗口中查看服务运行状态" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green
