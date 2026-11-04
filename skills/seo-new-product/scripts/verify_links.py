#!/usr/bin/env python3
"""Claude kiểm lại số liệu Anti trước khi ghi sheet: mã HTTP của link, và bài đã tồn tại chưa (tìm kiếm nội bộ TGDĐ).

Dùng: new_product_plan.py verify-links <URL...>. URL dạng `search:<từ khoá>` kiểm bài đã có bằng
/hoi-dap/tim-kiem?key=<kw> và /game-app/tim-kiem?key=<kw> (parse href /(hoi-dap|game-app)/...-\\d{5,}).
"""
from __future__ import annotations

import re
import urllib.parse
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (seo-new-product link check)"}
ARTICLE = re.compile(r'href="(/(?:hoi-dap|game-app)/[^"#?\s]*-\d{5,})"')
BASE = "https://www.thegioididong.com"


def fetch(url: str) -> tuple[int, str]:
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(400_000).decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:80]


def search_existing(keyword: str) -> list[str]:
    found: list[str] = []
    for site in ("hoi-dap", "game-app"):
        status, html = fetch(f"{BASE}/{site}/tim-kiem?key={urllib.parse.quote(keyword)}")
        if status == 200:
            found += [BASE + m for m in dict.fromkeys(ARTICLE.findall(html))]
    return list(dict.fromkeys(found))


def main(urls: list[str]) -> int:
    bad = 0
    for u in urls:
        if u.startswith("search:"):
            hits = search_existing(u[7:])
            print(f"search '{u[7:]}': {len(hits)} bài" + ("".join(f"\n    {h}" for h in hits[:8])))
            continue
        status, _ = fetch(u)
        print(f"{status}  {u}")
        bad += status != 200
    return 1 if bad else 0
