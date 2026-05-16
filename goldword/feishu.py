"""飞书多维表薄封装层 — 基于 lark-cli。

提供热贴库、金词库、句式库、配置表的 CRUD 和识图轮询，以及封面图下载+上传。
读取走 lark-cli base +record-list（shell=True），写入走 lark-cli api（shell=True）。
"""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from goldword.config import (
    FEISHU_BITABLE_APP_TOKEN,
    FEISHU_CONFIG_TABLE_ID,
    FEISHU_GOLDWORDS_TABLE_ID,
    FEISHU_HOTPOSTS_TABLE_ID,
    FEISHU_PATTERNS_TABLE_ID,
)

import tempfile

# 纯 ASCII 临时目录放 JSON 文件
_CWD = str(Path(tempfile.gettempdir()) / "feishu_cli")
Path(_CWD).mkdir(exist_ok=True)


# ── 底层调用 ────────────────────────────────────────────────────────────

def _write_json(name: str, data: Any) -> str:
    """写 JSON 到 _CWD，返回 @name（用于 lark-cli --data @name）。"""
    Path(_CWD, name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return f"@{name}"


def _api(method: str, path: str, data: dict | None = None) -> dict:
    """写入操作：lark-cli api via shell=True（cmd.exe），已验证可写。"""
    cmd = f"lark-cli api {method} {path} --as user"
    if data:
        fname = f"_w_{abs(hash(json.dumps(data, sort_keys=True)))}.json"
        _write_json(fname, data)
        cmd += f" --data @{fname}"
    r = subprocess.run(cmd, capture_output=True, cwd=_CWD, shell=True)
    out = r.stdout.decode("utf-8", errors="replace")
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"lark-cli api {method} failed: {err[:200]} | {out[:200]}")
    return json.loads(out) if out.strip() else {}


def _base_path(table_id: str, suffix: str = "") -> str:
    return f"/open-apis/bitable/v1/apps/{FEISHU_BITABLE_APP_TOKEN}/tables/{table_id}{suffix}"


def _list_records(table_id: str, limit: int = 100, offset: int = 0) -> list[dict]:
    """读取操作：lark-cli base +record-list via shell=True。

    解析 tabular JSON 输出为 [{record_id, fields: {name: value}}] 列表。
    """
    cmd = (
        f"lark-cli base +record-list "
        f"--base-token {FEISHU_BITABLE_APP_TOKEN} "
        f"--table-id {table_id} "
        f"--as user --format json "
        f"--limit {limit} --offset {offset}"
    )
    r = subprocess.run(cmd, shell=True, capture_output=True)
    out = r.stdout.decode("utf-8", errors="replace")
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"lark-cli base +record-list failed: {err[:200]} | {out[:200]}")
    resp = json.loads(out)
    body = resp.get("data", {})
    field_names = body.get("fields", [])
    record_ids = body.get("record_id_list", [])
    rows = body.get("data", [])

    records = []
    for i, row in enumerate(rows):
        fields = {}
        for j, val in enumerate(row):
            if j < len(field_names) and val is not None:
                fields[field_names[j]] = val
        records.append({
            "record_id": record_ids[i] if i < len(record_ids) else "",
            "fields": fields,
        })
    return records


# ── 热贴库 ─────────────────────────────────────────────────────────────

def insert_post(record: dict) -> str:
    """写入热贴库一条记录，返回 record_id。"""
    resp = _api("POST", _base_path(FEISHU_HOTPOSTS_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": record}],
    })
    records = resp.get("data", {}).get("records", [])
    return records[0]["record_id"] if records else ""


def batch_insert_posts(records: list[dict]) -> list[str]:
    """批量写入热贴库。"""
    if not records:
        return []
    resp = _api("POST", _base_path(FEISHU_HOTPOSTS_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": r} for r in records],
    })
    return [r["record_id"] for r in resp.get("data", {}).get("records", [])]


