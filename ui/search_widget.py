from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton
)
from PyQt5.QtCore import Qt


class SearchWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setObjectName("search_container")
        self.setFixedWidth(340)
        
        self.search_input = None
        self.match_label = None
        self.prev_button = None
        self.next_button = None
        
        self.search_matches = []
        self.current_match_index = -1
        
        self.init_ui()
    
    def init_ui(self):
        self.setStyleSheet("""
            QFrame#search_container {
                background-color: #ffffff;
                border: 1px solid #e5e6eb;
                border-radius: 8px;
            }
            QFrame#search_container:focus-within {
                border: 2px solid #409eff;
                box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
            }
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                padding: 0;
                color: #1f2329;
            }
            QLineEdit::placeholder {
                color: #8f959e;
            }
            QPushButton#nav_btn {
                background-color: transparent;
                border: none;
                color: #8f959e;
                font-size: 12px;
                border-radius: 6px;
                padding: 4px 8px;
                margin: 0px;
            }
            QPushButton#nav_btn:hover {
                background-color: #f0f2f5;
                color: #409eff;
            }
            QPushButton#nav_btn:pressed {
                background-color: #e5e6eb;
            }
            QPushButton#nav_btn:disabled {
                color: #c0c4cc;
                background-color: transparent;
            }
        """)
        
        search_layout = QHBoxLayout(self)
        search_layout.setContentsMargins(12, 8, 8, 8)
        search_layout.setSpacing(8)
        self.setFixedHeight(40)
        
        search_label = QLabel("🔍")
        search_label.setStyleSheet("font-size: 14px; color: #8f959e;")
        search_label.setFixedSize(20, 20)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索结果...")
        self.search_input.textChanged.connect(
            self.parent_window.on_search_text_changed if self.parent_window else lambda x: None
        )
        
        self.match_label = QLabel("")
        self.match_label.setStyleSheet("font-size: 13px; color: #8f959e;")
        self.match_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.match_label.setMinimumWidth(50)
        
        # 分割线
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setStyleSheet("background-color: #e5e6eb;")
        separator.setFixedSize(1, 20)
        
        # 导航按钮
        self.prev_button = QPushButton("▲")
        self.prev_button.setObjectName("nav_btn")
        self.prev_button.setCursor(Qt.PointingHandCursor)
        self.prev_button.clicked.connect(
            self.parent_window.on_prev_match if self.parent_window else lambda: None
        )
        self.prev_button.setEnabled(False)
        self.prev_button.setFixedSize(28, 24)
        self.prev_button.setToolTip("上一条匹配")
        self.prev_button.setStyleSheet("font-size: 11px; font-family: 'Segoe UI Symbol', 'Microsoft YaHei', sans-serif;")
        
        self.next_button = QPushButton("▼")
        self.next_button.setObjectName("nav_btn")
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(
            self.parent_window.on_next_match if self.parent_window else lambda: None
        )
        self.next_button.setEnabled(False)
        self.next_button.setFixedSize(28, 24)
        self.next_button.setToolTip("下一条匹配")
        self.next_button.setStyleSheet("font-size: 11px; font-family: 'Segoe UI Symbol', 'Microsoft YaHei', sans-serif;")
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.match_label)
        search_layout.addWidget(separator)
        search_layout.addWidget(self.prev_button)
        search_layout.addWidget(self.next_button)
