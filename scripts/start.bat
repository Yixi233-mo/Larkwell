@echo off
REM ============================================================
REM Larkwell 启动脚本 (Windows)
REM ============================================================
REM 本脚本将启动 Larkwell 的所有服务组件：
REM   1. Elog 语雀文档同步
REM   2. VitePress 文档站点
REM   3. FastAPI AI 助手
REM ============================================================

chcp 65001 >nul
title Larkwell - 智能知识库与 AI 助手

echo ============================================================
echo   Larkwell 智能知识库与 AI 助手
echo   正在启动所有服务组件...
echo ============================================================
echo.

REM 检查 Node.js 是否安装
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js 18+ 版本
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

REM 检查 Python 是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+ 版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 Node.js 依赖是否安装
if not exist "node_modules" (
    echo [安装] 正在安装 Node.js 依赖...
    call npm install
    if %errorlevel% neq 0 (
        echo [错误] Node.js 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查 Python 依赖是否安装
echo [检查] Python 依赖...
python -c "import fastapi; import langchain; import pymilvus" >nul 2>nul
if %errorlevel% neq 0 (
    echo [安装] 正在安装 Python 依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] Python 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查 .env 配置文件
if not exist ".env" (
    echo [警告] 未找到 .env 配置文件
    echo 请复制 .env.example 并填入您的配置
    if exist ".env.example" (
        copy .env.example .env >nul
        echo 已从 .env.example 创建 .env，请修改其中的配置
    )
)

echo.
echo [1/3] 正在从语雀同步文档...
echo ------------------------------------------------------------
call npx elog sync
if %errorlevel% neq 0 (
    echo [警告] 语雀同步可能未完全成功，请检查配置
)

echo.
echo [2/3] 启动 VitePress 文档站点 (后台模式)...
start "Larkwell Docs" cmd /c "npm run docs:dev"

echo.
echo [3/3] 启动 FastAPI AI 助手 (后台模式)...
cd src
start "Larkwell API" cmd /c "python app.py"
cd ..

echo.
echo ============================================================
echo   Larkwell 服务启动完成！
echo ============================================================
echo.
echo   文档站点: http://localhost:5173
echo   AI 助手:  http://localhost:8000
echo   API 文档:  http://localhost:8000/docs
echo.
echo   按 Ctrl+C 或关闭窗口停止服务
echo ============================================================
echo.
pause
