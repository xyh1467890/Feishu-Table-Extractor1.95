"""
批量提取产品数据对话框
"""
import sys
import os
import csv
import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QCheckBox, QWidget, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed

from ui.styles import APP_STYLE


class BatchExtractThread(QThread):
    """批量提取数据的线程"""
    progress = pyqtSignal(int, int, str)  # 当前, 总数, 状态
    row_result = pyqtSignal(int, bool, object, str)  # 行号, 成功, 数据, 错误
    finished = pyqtSignal(list, list, list)  # 成功, 失败, 原始

    def __init__(self, csv_data, column_name, auth_type, auth_data, module_type, **kwargs):
        super().__init__()
        self.csv_data = csv_data
        self.column_name = column_name
        self.auth_type = auth_type
        self.auth_data = auth_data
        self.module_type = module_type
        self.kwargs = kwargs
        self.is_running = True

    def run(self):
        total = len(self.csv_data)
        success_results = []
        failed_results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for idx, row in enumerate(self.csv_data):
                url = row.get(self.column_name, '')
                if url:
                    future = executor.submit(
                        self._extract_single, 
                        url, 
                        self.auth_type, 
                        self.auth_data, 
                        self.module_type,
                        self.kwargs
                    )
                    futures[future] = (idx, row)

            for future in as_completed(futures):
                if not self.is_running:
                    break

                idx, row = futures[future]
                try:
                    data = future.result()
                    success_results.append((idx, row, data))
                    self.row_result.emit(idx, True, data, "")
                except Exception as e:
                    failed_results.append((idx, row, str(e)))
                    self.row_result.emit(idx, False, None, str(e))

                current = len(success_results) + len(failed_results)
                self.progress.emit(current, total, f"处理中 {current}/{total}")

        self.finished.emit(success_results, failed_results, self.csv_data)

    def _extract_single(self, url, auth_type, auth_data, module_type, kwargs):
        headers = {}
        if auth_type == 'token':
            headers = {'Authorization': f'Bearer {auth_data}'}
        elif auth_type == 'cookie':
            headers = {'Cookie': auth_data}

        # 根据模块类型调用不同的API
        if module_type == "table":
            from api.feishu_api import extract_bitable_info
            fetch_records = kwargs.get("fetch_records", False)
            return extract_bitable_info(url, headers=headers, fetch_records=fetch_records)
        elif module_type == "dashboard":
            from api.feishu_dashboard_api import extract_dashboard_info
            return extract_dashboard_info(url, auth_data)
        elif module_type == "workflow":
            from api.feishu_workflow_api import extract_workflow_info
            return extract_workflow_info(url, auth_data)
        elif module_type == "permission":
            from api.feishu_permission_api import extract_permission_info
            return extract_permission_info(url, auth_data)
        elif module_type == "form":
            from api.feishu_form_api import extract_form_info
            return extract_form_info(url, auth_data)
        else:
            raise ValueError(f"未知的模块类型: {module_type}")

    def stop(self):
        self.is_running = False


