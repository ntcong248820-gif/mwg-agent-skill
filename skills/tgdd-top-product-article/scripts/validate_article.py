#!/usr/bin/env python3
"""Validate bài "Top N sản phẩm" TGDĐ trước khi giao/publish.

Bắt đúng các lỗi đã gặp thật khi làm bài Top 10 laptop gaming:
  - caption lặp 2 lần (có cả <img title> VÀ <p class="titleOfImages">)
  - ảnh đặt sai vị trí (ngay sau [product ID] thay vì sau đoạn văn mở đầu)
  - listid lệch giữa Product_Promotion đầu bài / [sosanh] / danh sách SP thật
  - Product_Promotion cuối bài trùng SP trong bài (phải là SP giảm sốc khác)
  - thiếu shortcode [sosanh] hoặc đặt sai chỗ
  - ảnh chưa upload CMS -> lên bài không hiển thị
  - source-content.html và final-content.html lệch nhau

Usage:
  python3 validate_article.py --workspace path/to/content-workspace/{slug}
  python3 validate_article.py --file path/to/final-content.html
  python3 validate_article.py --workspace DIR --check-cdn   # HEAD request từng ảnh
"""
import argparse
import os
import re
import sys
import urllib.error
import urllib.request

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Cần BeautifulSoup: python3 -m pip install beautifulsoup4")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
FAIL, WARN, OK = "FAIL", "WARN", "OK"


class Report:
    def __init__(self):
        self.rows = []

    def add(self, level, check, msg):
        self.rows.append((level, check, msg))

    def ok(self, check, msg=""):
        self.add(OK, check, msg)

    def warn(self, check, msg):
        self.add(WARN, check, msg)

    def fail(self, check, msg):
        self.add(FAIL, check, msg)

    def render(self):
        icons = {OK: "OK  ", WARN: "WARN", FAIL: "FAIL"}
        for lvl, check, msg in self.rows:
            print(f"[{icons[lvl]}] {check}" + (f": {msg}" if msg else ""))
        n_fail = sum(1 for r in self.rows if r[0] == FAIL)
        n_warn = sum(1 for r in self.rows if r[0] == WARN)
        print(f"\n{len(self.rows)} check | FAIL {n_fail} | WARN {n_warn}")
        if n_fail:
            print("\nCHUA DAT - sua het FAIL truoc khi giao bai.")
        elif n_warn:
            print("\nDat, nhung xem lai cac WARN.")
        else:
            print("\nDat toan bo check.")
        return 1 if n_fail else 0


def ids_in(s):
    return re.findall(r"\d+", s or "")


def shortcodes(html, name):
    """Trả list (full_text, attrs_dict) cho mỗi shortcode tên `name`."""
    out = []
    for m in re.finditer(rf"\[{name}\b([^\]]*)\]", html, re.I):
        body = m.group(1)
        attrs = {k.lower(): v for k, v in re.findall(r'(\w+)\s*=\s*"([^"]*)"', body)}
        out.append((m.group(0), attrs, m.start()))
    return out


def product_blocks(soup):
    """Mỗi H4 có [product ID] -> list các sibling tag tới H3/H4 kế tiếp."""
    blocks = []
    for h4 in soup.find_all("h4"):
        grp, node = [], h4.find_next_sibling()
        while node is not None and node.name not in ("h3", "h4"):
            grp.append(node)
            node = node.find_next_sibling()
        if any(t.name == "p" and "[product ID=" in t.get_text() for t in grp):
            blocks.append((h4, grp))
    return blocks


