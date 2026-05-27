import sys
import os
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget
)
from PyQt5.QtCore import Qt

from config.settings import REDIRECT_PORT


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class PermissionPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("module_panel")
        
        self.tabs = None
        self.app_id_input = None
        self.app_secret_input = None
        self.login_button = None
        self.oauth_status_label = None
        self.token_input = None
        self.show_token_btn = None
        self.open_api_btn = None
        self.url_input = None
        self.fetch_button = None
        self.progress_label = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)
        
        # Auth Section
        auth_title = QLabel("认证方式")
        auth_title.setObjectName("section_title")
        layout.addWidget(auth_title)
        
        self.tabs = QTabWidget()
        self.tabs.setObjectName("auth_tabs")
        
        # --- Manual Token Tab ---
        manual_tab = QWidget()
        manual_layout = QVBoxLayout(manual_tab)
        manual_layout.setContentsMargins(0, 16, 0, 0)
        manual_layout.setSpacing(12)
        
        manual_info1 = QLabel("直接输入已有的 <a href='help:token' style='color:#409eff; text-decoration:none;'>User Access Token</a>。")
        manual_info1.setObjectName("info_text")
        manual_info1.setOpenExternalLinks(False)
        manual_info1.setWordWrap(True)
        manual_info1.setToolTip("点击查看如何获取 User Access Token 的视频教程")
        manual_info1.linkActivated.connect(self.parent_window.on_manual_info_link_clicked if self.parent_window else lambda x: None)
        manual_layout.addWidget(manual_info1)
        
        manual_info2 = QLabel("<a href='https://open.feishu.cn/api-explorer' style='color:#409eff; text-decoration:none;'>前往 API 调试台</a> 获取。")
        manual_info2.setObjectName("info_text")
        manual_info2.setOpenExternalLinks(True)
        manual_info2.setWordWrap(True)
        manual_layout.addWidget(manual_info2)
        
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("粘贴 User Access Token")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setObjectName("auth_input")
        manual_layout.addWidget(self.token_input)
        
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.show_token_btn = QPushButton("显示")
        self.show_token_btn.setCheckable(True)
        self.show_token_btn.setObjectName("action_btn")
        self.show_token_btn.toggled.connect(self.parent_window.toggle_token_visibility if self.parent_window else lambda x: None)
        self.open_api_btn = QPushButton("打开调试台")
        self.open_api_btn.setObjectName("action_btn")
        self.open_api_btn.clicked.connect(lambda: webbrowser.open("https://open.feishu.cn/api-explorer"))
        btn_row.addWidget(self.show_token_btn)
        btn_row.addWidget(self.open_api_btn)
        manual_layout.addLayout(btn_row)
        manual_layout.addStretch()
        
        # --- OAuth Tab ---
        oauth_tab = QWidget()
        oauth_layout = QVBoxLayout(oauth_tab)
        oauth_layout.setContentsMargins(0, 16, 0, 0)
        oauth_layout.setSpacing(12)
        
        info_label = QLabel(f"通过应用凭证一键获取 User Token。<br><a href='https://open.feishu.cn' style='color:#409eff; text-decoration:none;'>前往开放平台</a> 配置回调 URI: <code style='background:#f5f7fa; padding:2px 6px; border-radius:4px;'>http://localhost:{REDIRECT_PORT}</code>")
        info_label.setObjectName("info_text")
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        oauth_layout.addWidget(info_label)
        
        self.app_id_input = QLineEdit()
        self.app_id_input.setPlaceholderText("App ID (cli_...)")
        self.app_id_input.setObjectName("auth_input")
        oauth_layout.addWidget(self.app_id_input)
        
        self.app_secret_input = QLineEdit()
        self.app_secret_input.setPlaceholderText("App Secret")
        self.app_secret_input.setEchoMode(QLineEdit.Password)
        self.app_secret_input.setObjectName("auth_input")
        oauth_layout.addWidget(self.app_secret_input)
        
        self.login_button = QPushButton("浏览器一键授权")
        self.login_button.setObjectName("oauth_btn")
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.parent_window.start_oauth_flow if self.parent_window else lambda: None)
        oauth_layout.addWidget(self.login_button)
        
        self.oauth_status_label = QLabel("")
        self.oauth_status_label.setStyleSheet("color: #409eff; font-size: 12px;")
        oauth_layout.addWidget(self.oauth_status_label)
        oauth_layout.addStretch()
        
        self.tabs.addTab(manual_tab, "Token")
        self.tabs.addTab(oauth_tab, "OAuth")
        layout.addWidget(self.tabs)
        
        layout.addSpacing(8)
        
        # Target URL Section
        target_title = QLabel("目标数据表")
        target_title.setObjectName("section_title")
        layout.addWidget(target_title)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://xxx.feishu.cn/base/...")
        self.url_input.setObjectName("url_input")
        layout.addWidget(self.url_input)
        
        layout.addStretch()
        
        # Action Button
        self.fetch_button = QPushButton("获取高级权限数据")
        self.fetch_button.setObjectName("primary_btn")
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.parent_window.fetch_data if self.parent_window else lambda: None)
        layout.addWidget(self.fetch_button)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #67c23a; font-size: 13px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.progress_label)
