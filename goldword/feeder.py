"""他山之石：手动素材输入（PRD v2 §3.2）。

从 URL / 文本 / 文件提取内容，供 Claude 蒸馏分析。
提取后走同一 distill 流程，source 标记为"他山之石"。
"""

from __future__ import annotations

import re
from pathlib import Path

import requests


def feed_url(url: str) -> dict:
    """从 URL 提取内容。小红书链接走 TikHub API，其他走 requests。"""
    if "xiaohongshu.com" in url or "xhslink.com" in url:
        return _feed_xhs_url(url)
    return _feed_generic_url(url)


def _feed_xhs_url(url: str) -> dict:
    """通过 TikHub API 获取小红书笔记内容。"""
    from goldword.harvester import RawPost, _api_get

    # 短链先解析
    if "xhslink.com" in url:
        try:
            resp = requests.head(url, allow_redirects=True, timeout=10)
            url = str(resp.url)
        except Exception as e:
            return {"error": f"短链解析失败: {e}"}

    match = re.search(r"/explore/([a-f0-9]+)", url) or re.search(r"/discovery/item/([a-f0-9]+)", url)
    if not match:
        return {"error": f"无法从 URL 提取笔记 ID: {url}"}

    note_id = match.group(1)

    # 尝试图文详情，失败再试视频
    data = _api_get("/api/v1/xiaohongshu/app_v2/get_image_note_detail", {"note_id": note_id})
    if not data:
        data = _api_get("/api/v1/xiaohongshu/app_v2/get_video_note_detail", {"note_id": note_id})
    if not data:
        return {"error": f"TikHub 获取笔记详情失败: {note_id}"}

    outer = data.get("data", {}).get("data", [])
    if isinstance(outer, list) and outer:
        note_list = outer[0].get("note_list", [])
        if note_list:
            detail = note_list[0]
            return {
                "title": detail.get("title", ""),
                "content": detail.get("desc", ""),
                "url": url,
                "author": detail.get("user", {}).get("nickname", ""),
                "like_count": detail.get("liked_count", 0),
                "collect_count": detail.get("collected_count", 0),
                "source": "他山之石",
                "post_id": note_id,
            }

    return {"error": f"笔记内容解析失败: {note_id}"}


def _feed_generic_url(url: str) -> dict:
    """通用 URL 抓取（非小红书）。"""
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        # 尝试 UTF-8 解码
        text = resp.content.decode("utf-8", errors="replace")
        return {
            "title": url,
            "content": text[:8000],
            "url": url,
            "source": "他山之石",
        }
    except Exception as e:
        return {"error": f"抓取失败: {e}"}


def feed_text(text: str, domain: str | None = None) -> dict:
    """直接接受文本内容。"""
    return {
        "title": text[:50] + ("..." if len(text) > 50 else ""),
        "content": text,
        "domain": domain,
        "source": "他山之石",
    }


def feed_file(path: str) -> dict:
    """从文件读取内容。"""
    p = Path(path)
    if not p.exists():
        return {"error": f"文件不存在: {path}"}
    content = p.read_text(encoding="utf-8", errors="replace")
    return {
        "title": p.stem,
        "content": content,
        "file_path": str(p),
        "source": "他山之石",
    }


if __name__ == "__main__":
    import sys
    import io
    import json

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print("Usage: feeder.py <url|text|file>")
        sys.exit(1)

    arg = sys.argv[1]
    if arg.startswith("http"):
        result = feed_url(arg)
    elif Path(arg).exists():
        result = feed_file(arg)
    else:
        result = feed_text(arg)

    print(json.dumps(result, ensure_ascii=False, indent=2))
