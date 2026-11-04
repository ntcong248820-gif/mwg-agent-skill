#!/usr/bin/env python3
"""Nguồn từ khoá cho Plan SEO nhóm SP: file research có sẵn, kho từ khoá hệ thống, tự sinh khi thiếu.

Thứ tự ưu tiên (xem references/keyword-sourcing.md): file research (--kw-file) > tab research SP/Hãng mới >
tab `All KW` > tự sinh từ URL (volume 0). Skill KHÔNG tự gọi Ahrefs: thiếu từ khoá thì báo để owner duyệt units.
"""
from __future__ import annotations

import csv
import json
import re

from nh_order_lib import norm_url, parse_int, require, url_path, values_get

TOKEN = re.compile(r"[a-z0-9à-ỹ]+")
EN_MARKERS = {"what", "is", "vs", "price", "specs", "spec", "release", "date", "best", "how", "review", "benchmark",
              "benchmarks", "performance", "buy", "laptops", "the", "with", "for"}
BLOG_MARKERS = ("là gì", "benchmark", "cách ", "so sánh", "tin tức", "ra mắt", "hiệu năng", "review", "đánh giá",
                "ưu nhược điểm", "có tốt không", "có nên", "bao giờ", "khi nào")
NOT_LAPTOP = ("pc ", " pc", "để bàn", "desktop", "mini pc")
BRANDS = {"asus", "acer", "dell", "hp", "lenovo", "apple", "macbook", "msi", "gigabyte", "huawei", "samsung",
          "lg", "surface", "microsoft", "razer", "xiaomi", "masstel", "avita", "vaio", "intel", "amd", "qualcomm"}
GENERIC = {"laptop", "may", "tinh", "xach", "tay", "chinh", "hang", "gia", "re", "mua", "ai", "plus"}


def tokens(text: str) -> list[str]:
    return TOKEN.findall((text or "").lower())


def slug_tokens(url: str) -> list[str]:
    return tokens(url_path(url).replace("-", " ").replace("/", " "))


def drop_reason(kw: str, page_type: str, own_brand: str, group_tokens: set[str], url_tokens: set[str]) -> str | None:
    """Lý do loại một từ khoá theo luật owner chốt 28/10 (không blog, không hãng khác, bỏ tiếng Anh, phải liên quan URL)."""
    low = f" {kw.lower()} "
    toks = set(tokens(kw))
    if toks & EN_MARKERS:
        return "tiếng Anh"
    if any(m in low for m in BLOG_MARKERS):
        return "ý định bài viết/blog"
    if any(m in low for m in NOT_LAPTOP):
        return "không phải laptop"
    other = (toks & BRANDS) - {own_brand} - group_tokens - url_tokens
    if other:
        return f"hãng khác ({', '.join(sorted(other))})"
    if not (toks & (url_tokens - GENERIC)):
        return "không chứa thực thể của URL"
    return None


def load_kw_file(path: str) -> list[dict]:
    """File research có sẵn: JSON (list hoặc {"keywords": [...]} như raw Ahrefs) hoặc CSV có header keyword,volume[,url,main]."""
    if path.lower().endswith(".csv"):
        with open(path, encoding="utf-8-sig", newline="") as f:
            items = list(csv.DictReader(f))
    else:
        data = json.load(open(path, encoding="utf-8"))
        items = data["keywords"] if isinstance(data, dict) else data
    out = []
    for it in items:
        kw = (it.get("keyword") or it.get("Từ khóa") or "").strip()
        if kw:
            out.append({"keyword": kw, "volume": parse_int(it.get("volume", it.get("Volume", 0))),
                        "url": norm_url(it.get("url") or it.get("URL") or ""), "source": "file research"})
    return out


def _add(store: dict, url: str, kw: str, vol, source: str) -> None:
    u = norm_url(url)
    if u and kw:
        store.setdefault(u, []).append({"keyword": kw.strip(), "volume": parse_int(vol), "source": source})


