import sys
import os
import webbrowser
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from config.settings import REDIRECT_PORT


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class TablePanel(QWidget):
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
        self.get_cookie_btn = None
        self.confirm_login_btn = None
        self.cookie_status_label = None
        self.clear_cookie_btn = None
        self.cookie_input = None
        self.url_input = None
        self.fetch_records_checkbox = None
        self.fetch_button = None
        self.progress_label = None
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)
        
        # Section 1: Auth
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
        
        # --- Cookie Tab ---
        cookie_tab = QWidget()
        cookie_layout = QVBoxLayout(cookie_tab)
        cookie_layout.setContentsMargins(0, 16, 0, 0)
        cookie_layout.setSpacing(12)
        
        auto_info = QLabel("方式一：浏览器自动提取（推荐）")
        auto_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        cookie_layout.addWidget(auto_info)
        
        auto_desc = QLabel("自动打开飞书网页，登录后一键提取 Cookie。")
        auto_desc.setStyleSheet("color: #909399; font-size: 12px; margin-bottom: 5px;")
        cookie_layout.addWidget(auto_desc)
        
        auto_btn_layout = QHBoxLayout()
        auto_btn_layout.setSpacing(10)
        
        self.get_cookie_btn = QPushButton("🚀 启动浏览器")
        self.get_cookie_btn.setObjectName("cookie_auto_btn")
        self.get_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.get_cookie_btn.clicked.connect(self.parent_window.start_get_cookie if self.parent_window else lambda: None)
        
        self.confirm_login_btn = QPushButton("✓ 已登录，提取 Cookie")
        self.confirm_login_btn.setEnabled(False)
        self.confirm_login_btn.setObjectName("cookie_confirm_btn")
        self.confirm_login_btn.setCursor(Qt.PointingHandCursor)
        self.confirm_login_btn.clicked.connect(self.parent_window.confirm_get_cookie if self.parent_window else lambda: None)
        
        auto_btn_layout.addWidget(self.get_cookie_btn)
        auto_btn_layout.addWidget(self.confirm_login_btn)
        auto_btn_layout.addStretch()
        
        cookie_layout.addLayout(auto_btn_layout)
        
        self.cookie_status_label = QLabel("")
        self.cookie_status_label.setStyleSheet("color: #e6a23c; font-size: 12px;")
        cookie_layout.addWidget(self.cookie_status_label)
        
        cookie_layout.addSpacing(5)
        
        divider_layout = QHBoxLayout()
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: #ebeef5; max-height: 1px;")
        or_label = QLabel("           或")
        or_label.setStyleSheet("color: #c0c4cc; font-size: 13px;")
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #ebeef5; max-height: 1px;")
        divider_layout.addWidget(line1)
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(line2)
        cookie_layout.addLayout(divider_layout)
        
        cookie_layout.addSpacing(5)
        
        manual_header_layout = QHBoxLayout()
        manual_info = QLabel("方式二：手动输入")
        manual_info.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        
        self.clear_cookie_btn = QPushButton("清空内容")
        self.clear_cookie_btn.setObjectName("clear_btn")
        self.clear_cookie_btn.setCursor(Qt.PointingHandCursor)
        self.clear_cookie_btn.clicked.connect(lambda: self.cookie_input.clear())
        
        manual_header_layout.addWidget(manual_info)
        manual_header_layout.addStretch()
        manual_header_layout.addWidget(self.clear_cookie_btn)
        cookie_layout.addLayout(manual_header_layout)
        
        self.cookie_input = QLineEdit()
        self.cookie_input.setPlaceholderText("请在此粘贴完整的飞书 Cookie...")
        self.cookie_input.setMinimumHeight(42)
        self.cookie_input.setClearButtonEnabled(True)
        self.cookie_input.setObjectName("auth_input")
        cookie_layout.addWidget(self.cookie_input)
        
        cookie_layout.addStretch()
        
        self.tabs.addTab(manual_tab, "Token")
        self.tabs.addTab(oauth_tab, "OAuth")
        self.tabs.addTab(cookie_tab, "Cookie")
        layout.addWidget(self.tabs)
        
        layout.addSpacing(8)
        
        # Section 2: Target
        target_title = QLabel("目标数据表")
        target_title.setObjectName("section_title")
        layout.addWidget(target_title)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://xxx.feishu.cn/base/...")
        self.url_input.setObjectName("url_input")
        layout.addWidget(self.url_input)
        
        self.fetch_records_checkbox = QCheckBox("同时获取数据表记录内容")
        self.fetch_records_checkbox.setChecked(True)
        self.fetch_records_checkbox.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.fetch_records_checkbox)
        
        layout.addStretch()
        
        # Action Button
        self.fetch_button = QPushButton("获取数据")
        self.fetch_button.setObjectName("primary_btn")
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.parent_window.fetch_data if self.parent_window else lambda: None)
        layout.addWidget(self.fetch_button)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #67c23a; font-size: 13px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.progress_label)
