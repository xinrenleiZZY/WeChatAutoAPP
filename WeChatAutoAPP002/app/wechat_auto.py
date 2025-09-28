import pyautogui
import pygetwindow as gw
import time
import sys
import os
import json
from PIL import Image
import pyperclip
import importlib.util
import psutil
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
import cv2
import numpy as np
# 在WeChatAuto类中添加信号支持
from PyQt5.QtCore import QObject, pyqtSignal

# 配置文件路径
CONFIG_FILE = "wechat_config.json"
DEFAULT_CONFIG = {
    "wechat_path": "D:\\天帝殿\\Weixin\\Weixin.exe",
    "template_path": "wechat_templates",
    "friends_file": "friends.txt",
    "pyautogui_pause": 0.5,
    "use_hybrid_mode": True,
    "auto_login_wait_time": 5,
    "retry_times": 2,
    "confidence": 0.7
}

class ConfigManager:
    """配置文件管理类"""
    @staticmethod
    def load_config():
        """加载配置文件，不存在则创建默认配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并新的默认配置项（处理配置文件版本更新）
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                ConfigManager.save_config(config)
                return config
            except Exception as e:
                print(f"配置文件加载失败，使用默认配置: {e}")
                return DEFAULT_CONFIG.copy()
        else:
            ConfigManager.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config):
        """保存配置到文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"配置保存失败: {e}")
            return False


