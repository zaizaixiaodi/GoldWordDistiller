"""Batch upload covers to Feishu via lark-cli (uses UAT)."""

import json
import os
import subprocess
import sys
import io
import tempfile
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

LARK_CLI = os.path.join(os.environ.get("APPDATA", ""), "npm", "lark-cli.cmd")

BITABLE_TOKEN = "Z5DubZ9DMaPkgDsbMWScnrgknSz"
TABLE_ID = "tblg2nOd7LvMZCKC"
COVER_DIR = os.path.dirname(os.path.abspath(__file__))

# Use a temp dir with ASCII-only path
TMP_DIR = os.path.join(tempfile.gettempdir(), "feishu_upload")
os.makedirs(TMP_DIR, exist_ok=True)


def larkcli_upload(filepath, size):
    """Upload file via lark-cli, return file_token or None."""
    upload_json = json.dumps({
        "file_name": "cover.jpg",
        "parent_type": "bitable_image",
        "parent_node": BITABLE_TOKEN,
        "size": str(size),
    })
    with open(os.path.join(TMP_DIR, "upload_req.json"), "w", encoding="utf-8") as f:
        f.write(upload_json)

    # Copy image to temp dir with ASCII name
    tmp_img = os.path.join(TMP_DIR, "cover.jpg")
    shutil.copy2(filepath, tmp_img)

    result = subprocess.run(
        [
            LARK_CLI, "api", "POST",
            "/open-apis/drive/v1/medias/upload_all",
            "--as", "user",
            "--data", "@upload_req.json",
            "--file", "file=cover.jpg",
        ],
        capture_output=True, text=True, timeout=30,
        cwd=TMP_DIR,
    )
    output = (result.stdout or "") + (result.stderr or "")
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, ValueError):
        print(f"    parse error: {output[:300]}")
        return None
    if data.get("code") != 0:
        print(f"    upload fail: {output[:300]}")
        return None
    return data["data"]["file_token"]


def larkcli_update(record_id, file_token):
    """Update Feishu record with file_token."""
    update_json = json.dumps({
        "fields": {"封面": [{"file_token": file_token}]}
    })
    with open(os.path.join(TMP_DIR, "update_req.json"), "w", encoding="utf-8") as f:
        f.write(update_json)

    result = subprocess.run(
        [
            LARK_CLI, "api", "PUT",
            f"/open-apis/bitable/v1/apps/{BITABLE_TOKEN}/tables/{TABLE_ID}/records/{record_id}",
            "--as", "user",
            "--data", "@update_req.json",
        ],
        capture_output=True, text=True, timeout=15,
        cwd=TMP_DIR,
    )
    output = (result.stdout or "") + (result.stderr or "")
    try:
        data = json.loads(output)
    except (json.JSONDecodeError, ValueError):
        print(f"    parse error: {output[:300]}")
        return False
    if data.get("code") != 0:
        print(f"    update fail: {output[:300]}")
        return False
    return True


def main():
    print("=== Batch upload covers via lark-cli (UAT) ===")
    print(f"  TMP_DIR: {TMP_DIR}")

    cmd_file = os.path.join(COVER_DIR, "upload_commands.json")
    with open(cmd_file, encoding="utf-8") as f:
        commands = json.load(f)

    done = {"recvjHJKJQy2pC"}
    success = 1
    fail = 0

    for cmd in commands:
        record_id = cmd["record_id"]
        filepath = cmd["file"]
        if record_id in done:
            print(f"\n  [{record_id}] SKIP (already done)")
            continue

        abs_path = os.path.normpath(os.path.join(COVER_DIR, "..", "..", filepath))
        size = os.path.getsize(abs_path)
        print(f"\n  [{record_id}] {filepath} ({size} bytes)")

        # Step 1: Upload
        print("    uploading...", end=" ")
        file_token = larkcli_upload(abs_path, size)
        if not file_token:
            fail += 1
            continue
        print(f"OK (token: {file_token})")

        # Step 2: Update
        print("    updating...", end=" ")
        ok = larkcli_update(record_id, file_token)
        if ok:
            print("OK")
            success += 1
        else:
            fail += 1

    print(f"\n=== Done: {success} success, {fail} fail ===")


if __name__ == "__main__":
    main()