def check_shortcodes(html, rep):
    prom = shortcodes(html, "Product_Promotion")
    sosanh = shortcodes(html, "sosanh")
    prod_ids = re.findall(r'\[product ID="(\d+)"', html)

    if not prod_ids:
        rep.fail("product-widget", "khong tim thay [product ID=...] nao")
        return prod_ids

    # --- Product_Promotion dau bai ---
    if len(prom) < 2:
        rep.fail("promo-count",
                 f"can 2 [Product_Promotion] (dau bai = SP trong bai, cuoi bai = SP GIAM SOC khac), thay {len(prom)}")
    else:
        rep.ok("promo-count", "2 shortcode Product_Promotion")

    if prom:
        top, top_attrs, top_pos = prom[0]
        body_start = min([m.start() for m in re.finditer(r"<h2|<h3", html)] or [len(html)])
        if top_pos > body_start:
            rep.fail("promo-top-position", "Product_Promotion dau bai phai nam TRUOC <h2> mo dau")
        else:
            rep.ok("promo-top-position")
        if "ĐỪNG BỎ LỠ" not in top_attrs.get("title", ""):
            rep.warn("promo-top-title", f'title nen bat dau "ĐỪNG BỎ LỠ ...": {top_attrs.get("title","")!r}')
        else:
            rep.ok("promo-top-title")
        top_ids = ids_in(top_attrs.get("listid", ""))
        if top_ids != prod_ids:
            rep.fail("promo-top-listid",
                     f"listid dau bai phai KHOP dung thu tu SP trong bai.\n"
                     f"         listid: {','.join(top_ids)}\n"
                     f"         SP bai: {','.join(prod_ids)}")
        else:
            rep.ok("promo-top-listid", f"{len(top_ids)} ID khop thu tu SP trong bai")

    # --- Product_Promotion cuoi bai ---
    if len(prom) >= 2:
        _, bot_attrs, bot_pos = prom[-1]
        bot_ids = ids_in(bot_attrs.get("listid", ""))
        if bot_pos < (html.rfind("</h3>") if "</h3>" in html else 0):
            rep.warn("promo-bottom-position", "Product_Promotion GIAM SOC nen nam cuoi bai")
        else:
            rep.ok("promo-bottom-position")
        overlap = sorted(set(bot_ids) & set(prod_ids))
        if not bot_ids:
            rep.fail("promo-bottom-listid", "listid cuoi bai rong")
        elif overlap:
            rep.fail("promo-bottom-listid",
                     f"listid cuoi bai phai la SP GIAM SOC KHAC, khong trung SP trong bai. Trung: {','.join(overlap)}")
        else:
            rep.ok("promo-bottom-listid", f"{len(bot_ids)} SP giam soc, khong trung SP trong bai")
        if "ĐỪNG BỎ LỠ" not in bot_attrs.get("title", ""):
            rep.warn("promo-bottom-title", f'title nen dang "ĐỪNG BỎ LỠ ... GIẢM SỐC:": {bot_attrs.get("title","")!r}')
        else:
            rep.ok("promo-bottom-title")

    # --- sosanh ---
    if not sosanh:
        rep.fail("sosanh-present", "thieu shortcode [sosanh ...] (bang so sanh thong so)")
    else:
        _, s_attrs, s_pos = sosanh[0]
        if len(sosanh) > 1:
            rep.warn("sosanh-present", f"co {len(sosanh)} shortcode [sosanh], thuong chi can 1")
        else:
            rep.ok("sosanh-present")
        s_ids = ids_in(s_attrs.get("products", ""))
        if s_ids != prod_ids:
            rep.fail("sosanh-products",
                     f"products phai KHOP dung thu tu SP trong bai.\n"
                     f"         products: {','.join(s_ids)}\n"
                     f"         SP bai  : {','.join(prod_ids)}")
        else:
            rep.ok("sosanh-products", f"{len(s_ids)} ID khop")
        props = ids_in(s_attrs.get("properties", ""))
        if not props:
            rep.fail("sosanh-properties", "properties rong -> bang khong hien cot thong so")
        elif len(props) > 7:
            rep.fail("sosanh-properties", f"{len(props)} thuoc tinh, toi da 7 (tu thu 8 khong hien)")
        else:
            rep.ok("sosanh-properties", f"{len(props)} thuoc tinh")
        if not s_attrs.get("categoryid", "").strip():
            rep.fail("sosanh-categoryid", "categoryid rong -> KHONG hien ca bang")
        else:
            rep.ok("sosanh-categoryid", s_attrs["categoryid"])
        # vi tri: ngay sau bang tong hop (section 2), truoc H3 muc 3
        tbl_end = html.rfind("</table>", 0, s_pos)
        between = re.sub(r"\s+", "", html[tbl_end + 8:s_pos]) if tbl_end != -1 else "X"
        if tbl_end == -1 or between not in ("", "<p>", "<p></p>"):
            rep.warn("sosanh-position", "[sosanh] nen nam ngay duoi bang tong hop muc 2")
        else:
            rep.ok("sosanh-position", "ngay duoi bang tong hop")

    return prod_ids


