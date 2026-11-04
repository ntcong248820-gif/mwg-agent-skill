#!/usr/bin/env python3
"""Đọc tab Danh_Sách_Order của file chính NH Order SEO Laptop và gom theo nhóm sản phẩm."""
from __future__ import annotations

from nh_order_lib import norm_url, require, values_get

TAB = "Danh_Sách_Order"
COLS = ["code", "date", "person", "group", "page_type", "url", "plan", "km", "status"]  # A:I


def main_id() -> str:
    return require(["sheets.nhOrderMain"])[0]


def read_orders() -> list[dict]:
    """Mọi dòng có URL. `row` là số dòng thật trên sheet (dòng 1 là header)."""
    raw = values_get(main_id(), f"'{TAB}'!A2:I")
    rows = []
    for i, r in enumerate(raw, start=2):
        r = (list(r) + [""] * len(COLS))[: len(COLS)]
        d = dict(zip(COLS, (c.strip() if isinstance(c, str) else c for c in r)))
        if d["url"]:
            d["row"] = i
            d["url_norm"] = norm_url(d["url"])
            rows.append(d)
    return rows


def group_orders(rows: list[dict], order: str | None = None, group: str | None = None,
                 include_linked: bool = False) -> list[dict]:
    """Gom theo `Nhóm sản phẩm`. Dòng chờ plan = có URL và cột G trống (include_linked: tính cả dòng đã có link,
    dùng để thử/đối chiếu).

    Nhóm có dòng đã có link plan lẫn dòng chưa có là ca "thêm URL vào nhóm cũ": đánh dấu mode=extend,
    skill không tự tạo file mới cho nó (xem SKILL.md).
    """
    groups: dict[str, dict] = {}
    for r in rows:
        if order and r["code"] != order:
            continue
        if group and group.lower() not in r["group"].lower():
            continue
        g = groups.setdefault(r["group"], {"name": r["group"], "code": r["code"], "rows": [], "links": set()})
        g["rows"].append(r)
        if r["plan"]:
            g["links"].add(r["plan"])
    out = []
    for g in groups.values():
        pending = [r for r in g["rows"] if include_linked or not r["plan"]]
        if not pending:
            continue
        g["pending"] = pending
        g["mode"] = "extend" if g["links"] and not include_linked and len(pending) < len(g["rows"]) else "new"
        g["km"] = next((r["km"] for r in g["rows"] if r["km"]), "")
        out.append(g)
    return out
