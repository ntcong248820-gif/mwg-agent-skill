#!/usr/bin/env python3
"""Test không cần mạng: timeline, gán từ khoá vào URL, luật lọc. Chạy: python3 tests/test_action_plan.py"""
import datetime as dt
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import action_plan as ap  # noqa: E402
import kw_sources as ks  # noqa: E402
from nh_order_lib import add_workdays, norm_url  # noqa: E402

SP1 = {"url": "https://www.thegioididong.com/laptop/msi-prestige-n16-flip-ai-c1xmt-016vn-rtx-spark-n1x", "page_type": "Sản phẩm"}
SP2 = {"url": "https://www.thegioididong.com/laptop/msi-prestige-n16-flip-ai-c1xmt-017vn-rtx-spark-n1x", "page_type": "Sản phẩm"}
FL = {"url": "https://www.thegioididong.com/laptop-rtx-spark", "page_type": "Filter"}
URLS = [SP1, SP2, FL]


def test_workdays_skip_weekend():
    assert add_workdays(dt.date(2026, 10, 30), 1) == dt.date(2026, 11, 2)  # thứ Sáu -> thứ Hai


def test_assign():
    assert ks.assign_to_url("msi prestige n16 flip ai+ c1xmt 017vn", URLS) is SP2
    assert ks.assign_to_url("msi prestige n16 flip ai+", URLS) is SP1
    assert ks.assign_to_url("rtx spark laptop", URLS) is FL
    assert ks.assign_to_url("nvidia rtx spark", URLS) is FL


def test_drop_reason():
    toks = set(ks.slug_tokens(FL["url"]))
    assert ks.drop_reason("rtx spark là gì", "Filter", "", set(), toks)
    assert ks.drop_reason("rtx spark price", "Filter", "", set(), toks) == "tiếng Anh"
    assert ks.drop_reason("asus rtx spark", "Filter", "", set(), toks).startswith("hãng khác")
    assert ks.drop_reason("rtx spark laptop", "Filter", "", set(), toks) is None


def test_actions_timeline_and_research():
    start = dt.date(2026, 10, 28)
    rs = {"renew": [{"url": "https://x/a-12345", "note": "Thêm X vào danh sách"}],
          "new_articles": [{"site": "game-app", "topic": "T1", "existing_url": None},
                           {"site": "hoi-dap", "topic": "T2", "existing_url": "https://x/b-54321"}]}
    rows = ap.build_actions(URLS, rs, start, "Công - 1", "Vinh - 2")
    acts = [r["action"] for r in rows]
    assert acts.count(ap.A_TITLE) == 3 and acts.count(ap.A_PROMOTE) == 3 and acts.count(ap.A_RENEW) == 2
    assert acts.count("Lên bài viết mới Game App") == 1 and ap.A_NEWS in acts
    assert rows[0]["date"] == dt.date(2026, 10, 29)
    assert max(r["date"] for r in rows if r["date"]) <= add_workdays(start, 12)  # trong ~2 tuần
    assert next(r for r in rows if r["action"] == ap.A_NEWS)["date"] is None


def test_representative_keyword_and_candidates():
    assert ks.autogen_keyword(SP2["url"])["keyword"] == "msi prestige n16 flip ai c1xmt 017vn"
    assert ks.autogen_keyword(FL["url"])["keyword"] == "laptop rtx spark"
    assert ks.candidate_terms(FL["url"]) == ["laptop rtx spark"]
    assert ks.candidate_terms(SP2["url"]) == ["msi prestige n16 flip", "msi prestige n16 flip ai"]


def test_norm_url():
    assert norm_url("https://thegioididong.com/laptop-rtx-spark/?a=1#x") == "https://www.thegioididong.com/laptop-rtx-spark"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
