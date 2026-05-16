"""配置管理：加载 .env 环境变量，对外暴露常量。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录的 .env
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

# TikHub
TIKHUB_API_KEY: str = os.getenv("TIKHUB_API_KEY", "")

# 飞书多维表
FEISHU_BITABLE_APP_TOKEN: str = os.getenv("FEISHU_BITABLE_APP_TOKEN", "")
FEISHU_HOTPOSTS_TABLE_ID: str = os.getenv("FEISHU_HOTPOSTS_TABLE_ID", "")
FEISHU_GOLDWORDS_TABLE_ID: str = os.getenv("FEISHU_GOLDWORDS_TABLE_ID", "")
FEISHU_CONFIG_TABLE_ID: str = os.getenv("FEISHU_CONFIG_TABLE_ID", "")
FEISHU_PATTERNS_TABLE_ID: str = os.getenv("FEISHU_PATTERNS_TABLE_ID", "")

# 飞书自建应用（备用，供 Python 直接调 API 时使用）
FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")


def load_search_config() -> list[dict]:
    """从飞书配置表读取 is_active=True 的搜索配置。

    返回: [{"domain_word": str, "search_keyword": str, "priority": int}, ...]
    """
    # 延迟导入避免循环依赖
    from goldword.feishu import query_config

    all_records = query_config()
    active = []
    for rec in all_records:
        fields = rec.get("fields", {})
        is_active = fields.get("is_active", False)
        if not is_active:
            continue
        active.append({
            "domain_word": fields.get("domain_word", ""),
            "search_keyword": fields.get("search_keyword", ""),
            "priority": fields.get("priority", 99),
        })
    active.sort(key=lambda x: x["priority"])
    return active
