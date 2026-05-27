"""
飞书工作流 API 工具模块
用于通过 Cookie 方式获取工作流配置
完全基于 feishu_workflowclean 仓库代码
"""

import json
import time
import requests
from urllib.parse import parse_qs, urlparse

# 请求配置
REQUEST_TIMEOUT = 30
RETRY_COUNT = 3
RETRY_DELAY = 1.0


def get_headers(cookie, referer):
    return {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cookie,
        "Referer": referer,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }


def parse_lark_url(url):
    parsed = urlparse(url)
    host = parsed.netloc
    
    path_parts = parsed.path.strip("/").split("/")
    base_id = path_parts[-1] if path_parts else None
    
    query = parse_qs(parsed.query)
    table_id = query.get("table", [None])[0]
    
    if not host or not base_id or not table_id:
        raise ValueError(
            f"URL parse failed!\n"
            f"  host: {host}\n"
            f"  base_id: {base_id}\n"
            f"  table_id: {table_id}\n"
            f"Please make sure URL format is correct and contains table parameter"
        )
    
    return host, base_id, table_id


def get_workflow_id_from_url(url, cookie):
    host, base_id, table_id = parse_lark_url(url)
    
    parsed = urlparse(url)
    block_info_url = f"{parsed.scheme}://{host}/space/api/bitable/{base_id}/block_info"
    
    headers = get_headers(cookie, url)
    
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(
                block_info_url,
                params={"table": table_id},
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            payload = response.json()
            
            if payload.get("code") != 0:
                raise ValueError(
                    f"API returned error: code={payload.get('code')}, msg={payload.get('msg')}"
                )
            
            blocks = payload.get("data", {}).get("blocks", {})
            block = blocks.get(table_id)
            
            if not block or "blockToken" not in block:
                raise ValueError(
                    f"blockToken not found!\n"
                    f"Please check:\n"
                    f"  1. Table permission\n"
                    f"  2. URL correctness\n"
                    f"  3. Cookie validity"
                )
            
            workflow_id = str(block["blockToken"])
            return workflow_id, base_id, host
            
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise


def get_workflow_draft(workflow_id, base_id, host, cookie):
    detail_url = f"https://{host}/space/api/bitable/{base_id}/workflow/detail"
    referer = f"https://{host}/base/{base_id}"
    headers = get_headers(cookie, referer)
    
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(
                detail_url,
                params={"workflowID": workflow_id, "bizType": 2},
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            payload = response.json()
            
            if payload.get("code") != 0:
                raise ValueError(
                    f"API returned error: code={payload.get('code')}, msg={payload.get('msg')}"
                )
            
            data = payload.get("data", {})
            workflow = data.get("workflow", {})
            
            draft = workflow.get("draft") or data.get("draft")
            
            if not draft:
                raise ValueError(
                    "Workflow draft not found!\n"
                    "Please check permission or workflow_id"
                )
            
            if isinstance(draft, str):
                draft = json.loads(draft)
            
            if not isinstance(draft, dict):
                raise ValueError(
                    f"Workflow draft type error!\n"
                    f"  Expected: dict/str\n"
                    f"  Actual: {type(draft)}"
                )
            
            return draft
            
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise


def clean_workflow_draft(draft):
    result = json.loads(json.dumps(draft))
    
    fields_to_remove = [
        "blockId", "blockToken",
        "baseId", "tableId", "viewId",
        "fieldId", "optionId", "sourceId",
        "targetId",
        "tableFieldMap", "tabldFieldMap"
    ]
    
    def clean_all(obj):
        if isinstance(obj, dict):
            keys_to_remove = []
            for key, value in obj.items():
                if key in fields_to_remove:
                    keys_to_remove.append(key)
                else:
                    clean_all(value)
            for key in keys_to_remove:
                del obj[key]
        elif isinstance(obj, list):
            for item in obj:
                clean_all(item)
    
    clean_all(result)
    
    if "steps" in result:
        cleaned_steps = []
        for step in result["steps"]:
            cleaned_step = clean_step(step)
            cleaned_steps.append(cleaned_step)
        result["steps"] = cleaned_steps
    
    return result


def clean_step(step):
    return json.loads(json.dumps(step))


def extract_workflow_info(url, cookie):
    """
    提取工作流信息
    
    Args:
        url: 飞书工作流链接
        cookie: 飞书 Cookie
        
    Returns:
        包含工作流信息的字典
    """
    workflow_id, base_id, host = get_workflow_id_from_url(url, cookie)
    draft = get_workflow_draft(workflow_id, base_id, host, cookie)
    cleaned_draft = clean_workflow_draft(draft)
    
    return {
        "type": "workflow",
        "url": url,
        "workflow_id": workflow_id,
        "base_id": base_id,
        "host": host,
        "draft": cleaned_draft,
        "raw_draft": draft
    }




