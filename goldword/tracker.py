"""趋势追踪：金词 + 句式双路。

把蒸馏产出的候选金词/句式与飞书历史数据比对，打趋势标签后写回。
- 新词：首次出现
- 上升：本次又出现（frequency+1）
- 平稳：上次是上升，本次未出现
- 下降：连续多批未出现（由 refresh_trends 处理）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from goldword import feishu


def _now_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


def _unwrap(val: Any) -> Any:
    """飞书 single-select 字段返回 list（如 ['twist']），取第一个元素。"""
    if isinstance(val, list) and len(val) == 1:
        return val[0]
    return val


# ── 金词趋势追踪 ────────────────────────────────────────────────────


def _build_word_index() -> dict[tuple[str, str], dict]:
    """从飞书金词库构建 (category, word_lower) → 记录索引。"""
    records = feishu.query_words(limit=500)
    index: dict[tuple[str, str], dict] = {}
    for rec in records:
        fields = rec.get("fields", {})
        word = str(_unwrap(fields.get("word", ""))).strip()
        cat = str(_unwrap(fields.get("category", ""))).strip()
        if not word or not cat:
            continue
        aliases_raw = _unwrap(fields.get("aliases", ""))
        aliases = [a.strip() for a in str(aliases_raw).split(",") if a.strip()]
        index[(cat, word.lower())] = {
            "record_id": rec["record_id"],
            "word": word,
            "aliases": aliases,
            "frequency": int(_unwrap(fields.get("frequency", 1)) or 1),
            "trend": str(_unwrap(fields.get("trend", "新词"))),
        }
    return index


def _find_match(
    word: str, category: str, index: dict[tuple[str, str], dict]
) -> dict | None:
    """在索引中查找匹配：先精确，再别名，再子串。"""
    wl = word.lower()

    # 1. 精确匹配
    entry = index.get((category, wl))
    if entry:
        return entry

    # 2. 别名 / 子串匹配（同 category 内）
    for (cat, _), entry in index.items():
        if cat != category:
            continue
        # 别名匹配
        if wl in [a.lower() for a in entry["aliases"]]:
            return entry
        # 双向子串（至少 2 字符）
        if len(wl) >= 2 and (wl in entry["word"].lower() or entry["word"].lower() in wl):
            return entry

    return None


def track_words(candidates: list[dict]) -> list[dict]:
    """比对候选金词与飞书历史，返回带趋势标签的结果。

    candidates: [{word, category, aliases?, domain?, source_field?, vibe_score?}]
    returns: [{... + trend, frequency, first_seen?, last_seen, is_new, record_id?}]
    """
    index = _build_word_index()
    now_ms = _now_ms()
    results: list[dict] = []

    for cand in candidates:
        word = str(_unwrap(cand.get("word", ""))).strip()
        cat = str(_unwrap(cand.get("category", ""))).strip()
        if not word or not cat:
            continue

        entry = _find_match(word, cat, index)

        if entry:
            new_freq = (entry["frequency"] or 1) + 1
            results.append({
                **cand,
                "trend": "上升",
                "frequency": new_freq,
                "last_seen": now_ms,
                "is_new": False,
                "record_id": entry["record_id"],
            })
        else:
            results.append({
                **cand,
                "trend": "新词",
                "frequency": cand.get("frequency", 1),
                "first_seen": now_ms,
                "last_seen": now_ms,
                "is_new": True,
            })

    return results


def upsert_words(tracked: list[dict]) -> dict[str, int]:
    """将追踪结果写回飞书：新词 insert，已有 update。"""
    now_ms = _now_ms()
    inserted = updated = errors = 0

    for t in tracked:
        try:
            if t["is_new"]:
                feishu.insert_word({
                    "word": t["word"],
                    "aliases": t.get("aliases", ""),
                    "domain": t.get("domain", "搞钱"),
                    "category": t["category"],
                    "source_field": t.get("source_field", "title"),
                    "vibe_score": t.get("vibe_score", 5),
                    "frequency": t.get("frequency", 1),
                    "first_seen": t.get("first_seen", now_ms),
                    "last_seen": t.get("last_seen", now_ms),
                    "trend": "新词",
                    "source": t.get("source", "平台直出"),
                    "status": "待审",
                })
                inserted += 1
            else:
                feishu.update_word(t["record_id"], {
                    "frequency": t["frequency"],
                    "last_seen": t["last_seen"],
                    "trend": "上升",
                })
                updated += 1
        except Exception as e:
            errors += 1
            print(f"  [tracker] upsert word failed: {t['word']} -> {e}")

    return {"inserted": inserted, "updated": updated, "errors": errors}


# ── 句式趋势追踪 ────────────────────────────────────────────────────


def _build_pattern_index() -> dict[str, dict]:
    """从飞书句式库构建 skeleton → 记录索引。"""
    records = feishu.query_patterns(limit=500)
    index: dict[str, dict] = {}
    for rec in records:
        fields = rec.get("fields", {})
        skeleton = str(_unwrap(fields.get("skeleton", ""))).strip()
        if not skeleton:
            continue
        old_examples = str(_unwrap(fields.get("examples", "")))
        old_list = [e.strip() for e in old_examples.split("\n") if e.strip()]
        index[skeleton] = {
            "record_id": rec["record_id"],
            "frequency": int(_unwrap(fields.get("frequency", 1)) or 1),
            "trend": str(_unwrap(fields.get("trend", "新句式"))),
            "examples": old_list,
        }
    return index


def track_patterns(candidates: list[dict]) -> list[dict]:
    """比对候选句式与飞书历史。

    candidates: [{skeleton, category, examples: [str]}]
    returns: [{... + trend, frequency, examples(str), is_new, record_id?}]
    """
    index = _build_pattern_index()
    now_ms = _now_ms()
    results: list[dict] = []

    for cand in candidates:
        skeleton = str(_unwrap(cand.get("skeleton", ""))).strip()
        if not skeleton:
            continue

        entry = index.get(skeleton)

        if entry:
            new_freq = (entry["frequency"] or 1) + 1
            # 合并 examples
            merged = list(entry["examples"])
            for ex in cand.get("examples", []):
                ex = ex.strip()
                if ex and ex not in merged:
                    merged.append(ex)

            results.append({
                **cand,
                "trend": "上升",
                "frequency": new_freq,
                "examples": "\n".join(merged),
                "last_seen": now_ms,
                "is_new": False,
                "record_id": entry["record_id"],
            })
        else:
            examples = cand.get("examples", [])
            results.append({
                **cand,
                "trend": "新句式",
                "frequency": len(examples) if examples else 1,
                "examples": "\n".join(examples) if examples else "",
                "first_seen": now_ms,
                "last_seen": now_ms,
                "is_new": True,
            })

    return results


def upsert_patterns(tracked: list[dict]) -> dict[str, int]:
    """将追踪结果写回飞书。"""
    now_ms = _now_ms()
    inserted = updated = errors = 0

    for t in tracked:
        try:
            if t["is_new"]:
                feishu.insert_pattern({
                    "skeleton": t["skeleton"],
                    "category": t.get("category", ""),
                    "examples": t.get("examples", ""),
                    "frequency": t.get("frequency", 1),
                    "first_seen": t.get("first_seen", now_ms),
                    "last_seen": t.get("last_seen", now_ms),
                    "trend": "新句式",
                })
                inserted += 1
            else:
                feishu.update_pattern(t["record_id"], {
                    "frequency": t["frequency"],
                    "last_seen": t["last_seen"],
                    "trend": "上升",
                    "examples": t.get("examples", ""),
                })
                updated += 1
        except Exception as e:
            errors += 1
            print(f"  [tracker] upsert pattern failed: {t['skeleton']} -> {e}")

    return {"inserted": inserted, "updated": updated, "errors": errors}


# ── 趋势衰减（批次间调用）──────────────────────────────────────────


def refresh_trends() -> dict[str, int]:
    """扫描飞书所有金词和句式，将"上升"→"平稳"（本次未出现）。

    应在每次 track + upsert 之后调用。
    """
    now_ms = _now_ms()
    words_decay = 0
    patterns_decay = 0

    # 金词：上升 → 平稳
    word_records = feishu.query_words(limit=500)
    for rec in word_records:
        fields = rec.get("fields", {})
        if fields.get("trend") == "上升":
            feishu.update_word(rec["record_id"], {"trend": "平稳"})
            words_decay += 1

    # 句式：上升 → 平稳
    pattern_records = feishu.query_patterns(limit=500)
    for rec in pattern_records:
        fields = rec.get("fields", {})
        if fields.get("trend") == "上升":
            feishu.update_pattern(rec["record_id"], {"trend": "平稳"})
            patterns_decay += 1

    return {"words_decayed": words_decay, "patterns_decayed": patterns_decay}
