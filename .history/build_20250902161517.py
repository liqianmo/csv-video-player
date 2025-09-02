#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本 - 用于本地构建可执行文件
"""

import os
import sys
import subprocess
import platform

def build_executable():
    """构建可执行文件"""
    system = platform.system()
    
    print(f"正在为 {system} 系统构建可执行文件...")
    
    # PyInstaller 命令
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=CSV作品播放器',
        'main.py'
    ]
    
    # Windows系统添加图标（如果存在）
    if system == "Windows" and os.path.exists("icon.ico"):
        cmd.extend(['--icon=icon.ico'])
    
    try:
        # 执行构建
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("构建成功！")
        print(f"可执行文件位置: dist/CSV作品播放器{'.exe' if system == 'Windows' else ''}")
        
        # 显示文件大小
        if system == "Windows":
            exe_path = "dist/CSV作品播放器.exe"
        else:
            exe_path = "dist/CSV作品播放器"
            
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"文件大小: {size / (1024*1024):.1f} MB")
            
    except subprocess.CalledProcessError as e:
        print("构建失败!")
        print("错误信息:", e.stderr)
        return False
    except FileNotFoundError:
        print("错误: 未找到 pyinstaller")
        print("请先安装 pyinstaller: pip install pyinstaller")
        return False
    
    return True

def clean_build():
    """清理构建文件"""
    import shutil
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['CSV作品播放器.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已删除目录: {dir_name}")
    
    for file_name in files_to_clean:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"已删除文件: {file_name}")

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == 'clean':
        clean_build()
        print("清理完成!")
        return
    
    print("CSV作品播放器 - 构建脚本")
    print("=" * 40)
    
    # 检查依赖
    try:
        import PyQt5
        import requests
        print("✓ 依赖检查通过")
    except ImportError as e:
        print(f"✗ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 构建
    if build_executable():
        print("\n构建完成! 您可以在 dist/ 目录中找到可执行文件。")
        print("\n使用方法:")
        print("1. 运行可执行文件")
        print("2. 点击 '导入CSV文件' 导入您的数据文件")
        print("3. 双击作品行或点击播放按钮播放视频")
    else:
        print("\n构建失败，请检查错误信息。")

if __name__ == '__main__':
    main()
