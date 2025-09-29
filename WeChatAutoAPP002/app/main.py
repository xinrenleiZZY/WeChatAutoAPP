import sys
import os
# from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
from app.ui_main import MainWindow
from app.wechat_auto import WeChatAuto, ConfigManager
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QTabWidget, QLabel, QLineEdit, QTextEdit, QPushButton,
                           QGroupBox, QProgressBar, QSplitter, QFormLayout,
                           QDoubleSpinBox, QCheckBox, QSpinBox, QFileDialog, 
                           QScrollArea,QApplication, QMessageBox
                           )

class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished_signal.emit(result)
        except Exception as e:
            self.log_signal.emit(f"错误: {str(e)}")
            self.finished_signal.emit(False)

class WeChatApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = MainWindow()
        self.config = ConfigManager.load_config()
        self.wechat_auto = WeChatAuto(self.config)
        self.setup_signals()
        self.load_config_to_ui()
        
    def setup_signals(self):
        """设置信号与槽连接"""
        # 单发送按钮
        self.window.send_single_btn.clicked.connect(self.send_single_message)
        
        # 批量发送按钮
        self.window.send_batch_btn.clicked.connect(self.send_batch_messages)
        
        # 设置相关
        self.window.wechat_path_btn.clicked.connect(self.browse_wechat_path)
        self.window.template_path_btn.clicked.connect(self.browse_template_path)
        self.window.friends_file_btn.clicked.connect(self.browse_friends_file)
        self.window.save_settings_btn.clicked.connect(self.save_settings)
        
        # 绑定自动化模块的信号
        self.wechat_auto.status_updated.connect(self.update_log)
        self.wechat_auto.progress_updated.connect(self.update_progress)
    
    def load_config_to_ui(self):
        """加载配置到界面"""
        self.window.wechat_path_input.setText(self.config["wechat_path"])
        self.window.template_path_input.setText(self.config["template_path"])
        self.window.friends_file_input.setText(self.config["friends_file"])
        self.window.pyautogui_pause.setValue(self.config["pyautogui_pause"])
        self.window.use_hybrid_mode.setChecked(self.config["use_hybrid_mode"])
        self.window.auto_login_wait_time.setValue(self.config["auto_login_wait_time"])
        self.window.retry_times.setValue(self.config["retry_times"])
        self.window.confidence.setValue(self.config["confidence"])
        
        # 更新批量发送页面的好友文件信息
        self.window.friends_file_info.setText(
            f"当前好友文件: {self.config['friends_file']}"
        )
    
    def save_settings(self):
        """保存设置到配置文件"""
        new_config = {
            "wechat_path": self.window.wechat_path_input.text(),
            "template_path": self.window.template_path_input.text(),
            "friends_file": self.window.friends_file_input.text(),
            "pyautogui_pause": self.window.pyautogui_pause.value(),
            "use_hybrid_mode": self.window.use_hybrid_mode.isChecked(),
            "auto_login_wait_time": self.window.auto_login_wait_time.value(),
            "retry_times": self.window.retry_times.value(),
            "confidence": self.window.confidence.value()
        }
        
        if ConfigManager.save_config(new_config):
            self.config = new_config
            self.wechat_auto = WeChatAuto(new_config)
            self.wechat_auto.status_updated.connect(self.update_log)
            self.wechat_auto.progress_updated.connect(self.update_progress)
            self.window.statusBar().showMessage("设置保存成功")
            self.window.friends_file_info.setText(
                f"当前好友文件: {self.config['friends_file']}"
            )
        else:
            self.window.statusBar().showMessage("设置保存失败")
    
    def browse_wechat_path(self):
        try:
            path, _ = QFileDialog.getOpenFileName(
                self.window, "选择微信程序", "", "可执行文件 (*.exe)"
            )
            if path:
                self.window.wechat_path_input.setText(path)
        except Exception as e:
            self.show_error(f"选择微信程序失败: {str(e)}")  
    
    def browse_template_path(self):
        path = QFileDialog.getExistingDirectory(
            self.window, "选择模板目录"
        )
        if path:
            self.window.template_path_input.setText(path)
    
    def browse_friends_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self.window, "选择好友文件", "", "文本文件 (*.txt)"
        )
        if path:
            self.window.friends_file_input.setText(path)
    
    def send_single_message(self):
        friend_name = self.window.friend_input.text().strip()
        message = self.window.msg_editor.toPlainText().strip()
        
        if not friend_name:
            self.show_error("请输入好友名称")
            return
            
        if not message:
            self.show_error("请输入消息内容")
            return
        
        self.window.send_single_btn.setEnabled(False)
        self.window.log_text.clear()
        
        self.worker = WorkerThread(
            self.wechat_auto.send_wechat_message,
            friend_name, message
        )
        self.worker.log_signal.connect(self.window.log_text.append)
        self.worker.finished_signal.connect(lambda: self.window.send_single_btn.setEnabled(True))
        self.worker.start()
    
    def send_batch_messages(self):
        message = self.window.batch_msg_editor.toPlainText().strip()
        if not message:
            self.show_error("请输入消息内容")
            return
        # 读取好友列表文件
        try:
            with open(self.config["friends_file"], 'r', encoding='utf-8') as f:
                friend_list = [line.strip() for line in f if line.strip()]
            
            if not friend_list:
                self.show_error("好友列表为空，请检查好友文件")
                return
        except Exception as e:
            self.show_error(f"读取好友文件失败: {str(e)}")
            return
        self.window.send_batch_btn.setEnabled(False)
        self.window.batch_log_text.clear()
        self.window.batch_progress_bar.setValue(0)
        
        # 设置当前消息
        self.wechat_auto.current_message = message
        
        # 启动工作线程时传递好友列表和消息
        self.batch_worker = WorkerThread(
            self.wechat_auto.send_batch_messages,
            friend_list,  # 第一个参数：好友列表
            message       # 第二个参数：消息内容
        )
        self.batch_worker.log_signal.connect(self.window.batch_log_text.append)
        self.batch_worker.progress_signal.connect(self.window.batch_progress_bar.setValue)
        self.batch_worker.finished_signal.connect(lambda: self.window.send_batch_btn.setEnabled(True))
        self.batch_worker.start()
    
    def update_log(self, message):
        """根据当前激活的标签页更新对应日志"""
        current_tab = self.window.tabs.currentIndex()
        if current_tab == 0:  # 单发送
            self.window.log_text.append(message)
        elif current_tab == 1:  # 批量发送
            self.window.batch_log_text.append(message)
    
    def update_progress(self, value):
        """根据当前激活的标签页更新对应进度条"""
        current_tab = self.window.tabs.currentIndex()
        if current_tab == 0:  # 单发送
            self.window.progress_bar.setValue(value)
        elif current_tab == 1:  # 批量发送
            self.window.batch_progress_bar.setValue(value)
    
    def show_error(self, message):
        QMessageBox.critical(self.window, "错误", message)
    
    def run(self):
        self.window.show()
        sys.exit(self.app.exec_())

def main():
    app = WeChatApp()
    app.run()

if __name__ == "__main__":
    main()