#!/usr/bin/env python3
"""Đọc sheet `Cấu hình ảnh AI` và trả về config prompt đã match cho 1 profile/ngành hàng.

Thứ tự match giống workflow n8n `vTJmWPMVPL8G64dm`:
  Prompt Profile -> Tên ngành hàng -> dòng Default.

Dòng profile có thể chỉ có style (không có template). Khi đó lấy template từ
dòng category/Default và chỉ thay style guide + prompt guard.
"""

import os
import argparse
import json
import subprocess
import sys
import time

def _require(name, value, hint):
    """Fail loudly instead of querying the wrong spreadsheet with an empty id."""
    if not value:
        raise SystemExit(
            "%s is not set.\n"
            "Export it to point this skill at your own sheet:\n"
            "    export %s=<spreadsheet-id>\n"
            "%s" % (name, name, hint))
    return value


SPREADSHEET_ID = _require("SPREADSHEET_ID", os.environ.get("SPREADSHEET_ID", ""),
    "Sheet holding the per-category image prompt config.")
SHEET_NAME = "Cấu hình ảnh AI"
READ_RANGE = f"'{SHEET_NAME}'!A1:M50"

# Vị trí cột theo header sheet (A..L)
COLUMNS = {
    "category": 0,          # Tên ngành hàng
    "styleGuide": 1,        # Style Hướng Dẫn Chung
    "showcase": 2,          # Prompt - Ảnh Sản Phẩm (Showcase)
    "comparison": 3,        # Prompt - Ảnh So Sánh (Comparison)
    "instructional": 4,     # Prompt - Ảnh Hướng Dẫn (Instructional)
    "feature_highlight": 5,  # Prompt - Ảnh Tính Năng (Feature Highlight)
    "lineup_overview": 6,   # Prompt - Ảnh Tổng Quan Dòng (Lineup Overview)
    "buying_guide": 7,      # Prompt - Ảnh Chọn Mua (Buying Guide)
    "lifestyle_context": 8,  # Prompt - Ảnh Ngữ Cảnh (Lifestyle Context)
    "analyzerPrompt": 9,    # Prompt Phân Tích Ảnh Gốc
    "profile": 10,          # Prompt Profile
    "promptGuard": 11,      # Prompt Guard Tạo Ảnh
}

TEMPLATE_KEYS = [
    "showcase",
    "comparison",
    "instructional",
    "feature_highlight",
    "lineup_overview",
    "buying_guide",
    "lifestyle_context",
]


# Lỗi phía Google hay gặp và tự hết — retry thay vì bắt user chạy lại tay.
TRANSIENT_MARKERS = (
    "currently unavailable",
    "internal error",
    "backenderror",
    "rateLimitExceeded",
    "try again",
    "503",
    "500",
)
MAX_ATTEMPTS = 4


def _read_sheet_once():
    """1 lần gọi gws. Trả về (values, None) khi OK, (None, lý do lỗi) khi hỏng."""
    cmd = [
        "gws", "sheets", "+read",
        "--spreadsheet", SPREADSHEET_ID,
        "--range", READ_RANGE,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        sys.exit("ERROR: không tìm thấy lệnh `gws`. Cài gws CLI trước.")
    except subprocess.TimeoutExpired:
        # Treo là dấu hiệu Keychain khoá, không phải lỗi tạm — retry vô ích.
        sys.exit(
            "ERROR: gws treo quá 120s. Thường là Keychain đang khoá — "
            "mở Keychain/đăng nhập lại rồi chạy lại."
        )

    # gws in dòng "Using keyring backend: ..." trước JSON -> cắt từ dấu { đầu tiên
    out = proc.stdout
    start = out.find("{")
    if start < 0:
        return None, f"gws không trả JSON.\n{proc.stdout}\n{proc.stderr}"

    try:
        payload = json.loads(out[start:])
    except json.JSONDecodeError as exc:
        return None, f"không parse được JSON từ gws: {exc}"

    if "error" in payload:
        message = payload["error"].get("message", str(payload["error"]))
        return None, message

    return payload.get("values", []), None


def read_sheet():
    """Gọi gws CLI đọc sheet, retry khi Google trả lỗi tạm thời."""
    reason = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        values, reason = _read_sheet_once()
        if values is not None:
            return values

        is_transient = any(marker.lower() in reason.lower() for marker in TRANSIENT_MARKERS)
        if not is_transient or attempt == MAX_ATTEMPTS:
            break

        delay = 2 ** attempt  # 2s, 4s, 8s
        print(
            f"WARN gws lỗi tạm thời (lần {attempt}/{MAX_ATTEMPTS}): {reason.strip()[:120]} "
            f"-> thử lại sau {delay}s",
            file=sys.stderr,
        )
        time.sleep(delay)

    sys.exit(f"ERROR: gws trả lỗi: {reason}")


def cell(row, key):
    idx = COLUMNS[key]
    if idx < len(row):
        return (row[idx] or "").strip()
    return ""


def row_to_config(row):
    return {key: cell(row, key) for key in COLUMNS}


def find_row(rows, key, wanted):
    """Tìm dòng có cột `key` khớp `wanted` (không phân biệt hoa thường)."""
    target = wanted.strip().lower()
    for row in rows:
        if cell(row, key).lower() == target:
            return row
    return None


def has_templates(config):
    return any(config.get(key) for key in TEMPLATE_KEYS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", help="Prompt Profile, vd bright-minimal / gaming / premium")
    parser.add_argument("--category", help="Tên ngành hàng, vd 'Laptop Gaming'")
    parser.add_argument("--out", help="Ghi config ra file JSON")
    args = parser.parse_args()

    rows = read_sheet()
    if len(rows) < 2:
        sys.exit("ERROR: sheet không có dòng dữ liệu nào.")

    data_rows = rows[1:]

    default_row = find_row(data_rows, "category", "Default")
    if default_row is None:
        sys.exit("ERROR: sheet thiếu dòng `Default` — không có fallback an toàn.")
    default_config = row_to_config(default_row)

    matched = None
    match_source = "default"

    if args.profile:
        row = find_row(data_rows, "profile", args.profile)
        if row is None:
            row = find_row(data_rows, "category", args.profile)
        if row is not None:
            matched = row_to_config(row)
            match_source = f"profile:{args.profile}"

    if matched is None and args.category:
        row = find_row(data_rows, "category", args.category)
        if row is not None:
            matched = row_to_config(row)
            match_source = f"category:{args.category}"

    if matched is None:
        matched = default_config

    # Dòng style-only: mượn template của Default, giữ style guide + guard riêng.
    config = dict(matched)
    if not has_templates(config):
        for key in TEMPLATE_KEYS:
            config[key] = default_config.get(key, "")
        config["_templateSource"] = "default"
    else:
        config["_templateSource"] = match_source

    if not config.get("styleGuide"):
        config["styleGuide"] = default_config.get("styleGuide", "")
    if not config.get("promptGuard"):
        config["promptGuard"] = default_config.get("promptGuard", "")

    config["_matchSource"] = match_source
    config["_availableProfiles"] = sorted(
        {cell(r, "profile") for r in data_rows if cell(r, "profile")}
    )

    text = json.dumps(config, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(text)
        missing = [k for k in TEMPLATE_KEYS if not config.get(k)]
        print(f"OK config -> {args.out}")
        print(f"   match={config['_matchSource']} template={config['_templateSource']}")
        if missing:
            print(f"   WARN template rỗng: {', '.join(missing)}")
    else:
        print(text)


if __name__ == "__main__":
    main()
