@echo off
chcp 65001 >nul
title Hugo-Self 优化启动器

echo ================================================
echo Hugo-Self 智能启动器 (优化版)
echo ================================================
echo.

echo 🔍 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装，请先安装Python 3.6+
    pause
    exit /b 1
)

echo 🔍 检查Hugo环境...
hugo version >nul 2>&1
if errorlevel 1 (
    echo ❌ Hugo未安装，请先安装Hugo
    echo 💡 提示: choco install hugo-extended
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

echo 🚀 启动Hugo-Self管理系统...
echo ⏳ 正在检测可用端口并启动服务...
echo.

:: 启动分离式架构管理系统
python scripts\start_separated.py

echo.
echo 🛑 所有服务已停止
pause