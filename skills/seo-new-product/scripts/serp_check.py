#!/usr/bin/env python3
"""Kiểm SERP bằng SerpApi để chốt từ khoá thuộc dạng URL nào (bán hàng hay bài viết/tin).

Mặc định chỉ ĐỌC cache (--serp-cache). Gọi SerpApi thật (mỗi từ khoá 1 credit) chỉ khi truyền --serp và
--approve-serp <số credit>, giống cổng chi phí Ahrefs. Khoá API đọc từ biến môi trường SERP_API_KEY; nếu chưa có,
nạp đúng biến đó từ .env gốc, không in và không ghi ra đâu.
Cache: {từ khoá: [[hạng, url, tiêu đề], ...]} (cùng khuôn với data/raw/serp-vn-*.json của task RTX Spark).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from urllib.parse import urlsplit

from nh_order_lib import ROOT

RETAIL = ("thegioididong.com", "dienmayxanh.com", "cellphones.com.vn", "fptshop.com.vn", "nguyenkim.com",
          "phongvu.vn", "gearvn.com", "hacom.vn", "anphatpc.com.vn", "memoryzone.com.vn", "tinhocngoisao.com",
          "mediamart.vn", "didongviet.vn", "hoanghamobile.com", "laptopworld.vn", "vn.msi.com", "shopee.vn",
          "lazada.vn", "tiki.vn", "nguyenvu.store", "laptop88.vn", "laptopvang.com", "binhminhdigital.com")
OWN = "thegioididong.com"


def load_cache(path: str | None) -> dict:
    if path and os.path.isfile(path):
        return json.load(open(path, encoding="utf-8"))
    return {}


def save_cache(path: str, cache: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)


def _api_key() -> str:
    key = os.environ.get("SERP_API_KEY", "")
    if not key:
        env = ROOT / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                m = re.match(r"\s*SERP_API_KEY\s*=\s*(.*)", line)
                if m:
                    key = m.group(1).strip().strip("'\"")
    if not key:
        raise SystemExit("Thiếu SERP_API_KEY (biến môi trường hoặc .env gốc)")
    return key


def fetch_serp(keyword: str) -> list[list]:
    q = urllib.parse.urlencode({"engine": "google", "q": keyword, "google_domain": "google.com.vn", "gl": "vn",
                                "hl": "vi", "num": 10, "api_key": _api_key()})
    with urllib.request.urlopen(f"https://serpapi.com/search.json?{q}", timeout=60) as r:
        data = json.load(r)
    return [[i, o.get("link", ""), o.get("title", "")] for i, o in enumerate(data.get("organic_results", [])[:10], 1)]


def verdict(results: list[list]) -> dict:
    """Đếm kết quả bán hàng / bài viết trong top 10 và hạng của TGDĐ."""
    host = lambda u: urlsplit(u).netloc.lower().removeprefix("www.")  # noqa: E731
    retail = sum(1 for _, u, _ in results if any(host(u).endswith(d) for d in RETAIL))
    own = next((r for r, u, _ in results if host(u).endswith(OWN)), None)
    kind = "bán hàng" if retail >= 3 else ("bài viết/tin" if retail <= 1 else "lẫn")
    return {"retail": retail, "total": len(results), "own_rank": own, "kind": kind}


def annotate(keywords: list[str], cache: dict, cache_path: str | None, call: bool, approve: int,
             today: str, log=print) -> dict[str, dict]:
    """Trả {từ khoá: {kind, retail, total, own_rank, note}} cho các từ khoá có SERP (cache hoặc vừa gọi)."""
    missing = [k for k in keywords if k not in cache]
    if call and missing:
        if approve < len(missing):
            log(f"  COST_GATE SerpApi: cần {len(missing)} credit, chưa được duyệt (--approve-serp {approve}). Không gọi.")
        else:
            for k in missing:
                cache[k] = fetch_serp(k)
                time.sleep(1)
            if cache_path:
                save_cache(cache_path, cache)
    elif missing:
        log(f"  SERP: {len(missing)}/{len(keywords)} từ khoá chưa có cache (thêm --serp --approve-serp {len(missing)} để gọi SerpApi)")
    out = {}
    for k in keywords:
        if k in cache:
            v = verdict(cache[k])
            own = f"TGDĐ hạng {v['own_rank']}" if v["own_rank"] else "TGDĐ chưa vào top 10"
            v["note"] = f"SERP {today}: {v['retail']}/{v['total']} trang bán hàng ({v['kind']}), {own}"
            out[k] = v
    return out
