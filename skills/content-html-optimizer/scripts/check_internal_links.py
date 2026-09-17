#!/usr/bin/env python3
"""QC internal link sau khi optimize xong bài.

Chạy lớp luật xác định (chi phí 0) để lọc ra link nghi sai ngữ cảnh, rồi xuất
JSON làm đầu vào cho lớp review bằng model.

Nguyên tắc gốc: link đúng khi trang đích nói về ĐÚNG thực thể mà anchor đang chỉ
trong câu đó — không phải thứ chứa nó (dòng/hãng/ngành hàng), thứ gần nó (phụ
kiện cùng tên), hay thứ trùng tên khác nghĩa.

Usage:
    python3 check_internal_links.py --workspace <path> [--json out.json]
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

MAP_FILE = Path(__file__).resolve().parent.parent / "references" / "link-category-map.json"

# Token ngay sau anchor cho thấy anchor chỉ là tiền tố của một tên dài hơn:
# mã đời ("7", "15IAX9E", "F16", "108a", "P2505W").
MODEL_TOKEN = re.compile(r"^[\s ]{0,2}([0-9][0-9A-Za-z\-\.]{0,14}|[A-Z][0-9][0-9A-Za-z\-]{0,13})\b")
# Đơn vị đo — token sau anchor là thông số, KHÔNG phải mã đời.
SPEC_UNIT = re.compile(
    r"^\s*\d[\d\.,]*\s*(hz|ghz|mhz|w|wh|kw|v|mah|gb|tb|mb|nits?|inch|mm|cm|kg|g|bit|fps|dpi|"
    r"trang|nhân|luồng|k\b|%)",
    re.IGNORECASE,
)
LINK_RE = re.compile(r'<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
INFO_RE = re.compile(r"\[info\].*?\[/info\]", re.S)
XEMTHEM_RE = re.compile(r"\[info\](?:(?!\[/info\]).)*?Xem th[êe]m.*?\[/info\]", re.S | re.I)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def path_of(url):
    p = re.sub(r"^https?://[^/]+", "", url.split("?")[0].split("#")[0])
    return p.strip("/")


def first_segment(url):
    p = path_of(url)
    return p.split("/")[0] if p else ""


def article_id(url):
    m = re.search(r"(\d{5,8})/?$", path_of(url))
    return m.group(1) if m else None


class Checker:
    def __init__(self, cfg, nganh):
        self.seg2nganh = {}
        for ng, prefixes in cfg["nganh_hang"].items():
            for p in prefixes:
                self.seg2nganh[p] = ng
        self.trung_tinh = set(cfg["trung_tinh"])
        self.brands = set(cfg.get("brand_tokens", []))
        self.nganh = nganh
        self.phu_kien_ok = set(cfg.get("phu_kien_hop_le", {}).get(nganh, []))

    def is_brand_page(self, url):
        """Đích là trang hãng/dòng (vd /may-in-hp, /laptop-acer-aspire).

        Ở trang loại này, token số ngay sau anchor là MÃ ĐỜI ('HP 107w'), không
        phải đơn vị đo — nên không được miễn trừ bằng SPEC_UNIT.
        """
        segs = path_of(url).split("-")
        return any(b in segs for b in self.brands)

    def nganh_of(self, url):
        seg = first_segment(url)
        if seg in self.trung_tinh:
            return "trung-tinh"
        # khớp prefix dài nhất: "laptop-acer-aspire" -> "laptop"
        best = None
        for p, ng in self.seg2nganh.items():
            if seg == p or seg.startswith(p + "-"):
                if best is None or len(p) > len(best[0]):
                    best = (p, ng)
        return best[1] if best else "khong-ro"

    def is_explainer(self, url):
        return first_segment(url) in ("hoi-dap", "tin-tuc")


def sentence_around(text, pos, width=170):
    seg = text[max(0, pos - width): pos + width]
    seg = re.sub(r"\s+", " ", seg).strip()
    return seg


def check(workspace, cfg):
    ws = Path(workspace)
    final = (ws / "source" / "final-content.html").read_text(encoding="utf-8")
    src_file = ws / "source" / "source-content.html"
    src_urls = set()
    if src_file.exists():
        src_urls = set(re.findall(r'href="([^"]+)"', src_file.read_text(encoding="utf-8")))

    slug = ws.name
    nganh = "khong-ro"
    for prefix, ng in cfg["nganh_theo_slug"].items():
        if slug.startswith(prefix):
            nganh = ng
            break
    ck = Checker(cfg, nganh)

    self_ids = set()
    url_file = ws / "source" / "article-url.txt"
    if url_file.exists():
        aid = article_id(url_file.read_text(encoding="utf-8").strip())
        if aid:
            self_ids.add(aid)

    info_zones = [(m.start(), m.end()) for m in INFO_RE.finditer(final)]
    xemthem_urls = set()
    for m in XEMTHEM_RE.finditer(final):
        xemthem_urls.update(u for u, _ in LINK_RE.findall(m.group(0)))

    plain = strip_tags(final)
    findings, seen = [], {}
    for m in LINK_RE.finditer(final):
        url, inner = m.group(1), m.group(2)
        anchor = strip_tags(inner).strip()
        after = strip_tags(final[m.end(): m.end() + 60])
        inserted = url not in src_urls
        in_info = any(a <= m.start() < b for a, b in info_zones)
        cases = []

        # D2 — trùng đích
        if url in seen:
            cases.append(("D2", "dup-url", f"URL đã dùng ở link '{seen[url]}'"))
        else:
            seen[url] = anchor

        # D1 — tự link về chính bài
        if article_id(url) and article_id(url) in self_ids:
            cases.append(("D1", "self-link", "trỏ về chính bài này"))

        # C1 — trong khối [info] thông số mà đích là category mua hàng
        if (in_info and not ck.is_explainer(url) and url not in xemthem_urls
                and first_segment(url) not in ck.trung_tinh):
            cases.append(("C1", "info-block-category",
                          "nằm trong khối [info] thông số nhưng đích là trang mua hàng"))

        # A1/A4 — anchor là tiền tố, mã đời nằm ngay sau, đích là category dòng/hãng
        spec_exempt = SPEC_UNIT.match(after) and not ck.is_brand_page(url)
        if not ck.is_explainer(url) and not spec_exempt:
            t = MODEL_TOKEN.match(after)
            if t:
                cases.append(("A1", "prefix-swallow",
                              f"ngữ cảnh nói về '{anchor} {t.group(1)}', đích chỉ là '{path_of(url)}'"))

        # B4 — lệch ngành hàng bài
        dest_ng = ck.nganh_of(url)
        if (nganh != "khong-ro" and dest_ng not in ("trung-tinh", "khong-ro", nganh)
                and first_segment(url) not in ck.phu_kien_ok):
            cases.append(("B4", "cross-category",
                          f"bài ngành '{nganh}' nhưng đích thuộc ngành '{dest_ng}'"))

        # D3 — đích đã nằm trong box Xem thêm
        if url in xemthem_urls and not in_info:
            cases.append(("D3", "dup-xem-them", "đích đã được dẫn trong box Xem thêm"))

        if cases:
            findings.append({
                "cases": [c for c, _, _ in cases],
                "rules": [r for _, r, _ in cases],
                "anchor": anchor, "url": url,
                "inserted_by_optimizer": inserted, "in_info_block": in_info,
                "why": "; ".join(w for _, _, w in cases),
                "cau": sentence_around(plain, len(strip_tags(final[:m.start()]))),
            })

    total = len(LINK_RE.findall(final))
    return {"workspace": slug, "nganh_hang": nganh, "tong_link": total,
            "so_findings": len(findings), "findings": findings}


def strip_flagged_links(ws: Path, findings) -> int:
    """Gỡ thẻ <a> của các link bị gắn cờ, giữ nguyên phần chữ bên trong.

    Chạy trên `final-content.html`. Optimizer chèn link lại ở MỖI lần build, nên
    bước này phải chạy lại sau mỗi lần optimize — không phải sửa một lần là xong.
    """
    path = ws / "source" / "final-content.html"
    html_text = path.read_text(encoding="utf-8")
    backup = path.with_suffix(".html.prelinkfix")
    if not backup.exists():
        backup.write_text(html_text, encoding="utf-8")

    # D2 (trùng URL) KHÔNG tự gỡ: hai link cùng URL có thể là 2 nút CTA đặt đầu
    # và cuối bài — thiết kế cố ý. Người quyết, không để script quyết.
    targets = {(f["anchor"].strip(), f["url"]) for f in findings
               if f["cases"] != ["D2"]}
    removed = 0

    def repl(m):
        nonlocal removed
        inner = m.group(2)
        if (strip_tags(inner).strip(), m.group(1)) in targets:
            removed += 1
            return inner
        return m.group(0)

    path.write_text(LINK_RE.sub(repl, html_text), encoding="utf-8")
    return removed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--json", help="ghi kết quả ra file JSON")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--fix", action="store_true",
                    help="GỠ các link bị gắn cờ khỏi final-content.html (giữ nguyên chữ). "
                         "Chỉ dùng SAU KHI người đã đọc từng câu và duyệt.")
    a = ap.parse_args()

    cfg = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    r = check(a.workspace, cfg)

    if not a.quiet:
        print(f"\n{r['workspace']}  (ngành: {r['nganh_hang']}, {r['tong_link']} link) "
              f"-> {r['so_findings']} nghi ngờ")
        for f in r["findings"]:
            print(f"  [{'+'.join(f['cases'])}] {f['anchor'][:32]:34s} -> {path_of(f['url'])[:50]}")
            print(f"        {f['why']}")
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    if a.fix and r["findings"]:
        removed = strip_flagged_links(Path(a.workspace), r["findings"])
        print(f"  [FIX] gỡ {removed}/{r['so_findings']} link (giữ nguyên chữ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
