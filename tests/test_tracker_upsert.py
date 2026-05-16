"""Test tracker upsert: verify update (existing) and insert (new) to Feishu."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "D:/AI Agent/金词挖掘机")

from goldword.tracker import track_words, upsert_words, track_patterns, upsert_patterns

# 1. Test upsert existing word (should UPDATE, freq+1)
print("=== Test upsert: existing word ===")
from goldword.feishu import query_words
words = query_words(limit=5)
sample = words[0]["fields"]
from goldword.tracker import _unwrap
word_val = _unwrap(sample.get("word", ""))
cat_val = _unwrap(sample.get("category", ""))
freq_before = _unwrap(sample.get("frequency", 1))
print(f"  Before: {word_val} freq={freq_before}")

candidates = [{"word": word_val, "category": cat_val, "source_field": "title", "vibe_score": 5}]
tracked = track_words(candidates)
result = upsert_words(tracked)
print(f"  Upsert result: {result}")

# Verify
words2 = query_words(limit=5)
for w in words2:
    f2 = w["fields"]
    if _unwrap(f2.get("word", "")) == word_val:
        freq_after = _unwrap(f2.get("frequency", 1))
        trend_after = _unwrap(f2.get("trend", ""))
        print(f"  After: {word_val} freq={freq_after} trend={trend_after}")
        break

# 2. Test insert new word (should INSERT)
print("\n=== Test upsert: new word ===")
new_word = f"tracker_test_{_unwrap(words[0]['fields'].get('word',''))[:3]}"
new_candidates = [{"word": new_word, "category": "feel", "source_field": "title", "vibe_score": 3, "domain": "搞钱"}]
tracked_new = track_words(new_candidates)
print(f"  Tracked: is_new={tracked_new[0]['is_new']}")
result2 = upsert_words(tracked_new)
print(f"  Insert result: {result2}")

# 3. Test pattern upsert (existing)
print("\n=== Test upsert: existing pattern ===")
from goldword.feishu import query_patterns
pats = query_patterns(limit=3)
if pats:
    pat_sample = pats[0]["fields"]
    skel = _unwrap(pat_sample.get("skeleton", ""))
    pat_cands = [{"skeleton": skel, "category": "清单", "examples": ["tracker测试example"]}]
    tracked_pat = track_patterns(pat_cands)
    pat_result = upsert_patterns(tracked_pat)
    print(f"  Pattern upsert: {pat_result}")

print("\n=== Upsert tests done ===")
