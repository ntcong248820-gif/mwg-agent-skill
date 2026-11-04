#!/usr/bin/env python3
"""Thêm 1 dòng task vào sheet tổng hợp task IT (key sheets.itTaskTracker), tab theo site.

    python3 add-tracker-row.py <spec.json> --doc-url URL            # dry-run: in dòng sẽ ghi + ô đích
    python3 add-tracker-row.py <spec.json> --doc-url URL --write    # ghi rồi đọc lại so từng ô

- Map cột theo TÊN header dòng 1 (tab ĐMX/ERA BLUE có xuống dòng trong header) — không theo vị trí.
- Kiểm giá trị dropdown theo tab 'Data System' trước khi ghi.
- Dòng đích = ngay sau dòng cuối có 'Tên task'; dòng đó phải trống hoàn toàn, không thì dừng.
- Không đụng cột duyệt (Trạng thái duyệt task), timeline thực tế, Ghi chú SEO, cột note của IT.
"""
from __future__ import annotations

import argparse
import re
import sys

from mo_ta_common import cfg, gws, load_spec

COLS = {  # khoá tracker -> tên header (so sau khi gộp khoảng trắng)
    "uu_tien": "Thứ tự ưu tiên", "site": "Site", "du_an": "Dự án", "pic": "PIC",
    "ten_task": "Tên task", "loai_task": "Loại task", "muc_dich": "Mục đích task giải quyết vấn đề gì? (ghi chi tiết)",
    "link": "Link mô tả", "trang_thai": "Trạng thái task", "phu_trach": "Phụ trách Task",
    "timeline_ky_vong": "Timeline hoàn thành kỳ vọng",
}
DROPDOWN = {  # khoá -> range trong Data System (đọc từ data validation của tab TGDĐ, 09/10/2026)
    "uu_tien": "J2:J101", "site": "D2:D101", "du_an": "E2:E101", "pic": "F2:F7",
    "loai_task": "H2:H3", "phu_trach": "I2:I101", "trang_thai": "A11:A19",
}
norm = lambda s: re.sub(r"\s+", " ", str(s)).strip()


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def values(sid, rng):
    return gws("sheets", "spreadsheets", "values", "get", params={"spreadsheetId": sid, "range": rng}).get("values", [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--doc-url", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    spec, sid = load_spec(a.spec), cfg("sheets.itTaskTracker")
    tr = dict(spec["tracker"])
    tr.setdefault("ten_task", spec["title"])
    tr["link"], tr["trang_thai"] = a.doc_url, tr.get("trang_thai", "New")
    tab = tr["tab"]

    errs = []
    for k, rng in DROPDOWN.items():
        if tr.get(k):
            allowed = {norm(r[0]) for r in values(sid, f"'Data System'!{rng}") if r}
            if norm(tr[k]) not in allowed:
                errs.append(f"{k}={tr[k]!r} không có trong dropdown Data System!{rng}")
    hdr = [norm(h) for h in (values(sid, f"'{tab}'!A1:Z1") or [[]])[0]]
    pos = {}
    for k, name in COLS.items():
        if norm(name) in hdr:
            pos[k] = hdr.index(norm(name))
        elif tr.get(k):
            errs.append(f"tab '{tab}' không có cột '{name}'")
    if errs:
        sys.exit("DỪNG:\n- " + "\n- ".join(errs))

    rows = values(sid, f"'{tab}'!A1:Z2000")
    ti = pos["ten_task"]
    last = max((i for i, r in enumerate(rows) if len(r) > ti and r[ti].strip()), default=0)
    target = last + 2  # 1-based, ngay sau dòng cuối có Tên task
    if target - 1 < len(rows) and any(c.strip() for c in rows[target - 1]):
        sys.exit(f"Dòng {target} không trống — kiểm tay trước khi ghi.")
    width = max(pos.values()) + 1
    line = [""] * width
    for k, i in pos.items():
        line[i] = str(tr.get(k, ""))
    rng = f"'{tab}'!A{target}:{col_letter(width - 1)}{target}"
    print(f"Ô đích: {rng}")
    for k, i in sorted(pos.items(), key=lambda x: x[1]):
        print(f"  {col_letter(i)} {COLS[k]}: {line[i][:110]!r}")
    if not a.write:
        print("DRY-RUN — thêm --write để ghi.")
        return
    prof = gws("gmail", "users", "getProfile", params={"userId": "me"})
    print("Tài khoản:", prof.get("emailAddress"))
    gws("sheets", "spreadsheets", "values", "update", params={"spreadsheetId": sid, "range": rng, "valueInputOption": "USER_ENTERED"},
        body={"range": rng, "majorDimension": "ROWS", "values": [line]})
    back = (values(sid, rng) or [[]])[0] + [""] * width
    bad = [col_letter(i) for i in range(width) if norm(back[i]) != norm(line[i])]
    print("READBACK", "KHỚP" if not bad else f"LỆCH ở cột {bad}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
