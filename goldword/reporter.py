"""简报 + 周报生成器。

实时简报：每次 /harvest 末尾或 /report 触发。
周报：/report --weekly 触发，含 PRD v2 §8.2 七节模板（含元认知反思）。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from goldword import feishu

_REPORTS_DIR = Path(__file__).resolve().parent.parent / "workspace" / "reports"
_REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _unwrap(val: Any) -> Any:
    if isinstance(val, list) and len(val) == 1:
        return val[0]
    return val


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


# ── 实时简报 ─────────────────────────────────────────────────────────


def generate_brief() -> str:
    """生成实时简报（PRD v2 §8.1），从飞书读取最近一批数据。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    words = feishu.query_words(limit=500)
    patterns = feishu.query_patterns(limit=500)

    new_words = [
        w["fields"] for w in words
        if _unwrap(w["fields"].get("trend", "")) == "新词"
    ]
    new_patterns = [
        p["fields"] for p in patterns
        if _unwrap(p["fields"].get("trend", "")) == "新句式"
    ]

    up_words = [
        w["fields"] for w in words
        if _unwrap(w["fields"].get("trend", "")) == "上升"
    ]
    down_words = [
        w["fields"] for w in words
        if _unwrap(w["fields"].get("trend", "")) == "下降"
    ]

    lines = [
        "=" * 42,
        f"  本次采集 | {now}",
        "=" * 42,
        f"  金词库累计 {len(words)} 条 | 句式库 {len(patterns)} 条",
        "",
        "  新金词（按 vibe_score 排序）",
    ]

    new_words.sort(key=lambda w: _safe_int(w.get("vibe_score", 0)), reverse=True)
    if new_words:
        for i, w in enumerate(new_words[:10], 1):
            word = w.get("word", "")
            cat = _unwrap(w.get("category", ""))
            sf = _unwrap(w.get("source_field", ""))
            vibe = _safe_int(w.get("vibe_score", 0))
            freq = _safe_int(w.get("frequency", 1))
            lines.append(f'  {i}. "{word}"  [{cat}|{sf}|vibe={vibe}]  频次:{freq}')
    else:
        lines.append("  (暂无新词)")

    if new_patterns:
        lines.append("")
        lines.append("  新句式")
        for p in new_patterns[:5]:
            sk = _unwrap(p.get("skeleton", ""))
            examples = _unwrap(p.get("examples", ""))
            if isinstance(examples, str):
                ex = examples.split("\n")[0].strip()
            else:
                ex = ""
            ex_str = f" -- {ex}" if ex else ""
            lines.append(f'  . "{sk}"{ex_str}')

    if up_words or down_words:
        lines.append("")
        if up_words:
            up_names = ", ".join(w.get("word", "") for w in up_words[:5])
            lines.append(f"  升温: {up_names}")
        if down_words:
            dn_names = ", ".join(w.get("word", "") for w in down_words[:5])
            lines.append(f"  下降: {dn_names}")

    lines.append("")
    lines.append("  详细趋势见 /report --weekly")
    lines.append("=" * 42)
    return "\n".join(lines)


# ── 周报 ─────────────────────────────────────────────────────────


_CAT_NAMES = {
    "who": "身份标签", "when": "场景锚点", "pain": "痛点/欲望",
    "do": "行动召唤", "twist": "反常识钩子", "number": "量化锚",
    "feel": "情绪/状态词", "picture": "隐喻具象",
}
_CATEGORIES = list(_CAT_NAMES)


def _week_range(week_str: str) -> tuple[datetime, datetime]:
    """'2026-W20' → (周一 00:00, 周日 23:59)。"""
    year, week = week_str.split("-W")
    year, week = int(year), int(week)
    jan4 = datetime(year, 1, 4)
    start = jan4 - __import__("datetime").timedelta(days=jan4.weekday())
    start = start + __import__("datetime").timedelta(weeks=week - 1)
    from datetime import timedelta
    end = start + timedelta(days=6)
    return start, end


def _to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _filter_week(records: list[dict], start_ms: int, end_ms: int) -> list[dict]:
    """筛选 last_seen 在范围内的记录，返回 fields 列表。"""
    result = []
    for rec in records:
        fields = rec.get("fields", {})
        ts = _safe_int(fields.get("last_seen", 0))
        if start_ms <= ts <= end_ms:
            result.append(fields)
    return result


