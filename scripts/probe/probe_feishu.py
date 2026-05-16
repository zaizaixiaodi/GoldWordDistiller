"""飞书多维表 CRUD 联调测试 — 覆盖热贴库、金词库、句式库、配置表。

用法: python scripts/probe_feishu.py
"""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from goldword import feishu

PASSED = 0
FAILED = 0


def test(name: str, fn):
    global PASSED, FAILED
    try:
        fn()
        print(f"  OK {name}")
        PASSED += 1
    except Exception as e:
        print(f"  FAIL {name}: {e}")
        FAILED += 1


# ── 热贴库 ─────────────────────────────────────────────────────────────

_hotpost_id = ""


def test_insert_post():
    global _hotpost_id
    _hotpost_id = feishu.insert_post({
        "post_id": "test_probe_002",
        "title": "联调测试帖子v2",
        "desc": "测试数据，稍后删除",
        "url": {"link": "https://example.com/test", "text": "测试链接"},
        "author": "测试bot",
        "note_type": "normal",
        "like_count": 0,
        "collect_count": 0,
        "comment_count": 0,
        "share_count": 0,
        "search_keyword": "联调测试",
        "source": "search",
        "harvested_at": "2026-05-16 12:30:00",
    })
    assert _hotpost_id, "insert_post 返回空 record_id"


def test_query_posts():
    items = feishu.query_posts(limit=5)
    assert isinstance(items, list), "query_posts 应返回 list"


def test_update_post():
    feishu.update_post(_hotpost_id, {"like_count": 42})


# ── 金词库 ─────────────────────────────────────────────────────────────

_goldword_id = ""


def test_insert_word():
    global _goldword_id
    _goldword_id = feishu.insert_word({
        "word": "测试金词_probe_v2",
        "aliases": "测试金词别名",
        "domain": "搞钱",
        "category": "twist",
        "source_field": "title",
        "vibe_score": 7,
        "frequency": 1,
        "trend": "新词",
        "source": "人工精选",
        "status": "待审",
        "user_note": "联调测试，稍后删除",
    })
    assert _goldword_id, "insert_word 返回空 record_id"


def test_query_words():
    items = feishu.query_words()
    assert isinstance(items, list), "query_words 应返回 list"


def test_update_word():
    feishu.update_word(_goldword_id, {"vibe_score": 9, "status": "已采纳"})


# ── 句式库 ─────────────────────────────────────────────────────────────

_pattern_id = ""


def test_insert_pattern():
    global _pattern_id
    _pattern_id = feishu.insert_pattern({
        "skeleton": "不是 X，是 Y（测试v2）",
        "category": "递进",
        "examples": "不是想躺平，是太累了",
        "frequency": 1,
        "trend": "新句式",
        "user_note": "联调测试，稍后删除",
    })
    assert _pattern_id, "insert_pattern 返回空 record_id"


def test_query_patterns():
    items = feishu.query_patterns()
    assert isinstance(items, list), "query_patterns 应返回 list"


def test_update_pattern():
    feishu.update_pattern(_pattern_id, {"frequency": 2, "trend": "上升"})


# ── 配置表 ─────────────────────────────────────────────────────────────

_config_id = ""


def test_insert_config():
    global _config_id
    _config_id = feishu.insert_config(
        domain_word="搞钱",
        search_keyword="副业联调测试v2",
        is_active=True,
        priority=99,
        note="联调测试，稍后删除",
    )
    assert _config_id, "insert_config 返回空 record_id"


def test_query_config():
    items = feishu.query_config()
    assert isinstance(items, list), "query_config 应返回 list"


# ── main ──────────────────────────────────────────────────────────────

def main():
    print("=== 飞书多维表 CRUD 联调测试 ===\n")

    print("【热贴库】")
    test("insert_post", test_insert_post)
    test("query_posts", test_query_posts)
    test("update_post", test_update_post)

    print("\n【金词库】")
    test("insert_word", test_insert_word)
    test("query_words", test_query_words)
    test("update_word", test_update_word)

    print("\n【句式库】")
    test("insert_pattern", test_insert_pattern)
    test("query_patterns", test_query_patterns)
    test("update_pattern", test_update_pattern)

    print("\n【配置表】")
    test("insert_config", test_insert_config)
    test("query_config", test_query_config)

    print(f"\n=== 结果: {PASSED} passed / {FAILED} failed ===")


if __name__ == "__main__":
    main()
