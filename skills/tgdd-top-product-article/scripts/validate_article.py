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
  python3 validate_article.py --workspace mwg-content-editor/content-workspaces/{slug}
  python3 validate_article.py --file path/to/final-content.html
  python3 validate_article.py --workspace DIR --check-cdn   # HEAD request từng ảnh
"""
import argparse
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

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
        if not bot_ids and bot_attrs.get("categoryid") and bot_attrs.get("sort"):
            rep.ok("promo-bottom-listid",
                   f'listing theo nganh hang categoryid={bot_attrs["categoryid"]} sort={bot_attrs["sort"]}')
        elif not bot_ids:
            rep.fail("promo-bottom-listid", "listid cuoi bai rong va khong co categoryid + sort")
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


EXPLAINER_SEGS = ("hoi-dap", "tin-tuc", "kinh-nghiem-hay", "game-app")
SELF_BRAND_RE = re.compile(r"^\s*(th[eê]['´̂]?\s*gi[oơ]['´̛]?i\s*di\s*[dđ][oô][.̣]?ng|tgd[dđ])\s*$", re.I)


def url_path(href):
    return re.sub(r"^https?://[^/]+", "", (href or "").split("?")[0].split("#")[0]).strip("/")


def is_pdp_href(href):
    """PDP = trang sản phẩm: path đúng 2 segment, segment đầu là ngành hàng."""
    segs = [s for s in url_path(href).split("/") if s]
    return len(segs) == 2 and segs[0] not in EXPLAINER_SEGS


def check_product_sections(soup, rep):
    """Mỗi khối SP phải tự dẫn về PDP của chính nó, và nhãn thông số phải in đậm."""
    no_pdp, partial_anchor, weak_label = [], [], []
    for h4, grp in product_blocks(soup):
        name = h4.get_text(strip=True)
        pdp = None
        for node in grp:
            for a in (node.find_all("a", href=True) if node.name else []):
                if is_pdp_href(a.get("href")):
                    pdp = a
                    break
            if pdp:
                break
        if pdp is None:
            no_pdp.append(name[:45])
        else:
            # anchor phải bọc TOÀN BỘ tên SP, không bọc một phần
            # Anchor được phép bỏ mã SP/cấu hình ở đuôi, nhưng phải bọc phần lớn
            # tên máy. Dưới 60% số từ là kiểu "MSI Modern" trong "MSI Modern 14 F1MG".
            core = re.sub(r"\s*[\(\-–].*$", "", name).strip().lower().split()
            anchor = pdp.get_text(strip=True)
            kept = sum(1 for w in core if w in anchor.lower())
            if core and kept / len(core) < 0.6:
                partial_anchor.append(f"{name[:35]}: anchor {anchor[:40]!r}")

        for node in grp:
            if not node.name:
                continue
            for li in node.find_all("li"):
                txt = li.get_text(" ", strip=True)
                if ":" not in txt:
                    continue
                label = txt.split(":", 1)[0].strip()
                bold = " ".join(b.get_text(" ", strip=True).rstrip(":").strip()
                                for b in li.find_all(["strong", "b"]))
                if label and label not in bold:
                    weak_label.append(f"{name[:30]} / {label[:24]}")

    if no_pdp:
        rep.fail("product-pdp-link",
                 "khoi SP thieu link PDP cua chinh no (phai boc TEN SP o cau dau): "
                 + "; ".join(no_pdp))
    else:
        rep.ok("product-pdp-link", "moi khoi SP co link PDP cua chinh no")

    if partial_anchor:
        rep.warn("product-pdp-anchor", "anchor PDP khong boc du ten SP: " + "; ".join(partial_anchor[:6]))
    else:
        rep.ok("product-pdp-anchor", "anchor PDP boc du ten SP")

    if weak_label:
        rep.fail("spec-label-bold",
                 "nhan thong so trong [info] phai in dam (<strong>CPU:</strong> ...): "
                 + "; ".join(weak_label[:8]))
    else:
        rep.ok("spec-label-bold", "nhan thong so da in dam")


def check_justify(soup, rep):
    """Đoạn văn thân bài phải canh đều; optimize_content.py tự gán, thiếu = chưa optimize."""
    missing = 0
    for p in soup.find_all("p"):
        if p.find_parent(["table", "li"]) or p.find("img"):
            continue
        txt = p.get_text(strip=True)
        if not txt or txt.startswith("["):
            continue
        if "text-align" not in (p.get("style") or ""):
            missing += 1
    if missing:
        rep.warn("body-justify",
                 f'{missing} doan van chua co style="text-align: justify;" '
                 f"- chay lai optimize_content.py")
    else:
        rep.ok("body-justify", "doan van than bai da canh deu")


def check_table_cell_linebreak(soup, rep):
    """Ô bảng ngắt dòng bằng <br/> hoặc chữ "- " dính một <p> → live hiện một dòng.

    Site TGDĐ bỏ <br/> trong <td> lúc render (CMS vẫn lưu), nên chỉ <p> riêng từng dòng mới sống.
    """
    br_cells = flat_cells = 0
    for td in soup.find_all(["td", "th"]):
        if td.find("br"):
            br_cells += 1
        elif not td.find("p") and not td.find("li") and re.search(r"\n\s*[-•]\s+\S", td.get_text()):
            flat_cells += 1
    if br_cells or flat_cells:
        rep.fail("table-cell-linebreak",
                 f"{br_cells} o dung <br/> (site live bo <br/>), {flat_cells} o gach dau dong khong co <p> "
                 f"rieng -> gach dau dong dinh thanh 1 dong. Moi dong phai la <p> rieng")
    else:
        rep.ok("table-cell-linebreak", "o bang ngat dong bang <p>")


def check_table_header(soup, rep):
    bad = sum(1 for th in soup.find_all("th") if "font-size" not in (th.get("style") or ""))
    if bad:
        rep.warn("table-header-font",
                 f"{bad} <th> chua set font-size (ke thua 14px cua table -> chu header nho "
                 f"bang chu o) - chay lai optimize_content.py")
    else:
        rep.ok("table-header-font", "<th> co font-size rieng")


# Danh từ đầu cụm đứng trước tên hãng/công nghệ. Bản rút gọn của
# `content-html-optimizer/scripts/link_anchor.py` — validator phải chạy được độc
# lập với skill kia (khác package), nên chép chứ không import.
HEAD_NOUNS = (
    "màn hình máy tính", "máy tính để bàn", "máy tính bảng", "card màn hình",
    "card đồ họa", "card đồ hoạ", "màn hình", "máy tính", "máy in", "laptop",
    "thương hiệu", "tấm nền", "ổ cứng", "bàn phím", "cảm biến", "chuột",
    "hãng", "card", "chip", "cpu", "gpu", "ram", "pin",
)
_HEAD_NOUNS_BY_LEN = tuple(sorted(HEAD_NOUNS, key=len, reverse=True))
SINGLE_LATIN_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+\-]*$")


def text_before(tag):
    """Chữ đứng ngay trước tag, trong cùng một text node (giữ khoảng trắng cuối)."""
    prev = tag.previous_sibling
    if prev is None or getattr(prev, "name", None) is not None:
        return ""
    return str(prev)[-80:]


def partial_phrase_anchor(anchor, before):
    """Trả cụm đầy đủ ("laptop HP") khi anchor cắt nửa cụm, None nếu anchor ổn."""
    anchor = (anchor or "").strip()
    if not anchor or " " in anchor or anchor.lower() in {n.lower() for n in HEAD_NOUNS}:
        return None
    if not SINGLE_LATIN_TOKEN.fullmatch(anchor):
        return None
    if not re.search(r"[ \t ]$", before or ""):
        return None
    stem = before[:-1]
    low = stem.lower()
    for noun in _HEAD_NOUNS_BY_LEN:
        if not low.endswith(noun):
            continue
        start = len(stem) - len(noun)
        if start > 0 and re.match(r"[\w]", stem[start - 1], re.UNICODE):
            continue
        return f"{stem[start:].strip()} {anchor}"
    return None


def check_anchor_phrase(soup, rep):
    """Anchor phải trọn nghĩa: "laptop HP", không phải "laptop [HP]".

    Reviewer MWG 29/09/2026 bắt mẫu này ở bài đã air. `optimize_content.py` tự
    nới khi chèn, nên còn sót thường là anchor viết tay trong source.
    """
    bad = []
    for a in soup.find_all("a", href=True):
        full = partial_phrase_anchor(a.get_text(strip=True), text_before(a))
        if full:
            bad.append(f"'{a.get_text(strip=True)}' -> phai boc ca '{full}'")
    if bad:
        rep.warn("link-anchor-phrase",
                 "anchor cat nua cum (link mot chu le giua cau): " + "; ".join(bad[:6])
                 + "\n         Sua o source-content.html roi chay lai optimize_content.py.")
    else:
        rep.ok("link-anchor-phrase", "anchor khong cat nua cum")


def check_link_http(soup, rep, offline=False):
    """Mọi href nội bộ phải trả 200 và KHÔNG redirect.

    Chết (404/410/5xx) và còn redirect đều = **FAIL** (owner chốt 29/09/2026).
    Trước đó redirect chỉ là WARN vì "cách sửa là chạy lại optimizer" — nhưng
    WARN không chặn air, nên bài vẫn ra ngoài với href đẩy người đọc thêm một
    chặng, có ca rơi hẳn về trang rộng hơn. Cách sửa không đổi (chạy lại
    `optimize_content.py`, nó tự đổi sang URL cuối / tìm URL thay thế); chỉ có
    mức nghiêm trọng đổi.

    Không đo được (mất mạng, bị chặn) thì WARN — không kết luận link hỏng.
    `--offline` / `MWG_LINK_OFFLINE=1` bỏ qua phần HTTP và nói rõ là **chưa kiểm**.
    """
    if offline or os.environ.get("MWG_LINK_OFFLINE", "").strip() not in ("", "0"):
        rep.warn("link-http", "bo qua kiem HTTP/redirect (offline)")
        return
    hrefs = []
    for a in soup.find_all("a", href=True):
        h = a["href"].strip()
        if any(d in h for d in ("thegioididong.com", "dienmayxanh.com", "topzone.vn")):
            hrefs.append(h)
    if not hrefs:
        rep.ok("link-http", "khong co href noi bo")
        return

    dead, redirected, unknown = [], [], 0
    with ThreadPoolExecutor(max_workers=6) as pool:
        for href, (status, final_url, err) in zip(hrefs, pool.map(head_final, hrefs)):
            if err or status is None:
                unknown += 1
            elif status in (404, 410) or status >= 500:
                dead.append(f"{url_path(href)} (HTTP {status})")
            elif url_path(final_url) != url_path(href):
                redirected.append(f"{url_path(href)} -> {url_path(final_url)}")

    if dead or redirected:
        msg = []
        if dead:
            msg.append("link chet: " + "; ".join(sorted(set(dead))[:6]))
        if redirected:
            msg.append("href con redirect, phai dung URL cuoi: "
                       + "; ".join(sorted(set(redirected))[:6]))
        rep.fail("link-http", "; ".join(msg)
                 + "\n         Chay lai optimize_content.py: no doi sang URL cuoi, "
                   "tim URL thay the cho link chet/lech dich, khong co thi go link giu chu.")
    elif unknown:
        rep.warn("link-http", f"{unknown} href khong do duoc (mang/chan bot), kiem lai tay")
    else:
        rep.ok("link-http", f"{len(set(hrefs))} href tra 200, khong redirect")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def _one_hop(url, method, timeout):
    """Trả (status, location, loi) cho ĐÚNG một request, không đi theo redirect."""
    try:
        req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
        with _OPENER.open(req, timeout=timeout) as r:
            return getattr(r, "status", r.getcode()), None, None
    except urllib.error.HTTPError as e:
        return e.code, (e.headers.get("Location") if e.headers else None), None
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"


def head_final(url, timeout=12, max_hops=5):
    """Trả (status_cuoi, url_cuoi, loi). Tu di theo redirect de biet CO redirect."""
    current, status, err = url, None, None
    for _ in range(max_hops):
        status, loc, err = _one_hop(current, "HEAD", timeout)
        if status in (403, 405, 501):  # vai origin chan HEAD nhung cho GET
            status, loc, err = _one_hop(current, "GET", timeout)
        if err or not (status and 300 <= status < 400 and loc):
            break
        current = urllib.parse.urljoin(current, loc)
    return status, current, err


def check_link_context(soup, rep):
    """Cảnh báo mẫu link chắc chắn nghi sai ngữ cảnh. KHÔNG tự xóa — người review."""
    in_spec, self_brand = [], []
    for a in soup.find_all("a", href=True):
        anchor = a.get_text(strip=True)
        if a.find_parent("li") and not is_pdp_href(a["href"]) and len(anchor.split()) <= 4:
            in_spec.append(anchor[:30])
        if not url_path(a["href"]) or SELF_BRAND_RE.match(anchor):
            self_brand.append(anchor[:30] or a["href"][:40])
    msgs = []
    if in_spec:
        msgs.append("anchor trong <li> (dong thong so khong phai cho di link): " + "; ".join(in_spec[:5]))
    if self_brand:
        msgs.append("link tu xung TGDD / trang chu: " + "; ".join(self_brand[:5]))
    if msgs:
        rep.warn("link-context", " | ".join(msgs)
                 + "\n         Doc lai tung link bang check_internal_links.py truoc khi air.")
    else:
        rep.ok("link-context", "khong thay mau link nghi sai ngu canh")


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
    g.add_argument("--workspace", help="content-workspaces/{slug} (validate final-content.html)")
    g.add_argument("--file", help="File HTML cu the")
    ap.add_argument("--check-cdn", action="store_true", help="HEAD request tung anh -> bao anh chua upload CMS")
    ap.add_argument("--offline", action="store_true",
                    help="Bo kiem HTTP/redirect cua href (khong co mang). "
                         "Tuong duong bien moi truong MWG_LINK_OFFLINE=1.")
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
        check_product_sections(soup, rep)
    check_formatting(soup, rep)
    check_justify(soup, rep)
    check_table_header(soup, rep)
    check_table_cell_linebreak(soup, rep)
    check_link_context(soup, rep)
    check_anchor_phrase(soup, rep)
    check_link_http(soup, rep, offline=a.offline)
    if ws:
        check_parity(ws, rep)
    if a.check_cdn:
        check_cdn(soup, rep, ws)

    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
