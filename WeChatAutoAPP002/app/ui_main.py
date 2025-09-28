from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
                           QGroupBox, QProgressBar, QSplitter, QFormLayout,
                           QDoubleSpinBox, QCheckBox, QSpinBox, QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 窗口基本设置
        self.setWindowTitle("微信自动化助手")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # 设置全局样式
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f5f7fa;
            }
            QTabBar::tab {
                padding: 10px 20px;
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                margin-right: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2c3e50;
                color: white;
            }
            QTabBar::tab:!selected {
                background-color: #eaecef;
                color: #34495e;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-family: 'Microsoft YaHei';
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f6dad;
            }
            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px;
                font-family: 'Microsoft YaHei';
                font-weight: bold;
                color: #2c3e50;
            }
            QLineEdit, QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 6px 10px;
                font-family: 'Microsoft YaHei';
            }
            QProgressBar {
                border-radius: 4px;
                text-align: center;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 顶部标题
        title_label = QLabel("微信自动化助手")
        title_font = QFont("Microsoft YaHei", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("margin: 15px 0px; color: #2c3e50;")
        main_layout.addWidget(title_label)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tab_single = QWidget()  # 单好友发送
        self.tab_batch = QWidget()   # 批量发送
        self.tab_settings = QWidget()   # 设置
        
        self.tabs.addTab(self.tab_single, "单好友发送")
        self.tabs.addTab(self.tab_batch, "批量发送")
        self.tabs.addTab(self.tab_settings, "设置")
        
        # 初始化各标签页
        self.init_single_tab()
        self.init_batch_tab()
        self.init_settings_tab()
        
        main_layout.addWidget(self.tabs)
        
        # 状态栏
        self.statusBar().setStyleSheet("color: #34495e; font-family: 'Microsoft YaHei';")
        self.statusBar().showMessage("就绪")
        
    def init_single_tab(self):
        layout = QHBoxLayout(self.tab_single)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        
        # 好友输入
        friend_group = QGroupBox("好友名称")
        friend_layout = QVBoxLayout()
        self.friend_input = QLineEdit()
        self.friend_input.setPlaceholderText("请输入好友昵称")
        friend_layout.addWidget(self.friend_input)
        friend_group.setLayout(friend_layout)
        left_layout.addWidget(friend_group)
        
        # 消息编辑
        msg_group = QGroupBox("消息内容")
        msg_layout = QVBoxLayout()
        self.msg_editor = QTextEdit()
        self.msg_editor.setPlaceholderText("请输入要发送的消息...")
        msg_layout.addWidget(self.msg_editor)
        msg_group.setLayout(msg_layout)
        left_layout.addWidget(msg_group, 1)
        
        # 发送按钮
        self.send_single_btn = QPushButton("发送消息")
        self.send_single_btn.setMinimumHeight(40)
        self.send_single_btn.setStyleSheet("""
            background-color: #3498db;
            font-size: 15px;
            padding: 10px;
        """)
        left_layout.addWidget(self.send_single_btn)
        
        # 右侧面板 - 日志
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(15)
        
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group, 1)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def init_batch_tab(self):
        layout = QHBoxLayout(self.tab_batch)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(15)
        
        # 好友文件信息
        friends_file_group = QGroupBox("好友文件")
        friends_file_layout = QVBoxLayout()
        self.friends_file_info = QLabel("好友文件路径将从配置中读取")
        self.friends_file_info.setStyleSheet("color: #7f8c8d; font-style: italic;")
        friends_file_layout.addWidget(self.friends_file_info)
        friends_file_group.setLayout(friends_file_layout)
        left_layout.addWidget(friends_file_group)
        
        # 消息编辑
        msg_group = QGroupBox("消息内容")
        msg_layout = QVBoxLayout()
        self.batch_msg_editor = QTextEdit()
        self.batch_msg_editor.setPlaceholderText("请输入要发送的消息...")
        msg_layout.addWidget(self.batch_msg_editor)
        msg_group.setLayout(msg_layout)
        left_layout.addWidget(msg_group, 1)
        
        # 发送按钮
        self.send_batch_btn = QPushButton("批量发送")
        self.send_batch_btn.setMinimumHeight(40)
        self.send_batch_btn.setStyleSheet("""
            background-color: #2ecc71;
            font-size: 15px;
            padding: 10px;
        """)
        left_layout.addWidget(self.send_batch_btn)
        
        # 右侧面板 - 日志
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(15)
        
        log_group = QGroupBox("操作日志")
        log_layout = QVBoxLayout()
        self.batch_log_text = QTextEdit()
        self.batch_log_text.setReadOnly(True)
        log_layout.addWidget(self.batch_log_text)
        log_group.setLayout(log_layout)
        right_layout.addWidget(log_group, 1)
        
        # 进度条
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)
        right_layout.addWidget(self.batch_progress_bar)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
    
    def init_settings_tab(self):
        layout = QVBoxLayout(self.tab_settings)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建滚动区域
        from PyQt5.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")
        
        settings_widget = QWidget()
        settings_layout = QFormLayout(settings_widget)
        settings_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        settings_layout.setSpacing(15)
        settings_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # 微信路径设置
        self.wechat_path_input = QLineEdit()
        self.wechat_path_btn = QPushButton("浏览...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.wechat_path_input)
        path_layout.addWidget(self.wechat_path_btn)
        settings_layout.addRow("微信路径:", path_layout)
        
        # 模板路径设置
        self.template_path_input = QLineEdit()
        self.template_path_btn = QPushButton("浏览...")
        tpl_layout = QHBoxLayout()
        tpl_layout.addWidget(self.template_path_input)
        tpl_layout.addWidget(self.template_path_btn)
        settings_layout.addRow("模板路径:", tpl_layout)
        
        # 好友文件路径
        self.friends_file_input = QLineEdit()
        self.friends_file_btn = QPushButton("浏览...")
        friends_layout = QHBoxLayout()
        friends_layout.addWidget(self.friends_file_input)
        friends_layout.addWidget(self.friends_file_btn)
        settings_layout.addRow("好友文件:", friends_layout)
        
        # 其他设置
        self.pyautogui_pause = QDoubleSpinBox()
        self.pyautogui_pause.setRange(0.1, 2.0)
        self.pyautogui_pause.setSingleStep(0.1)
        settings_layout.addRow("操作延迟(秒):", self.pyautogui_pause)
        
        self.use_hybrid_mode = QCheckBox()
        self.use_hybrid_mode.setChecked(True)
        settings_layout.addRow("使用混合模式:", self.use_hybrid_mode)
        
        self.auto_login_wait_time = QSpinBox()
        self.auto_login_wait_time.setRange(1, 30)
        settings_layout.addRow("登录等待时间(秒):", self.auto_login_wait_time)
        
        self.retry_times = QSpinBox()
        self.retry_times.setRange(1, 5)
        settings_layout.addRow("重试次数:", self.retry_times)
        
        self.confidence = QDoubleSpinBox()
        self.confidence.setRange(0.5, 1.0)
        self.confidence.setSingleStep(0.05)
        settings_layout.addRow("识别置信度:", self.confidence)
        
        # 保存按钮
        self.save_settings_btn = QPushButton("保存设置")
        self.save_settings_btn.setMinimumHeight(40)
        self.save_settings_btn.setStyleSheet("""
            background-color: #f39c12;
            font-size: 15px;
        """)
        settings_layout.addRow("", self.save_settings_btn)
        
        scroll_area.setWidget(settings_widget)
        layout.addWidget(scroll_area)