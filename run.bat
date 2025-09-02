@echo off
chcp 65001 >nul
echo CSV作品播放器 - Windows启动脚本
echo ==========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python
    echo 请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo 启动应用程序...
python run.py

pause
