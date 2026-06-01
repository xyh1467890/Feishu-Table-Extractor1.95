from PyQt5.QtCore import QThread, pyqtSignal
import os
import tempfile

# 顶部导入供PyInstaller分析依赖
# 移除严格的导入检查，允许运行时动态导入
_selenium_available = True


class GetCookieThread(QThread):
    cookie_received = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # 运行时再次导入，确保正确
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
            
            self.progress.emit("正在启动浏览器...")
            
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_experimental_option("detach", True)
            
            self.progress.emit("正在打开飞书网页...")
            
            # 尝试多种方案启动浏览器
            driver = None
            try:
                # 方案1: 使用 webdriver-manager
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
            except Exception as e1:
                try:
                    # 方案2: 直接启动，可能使用系统中的 ChromeDriver
                    self.progress.emit("尝试备用方案1...")
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e2:
                    # 方案3: 提示用户手动处理
                    error_msg = f"无法启动浏览器。请尝试：\n1. 关闭所有 Chrome 窗口\n2. 删除文件夹: C:\\Users\\{os.environ.get('USERNAME', '')}\\.wdm\n3. 重新运行程序\n\n错误: {str(e1)}"
                    self.error.emit(error_msg)
                    return
            
            driver.get("https://www.feishu.cn/")
            
            self.progress.emit("请在浏览器中登录飞书账户...")
            self.progress.emit("登录完成后点击应用中的确定按钮")
            
            # 保存 driver 引用，以便主程序可以控制
            self.driver = driver
            
            # 等待用户登录（这里我们不阻塞，让主程序处理）
            
        except ImportError as e:
            self.error.emit(f"缺少必要的库，错误详情: {str(e)}\n请确保已安装 selenium 和 webdriver-manager")
        except Exception as e:
            self.error.emit(f"启动浏览器失败: {str(e)}")
    
    def get_cookie_after_login(self):
        """在用户登录后获取 Cookie"""
        try:
            if not hasattr(self, 'driver') or not self.driver:
                self.error.emit("浏览器未启动")
                return
            
            self.progress.emit("正在获取 Cookie...")
            cookies = self.driver.get_cookies()
            
            # 转换为字符串格式
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            
            # 关闭浏览器
            try:
                self.driver.quit()
            except:
                pass
            
            self.cookie_received.emit(cookie_str)
            
        except Exception as e:
            self.error.emit(f"获取 Cookie 失败: {str(e)}")
