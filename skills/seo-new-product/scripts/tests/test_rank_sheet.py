#!/usr/bin/env python3
"""Test không cần mạng: cấu trúc Rank_Theo_Dõi 15 cột, quét ô lỗi Tổng_Hợp, dữ liệu seed. Chạy: python3 tests/test_rank_sheet.py"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import plan_writer as pw  # noqa: E402
import rank_sheet as rs  # noqa: E402

CURRENT = ["Keyword", "Rank", "Domain", "URL", "AI Overview", "Side panel", "Citation", "Link", "AIO total",
           "Top 1 URL", "Top 1 Title", "Top 2 URL", "Top 2 Title", "Top 3 URL", "Top 3 Title", "Ngày đo"]


def test_header_ok():
    assert rs.header_problems(CURRENT) == []
    assert rs.header_problems(CURRENT + ["", ""]) == []


def test_header_without_date_column_rejected():
    assert any("Ngày đo" in b for b in rs.header_problems(CURRENT[:15]))


def test_header_old_structure_rejected():
    old = ["Ngày đo", "Từ khóa", "URL", "Thứ hạng", "Hiện trên AI Overview?", "Nhóm ranking", "Ghi chú"]
    bad = rs.header_problems(old)
    assert bad and "cột 1" in bad[0]


def test_header_extra_column_rejected():
    assert any("thừa" in b for b in rs.header_problems(CURRENT + ["Ghi chú"]))


def test_find_errors():
    vals = [["a", "#REF!"], ["#N/A", "5"], ["#ERROR!", "#DIV/0!"], ["Top 1", "2"]]
    assert len(rs.find_errors(vals)) == 4
    assert rs.find_errors([["a", "1"], ["", "—"]]) == []


def test_seed_only_keyword_column():
    plan = {"urls": [{"url": "https://www.thegioididong.com/laptop-rtx-spark", "url_norm": "x", "page_type": "Filter"}],
            "keywords": {"https://www.thegioididong.com/laptop-rtx-spark": [
                {"keyword": "rtx spark laptop", "volume": 200, "main": True, "source": "ahrefs"},
                {"keyword": "laptop rtx spark", "volume": 70, "main": True, "source": "ahrefs"}]},
            "title_meta": {}, "actions": [], "start": "29/10/2026"}
    exp = pw._expected(plan)
    assert exp[pw.RK] == [["rtx spark laptop"], ["laptop rtx spark"]]


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
    print(f"{n} test pass")
