#!/usr/bin/env python3
"""Hạ tầng dùng chung của skill seo-new-product: config harness, gọi CLI Workspace, helper Sheet/Drive, ngày, URL.

Không chứa ID sheet/folder hay tên người: mọi giá trị nội bộ đọc từ harness.config.json
(khoá `sheets.nhOrderMain`, `sheets.nhOrderPlanReference`, `drive.nhOrderFolder`, `nhOrder.*`).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import pathlib
import re
import subprocess
import sys
from urllib.parse import urlsplit

HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / "harness" / "harness_config.py").is_file())
sys.path.insert(0, str(ROOT / "harness"))
from harness_config import HarnessConfigError, load_harness_config  # noqa: E402

GWS_TIMEOUT = 300  # CLI có thể treo khi keychain khoá, luôn đặt timeout
GWS_BIN = "gws"


def cfg():
    try:
        return load_harness_config()
    except HarnessConfigError as exc:
        sys.exit(f"LỖI CONFIG: {exc}")


def require(keys: list[str]) -> list:
    try:
        return cfg().require(keys)
    except HarnessConfigError as exc:
        sys.exit(f"LỖI CONFIG: {exc}")


def run_cli(args: list[str]) -> dict:
    config_dir = os.path.expanduser(cfg().get("gws.configDir", "<configDir>"))
    env = dict(os.environ, GOOGLE_WORKSPACE_CLI_CONFIG_DIR=config_dir)
    try:
        out = subprocess.run([GWS_BIN, *args], capture_output=True, text=True, env=env, timeout=GWS_TIMEOUT)
    except subprocess.TimeoutExpired:
        sys.exit("CLI Workspace quá thời gian chờ (có thể keychain đang khoá), mở khoá rồi chạy lại")
    text = "\n".join(l for l in out.stdout.splitlines() if "keyring backend" not in l)
    if out.returncode != 0:
        sys.exit(f"CLI Workspace lỗi: {(out.stderr or text)[-500:]}")
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        sys.exit(f"CLI Workspace trả dữ liệu không phải JSON: {text[:200]}")


def assert_account() -> str:
    """Xác nhận profile đang dùng đúng tài khoản trong config trước mọi thao tác ghi."""
    want = cfg().get("gws.accountEmail")
    got = run_cli(["gmail", "users", "getProfile", "--params", json.dumps({"userId": "me"})]).get("emailAddress")
    if want and got != want:
        sys.exit(f"Sai tài khoản Workspace: đang là {got}, config cần {want}")
    return got or ""


def p(**kw) -> str:
    return json.dumps(kw, ensure_ascii=False)


def values_get(sid: str, rng: str, render: str = "FORMATTED_VALUE") -> list[list]:
    return run_cli(["sheets", "spreadsheets", "values", "get", "--params",
                    p(spreadsheetId=sid, range=rng, valueRenderOption=render)]).get("values", [])


def values_update(sid: str, rng: str, values: list[list], option: str = "USER_ENTERED") -> dict:
    return run_cli(["sheets", "spreadsheets", "values", "update", "--params",
                    p(spreadsheetId=sid, range=rng, valueInputOption=option),
                    "--json", json.dumps({"values": values}, ensure_ascii=False)])


def values_clear(sid: str, rng: str) -> dict:
    return run_cli(["sheets", "spreadsheets", "values", "clear", "--params", p(spreadsheetId=sid, range=rng), "--json", "{}"])


def batch_update(sid: str, requests: list[dict]) -> dict:
    return run_cli(["sheets", "spreadsheets", "batchUpdate", "--params", p(spreadsheetId=sid),
                    "--json", json.dumps({"requests": requests}, ensure_ascii=False)])


def sheet_meta(sid: str) -> dict:
    data = run_cli(["sheets", "spreadsheets", "get", "--params", p(spreadsheetId=sid, fields="properties.title,sheets.properties")])
    return {s["properties"]["title"]: {"gid": s["properties"]["sheetId"], "index": s["properties"]["index"],
                                       "rows": s["properties"]["gridProperties"].get("rowCount", 0)}
            for s in data["sheets"]}


def drive_copy(file_id: str, name: str, parent: str) -> dict:
    return run_cli(["drive", "files", "copy", "--params", p(fileId=file_id, supportsAllDrives=True, fields="id,name,parents,webViewLink"),
                    "--json", json.dumps({"name": name, "parents": [parent]}, ensure_ascii=False)])


def drive_get(file_id: str) -> dict:
    return run_cli(["drive", "files", "get", "--params", p(fileId=file_id, supportsAllDrives=True, fields="id,name,parents,trashed,webViewLink")])


def drive_trash(file_id: str) -> dict:
    """Đưa file vào thùng rác Drive (khôi phục được), không xoá vĩnh viễn."""
    return run_cli(["drive", "files", "update", "--params", p(fileId=file_id, supportsAllDrives=True, fields="id,name,trashed"),
                    "--json", json.dumps({"trashed": True})])


def sheet_url(sid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sid}/edit"


def col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def serial(d: dt.date) -> int:
    return (d - dt.date(1899, 12, 30)).days


def fmt_date(d) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def parse_date(s: str) -> dt.date:
    return dt.datetime.strptime(s.strip(), "%d/%m/%Y").date()


def add_workdays(d: dt.date, n: int) -> dt.date:
    """Cộng n ngày làm việc (bỏ thứ Bảy, Chủ nhật)."""
    while n > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def norm_url(u: str) -> str:
    """Chuẩn hoá URL để so khớp: bỏ query/fragment/dấu / cuối, host về www.thegioididong.com."""
    u = (u or "").strip()
    if not u:
        return ""
    sp = urlsplit(u if "//" in u else "https://" + u)
    host = sp.netloc.lower()
    if host in ("thegioididong.com", "m.thegioididong.com"):
        host = "www.thegioididong.com"
    return f"{sp.scheme or 'https'}://{host}{sp.path.rstrip('/')}".lower()


def url_path(u: str) -> str:
    return urlsplit(u).path or "/"


def parse_int(s) -> int:
    d = re.sub(r"[^\d]", "", str(s or ""))
    return int(d) if d else 0
