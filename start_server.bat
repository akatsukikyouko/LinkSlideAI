@echo off
echo 正在启动...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误：未检测到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查uv是否安装
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装uv包管理器...
    pip install uv
)

REM 检查是否存在虚拟环境，如果没有则创建
if not exist ".venv" (
    echo 创建虚拟环境...
    uv venv --python 3.12
)

REM 使用uv安装依赖
echo 检查并安装依赖库...
uv pip install -r requirements.txt

echo.
echo 环境准备完成，启动中
uv run app.py
pause
