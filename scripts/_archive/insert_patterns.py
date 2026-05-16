"""Insert 15 abstract skeletons (human-readable naming) into Feishu patterns table."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from goldword.feishu import insert_pattern

BASE = Path(__file__).parent
today_ts = int(datetime.now().timestamp() * 1000)

# Load 15 abstract skeletons
with open(BASE / "abstract_skeletons.json", "r", encoding="utf-8") as f:
    skeletons = json.load(f)

print(f"Loaded {len(skeletons)} skeletons")

ok = 0
fail = 0
for s in skeletons:
    record = {
        "skeleton": s["skeleton"],
        "category": s["category"],
        "examples": "\n".join(s.get("examples", [])),
        "frequency": len(s.get("examples", [])),
        "first_seen": today_ts,
        "last_seen": today_ts,
        "trend": "新句式",
    }
    try:
        insert_pattern(record)
        ok += 1
        print(f"  OK: {s['skeleton']}")
    except Exception as e:
        fail += 1
        print(f"  FAIL: {s['skeleton']} -> {str(e)[:120]}")

print(f"\nDone: {ok} inserted, {fail} failed")
