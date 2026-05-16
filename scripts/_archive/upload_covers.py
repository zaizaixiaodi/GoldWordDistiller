"""下载封面图并生成 lark-cli 上传命令列表。"""

import json
import sys
import io
import os
import time
import requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 飞书记录（record_id → post_id 映射）───────────────────────────────
FEISHU_RECORDS = {
    "6968ded8000000001a02d4cb": "recvjHJKJQSE4j",
    "67e79618000000001200c6e9": "recvjHJKJQy2pC",
    "69a24e32000000001b017787": "recvjHJKJQCoW5",
    "66758e8b000000001f0054a7": "recvjHJKJQHtTe",
    "6721edb5000000001a01ff73": "recvjHJKJQnuPM",
    "65fbcf4400000000130245be": "recvjHJKJQaQjU",
    "69b40e49000000001a02e76b": "recvjHJKJQo3Fp",
    "6618a421000000001b00abe7": "recvjHJKJQea4y",
    "69638175000000000b013b1b": "recvjHJKJQ9Igv",
    "6a01f9f90000000008032f4b": "recvjHJKJQ3myt",
    "64aff09c0000000016024a94": "recvjHJKJQX6CP",
    "62b53950000000000f0087dc": "recvjHJKJQZqwn",
    "6978ac1a000000002103c09c": "recvjHJKJQS0Bc",
    "64bfa54d0000000012018e83": "recvjHJKJQzbzk",
    "69ec964d0000000037036426": "recvjHJKJQBlRO",
    "68bb9cdd000000001d0165f4": "recvjHJKJQjL94",
    "65fbe6bb00000000120321f2": "recvjHJKJQ2GdF",
    "681f85b50000000023001011": "recvjHJKJQ3tXt",
    "68442fcc000000001101e0a2": "recvjHJKJQOfgm",
    "68024a4a000000001c033ff1": "recvjHJKJQhoTU",
}

# ── TikHub 搜索 ────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()
TIKHUB_API_KEY = os.environ["TIKHUB_API_KEY"]
BASE = "https://api.tikhub.io"
HEADERS = {"Authorization": f"Bearer {TIKHUB_API_KEY}"}


def search_covers(keyword="副业"):
    """搜索并返回 post_id → cover_url 映射。"""
    resp = requests.get(
        f"{BASE}/api/v1/xiaohongshu/app_v2/search_notes",
        headers=HEADERS,
        params={"keyword": keyword, "page": 1, "sort_type": "popularity_descending"},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"搜索失败: HTTP {resp.status_code}")
        return {}

    items = resp.json().get("data", {}).get("data", {}).get("items", [])
    mapping = {}
    for item in items:
        note = item.get("note", {})
        note_id = note.get("id", "")
        if not note_id:
            continue

        # 提取封面 URL：统一用 images_list[cover_index]
        # video_info_v2.image.thumbnail 是视频帧截图，不是封面
        cover_url = ""
        images_list = note.get("images_list", [])
        cover_idx = note.get("cover_image_index", 0)
        if images_list and cover_idx < len(images_list):
            cover_url = (
                images_list[cover_idx].get("url_size_large", "")
                or images_list[cover_idx].get("url", "")
            )

        if cover_url and note_id in FEISHU_RECORDS:
            mapping[note_id] = cover_url

    return mapping


def download_images(mapping, out_dir="scripts/covers"):
    """下载封面图到本地，返回 record_id → 本地路径映射。"""
    os.makedirs(out_dir, exist_ok=True)
    result = {}
    for post_id, url in mapping.items():
        record_id = FEISHU_RECORDS[post_id]
        # 从 URL 推断扩展名
        ext = ".jpg"
        if "webp" in url:
            ext = ".webp"
        elif "png" in url:
            ext = ".png"
        filepath = os.path.join(out_dir, f"{record_id}{ext}")

        print(f"  下载 {post_id} → {filepath} ...", end=" ")
        try:
            resp = requests.get(url, timeout=30, stream=True)
            if resp.status_code == 200:
                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)
                size_kb = os.path.getsize(filepath) / 1024
                print(f"OK ({size_kb:.0f} KB)")
                result[record_id] = filepath
            else:
                print(f"FAIL (HTTP {resp.status_code})")
        except Exception as e:
            print(f"FAIL ({e})")

        time.sleep(0.3)

    return result


def main():
    print("=== Step 1: TikHub 搜索封面 ===")
    mapping = search_covers()
    print(f"  匹配到 {len(mapping)} 条封面 URL")

    unmatched = set(FEISHU_RECORDS.keys()) - set(mapping.keys())
    if unmatched:
        print(f"  未匹配: {len(unmatched)} 条 (post_id 不在搜索结果中)")

    print(f"\n=== Step 2: 下载封面图 ===")
    downloaded = download_images(mapping)
    print(f"  成功下载 {len(downloaded)} 张")

    # 输出上传命令 JSON
    output_file = "scripts/covers/upload_commands.json"
    commands = []
    for record_id, filepath in downloaded.items():
        commands.append({
            "record_id": record_id,
            "file": filepath.replace("\\", "/"),
        })
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(commands, f, indent=2, ensure_ascii=False)
    print(f"\n  上传列表已保存到 {output_file}")


if __name__ == "__main__":
    main()