def generate_weekly_report(week: str | None = None) -> str:
    """生成周报（PRD v2 §8.2 七节模板）并保存到 workspace/reports/。"""
    from datetime import timedelta

    if not week:
        iso = datetime.now().isocalendar()
        week = f"{iso[0]}-W{iso[1]:02d}"

    start, end = _week_range(week)
    start_ms, end_ms = _to_ms(start), _to_ms(end + timedelta(hours=23, minutes=59, seconds=59))
    date_range = f"{start.strftime('%m-%d')} ~ {end.strftime('%m-%d')}"

    all_word_recs = feishu.query_words(limit=500)
    all_pat_recs = feishu.query_patterns(limit=500)
    week_words = _filter_week(all_word_recs, start_ms, end_ms)
    week_pats = _filter_week(all_pat_recs, start_ms, end_ms)

    all_words = [r["fields"] for r in all_word_recs]
    all_pats = [r["fields"] for r in all_pat_recs]

    lines = [f"# 金词蒸馏周报 | {week}（{date_range}）", ""]

    # §1
    lines += [
        "## 1. 数据概览",
        f"- 金词库累计：{len(all_words)} 条",
        f"- 本周新增金词：{len(week_words)} 个",
        f"- 句式库累计：{len(all_pats)} 条",
        f"- 本周新增句式：{len(week_pats)} 个",
        "",
    ]

    # §2
    lines += ["## 2. 金词层次分布（按功能位）", "", "| 功能位 | 本周新增 | 累计 |", "|--------|---------|------|"]
    for cat in _CATEGORIES:
        wc = sum(1 for w in week_words if _unwrap(w.get("category", "")) == cat)
        tc = sum(1 for w in all_words if _unwrap(w.get("category", "")) == cat)
        lines.append(f"| {_CAT_NAMES[cat]} | {wc} | {tc} |")
    lines.append("")

    # §3
    lines.append("## 3. TOP 金词推荐（按 vibe_score 排序）")
    for label, source_fields in [("标题用", ("title", "both")), ("封面用", ("cover", "both"))]:
        subset = [w for w in week_words if _unwrap(w.get("source_field", "")) in source_fields]
        subset.sort(key=lambda w: _safe_int(w.get("vibe_score", 0)), reverse=True)
        lines += ["", f"### {label} Top 5"]
        for i, w in enumerate(subset[:5], 1):
            word = w.get("word", "")
            vibe = _safe_int(w.get("vibe_score", 0))
            cat = _unwrap(w.get("category", ""))
            lines.append(f'{i}. "{word}" (vibe={vibe}, {cat})')
    lines.append("")

    # §4
    lines.append("## 4. 新句式发现")
    if week_pats:
        for p in week_pats:
            sk = _unwrap(p.get("skeleton", ""))
            cat = _unwrap(p.get("category", ""))
            examples = _unwrap(p.get("examples", ""))
            ex_list = [e.strip() for e in str(examples).split("\n") if e.strip()] if examples else []
            lines.append(f'- **{sk}**（{cat}）')
            for ex in ex_list[:3]:
                lines.append(f"  - 例：{ex}")
    else:
        lines.append("本周无新句式。")
    lines.append("")

    # §5
    lines.append("## 5. 趋势变化")
    trend_map = {"上升": "升温词", "下降": "降温词", "平稳": "平稳词", "新词": "新词"}
    for trend_key, label in trend_map.items():
        group = [w for w in week_words if _unwrap(w.get("trend", "")) == trend_key]
        if group:
            names = ", ".join(w.get("word", "") for w in group[:10])
            lines.append(f"**{label}**：{names}")
    lines.append("")

    # §6 选题建议（占位，Claude 补充）
    lines += [
        "## 6. 选题建议（基于本周原料）",
        "",
        "> 需要基于高 vibe 金词 + 升温句式组合生成 5 个候选标题/封面。",
        "> 请 Claude 分析本周数据后补充此节。",
        "",
    ]

    # §7 元认知反思
    lines += ["## 7. 元认知反思", ""]
    lines.append("### 7.1 功能位模型是否需要调整？")
    for cat in _CATEGORIES:
        count = sum(1 for w in week_words if _unwrap(w.get("category", "")) == cat)
        if count == 0:
            lines.append(f"- **{_CAT_NAMES[cat]}**：0 条（可能需关注）")
        else:
            lines.append(f"- {_CAT_NAMES[cat]}：{count} 条")
    lines += [
        "",
        "### 7.2 蒸馏 prompt 是否需要迭代？",
        "- 漏检案例：（人审后补充）",
        "- 误检案例：（人审后补充）",
        "",
        "### 7.3 飞书识图质量",
        "- 识图成功率：（从 harvest 结果推断）",
        "",
        "### 7.4 分词与停用词策略",
        "- 新增建议加入停用词的高频通用词：（待观察）",
        '- 新增建议从停用词移出的"误杀"词：（待观察）',
        "",
        "### 7.5 待回测的开放问题",
        "- 必填位 vs 加分位分级是否生效？（需 >=200 条数据回测）",
        '- 第 9 类"工具/IP 名"是否独立？（需专项回测）',
    ]

    report = "\n".join(lines)

    report_file = _REPORTS_DIR / f"weekly_{week}.md"
    report_file.write_text(report, encoding="utf-8")
    print(f"[reporter] 周报已保存: {report_file}")

    return report


if __name__ == "__main__":
    import sys
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if "--weekly" in sys.argv:
        week = None
        for i, arg in enumerate(sys.argv):
            if arg == "--week" and i + 1 < len(sys.argv):
                week = sys.argv[i + 1]
        print(generate_weekly_report(week))
    else:
        print(generate_brief())