class BatchExtractDialog(QDialog):
    """批量提取对话框"""

    def __init__(self, auth_type, auth_data, module_type, parent=None):
        super().__init__(parent)
        self.auth_type = auth_type
        self.auth_data = auth_data
        self.module_type = module_type
        self.csv_headers = []
        self.csv_data = []
        self.worker = None

        # 设置窗口标题
        module_names = {
            "table": "数据表",
            "dashboard": "仪表盘",
            "workflow": "工作流",
            "permission": "高级权限",
            "form": "表单"
        }
        self.setWindowTitle(f"批量提取{module_names.get(module_type, '')}数据")
        self.resize(1100, 950)
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(APP_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # 顶部标题区域
        header_layout = QHBoxLayout()
        title_label = QLabel("📦 批量提取工具")
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: 800;
            color: #1e293b;
        """)
        
        desc_label = QLabel("批量处理多个链接，高效提取数据")
        desc_label.setStyleSheet("""
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(desc_label)
        layout.addLayout(header_layout)

        # 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background: #e2e8f0; max-height: 1px;")
        layout.addWidget(divider)

        # 第一步：选择CSV文件
        file_section = self._create_file_section()
        layout.addWidget(file_section)

        # 第二步：设置提取选项
        option_section = self._create_option_section()
        layout.addWidget(option_section)

        # 进度和状态区域
        progress_container = QWidget()
        progress_container.setStyleSheet("""
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 16px;
        """)
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(16, 16, 16, 16)
        
        self.status_label = QLabel("准备就绪")
        self.status_label.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
            font-weight: 600;
        """)
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background: #ffffff;
                text-align: center;
                font-size: 11px;
                font-weight: 600;
                color: #64748b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 #3b82f6);
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_container)

        # 结果表格区域
        result_title = QLabel("提取结果")
        result_title.setStyleSheet("""
            color: #334155;
            font-size: 14px;
            font-weight: 700;
        """)
        layout.addWidget(result_title)

        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cbd5e1;
                border-radius: 12px;
                background: #ffffff;
                gridline-color: #f1f5f9;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px;
                color: #334155;
            }
            QTableWidget::item:selected {
                background: #eff6ff;
                color: #1e293b;
            }
            QHeaderView::section {
                background: #f1f5f9;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                color: #334155;
                font-weight: 700;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.result_table, 1)

        # 底部按钮区域
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addStretch()

        # 关闭按钮 - 灰色边框
        self.close_btn = QPushButton("关闭")
        self.close_btn.setMinimumWidth(100)
        self.close_btn.setMinimumHeight(40)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f8fafc;
                border-color: #94a3b8;
                color: #334155;
            }
            QPushButton:pressed {
                background: #f1f5f9;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        # 导出结果按钮 - 绿色
        self.export_btn = QPushButton("📥 导出结果")
        self.export_btn.setMinimumWidth(120)
        self.export_btn.setMinimumHeight(40)
        self.export_btn.setEnabled(False)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:pressed {
                background: #047857;
            }
            QPushButton:disabled {
                background: #a7f3d0;
            }
        """)
        self.export_btn.clicked.connect(self.export_result)
        btn_layout.addWidget(self.export_btn)

        # 停止按钮 - 红色
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.setMinimumWidth(100)
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f87171, stop:1 #ef4444);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #dc2626;
            }
            QPushButton:pressed {
                background: #b91c1c;
            }
            QPushButton:disabled {
                background: #fecaca;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_extract)
        btn_layout.addWidget(self.stop_btn)

        # 开始提取按钮 - 蓝色（主按钮）
        self.start_btn = QPushButton("▶️ 开始提取")
        self.start_btn.setMinimumWidth(140)
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 #3b82f6);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #93c5fd;
            }
        """)
        self.start_btn.clicked.connect(self.start_extract)
        btn_layout.addWidget(self.start_btn)

        layout.addWidget(btn_container)

    def _create_file_section(self):
        """创建文件选择区域"""
        widget = QWidget()
        widget.setStyleSheet("""
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 4px;
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题区域
        title_layout = QHBoxLayout()
        title_icon = QLabel("📂")
        title_icon.setStyleSheet("font-size: 18px;")
        title_label = QLabel("第一步：选择CSV文件")
        title_label.setStyleSheet("""
            color: #334155;
            font-size: 14px;
            font-weight: 700;
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)

        desc_label = QLabel("选择包含产品链接的CSV文件")
        desc_label.setStyleSheet("""
            color: #64748b;
            font-size: 13px;
        """)
        layout.addWidget(desc_label)

        file_layout = QHBoxLayout()
        file_layout.setSpacing(12)

        self.file_input = QLineEdit()
        self.file_input.setReadOnly(True)
        self.file_input.setPlaceholderText("点击右侧按钮选择CSV文件...")
        self.file_input.setMinimumHeight(44)
        self.file_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.file_input.setStyleSheet("""
            QLineEdit {
                background: #f8fafc;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                padding: 12px 16px;
                color: #64748b;
                font-size: 13px;
            }
        """)

        select_btn = QPushButton("选择文件")
        select_btn.setMinimumHeight(44)
        select_btn.setMinimumWidth(120)
        select_btn.setObjectName("primary_btn")
        select_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #60a5fa, stop:1 #3b82f6);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:pressed {
                background: #1d4ed8;
            }
            QPushButton:disabled {
                background: #93c5fd;
            }
        """)
        select_btn.clicked.connect(self.select_file)
        
        file_layout.addWidget(self.file_input, 1)
        file_layout.addWidget(select_btn)

        layout.addLayout(file_layout)

        return widget

    def _create_option_section(self):
        """创建选项区域"""
        widget = QWidget()
        widget.setStyleSheet("""
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 4px;
        """)
        
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题区域
        title_layout = QHBoxLayout()
        title_icon = QLabel("⚙️")
        title_icon.setStyleSheet("font-size: 18px;")
        title_label = QLabel("第二步：设置提取选项")
        title_label.setStyleSheet("""
            color: #334155;
            font-size: 14px;
            font-weight: 700;
        """)
        
        title_layout.addWidget(title_icon)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(16)

        col_label = QLabel("选择链接列：")
        col_label.setStyleSheet("""
            color: #334155;
            font-size: 13px;
            font-weight: 600;
        """)
        
        self.column_combo = QComboBox()
        self.column_combo.setMinimumWidth(240)
        self.column_combo.setMinimumHeight(44)
        self.column_combo.setStyleSheet("""
            QComboBox {
                background: #ffffff;
                border: 2px solid #cbd5e1;
                border-radius: 10px;
                padding: 10px 14px;
                color: #1e293b;
                font-size: 13px;
                font-weight: 500;
            }
            QComboBox:hover {
                border-color: #94a3b8;
            }
            QComboBox:focus {
                border-color: #60a5fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #64748b;
                width: 0;
                height: 0;
            }
        """)

        row_layout.addWidget(col_label)
        row_layout.addWidget(self.column_combo)

        # 只在table模块时显示"同时获取记录内容"选项
        if self.module_type == "table":
            self.fetch_records_check = QCheckBox("同时获取记录内容")
            self.fetch_records_check.setChecked(True)
            row_layout.addWidget(self.fetch_records_check)

        row_layout.addStretch()

        layout.addLayout(row_layout)

        return widget

    def select_file(self):
        """选择CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择CSV文件", "", "CSV文件 (*.csv);;所有文件 (*)"
        )

        if file_path:
            self.file_input.setText(file_path)
            self.load_csv(file_path)

    def load_csv(self, file_path):
        """加载CSV文件"""
        try:
            self.csv_headers = []
            self.csv_data = []

            # 尝试UTF-8编码
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.csv_headers = reader.fieldnames or []
                    for row in reader:
                        self.csv_data.append(row)
            except UnicodeDecodeError:
                # 尝试GBK编码
                with open(file_path, 'r', encoding='gbk') as f:
                    reader = csv.DictReader(f)
                    self.csv_headers = reader.fieldnames or []
                    for row in reader:
                        self.csv_data.append(row)

            if not self.csv_headers:
                QMessageBox.warning(self, "提示", "CSV文件为空或格式不正确")
                return

            # 更新列选择下拉框
            self.column_combo.clear()
            self.column_combo.addItems(self.csv_headers)

            # 初始化结果表格
            self._init_result_table()

            self.start_btn.setEnabled(True)
            self.status_label.setText(f"✓ 已加载 {len(self.csv_data)} 条数据")
            self.status_label.setStyleSheet("""
                color: #10b981;
                font-size: 13px;
                font-weight: 600;
            """)

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载CSV失败: {str(e)}")

    def _init_result_table(self):
        """初始化结果表格"""
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["序号", "状态", "链接", "备注"])

        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.result_table.setRowCount(len(self.csv_data))

        column_name = self.column_combo.currentText()
        for idx, row in enumerate(self.csv_data):
            self.result_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))
            status_item = QTableWidgetItem("等待中")
            status_item.setForeground(Qt.gray)
            self.result_table.setItem(idx, 1, status_item)
            self.result_table.setItem(idx, 2, QTableWidgetItem(str(row.get(column_name, ""))))

    def start_extract(self):
        """开始提取"""
        if not self.csv_data:
            QMessageBox.warning(self, "提示", "请先选择CSV文件")
            return

        column_name = self.column_combo.currentText()
        if not column_name:
            QMessageBox.warning(self, "提示", "请选择链接列")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.export_btn.setEnabled(False)

        # 构建额外参数
        kwargs = {}
        if self.module_type == "table" and hasattr(self, "fetch_records_check"):
            kwargs["fetch_records"] = self.fetch_records_check.isChecked()

        self.worker = BatchExtractThread(
            self.csv_data,
            column_name,
            self.auth_type,
            self.auth_data,
            self.module_type,
            **kwargs
        )

        self.worker.progress.connect(self.on_progress)
        self.worker.row_result.connect(self.on_row_result)
        self.worker.finished.connect(self.on_finished)

        self.worker.start()

    def stop_extract(self):
        """停止提取"""
        if self.worker:
            self.worker.stop()
            self.status_label.setText("正在停止...")
            self.status_label.setStyleSheet("""
                color: #f59e0b;
                font-size: 13px;
                font-weight: 600;
            """)

    def on_progress(self, current, total, text):
        """进度更新"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(text)

    def on_row_result(self, idx, success, data, error):
        """单行结果"""
        status_item = QTableWidgetItem("✓ 成功" if success else "✗ 失败")
        if success:
            status_item.setForeground(Qt.darkGreen)
        else:
            status_item.setForeground(Qt.darkRed)
        
        self.result_table.setItem(idx, 1, status_item)

        if error:
            error_text = error[:80] + "..." if len(error) > 80 else error
            self.result_table.setItem(idx, 3, QTableWidgetItem(error_text))

    def on_finished(self, success, failed, original):
        """完成"""
        self.success_results = success
        self.failed_results = failed
        self.original_data = original

        total = len(original)
        self.status_label.setText(f"✓ 完成！成功 {len(success)}，失败 {len(failed)}，总计 {total}")
        self.status_label.setStyleSheet("""
            color: #10b981;
            font-size: 13px;
            font-weight: 600;
        """)

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.export_btn.setEnabled(len(success) > 0 or len(failed) > 0)

        if len(failed) > 0:
            QMessageBox.information(
                self, "完成", 
                f"提取完成！\n成功: {len(success)} 条\n失败: {len(failed)} 条"
            )

    def export_result(self):
        """导出结果"""
        if not hasattr(self, 'success_results'):
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", "CSV文件 (*.csv)"
        )

        if file_path:
            try:
                # 构建新的数据
                new_headers = list(self.csv_headers) + ["提取状态", "提取结果", "错误信息"]
                new_data = []

                # 创建索引映射
                result_map = {}
                for idx, row, data in self.success_results:
                    result_map[idx] = ("成功", json.dumps(data, ensure_ascii=False), "")
                for idx, row, error in self.failed_results:
                    result_map[idx] = ("失败", "", error)

                # 合并数据
                for idx, row in enumerate(self.original_data):
                    new_row = dict(row)
                    if idx in result_map:
                        status, data, error = result_map[idx]
                        new_row["提取状态"] = status
                        new_row["提取结果"] = data
                        new_row["错误信息"] = error
                    else:
                        new_row["提取状态"] = "未处理"
                        new_row["提取结果"] = ""
                        new_row["错误信息"] = ""
                    new_data.append(new_row)

                # 写入文件
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=new_headers)
                    writer.writeheader()
                    writer.writerows(new_data)

                QMessageBox.information(self, "成功", f"✓ 结果已导出到：{file_path}")

            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败：{str(e)}")
