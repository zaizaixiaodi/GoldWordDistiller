"""上传封面图到飞书多维表附件字段。"""

import json
import os
import sys
import io
import time

import requests
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
load_dotenv()

APP_ID = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
BITABLE_TOKEN = "Z5DubZ9DMaPkgDsbMWScnrgknSz"
TABLE_ID = "tblg2nOd7LvMZCKC"
COVER_DIR = "scripts/covers"


def get_tenant_token():
    """获取飞书 tenant_access_token。"""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10,
    )
    data = resp.json()
    if data.get("code") != 0:
        print(f"  获取 token 失败: {data}")
        return None
    return data["tenant_access_token"]


def upload_file(token, filepath):
    """上传文件到飞书 Drive，返回 file_token。"""
    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    with open(filepath, "rb") as f:
        resp = requests.post(
            "https://open.feishu.cn/open-apis/drive/v1/medias/upload_all",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "file_name": filename,
                "parent_type": "bitable_image",
                "parent_node": BITABLE_TOKEN,
                "size": str(size),
            },
            files={"file": (filename, f)},
            timeout=30,
        )
    data = resp.json()
    if data.get("code") != 0:
        print(f"  上传失败: {data}")
        return None
    return data["data"]["file_token"]


def update_record(token, record_id, field_name, file_token):
    """更新记录的附件字段。"""
    body = {
        "fields": {
            field_name: [{"file_token": file_token}]
        }
    }
    resp = requests.put(
        f"https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_TOKEN}/tables/{TABLE_ID}/records/{record_id}",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=15,
    )
    data = resp.json()
    return data.get("code") == 0, data


def main():
    print("=== 飞书封面图上传 ===")

    # 读取上传列表
    cmd_file = os.path.join(COVER_DIR, "upload_commands.json")
    with open(cmd_file, encoding="utf-8") as f:
        commands = json.load(f)
    print(f"  待上传: {len(commands)} 张")

    # 获取 token
    print("\n--- 获取 token ---")
    token = get_tenant_token()
    if not token:
        sys.exit(1)
    print(f"  token: {token[:20]}...")

    # 逐条上传
    print("\n--- 上传封面图 ---")
    success = 0
    fail = 0
    for cmd in commands:
        record_id = cmd["record_id"]
        filepath = cmd["file"]
        print(f"\n  [{record_id}] {filepath}")

        # Step 1: 上传文件
        print(f"    上传文件...", end=" ")
        file_token = upload_file(token, filepath)
        if not file_token:
            fail += 1
            continue
        print(f"OK (token: {file_token})")

        # Step 2: 更新记录
        print(f"    更新记录...", end=" ")
        ok, resp = update_record(token, record_id, "封面", file_token)
        if ok:
            print("OK")
            success += 1
        else:
            code = resp.get("code", "?")
            msg = resp.get("msg", "unknown")
            print(f"FAIL (code={code}, msg={msg})")
            fail += 1

        time.sleep(0.5)

    print(f"\n=== 完成: {success} 成功, {fail} 失败 ===")


if __name__ == "__main__":
    main()
