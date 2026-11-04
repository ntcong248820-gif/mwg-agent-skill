#!/usr/bin/env python3
"""QC internal link sau khi optimize xong bài.

Chạy lớp luật xác định (chi phí 0) để lọc ra link nghi sai ngữ cảnh, rồi xuất
JSON làm đầu vào cho lớp review bằng model.

Nguyên tắc gốc: link đúng khi trang đích nói về ĐÚNG thực thể mà anchor đang chỉ
trong câu đó — không phải thứ chứa nó (dòng/hãng/ngành hàng), thứ gần nó (phụ
kiện cùng tên), hay thứ trùng tên khác nghĩa.

Ngoài ngữ cảnh, script còn kiểm hai thứ đo được chắc chắn: anchor có cắt nửa cụm
không (F1 — "laptop [HP]"), và href có trả 200 mà không redirect không (F2/F3).

Usage:
    python3 check_internal_links.py --workspace <path> [--json out.json] [--offline]
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_anchor as la  # noqa: E402
import link_category as lc  # noqa: E402
import link_redirect as lr  # noqa: E402

MAP_FILE = lc.MAP_FILE

# Mức nghiêm trọng của từng case. FAIL = link sai/hỏng, phải xử lý trước khi air;
# WARN = heuristic ngữ cảnh, đọc câu rồi quyết.
SEVERITY = {
    "A1": "FAIL", "B4": "FAIL", "C1": "FAIL", "D1": "FAIL", "D3": "FAIL",
    "E1": "FAIL", "F2": "FAIL", "F3": "FAIL",
    "D2": "WARN", "E2": "WARN", "E3": "WARN", "F1": "WARN",
}

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
LI_RE = re.compile(r"<li\b[^>]*>.*?</li>", re.S | re.I)
H4_RE = re.compile(r"<h4\b[^>]*>(.*?)</h4>", re.S | re.I)
# Tự xưng: anchor hoặc đích là chính TGDĐ / trang chủ.
SELF_BRAND_RE = re.compile(r"th[êe]́?\s*gi[ơo]́?i\s*di\s*đ[ôo]̣?ng|thegioididong|tgdđ|tgdd", re.I)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s))


def normalize_name(s):
    return re.sub(r"\s+", " ", strip_tags(s)).strip().lower()


def product_names(final_html):
    """Tên sản phẩm lấy từ các <h4> (bỏ phần mã trong ngoặc) — dùng để phát hiện
    anchor nằm LỌT trong tên sản phẩm."""
    names = []
    for m in H4_RE.finditer(final_html):
        name = normalize_name(m.group(1))
        name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
        if len(name.split()) >= 2:
            names.append(name)
    return names


def is_pdp(url):
    """PDP = trang sản phẩm: đúng 2 segment và segment đầu không phải hệ bài viết."""
    segs = [s for s in path_of(url).split("/") if s]
    return len(segs) == 2 and segs[0] not in ("hoi-dap", "tin-tuc", "kinh-nghiem-hay", "game-app")


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
    def __init__(self, cfg, nganh, article_seg=""):
        self.cfg = cfg
        self.trung_tinh = set(cfg["trung_tinh"])
        self.brands = set(cfg.get("brand_tokens", []))
        self.nganh = nganh
        self.article_seg = article_seg

    def is_brand_page(self, url):
        """Đích là trang hãng/dòng (vd /may-in-hp, /laptop-acer-aspire).

        Ở trang loại này, token số ngay sau anchor là MÃ ĐỜI ('HP 107w'), không
        phải đơn vị đo — nên không được miễn trừ bằng SPEC_UNIT.
        """
        segs = path_of(url).split("-")
        return any(b in segs for b in self.brands)

    def cross_nganh(self, url):
        """Ngành đích nếu lệch ngành bài (sau khi trừ phụ kiện hợp lệ), không thì None."""
        return lc.is_cross(url, self.nganh, self.article_seg, self.cfg)

    def is_explainer(self, url):
        return first_segment(url) in ("hoi-dap", "tin-tuc")


def sentence_around(text, pos, width=170):
    seg = text[max(0, pos - width): pos + width]
    seg = re.sub(r"\s+", " ", seg).strip()
    return seg


def check(workspace, cfg, offline=False):
    ws = Path(workspace)
    final = (ws / "source" / "final-content.html").read_text(encoding="utf-8")
    src_file = ws / "source" / "source-content.html"
    src_urls = set()
    if src_file.exists():
        src_urls = set(re.findall(r'href="([^"]+)"', src_file.read_text(encoding="utf-8")))

    slug = ws.name
    url_file = ws / "source" / "article-url.txt"
    self_url = url_file.read_text(encoding="utf-8").strip().splitlines()[0].strip() \
        if url_file.exists() and url_file.read_text(encoding="utf-8").strip() else ""
    nganh, article_seg = lc.article_nganh(slug, self_url, cfg)
    ck = Checker(cfg, nganh, article_seg)

    self_ids = set()
    if self_url:
        aid = article_id(self_url)
        if aid:
            self_ids.add(aid)

    info_zones = [(m.start(), m.end()) for m in INFO_RE.finditer(final)]
    li_zones = [(m.start(), m.end()) for m in LI_RE.finditer(final)]
    names = product_names(final)
    xemthem_urls = set()
    for m in XEMTHEM_RE.finditer(final):
        xemthem_urls.update(u for u, _ in LINK_RE.findall(m.group(0)))

    # Trạng thái HTTP của mọi href nội bộ: link trong bài đã build phải trả 200
    # và KHÔNG redirect. Đo một lượt, song song, cache trong cùng lần chạy.
    http = {}
    if not lr.offline(offline):
        http = lr.resolve_many([u for u, _ in LINK_RE.findall(final) if lr.is_internal(u)])

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
        dest_ng = ck.cross_nganh(url)
        if dest_ng:
            cases.append(("B4", "cross-category",
                          f"bài ngành '{nganh}' nhưng đích thuộc ngành '{dest_ng}'"))

        # D3 — đích đã nằm trong box Xem thêm
        if url in xemthem_urls and not in_info:
            cases.append(("D3", "dup-xem-them", "đích đã được dẫn trong box Xem thêm"))

        # E1 — anchor nằm trong <li> khối thông số: dòng thông số không phải chỗ đi link
        if any(a <= m.start() < b for a, b in li_zones) and in_info and url not in xemthem_urls:
            cases.append(("E1", "spec-li-anchor",
                          "anchor nằm trong <li> khối thông số, không phải câu văn"))

        # E2 — tự xưng: anchor CHÍNH LÀ tên TGDĐ, hoặc đích là trang chủ.
        # Chỉ khớp khi cả anchor là tên hãng mình — tiêu đề bài có đuôi "tại TGDĐ"
        # là anchor hợp lệ của box Xem thêm, không phải lỗi.
        if not path_of(url) or SELF_BRAND_RE.fullmatch(anchor.strip()):
            cases.append(("E2", "self-brand-home",
                          f"anchor/đích là chính TGDĐ hoặc trang chủ ('{anchor[:40]}')"))

        # E3 — anchor lọt GIỮA tên sản phẩm mà đích không phải PDP của SP đó.
        # Điều kiện: chữ trước anchor nối đúng phần đầu tên SP VÀ chữ sau anchor nối
        # đúng phần đuôi. Anchor mở đầu một câu nói về hãng/dòng ("Asus là...") không
        # thỏa vì phần đuôi tên SP không theo sau.
        before = normalize_name(final[max(0, m.start() - 120): m.start()])
        after_n = normalize_name(after)
        anchor_n = normalize_name(anchor)
        if anchor_n and not is_pdp(url):
            for nm in names:
                if anchor_n == nm or anchor_n not in nm:
                    continue
                cut = nm.index(anchor_n)
                head, tail = nm[:cut].strip(), nm[cut + len(anchor_n):].strip()
                if head and not before.endswith(head):
                    continue
                if tail and not after_n.startswith(tail.split()[0]):
                    continue
                if not head and not tail:
                    continue
                cases.append(("E3", "inside-product-name",
                              f"anchor '{anchor}' là một phần tên SP '{nm}', đích lại là "
                              f"'{path_of(url)}'"))
                break

        # F1 — anchor cắt nửa cụm: "laptop [HP]", "màn hình [OLED]".
        # Chữ ngay trước anchor lấy nguyên văn từ HTML (strip_tags biến thẻ thành
        # khoảng trắng), nên "laptop " vẫn còn nguyên khoảng cách để nhận cụm.
        before_raw = strip_tags(final[max(0, m.start() - 80): m.start()])
        full_phrase = la.partial_phrase_anchor(anchor, before_raw)
        if full_phrase:
            cases.append(("F1", "partial-phrase-anchor",
                          f"anchor '{anchor}' cắt nửa cụm, phải bọc cả '{full_phrase}'"))

        # F2/F3 — đích chết hoặc còn redirect. Link trong bài phải là URL CUỐI.
        res = http.get(url)
        if res:
            verdict, why = lr.classify(res)
            if verdict == "dead":
                cases.append(("F2", "dead-link", f"đích không truy cập được ({why})"))
            elif verdict == "offtopic":
                cases.append(("F3", "redirect-offtopic", f"đích redirect lệch chủ đề: {why}"))
            elif verdict == "redirect":
                cases.append(("F3", "redirect-link",
                              f"đích còn redirect, phải dùng URL cuối: {why}"))

        if cases:
            findings.append({
                "cases": [c for c, _, _ in cases],
                "severity": ("FAIL" if any(SEVERITY.get(c) == "FAIL" for c, _, _ in cases)
                             else "WARN"),
                "rules": [r for _, r, _ in cases],
                "anchor": anchor, "url": url,
                "inserted_by_optimizer": inserted, "in_info_block": in_info,
                "why": "; ".join(w for _, _, w in cases),
                "cau": sentence_around(plain, len(strip_tags(final[:m.start()]))),
            })

    total = len(LINK_RE.findall(final))
    return {"workspace": slug, "nganh_hang": nganh, "tong_link": total,
            "so_findings": len(findings),
            "so_fail": sum(1 for f in findings if f["severity"] == "FAIL"),
            "http_checked": bool(http),
            "findings": findings}


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
    # và cuối bài — thiết kế cố ý. E2/E3 là heuristic ngữ cảnh, đọc câu mới biết
    # đúng sai. F1 (anchor nửa cụm) và F3 (đích còn redirect) sửa bằng cách NỚI
    # anchor / đổi href — gỡ link là mất luôn cái đang đúng. Chạy lại
    # optimize_content.py là xong cả hai.
    advisory = {"D2", "E2", "E3", "F1", "F3"}
    targets = {(f["anchor"].strip(), f["url"]) for f in findings
               if not set(f["cases"]) <= advisory}
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
    ap.add_argument("--offline", action="store_true",
                    help="Bỏ kiểm HTTP/redirect của href (không có mạng). "
                         "Tương đương biến môi trường MWG_LINK_OFFLINE=1.")
    a = ap.parse_args()

    cfg = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    r = check(a.workspace, cfg, offline=a.offline)

    if not a.quiet:
        print(f"\n{r['workspace']}  (ngành: {r['nganh_hang']}, {r['tong_link']} link) "
              f"-> {r['so_findings']} nghi ngờ ({r['so_fail']} FAIL)")
        if not r["http_checked"]:
            print("  [WARN] chưa kiểm HTTP/redirect của href (offline).")
        for f in r["findings"]:
            print(f"  [{f['severity']}][{'+'.join(f['cases'])}] {f['anchor'][:32]:34s} "
                  f"-> {path_of(f['url'])[:50]}")
            print(f"        {f['why']}")
    if a.json:
        Path(a.json).write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")

    if a.fix and r["findings"]:
        removed = strip_flagged_links(Path(a.workspace), r["findings"])
        print(f"  [FIX] gỡ {removed}/{r['so_findings']} link (giữ nguyên chữ)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
