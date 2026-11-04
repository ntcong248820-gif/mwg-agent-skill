#!/usr/bin/env python3
"""Tab Rank_Theo_Dõi và kiểm Tổng_Hợp của file Plan nhóm SP.

Rank_Theo_Dõi là MỘT tab duy nhất để dán kết quả từ tool SERP Rank Checker của owner (extension Chrome): A:O là 15 cột của tool
(mỗi từ khoá một dòng, không có cột Nhóm ranking), P là `Ngày đo` do owner nhập khi dán. Mỗi lần đo dán nối tiếp xuống dưới.
Skill chỉ điền sẵn cột A (Keyword); B:P để trống. Nhóm ranking, Top 1-2 KPI, AI Overview, đối thủ Top 1-3 và xu hướng theo ngày
do tab Tổng_Hợp (công thức + chart) tự tính: số liệu hiện tại lấy các dòng có Ngày đo lớn nhất, xu hướng gom theo Ngày đo.
"""
from __future__ import annotations

import re

from nh_order_lib import batch_update, p, run_cli, values_get

RK = "Rank_Theo_Dõi"
TK = "Từ_Khóa"
TONG = "Tổng_Hợp"
RANK_LAST_ROW = 2000
RANK_HEADERS = ["Keyword", "Rank", "Domain", "URL", "AI Overview", "Side panel", "Citation", "Link", "AIO total",
                "Top 1 URL", "Top 1 Title", "Top 2 URL", "Top 2 Title", "Top 3 URL", "Top 3 Title", "Ngày đo"]
# Trạng thái cột AI Overview mà tool xuất ra (extension v1.4+); dropdown không chặn dán.
AIO_STATUSES = ["In", "Not cited", "No AI Overview", "Limit", "Timeout", "Error"]
# Cột căn giữa: Rank, AI Overview, AIO total, Ngày đo; còn lại căn trái.
CENTER_COLS = (1, 4, 8, 15)
DATE_COL = len(RANK_HEADERS) - 1
ROW_PX = 28
_ERROR = re.compile(r"^#(REF|N/A|VALUE|DIV/0|ERROR|NAME|NUM|NULL)")


def header_problems(row: list) -> list[str]:
    """So dòng tiêu đề của tab với cấu trúc 15 cột chuẩn; trả danh sách lệch (rỗng = khớp)."""
    got = [str(x).strip() for x in (row or [])]
    bad = []
    for i, want in enumerate(RANK_HEADERS):
        have = got[i] if i < len(got) else ""
        if have != want:
            bad.append(f"cột {i + 1}: cần '{want}', file có '{have}'")
    if len(got) > len(RANK_HEADERS) and any(got[len(RANK_HEADERS):]):
        bad.append(f"có cột thừa sau cột {len(RANK_HEADERS)}: {got[len(RANK_HEADERS):]}")
    return bad


def find_errors(values: list[list]) -> list[str]:
    """Các ô lỗi công thức (#REF!, #N/A, #VALUE!, #ERROR!...) trong một dải giá trị đã đọc."""
    out = []
    for r, row in enumerate(values, 1):
        for c, cell in enumerate(row, 1):
            if _ERROR.match(str(cell)):
                out.append(f"hàng {r} cột {c}: {cell}")
    return out


def check_structure(sid: str, where: str) -> None:
    """Dừng nếu Rank_Theo_Dõi của file nguồn/đích không đúng 15 cột chuẩn (owner đổi cấu trúc thì phải sửa skill trước)."""
    bad = header_problems((values_get(sid, f"{RK}!A1:Z1") or [[]])[0])
    if bad:
        raise SystemExit(f"Dừng: {RK} của {where} không đúng cấu trúc 15 cột của tool SERP Rank Checker:\n  " + "\n  ".join(bad)
                         + "\nSửa rank_sheet.RANK_HEADERS, công thức Tổng_Hợp và references/plan-file-spec.md cho khớp trước khi dựng file.")


def check_tong_hop(sid: str) -> list[str]:
    """Đọc cả tab Tổng_Hợp, trả danh sách ô lỗi công thức (rỗng = sạch)."""
    return find_errors(values_get(sid, f"{TONG}!A1:N130"))


def normalize_rank_tab(sid: str, gid: int, tk_gid: int) -> None:
    """Chỉ chạy trên BẢN COPY: đưa tab Rank_Theo_Dõi về quy ước gws-sheets (Inter 9, giữa dọc, dòng 28px, CLIP), xoá luật
    tô màu cũ của cột Nhóm ranking (nay cột đó không còn), đặt dropdown cho AI Overview, header theo Từ_Khóa."""
    meta = run_cli(["sheets", "spreadsheets", "get", "--params", p(
        spreadsheetId=sid, ranges=[f"{TK}!A1"], includeGridData=True,
        fields="sheets(properties.sheetId,conditionalFormats,data.rowData.values.userEnteredFormat)")])
    tk = next(s for s in meta["sheets"] if s["properties"]["sheetId"] == tk_gid)
    hfmt = tk["data"][0]["rowData"][0]["values"][0]["userEnteredFormat"]
    cf = run_cli(["sheets", "spreadsheets", "get", "--params", p(
        spreadsheetId=sid, fields="sheets(properties.sheetId,conditionalFormats)")])
    n_cf = len(next((s for s in cf["sheets"] if s["properties"]["sheetId"] == gid), {}).get("conditionalFormats", []))
    ncol = len(RANK_HEADERS)
    full = {"sheetId": gid, "startRowIndex": 0, "endRowIndex": RANK_LAST_ROW, "startColumnIndex": 0, "endColumnIndex": ncol}
    body_fmt = {"textFormat": {"fontFamily": "Inter", "fontSize": 9}, "verticalAlignment": "MIDDLE",
                "wrapStrategy": "CLIP", "horizontalAlignment": "LEFT"}
    reqs = [{"deleteConditionalFormatRule": {"sheetId": gid, "index": i}} for i in range(n_cf - 1, -1, -1)]
    reqs += [
        {"repeatCell": {"range": {**full, "startRowIndex": 1}, "cell": {"userEnteredFormat": body_fmt},
                        "fields": "userEnteredFormat(textFormat,verticalAlignment,wrapStrategy,horizontalAlignment)"}},
        {"repeatCell": {"range": {**full, "endRowIndex": 1, "endColumnIndex": ncol}, "cell": {"userEnteredFormat": hfmt},
                        "fields": "userEnteredFormat"}},
        {"updateDimensionProperties": {"range": {"sheetId": gid, "dimension": "ROWS", "startIndex": 0, "endIndex": RANK_LAST_ROW},
                                       "properties": {"pixelSize": ROW_PX}, "fields": "pixelSize"}},
        {"repeatCell": {"range": {**full, "startRowIndex": 1, "startColumnIndex": DATE_COL, "endColumnIndex": DATE_COL + 1},
                        "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}}},
                        "fields": "userEnteredFormat.numberFormat"}},
        {"setDataValidation": {"range": {**full, "startRowIndex": 1, "startColumnIndex": 4, "endColumnIndex": 5},
                               "rule": {"condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in AIO_STATUSES]},
                                        "showCustomUi": True, "strict": False}}},
    ]
    for c in CENTER_COLS:
        reqs.append({"repeatCell": {"range": {**full, "startRowIndex": 0, "startColumnIndex": c, "endColumnIndex": c + 1},
                                    "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                                    "fields": "userEnteredFormat.horizontalAlignment"}})
    batch_update(sid, reqs)
