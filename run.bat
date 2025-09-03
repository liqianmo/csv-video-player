@echo off
echo 启动 CSV 作品播放器...
python main.py
if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查:
    echo 1. Python 是否正确安装
    echo 2. 是否已运行 install_windows.bat 安装依赖
    echo 3. 查看上方的错误信息
    echo.
    pause
)