def query_posts(limit: int = 100) -> list[dict]:
    """查询热贴库。"""
    return _list_records(FEISHU_HOTPOSTS_TABLE_ID, limit=limit)


def update_post(record_id: str, fields: dict) -> None:
    """更新热贴库一条记录。"""
    _api("PUT", _base_path(FEISHU_HOTPOSTS_TABLE_ID, f"/records/{record_id}"), {"fields": fields})


# ── 金词库 ─────────────────────────────────────────────────────────────

def insert_word(fields: dict) -> str:
    """写入金词库。"""
    resp = _api("POST", _base_path(FEISHU_GOLDWORDS_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": fields}],
    })
    records = resp.get("data", {}).get("records", [])
    return records[0]["record_id"] if records else ""


def batch_insert_words(fields_list: list[dict]) -> list[str]:
    """批量写入金词库。"""
    if not fields_list:
        return []
    resp = _api("POST", _base_path(FEISHU_GOLDWORDS_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": f} for f in fields_list],
    })
    return [r["record_id"] for r in resp.get("data", {}).get("records", [])]


def update_word(record_id: str, fields: dict) -> None:
    """更新金词库。"""
    _api("PUT", _base_path(FEISHU_GOLDWORDS_TABLE_ID, f"/records/{record_id}"), {"fields": fields})


def query_words(limit: int = 500) -> list[dict]:
    """查询金词库。"""
    return _list_records(FEISHU_GOLDWORDS_TABLE_ID, limit=limit)


# ── 句式库 ─────────────────────────────────────────────────────────────

def insert_pattern(fields: dict) -> str:
    """写入句式库。"""
    resp = _api("POST", _base_path(FEISHU_PATTERNS_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": fields}],
    })
    records = resp.get("data", {}).get("records", [])
    return records[0]["record_id"] if records else ""


def update_pattern(record_id: str, fields: dict) -> None:
    """更新句式库。"""
    _api("PUT", _base_path(FEISHU_PATTERNS_TABLE_ID, f"/records/{record_id}"), {"fields": fields})


def query_patterns(limit: int = 500) -> list[dict]:
    """查询句式库。"""
    return _list_records(FEISHU_PATTERNS_TABLE_ID, limit=limit)


# ── 配置表 ─────────────────────────────────────────────────────────────

def query_config() -> list[dict]:
    """读取配置表。"""
    return _list_records(FEISHU_CONFIG_TABLE_ID, limit=100)


def insert_config(domain_word: str, search_keyword: str, is_active: bool = True,
                  priority: int = 0, note: str = "") -> str:
    """插入配置表。"""
    resp = _api("POST", _base_path(FEISHU_CONFIG_TABLE_ID, "/records/batch_create"), {
        "records": [{"fields": {
            "domain_word": domain_word,
            "search_keyword": search_keyword,
            "is_active": is_active,
            "priority": priority,
            "note": note,
        }}],
    })
    records = resp.get("data", {}).get("records", [])
    return records[0]["record_id"] if records else ""


def delete_config(record_id: str) -> None:
    """删除配置表一条记录。"""
    _api("DELETE", _base_path(FEISHU_CONFIG_TABLE_ID, f"/records/{record_id}"))


# ── 封面上传 ──────────────────────────────────────────────────────────

_COVER_DIR = str(Path(tempfile.gettempdir()) / "feishu_covers")
Path(_COVER_DIR).mkdir(exist_ok=True)


def download_cover(url: str, record_id: str) -> str | None:
    """下载封面图到临时目录，返回本地路径。失败返回 None。"""
    import requests as _req

    # 推断扩展名
    ext = ".jpg"
    if "webp" in url:
        ext = ".webp"
    elif "png" in url:
        ext = ".png"

    filepath = Path(_COVER_DIR) / f"{record_id}{ext}"
    if filepath.exists():
        return str(filepath)  # 已下载，跳过

    try:
        resp = _req.get(url, timeout=30, stream=True)
        if resp.status_code == 200:
            filepath.write_bytes(resp.content)
            return str(filepath)
        else:
            print(f"    下载封面失败 HTTP {resp.status_code}: {url[:80]}")
            return None
    except Exception as e:
        print(f"    下载封面异常: {e}")
        return None


