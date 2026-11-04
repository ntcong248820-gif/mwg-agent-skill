#!/usr/bin/env python3
"""Tạo file Plan SEO nhóm SP bằng cách COPY file Plan mẫu (giữ chip màu dropdown, format, pivot, chart), xoá dữ liệu
mẫu, điền dữ liệu, đọc lại đối chiếu; thêm dòng vào file Plan đã có (extend); ghi link vào cột G của file chính.

Chip màu dropdown không đặt được qua Sheets API, nên không bao giờ dựng file phụ từ đầu. Không giữ file mẫu riêng:
nguồn copy là file Plan tham chiếu `sheets.nhOrderPlanReference` (chỉ đọc), dữ liệu mẫu bị xoá ở bản copy.
"""
from __future__ import annotations

import json

import order_reader as orders
import re

import rank_sheet

from nh_order_lib import (assert_account, batch_update, drive_copy, fmt_date, parse_date, require, serial, sheet_meta,
                          sheet_url, values_clear, values_get, values_update, run_cli, p)

HD, TK, RK, TH, TONG, NS = "Hành_Động_SEO", "Từ_Khóa", "Rank_Theo_Dõi", "Title_Meta", "Tổng_Hợp", "Nhân_sự"
TH_HEADER = ["URL", "Dạng trang", "Mode", "Title đề xuất", "Độ dài Title", "Meta đề xuất", "Độ dài Meta", "Ghi chú"]
TH_WIDTHS = [330, 80, 80, 360, 80, 520, 80, 260]
ROW_PX = 28
RANK_LAST_ROW = rank_sheet.RANK_LAST_ROW


def reset_values(sid: str) -> None:
    """Xoá dữ liệu mẫu (kể cả 15 cột kết quả đo và cột Ngày đo của Rank_Theo_Dõi), giữ format, dropdown, công thức/pivot/chart của Tổng_Hợp.
    Rank_Theo_Dõi của bản copy được đưa về quy ước format riêng (nguồn là file làm việc, owner dán thẳng từ tool vào)."""
    meta = sheet_meta(sid)
    for rng in (f"{HD}!A2:G", f"{TK}!A2:E", f"{RK}!A2:P"):
        values_clear(sid, rng)
    rank_sheet.normalize_rank_tab(sid, meta[RK]["gid"], meta[TK]["gid"])


