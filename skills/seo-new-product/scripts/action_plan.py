#!/usr/bin/env python3
"""Sinh các dòng Hành_Động_SEO (timeline cơ bản ~2 tuần) theo dạng trang và kết quả research bài viết.

Offset (ngày làm việc kể từ ngày dựng plan) hiệu chỉnh theo file làm tay của order RTX Spark:
Title/Meta +1, Nội dung +4, Renew/Lên bài mới +5 (dàn thêm tối đa +3), Chèn link Promote +8/+9 (sau khi bài mới lên).
Hành_Động_SEO không có cột URL, nên dòng gắn với URL ghi đường dẫn vào Ghi chú.
"""
from __future__ import annotations

import datetime as dt

from nh_order_lib import add_workdays, url_path

A_TITLE = "Tối ưu Tiêu đề / Mô tả SEO"
A_CONTENT = "Tối ưu Nội dung"
A_NEWS = "Lên bài viết mới Tin tức"
A_RENEW = "Renew bài viết cũ liên quan"
A_PROMOTE = "Chèn link Promote"
A_NEW = {"hoi-dap": "Lên bài viết mới Hỏi Đáp", "game-app": "Lên bài viết mới Game App"}

OFFSET = {A_TITLE: 1, A_CONTENT: 4, A_RENEW: 5, "new": 5, A_PROMOTE: 8}
STAGGER_MAX = 3


def _row(action: str, owner: str, date: dt.date | None, note: str = "", link: str = "") -> dict:
    return {"action": action, "owner": owner, "date": date, "status": "Chưa làm", "done": "", "link": link, "note": note}


def build_actions(urls: list[dict], research: dict | None, start: dt.date, owner: str, news_owner: str | None) -> list[dict]:
    """`urls`: [{url, page_type}]. `research`: JSON đã được Claude kiểm (xem references/anti-research.md)."""
    rows: list[dict] = []
    day = lambda key, i=0: add_workdays(start, OFFSET[key] + min(i, STAGGER_MAX))  # noqa: E731

    for i, u in enumerate(urls):
        rows.append(_row(A_TITLE, owner, day(A_TITLE, i // 2), f"{url_path(u['url'])} (đề xuất ở tab Title_Meta)"))
    for i, u in enumerate(urls):
        what = "bài thông tin SP trên PIM" if u["page_type"].lower().startswith("sản") else "infobox trang Filter"
        rows.append(_row(A_CONTENT, owner, day(A_CONTENT, i // 2), f"{url_path(u['url'])} ({what})"))
    if news_owner:
        rows.append(_row(A_NEWS, news_owner, None, "Chờ bên Tin tức lên kế hoạch, điền link vào cột Link kết quả"))

    research = research or {}
    renews = list(research.get("renew", []))
    news = []
    for art in research.get("new_articles", []):
        if art.get("existing_url"):  # bài đã có trên site thì chuyển sang Renew, ghi link bài
            renews.append({"url": art["existing_url"], "note": art.get("note") or f"Thêm sản phẩm vào bài về {art['topic']}"})
        else:
            news.append(art)
    for i, r in enumerate(renews):
        rows.append(_row(A_RENEW, owner, day(A_RENEW, i), r.get("note", ""), r["url"]))
    for i, a in enumerate(news):
        note = a["topic"] + (f" ({a['kind']})" if a.get("kind") else "")
        rows.append(_row(A_NEW.get(a.get("site", "hoi-dap"), A_NEW["hoi-dap"]), owner, day("new", i), note))

    for i, u in enumerate(urls):
        rows.append(_row(A_PROMOTE, owner, day(A_PROMOTE, i), f"{url_path(u['url'])} (chèn link từ bài mới/bài cũ về URL này)"))
    return rows
