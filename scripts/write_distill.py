"""批量蒸馏流水线 · 第 4 步 — 把蒸馏结果 JSON 写回飞书金词库 + 句式库。

用法:
    python scripts/write_distill.py --input workspace/distilled/batch_<标签>_result.json

输入 JSON 结构: {"gold_words": [...], "patterns": [...]}
经 goldword.tracker 打趋势标签后 upsert 到飞书
完整流水线见 .claude/commands/distill.md
"""
import json, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from goldword.tracker import track_words, upsert_words, track_patterns, upsert_patterns, refresh_trends

def write_results(gold_words: list[dict], patterns: list[dict], batch_label: str = ""):
    """Track and upsert gold words and patterns to feishu."""
    print(f"[{batch_label}] 追踪 {len(gold_words)} 金词 + {len(patterns)} 句式 ...")

    if gold_words:
        tracked = track_words(gold_words)
        r = upsert_words(tracked)
        print(f"  金词: insert {r['inserted']} / update {r['updated']} / error {r['errors']}")

    if patterns:
        tracked = track_patterns(patterns)
        r = upsert_patterns(tracked)
        print(f"  句式: insert {r['inserted']} / update {r['updated']} / error {r['errors']}")

    refresh_trends()
    print(f"  [{batch_label}] 完成")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSON file with gold_words and patterns")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    write_results(
        data.get("gold_words", []),
        data.get("patterns", []),
        batch_label=data.get("_batch_label", Path(args.input).stem),
    )
