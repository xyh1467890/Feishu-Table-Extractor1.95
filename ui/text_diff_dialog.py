

import difflib

from PyQt5.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QFrame,
    QScrollArea,
    QSizePolicy
)

from PyQt5.QtCore import Qt
from PyQt5.QtGui import (
    QTextCursor,
    QTextCharFormat,
    QColor,
    QTextBlockFormat
)


class TextDiffDialog(QDialog):

    def __init__(self, parent=None):
        # 不传入parent，创建真正独立的窗口
        super().__init__(None)

        self.setWindowTitle("文本对比")

        # 调整到更合适的大小
        self.resize(1400, 900)
        self.setMinimumSize(1100, 720)

        # 设置为独立窗口，不跟随父窗口最小化
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.init_ui()

    # =========================================================
    # UI
    # =========================================================

    def init_ui(self):

        # 浅灰色背景
        self.setStyleSheet("""
            QDialog {
                background: #f5f6f7;
            }
        """)

        root = QVBoxLayout(self)

        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.create_header(root)
        self.create_content(root)

    # =========================================================
    # 顶栏 - 更宽松
    # =========================================================

    def create_header(self, parent):

        header = QWidget()

        # 更大的高度
        header.setFixedHeight(72)

        header.setStyleSheet("""
            QWidget {
                background: white;
                border-bottom: 1px solid #e8ecf0;
            }
        """)

        layout = QHBoxLayout(header)

        # 更大的边距
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(20)

        title = QLabel("文本对比工具")

        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
                font-family: "PingFang SC";
            }
        """)

        layout.addWidget(title)

        self.status_label = QLabel("")

        self.status_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #86909c;
                padding-top: 4px;
            }
        """)

        layout.addWidget(self.status_label)

        layout.addStretch()

        # =====================================================
        # 按钮 - 更大更宽松
        # =====================================================

        btn_style = """
            QPushButton {
                border: none;
                background: transparent;
                color: #4e5969;
                font-size: 14px;
                padding: 10px 18px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background: #f2f3f5;
            }

            QPushButton:pressed {
                background: #e5e6eb;
            }
        """

        primary_style = """
            QPushButton {
                border: none;
                background: #3370ff;
                color: white;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 24px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background: #2864f0;
            }

            QPushButton:pressed {
                background: #1f54d1;
            }
        """

        compare_btn = QPushButton("开始对比")
        compare_btn.setStyleSheet(primary_style)
        compare_btn.clicked.connect(self.compare_texts)

        # 清空按钮带垃圾桶图标 - 更醒目的配色
        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.setStyleSheet("""
            QPushButton {
                border: none;
                background: #fff1f0;
                color: #ff4d4f;
                font-size: 14px;
                padding: 10px 18px;
                border-radius: 8px;
            }

            QPushButton:hover {
                background: #ffe5e3;
            }

            QPushButton:pressed {
                background: #ffd9d6;
            }
        """)
        clear_btn.clicked.connect(self.clear_texts)

        layout.addWidget(clear_btn)
        layout.addSpacing(16)
        layout.addWidget(compare_btn)

        parent.addWidget(header)

    # =========================================================
    # 内容区 - 两个编辑器，一个滚动条
    # =========================================================

    def create_content(self, parent):

        content = QWidget()

        content_layout = QVBoxLayout(content)

        # 更大的外边距
        content_layout.setContentsMargins(32, 32, 32, 32)
        content_layout.setSpacing(0)

        # =====================================================
        # 顶部分栏标题 - 更宽松
        # =====================================================

        top_bar = QWidget()

        top_bar.setFixedHeight(56)

        top_bar.setStyleSheet("""
            QWidget {
                background: white;
                border-bottom: 1px solid #e8ecf0;
            }
        """)

        top_layout = QHBoxLayout(top_bar)

        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        left_label = self.create_column_title("原始文本")
        
        # 交换按钮在中间
        swap_btn_middle = QPushButton("交换")
        swap_btn_middle.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #4e5969;
                font-size: 13px;
                padding: 6px 12px;
                border-radius: 6px;
            }

            QPushButton:hover {
                background: #f2f3f5;
            }

            QPushButton:pressed {
                background: #e5e6eb;
            }
        """)
        swap_btn_middle.clicked.connect(self.swap_texts)
        
        right_label = self.create_column_title("修改后文本")

        top_layout.addWidget(left_label, 1)
        top_layout.addWidget(swap_btn_middle)
        top_layout.addWidget(right_label, 1)

        content_layout.addWidget(top_bar)

        # =====================================================
        # 编辑区域 - 两个编辑器一个滚动条
        # =====================================================

        # 创建滚动区域（放在右侧）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
            QScrollBar:vertical {
                width: 12px;
                background: transparent;
                margin: 16px 6px 16px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0,0,0,0.12);
                border-radius: 6px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0,0,0,0.2);
            }
        """)

        # 创建滚动区域内部的容器
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: white;")
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 16, 16, 16)
        scroll_layout.setSpacing(24)

        # 左编辑器 - 隐藏滚动条
        self.text1 = self.create_editor("请输入原始文本")
        self.text1.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text1.setMinimumWidth(400)
        
        # 右编辑器 - 隐藏滚动条
        self.text2 = self.create_editor("请输入修改后文本")
        self.text2.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text2.setMinimumWidth(400)

        # 连接滚动信号实现同步
        self.text1.verticalScrollBar().valueChanged.connect(self.sync_scroll_from_text1)
        self.text2.verticalScrollBar().valueChanged.connect(self.sync_scroll_from_text2)

        scroll_layout.addWidget(self.text1, 1)
        scroll_layout.addWidget(self.text2, 1)

        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area, 1)
        parent.addWidget(content, 1)

    # =========================================================
    # 同步滚动
    # =========================================================

    def sync_scroll_from_text1(self, value):
        """当text1滚动时，同步text2"""
        self.text2.blockSignals(True)
        self.text2.verticalScrollBar().setValue(value)
        self.text2.blockSignals(False)

    def sync_scroll_from_text2(self, value):
        """当text2滚动时，同步text1"""
        self.text1.blockSignals(True)
        self.text1.verticalScrollBar().setValue(value)
        self.text1.blockSignals(False)

    # =========================================================
    # 分栏标题 - 更宽松
    # =========================================================

    def create_column_title(self, text):

        wrapper = QWidget()

        layout = QHBoxLayout(wrapper)

        # 更大的内边距
        layout.setContentsMargins(40, 0, 40, 0)

        label = QLabel(text)

        label.setStyleSheet("""
            QLabel {
                font-size: 15px;
                color: #4e5969;
                font-weight: 500;
                font-family: "PingFang SC";
            }
        """)

        layout.addWidget(label)

        return wrapper

    # =========================================================
    # 编辑器 - 更宽松的内边距
    # =========================================================

    def create_editor(self, placeholder):

        editor = QTextEdit()

        editor.setPlaceholderText(placeholder)
        editor.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )
        editor.setLineWrapMode(QTextEdit.WidgetWidth)

        editor.setStyleSheet("""
            QTextEdit {
                background: #fafbfc;
                border: none;
                border-radius: 8px;

                /* 合适的内边距 */
                padding: 24px 32px;

                color: #1a1a1a;

                font-size: 14px;
                line-height: 1.8;

                font-family:
                    "PingFang SC",
                    "Microsoft YaHei",
                    monospace;

                selection-background-color: #dbeafe;
            }

            QTextEdit:focus {
                border: none;
                background: #ffffff;
            }
        """)

        return editor

    # =========================================================
    # 清空
    # =========================================================

    def clear_texts(self):

        self.text1.clear()
        self.text2.clear()

        self.text1.setReadOnly(False)
        self.text2.setReadOnly(False)

        self.status_label.setText("")

    # =========================================================
    # 交换
    # =========================================================

    def swap_texts(self):

        t1 = self.text1.toPlainText()
        t2 = self.text2.toPlainText()

        self.text1.setText(t2)
        self.text2.setText(t1)

    # =========================================================
    # 对比
    # =========================================================

    def compare_texts(self):

        text1 = self.text1.toPlainText()
        text2 = self.text2.toPlainText()

        lines1 = text1.splitlines()
        lines2 = text2.splitlines()

        self.render_diff(lines1, lines2)

    # =========================================================
    # 渲染差异
    # =========================================================

    def render_diff(self, lines1, lines2):

        matcher = difflib.SequenceMatcher(None, lines1, lines2)

        left_result = []
        right_result = []

        left_types = []
        right_types = []

        diff_count = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():

            if tag == "equal":
                # 相等的内容，左右两侧应该一一对应
                for i in range(i2 - i1):
                    left_result.append(lines1[i1 + i])
                    left_types.append("normal")
                    right_result.append(lines2[j1 + i])
                    right_types.append("normal")

            elif tag == "replace":

                diff_count += max(i2 - i1, j2 - j1)

                max_len = max(i2 - i1, j2 - j1)

                for i in range(max_len):

                    left_line = lines1[i1 + i] if i < i2 - i1 else ""
                    right_line = lines2[j1 + i] if i < j2 - j1 else ""

                    # 逐行比较，真正相同的行标记为 normal
                    if left_line == right_line:
                        left_result.append(left_line)
                        left_types.append("normal")
                        right_result.append(right_line)
                        right_types.append("normal")
                    else:
                        if i < i2 - i1:
                            left_result.append(left_line)
                            left_types.append("delete")
                        else:
                            left_result.append("")
                            left_types.append("empty")

                        if i < j2 - j1:
                            right_result.append(right_line)
                            right_types.append("insert")
                        else:
                            right_result.append("")
                            right_types.append("empty")

            elif tag == "delete":

                diff_count += i2 - i1

                for line in lines1[i1:i2]:

                    left_result.append(line)
                    left_types.append("delete")

                    right_result.append("")
                    right_types.append("empty")

            elif tag == "insert":

                diff_count += j2 - j1

                for line in lines2[j1:j2]:

                    left_result.append("")
                    left_types.append("empty")

                    right_result.append(line)
                    right_types.append("insert")

        self.text1.setPlainText("\n".join(left_result))
        self.text2.setPlainText("\n".join(right_result))

        self.apply_styles(self.text1, left_types)
        self.apply_styles(self.text2, right_types)

        self.status_label.setText(f"发现 {diff_count} 处变更")

    # =========================================================
    # 应用样式
    # =========================================================

    def apply_styles(self, editor, types):

        doc = editor.document()

        for i, line_type in enumerate(types):

            block = doc.findBlockByNumber(i)

            if not block.isValid():
                continue

            cursor = QTextCursor(block)

            cursor.select(QTextCursor.BlockUnderCursor)

            fmt = QTextCharFormat()

            block_fmt = QTextBlockFormat()

            block_fmt.setLeftMargin(12)

            if line_type == "delete":
                # 删除的内容（不一致）- 红色背景
                fmt.setForeground(QColor("#991b1b"))
                block_fmt.setBackground(QColor("#fee2e2"))

            elif line_type == "insert":
                # 插入的内容（不一致）- 红色背景
                fmt.setForeground(QColor("#991b1b"))
                block_fmt.setBackground(QColor("#fee2e2"))

            elif line_type == "empty":

                fmt.setForeground(QColor("#d0d4da"))
                block_fmt.setBackground(QColor("#fcfcfd"))

            else:
                # 一致的内容 - 绿色背景
                fmt.setForeground(QColor("#1a1a1a"))
                block_fmt.setBackground(QColor("#dcfce7"))

            cursor.setBlockFormat(block_fmt)
            cursor.setCharFormat(fmt)

