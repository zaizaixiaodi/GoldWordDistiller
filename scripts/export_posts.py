"""批量蒸馏流水线 · 第 1 步 — 从飞书热贴库导出所有帖子，按 domain 分组。

输出: workspace/distilled/posts_for_redistill.json
下游: scripts/format_batch.py 读此文件切批次
完整流水线见 .claude/commands/distill.md
"""
import json, sys, io
from pathlib import Path
from goldword import feishu

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

posts = feishu.query_posts()  # 默认拉全量（_list_records 自动翻页）
by_domain = {}
for p in posts:
    f = p["fields"]
    d = f.get("domain", "") or "未分类"
    by_domain.setdefault(d, []).append(p)

out = {}
for domain, domain_posts in sorted(by_domain.items()):
    items = []
    for p in domain_posts:
        f = p["fields"]
        cover_text = f.get("封面文案输出结果", "")
        if cover_text and "上传图片" in cover_text:
            cover_text = ""
        items.append({
            "record_id": p["record_id"],
            "title": f.get("title", ""),
            "desc": f.get("desc", "")[:300],
            "cover_text": cover_text,
            "like": f.get("like_count", 0),
            "collect": f.get("collect_count", 0),
            "domain": domain,
        })
    out[domain] = items

outfile = Path("workspace/distilled/posts_for_redistill.json")
outfile.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"已导出到 {outfile}")
for d, items in sorted(out.items()):
    print(f"  {d}: {len(items)} 条")
