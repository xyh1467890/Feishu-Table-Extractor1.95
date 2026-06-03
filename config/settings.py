# OAuth 配置
REDIRECT_PORT = 3000
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"

# Building 机评 API 配置
JUDGE_API_URL = "https://sszy6ucc.fn-boe.bytedance.net/v1/judge"

# 配置文件路径
import os
import json

CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CONFIG_DIR, "user_config.json")

def get_config():
    """获取用户配置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config(config):
    """保存用户配置"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")

def get_judge_api_key():
    """获取 JUDGE_API_KEY"""
    config = get_config()
    return config.get("JUDGE_API_KEY", "")

def set_judge_api_key(api_key):
    """设置 JUDGE_API_KEY"""
    config = get_config()
    config["JUDGE_API_KEY"] = api_key
    save_config(config)
