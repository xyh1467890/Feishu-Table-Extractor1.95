
import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QFrame, QLineEdit, QSplitter
)
from PyQt5.QtCore import Qt


def resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发和打包后"""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class QueryVerifyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("module_panel")
        
        self.api_key_input = None
        self.api_base_input = None
        self.model_input = None
        self.query_input = None
        self.verify_button = None
        self.result_text = None
        self.progress_label = None
        self.toggle_visibility_btn = None
        self.is_key_visible = False
        
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 使用 Splitter 分隔中间区域和右侧区域
        splitter = QSplitter(Qt.Horizontal)
        
        # 中间区域：用户输入
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧区域：结果展示
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置比例，左边占 50%，右边占 50%
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter)
    
    def create_left_panel(self):
        """创建左侧（中间）输入面板"""
        panel = QWidget()
        panel.setObjectName("left_panel_container")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)
        
        # API 配置区域
        api_title = QLabel("API 配置")
        api_title.setObjectName("section_title")
        layout.addWidget(api_title)
        
        # API Base
        api_base_label = QLabel("API Base:")
        api_base_label.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        layout.addWidget(api_base_label)
        
        self.api_base_input = QLineEdit()
        self.api_base_input.setPlaceholderText("https://api.openai.com/v1 (可选)")
        self.api_base_input.setMinimumHeight(45)
        self.api_base_input.setClearButtonEnabled(True)
        self.api_base_input.setObjectName("auth_input")
        layout.addWidget(self.api_base_input)
        
        layout.addSpacing(12)
        
        # LLM Model
        model_label = QLabel("LLM Model:")
        model_label.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        layout.addWidget(model_label)
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("请输入 LLM Model (可选)")
        self.model_input.setMinimumHeight(45)
        self.model_input.setClearButtonEnabled(True)
        self.model_input.setObjectName("auth_input")
        layout.addWidget(self.model_input)
        
        layout.addSpacing(12)
        
        # API Key
        api_key_label = QLabel("API Key:")
        api_key_label.setStyleSheet("color: #303133; font-weight: bold; font-size: 13px;")
        layout.addWidget(api_key_label)
        
        # API Key 输入框 + 显示/隐藏按钮
        api_key_layout = QHBoxLayout()
        api_key_layout.setSpacing(8)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 API Key...")
        self.api_key_input.setMinimumHeight(45)
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setClearButtonEnabled(True)
        self.api_key_input.setObjectName("auth_input")
        
        self.toggle_visibility_btn = QPushButton("显示")
        self.toggle_visibility_btn.setFixedWidth(60)
        self.toggle_visibility_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_visibility_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f7fa;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                font-size: 13px;
                color: #303133;
            }
            QPushButton:hover {
                background-color: #e4e7ed;
            }
        """)
        self.toggle_visibility_btn.clicked.connect(self.toggle_key_visibility)
        
        api_key_layout.addWidget(self.api_key_input, 1)
        api_key_layout.addWidget(self.toggle_visibility_btn)
        layout.addLayout(api_key_layout)
        
        layout.addSpacing(20)
        
        # 查询输入区域
        query_title = QLabel("Query 输入")
        query_title.setObjectName("section_title")
        layout.addWidget(query_title)
        
        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("请输入要检查的 Query")
        self.query_input.setMinimumHeight(200)
        self.query_input.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        layout.addWidget(self.query_input)
        
        layout.addStretch()
        
        # 执行按钮
        self.verify_button = QPushButton("开始检查")
        self.verify_button.setObjectName("primary_btn")
        self.verify_button.setMinimumHeight(48)
        self.verify_button.setCursor(Qt.PointingHandCursor)
        self.verify_button.clicked.connect(self.parent_window.verify_query if self.parent_window else lambda: None)
        layout.addWidget(self.verify_button)
        
        # 进度标签
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #67c23a; font-size: 13px; font-weight: bold; margin-top: 5px;")
        layout.addWidget(self.progress_label)
        
        return panel
    
    def create_right_panel(self):
        """创建右侧结果展示面板"""
        panel = QWidget()
        panel.setObjectName("right_panel_container")
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(20)
        
        # 标题
        result_title = QLabel("检查结果")
        result_title.setObjectName("section_title")
        layout.addWidget(result_title)
        
        # 结果显示区域
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("检查结果将在这里显示...")
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                padding: 16px;
                font-size: 14px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.result_text)
        
        return panel
    
    def toggle_key_visibility(self):
        """切换 API Key 的显示/隐藏"""
        self.is_key_visible = not self.is_key_visible
        if self.is_key_visible:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.toggle_visibility_btn.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.toggle_visibility_btn.setText("显示")
    
    def set_result(self, text):
        """设置结果文本"""
        self.result_text.setPlainText(text)
    
    def append_result(self, text):
        """追加结果文本"""
        current_text = self.result_text.toPlainText()
        if current_text:
            self.result_text.setPlainText(current_text + "\n" + text)
        else:
            self.result_text.setPlainText(text)
    
    def clear_result(self):
        """清空结果"""
        self.result_text.clear()
    
    def get_api_key(self):
        """获取 API Key"""
        return self.api_key_input.text().strip()
    
    def get_api_base(self):
        """获取 API Base"""
        return self.api_base_input.text().strip()
    
    def get_model(self):
        """获取 LLM Model"""
        return self.model_input.text().strip()
    
    def get_query(self):
        """获取查询内容"""
        return self.query_input.toPlainText().strip()