def upload_cover(filepath: str) -> str | None:
    """上传封面图到飞书 Drive，返回 file_token。失败返回 None。

    必须用 --as user（tenant token 无 drive:file:upload 权限）。
    """
    fpath = Path(filepath)
    size = fpath.stat().st_size
    stem = fpath.stem

    # 复制到 _CWD 并重命名为纯 ASCII 名，方便 lark-cli --file 引用
    upload_name = f"{stem[:30]}.jpg"
    tmp_img = Path(_CWD) / upload_name
    _shutil_copy(filepath, str(tmp_img))

    req_json = {
        "file_name": upload_name,
        "parent_type": "bitable_image",
        "parent_node": FEISHU_BITABLE_APP_TOKEN,
        "size": str(size),
    }
    req_name = f"_upload_{stem[:20]}.json"
    _write_json(req_name, req_json)

    cmd = (
        f"lark-cli api POST /open-apis/drive/v1/medias/upload_all "
        f"--as user --data @{req_name} --file file={upload_name}"
    )
    r = subprocess.run(cmd, capture_output=True, cwd=_CWD, shell=True)
    out = r.stdout.decode("utf-8", errors="replace")

    try:
        data = json.loads(out)
    except (json.JSONDecodeError, ValueError):
        print(f"    upload_cover parse error: {out[:200]}")
        return None

    if data.get("code") != 0:
        print(f"    upload_cover fail: {out[:200]}")
        return None
    return data["data"]["file_token"]


def update_cover_attachment(record_id: str, file_token: str) -> bool:
    """把 file_token 写入热贴库记录的"封面"附件字段。"""
    data_ref = _write_json("_upd_cover.json", {"fields": {"封面": [{"file_token": file_token}]}})
    try:
        _api("PUT", _base_path(FEISHU_HOTPOSTS_TABLE_ID, f"/records/{record_id}"),
             {"fields": {"封面": [{"file_token": file_token}]}})
        return True
    except Exception as e:
        print(f"    update_cover_attachment fail: {e}")
        return False


def _shutil_copy(src: str, dst: str) -> None:
    import shutil
    shutil.copy2(src, dst)


# ── 识图轮询 ──────────────────────────────────────────────────────────

def wait_for_cover_text(
    record_ids: list[str],
    initial_wait: int = 90,
    retry_interval: int = 30,
    max_retries: int = 3,
) -> dict:
    """轮询热贴库，等待飞书豆包识图填充"封面文案输出结果"字段。

    返回: {"success": [id...], "failed": [id...], "data": {id: text}}
    """
    result: dict[str, Any] = {"success": [], "failed": [], "data": {}}
    pending = set(record_ids)
    if not pending:
        return result

    print(f"  [feishu] 等待识图 {initial_wait}s ...")
    time.sleep(initial_wait)

    for attempt in range(max_retries):
        if not pending:
            break
        newly_done = set()
        for rid in list(pending):
            try:
                resp = _api("GET", _base_path(FEISHU_HOTPOSTS_TABLE_ID, f"/records/{rid}"))
                record = resp.get("data", {}).get("record", {})
                cover_text = record.get("fields", {}).get("封面文案输出结果", "")
                if cover_text:
                    result["success"].append(rid)
                    result["data"][rid] = cover_text
                    newly_done.add(rid)
            except Exception:
                pass
        pending -= newly_done
        if pending and attempt < max_retries - 1:
            print(f"  [feishu] 还有 {len(pending)} 条待识图，{retry_interval}s 后重试 ...")
            time.sleep(retry_interval)

    result["failed"] = list(pending)
    return result