class WeChatAuto(QObject):
    status_updated = pyqtSignal(str)  # 状态更新信号
    progress_updated = pyqtSignal(int)  # 添加进度更新信号
    def __init__(self, config=None):
        # 加载配置
        super().__init__()
        self.config = config or ConfigManager.load_config()
        self.template_path = self.config["template_path"]
        self.wechat_path = self.config["wechat_path"]
        
        # 初始化配置
        self.use_hybrid_mode = self.config["use_hybrid_mode"]
        self.window_coordinates = {}  # 存储窗口坐标信息
        self.status_callback = None  # 状态回调函数，用于UI反馈
        
        self.create_template_dir()
        # 检查必要的库是否安装
        self.check_dependencies()
        # 配置pyautogui
        pyautogui.PAUSE = self.config["pyautogui_pause"]  # 每个操作后的暂停时间
        pyautogui.FAILSAFE = True  # 启用安全模式

    def set_status_callback(self, callback):
        """设置状态回调函数，用于向UI反馈进度"""
        self.status_callback = callback
    
    def _update_status(self, message):
        """更新状态，通过回调函数通知UI"""
        if self.status_callback:
            self.status_callback(message)
        print(message)
    
    def check_dependencies(self):
        """检查必要的依赖库是否安装"""
        required_libs = {
            "cv2": "opencv-python",
            "pygetwindow": "pygetwindow",
            "pyautogui": "pyautogui"
        }
        
        missing = []
        for lib, pkg in required_libs.items():
            if importlib.util.find_spec(lib) is None:
                missing.append(pkg)
                
        if missing:
            msg = f"缺少必要的库，请先安装：\npip install {' '.join(missing)}"
            self._update_status(msg)
            sys.exit(1)
            
        # 特别检查OpenCV是否可用
        self.opencv_available = importlib.util.find_spec("cv2") is not None
            
    def create_template_dir(self):
        """创建模板图片目录，包括深色模式(dark)和浅色模式(light)子目录"""
        if not os.path.exists(self.template_path):
            os.makedirs(self.template_path)
            self._update_status(f"已创建模板主目录: {self.template_path}")
            
            # 创建浅色模式子目录(light)
            light_mode_path = os.path.join(self.template_path, "light")
            os.makedirs(light_mode_path)
            self._update_status(f"已创建浅色模式目录: {light_mode_path}")
            
            # 创建深色模式子目录(dark)
            dark_mode_path = os.path.join(self.template_path, "dark")
            os.makedirs(dark_mode_path)
            self._update_status(f"已创建深色模式目录: {dark_mode_path}")
            
            self._update_status("请将浅色模式界面元素图片放入light子目录，深色模式放入dark子目录")
    
    def get_wechat_window_info(self):
        """获取微信窗口信息"""
        try:
            wechat_windows = gw.getWindowsWithTitle('微信')
            if wechat_windows:
                win = wechat_windows[0]
                self.window_coordinates = {
                    'left': win.left,
                    'top': win.top,
                    'width': win.width,
                    'height': win.height,
                    'right': win.left + win.width,
                    'bottom': win.top + win.height
                }
                return True
            return False
        except Exception as e:
            self._update_status(f"获取窗口信息失败: {e}")
            return False
    
    def click_relative_position(self, rel_x, rel_y, description=""):
        """点击相对窗口位置"""
        if not self.window_coordinates:
            if not self.get_wechat_window_info():
                return False
        
        abs_x = self.window_coordinates['left'] + int(self.window_coordinates['width'] * rel_x)
        abs_y = self.window_coordinates['top'] + int(self.window_coordinates['height'] * rel_y)
        
        self._update_status(f"点击 {description}: 相对位置({rel_x:.2f}, {rel_y:.2f}) -> 绝对位置({abs_x}, {abs_y})")
        pyautogui.moveTo(abs_x, abs_y, duration=0.3)
        pyautogui.click()
        time.sleep(0.5)
        return True
            
    def take_screenshot(self, region_name, region=None, is_dark_mode=False):
        """截取指定区域的屏幕截图，用于制作模板"""
        try:
            # 根据模式选择子目录
            mode_dir = "dark" if is_dark_mode else "light"
            full_template_path = os.path.join(self.template_path, mode_dir)
            os.makedirs(full_template_path, exist_ok=True)  # 确保目录存在

            if region:
                # 确保区域有效
                screen_width, screen_height = pyautogui.size()
                if (region[0] + region[2] > screen_width or 
                    region[1] + region[3] > screen_height):
                    self._update_status("警告：截图区域超出屏幕范围，将截取全屏")
                    screenshot = pyautogui.screenshot()
                else:
                    screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
                
            # 修正保存路径：存入对应模式的子目录（light/dark）
            filename = os.path.join(full_template_path, f"{region_name}.png")
            screenshot.save(filename)
            self._update_status(f"已保存截图: {filename}")
            return filename
        except Exception as e:
            self._update_status(f"截图失败: {e}")
            return None
    
    def advanced_locate_element(self, template_name, confidence=None, retry_times=None):
        """高级图像识别定位 - 多尺度+特征匹配"""
        confidence = confidence or self.config["confidence"]
        retry_times = retry_times or self.config["retry_times"]
        
        if not self.opencv_available:
            return self.locate_element(template_name, confidence, retry_times)
            
        modes = ["light", "dark"]
        template_files = [
            os.path.join(self.template_path, mode, f"{template_name}.png") 
            for mode in modes
        ]
        
        valid_templates = [f for f in template_files if os.path.exists(f)]
        if not valid_templates:
            self._update_status(f"模板文件不存在: {template_files}")
            return None
        
        for template_file in valid_templates:
            # 尝试多尺度匹配
            result = self.multi_scale_template_match(template_file, confidence)
            if result:
                mode_used = "深色" if "dark" in template_file else "浅色"
                self._update_status(f"✓ 多尺度匹配成功定位 {template_name}（{mode_used}模式）")
                return result
            
            # 尝试特征匹配
            result = self.feature_based_match(template_file)
            if result:
                mode_used = "深色" if "dark" in template_file else "浅色"
                self._update_status(f"✓ 特征匹配成功定位 {template_name}（{mode_used}模式）")
                return result
        
        return None
    
    def multi_scale_template_match(self, template_path, confidence=0.7):
        """多尺度模板匹配"""
        try:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            
            scales = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
            best_match = None
            best_confidence = 0
            
            for scale in scales:
                new_w = int(template.shape[1] * scale)
                new_h = int(template.shape[0] * scale)
                if new_w < 20 or new_h < 20:
                    continue
                    
                resized_template = cv2.resize(template, (new_w, new_h))
                result = cv2.matchTemplate(screen_gray, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence and max_val > confidence:
                    best_confidence = max_val
                    x, y = max_loc
                    best_match = type('Obj', (), {
                        'left': x, 'top': y, 'width': new_w, 'height': new_h,
                        'confidence': max_val
                    })()
            
            return best_match
        except Exception as e:
            self._update_status(f"多尺度匹配失败: {e}")
            return None
    
    def feature_based_match(self, template_path):
        """基于特征的图像匹配"""
        try:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_gray = cv2.cvtColor(screen_np, cv2.COLOR_RGB2GRAY)
            
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                return None
            
            # 使用ORB特征检测器
            orb = cv2.ORB_create()
            kp1, des1 = orb.detectAndCompute(screen_gray, None)
            kp2, des2 = orb.detectAndCompute(template, None)
            
            if des1 is None or des2 is None:
                return None
            
            # 特征匹配
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            matches = bf.match(des1, des2)
            matches = sorted(matches, key=lambda x: x.distance)
            
            if len(matches) >= 10:
                good_matches = matches[:10]
                avg_distance = sum(m.distance for m in good_matches) / len(good_matches)
                
                if avg_distance < 50:  # 距离越小匹配越好
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches])
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches])
                    
                    M, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
                    if M is not None:
                        h, w = template.shape
                        pts = np.float32([[0,0], [0,h-1], [w-1,h-1], [w-1,0]]).reshape(-1,1,2)
                        dst = cv2.perspectiveTransform(pts, M)
                        
                        x, y, w, h = cv2.boundingRect(dst)
                        return type('Obj', (), {'left': x, 'top': y, 'width': w, 'height': h})()
            
            return None
        except Exception as e:
            self._update_status(f"特征匹配失败: {e}")
            return None
    
    def locate_element(self, template_name, confidence=None, retry_times=None, grayscale=True):
        """使用图像识别定位元素，增加兼容性处理，同时尝试浅色和深色模式模板"""
        confidence = confidence or self.config["confidence"]
        retry_times = retry_times or self.config["retry_times"]
        
        # 如果启用混合模式，使用高级识别
        if self.use_hybrid_mode and self.opencv_available:
            result = self.advanced_locate_element(template_name, confidence, retry_times)
            if result:
                return result
        
        # 回退到原来的方法
        modes = ["light", "dark"]
        template_files = [
            os.path.join(self.template_path, mode, f"{template_name}.png") 
            for mode in modes
        ]
        
        valid_templates = [f for f in template_files if os.path.exists(f)]
        if not valid_templates:
            self._update_status(f"模板文件不存在: {template_files}")
            return None
        
        kwargs = {"grayscale": grayscale}
        if self.opencv_available:
            kwargs["confidence"] = confidence
            
        for i in range(retry_times):
            try:
                element_location = None
                for template_file in valid_templates:
                    element_location = pyautogui.locateOnScreen(template_file, **kwargs)
                    if element_location:
                        mode_used = "深色" if "dark" in template_file else "浅色"
                        self._update_status(f"✓ 基础识别成功定位 {template_name}（{mode_used}模式）")
                        return element_location
                
                # 如果全屏没找到，尝试只在微信窗口内搜索
                wechat_windows = gw.getWindowsWithTitle('微信')
                if wechat_windows:
                    wechat_win = wechat_windows[0]
                    region = (wechat_win.left, wechat_win.top, wechat_win.width, wechat_win.height)
                    for template_file in valid_templates:
                        element_location = pyautogui.locateOnScreen(template_file, region=region,** kwargs)
                        if element_location:
                            mode_used = "深色" if "dark" in template_file else "浅色"
                            self._update_status(f"✓ 窗口内定位 {template_name}（{mode_used}模式）")
                            return element_location
            
                self._update_status(f"第 {i+1} 次尝试定位 {template_name} 失败")
                time.sleep(1)
            except Exception as e:
                self._update_status(f"定位 {template_name} 时出错: {e}")
                time.sleep(1)
                
        self._update_status(f"✗ 无法定位 {template_name}，将尝试坐标定位")
        return None
    
    def hybrid_click(self, template_name, element_type, confidence=None, retry_times=None):
        """混合点击方法：图像识别 + 坐标定位 + 快捷键"""
        confidence = confidence or self.config["confidence"]
        retry_times = retry_times or self.config["retry_times"]
        
        self._update_status(f"尝试混合点击: {template_name} ({element_type})")
        
        # 方法1: 图像识别点击
        element = self.locate_element(template_name, confidence, retry_times)
        if element:
            click_x = element.left + element.width // 2
            click_y = element.top + element.height // 2
            pyautogui.moveTo(click_x, click_y, duration=0.2)
            pyautogui.click()
            time.sleep(0.5)
            self._update_status(f"✓ 图像识别点击成功: {template_name}")
            return True
        
        # 方法2: 坐标定位点击
        if element_type == "search_icon":
            if self.click_relative_position(0.02, 0.05, "搜索图标"):
                self._update_status("✓ 坐标定位搜索图标成功")
                return True
        elif element_type == "message_input":
            if self.click_relative_position(0.15, 0.92, "消息输入框"):
                self._update_status("✓ 坐标定位输入框成功")
                return True
        elif element_type == "send_button":
            # 发送按钮可以用回车替代
            self._update_status("使用回车键发送")
            pyautogui.press('enter')
            return True
        
        # 方法3: 快捷键
        if element_type == "search_icon":
            self._update_status("使用快捷键 Ctrl+F 打开搜索")
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1)
            return True
        
        return False
    
    def kill_wechat(self):
        """关闭所有微信进程，确保干净启动"""
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] in ['WeChat.exe', 'WeChatApp.exe']:
                try:
                    proc.kill()
                    self._update_status(f"已关闭微信进程（PID: {proc.info['pid']}）")
                except Exception as e:
                    self._update_status(f"忽略进程关闭错误：{str(e)}")
        time.sleep(3)

    def activate_wechat(self, wait_login_time=None):
        """激活微信窗口 - 优先使用UIA，失败时使用备选方案"""
        wait_login_time = wait_login_time or self.config["auto_login_wait_time"]
        self._update_status("尝试激活微信窗口...")
        
        # 方法1: 优先使用UIA激活
        try:
            # 尝试连接已运行的微信
            app = Application(backend="uia").connect(title="微信", class_name="Qt51514QWindowIcon")
            main_window = app.window(title="微信", class_name="Qt51514QWindowIcon")
            main_window.wait("ready", timeout=10)
            main_window.set_focus()
            self._update_status("✓ UIA方式激活微信窗口成功")
            
            # 确保窗口前置
            main_window.restore()  # 确保不是最小化
            main_window.set_focus()
            time.sleep(1)
            
            # 更新窗口坐标信息
            self.get_wechat_window_info()
            return True
            
        except ElementNotFoundError:
            self._update_status("未找到运行中的微信窗口，尝试启动新实例...")
        except Exception as e:
            self._update_status(f"UIA激活失败: {e}，尝试备选方案...")
        
        # 方法2: 启动新微信实例
        try:
            self.kill_wechat()
            app = Application(backend="uia").start(self.wechat_path)
            self._update_status(f"请在{wait_login_time}秒内完成微信登录...")
            time.sleep(wait_login_time)
            
            # 尝试连接新启动的微信
            for i in range(3):
                try:
                    app = Application(backend="uia").connect(title="微信", class_name="Qt51514QWindowIcon")
                    main_window = app.window(title="微信", class_name="Qt51514QWindowIcon")
                    main_window.wait("ready", timeout=15)
                    main_window.set_focus()
                    self._update_status("✓ 新微信实例启动并激活成功")
                    self.get_wechat_window_info()
                    return True
                except:
                    time.sleep(2)
            
            self._update_status("微信启动超时，尝试基础激活方式...")
        except Exception as e:
            self._update_status(f"启动微信失败: {e}，尝试基础激活...")
        
        # 方法3: 基础激活方式（备选）
        return self.fallback_activate_wechat()
    
    def fallback_activate_wechat(self):
        """备选激活方案：使用窗口管理和点击"""
        self._update_status("使用备选方案激活微信...")
        
        # 尝试通过窗口标题查找
        wechat_windows = gw.getWindowsWithTitle('微信')
        if wechat_windows:
            try:
                win = wechat_windows[0]
                # 激活窗口
                win.activate()
                time.sleep(1)
                
                # 如果窗口最小化，先恢复
                if win.isMinimized:
                    win.restore()
                    time.sleep(1)
                
                # 点击窗口中央激活
                center_x = win.left + win.width // 2
                center_y = win.top + win.height // 2
                pyautogui.click(center_x, center_y)
                time.sleep(0.5)
                
                self.window_coordinates = {
                    'left': win.left,
                    'top': win.top,
                    'width': win.width,
                    'height': win.height
                }
                self._update_status("✓ 备选方案激活微信成功")
                return True
            except Exception as e:
                self._update_status(f"备选激活失败: {e}")
        
        # 方法4: 最后尝试直接启动
        try:
            os.startfile(self.wechat_path)
            self._update_status("已启动微信，请手动登录后重试")
            return False
        except:
            self._update_status("无法启动微信，请检查路径是否正确")
            return False
    
    def search_and_open_chat(self, friend_name):
        """搜索并打开指定好友的聊天窗口 - 混合方案"""
        self._update_status(f"搜索好友: {friend_name}")
        
        # 确保窗口已激活
        if not self.get_wechat_window_info():
            self._update_status("无法获取微信窗口信息")
            return False
        
        # 方法1: 混合点击搜索图标
        if not self.hybrid_click("search_icon", "search_icon"):
            # 方法2: 直接使用快捷键
            self._update_status("尝试直接使用搜索快捷键")
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1)
        
        # 清空并输入搜索内容
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.3)
        
        pyperclip.copy(friend_name)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)  # 等待搜索结果
        
        # 选择好友
        pyautogui.press('enter')
        time.sleep(1.5)
        
        # 验证是否成功打开聊天窗口
        if self.verify_chat_opened():
            self._update_status("✓ 成功打开聊天窗口")
            return True
        else:
            # 备用选择方法
            self._update_status("尝试备用选择方法")
            pyautogui.press('down')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1.5)
            
            return self.verify_chat_opened()
    
    def verify_chat_opened(self):
        """验证聊天窗口是否成功打开"""
        # 多种验证方式
        checks = [
            lambda: self.locate_element("message_input", confidence=0.6) is not None,
            lambda: self.hybrid_click("message_input", "message_input", retry_times=1),
            lambda: self.get_wechat_window_info() and "聊天" in gw.getActiveWindow().title
        ]
        
        for check in checks:
            try:
                if check():
                    return True
            except:
                continue
        return False
    
    def send_message(self, message):
        """发送消息 - 混合方案"""
        self._update_status("准备发送消息")
        
        # 激活输入框
        if not self.hybrid_click("message_input", "message_input"):
            # 备用方案：直接点击相对位置
            self.click_relative_position(0.15, 0.92, "消息输入框")
        
        # 清空并输入消息
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        time.sleep(0.2)
        
        pyperclip.copy(message)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        # 发送消息
        if not self.hybrid_click("send_button", "send_button"):
            # 备用发送方案
            pyautogui.press('enter')
        
        time.sleep(1)
        self._update_status("✓ 消息发送完成")
        return True
    
    def send_wechat_message(self, friend_name, message):
        """主函数：发送微信消息"""
        self._update_status(f"开始发送消息给 {friend_name}...")
        
        # 激活微信窗口
        if not self.activate_wechat():
            self._update_status("无法激活微信窗口")
            return False
        
        # 搜索并打开聊天窗口
        if not self.search_and_open_chat(friend_name):
            self._update_status("无法打开聊天窗口")
            return False
        
        # 发送消息
        if not self.send_message(message):
            self._update_status("发送消息失败")
            return False
        
        self._update_status(f"✓ 成功发送消息给 {friend_name}")
        return True
    
    def create_templates(self):
        """创建模板图片"""
        self._update_status("\n=== 微信界面元素模板创建向导 ===")
        self._update_status("请按照提示操作，确保微信窗口可见且未被遮挡")
        
        # 先获取窗口信息
        if not self.get_wechat_window_info():
            self._update_status("请先打开微信窗口")
            return
        
        self._update_status("\n===== 请确保微信处于浅色模式 =====")
        input("1. 将鼠标移动到【搜索图标】上，按回车...")
        pos = pyautogui.position()
        search_region = (pos[0]-25, pos[1]-25, 50, 50)  # 更大的区域
        self.take_screenshot("search_icon", search_region)
        
        input("2. 将鼠标移动到【消息输入框】内，按回车...")
        pos = pyautogui.position()
        input_region = (pos[0]-60, pos[1]-20, 120, 40)
        self.take_screenshot("message_input", input_region)
        
        input("3. 将鼠标移动到【发送按钮】上，按回车...")
        pos = pyautogui.position()
        send_region = (pos[0]-25, pos[1]-25, 50, 50)
        self.take_screenshot("send_button", send_region)
        
        self._update_status("\n===== 请切换微信到深色模式 =====")
        input("1. 将鼠标移动到【搜索图标】上，按回车...")
        pos = pyautogui.position()
        search_region = (pos[0]-25, pos[1]-25, 50, 50)
        self.take_screenshot("search_icon", search_region, is_dark_mode=True)
        
        input("2. 将鼠标移动到【消息输入框】内，按回车...")
        pos = pyautogui.position()
        input_region = (pos[0]-60, pos[1]-20, 120, 40)
        self.take_screenshot("message_input", input_region, is_dark_mode=True)
        
        input("3. 将鼠标移动到【发送按钮】上，按回车...")
        pos = pyautogui.position()
        send_region = (pos[0]-25, pos[1]-25, 50, 50)
        self.take_screenshot("send_button", send_region, is_dark_mode=True)
        
        self._update_status("\n✓ 模板创建完成！")
        self._update_status("提示：现在支持混合定位，即使模板识别失败也会尝试坐标定位")

    def send_batch_messages(self, friend_list, message):
        """批量发送消息"""
        self._update_status(f"\n=== 开始批量发送消息 ===")
        total = len(friend_list)
        if total == 0:
            self.status_updated.emit("好友列表为空，无法发送消息")
            return False
        self._update_status(f"目标好友数量: {len(friend_list)}")
        
        if not self.activate_wechat():
            self._update_status("批量发送失败：无法激活微信窗口")
            return False
            
        success_count = 0
        fail_list = []
        
        for index, friend_name in enumerate(friend_list, 1):
            self._update_status(f"\n--- 正在处理第 {index}/{len(friend_list)} 位好友：{friend_name} ---")
            
            try:
                if self.search_and_open_chat(friend_name) and self.send_message(message):
                    success_count += 1
                    self._update_status(f"✅ 已发送给 {friend_name}")
                else:
                    fail_list.append(friend_name)
                    self._update_status(f"❌ 发送给 {friend_name} 失败")
                
                # 休息避免频繁操作
                if index % 3 == 0:
                    self._update_status("休息3秒...")
                    time.sleep(3)
                    
            except Exception as e:
                fail_list.append(friend_name)
                self._update_status(f"❌ 处理 {friend_name} 时出错: {str(e)}")
                # 出错后重新激活微信窗口
                self.activate_wechat()
        
        self._update_status(f"\n=== 批量发送完成 ===")
        self._update_status(f"成功: {success_count}/{len(friend_list)}")
        
        if fail_list:
            self._update_status(f"失败列表: {fail_list}")
                
        return success_count > 0

    def _update_status(self, message):
        """更新状态，通过信号通知UI"""
        self.status_updated.emit(message)
        print(message)