def check_images(soup, html, prod_ids, rep):
    imgs = soup.find_all("img")
    if len(imgs) != len(prod_ids):
        rep.fail("image-count", f"{len(imgs)} anh / {len(prod_ids)} san pham - moi SP can dung 1 anh")
    else:
        rep.ok("image-count", f"{len(imgs)} anh = {len(prod_ids)} SP")

    # caption lap: CMS render `title` thanh caption -> them titleOfImages = lap 2 lan
    dup = soup.select("p.titleOfImages")
    if dup:
        rep.fail("caption-duplicate",
                 f'{len(dup)} <p class="titleOfImages"> - CMS da render title cua <img> thanh caption, '
                 f"the nay lam caption hien 2 LAN. Bo het, chi giu <img title alt>.")
    else:
        rep.ok("caption-duplicate", "khong co caption lap")

    bad_attr, bad_w = [], []
    for im in imgs:
        src = (im.get("src") or "").rsplit("/", 1)[-1]
        alt, title = (im.get("alt") or "").strip(), (im.get("title") or "").strip()
        if not alt or not title:
            bad_attr.append(f"{src} (alt={bool(alt)} title={bool(title)})")
        if (im.get("width") or "") != "800":
            bad_w.append(f"{src} (width={im.get('width') or 'thieu'})")
    if bad_attr:
        rep.fail("image-alt-title", "thieu alt/title: " + "; ".join(bad_attr))
    else:
        rep.ok("image-alt-title", "du alt + title")
    if bad_w:
        rep.warn("image-width", "width != 800: " + "; ".join(bad_w))
    else:
        rep.ok("image-width", 'tat ca width="800"')

    # vi tri anh trong tung block SP
    misplaced, missing = [], []
    for h4, grp in product_blocks(soup):
        name = h4.get_text(strip=True)[:45]
        idx_widget = idx_info_close = idx_img = None
        first_content_p = None
        for i, t in enumerate(grp):
            txt = t.get_text(strip=True) if t.name else ""
            if t.name == "p" and "[product ID=" in txt and idx_widget is None:
                idx_widget = i
            if t.name == "p" and txt == "[/info]" and idx_info_close is None:
                idx_info_close = i
            if (t.name == "p" and idx_info_close is not None and i > idx_info_close
                    and first_content_p is None and not t.find("img") and txt):
                first_content_p = i
            if t.name == "p" and t.find("img") and idx_img is None:
                idx_img = i
        if idx_img is None:
            missing.append(name)
            continue
        if idx_widget is not None and idx_img == idx_widget + 1 and (
                idx_info_close is None or idx_img < idx_info_close):
            misplaced.append(f"{name}: anh ngay sau [product ID], phai nam SAU khoi [info] + doan van mo dau")
        elif idx_info_close is not None and idx_img < idx_info_close:
            misplaced.append(f"{name}: anh nam TRONG/TRUOC khoi [info]")
        elif first_content_p is not None and idx_img < first_content_p:
            misplaced.append(f"{name}: anh dat truoc doan van mo dau")

    if missing:
        rep.fail("image-per-product", "SP khong co anh: " + "; ".join(missing))
    elif misplaced:
        rep.fail("image-position", "\n         ".join(misplaced))
    else:
        rep.ok("image-position", "anh nam sau [info] + doan van mo dau o moi SP")


