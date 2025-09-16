@echo off
chcp 65001 >nul
echo.
echo =====================================
echo 🧹 Hugo-Self 端口清理工具
echo =====================================
echo.
echo 此工具将检查并清理Hugo-Self使用的端口:
echo   📝 Hugo博客: 8000
echo   🔧 管理后台: 8080  
echo   🔌 API服务: 8081
echo.
pause
echo.

python "%~dp0cleanup_ports.py"

echo.
echo =====================================
echo 🚀 清理完成！
echo =====================================
echo.
echo 现在可以运行启动脚本了:
echo   cd /d "%~dp0.."
echo   python scripts\start_separated.py
echo.
pause