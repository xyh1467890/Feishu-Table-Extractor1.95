"""
飞书高级权限 API 工具模块
基于 feiushu_permission_clean 仓库代码
"""

import json
import time
import requests
from urllib.parse import urlparse


def parse_app_id(feishu_url):
    """从飞书链接解析应用ID"""
    parsed = urlparse(feishu_url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2 or parts[0] != "base":
        raise ValueError("不是有效的飞书多维表格链接")
    return parts[1]


def feishu_get(url, headers, params=None):
    """飞书API通用GET请求"""
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"接口请求失败：{data}")
    return data.get("data", {})


def get_all_pages(url, headers, params=None):
    """获取所有页数据"""
    params = params or {}
    params = dict(params)
    params.setdefault("page_size", 100)
    items = []
    page_token = None
    while True:
        if page_token:
            params["page_token"] = page_token
        data = feishu_get(url, headers, params=params)
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
        time.sleep(0.2)
    return items


def get_advanced_permissions(base_token, headers):
    """获取高级权限配置"""
    roles_url = f"https://open.feishu.cn/open-apis/base/v2/apps/{base_token}/roles"
    roles = get_all_pages(roles_url, headers)
    return {"roles": roles}


def extract_permission_info(feishu_url, user_token):
    """
    提取高级权限信息
    
    Args:
        feishu_url: 飞书链接
        user_token: 用户访问令牌 (User Access Token)
        
    Returns:
        包含权限配置的字典
    """
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    base_token = parse_app_id(feishu_url)
    
    try:
        permissions = get_advanced_permissions(base_token, headers)
    except Exception as e:
        error_msg = str(e)
        # 检查是否是没有设置高级权限的错误（错误码 1254301）
        if "1254301" in error_msg or "OperationTypeError" in error_msg:
            permissions = {"roles": [], "error": "当前数据表没有设置高级权限"}
        else:
            permissions = {"roles": [], "error": error_msg}
    
    return {
        "type": "permission",
        "url": feishu_url,
        "base_token": base_token,
        "permissions": permissions
    }

