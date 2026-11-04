#!/usr/bin/env python3
"""Ghép từ khoá, hành động, Title/Meta thành một "plan" (dict) cho một nhóm sản phẩm. Không ghi gì ra ngoài."""
from __future__ import annotations

import datetime as dt
import json

import kw_sources as ks
import serp_check
from action_plan import build_actions
from nh_order_lib import cfg, fmt_date, norm_url, url_path

def _filter_exempt(kw: str, u: dict) -> bool:
    """Luật owner 28/10: từ chung về khái niệm của Filter + "laptop" thuộc trang Filter, không loại theo SERP."""
    if u["page_type"].lower().startswith("sản"):
        return False
    concept = set(ks.slug_tokens(u["url"])) - ks.GENERIC
    toks = set(ks.tokens(kw))
    return bool(concept) and concept <= toks and "laptop" in toks


def _probe_or_generate(u: dict, cache: dict, cache_path: str | None, call: bool, budget: int, today: str,
                       use_serp: bool, log) -> list[dict]:
    """URL không có từ khoá trong Ahrefs/kho: dò SERP các từ chung chung hơn xem URL có rank không; nếu không thì tự sinh 1 từ đại diện."""
    if use_serp:
        cands = ks.candidate_terms(u["url"])
        notes = serp_check.annotate(cands, cache, cache_path, call, budget, today, log)
        hits = [c for c in cands if c in cache and any(norm_url(r[1]) == u["url_norm"] for r in cache[c])]
        if hits:
            return [{"keyword": c, "volume": 0, "source": "SERP: URL có trong top 10 (volume chưa đo)",
                     "serp": notes[c]["note"]} for c in hits]
        log(f"  {url_path(u['url'])}: dò SERP {cands} không thấy URL trong top 10, tự sinh từ khoá đại diện")
    g = ks.autogen_keyword(u["url"])
    g["serp"] = ""
    return [g]


def build_keywords(group: dict, kw_file: str | None, serp_cache: str | None, call_serp: bool, approve_serp: int,
                   today: str, max_kw: int | None, log=print) -> dict:
    urls = [{"url": r["url"], "url_norm": r["url_norm"], "page_type": r["page_type"]} for r in group["pending"]]
    by_url: dict[str, list[dict]] = {u["url_norm"]: [] for u in urls}
    dropped: list[dict] = []
    group_tokens = set(ks.tokens(group["name"]))
    own_brand = (ks.slug_tokens(urls[0]["url"])[1:2] or [""])[0] if urls[0]["page_type"].lower().startswith("sản") else ""

    pool = ks.load_kw_file(kw_file) if kw_file else []
    store = ks.fetch_store_keywords({u["url_norm"] for u in urls}, log)
    for u, items in store.items():
        for it in items:
            by_url[u].append(it)
    for it in pool:
        target = next((u for u in urls if u["url_norm"] == it["url"]), None) or ks.assign_to_url(it["keyword"], urls)
        by_url[target["url_norm"]].append(it)

    # Pass 1: gộp trùng + lọc theo luật tĩnh (không tốn credit). Chỉ từ còn lại mới đem kiểm SERP.
    merged_by_url: dict[str, list[dict]] = {}
    for u in urls:
        merged: dict[str, dict] = {}
        for it in by_url[u["url_norm"]]:
            key = it["keyword"].lower()
            if key in merged:
                merged[key]["volume"] = max(merged[key]["volume"], it["volume"])
            else:
                merged[key] = dict(it)
        url_tok = set(ks.slug_tokens(u["url"]))
        survivors = []
        for it in merged.values():
            why = ks.drop_reason(it["keyword"], u["page_type"], own_brand, group_tokens, url_tok)
            if why:
                dropped.append({"keyword": it["keyword"], "volume": it["volume"], "url": u["url"], "reason": why})
            else:
                survivors.append(it)
        merged_by_url[u["url_norm"]] = survivors

    serp, use_serp = {}, bool(serp_cache or call_serp)
    cache = serp_check.load_cache(serp_cache) if use_serp else {}
    base_len = len(cache)  # số credit đã tiêu = số từ khoá mới vào cache so với lúc đầu
    if use_serp:
        all_kw = sorted({it["keyword"] for v in merged_by_url.values() for it in v})
        serp = serp_check.annotate(all_kw, cache, serp_cache, call_serp, approve_serp, today, log)

    # Pass 2: loại theo SERP, trần (nếu có), dò SERP/tự sinh cho URL không còn từ khoá nào.
    result = {}
    for u in urls:
        kept = []
        for it in merged_by_url[u["url_norm"]]:
            sv = serp.get(it["keyword"])
            if sv and sv["kind"] == "bài viết/tin" and not _filter_exempt(it["keyword"], u):
                dropped.append({"keyword": it["keyword"], "volume": it["volume"], "url": u["url"],
                                "reason": "SERP toàn bài viết/tin, hợp bài blog hơn trang bán hàng"})
            else:
                it["serp"] = sv["note"] if sv else ""
                kept.append(it)
        kept.sort(key=lambda x: (-x["volume"], len(x["keyword"])))
        if max_kw:  # mặc định không có trần: lấy mọi từ đúng intent (owner chốt 29/10)
            for it in kept[max_kw:]:
                dropped.append({"keyword": it["keyword"], "volume": it["volume"], "url": u["url"], "reason": f"vượt trần {max_kw} từ/URL"})
            kept = kept[:max_kw]
        if not kept:
            kept = _probe_or_generate(u, cache, serp_cache, call_serp, approve_serp - (len(cache) - base_len), today, use_serp, log)
        for it in kept:
            it["main"] = True  # luật team (Rule_Từ_Khóa): mọi từ khoá đưa vào đều là KW chính
        result[u["url"]] = kept
    return {"urls": urls, "keywords": result, "dropped": dropped}


