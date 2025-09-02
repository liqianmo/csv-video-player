#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 检查环境并启动应用程序
"""

import sys
import os
import subprocess

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("需要Python 3.8或更高版本")
        return False
    
    print(f"✓ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True

def install_dependencies():
    """安装依赖"""
    print("正在检查并安装依赖...")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
        ], check=True, capture_output=True, text=True)
        print("✓ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print("请手动运行: pip install -r requirements.txt")
        return False

def run_application():
    """运行应用程序"""
    print("启动CSV作品播放器...")
    
    try:
        # 导入并运行主程序
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import main
        main.main()
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保所有依赖都已正确安装")
        return False
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("CSV作品播放器 - 启动器")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        input("按Enter键退出...")
        return
    
    # 检查是否需要安装依赖
    try:
        import PyQt5
        import requests
        print("✓ 依赖已安装")
    except ImportError:
        print("⚠ 检测到缺少依赖")
        response = input("是否自动安装依赖? (y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            if not install_dependencies():
                input("按Enter键退出...")
                return
        else:
            print("请手动安装依赖: pip install -r requirements.txt")
            input("按Enter键退出...")
            return
    
    # 运行应用程序
    print("\n启动应用程序...")
    run_application()

if __name__ == '__main__':
    main()
