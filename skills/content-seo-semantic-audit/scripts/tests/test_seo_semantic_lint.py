"""Test lint bài SEO semantic. Chạy: python3 -m unittest discover -s scripts/tests"""
import importlib.util
import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("lint", os.path.join(HERE, "..", "seo-semantic-lint.py"))
lint_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_mod)

BRIEF = {
    "kw_chinh": "bảo lãnh vợ chồng",
    "kw_phu": ["bảo lãnh vợ chồng sang mỹ"],
    "brand": "ACME",
    "brand_so_lan": 4,
    "brand_tieu_de": {"h1": 1, "h2": 1},
    "kw_chinh_nguyen_cum": 2,
    "tan_suat_toi_da": {"bảo lãnh vợ chồng": 3},
    "cau_truc_h2": [{"h3": 1, "checklist": False}, {"h3": 0, "checklist": True}],
    "tu_han_che": ["hỗ trợ"],
    "tu_han_che_toi_da": 1,
    "cta_ket": "Liên hệ ACME ngay.",
    "so_tu": {"muc_tieu": 10, "toi_da": 200},
}

GOOD = """META: Hướng dẫn ngắn về hồ sơ.
# Bảo lãnh vợ chồng cùng ACME
Sapo nói về bảo lãnh vợ chồng và ACME.
## Hồ sơ cần có tại ACME
### Giấy tờ
Chuẩn bị giấy tờ cho bảo lãnh vợ chồng sang Mỹ thật kỹ.
## Danh sách kiểm tra
- Ảnh cưới
- Sao kê chung
Liên hệ ACME ngay.
"""


def levels(md, brief=BRIEF, stage="final"):
    return {(r["level"], r["check"]) for r in lint_mod.lint(md, brief, stage)}


class LintTest(unittest.TestCase):
    def test_good_article_has_no_fail(self):
        fails = [r for r in lint_mod.lint(GOOD, BRIEF) if r["level"] == "FAIL"]
        self.assertEqual(fails, [])

    def test_variant_does_not_count_as_standalone_keyword(self):
        text = lint_mod.norm("bảo lãnh vợ chồng sang mỹ và bảo lãnh vợ chồng")
        self.assertEqual(lint_mod.standalone(text, "bảo lãnh vợ chồng", ["bảo lãnh vợ chồng sang mỹ"]), 1)
        self.assertEqual(lint_mod.count(text, "bảo lãnh vợ chồng"), 2)

    def test_missing_cta_and_bold_fail(self):
        md = GOOD.replace("Liên hệ ACME ngay.", "Liên hệ **ACME** sớm.")
        got = levels(md)
        self.assertIn(("FAIL", "cta"), got)
        self.assertIn(("FAIL", "dinh_dang"), got)

    def test_structure_mismatch_fails(self):
        md = GOOD.replace("### Giấy tờ\n", "")
        self.assertIn(("FAIL", "cau_truc"), levels(md))

    def test_restricted_word_over_limit(self):
        md = GOOD.replace("Ảnh cưới", "hỗ trợ hỗ trợ")
        self.assertIn(("FAIL", "tu_han_che"), levels(md))

    def test_meta_missing_is_warn_in_draft(self):
        md = GOOD.split("\n", 1)[1]
        self.assertIn(("WARN", "meta"), levels(md, stage="draft"))
        self.assertIn(("FAIL", "meta"), levels(md, stage="final"))

    def test_english_word_flagged(self):
        md = GOOD.replace("Ảnh cưới", "Ảnh cưới và interview")
        self.assertIn(("WARN", "tieng_anh"), levels(md))


if __name__ == "__main__":
    unittest.main()
