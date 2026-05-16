"""Test tracker.py: verify _list_records fix and trend tracking logic."""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# 1. Test _list_records fix (shell=True instead of bash -c)
print("=== Test 1: query_words via shell=True ===")
from goldword.feishu import query_words

words = query_words(limit=5)
print(f"  Count: {len(words)}")
for w in words[:3]:
    f = w["fields"]
    word_val = f.get("word", "?")
    cat_val = f.get("category", "?")
    freq_val = f.get("frequency", "?")
    trend_val = f.get("trend", "?")
    print(f"  {word_val} | cat={cat_val} | freq={freq_val} | trend={trend_val}")

# 2. Test _build_word_index
print("\n=== Test 2: _build_word_index ===")
from goldword.tracker import _build_word_index

index = _build_word_index()
print(f"  Index size: {len(index)}")
# Show a few entries
for i, ((cat, wl), entry) in enumerate(index.items()):
    if i >= 5:
        break
    print(f"  ({cat}, {wl}) -> freq={entry['frequency']} trend={entry['trend']}")

# 3. Test track_words with a known word (should match existing)
print("\n=== Test 3: track_words (existing word) ===")
from goldword.tracker import track_words

if words:
    sample = words[0]["fields"]
    candidates = [{
        "word": sample["word"],
        "category": sample.get("category", ""),
        "source_field": sample.get("source_field", "title"),
        "vibe_score": sample.get("vibe_score", 5),
    }]
    tracked = track_words(candidates)
    for t in tracked:
        print(f"  {t['word']} -> is_new={t['is_new']} trend={t['trend']} freq={t['frequency']}")

# 4. Test track_words with a new word (should NOT match)
print("\n=== Test 4: track_words (new word) ===")
new_candidates = [{
    "word": "测试金词_tracker_验证",
    "category": "feel",
    "source_field": "title",
    "vibe_score": 3,
}]
tracked_new = track_words(new_candidates)
for t in tracked_new:
    print(f"  {t['word']} -> is_new={t['is_new']} trend={t['trend']}")

# 5. Test track_patterns
print("\n=== Test 5: track_patterns ===")
from goldword.tracker import track_patterns, _build_pattern_index

pindex = _build_pattern_index()
print(f"  Pattern index size: {len(pindex)}")
for skel in list(pindex.keys())[:3]:
    print(f"  {skel}")

# Match existing pattern
if pindex:
    first_skeleton = list(pindex.keys())[0]
    pat_candidates = [{"skeleton": first_skeleton, "category": "对比", "examples": ["测试example"]}]
    tracked_pats = track_patterns(pat_candidates)
    for tp in tracked_pats:
        print(f"  Match: {tp['skeleton'][:30]} -> is_new={tp['is_new']} freq={tp['frequency']}")

print("\n=== All tests done ===")
