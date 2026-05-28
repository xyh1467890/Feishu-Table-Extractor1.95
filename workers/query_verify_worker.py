
import sys
import os
from PyQt5.QtCore import QThread, pyqtSignal

# 添加 query_validity_Checkfeishu 到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'query_validity_Checkfeishu'))

from core.query_evaluator import evaluate_query


class QueryVerifyWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, query: str, api_key: str, api_base: str = ""):
        super().__init__()
        self.query = query
        self.api_key = api_key
        self.api_base = api_base if api_base else None

    def run(self):
        try:
            self.progress.emit("正在评测 Query...")
            result = evaluate_query(
                query=self.query,
                api_key=self.api_key,
                api_base=self.api_base,
                verbose=False
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(f"评测失败: {str(e)}")