def fetch_store_keywords(urls: set[str], log=print) -> dict[str, list[dict]]:
    """Đọc 4 nguồn hệ thống (chỉ đọc), trả {url chuẩn hoá: [keyword...]} cho các URL cần tìm."""
    all_kw_id, research_id = require(["sheets.allKw", "sheets.researchSpHangMoi"])
    store: dict[str, list[dict]] = {}
    for r in values_get(all_kw_id, "'All KW'!L2:O"):
        r = (r + [""] * 4)[:4]
        if norm_url(r[3]) in urls:
            _add(store, r[3], r[0], r[1], "All KW")
    for tab in ("Research NH Filter", "Research Dòng Filter"):
        for r in values_get(research_id, f"'{tab}'!D2:H"):
            r = (r + [""] * 5)[:5]
            if norm_url(r[0]) in urls:
                _add(store, r[0], r[2], r[3], tab)
    id_to_url = {}
    for r in values_get(research_id, "'Data_Sản_Phẩm_Mới'!E2:G"):
        r = (r + [""] * 3)[:3]
        if norm_url(r[2]) in urls:
            id_to_url[r[0]] = r[2]
    for r in values_get(research_id, "'KW_Sản_phẩm_Mới'!A2:H"):
        r = (r + [""] * 8)[:8]
        url = r[3] if norm_url(r[3]) in urls else id_to_url.get(r[0], "")
        if url:
            _add(store, url, r[5], r[6], "KW_Sản_phẩm_Mới")
    log(f"  kho từ khoá hệ thống: {sum(len(v) for v in store.values())} từ cho {len(store)}/{len(urls)} URL")
    return store


def assign_to_url(kw: str, urls: list[dict]) -> dict:
    """Gán một từ khoá chưa có URL vào URL của nhóm: mã model riêng > tên SP > từ chung thuộc Filter."""
    toks = set(tokens(kw))
    sps = [u for u in urls if u["page_type"].lower().startswith("sản")]
    filters = [u for u in urls if not u["page_type"].lower().startswith("sản")]
    f_tok = set().union(*(set(slug_tokens(u["url"])) for u in filters)) if filters else set()
    sp_tok = [set(slug_tokens(u["url"])) - GENERIC - f_tok for u in sps]  # token riêng của SP, không phải khái niệm của Filter
    for u, t in zip(sps, sp_tok):
        others = set().union(*(x for x in sp_tok if x is not t)) if len(sps) > 1 else set()
        if toks & (t - others):
            return u
    if sps and toks & set().union(*sp_tok):
        return sps[0]  # tên SP chung của nhóm (hãng, dòng) gắn SP đầu tiên, theo cách owner chốt ở order RTX Spark
    return (filters or sps)[0]  # chỉ còn khái niệm chung (vd "rtx spark" + laptop) thuộc trang Filter


CODE = re.compile(r"^(?=.*\d)(?=.*[a-z])[a-z0-9]{4,}$")  # mã model kiểu c1xmt, 016vn


def _name_tokens(url: str) -> list[str]:
    return tokens(url_path(url).strip("/").split("/")[-1].replace("-", " "))


def candidate_terms(url: str) -> list[str]:
    """Từ chung chung hơn tên đầy đủ để dò SERP khi URL không có từ khoá (một SP đôi khi rank cho từ rộng hơn).

    SP: tên bỏ mã model, cắt 4 và 5 từ đầu. Filter: toàn bộ slug. Tối đa 2 từ/URL (mỗi từ 1 credit SerpApi).
    """
    toks = _name_tokens(url)
    if len(url_path(url).strip("/").split("/")) < 2:
        return [" ".join(toks)] if toks else []
    plain = [t for t in toks if not CODE.match(t)]
    return list(dict.fromkeys(" ".join(plain[:n]) for n in (4, 5) if len(plain) >= 3))


def autogen_keyword(url: str) -> dict:
    """Không có từ khoá nào (kể cả dò SERP): sinh 1 từ khoá đại diện từ slug, volume 0, đánh dấu để owner duyệt.

    SP: cắt slug tới mã model cuối cùng (vd "... c1xmt 017vn"), bỏ phần công nghệ phía sau. Filter: cả slug.
    """
    toks = _name_tokens(url)
    if len(url_path(url).strip("/").split("/")) >= 2:
        codes = [i for i, t in enumerate(toks) if CODE.match(t)]
        if codes:
            toks = toks[: codes[-1] + 1]
    return {"keyword": " ".join(toks), "volume": 0, "source": "tự sinh từ URL"}
