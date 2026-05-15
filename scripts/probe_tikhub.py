"""TikHub 接口探测脚本：搜索笔记 + 热榜，各调 1 次，dump 原始 JSON。"""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from goldword.config import TIKHUB_API_KEY

BASE = "https://api.tikhub.io"
HEADERS = {"Authorization": f"Bearer {TIKHUB_API_KEY}"}
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "samples")
os.makedirs(SAMPLES_DIR, exist_ok=True)


def probe_search(keyword: str = "副业"):
    """搜索笔记，取第 1 页，按热度排序。"""
    resp = requests.get(
        f"{BASE}/api/v1/xiaohongshu/app_v2/search_notes",
        headers=HEADERS,
        params={"keyword": keyword, "page": 1, "sort_type": "popularity_descending"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[search] HTTP {resp.status_code}: {resp.text[:500]}")
        return None
    data = resp.json()

    out = os.path.join(SAMPLES_DIR, "search_notes.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    items = data.get("data", {}).get("data", {}).get("items", [])
    print(f"[search] keyword={keyword!r}, got {len(items)} items, saved to {out}")
    return data


def probe_hotlist():
    """小红书热榜。"""
    resp = requests.get(
        f"{BASE}/api/v1/xiaohongshu/web_v2/fetch_hot_list",
        headers=HEADERS,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"[hotlist] HTTP {resp.status_code}: {resp.text[:500]}")
        return None
    data = resp.json()

    out = os.path.join(SAMPLES_DIR, "hot_list.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    items = data.get("data", {}).get("data", [])
    print(f"[hotlist] got {len(items)} items, saved to {out}")
    return data


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "副业"
    print(f"Probing TikHub with keyword={keyword!r} ...")
    probe_search(keyword)
    probe_hotlist()
    print("Done. Check scripts/samples/ for raw JSON.")