def build_plan(group: dict, args, log=print) -> dict:
    today = dt.date.today()
    start = args.start or today
    c = cfg()
    owner = c.get("nhOrder.defaultOwner", "")
    news_owner = None if args.no_news else c.get("nhOrder.newsOwner")
    kws = build_keywords(group, args.kw_file, args.serp_cache, args.serp, args.approve_serp, fmt_date(today), args.max_kw, log)
    research = json.load(open(args.research, encoding="utf-8")) if args.research else None
    title_meta = {}
    if args.title_meta:
        for it in json.load(open(args.title_meta, encoding="utf-8")):
            title_meta[norm_url(it["url"])] = it
    actions = build_actions(kws["urls"], research, start, owner, news_owner)
    return {"group": group["name"], "code": group["code"], "km": group["km"], "start": fmt_date(start),
            "urls": kws["urls"], "keywords": kws["keywords"], "dropped": kws["dropped"], "actions": actions,
            "title_meta": title_meta, "target_rows": [r["row"] for r in group["pending"]],
            "row_urls": {r["row"]: r["url_norm"] for r in group["pending"]},
            "warnings": _warnings(kws, research, title_meta)}


def _warnings(kws: dict, research: dict | None, title_meta: dict) -> list[str]:
    w = []
    for u in kws["urls"]:
        if kws["keywords"][u["url"]][0]["source"] == "tự sinh từ URL":
            w.append(f"{url_path(u['url'])}: không có từ khoá nào, đã tự sinh 1 từ (volume 0), cần owner duyệt hoặc xin units Ahrefs")
        if u["url_norm"] not in title_meta:
            w.append(f"{url_path(u['url'])}: chưa có đề xuất Title/Meta (chạy skill tgdd-seo-title-description rồi truyền --title-meta)")
    if not research:
        w.append("Chưa có research bài viết (Anti): thiếu dòng Renew/Lên bài mới, xem references/anti-research.md")
    return w
