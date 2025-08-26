@echo off
chcp 65001 >nul
title Hugo-Self Admin

echo ================================================
echo Hugo-Self Admin Launcher
echo ================================================
echo.

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found, please install Python 3.6+
    pause
    exit /b 1
)

echo Checking Hugo...
hugo version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Hugo not found, please install Hugo
    echo TIP: choco install hugo-extended
    pause
    exit /b 1
)

echo Environment check passed
echo.

echo Starting Hugo-Self with separated architecture...
python scripts\start_separated.py

pause
