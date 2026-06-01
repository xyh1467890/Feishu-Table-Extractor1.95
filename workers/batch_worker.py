"""
批量提取产品数据的工作线程
"""
import os
import csv
import json
from PyQt5.QtCore import QThread, pyqtSignal
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchExtractWorker(QThread):
    """批量提取数据的工作线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总数, 状态信息
    row_processed = pyqtSignal(int, bool, object, str)  # 行号, 是否成功, 结果, 错误信息
    batch_finished = pyqtSignal(list, list, list)  # 成功数据, 失败数据, 原始数据
    
    def __init__(self, csv_data, column_name, auth_type, auth_data, module_type, **kwargs):
        super().__init__()
        self.csv_data = csv_data  # CSV数据，列表形式
        self.column_name = column_name  # 选择的列名
        self.auth_type = auth_type  # 认证方式: "token" 或 "cookie"
        self.auth_data = auth_data  # 认证数据
        self.module_type = module_type  # 模块类型: table/dashboard/workflow/permission/form
        self.kwargs = kwargs  # 其他参数
        self.is_running = True
        self.max_workers = 5  # 最大并发数
    
    def run(self):
        """执行批量处理"""
        total = len(self.csv_data)
        success_results = []
        failed_results = []
        original_data = list(self.csv_data)  # 保存原始数据
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for idx, row in enumerate(self.csv_data):
                url = row.get(self.column_name, '')
                if url:
                    future = executor.submit(
                        self._process_single_url, 
                        url, 
                        self.auth_type, 
                        self.auth_data, 
                        self.module_type,
                        self.kwargs
                    )
                    futures[future] = (idx, row)
            
            # 收集结果
            completed = 0
            for future in as_completed(futures):
                if not self.is_running:
                    break
                
                idx, row = futures[future]
                try:
                    result = future.result()
                    success_results.append((idx, row, result))
                    self.row_processed.emit(idx, True, result, "")
                except Exception as e:
                    failed_results.append((idx, row, str(e)))
                    self.row_processed.emit(idx, False, None, str(e))
                
                completed += 1
                progress_text = f"正在处理 {completed}/{total}"
                self.progress_updated.emit(completed, total, progress_text)
        
        # 发送完成信号
        self.batch_finished.emit(success_results, failed_results, original_data)
    
    def _process_single_url(self, url, auth_type, auth_data, module_type, kwargs):
        """处理单个URL"""
        # 构建请求头
        headers = {}
        if auth_type == 'token':
            headers = {
                "Authorization": f"Bearer {auth_data}",
                "Content-Type": "application/json"
            }
        elif auth_type == 'cookie':
            headers = {
                "Cookie": auth_data
            }
        
        # 根据模块类型调用不同的API
        if module_type == "table":
            from api.feishu_api import extract_bitable_info
            fetch_records = kwargs.get("fetch_records", False)
            result = extract_bitable_info(url, headers=headers, fetch_records=fetch_records)
        elif module_type == "dashboard":
            from api.feishu_dashboard_api import extract_dashboard_info
            result = extract_dashboard_info(url, auth_data)
        elif module_type == "workflow":
            from api.feishu_workflow_api import extract_workflow_info
            result = extract_workflow_info(url, auth_data)
        elif module_type == "permission":
            from api.feishu_permission_api import extract_permission_info
            result = extract_permission_info(url, auth_data)
        elif module_type == "form":
            from api.feishu_form_api import extract_form_info
            result = extract_form_info(url, auth_data)
        else:
            raise ValueError(f"未知的模块类型: {module_type}")
        
        return result
    
    def stop(self):
        """停止处理"""
        self.is_running = False


def read_csv_file(file_path):
    """
    读取CSV文件
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        (headers, data): 表头和数据列表
    """
    headers = []
    data = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                data.append(row)
    except UnicodeDecodeError:
        # 尝试使用gbk编码
        with open(file_path, 'r', encoding='gbk') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                data.append(row)
    
    return headers, data


def write_csv_file(file_path, headers, data):
    """
    写入CSV文件
    
    Args:
        file_path: 输出文件路径
        headers: 表头列表
        data: 数据列表
    """
    with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


def merge_results(original_data, success_results, failed_results):
    """
    合并原始数据和提取结果
    
    Args:
        original_data: 原始CSV数据
        success_results: 成功的结果列表
        failed_results: 失败的结果列表
        
    Returns:
        合并后的数据列表
    """
    # 创建索引到结果的映射
    index_to_result = {}
    for idx, row, result in success_results:
        index_to_result[idx] = ('success', result)
    for idx, row, error in failed_results:
        index_to_result[idx] = ('failed', error)
    
    # 合并数据
    merged_data = []
    for idx, row in enumerate(original_data):
        merged_row = dict(row)
        if idx in index_to_result:
            status, value = index_to_result[idx]
            merged_row['提取状态'] = status
            if status == 'success':
                merged_row['提取结果'] = json.dumps(value, ensure_ascii=False)
            else:
                merged_row['错误信息'] = value
        else:
            merged_row['提取状态'] = '未处理'
        
        merged_data.append(merged_row)
    
    return merged_data
