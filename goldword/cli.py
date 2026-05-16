"""CLI 工具：金词列表 / 句式浏览 / 配置管理。

供 /list、/patterns、/config 等 slash command 调用。
"""

from __future__ import annotations

import sys
import io
from datetime import datetime
from typing import Any

from goldword import feishu

# Windows GBK 终端兼容
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _unwrap(val: Any) -> Any:
    if isinstance(val, list) and len(val) == 1:
        return val[0]
    return val


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


def _ts_to_date(val: Any) -> str:
    """飞书毫秒时间戳 → 'YYYY-MM-DD'。"""
    ts = _safe_int(val, 0)
    if not ts:
        return ""
    return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")


# ── /list ─────────────────────────────────────────────────────────


def list_words(
    category: str = "",
    field: str = "",
    trend: str = "",
    status: str = "",
    domain: str = "",
    min_vibe: int = 0,
    limit: int = 50,
) -> None:
    """查询金词库并格式化输出。"""
    records = feishu.query_words()

    # 过滤
    filtered = []
    trend_map = {"up": "上升", "down": "下降", "stable": "平稳", "new": "新词"}
    for rec in records:
        f = rec["fields"]
        if category and _unwrap(f.get("category", "")) != category:
            continue
        if field and _unwrap(f.get("source_field", "")) not in (field, "both"):
            continue
        if trend:
            actual_trend = _unwrap(f.get("trend", ""))
            if actual_trend != trend_map.get(trend, trend):
                continue
        if status and _unwrap(f.get("status", "")) != status:
            continue
        if domain and _unwrap(f.get("domain", "")) != domain:
            continue
        if min_vibe and _safe_int(f.get("vibe_score", 0)) < min_vibe:
            continue
        filtered.append(f)

    if not filtered:
        print("  (无匹配金词)")
        return

    # 按 vibe_score 降序
    filtered.sort(key=lambda w: _safe_int(w.get("vibe_score", 0)), reverse=True)
    filtered = filtered[:limit]

    print(f"  共 {len(filtered)} 条金词（金词库累计 {len(records)}）\n")
    print(f"  {'#':<3} {'金词':<14} {'功能位':<8} {'来源':<6} {'vibe':<5} {'频次':<4} {'趋势':<5} {'状态':<5} {'最近'}")
    print("  " + "-" * 75)
    for i, w in enumerate(filtered[:50], 1):
        word = str(w.get("word", ""))[:12]
        cat = str(_unwrap(w.get("category", "")))[:6]
        sf = str(_unwrap(w.get("source_field", "")))[:4]
        vibe = _safe_int(w.get("vibe_score", 0))
        freq = _safe_int(w.get("frequency", 1))
        tr = str(_unwrap(w.get("trend", "")))[:4]
        st = str(_unwrap(w.get("status", "")))[:4]
        last = _ts_to_date(w.get("last_seen", ""))
        print(f"  {i:<3} {word:<14} {cat:<8} {sf:<6} {vibe:<5} {freq:<4} {tr:<5} {st:<5} {last}")


# ── /patterns ─────────────────────────────────────────────────────


def list_patterns() -> None:
    """列出句式库，按 trend 分组。"""
    records = feishu.query_patterns()

    trend_groups: dict[str, list[dict]] = {}
    for rec in records:
        f = rec["fields"]
        trend = str(_unwrap(f.get("trend", "其他")))
        trend_groups.setdefault(trend, []).append(f)

    print(f"  句式库共 {len(records)} 条\n")

    for trend_name in ["新句式", "上升", "平稳", "下降", "其他"]:
        group = trend_groups.get(trend_name, [])
        if not group:
            continue
        print(f"  ── {trend_name} ({len(group)}) ──")
        for p in group:
            sk = _unwrap(p.get("skeleton", ""))
            cat = _unwrap(p.get("category", ""))
            freq = _safe_int(p.get("frequency", 1))
            examples = _unwrap(p.get("examples", ""))
            ex_line = examples.split("\n")[0].strip() if examples else ""
            print(f"  . [{cat}] \"{sk}\" (频次:{freq})")
            if ex_line:
                print(f"    例：{ex_line}")
        print()


