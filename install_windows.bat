@echo off
echo 正在安装 CSV 作品播放器依赖...
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.6 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 已安装，正在安装依赖包...
echo.

REM 升级 pip
python -m pip install --upgrade pip

REM 安装 PyQt5
echo 正在安装 PyQt5...
python -m pip install PyQt5>=5.15.0

REM 安装 PyQt5-tools (可选)
echo 正在安装 PyQt5-tools...
python -m pip install PyQt5-tools>=5.15.0

echo.
echo 安装完成！
echo.
echo 使用方法:
echo 1. 双击运行 run.bat
echo 2. 或在命令行中运行: python main.py
echo.
pause