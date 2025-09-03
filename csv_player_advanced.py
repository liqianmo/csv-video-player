#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV作品播放器 - 高级版
功能：CSV导入、在线播放、本地缓存、系统播放器集成
特点：纯Python标准库实现，无需外部依赖，更好的用户体验
作者：CodeBuddy
版本：2.0
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import urllib.request
import urllib.parse
import webbrowser
import os
import threading
import time
import json
import subprocess
import sys
import csv
import re
from pathlib import Path
import ssl
import tempfile
import shutil

# 禁用SSL验证（处理某些下载链接的SSL问题）
ssl._create_default_https_context = ssl._create_unverified_context

class CSVReader:
    """CSV文件读取器（支持多种编码）"""
    
    @staticmethod
    def read_csv(file_path):
        """智能读取CSV文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        
        for encoding in encodings:
            try:
                data = []
                with open(file_path, 'r', encoding=encoding) as f:
                    # 检测分隔符
                    sample = f.read(1024)
                    f.seek(0)
                    
                    delimiter = ','
                    if sample.count(';') > sample.count(','):
                        delimiter = ';'
                    elif sample.count('\t') > sample.count(','):
                        delimiter = '\t'
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    data = list(reader)
                    columns = reader.fieldnames
                    
                return data, columns, encoding
                
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                if encoding == encodings[-1]:  # 最后一个编码也失败
                    raise Exception(f"无法读取CSV文件: {e}")
                continue
                
        raise Exception("无法识别文件编码")

class MediaManager:
    """媒体文件管理器"""
    
    def __init__(self, progress_callback=None, log_callback=None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.cache_dir = os.path.join(tempfile.gettempdir(), "csv_player_cache")
        self.cached_files = {}
        self.load_cache_info()
        
    def load_cache_info(self):
        """加载缓存信息"""
        cache_file = os.path.join(self.cache_dir, "cache_info.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cached_files = json.load(f)
            except Exception as e:
                self.log(f"加载缓存信息失败: {e}")
                
    def save_cache_info(self):
        """保存缓存信息"""
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_file = os.path.join(self.cache_dir, "cache_info.json")
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cached_files, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"保存缓存信息失败: {e}")
            
    def log(self, message):
        """记录日志"""
        print(f"[{time.strftime('%H:%M:%S')}] {message}")
        if self.log_callback:
            self.log_callback(message)
            
    def get_safe_filename(self, url, work_name=""):
        """生成安全的文件名"""
        if work_name:
            # 使用作品名称作为文件名
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', work_name)
            safe_name = safe_name[:50]  # 限制长度
        else:
            # 从URL提取文件名
            parsed = urllib.parse.urlparse(url)
            safe_name = os.path.basename(parsed.path) or f"media_{int(time.time())}"
            
        # 确保有扩展名
        if '.' not in safe_name:
            # 根据URL推测扩展名
            if any(ext in url.lower() for ext in ['.mp4', '.avi', '.mov', '.wmv']):
                for ext in ['.mp4', '.avi', '.mov', '.wmv']:
                    if ext in url.lower():
                        safe_name += ext
                        break
            else:
                safe_name += '.mp4'  # 默认扩展名
                
        return safe_name
        
    def is_video_platform_url(self, url):
        """检查是否为视频平台URL"""
        platforms = [
            'bilibili.com', 'b23.tv',
            'youtube.com', 'youtu.be',
            'youku.com', 'iqiyi.com',
            'qq.com/v', 'v.qq.com',
            'weibo.com', 'douyin.com'
        ]
        return any(platform in url.lower() for platform in platforms)
        
    def try_download_video(self, url, work_name):
        """尝试下载视频文件"""
        try:
            # 检查是否已缓存
            if url in self.cached_files:
                cached_path = self.cached_files[url]
                if os.path.exists(cached_path):
                    self.log(f"使用缓存文件: {work_name}")
                    return cached_path
                    
            filename = self.get_safe_filename(url, work_name)
            cache_path = os.path.join(self.cache_dir, filename)
            
            os.makedirs(self.cache_dir, exist_ok=True)
            
            self.log(f"尝试下载: {work_name}")
            
            # 创建请求
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Referer', url)
            
            # 下载文件
            with urllib.request.urlopen(req, timeout=30) as response:
                # 检查内容类型
                content_type = response.headers.get('Content-Type', '').lower()
                if 'text/html' in content_type:
                    # 这可能是一个网页，不是直接的视频文件
                    self.log(f"检测到网页内容，建议在浏览器中打开: {work_name}")
                    return None
                    
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                
                with open(cache_path, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if self.progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.progress_callback(progress)
                            
            # 验证下载的文件
            if os.path.getsize(cache_path) < 1024:  # 文件太小，可能不是视频
                os.remove(cache_path)
                self.log(f"下载的文件太小，可能不是视频文件: {work_name}")
                return None
                
            # 记录缓存
            self.cached_files[url] = cache_path
            self.save_cache_info()
            
            self.log(f"下载完成: {work_name}")
            return cache_path
            
        except Exception as e:
            self.log(f"下载失败 {work_name}: {e}")
            return None

class SystemPlayer:
    """系统播放器集成"""
    
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        
    def log(self, message):
        """记录日志"""
        if self.log_callback:
            self.log_callback(f"[播放器] {message}")
            
    def play_file(self, file_path):
        """使用系统默认播放器播放文件"""
        try:
            if not os.path.exists(file_path):
                self.log(f"文件不存在: {file_path}")
                return False
                
            self.log(f"使用系统播放器打开: {os.path.basename(file_path)}")
            
            if sys.platform.startswith('win'):
                os.startfile(file_path)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
                
            return True
                
        except Exception as e:
            self.log(f"播放失败: {e}")
            return False
            
    def open_url_in_browser(self, url):
        """在浏览器中打开URL"""
        try:
            webbrowser.open(url)
            self.log(f"在浏览器中打开: {url}")
            return True
        except Exception as e:
            self.log(f"打开浏览器失败: {e}")
            return False

class AdvancedCSVPlayer:
    """高级CSV播放器主应用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CSV作品播放器 v2.0 (高级版)")
        self.root.geometry("1400x900")
        self.root.configure(bg='#F5F5F7')
        
        # 设置窗口图标（如果有的话）
        try:
            # self.root.iconbitmap('icon.ico')
            pass
        except:
            pass
            
        # 数据存储
        self.data = []
        self.columns = []
        self.work_data = {}
        
        # 初始化组件
        self.media_manager = MediaManager(
            progress_callback=self.update_progress,
            log_callback=self.add_log
        )
        self.player = SystemPlayer(log_callback=self.add_log)
        
        # 创建界面
        self.create_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        
        # 配置样式
        style.configure('Title.TLabel', font=('Microsoft YaHei', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Microsoft YaHei', 12, 'bold'))
        style.configure('Info.TLabel', font=('Microsoft YaHei', 9), foreground='#666666')
        
    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root, padding="15")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=2)
        main_container.columnconfigure(2, weight=1)
        main_container.rowconfigure(1, weight=1)
        
        # 标题栏
        self.create_header(main_container)
        
        # 左侧控制面板
        self.create_control_panel(main_container)
        
        # 中间作品列表
        self.create_work_list(main_container)
        
        # 右侧信息面板
        self.create_info_panel(main_container)
        
        # 底部状态栏
        self.create_status_bar(main_container)
        
    def create_header(self, parent):
        """创建标题栏"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="CSV作品播放器 v2.0", style='Title.TLabel')
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="高级版 - 智能播放 · 无需依赖", style='Info.TLabel')
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
    def create_control_panel(self, parent):
        """创建左侧控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 文件操作
        file_frame = ttk.LabelFrame(control_frame, text="文件操作", padding="8")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(0, weight=1)
        
        ttk.Button(file_frame, text="📁 导入CSV文件", 
                  command=self.import_csv).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.file_info_label = ttk.Label(file_frame, text="未导入文件", style='Info.TLabel')
        self.file_info_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 播放控制
        play_frame = ttk.LabelFrame(control_frame, text="播放控制", padding="8")
        play_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        play_frame.columnconfigure(0, weight=1)
        
        # 搜索框
        ttk.Label(play_frame, text="快速搜索:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(play_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=2)
        self.search_entry.bind('<KeyRelease>', self.filter_works)
        self.search_entry.bind('<Return>', self.play_first_match)
        
        ttk.Button(play_frame, text="🔍 搜索播放", 
                  command=self.play_first_match).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        # 播放模式
        mode_frame = ttk.LabelFrame(control_frame, text="播放模式", padding="8")
        mode_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.play_mode = tk.StringVar(value="browser")\n        ttk.Radiobutton(mode_frame, text="🌐 浏览器播放 (推荐)", \n                       variable=self.play_mode, value="browser").grid(row=0, column=0, sticky=tk.W)\n        ttk.Radiobutton(mode_frame, text="💾 下载后播放", \n                       variable=self.play_mode, value="download").grid(row=1, column=0, sticky=tk.W)\n        \n        # 进度显示\n        progress_frame = ttk.LabelFrame(control_frame, text="进度信息", padding="8")\n        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))\n        progress_frame.columnconfigure(0, weight=1)\n        \n        self.progress_var = tk.DoubleVar()\n        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)\n        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=2)\n        \n        self.status_label = ttk.Label(progress_frame, text="就绪", style='Info.TLabel')\n        self.status_label.grid(row=1, column=0, sticky=tk.W)\n        \n        # 工具按钮\n        tools_frame = ttk.LabelFrame(control_frame, text="工具", padding="8")\n        tools_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))\n        tools_frame.columnconfigure(0, weight=1)\n        \n        ttk.Button(tools_frame, text="📂 打开缓存目录", \n                  command=self.open_cache_dir).grid(row=0, column=0, sticky=(tk.W, tk.E), pady=1)\n        ttk.Button(tools_frame, text="🗑️ 清理缓存", \n                  command=self.clear_cache).grid(row=1, column=0, sticky=(tk.W, tk.E), pady=1)\n        ttk.Button(tools_frame, text="ℹ️ 关于程序", \n                  command=self.show_about).grid(row=2, column=0, sticky=(tk.W, tk.E), pady=1)\n        \n    def create_work_list(self, parent):\n        """创建中间作品列表"""\n        list_frame = ttk.LabelFrame(parent, text="作品列表", padding="10")\n        list_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5)\n        list_frame.columnconfigure(0, weight=1)\n        list_frame.rowconfigure(0, weight=1)\n        \n        # 创建Treeview\n        columns = ('作品名称', '参赛者', '组别', '指导老师', '推送单位', '状态')\n        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)\n        \n        # 设置列\n        column_widths = {'作品名称': 200, '参赛者': 100, '组别': 80, \n                        '指导老师': 100, '推送单位': 150, '状态': 80}\n        \n        for col in columns:\n            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))\n            self.tree.column(col, width=column_widths.get(col, 100))\n        \n        # 滚动条\n        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)\n        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)\n        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)\n        \n        # 布局\n        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))\n        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))\n        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))\n        \n        # 事件绑定\n        self.tree.bind('<Double-1>', self.play_selected)\n        self.tree.bind('<Button-3>', self.show_context_menu)\n        self.tree.bind('<<TreeviewSelect>>', self.on_selection_change)\n        \n        # 创建右键菜单\n        self.create_context_menu()\n        \n    def create_context_menu(self):\n        """创建右键菜单"""\n        self.context_menu = tk.Menu(self.root, tearoff=0)\n        self.context_menu.add_command(label="▶️ 播放", command=self.play_selected)\n        self.context_menu.add_command(label="🌐 在浏览器中打开", command=self.open_in_browser)\n        self.context_menu.add_separator()\n        self.context_menu.add_command(label="💾 下载到本地", command=self.download_selected)\n        self.context_menu.add_command(label="📂 打开文件位置", command=self.open_file_location)\n        \n    def create_info_panel(self, parent):\n        """创建右侧信息面板"""\n        info_frame = ttk.LabelFrame(parent, text="详细信息", padding="10")\n        info_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))\n        info_frame.columnconfigure(0, weight=1)\n        info_frame.rowconfigure(1, weight=1)\n        \n        # 作品信息显示\n        self.info_text = scrolledtext.ScrolledText(info_frame, width=35, height=15, \n                                                  wrap=tk.WORD, state=tk.DISABLED)\n        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))\n        \n        # 日志显示\n        log_label = ttk.Label(info_frame, text="操作日志", style='Heading.TLabel')\n        log_label.grid(row=1, column=0, sticky=tk.W, pady=(10, 5))\n        \n        self.log_text = scrolledtext.ScrolledText(info_frame, width=35, height=15, \n                                                 wrap=tk.WORD, state=tk.DISABLED)\n        self.log_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))\n        \n    def create_status_bar(self, parent):\n        """创建底部状态栏"""\n        status_frame = ttk.Frame(parent)\n        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))\n        status_frame.columnconfigure(1, weight=1)\n        \n        self.status_left = ttk.Label(status_frame, text="就绪")\n        self.status_left.grid(row=0, column=0, sticky=tk.W)\n        \n        self.status_right = ttk.Label(status_frame, text="CSV作品播放器 v2.0", style='Info.TLabel')\n        self.status_right.grid(row=0, column=2, sticky=tk.E)\n        \n    def import_csv(self):\n        """导入CSV文件"""\n        file_path = filedialog.askopenfilename(\n            title=\"选择CSV文件\",\n            filetypes=[(\"CSV files\", \"*.csv\"), (\"All files\", \"*.*\")]\n        )\n        \n        if not file_path:\n            return\n            \n        try:\n            self.add_log(f\"正在读取文件: {os.path.basename(file_path)}\")\n            \n            # 读取CSV文件\n            self.data, self.columns, encoding = CSVReader.read_csv(file_path)\n            \n            self.add_log(f\"文件编码: {encoding}\")\n            \n            # 检查必要的列\n            required_columns = ['作品名称']\n            missing_columns = [col for col in required_columns if col not in self.columns]\n            \n            if missing_columns:\n                messagebox.showerror(\"错误\", f\"文件缺少必要的列: {', '.join(missing_columns)}\")\n                return\n                \n            # 查找链接列\n            link_columns = []\n            for col in self.columns:\n                if any(keyword in col.lower() for keyword in ['链接', 'url', 'link', '地址', 'http']):\n                    link_columns.append(col)\n                    \n            if not link_columns:\n                messagebox.showwarning(\"警告\", \"未找到链接列，播放功能可能无法正常使用\")\n                \n            # 处理数据\n            self.process_data()\n            \n            # 更新界面\n            self.populate_tree()\n            \n            # 更新状态\n            self.file_info_label.config(text=f\"已导入: {os.path.basename(file_path)} ({len(self.data)} 条记录)\")\n            self.status_left.config(text=f\"已加载 {len(self.data)} 条作品记录\")\n            \n            self.add_log(f\"成功导入 {len(self.data)} 条记录\")\n            \n        except Exception as e:\n            error_msg = f\"导入失败: {e}\"\n            self.add_log(error_msg)\n            messagebox.showerror(\"错误\", error_msg)\n            \n    def process_data(self):\n        """处理导入的数据"""\n        self.work_data = {}\n        \n        for i, row in enumerate(self.data):\n            work_name = str(row.get('作品名称', f'作品_{i+1}')).strip()\n            if not work_name or work_name == 'nan':\n                work_name = f'作品_{i+1}'\n                \n            # 查找视频链接\n            video_url = \"\"\n            for col in self.columns:\n                if any(keyword in col.lower() for keyword in ['链接', 'url', 'link', '地址']):\n                    url_value = str(row.get(col, '')).strip()\n                    if url_value and url_value != 'nan' and url_value.startswith('http'):\n                        video_url = url_value\n                        break\n                        \n            # 存储作品数据\n            work_id = f\"work_{i}\"\n            self.work_data[work_id] = {\n                'id': work_id,\n                'name': work_name,\n                'participant': str(row.get('身份证名字', row.get('参赛者', row.get('姓名', '')))).strip(),\n                'category': str(row.get('参赛者组别', row.get('组别', ''))).strip(),\n                'teacher': str(row.get('指导老师', '')).strip(),\n                'organization': str(row.get('推送单位学校', row.get('推送单位', ''))).strip(),\n                'url': video_url,\n                'status': '有链接' if video_url else '无链接',\n                'cached_file': None\n            }\n            \n    def populate_tree(self):\n        """填充作品列表"""\n        # 清空现有数据\n        for item in self.tree.get_children():\n            self.tree.delete(item)\n            \n        # 添加数据\n        for work_id, work in self.work_data.items():\n            self.tree.insert('', tk.END, iid=work_id, values=(\n                work['name'],\n                work['participant'],\n                work['category'],\n                work['teacher'],\n                work['organization'],\n                work['status']\n            ))\n            \n    def filter_works(self, event=None):\n        """过滤作品列表"""\n        search_text = self.search_var.get().lower()\n        \n        # 清空现有显示\n        for item in self.tree.get_children():\n            self.tree.delete(item)\n            \n        # 重新添加匹配的项目\n        for work_id, work in self.work_data.items():\n            if (not search_text or \n                search_text in work['name'].lower() or \n                search_text in work['participant'].lower() or\n                search_text in work['organization'].lower()):\n                \n                self.tree.insert('', tk.END, iid=work_id, values=(\n                    work['name'],\n                    work['participant'],\n                    work['category'],\n                    work['teacher'],\n                    work['organization'],\n                    work['status']\n                ))\n                \n    def play_first_match(self, event=None):\n        """播放第一个匹配的作品"""\n        children = self.tree.get_children()\n        if children:\n            self.tree.selection_set(children[0])\n            self.play_selected()\n        else:\n            messagebox.showinfo(\"提示\", \"没有找到匹配的作品\")\n            \n    def play_selected(self, event=None):\n        """播放选中的作品"""\n        selection = self.tree.selection()\n        if not selection:\n            messagebox.showinfo(\"提示\", \"请先选择一个作品\")\n            return\n            \n        work_id = selection[0]\n        work = self.work_data.get(work_id)\n        \n        if not work or not work['url']:\n            messagebox.showinfo(\"提示\", \"该作品没有视频链接\")\n            return\n            \n        self.add_log(f\"准备播放: {work['name']}\")\n        \n        # 根据播放模式处理\n        if self.play_mode.get() == \"browser\" or self.media_manager.is_video_platform_url(work['url']):\n            # 浏览器播放\n            self.player.open_url_in_browser(work['url'])\n        else:\n            # 下载后播放\n            threading.Thread(target=self._download_and_play, args=(work,), daemon=True).start()\n            \n    def _download_and_play(self, work):\n        """下载并播放（在后台线程中执行）"""\n        try:\n            self.update_status(f\"正在下载: {work['name']}\")\n            \n            cached_file = self.media_manager.try_download_video(work['url'], work['name'])\n            \n            if cached_file:\n                work['cached_file'] = cached_file\n                work['status'] = '已缓存'\n                \n                # 更新界面\n                self.root.after(0, lambda: self.update_work_status(work['id'], '已缓存'))\n                \n                # 播放文件\n                self.root.after(0, lambda: self.player.play_file(cached_file))\n                self.root.after(0, lambda: self.update_status(\"播放中\"))\n            else:\n                # 下载失败，尝试浏览器播放\n                self.root.after(0, lambda: messagebox.showinfo(\n                    \"提示\", f\"无法下载视频文件，将在浏览器中打开\\n\\n作品: {work['name']}\"))\n                self.root.after(0, lambda: self.player.open_url_in_browser(work['url']))\n                \n        except Exception as e:\n            self.add_log(f\"播放失败: {e}\")\n            self.root.after(0, lambda: self.update_status(\"播放失败\"))\n            \n    def open_in_browser(self):\n        """在浏览器中打开选中的作品"""\n        selection = self.tree.selection()\n        if not selection:\n            return\n            \n        work_id = selection[0]\n        work = self.work_data.get(work_id)\n        \n        if work and work['url']:\n            self.player.open_url_in_browser(work['url'])\n        else:\n            messagebox.showinfo(\"提示\", \"该作品没有视频链接\")\n            \n    def download_selected(self):\n        """下载选中的作品"""\n        selection = self.tree.selection()\n        if not selection:\n            return\n            \n        work_id = selection[0]\n        work = self.work_data.get(work_id)\n        \n        if not work or not work['url']:\n            messagebox.showinfo(\"提示\", \"该作品没有视频链接\")\n            return\n            \n        threading.Thread(target=self._download_work, args=(work,), daemon=True).start()\n        \n    def _download_work(self, work):\n        """下载作品（后台线程）"""\n        try:\n            self.update_status(f\"正在下载: {work['name']}\")\n            \n            cached_file = self.media_manager.try_download_video(work['url'], work['name'])\n            \n            if cached_file:\n                work['cached_file'] = cached_file\n                work['status'] = '已缓存'\n                self.root.after(0, lambda: self.update_work_status(work['id'], '已缓存'))\n                self.add_log(f\"下载完成: {work['name']}\")\n            else:\n                self.add_log(f\"下载失败: {work['name']}\")\n                \n            self.root.after(0, lambda: self.update_status(\"就绪\"))\n            \n        except Exception as e:\n            self.add_log(f\"下载出错: {e}\")\n            \n    def open_file_location(self):\n        \"\"\"打开文件位置\"\"\"\n        selection = self.tree.selection()\n        if not selection:\n            return\n            \n        work_id = selection[0]\n        work = self.work_data.get(work_id)\n        \n        if work and work.get('cached_file') and os.path.exists(work['cached_file']):\n            file_path = work['cached_file']\n            if sys.platform.startswith('win'):\n                subprocess.run(['explorer', '/select,', file_path])\n            elif sys.platform.startswith('darwin'):\n                subprocess.run(['open', '-R', file_path])\n            else:\n                subprocess.run(['xdg-open', os.path.dirname(file_path)])\n        else:\n            messagebox.showinfo(\"提示\", \"文件未下载或不存在\")\n            \n    def update_work_status(self, work_id, status):\n        \"\"\"更新作品状态\"\"\"\n        if work_id in self.work_data:\n            self.work_data[work_id]['status'] = status\n            \n            # 更新树视图中的状态\n            try:\n                item = self.tree.item(work_id)\n                values = list(item['values'])\n                values[5] = status  # 状态列\n                self.tree.item(work_id, values=values)\n            except:\n                pass\n                \n    def show_context_menu(self, event):\n        \"\"\"显示右键菜单\"\"\"\n        try:\n            self.context_menu.tk_popup(event.x_root, event.y_root)\n        finally:\n            self.context_menu.grab_release()\n            \n    def on_selection_change(self, event=None):\n        \"\"\"选择改变时更新信息显示\"\"\"\n        selection = self.tree.selection()\n        if not selection:\n            return\n            \n        work_id = selection[0]\n        work = self.work_data.get(work_id)\n        \n        if work:\n            info_text = f\"\"\"作品信息\n{'='*30}\n\n作品名称: {work['name']}\n参赛者: {work['participant']}\n组别: {work['category']}\n指导老师: {work['teacher']}\n推送单位: {work['organization']}\n\n视频链接: {work['url'][:50] + '...' if len(work['url']) > 50 else work['url']}\n状态: {work['status']}\n\n{'='*30}\n双击播放 | 右键更多选项\"\"\"\n            \n            self.info_text.config(state=tk.NORMAL)\n            self.info_text.delete(1.0, tk.END)\n            self.info_text.insert(1.0, info_text)\n            self.info_text.config(state=tk.DISABLED)\n            \n    def sort_column(self, col):\n        \"\"\"排序列\"\"\"\n        # 简单的排序实现\n        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]\n        items.sort()\n        \n        for index, (val, child) in enumerate(items):\n            self.tree.move(child, '', index)\n            \n    def open_cache_dir(self):\n        \"\"\"打开缓存目录\"\"\"\n        cache_dir = os.path.abspath(self.media_manager.cache_dir)\n        if not os.path.exists(cache_dir):\n            os.makedirs(cache_dir)\n            \n        if sys.platform.startswith('win'):\n            os.startfile(cache_dir)\n        elif sys.platform.startswith('darwin'):\n            subprocess.run(['open', cache_dir])\n        else:\n            subprocess.run(['xdg-open', cache_dir])\n            \n    def clear_cache(self):\n        \"\"\"清理缓存\"\"\"\n        result = messagebox.askyesno(\"确认\", \"确定要清理所有缓存文件吗？\")\n        if result:\n            try:\n                cache_dir = self.media_manager.cache_dir\n                if os.path.exists(cache_dir):\n                    shutil.rmtree(cache_dir)\n                    os.makedirs(cache_dir)\n                    \n                self.media_manager.cached_files = {}\n                self.media_manager.save_cache_info()\n                \n                # 更新作品状态\n                for work in self.work_data.values():\n                    if work['status'] == '已缓存':\n                        work['status'] = '有链接'\n                        work['cached_file'] = None\n                        \n                self.populate_tree()\n                self.add_log(\"缓存已清理\")\n                messagebox.showinfo(\"完成\", \"缓存清理完成\")\n                \n            except Exception as e:\n                error_msg = f\"清理缓存失败: {e}\"\n                self.add_log(error_msg)\n                messagebox.showerror(\"错误\", error_msg)\n                \n    def show_about(self):\n        \"\"\"显示关于信息\"\"\"\n        about_text = \"\"\"CSV作品播放器 v2.0 (高级版)\n\n功能特点:\n• 智能CSV文件读取（支持多种编码）\n• 在线视频播放（浏览器模式）\n• 本地缓存下载播放\n• 系统播放器集成\n• 无需外部依赖\n\n使用说明:\n1. 点击"导入CSV文件"选择数据文件\n2. 在作品列表中选择要播放的作品\n3. 双击播放或使用右键菜单\n4. 支持搜索过滤功能\n\n技术特点:\n• 纯Python标准库实现\n• 跨平台兼容（Windows/Mac/Linux）\n• 智能播放模式选择\n• 完善的错误处理\n\n作者: CodeBuddy\n版本: 2.0\"\"\"\n        \n        messagebox.showinfo(\"关于\", about_text)\n        \n    def add_log(self, message):\n        \"\"\"添加日志\"\"\"\n        timestamp = time.strftime('%H:%M:%S')\n        log_message = f\"[{timestamp}] {message}\\n\"\n        \n        self.root.after(0, lambda: self._update_log_display(log_message))\n        \n    def _update_log_display(self, message):\n        \"\"\"更新日志显示（主线程）\"\"\"\n        self.log_text.config(state=tk.NORMAL)\n        self.log_text.insert(tk.END, message)\n        self.log_text.see(tk.END)\n        self.log_text.config(state=tk.DISABLED)\n        \n        # 限制日志长度\n        lines = self.log_text.get(1.0, tk.END).split('\\n')\n        if len(lines) > 1000:\n            self.log_text.config(state=tk.NORMAL)\n            self.log_text.delete(1.0, f\"{len(lines)-500}.0\")\n            self.log_text.config(state=tk.DISABLED)\n            \n    def update_progress(self, value):\n        \"\"\"更新进度条\"\"\"\n        self.root.after(0, lambda: self.progress_var.set(value))\n        \n    def update_status(self, message):\n        \"\"\"更新状态\"\"\"\n        self.root.after(0, lambda: self.status_label.config(text=message))\n        \n    def run(self):\n        \"\"\"运行应用程序\"\"\"\n        self.add_log(\"CSV作品播放器 v2.0 启动成功\")\n        self.add_log(\"提示: 高级版支持智能播放和本地缓存\")\n        self.add_log(\"建议: 视频平台链接使用浏览器播放模式\")\n        \n        # 设置窗口关闭事件\n        self.root.protocol(\"WM_DELETE_WINDOW\", self.on_closing)\n        \n        self.root.mainloop()\n        \n    def on_closing(self):\n        \"\"\"程序关闭时的清理工作\"\"\"\n        self.add_log(\"程序正在关闭...\")\n        self.root.destroy()\n\ndef main():\n    \"\"\"主函数\"\"\"\n    try:\n        app = AdvancedCSVPlayer()\n        app.run()\n    except Exception as e:\n        print(f\"程序启动失败: {e}\")\n        messagebox.showerror(\"错误\", f\"程序启动失败:\\n{e}\")\n\nif __name__ == \"__main__\":\n    main()