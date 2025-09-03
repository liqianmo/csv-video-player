#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV作品播放器
支持导入CSV文件，显示作品列表，点击播放视频作品
"""

import sys
import os
import csv
import webbrowser
from urllib.parse import urlparse


try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                                QWidget, QPushButton, QTableWidget, QTableWidgetItem, 
                                QFileDialog, QMessageBox, QLabel, QLineEdit, QProgressBar,
                                QHeaderView, QSplitter, QTextEdit, QGroupBox, QGridLayout,
                                QFrame, QStatusBar)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QUrl
    from PyQt5.QtGui import QFont, QIcon, QPalette, QColor
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
except ImportError:
    print("PyQt5未安装，请运行: pip install PyQt5")
    sys.exit(1)





class CSVPlayer(QMainWindow):
    """CSV作品播放器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.csv_data = []
        
        self.init_ui()
        self.setup_media_player()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("CSV作品播放器 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin: 3px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧作品列表
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧视频播放区域
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([800, 600])
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪 - 请导入CSV文件")
        
    def create_control_panel(self):
        """创建顶部控制面板"""
        group = QGroupBox("文件操作")
        layout = QHBoxLayout(group)
        
        # 导入CSV按钮
        self.import_btn = QPushButton("📁 导入CSV文件")
        self.import_btn.clicked.connect(self.import_csv)
        layout.addWidget(self.import_btn)
        
        # 文件信息标签
        self.file_info_label = QLabel("未导入文件")
        self.file_info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.file_info_label)
        
        layout.addStretch()
        
        # 搜索框
        search_label = QLabel("搜索:")
        layout.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入作品名称或参赛者姓名...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedWidth(300)
        layout.addWidget(self.search_input)
        
        return group
        
    def create_left_panel(self):
        """创建左侧作品列表面板"""
        group = QGroupBox("作品列表")
        layout = QVBoxLayout(group)
        
        # 作品表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "作品名称", "参赛者", "组别", "指导老师", "推送单位", "资料链接"
        ])
        
        # 设置表格属性
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.resizeSection(0, 200)  # 作品名称
        header.resizeSection(1, 120)  # 参赛者
        header.resizeSection(2, 100)  # 组别
        header.resizeSection(3, 120)  # 指导老师
        header.resizeSection(4, 150)  # 推送单位
        
        # 双击播放
        self.table.cellDoubleClicked.connect(self.play_video)
        
        layout.addWidget(self.table)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("▶️ 播放选中作品")
        self.play_btn.clicked.connect(self.play_selected_video)
        self.play_btn.setEnabled(False)
        button_layout.addWidget(self.play_btn)
        
        self.open_link_btn = QPushButton("🔗 在浏览器中打开")
        self.open_link_btn.clicked.connect(self.open_in_browser)
        self.open_link_btn.setEnabled(False)
        button_layout.addWidget(self.open_link_btn)
        
        layout.addLayout(button_layout)
        
        return group
        
    def create_right_panel(self):
        """创建右侧视频播放面板"""
        group = QGroupBox("视频播放器")
        layout = QVBoxLayout(group)
        
        # 视频显示区域
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(400)
        self.video_widget.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_widget)
        
        # 播放控制
        control_layout = QHBoxLayout()
        
        self.play_pause_btn = QPushButton("▶️")
        self.play_pause_btn.setFixedSize(50, 30)
        self.play_pause_btn.clicked.connect(self.toggle_playback)
        self.play_pause_btn.setEnabled(False)
        control_layout.addWidget(self.play_pause_btn)
        
        self.stop_btn = QPushButton("⏹️")
        self.stop_btn.setFixedSize(50, 30)
        self.stop_btn.clicked.connect(self.stop_playback)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # 作品信息显示
        self.info_text = QTextEdit()
        self.info_text.setMaximumHeight(150)
        self.info_text.setReadOnly(True)
        self.info_text.setPlaceholderText("选择一个作品查看详细信息...")
        layout.addWidget(self.info_text)
        
        return group
        
    def setup_media_player(self):
        """设置媒体播放器"""
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        
        # 连接播放器信号
        self.media_player.stateChanged.connect(self.on_media_state_changed)
        self.media_player.error.connect(self.on_media_error)
        
    def import_csv(self):
        """导入CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV files (*.csv)")
        
        if file_path:
            try:
                self.load_csv_data(file_path)
                self.populate_table()
                self.file_info_label.setText(f"已导入: {os.path.basename(file_path)} ({len(self.csv_data)} 条记录)")
                self.status_bar.showMessage(f"成功导入 {len(self.csv_data)} 条作品记录")
                self.play_btn.setEnabled(True)
                self.open_link_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入CSV文件失败:\n{str(e)}")
                
    def load_csv_data(self, file_path):
        """加载CSV数据"""
        self.csv_data = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # 只保留有作品名称和资料链接的记录
                if row.get('作品名称') and row.get('资料链接'):
                    self.csv_data.append(row)
                    
    def populate_table(self):
        """填充表格数据"""
        self.table.setRowCount(len(self.csv_data))
        
        for row, data in enumerate(self.csv_data):
            self.table.setItem(row, 0, QTableWidgetItem(data.get('作品名称', '')))
            self.table.setItem(row, 1, QTableWidgetItem(data.get('身份证名字', '')))
            self.table.setItem(row, 2, QTableWidgetItem(data.get('参赛者组别', '')))
            self.table.setItem(row, 3, QTableWidgetItem(data.get('指导老师', '')))
            self.table.setItem(row, 4, QTableWidgetItem(data.get('推送单位学校', '')))
            self.table.setItem(row, 5, QTableWidgetItem(data.get('资料链接', '')))
            
        # 选择改变时更新信息
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
    def filter_table(self):
        """过滤表格内容"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)
            
    def on_selection_changed(self):
        """选择改变时更新作品信息"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.csv_data):
            data = self.csv_data[current_row]
            
            info_html = f"""
            <h3>{data.get('作品名称', '未知作品')}</h3>
            <p><strong>参赛者:</strong> {data.get('身份证名字', '未知')}</p>
            <p><strong>组别:</strong> {data.get('参赛者组别', '未知')}</p>
            <p><strong>指导老师:</strong> {data.get('指导老师', '无')}</p>
            <p><strong>联系电话:</strong> {data.get('联系电话', '未提供')}</p>
            <p><strong>推送单位:</strong> {data.get('推送单位学校', '未知')}</p>
            <p><strong>资料链接:</strong> <a href="{data.get('资料链接', '')}">{data.get('资料链接', '')}</a></p>
            """
            
            self.info_text.setHtml(info_html)
            
    def play_video(self, row, column):
        """双击播放视频"""
        self.play_selected_video()
        
    def play_selected_video(self):
        """播放选中的视频"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.csv_data):
            video_url = self.csv_data[current_row].get('资料链接', '')
            work_name = self.csv_data[current_row].get('作品名称', '未知作品')
            
            if video_url:
                self.play_online_video(video_url, work_name)
            else:
                QMessageBox.warning(self, "警告", "该作品没有有效的视频链接")
                
    def play_online_video(self, url, work_name):
        """直接播放在线视频"""
        if not url.startswith('http'):
            QMessageBox.warning(self, "警告", "无效的视频链接")
            return
            
        self.status_bar.showMessage(f"正在加载视频: {work_name}")
        
        try:
            # 检查 URL 格式
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                QMessageBox.warning(self, "警告", "视频链接格式不正确")
                return
            
            # 对于某些视频平台，直接在浏览器中打开可能更好
            if any(platform in url.lower() for platform in ['bilibili', 'youtube', 'youku', 'iqiyi']):
                reply = QMessageBox.question(
                    self, "播放选择", 
                    f"检测到视频平台链接，建议在浏览器中打开。\n\n是否在浏览器中打开？\n\n点击 'No' 尝试直接播放",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    webbrowser.open(url)
                    return
            
            # 尝试直接播放
            media_content = QMediaContent(QUrl(url))
            self.media_player.setMedia(media_content)
            self.media_player.play()
            
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            
            self.status_bar.showMessage(f"正在播放: {work_name}")
            
            # 设置超时检查
            QTimer.singleShot(10000, self.check_playback_status)
            
        except Exception as e:
            error_msg = f"无法播放视频:\n{str(e)}\n\n建议:\n1. 检查网络连接\n2. 尝试在浏览器中打开\n3. 确认视频链接有效"
            QMessageBox.critical(self, "播放错误", error_msg)
            self.status_bar.showMessage("播放失败")
        
    def open_in_browser(self):
        """在浏览器中打开视频链接"""
        current_row = self.table.currentRow()
        if current_row >= 0 and current_row < len(self.csv_data):
            video_url = self.csv_data[current_row].get('资料链接', '')
            if video_url:
                webbrowser.open(video_url)
            else:
                QMessageBox.warning(self, "警告", "该作品没有有效的视频链接")
                
    def toggle_playback(self):
        """切换播放/暂停"""
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
            self.play_pause_btn.setText("▶️")
        else:
            self.media_player.play()
            self.play_pause_btn.setText("⏸️")
            
    def stop_playback(self):
        """停止播放"""
        self.media_player.stop()
        self.play_pause_btn.setText("▶️")
        
    def on_media_state_changed(self, state):
        """媒体状态改变"""
        if state == QMediaPlayer.PlayingState:
            self.play_pause_btn.setText("⏸️")
        else:
            self.play_pause_btn.setText("▶️")
            
    def check_playback_status(self):
        """检查播放状态"""
        if self.media_player.state() == QMediaPlayer.StoppedState and self.media_player.mediaStatus() == QMediaPlayer.InvalidMedia:
            QMessageBox.warning(
                self, "播放提示", 
                "视频可能无法直接播放。\n\n可能的原因:\n1. 视频格式不支持\n2. 需要特殊播放器\n3. 网络问题\n\n建议在浏览器中打开链接。"
            )
    
    def on_media_error(self, error):
        """媒体播放错误"""
        error_messages = {
            QMediaPlayer.NoError: "无错误",
            QMediaPlayer.ResourceError: "资源错误 - 视频文件无法访问",
            QMediaPlayer.FormatError: "格式错误 - 不支持的视频格式",
            QMediaPlayer.NetworkError: "网络错误 - 请检查网络连接",
            QMediaPlayer.AccessDeniedError: "访问被拒绝 - 可能需要权限验证",
            QMediaPlayer.ServiceMissingError: "服务缺失 - 缺少必要的多媒体组件"
        }
        
        error_msg = error_messages.get(error, f"未知错误 ({error})")
        detailed_msg = f"视频播放失败:\n\n错误类型: {error_msg}\n详细信息: {self.media_player.errorString()}\n\n解决建议:\n1. 尝试在浏览器中打开\n2. 检查网络连接\n3. 确认视频链接有效"
        
        QMessageBox.critical(self, "播放错误", detailed_msg)
        self.status_bar.showMessage(f"播放失败: {error_msg}")
        
    def closeEvent(self, event):
        """程序关闭事件"""
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("CSV作品播放器")
    app.setApplicationVersion("1.0")
    
    # 设置应用图标（如果有的话）
    # app.setWindowIcon(QIcon('icon.png'))
    
    window = CSVPlayer()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