def ensure_title_meta_tab(sid: str) -> int:
    """Thêm tab Title_Meta (sau Từ_Khóa) với format đồng bộ: Inter 9, căn giữa dọc, dòng 28px, CLIP, header như Từ_Khóa."""
    meta = sheet_meta(sid)
    if TH in meta:
        return meta[TH]["gid"]
    hdr = run_cli(["sheets", "spreadsheets", "get", "--params", p(
        spreadsheetId=sid, includeGridData=True, ranges=[f"{TK}!A1"],
        fields="sheets.data.rowData.values.userEnteredFormat")])
    hfmt = hdr["sheets"][0]["data"][0]["rowData"][0]["values"][0]["userEnteredFormat"]
    body_fmt = {"textFormat": {"fontFamily": "Inter", "fontSize": 9}, "verticalAlignment": "MIDDLE", "wrapStrategy": "CLIP"}
    res = batch_update(sid, [{"addSheet": {"properties": {
        "title": TH, "index": meta[TK]["index"] + 1,
        "gridProperties": {"rowCount": 1000, "columnCount": len(TH_HEADER), "frozenRowCount": 1}}}}])
    gid = res["replies"][0]["addSheet"]["properties"]["sheetId"]
    full = {"sheetId": gid, "startRowIndex": 1, "endRowIndex": 1000, "startColumnIndex": 0, "endColumnIndex": len(TH_HEADER)}
    reqs = [
        {"repeatCell": {"range": full, "cell": {"userEnteredFormat": body_fmt},
                        "fields": "userEnteredFormat(textFormat,verticalAlignment,wrapStrategy)"}},
        {"repeatCell": {"range": {**full, "startRowIndex": 0, "endRowIndex": 1}, "cell": {"userEnteredFormat": hfmt},
                        "fields": "userEnteredFormat"}},
        {"repeatCell": {"range": {**full, "startColumnIndex": 4, "endColumnIndex": 5}, "cell": {"userEnteredFormat": {**body_fmt, "horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat(textFormat,verticalAlignment,wrapStrategy,horizontalAlignment)"}},
        {"repeatCell": {"range": {**full, "startColumnIndex": 6, "endColumnIndex": 7}, "cell": {"userEnteredFormat": {**body_fmt, "horizontalAlignment": "CENTER"}},
                        "fields": "userEnteredFormat(textFormat,verticalAlignment,wrapStrategy,horizontalAlignment)"}},
        {"updateDimensionProperties": {"range": {"sheetId": gid, "dimension": "ROWS", "startIndex": 0, "endIndex": 1000},
                                       "properties": {"pixelSize": ROW_PX}, "fields": "pixelSize"}},
    ]
    for i, w in enumerate(TH_WIDTHS):
        reqs.append({"updateDimensionProperties": {"range": {"sheetId": gid, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                                                   "properties": {"pixelSize": w}, "fields": "pixelSize"}})
    batch_update(sid, reqs)
    values_update(sid, f"{TH}!A1:H1", [TH_HEADER])
    return gid


def _expected(plan: dict, th_first: int = 2) -> dict:
    """Dữ liệu sẽ ghi theo từng tab; ngày là số serial. Rank_Theo_Dõi chỉ điền cột A (từ khoá), kết quả đo do owner dán. `th_first`: dòng đầu của khối Title_Meta (cho công thức LEN)."""
    hd = [[a["action"], a["owner"], serial(a["date"]) if a["date"] else "", a["status"], "", a["link"], a["note"]]
          for a in plan["actions"]]
    tk, rk = [], []
    for u in plan["urls"]:
        for k in plan["keywords"][u["url"]]:
            note = k.get("serp", "") or ("Tự sinh, cần duyệt" if k["source"].startswith("tự sinh") else "")
            tk.append([k["keyword"], u["url"], k["volume"], bool(k["main"]), note])
            rk.append([k["keyword"]])
    th = []
    for u in plan["urls"]:
        t = plan["title_meta"].get(u["url_norm"])
        if t:
            i = th_first + len(th)
            th.append([u["url"], u["page_type"], t.get("mode", "Evergreen"), t["title"], f'=IF(D{i}="";"";LEN(D{i}))',
                       t["description"], f'=IF(F{i}="";"";LEN(F{i}))', t.get("note", "Đề xuất, chờ owner duyệt, chưa ghi PIM/MDM/CMS")])
    return {HD: hd, TK: tk, RK: rk, TH: th}


def _first_free(sid: str, tab: str, col: str = "A") -> int:
    """Dòng trống đầu tiên của tab (tính theo cột `col`, bỏ qua dòng tiêu đề)."""
    return len(values_get(sid, f"{tab}!{col}2:{col}")) + 2


def fill_plan(sid: str, plan: dict, at: dict | None = None) -> dict:
    """Ghi dữ liệu vào file phụ. `at` = dòng bắt đầu mỗi tab (mặc định 2: file mới; extend truyền dòng trống kế tiếp)."""
    at = at or {HD: 2, TK: 2, RK: 2, TH: 2}
    exp = _expected(plan, at[TH])
    ensure_title_meta_tab(sid)
    for tab, last in ((HD, "G"), (TK, "E"), (RK, "A"), (TH, "H")):
        if exp[tab]:
            values_update(sid, f"{tab}!A{at[tab]}:{last}{at[tab] + len(exp[tab]) - 1}", exp[tab])
    return at


def set_header_and_staff(sid: str, plan: dict) -> None:
    values_update(sid, f"{TONG}!A1", [[f"Tổng hợp tiến độ SEO và rank - {plan['group']}"]])
    staff = [[s] for s in require(["nhOrder.staff"])[0]]
    values_clear(sid, f"{NS}!A2:A")
    values_update(sid, f"{NS}!A2:A{len(staff) + 1}", staff)


def readback(sid: str, plan: dict, at: dict | None = None) -> list[str]:
    """Đọc lại từng dải đã ghi (FORMATTED_VALUE) và đối chiếu; trả danh sách lệch (rỗng = khớp)."""
    at = at or {HD: 2, TK: 2, RK: 2, TH: 2}
    exp, bad = _expected(plan, at[TH]), []

    def norm(v):
        return "" if v is None else str(v).strip()

    def block(tab, last, n):
        return values_get(sid, f"{tab}!A{at[tab]}:{last}{at[tab] + n - 1}") if n else []

    got = block(HD, "G", len(exp[HD]))
    for i, row in enumerate(exp[HD]):
        want = [norm(row[0]), norm(row[1]), fmt_date(plan["actions"][i]["date"]), norm(row[3]), "", norm(row[5]), norm(row[6])]
        g = (list(got[i]) + [""] * 7)[:7] if i < len(got) else [""] * 7
        if [norm(x) for x in g] != want:
            bad.append(f"{HD} dòng {at[HD] + i}: ghi {want} đọc lại {g}")
    gk = block(TK, "E", len(exp[TK]))
    for i, row in enumerate(exp[TK]):
        g = (list(gk[i]) + [""] * 5)[:5] if i < len(gk) else [""] * 5
        if [norm(g[0]), norm(g[1]), norm(g[2]), norm(g[3]).upper(), norm(g[4])] != [norm(row[0]), norm(row[1]), norm(row[2]), str(row[3]).upper(), norm(row[4])]:
            bad.append(f"{TK} dòng {at[TK] + i}: ghi {row} đọc lại {g}")
    gr = block(RK, "A", len(exp[RK]))
    for i, row in enumerate(exp[RK]):
        if i >= len(gr) or not gr[i] or norm(gr[i][0]) != row[0]:
            bad.append(f"{RK} dòng {at[RK] + i} lệch")
    bad += [f"{RK}: {x}" for x in rank_sheet.header_problems((values_get(sid, f"{RK}!A1:Z1") or [[]])[0])]
    bad += [f"{TONG}: ô lỗi {x}" for x in rank_sheet.check_tong_hop(sid)]
    gt = block(TH, "G", len(exp[TH]))
    for i, row in enumerate(exp[TH]):
        g = (list(gt[i]) + [""] * 7)[:7] if i < len(gt) else [""] * 7
        if [norm(g[0]), norm(g[3]), norm(g[5]), norm(g[4]), norm(g[6])] != [row[0], row[3], row[5], str(len(row[3])), str(len(row[5]))]:
            bad.append(f"{TH} dòng {at[TH] + i} lệch: {g}")
    return bad


def _report(bad: list[str]) -> None:
    print("Đọc lại: KHỚP toàn bộ dải đã ghi" if not bad else "Đọc lại LỆCH:\n  " + "\n  ".join(bad))


def create_plan_file(plan: dict, name: str) -> str:
    """Copy file Plan mẫu vào folder Laptop_NH_Order, xoá dữ liệu mẫu, điền, đọc lại. Trả ID file mới."""
    ref, folder = require(["sheets.nhOrderPlanReference", "drive.nhOrderFolder"])
    print(f"Tài khoản Workspace: {assert_account()}")
    rank_sheet.check_structure(ref, "file Plan tham chiếu")
    sid = drive_copy(ref, name, folder)["id"]
    print(f"Đã copy file Plan mẫu thành: {name}\n  {sheet_url(sid)}")
    reset_values(sid)
    fill_plan(sid, plan)
    set_header_and_staff(sid, plan)
    _report(readback(sid, plan))
    return sid


def plan_id_from_link(link: str) -> str:
    m = re.search(r"/d/([\w-]+)", link or "")
    if not m:
        raise SystemExit(f"Không tách được ID file từ link: {link}")
    return m.group(1)


def extend_plan_file(plan: dict, link: str) -> str:
    """Nhóm đã có file Plan: nối thêm dòng vào cuối từng tab của file đó, bỏ qua cặp (từ khoá, URL) đã có. Không xoá gì."""
    print(f"Tài khoản Workspace: {assert_account()}")
    sid = plan_id_from_link(link)
    rank_sheet.check_structure(sid, "file Plan đã có")
    have = {(r[0].strip().lower(), r[1].strip().lower()) for r in values_get(sid, f"{TK}!A2:B") if len(r) > 1}
    for u in plan["urls"]:
        kept = []
        for k in plan["keywords"][u["url"]]:
            if (k["keyword"].lower(), u["url"].lower()) in have:
                print(f"  bỏ qua từ khoá đã có: {k['keyword']}")
            else:
                kept.append(k)
        plan["keywords"][u["url"]] = kept
    at = {HD: _first_free(sid, HD), TK: _first_free(sid, TK), RK: _first_free(sid, RK, "A"),
          TH: _first_free(sid, TH) if TH in sheet_meta(sid) else 2}
    print(f"Thêm vào file hiện có {sheet_url(sid)} tại dòng {at}")
    fill_plan(sid, plan, at)
    _report(readback(sid, plan, at))
    return sid


def write_main_links(plan: dict, link: str, include_linked: bool) -> None:
    """Ghi link plan vào ĐÚNG ô G của các dòng URL thuộc nhóm. Đọc lại ngay trước khi ghi, không đụng ô khác."""
    assert_account()
    fresh = {r["row"]: r for r in orders.read_orders()}
    todo = []
    for row, url_norm in plan["row_urls"].items():
        row = int(row)
        cur = fresh.get(row)
        if not cur or cur["url_norm"] != url_norm:
            raise SystemExit(f"Dừng: dòng {row} của file chính đã đổi (URL không còn khớp), chạy lại plan")
        if cur["plan"]:
            print(f"  bỏ qua dòng {row}: cột G đã có link, không ghi đè")
            continue
        todo.append(row)
    for row in todo:
        values_update(orders.main_id(), f"'{orders.TAB}'!G{row}", [[link]], "RAW")
    after = {r["row"]: r for r in orders.read_orders()}
    for row in todo:
        ok = after[row]["plan"] == link and all(after[row][k] == fresh[row][k] for k in ("code", "url", "km", "status", "group"))
        print(f"  G{row}: {'OK' if ok else 'LỆCH'}")
