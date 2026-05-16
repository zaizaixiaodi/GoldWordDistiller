"""平台直出：TikHub 搜索 + 笔记详情 + 热榜采集。"""

from __future__ import annotations

import json as _json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import requests

from goldword.config import TIKHUB_API_KEY

BASE = "https://api.tikhub.io"
HEADERS = {"Authorization": f"Bearer {TIKHUB_API_KEY}"}

# 原始 API 返回落盘目录（永久存档，避免重复查询）
_raw_dir = Path(__file__).resolve().parent.parent / "scripts" / "samples" / "raw"
_raw_dir.mkdir(parents=True, exist_ok=True)
_batch_ts: str = ""  # 由 harvest_all 设置，同批次共享时间戳


def _save_raw(name: str, data: dict) -> None:
    """保存原始 API 返回 JSON，永久存档。"""
    ts = _batch_ts or datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = _raw_dir / f"{ts}_{name}.json"
    fname.write_text(_json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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
    cover_url: str = ""  # 封面/缩略图
    search_keyword: str = ""
    source: str = "search"  # search / hotlist
    harvested_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def to_dict(self) -> dict:
        return {
            "post_id": self.post_id,
            "title": self.title,
            "desc": self.desc,
            "url": {"link": self.url, "text": self.title[:50] or self.url[:50]} if self.url else None,
            "author": self.author,
            "note_type": self.note_type,
            "like_count": self.like_count,
            "collect_count": self.collect_count,
            "comment_count": self.comment_count,
            "share_count": self.share_count,
            "cover_url": self.cover_url,
            "search_keyword": self.search_keyword,
            "source": self.source,
            "harvested_at": self.harvested_at,
        }


def _api_get(path: str, params: dict | None = None, timeout: int = 30, retries: int = 2) -> dict | None:
    for attempt in range(retries + 1):
        try:
            resp = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=timeout)
            if resp.status_code != 200:
                print(f"  [TikHub] {path} → HTTP {resp.status_code}: {resp.text[:200]}")
                return None
            return resp.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt < retries:
                wait = (attempt + 1) * 2
                print(f"  [TikHub] 连接错误 ({e}), {wait}s 后重试...")
                time.sleep(wait)
            else:
                print(f"  [TikHub] 连接失败, 已重试{retries}次: {e}")
                return None


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
    _save_raw(f"search_{keyword}_p{page}", data)

    items = data.get("data", {}).get("data", {}).get("items", [])
    posts: list[RawPost] = []
    for item in items:
        note = item.get("note", {})
        if not note.get("id"):
            continue
        note_id = note["id"]
        xsec_token = note.get("xsec_token", "")
        url = f"https://www.xiaohongshu.com/explore/{note_id}"
        if xsec_token:
            url += f"?xsec_token={xsec_token}&xsec_source=pc_search"

        # 封面图：统一用 images_list[cover_index]，视频的 video_info_v2.image.thumbnail
        # 是自动截取的视频帧（/frame/ 路径），不是博主上传的封面
        cover_url = ""
        images_list = note.get("images_list", [])
        cover_idx = note.get("cover_image_index", 0)
        if images_list and cover_idx < len(images_list):
            cover_url = (
                images_list[cover_idx].get("url_size_large", "")
                or images_list[cover_idx].get("url", "")
            )

        posts.append(
            RawPost(
                post_id=note_id,
                title=note.get("title", ""),
                desc=note.get("abstract_show", ""),
                url=url,
                author=note.get("user", {}).get("nickname", ""),
                note_type=note.get("type", "normal"),
                like_count=note.get("liked_count", 0),
                collect_count=note.get("collected_count", 0),
                comment_count=note.get("comments_count", 0),
                share_count=note.get("shared_count", 0),
                cover_url=cover_url,
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
    _save_raw(f"detail_{note_id}", data)

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
    _save_raw("hotlist", data)

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
        try:
            fetch_note_detail(post)
        except Exception as e:
            print(f"  [harvester] 获取详情失败 {post.post_id}: {e}")
        count += 1
        time.sleep(0.8)  # 增加间隔避免触发限流
    return posts


# ── 端到端采集管道 ───────────────────────────────────────────────────────

@dataclass
class HarvestResult:
    """一次 /harvest 的结果汇总。"""

    total_searched: int = 0
    total_hotlist: int = 0
    total_inserted: int = 0
    total_duplicates: int = 0
    api_calls: int = 0
    cover_parsed: int = 0
    cover_failed: int = 0
    keywords_used: list[str] = field(default_factory=list)


def harvest_all(dry_run: bool = False) -> HarvestResult:
    """端到端采集：读配置 → 遍历搜索词 → 去重 → 写热贴库。

    不蒸馏，只沉淀数据。dry_run=True 时只打印计划不实际执行。
    """
    global _batch_ts
    _batch_ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    from goldword.config import load_search_config
    from goldword.feishu import batch_insert_posts, query_posts

    result = HarvestResult()

    # 1. 读配置
    configs = load_search_config()
    if not configs:
        print("[harvest] 配置表无活跃搜索词，退出。")
        return result

    result.keywords_used = [c["search_keyword"] for c in configs]

    if dry_run:
        print("[harvest --dry-run] 计划执行的搜索：")
        for c in configs:
            print(f"  {c['domain_word']} → {c['search_keyword']} (优先级 {c['priority']})")
        est_api = len(configs)  # 每个 keyword 1 次搜索
        est_detail = sum(min(20, 20) for _ in configs)  # 每词最多 20 次详情
        print(f"\n  预估 API 调用: 搜索 {est_api} 次 + 详情最多 {est_detail} 次")
        return result

    # 2. 去重：获取热贴库已有 post_id
    print("[harvest] 读取已有热贴去重表 ...")
    existing_posts = query_posts(limit=500)
    existing_ids = set()
    for rec in existing_posts:
        pid = rec.get("fields", {}).get("post_id", "")
        if pid:
            existing_ids.add(pid)
    print(f"  已有 {len(existing_ids)} 条记录，跳过重复")

    # 3. 遍历搜索词
    all_new_posts: list[dict] = []

    for cfg in configs:
        keyword = cfg["search_keyword"]
        domain = cfg["domain_word"]
        print(f"\n[harvest] 搜索: {keyword} (领域: {domain})")

        posts = search_with_detail(keyword, max_detail=15, detail_types={"normal"})
        result.api_calls += 1 + min(len(posts), 15)

        new_count = 0
        for p in posts:
            if p.post_id in existing_ids:
                result.total_duplicates += 1
                continue
            record = p.to_dict()
            record["_cover_url"] = p.cover_url  # 保留在备份中，写飞书时剔除
            record["domain"] = domain
            all_new_posts.append(record)
            existing_ids.add(p.post_id)
            new_count += 1
        result.total_searched += len(posts)
        print(f"  搜到 {len(posts)} 条，新增 {new_count} 条")

    # 4. 热榜
    print("\n[harvest] 拉取热榜 ...")
    hot_posts = fetch_hotlist()
    result.api_calls += 1
    new_hot = 0
    for p in hot_posts:
        if p.post_id in existing_ids:
            result.total_duplicates += 1
            continue
        record = p.to_dict()
        record["_cover_url"] = p.cover_url
        all_new_posts.append(record)
        existing_ids.add(p.post_id)
        new_hot += 1
    result.total_hotlist = len(hot_posts)
    print(f"  热榜 {len(hot_posts)} 条，新增 {new_hot} 条")

    # 5. 本地备份（写入飞书前先存档，防止数据丢失）
    if all_new_posts:
        _backup_dir = Path(__file__).resolve().parent.parent / "scripts" / "samples"
        _backup_dir.mkdir(parents=True, exist_ok=True)
        _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        _backup_file = _backup_dir / f"harvest_{_ts}.json"
        _backup_file.write_text(
            _json.dumps(all_new_posts, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[harvest] 本地备份: {_backup_file} ({len(all_new_posts)} 条)")

    # 6. 批量写入飞书（每批最多 10 条）
    if all_new_posts:
        print(f"[harvest] 写入飞书热贴库 ({len(all_new_posts)} 条) ...")
        batch_size = 10
        for i in range(0, len(all_new_posts), batch_size):
            batch = all_new_posts[i : i + batch_size]
            # 提取封面 URL 后剔除（飞书表无此字段）
            batch_covers = [r.pop("_cover_url", "") for r in batch]
            # 本地备份保留 _cover_url，写飞书的副本去掉
            feishu_batch = [{k: v for k, v in r.items() if k not in ("cover_url",)}
                           for r in batch]
            ids = batch_insert_posts(feishu_batch)
            result.total_inserted += len(ids)
            # 记录 (record_id, cover_url) 用于上传
            for j, rid in enumerate(ids):
                if batch_covers[j]:
                    cover_tasks.append((rid, batch_covers[j]))
            print(f"  批次 {i // batch_size + 1}: 写入 {len(ids)} 条")
    else:
        print("\n[harvest] 无新数据需要写入")

    # 7. 上传封面图
    if cover_tasks:
        from goldword.feishu import download_cover, upload_cover, update_cover_attachment

        print(f"\n[harvest] 上传封面图 ({len(cover_tasks)} 张) ...")
        ok = 0
        for idx, (rid, cover_url) in enumerate(cover_tasks):
            local_path = download_cover(cover_url, rid)
            if not local_path:
                continue
            file_token = upload_cover(local_path)
            if not file_token:
                continue
            if update_cover_attachment(rid, file_token):
                ok += 1
            # 进度提示
            if (idx + 1) % 20 == 0:
                print(f"  封面进度: {idx + 1}/{len(cover_tasks)} ({ok} OK)")
        result.cover_parsed = ok
        result.cover_failed = len(cover_tasks) - ok
        print(f"  封面上传完成: {ok} 成功 / {result.cover_failed} 失败")

    return result

# ── 封面对回填 ───────────────────────────────────────────────────────────

def backfill_covers(dry_run: bool = False) -> int:
    """回填已有热贴库记录的封面图：搜索关键词 → 匹配 post_id → 下载+上传。

    只搜索不调详情 API，cover_url 在搜索结果中直接返回，成本低。
    """
    from goldword.config import FEISHU_HOTPOSTS_TABLE_ID, load_search_config
    from goldword.feishu import (
        _list_records,
        download_cover,
        update_cover_attachment,
        upload_cover,
    )

    print("[backfill] 读取热贴库记录 ...")
    all_records = []
    offset = 0
    while True:
        page = _list_records(FEISHU_HOTPOSTS_TABLE_ID, limit=200, offset=offset)
        if not page:
            break
        all_records.extend(page)
        offset += 200
        if len(page) < 200:
            break
    print(f"  共 {len(all_records)} 条记录")
    no_cover = {}  # post_id → record_id
    has_cover = 0
    for rec in all_records:
        fields = rec.get("fields", {})
        pid = fields.get("post_id", "")
        if not pid:
            continue
        existing = fields.get("封面", [])
        if existing and isinstance(existing, list) and len(existing) > 0:
            has_cover += 1
        else:
            no_cover[pid] = rec["record_id"]
    print(f"  已有封面: {has_cover}, 待回填: {len(no_cover)}")

    if not no_cover:
        return 0
    if dry_run:
        print(f"[backfill --dry-run] 将回填 {len(no_cover)} 条")
        return 0

    configs = load_search_config()
    done = 0
    for cfg in configs:
        keyword = cfg["search_keyword"]
        print(f"\n[backfill] 搜索: {keyword} ...")
        posts = search_notes(keyword)
        matched = 0
        for p in posts:
            if p.post_id not in no_cover or not p.cover_url:
                continue
            rid = no_cover[p.post_id]
            print(f"  匹配: {p.post_id} → {rid}")
            local = download_cover(p.cover_url, rid)
            if not local:
                continue
            ft = upload_cover(local)
            if not ft:
                continue
            if update_cover_attachment(rid, ft):
                done += 1
                matched += 1
            if done % 10 == 0:
                print(f"  回填进度: {done}/{len(no_cover)}")
        print(f"  {keyword}: 匹配 {matched}, 累计 {done}")
    print(f"\n[backfill] 完成: {done} 成功, {len(no_cover) - done} 未匹配")
    return done


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
