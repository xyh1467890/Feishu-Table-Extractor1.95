"""
飞书仪表盘 API 工具模块
"""

import json
import time
import requests
from urllib.parse import parse_qs, urlparse


def get_dashboard_headers(cookie, referer):
    """获取仪表盘请求头"""
    cleaned_cookie = cookie.strip()
    cleaned_cookie = ''.join(filter(lambda c: c not in '\r\n\t', cleaned_cookie))
    
    return {
        "Accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Cookie": cleaned_cookie,
        "Referer": referer,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "X-Requested-With": "XMLHttpRequest",
    }


def parse_dashboard_url(url):
    """解析仪表盘URL，提取必要参数"""
    parsed = urlparse(url)
    host = parsed.netloc
    
    path_parts = parsed.path.strip("/").split("/")
    base_id = path_parts[-1] if path_parts else None
    
    query = parse_qs(parsed.query)
    
    if not query and parsed.fragment:
        fragment_query = parsed.fragment.split("?", 1)[-1]
        query = parse_qs(fragment_query)
    
    table_id = query.get("table", [None])[0]
    
    if not host or not base_id or not table_id:
        raise ValueError(
            f"URL解析失败！\n"
            f"  host: {host}\n"
            f"  base_id: {base_id}\n"
            f"  table_id: {table_id}\n"
            f"请确保URL格式正确且包含table参数"
        )
    
    return host, base_id, table_id


def extract_snapshot_data(raw_data):
    """提取并格式化snapshot数据"""
    result = {}
    
    if "snapshots" in raw_data:
        snapshots = raw_data["snapshots"]
        
        for chart_id, chart_data in snapshots.items():
            if "snapshot" in chart_data:
                snapshot_str = chart_data["snapshot"]
                try:
                    snapshot_json = json.loads(snapshot_str)
                    result[chart_id] = {
                        "chart_id": chart_id,
                        "snapshot": snapshot_json
                    }
                except json.JSONDecodeError:
                    result[chart_id] = {
                        "chart_id": chart_id,
                        "snapshot": snapshot_str
                    }
    
    return result


def extract_dashboard_info(url, cookie):
    """
    提取仪表盘信息
    
    Args:
        url: 飞书仪表盘链接
        cookie: 飞书Cookie
        
    Returns:
        包含仪表盘信息的字典
    """
    print(f"\n{'='*60}")
    print(f"🚀 开始提取仪表盘信息")
    print(f"{'='*60}")
    print(f"URL: {url}")
    
    host, base_id, table_id = parse_dashboard_url(url)
    print(f"   ✅ host: {host}")
    print(f"   ✅ base_id: {base_id}")
    print(f"   ✅ table_id: {table_id}")
    
    headers = get_dashboard_headers(cookie, url)
    
    # 直接使用base_id作为token参数
    api_url = f"https://{host}/space/api/v2/sheet/blocks/dashboard/web_ssr/charts"
    params = {"token": base_id, "tableID": table_id}
    
    print(f"\n📋 请求API: {api_url}")
    print(f"   参数: token={base_id}, tableID={table_id}")
    
    for attempt in range(3):
        try:
            response = requests.get(
                api_url,
                params=params,
                headers=headers,
                timeout=30
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                payload = response.json()
                print(f"   返回码: {payload.get('code')}")
                
                if payload.get("code") == 0:
                    raw_data = payload.get("data", {})
                    
                    print(f"   ✅ 获取成功！正在提取snapshot数据...")
                    
                    snapshots = extract_snapshot_data(raw_data)
                    
                    print(f"   ✅ 提取到 {len(snapshots)} 个图表的snapshot")
                    
                    return {
                        "type": "dashboard",
                        "url": url,
                        "host": host,
                        "base_id": base_id,
                        "table_id": table_id,
                        "snapshots": snapshots
                    }
                else:
                    raise ValueError(
                        f"API返回错误: code={payload.get('code')}, msg={payload.get('msg')}"
                    )
            
        except Exception as e:
            if attempt < 2:
                print(f"   重试 {attempt+1}/3...")
                time.sleep(1)
            else:
                raise
    
    raise ValueError(f"仪表盘获取失败！请检查URL、Cookie和权限。")