# ── /config ───────────────────────────────────────────────────────


def show_config() -> None:
    """显示当前搜索配置。"""
    records = feishu.query_config()

    active = [r for r in records if r["fields"].get("is_active")]
    inactive = [r for r in records if not r["fields"].get("is_active")]

    print(f"  配置表共 {len(records)} 条（活跃 {len(active)} / 停用 {len(inactive)}）\n")

    # 按领域分组
    domains: dict[str, list[dict]] = {}
    for r in active:
        f = r["fields"]
        dw = f.get("domain_word", "(未分类)")
        domains.setdefault(dw, []).append({**f, "record_id": r["record_id"]})

    for dw, keywords in sorted(domains.items()):
        print(f"  【{dw}】")
        for kw in sorted(keywords, key=lambda x: x.get("priority", 99)):
            sw = kw.get("search_keyword", "")
            pri = kw.get("priority", 0)
            note = kw.get("note", "")
            note_str = f" — {note}" if note else ""
            print(f"    {sw} (优先级 {pri}){note_str}")
        print()

    if inactive:
        print(f"  ── 停用 ({len(inactive)}) ──")
        for r in inactive:
            f = r["fields"]
            print(f"    {f.get('domain_word', '?')} → {f.get('search_keyword', '?')}")


# ── /sync ─────────────────────────────────────────────────────────


def sync_status() -> None:
    """显示飞书各表状态概览。"""
    posts = feishu.query_posts()
    words = feishu.query_words()
    patterns = feishu.query_patterns()
    config = feishu.query_config()

    print("  飞书多维表状态\n")
    print(f"  热贴库：{len(posts)} 条")
    print(f"  金词库：{len(words)} 条")
    print(f"  句式库：{len(patterns)} 条")
    print(f"  配置表：{len(config)} 条")

    # 金词按状态统计
    status_counts: dict[str, int] = {}
    for w in words:
        s = str(_unwrap(w["fields"].get("status", "未知")))
        status_counts[s] = status_counts.get(s, 0) + 1
    if status_counts:
        print(f"\n  金词状态分布：")
        for s, c in sorted(status_counts.items(), key=lambda x: -x[1]):
            print(f"    {s}: {c}")


# ── __main__ ──────────────────────────────────────────────────────

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "list":
        kwargs = {}
        i = 1
        while i < len(args):
            if args[i] == "--category" and i + 1 < len(args):
                kwargs["category"] = args[i + 1]; i += 2
            elif args[i] == "--field" and i + 1 < len(args):
                kwargs["field"] = args[i + 1]; i += 2
            elif args[i] == "--trend" and i + 1 < len(args):
                kwargs["trend"] = args[i + 1]; i += 2
            elif args[i] == "--status" and i + 1 < len(args):
                kwargs["status"] = args[i + 1]; i += 2
            elif args[i] == "--domain" and i + 1 < len(args):
                kwargs["domain"] = args[i + 1]; i += 2
            elif args[i] == "--min-vibe" and i + 1 < len(args):
                kwargs["min_vibe"] = int(args[i + 1]); i += 2
            else:
                i += 1
        list_words(**kwargs)
    elif args[0] == "patterns":
        list_patterns()
    elif args[0] == "config":
        show_config()
    elif args[0] == "sync":
        sync_status()
    else:
        print(f"用法: python -m goldword.cli [list|patterns|config|sync] [选项]")
        print("  list      --category <功能位> --field <title|cover> --trend <up|down|stable|new>")
        print("             --status <pending|adopted|used|stale> --domain <领域> --min-vibe <N>")
        print("  patterns  (无参数)")
        print("  config    (无参数)")
        print("  sync      (无参数)")
