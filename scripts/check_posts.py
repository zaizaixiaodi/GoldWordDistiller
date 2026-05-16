"""批量蒸馏流水线 · 辅助 — 统计 posts_for_redistill.json 各 domain 帖子数。

用于 export_posts 跑完后预估蒸馏工作量、规划批次切分。
完整流水线见 .claude/commands/distill.md
"""
import json
d = json.load(open("workspace/distilled/posts_for_redistill.json", encoding="utf-8"))
total = 0
for k, v in sorted(d.items()):
    print(f"{k}: {len(v)}")
    total += len(v)
print(f"Total: {total}")
