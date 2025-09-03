#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建可执行文件的脚本
使用 PyInstaller 将 Python 程序打包成独立的 exe 文件
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """安装 PyInstaller"""
    print("正在安装 PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller 安装成功！")
        return True
    except subprocess.CalledProcessError:
        print("PyInstaller 安装失败！")
        return False

def build_executable():
    """构建可执行文件"""
    print("正在构建可执行文件...")
    
    # PyInstaller 命令参数
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包成单个文件
        "--windowed",                   # 不显示控制台窗口
        "--name=CSV作品播放器",          # 可执行文件名称
        "--icon=icon.ico",              # 图标文件（如果存在）
        "--add-data=README_Windows.md;.", # 包含说明文件
        "main.py"
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists("icon.ico"):
        cmd.remove("--icon=icon.ico")
    
    try:
        subprocess.check_call(cmd)
        print("构建成功！")
        return True
    except subprocess.CalledProcessError:
        print("构建失败！")
        return False

def create_distribution():
    """创建发布包"""
    print("正在创建发布包...")
    
    # 创建发布目录
    dist_dir = "CSV作品播放器_发布包"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)
    
    # 复制可执行文件
    exe_path = os.path.join("dist", "CSV作品播放器.exe")
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, dist_dir)
        print(f"已复制可执行文件到 {dist_dir}")
    
    # 复制说明文件
    files_to_copy = [
        "README_Windows.md",
        "使用说明.txt"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, dist_dir)
            print(f"已复制 {file}")
    
    print(f"发布包创建完成：{dist_dir}")

def main():
    """主函数"""
    print("=== CSV作品播放器 可执行文件构建工具 ===")
    print()
    
    # 检查必要文件
    if not os.path.exists("main.py"):
        print("错误：找不到 main.py 文件！")
        return
    
    # 安装 PyInstaller
    if not install_pyinstaller():
        return
    
    # 构建可执行文件
    if not build_executable():
        return
    
    # 创建发布包
    create_distribution()
    
    print()
    print("构建完成！")
    print("可执行文件位置：CSV作品播放器_发布包/CSV作品播放器.exe")
    print("直接将整个发布包文件夹给客户即可使用。")

if __name__ == "__main__":
    main()