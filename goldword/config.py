"""配置管理：加载 .env 环境变量，对外暴露常量。"""

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

# 飞书自建应用（备用，供 Python 直接调 API 时使用）
FEISHU_APP_ID: str = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET: str = os.getenv("FEISHU_APP_SECRET", "")
