"""端到端冒烟测试 — 单关键词搜索 → 写飞书热贴库 → 上传封面图。

用法:
    python scripts/probe/probe_one_keyword.py <keyword> <domain> [top_n] [--type video|normal|both]

例:
    python scripts/probe/probe_one_keyword.py 汇报 职场 5
    python scripts/probe/probe_one_keyword.py FIRE 搞钱 3 --type video

走 harvester + feishu 的真实接口，不蒸馏。蒸馏由 /distill 流水线后续接力。

鲁棒性保险：
- 搜索后立即把 (post_id, cover_url, title, ...) 落盘到 workspace/harvest_backups/probe_*.json，
  确保即使后续步骤失败，cover_url 仍可被回放
- download_cover 已加 UA / Referer / 重试，单图失败不阻塞其他图
"""
import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from goldword.feishu import (
    batch_insert_posts,
    download_cover,
    query_posts,
    update_cover_attachment,
    upload_cover,
)
from goldword.harvester import search_with_detail


def main(keyword: str, domain: str, top_n: int = 5, post_type: str = "both") -> None:
    print(f"=== 搜索: {keyword} | domain: {domain} | top {top_n} | type={post_type} ===\n")

    # 解析 type
    if post_type == "video":
        detail_types = {"video"}
    elif post_type == "normal":
        detail_types = {"normal"}
    else:
        detail_types = {"normal", "video"}

    # 1. 搜 top_n*5 条原始候选（提高过滤后命中率），按点赞排
    posts = search_with_detail(keyword, max_detail=top_n * 5, detail_types=detail_types)
    print(f"\n[probe] 搜到 {len(posts)} 条原始结果")

    # 按类型过滤
    if post_type in ("video", "normal"):
        posts = [p for p in posts if p.note_type == post_type]
        print(f"[probe] 按 type={post_type} 过滤后 {len(posts)} 条")

    # 按点赞排序取 top_n
    posts.sort(key=lambda p: p.like_count, reverse=True)
    posts = posts[:top_n]
    print(f"[probe] 按点赞排序取前 {len(posts)} 条:")
    for i, p in enumerate(posts):
        print(f"  [{i+1}] {p.title[:40]} | {p.note_type} | 点赞 {p.like_count}")

    if not posts:
        print("[probe] 无候选，退出")
        return

    # 2. 落盘备份（包含 cover_url，保险层）
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).resolve().parent.parent.parent / "workspace" / "harvest_backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_file = backup_dir / f"probe_{keyword}_{ts}.json"
    backup_file.write_text(
        json.dumps(
            [
                {
                    "post_id": p.post_id,
                    "title": p.title,
                    "note_type": p.note_type,
                    "cover_url": p.cover_url,
                    "like_count": p.like_count,
                    "domain": domain,
                }
                for p in posts
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[probe] 本地备份: {backup_file}")

    # 3. 去重
    existing = {r.get("fields", {}).get("post_id", "") for r in query_posts()}
    new_posts = [p for p in posts if p.post_id not in existing]
    print(f"\n[probe] 去重后 {len(new_posts)} 条新帖（{len(posts) - len(new_posts)} 条已存在）")
    if not new_posts:
        print("[probe] 全部已存在，无需写入")
        return

    # 4. 写飞书
    records = []
    cover_urls = []
    for p in new_posts:
        r = p.to_dict()
        r["domain"] = domain
        cover_urls.append(r.pop("cover_url", "") or "")
        records.append(r)

    print(f"\n[probe] 写入飞书热贴库 ...")
    ids = batch_insert_posts(records)
    print(f"  写入 {len(ids)} 条:")
    for rid, p in zip(ids, new_posts):
        print(f"    {rid}  {p.title[:40]}")

    # 5. 上传封面
    print(f"\n[probe] 上传封面图 ({sum(1 for u in cover_urls if u)} 张) ...")
    ok = 0
    fail = []
    for rid, cover_url, p in zip(ids, cover_urls, new_posts):
        if not cover_url:
            print(f"  [skip] {rid}: 无 cover_url ({p.title[:30]})")
            fail.append((rid, "no_url"))
            continue
        local = download_cover(cover_url, rid)
        if not local:
            print(f"  [fail] {rid}: 下载失败")
            fail.append((rid, "download"))
            continue
        ft = upload_cover(local)
        if not ft:
            print(f"  [fail] {rid}: 上传失败")
            fail.append((rid, "upload"))
            continue
        if update_cover_attachment(rid, ft):
            print(f"  [ok]   {rid}")
            ok += 1
        else:
            print(f"  [fail] {rid}: attach 失败")
            fail.append((rid, "attach"))
    print(f"\n[probe] 封面上传: {ok} 成功 / {len(fail)} 失败")
    if fail:
        print(f"[probe] 失败明细: {fail}")
        print(f"[probe] cover_url 仍在备份: {backup_file}")
    print(f"\n[probe] 已写入 record_ids: {ids}")
    print(f"[probe] 下一步: 等 30s+ 让飞书豆包识图，然后跑 /distill --rids {','.join(ids)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("domain", help="所属 domain（如 搞钱/职场/...）")
    parser.add_argument("top_n", nargs="?", type=int, default=5, help="取前 N 条")
    parser.add_argument(
        "--type",
        dest="post_type",
        choices=["video", "normal", "both"],
        default="both",
        help="筛选笔记类型",
    )
    args = parser.parse_args()
    main(args.keyword, args.domain, args.top_n, args.post_type)
