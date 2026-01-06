@echo off
chcp 65001 > nul
title GLM 配额查询

echo.
echo ═══════════════════════════════════════════════════════════════
echo.
echo    🚀 正在启动 GLM 配额查询服务器...
echo.
echo ═══════════════════════════════════════════════════════════════
echo.

python src\server.py

pause
