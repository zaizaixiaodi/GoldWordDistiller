"""Batch insert distilled gold words into Feishu gold words table."""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from goldword.feishu import batch_insert_words

BASE = Path(__file__).parent

# Load merged distillation results
with open(BASE / "distilled_merged.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Load post_id -> domain/record_id mapping
with open(BASE / "pid_mapping.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)
pid2domain = mapping["pid2domain"]
pid2rid = mapping["pid2rid"]

today_ts = int(datetime.now().timestamp() * 1000)  # Feishu date = unix ms

def get_domain(related_ids):
    """Determine domain from related post IDs."""
    domains = set()
    for rid in related_ids:
        # rid here is a feishu record_id, but our data has post_ids
        # Need to check: related_post_ids in distilled data are record_ids
        d = pid2domain.get(rid, "")
        if d:
            domains.add(d)
    if not domains:
        return "搞钱"  # default
    if len(domains) == 1:
        return domains.pop()
    # Multiple domains -> pick the most common one, or just use first
    return list(domains)[0]

def get_related_record_ids(related_ids):
    """Convert post_ids to feishu record_ids for the 关联 field."""
    rids = []
    for pid in related_ids:
        rid = pid2rid.get(pid, "")
        if rid:
            rids.append(rid)
    return rids

# Format for Feishu
records = []
for gw in data["gold_words"]:
    domain = get_domain(gw["related_post_ids"])
    related_rids = get_related_record_ids(gw["related_post_ids"])

    record = {
        "word": gw["word"],
        "aliases": ", ".join(gw.get("aliases", [])) if gw.get("aliases") else "",
        "domain": domain,
        "category": gw["category"],
        "source_field": gw["source_field"],
        "vibe_score": gw["vibe_score"],
        "frequency": gw.get("frequency", 1),
        "first_seen": today_ts,
        "last_seen": today_ts,
        "trend": "新词",
        "source": "平台直出",
        "status": "待审",
    }
    # Only add related_posts if we have record IDs
    if related_rids:
        record["related_posts"] = related_rids

    records.append(record)

print(f"Prepared {len(records)} gold words for insertion")

# Batch insert (10 per batch)
batch_size = 10
total_inserted = 0
errors = 0

for i in range(0, len(records), batch_size):
    batch = records[i : i + batch_size]
    try:
        ids = batch_insert_words(batch)
        total_inserted += len(ids)
        print(f"  Batch {i // batch_size + 1}: {len(ids)} inserted")
    except Exception as e:
        errors += 1
        print(f"  Batch {i // batch_size + 1} ERROR: {e}")
        # Try one by one to find the bad record
        for rec in batch:
            try:
                from goldword.feishu import insert_word
                insert_word(rec)
                total_inserted += 1
            except Exception as e2:
                print(f"    Failed: {rec['word']} -> {e2}")

print(f"\nDone: {total_inserted} inserted, {errors} batch errors")
