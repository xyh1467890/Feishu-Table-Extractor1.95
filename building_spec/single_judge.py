"""
单条测试逻辑模块
负责处理单条测试的核心逻辑
"""
import requests
import json
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import get_judge_api_key, JUDGE_API_URL


class SingleJudge:
    """单条测试类"""
    
    def __init__(self):
        self.is_running = False
    
    def send_request(self, query, base_token, agent="building", dimensions=None, mode="spec"):
        """
        发送单条测试请求
        
        Args:
            query: 测试查询内容
            base_token: 基础 Token
            agent: Agent 类型
            dimensions: 评估维度（仅 building agent 需要）
            mode: 评估模式
        
        Returns:
            响应结果字典
        """
        if dimensions is None:
            dimensions = ["table", "permission", "workflow", "formula", "dashboard"]
        
        api_key = get_judge_api_key()
        if not api_key:
            return {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": "未配置 JUDGE_API_KEY",
                "message": "请在 Building 机评界面中配置 JUDGE_API_KEY"
            }
        
        headers = {
            "Content-Type": "application/json",
            "x-judge-api-key": api_key
        }
        
        # 构建请求体
        if agent == "building":
            # Building agent 特殊格式
            data = {
                "agent": agent,
                "cases": [{
                    "id": "SingleTest_001",
                    "query": query,
                    "baseToken": base_token
                }],
                "options": {
                    "dimensions": dimensions,
                    "concurrency": 1,
                    "mode": mode
                }
            }
        else:
            # 非 building agent 格式
            data = {
                "agent": agent,
                "cases": [{
                    "id": "SingleTest_001",
                    "query": query,
                    "baseToken": base_token
                }],
                "options": {
                    "concurrency": 1,
                    "mode": mode
                }
            }
        
        try:
            response = requests.post(JUDGE_API_URL, headers=headers, json=data)
            
            result = {
                "success": True,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "status_code": response.status_code,
                "request_body": data,
                "response_headers": dict(response.headers),
                "response_text": response.text
            }
            
            # 尝试解析 JSON
            try:
                result["response_json"] = response.json()
            except:
                result["response_json"] = None
            
            # 提取重要标识
            result["request_id"] = response.headers.get('x-bytefaas-request-id')
            result["tt_logid"] = response.headers.get('x-tt-logid')
            result["tt_trace_id"] = response.headers.get('x-tt-trace-id')
            
            # 添加状态消息
            if response.status_code == 201:
                result["message"] = "请求成功提交（异步任务已创建）"
            elif 200 <= response.status_code < 300:
                result["message"] = "请求成功"
            else:
                result["message"] = f"请求返回状态码: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            result = {
                "success": False,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "error": str(e),
                "message": f"网络请求异常: {e}"
            }
        
        return result
