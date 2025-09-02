#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 验证应用程序依赖和基本功能
"""

import sys
import os

def test_imports():
    """测试所有必需的导入"""
    print("测试依赖导入...")
    
    try:
        import PyQt5.QtWidgets
        print("✓ PyQt5.QtWidgets")
    except ImportError:
        print("✗ PyQt5.QtWidgets - 请安装: pip install PyQt5")
        return False
    
    try:
        import PyQt5.QtCore
        print("✓ PyQt5.QtCore")
    except ImportError:
        print("✗ PyQt5.QtCore")
        return False
    
    try:
        import PyQt5.QtMultimedia
        print("✓ PyQt5.QtMultimedia")
    except ImportError:
        print("✗ PyQt5.QtMultimedia")
        return False
    
    try:
        import PyQt5.QtMultimediaWidgets
        print("✓ PyQt5.QtMultimediaWidgets")
    except ImportError:
        print("✗ PyQt5.QtMultimediaWidgets")
        return False
    
    try:
        import requests
        print("✓ requests")
    except ImportError:
        print("✗ requests - 请安装: pip install requests")
        return False
    
    return True

def test_csv_file():
    """测试CSV文件是否存在"""
    csv_file = "集体参赛.csv"
    if os.path.exists(csv_file):
        print(f"✓ 找到CSV文件: {csv_file}")
        
        # 读取前几行检查格式
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                print(f"✓ CSV文件列名: {headers}")
                
                # 检查必需的列
                required_columns = ['作品名称', '资料链接', '身份证名字', '参赛者组别']
                missing_columns = [col for col in required_columns if col not in headers]
                
                if missing_columns:
                    print(f"⚠ 缺少必需列: {missing_columns}")
                else:
                    print("✓ CSV文件格式正确")
                    
        except Exception as e:
            print(f"✗ CSV文件读取错误: {e}")
            return False
    else:
        print(f"⚠ 未找到CSV文件: {csv_file}")
        print("  您可以稍后通过应用程序导入CSV文件")
    
    return True

def main():
    """主函数"""
    print("CSV作品播放器 - 依赖测试")
    print("=" * 40)
    
    # 测试导入
    if not test_imports():
        print("\n❌ 依赖测试失败，请安装缺少的包")
        print("运行: pip install -r requirements.txt")
        return
    
    print("\n测试CSV文件...")
    test_csv_file()
    
    print("\n✅ 基本测试通过!")
    print("\n您现在可以:")
    print("1. 运行主程序: python main.py")
    print("2. 或构建可执行文件: python build.py")

if __name__ == '__main__':
    main()
