"""平台直出：TikHub 搜索 + 笔记详情 + 热榜采集。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import requests

from goldword.config import TIKHUB_API_KEY

BASE = "https://api.tikhub.io"
HEADERS = {"Authorization": f"Bearer {TIKHUB_API_KEY}"}


@dataclass
class RawPost:
    """TikHub 采集到的原始帖子。"""

    post_id: str
    title: str
    desc: str
    url: str
    author: str
    note_type: str  # video / normal
    like_count: int
    collect_count: int
    comment_count: int
    share_count: int
    search_keyword: str = ""
    source: str = "search"  # search / hotlist
    harvested_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "title": self.title,
            "desc": self.desc,
            "url": self.url,
            "author": self.author,
            "note_type": self.note_type,
            "like_count": self.like_count,
            "collect_count": self.collect_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "search_keyword": self.search_keyword,
            "source": self.source,
            "harvested_at": self.harvested_at,
        }


def _api_get(path: str, params: dict | None = None, timeout: int = 30) -> dict | None:
    resp = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=timeout)
    if resp.status_code != 200:
        print(f"  [TikHub] {path} → HTTP {resp.status_code}: {resp.text[:200]}")
        return None
    return resp.json()


# ── 搜索 ─────────────────────────────────────────────────────────────────

def search_notes(
    keyword: str,
    page: int = 1,
    sort_type: str = "popularity_descending",
    note_type: str = "",
    time_filter: str = "",
) -> list[RawPost]:
    """搜索笔记，返回第 page 页结果。"""
    params: dict = {
        "keyword": keyword,
        "page": page,
        "sort_type": sort_type,
    }
    if note_type:
        params["note_type"] = note_type
    if time_filter:
        params["time_filter"] = time_filter

    data = _api_get("/api/v1/xiaohongshu/app_v2/search_notes", params)
    if not data:
        return []

    items = data.get("data", {}).get("data", {}).get("items", [])
    posts: list[RawPost] = []
    for item in items:
        note = item.get("note", {})
        if not note.get("id"):
            continue
        posts.append(
            RawPost(
                post_id=note["id"],
                title=note.get("title", ""),
                desc=note.get("abstract_show", ""),
                url=f"https://www.xiaohongshu.com/explore/{note['id']}",
                author=note.get("user", {}).get("nickname", ""),
                note_type=note.get("type", "normal"),
                like_count=note.get("liked_count", 0),
                collect_count=note.get("collected_count", 0),
                comment_count=note.get("comments_count", 0),
                share_count=note.get("shared_count", 0),
                search_keyword=keyword,
                source="search",
            )
        )
    return posts


# ── 笔记详情 ─────────────────────────────────────────────────────────────

def fetch_note_detail(post: RawPost) -> RawPost:
    """获取笔记详情（完整正文 + 链接），就地更新 post 并返回。"""
    note_id = post.post_id
    # 根据类型选端点，但实测 image 端点对 video 也能返回
    endpoint = "/api/v1/xiaohongshu/app_v2/get_image_note_detail"
    if post.note_type == "video":
        endpoint = "/api/v1/xiaohongshu/app_v2/get_video_note_detail"

    data = _api_get(endpoint, {"note_id": note_id})
    if not data:
        return post

    # data.data 是 list → 取第一个元素 → note_list → 取第一条
    outer = data.get("data", {}).get("data", [])
    if isinstance(outer, list) and outer:
        note_list = outer[0].get("note_list", [])
        if note_list:
            detail = note_list[0]
            post.desc = detail.get("desc", post.desc)
            post.like_count = detail.get("liked_count", post.like_count)
            post.collect_count = detail.get("collected_count", post.collect_count)
            post.comment_count = detail.get("comments_count", post.comment_count)
            # 链接
            share_info = detail.get("share_info", {})
            post.url = share_info.get("link", "")

    return post


# ── 热榜 ──────────────────────────────────────────────────────────────────

def fetch_hotlist() -> list[RawPost]:
    """拉取小红书热榜。"""
    data = _api_get("/api/v1/xiaohongshu/web_v2/fetch_hot_list")
    if not data:
        return []

    items = data.get("data", {}).get("data", {}).get("items", [])
    posts: list[RawPost] = []
    for item in items:
        title = item.get("title", "")
        if not title:
            continue
        posts.append(
            RawPost(
                post_id=item.get("id", ""),
                title=title,
                desc="",
                url="",
                author="",
                note_type="",
                like_count=0,
                collect_count=0,
                comment_count=0,
                share_count=0,
                source="hotlist",
            )
        )
    return posts


# ── 便捷：搜索 + 补详情 ──────────────────────────────────────────────────

def search_with_detail(
    keyword: str,
    page: int = 1,
    sort_type: str = "popularity_descending",
    max_detail: int = 20,
    detail_types: set[str] | None = None,
) -> list[RawPost]:
    """搜索笔记并自动补充详情（完整正文 + 链接）。

    max_detail: 最多补多少条详情（每条详情 = 1 次 API 调用）。
    detail_types: 只对这些类型的笔记补详情，默认只对 normal（图文）。
    """
    if detail_types is None:
        detail_types = {"normal"}

    posts = search_notes(keyword, page=page, sort_type=sort_type)
    count = 0
    for post in posts:
        if count >= max_detail:
            break
        if post.note_type not in detail_types:
            continue
        fetch_note_detail(post)
        count += 1
        time.sleep(0.5)
    return posts


# ── CLI 入口 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    keyword = sys.argv[1] if len(sys.argv) > 1 else "副业"
    print(f"=== 搜索: {keyword} ===")
    posts = search_with_detail(keyword, max_detail=5)
    for p in posts:
        print(f"\n[{p.note_type}] {p.title}")
        print(f"  作者: {p.author} | 点赞: {p.like_count} | 收藏: {p.collect_count}")
        print(f"  正文: {p.desc[:100]}...")
        print(f"  链接: {p.url[:80]}...")
