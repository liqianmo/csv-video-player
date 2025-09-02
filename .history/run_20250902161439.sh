#!/bin/bash

echo "CSV作品播放器 - macOS/Linux启动脚本"
echo "=========================================="

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    echo "请先安装Python 3.8或更高版本"
    exit 1
fi

echo "启动应用程序..."
python3 run.py

echo "按任意键退出..."
read -n 1