def check_formatting(soup, rep):
    bad_h2 = [h.get_text(strip=True)[:40] for h in soup.find_all("h2") if h.find(["strong", "b"])]
    if bad_h2:
        rep.fail("heading-h2", "H2 KHONG duoc bold: " + "; ".join(bad_h2))
    else:
        rep.ok("heading-h2", "H2 khong bold")

    bad_h = []
    for lvl in ("h3", "h4", "h5", "h6"):
        for h in soup.find_all(lvl):
            if not h.find("strong"):
                bad_h.append(f"{lvl}:{h.get_text(strip=True)[:35]}")
    if bad_h:
        rep.fail("heading-h3plus", "thieu <strong>: " + "; ".join(bad_h))
    else:
        rep.ok("heading-h3plus", "H3-H6 co <strong>")

    bad_a = []
    for a in soup.find_all("a", href=True):
        rel = " ".join(a.get("rel") or []) if isinstance(a.get("rel"), list) else (a.get("rel") or "")
        if a.get("target") != "_blank" or "noopener" not in rel:
            bad_a.append(a.get_text(strip=True)[:30] or a["href"][:40])
    if bad_a:
        rep.fail("link-attrs", 'thieu target="_blank" / rel noopener: ' + "; ".join(bad_a[:6]))
    else:
        rep.ok("link-attrs", 'tat ca <a> co target="_blank" rel noopener')


def check_cdn(soup, rep, workspace=None):
    """HEAD request tung anh -> anh nao chua upload CMS thi len bai khong hien."""
    srcs = [im["src"] for im in soup.find_all("img") if im.get("src", "").startswith("http")]
    missing = []
    for src in srcs:
        try:
            req = urllib.request.Request(src, method="HEAD", headers={"User-Agent": UA})
            urllib.request.urlopen(req, timeout=20)
        except Exception:
            missing.append(src)
    if missing:
        lines = []
        for src in missing:
            fn = src.rsplit("/", 1)[-1]
            local = ""
            if workspace:
                p = os.path.join(workspace, "images-processed", fn)
                local = f"  (file san: {p})" if os.path.exists(p) else "  (KHONG thay file local!)"
            lines.append(f"{fn}{local}")
        rep.fail("image-on-cms",
                 f"{len(missing)} anh CHUA co tren CDN -> len bai se khong hien. Upload dung ten file:\n         "
                 + "\n         ".join(lines))
    else:
        rep.ok("image-on-cms", f"{len(srcs)} anh da co tren CDN")


def check_parity(ws, rep):
    src_p = os.path.join(ws, "source", "source-content.html")
    fin_p = os.path.join(ws, "source", "final-content.html")
    if not (os.path.exists(src_p) and os.path.exists(fin_p)):
        return
    src = open(src_p, encoding="utf-8").read()
    fin = open(fin_p, encoding="utf-8").read()
    s_ids = re.findall(r'\[product ID="(\d+)"', src)
    f_ids = re.findall(r'\[product ID="(\d+)"', fin)
    s_img = sorted(re.findall(r'src="([^"]+)"', src))
    f_img = sorted(re.findall(r'src="([^"]+)"', fin))
    if s_ids != f_ids:
        rep.fail("source-final-parity",
                 "SP trong source-content.html lech final-content.html.\n"
                 "         optimize_content.py build final TU source -> sua o final se bi ghi de lan sau.")
    elif s_img != f_img:
        rep.fail("source-final-parity", "danh sach anh lech giua source-content.html va final-content.html")
    else:
        rep.ok("source-final-parity", "source va final dong bo (SP + anh)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--workspace", help="content-workspace/{slug} (validate final-content.html)")
    g.add_argument("--file", help="File HTML cu the")
    ap.add_argument("--check-cdn", action="store_true", help="HEAD request tung anh -> bao anh chua upload CMS")
    a = ap.parse_args()

    ws = a.workspace
    path = a.file or os.path.join(ws, "source", "final-content.html")
    if not os.path.exists(path):
        sys.exit(f"Khong thay file: {path}")

    html = open(path, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    print(f"Validate: {path}\n")

    rep = Report()
    prod_ids = check_shortcodes(html, rep)
    if prod_ids:
        check_images(soup, html, prod_ids, rep)
    check_formatting(soup, rep)
    if ws:
        check_parity(ws, rep)
    if a.check_cdn:
        check_cdn(soup, rep, ws)

    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
