"""批量蒸馏流水线 · 第 2 步 — 按 domain 切批次，输出蒸馏 prompt 输入格式。

用法:
    python scripts/format_batch.py <domain> [start] [limit]
    python scripts/format_batch.py --rids rid1,rid2,...    # 按 record_id 精确选

依赖: 先跑 scripts/export_posts.py 生成 workspace/distilled/posts_for_redistill.json
下游: stdout 内容由 AI 接走，按 prompts/distill.md 蒸馏后写到 batch_<标签>_result.json
完整流水线见 .claude/commands/distill.md
"""
import argparse
import io
import json
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

parser = argparse.ArgumentParser()
parser.add_argument("domain", nargs="?", help="按领域筛选；与 --rids 互斥")
parser.add_argument("start", nargs="?", type=int, default=0, help="批次起始 idx")
parser.add_argument("limit", nargs="?", type=int, default=50, help="批次大小")
parser.add_argument(
    "--rids",
    help="按 record_id 精确过滤（逗号分隔，遍历所有 domain）。出现时 domain/start/limit 被忽略",
)
args = parser.parse_args()

data = json.load(open("workspace/distilled/posts_for_redistill.json", encoding="utf-8"))

if args.rids:
    wanted = {r.strip() for r in args.rids.split(",") if r.strip()}
    batch = []
    label = ""
    for domain_key, posts in data.items():
        for p in posts:
            if p["record_id"] in wanted:
                # 复制并标记真正的 domain
                p2 = dict(p)
                p2["_actual_domain"] = domain_key
                batch.append(p2)
    label = f"--rids ({len(batch)}/{len(wanted)} 命中)"
    print(f"{label}")
else:
    if not args.domain:
        parser.error("必须给 domain 或 --rids")
    posts = data.get(args.domain, [])
    batch = posts[args.start : args.start + args.limit]
    for p in batch:
        p["_actual_domain"] = args.domain
    print(
        f"domain: {args.domain}  batch: [{args.start}-{args.start + len(batch)}]  total available: {len(posts)}"
    )

for p in batch:
    cover = p.get("cover_text", "").strip()
    cover_line = f"\n封面文案: {cover}" if cover else "\n封面文案: (空)"
    desc = p.get("desc", "").strip()[:300]
    desc_line = f"\n正文（摘要）: {desc}" if desc else ""
    dom = p.get("_actual_domain", "")
    print(
        f"\n[{p['record_id']}] {p['title']} | 点赞: {p['like']} | 收藏: {p['collect']} | 关键词: {dom}{desc_line}{cover_line}"
    )