class FileManager:
    """文件管理工具类"""
    @staticmethod
    def read_friend_list(file_path=None):
        """从文件读取好友名单"""
        config = ConfigManager.load_config()
        file_path = file_path or config["friends_file"]
        
        if not os.path.exists(file_path):
            FileManager.create_default_friends_file(file_path)
            return []
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                friends = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
            print(f"读取到 {len(friends)} 个好友")
            return friends
        except Exception as e:
            print(f"读取好友名单失败: {e}")
            return []
    
    @staticmethod
    def create_default_friends_file(file_path):
        """创建默认好友文件"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# 好友列表，每行一个好友名称\n")
                f.write("# 以#开头的行将被忽略\n")
                f.write("仙尊\n")
                f.write("慢点宝宝[猪头]\n")
                f.write("宝宝[猪头]\n")
            print(f"创建示例好友文件: {file_path}")
        except Exception as e:
            print(f"创建好友文件失败: {e}")
    
    @staticmethod
    def save_friend_list(friend_list, file_path=None):
        """保存好友列表到文件"""
        config = ConfigManager.load_config()
        file_path = file_path or config["friends_file"]
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# 好友列表，每行一个好友名称\n")
                f.write("# 以#开头的行将被忽略\n")
                for friend in friend_list:
                    f.write(f"{friend}\n")
            return True
        except Exception as e:
            print(f"保存好友列表失败: {e}")
            return False


def main():
    try:
        # 加载配置
        config = ConfigManager.load_config()
        wechat = WeChatAuto(config)

        # 检查模板文件
        required_templates = ["search_icon.png", "message_input.png", "send_button.png"]
        missing_templates = []
        
        for mode in ["light", "dark"]:
            mode_path = os.path.join(wechat.template_path, mode)
            if os.path.exists(mode_path):
                existing = os.listdir(mode_path)
                missing = [f"{mode}/{t}" for t in required_templates if t not in existing]
                missing_templates.extend(missing)
        
        if missing_templates:
            print(f"缺少模板文件: {missing_templates}")
            wechat.create_templates()
            if input("是否立即发送消息？(y/n)：").lower() != 'y':
                return
        
        # 读取好友列表
        friend_list = FileManager.read_friend_list()
        if not friend_list:
            if input("未读取到好友列表，是否手动输入？(y/n)：").lower() == 'y':
                friend_name = input("请输入好友名称：")
                friend_list = [friend_name]
            else:
                return

        # 输入消息
        default_msg = f"自动发送消息\n时间：{time.strftime('%Y-%m-%d %H:%M:%S')}"
        message = input(f"请输入消息内容（回车使用默认消息）：").strip()
        if not message:
            message = default_msg
        
        print(f"\n发送给 {len(friend_list)} 个好友：")
        for name in friend_list:
            print(f"  - {name}")
        print(f"消息内容：{message}")
        
        if input("\n确认发送？(y/n)：").lower() != 'y':
            return
        
        # 发送
        if len(friend_list) == 1:
            success = wechat.send_wechat_message(friend_list[0], message)
        else:
            success = wechat.send_batch_messages(friend_list, message)
        
        if success:
            print("🎉 发送完成！")
        else:
            print("❌ 发送失败")
            
    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    main()