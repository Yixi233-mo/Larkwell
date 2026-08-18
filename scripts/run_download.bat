@echo off
REM ============================================================
REM Larkwell 语雀文档下载 - 定时任务启动脚本
REM 创建时间: 2026-08-18
REM 用途: 每天早上10点自动执行语雀文档下载
REM ============================================================

chcp 65001 >nul
cd /d E:\plan\qwen\yuque-vitepress

echo ============================================================
echo   Larkwell 语雀文档同步
echo   执行时间: %date% %time%
echo ============================================================
echo.

python -u scripts\download_safe.py 2>&1

echo.
echo ============================================================
echo   下载任务完成
echo   日志已保存到: E:\plan\qwen\yuque-vitepress\logs\download.log
echo ============================================================

REM 记录执行日志
echo [%date% %time%] Download task completed >> logs\download_schedule.log
