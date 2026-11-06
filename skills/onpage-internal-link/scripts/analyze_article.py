#!/usr/bin/env python3
"""
analyze_article.py — Phân tích 1 bài tin live cho WF đi link (port node 6 của n8n "Onpage Ver 2").

Script chỉ làm phần MÁY làm được: bóc thân bài, dò link có sẵn, khớp keyword, lọc đoạn mốc,
phân nhánh. Phần cần đọc hiểu (lọc câu tách cụm, sửa anchor, chọn vị trí không cắt mạch,
viết câu chèn) do Claude làm dựa trên JSON xuất ra.

Usage:
  # 1 bài, 1 hoặc nhiều cặp keyword|URL đích
  python3 -I scripts/analyze_article.py analyze --url <URL bài tin> \
      --pair "iphone 16|https://www.thegioididong.com/dtdd/iphone-16" [--pair ...]

  # Đọc các dòng Status=Run của tab plan "onpage" rồi phân tích từng dòng
  python3 -I scripts/analyze_article.py plan [--spreadsheet-id <ID>] [--status Run]

  # Debug từ file HTML đã lưu
  python3 -I scripts/analyze_article.py analyze --url <URL> --html-file page.html --pair "kw|url"

Output: JSON ra stdout. Không ghi sheet.
Chỉ dùng thư viện chuẩn + curl + gws CLI.
"""

from __future__ import annotations

import argparse
import html as htmlmod
import json
import os
import re
import subprocess
import sys

PLAN_SHEET_ID = os.environ.get("SHEET_PLAN_ONPAGE_ID", "")  # đặt biến môi trường SHEET_PLAN_ONPAGE_ID hoặc truyền --spreadsheet-id
PLAN_TAB = "onpage"
CURL_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

VI = "À-ỹ"
W = r"[\w" + VI + "]"

# ── Text helpers ──
# Bóc thẻ mà KHÔNG gãy ở dấu ">" nằm trong giá trị thuộc tính (title="Vào AppStore > Đăng ký").
TAG_RE = re.compile(r"""<[!/a-zA-Z][^"'>]*(?:(?:"[^"]*"|'[^']*')[^"'>]*)*>""")


def decode(s: str) -> str:
    return htmlmod.unescape(s or "")


def html_to_text(h: str) -> str:
    s = h or ""
    s = re.sub(r"<script[\s\S]*?</script>", " ", s, flags=re.I)
    s = re.sub(r"<style[\s\S]*?</style>", " ", s, flags=re.I)
    s = re.sub(r"</(p|div|li|br|tr|h[1-6])\s*>", "\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = decode(TAG_RE.sub(" ", s))
    s = s.replace("\r", "\n")
    s = re.sub(r"[ \t ]+", " ", s)
    s = re.sub(r"[ \t]*\n[ \t]*", "\n", s)
    s = re.sub(r"\n{2,}", "\n", s)
    s = re.sub(r"\s+([.,;:!?%…)\]])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s.strip()


def inline(t: str) -> str:
    return " ".join(str(t or "").split())


def standalone_re(kw: str) -> re.Pattern:
    """Keyword đứng độc lập: không dính từ ASCII trọn vẹn phía sau (Pro, Max, 256GB...)."""
    return re.compile(r"(?<!" + W + ")" + re.escape(kw)
                      + r"(?!\s+[a-zA-Z0-9]+(?![a-zA-Z0-9" + VI + r"]))(?!" + W + ")", re.I)


NOT_VARIANT_AFTER = r"(?:xuyên|được|bị|thấy|gặp|dùng|sử\s+dụng|xảy|phải|hay)"
VARIANT_SUFFIX = (r"(?:bản\s+)?(?:tiêu\s+chuẩn(?!" + W + r")|thường(?!" + W + r")(?!\s+"
                  + NOT_VARIANT_AFTER + r"(?!" + W + r")))")


def anchorable_re(kw: str) -> re.Pattern:
    """Khắt khe hơn standalone_re: chặn thêm hậu tố biến thể có dấu ("iPhone 16 thường")."""
    return re.compile(r"(?<!" + W + ")" + re.escape(kw)
                      + r"(?!\s+[a-zA-Z0-9]+(?![a-zA-Z0-9" + VI + r"]))"
                      + r"(?!\s+" + VARIANT_SUFFIX + ")"
                      + r"(?!" + W + ")", re.I)


def has_longer_variant(sentence: str, kw: str) -> bool:
    if not kw:
        return False
    return bool(re.search(r"(?<!" + W + ")" + re.escape(kw) + r"\s+[a-zA-Z0-9]+(?![a-zA-Z0-9" + VI + "])",
                          sentence, re.I))


def normalize_url(u: str) -> str:
    return re.sub(r"/+$", "", str(u or "").lower()).strip()


def host_of(u: str) -> str:
    m = re.match(r"^https?://([^/?#]+)", str(u or "").lower())
    return re.sub(r"^www\.", "", m.group(1)) if m else ""


def url_key(u: str) -> str:
    """Cùng host + cùng TẬP token path => coi là 1 URL (bắt được bản redirect 301)."""
    bare = re.sub(r"[?#].*$", "", re.sub(r"^https?://", "", normalize_url(u)))
    host, _, path = bare.partition("/")
    uniq = []
    for t in re.split(r"[/\-_]+", path):
        if t and t not in uniq:
            uniq.append(t)
    return host + "|" + "-".join(sorted(uniq))


# ── Balanced <div> helpers ──
DIV_TAG = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)


def _div_end(src: str, start: int) -> int:
    depth = 1
    for m in DIV_TAG.finditer(src, start):
        if m.group(0).lower().startswith("</div"):
            depth -= 1
            if depth == 0:
                return m.start()
        else:
            depth += 1
    return -1


def slice_balanced_div(src: str, open_re: re.Pattern) -> str:
    m = open_re.search(src)
    if not m:
        return ""
    end = _div_end(src, m.end())
    return src[m.end():end] if end != -1 else ""


def class_div_re(cls: str) -> re.Pattern:
    return re.compile(r"""<div[^>]*class=["'][^"']*\b""" + cls + r"""\b[^"']*["'][^>]*>""", re.I)


def strip_balanced_blocks(src: str, classes: list[str]) -> str:
    out = src
    for cls in classes:
        rx = class_div_re(cls)
        while True:
            m = rx.search(out)
            if not m:
                break
            end = _div_end(out, m.end())
            if end == -1:
                break
            close = DIV_TAG.match(out, end)
            out = out[:m.start()] + out[close.end():]
    return out


def collect_infoboxes(src: str) -> list[str]:
    res = []
    for m in class_div_re("infobox").finditer(src):
        end = _div_end(src, m.end())
        if end != -1:
            res.append(src[m.end():end])
    return res


# ── Bóc thân bài ──
CONTAINERS = ["detail-content", "warpper-content", "article-content",
              "contentnews", "divContent", "contentpost", "content-article"]
CONTAINERS_DMX = ["contentnews", "divContent"] + CONTAINERS
TAIL = ["boxRatingNew", "boxreviewcontentv2", "reviewcontentV2", "kwLst",
        "askrelate", "cookie-found", "likeshare", "articleview", "rowcount"]
JUNK_BLOCKS = ["boxpromote", "banner-detail", "set_table", "box-relative", "rowuser", "promo",
               "listproduct", "shorcodeGA", "shortcodeGA"]


def cut_head(src: str) -> str:
    m = re.search(r"<h1\b[^>]*>", src, re.I)
    if m:
        return src[m.start():]
    return re.sub(r"""<ul[^>]*class=["'][^"']*\bbreadcrumb\b[\s\S]*?</ul>""", "", src, count=1, flags=re.I)


def cut_tail(src: str) -> str:
    cut = -1
    for t in TAIL:
        m = re.search(r"""<(?:div|ul|section)[^>]*class=["'][^"']*\b""" + t + r"\b", src, re.I)
        if m and (cut == -1 or m.start() < cut):
            cut = m.start()
    return src[:cut] if cut > 200 else src


def strip_see_also(src: str) -> str:
    """Xoá TẠI CHỖ hộp infobox mở đầu bằng "Xem thêm:" (có thể nằm giữa bài)."""
    out = src
    rx = class_div_re("infobox")
    for _ in range(20):
        target = None
        for m in rx.finditer(out):
            head = inline(decode(TAG_RE.sub(" ", out[m.start():m.start() + 300])))
            if re.match(r"^Xem\s*th[êe]m\s*:", head, re.I):
                target = m
                break
        if not target:
            return out
        end = _div_end(out, target.end())
        if end == -1:
            return out
        close = DIV_TAG.match(out, end)
        out = out[:target.start()] + out[close.end():]
    return out


def strip_listing_titles(src: str) -> str:
    return re.sub(r"""<b[^>]*class=["'][^"']*\btlt\b[^"']*["'][^>]*>[\s\S]*?</b>\s*(?=<div[^>]*class=["'][^"']*\bboxpromote\b)""",
                  "", src, flags=re.I)


def remove_non_anchor_elements(h: str) -> str:
    h = re.sub(r"""<a[^>]*class=["'][^"']*postarticle[^"']*["'][^>]*>[\s\S]*?</a>""", " ", h, flags=re.I)
    h = re.sub(r"""<a[^>]*class=["'][^"']+["'][^>]*>[\s\S]*?</a>""", " ", h, flags=re.I)
    h = re.sub(r"""<[^>]*class=["'][^"']*pro-(?:1sp|2sp|moresp|container)[^"']*["'][^>]*>[\s\S]*?</(?:ul|div|section)>""",
               " ", h, flags=re.I)
    h = re.sub(r"\[product[^\]]*\]", " ", h, flags=re.I)
    h = re.sub(r"<a[^>]*>\s*<img[^>]*>\s*</a>", " ", h, flags=re.I)
    return h


def extract_pure_anchors(h: str) -> list[dict]:
    out = []
    for m in re.finditer(r"<a\b([^>]*)>([\s\S]*?)</a>", h, re.I):
        text = inline(decode(TAG_RE.sub("", m.group(2))))
        hm = re.search(r"""href=["']([^"']+)["']""", m.group(1), re.I)
        if not hm:
            continue
        href = hm.group(1)
        if re.match(r"^(tel:|mailto:|javascript:|#)", href):
            continue
        if re.search(r"[?&]itm_(medium|source|campaign)=", href, re.I):
            continue
        if len(text) < 2:
            continue
        out.append({"href": href, "anchorText": text})
    return out


def mask_links(h: str) -> str:
    """Thay chữ nằm trong <a> bằng '·' (cùng độ dài) để không gắn link lồng link."""
    return re.sub(r"<a\b[^>]*>([\s\S]*?)</a>",
                  lambda m: re.sub(r"[^\s.!?…]", "·", html_to_text(m.group(1))), h, flags=re.I)


def is_link_list(h: str) -> bool:
    links = re.findall(r"<a\b[^>]*>[\s\S]*?</a>", h or "", re.I)
    if len(links) >= 12:
        return True
    if len(links) < 3:
        return False
    total = len(re.sub(r"\s", "", html_to_text(h)))
    in_links = sum(len(re.sub(r"\s", "", html_to_text(a))) for a in links)
    return total > 0 and in_links / total > 0.7


PROMO_RE = re.compile(r"(tham khảo (các|ngay|thêm)|xem thêm|mời bạn|đừng bỏ lỡ|giá bình dân|ưu đãi \d+%|sắm ngay|mua ngay|trả góp)", re.I)
LEADIN_RE = re.compile(r":\s*$")
NEGATIVE_RE = re.compile(r"(lừa đảo|cảnh giác|cảnh báo|giả mạo|mất tiền|mất tài khoản|hack|bẻ khóa|vi phạm|khiếu nại|rủi ro bảo mật)", re.I)
OUTRO_RE = re.compile(r"^(Hy vọng|Hi vọng|Trên đây|Như vậy|Tóm lại|Vừa rồi|Bài viết trên|Cảm ơn|Chúc bạn)", re.I)


def split_sentences(txt: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+|\n+", txt or "")
    return [s for s in (inline(p) for p in parts) if len(s) >= 25]


def brand_of(url_dich: str, url_bai: str) -> str:
    u = (url_dich or url_bai or "").lower()
    if "topzone.vn" in u:
        return "TopZone"
    if "dienmayxanh.com" in u:
        return "Điện máy XANH"
    return "Thế Giới Di Động"


UNIT_RE = re.compile(r"^(\d+(?:[.,]\d+)?)(gb|tb|mb|kg|ml|mah|hz|inch|w|l)$")


class Article:
    def __init__(self, url: str, raw_html: str):
        self.url = url
        self.host = host_of(url)
        names = CONTAINERS_DMX if "dienmayxanh.com" in self.host else CONTAINERS
        raw, used = "", ""
        for name in names:
            found = slice_balanced_div(raw_html, class_div_re(name))
            if len(found) > 200:
                raw, used = found, name
                break
        # Không fallback về <article>/toàn trang: dễ ăn cả khối bài liên quan cuối trang.
        self.container = used
        raw = strip_listing_titles(strip_see_also(cut_tail(cut_head(raw))))
        self.extract_ok = len(raw) > 200
        art = strip_balanced_blocks(raw, JUNK_BLOCKS)
        self.article_html = art

        # Vùng NHẬN DIỆN: giữ sapo + heading (sapo TGDĐ bọc trong <h2>).
        no_heading = re.sub(r"<p[^>]*text-align:\s*center[^>]*>[\s\S]*?</p>",
                            lambda m: "" if re.search(r"<a\b|<img\b", m.group(0), re.I) else m.group(0), art, flags=re.I)
        no_heading = re.sub(r"<table[\s\S]*?</table>", " ", no_heading, flags=re.I)
        self.no_heading = no_heading
        self.infobox_html = "\n".join(collect_infoboxes(no_heading))
        self.no_infobox = strip_balanced_blocks(no_heading, ["infobox"])

        # Vùng CHỌN ĐOẠN MỐC: bỏ sapo (trước heading đầu), heading, caption, bảng, infobox.
        fh = re.search(r"<h[2-6][^>]*>", art, re.I)
        body = art[fh.start():] if fh else art
        body = re.sub(r"<h[1-6][^>]*>[\s\S]*?</h[1-6]>", "", body, flags=re.I)
        body = re.sub(r"<p[^>]*(?:text-align:\s*center|color:\s*#?777)[^>]*>[\s\S]*?</p>", "", body, flags=re.I)
        body = re.sub(r"<table[\s\S]*?</table>", " ", body, flags=re.I)
        self.anchor_candidate_html = strip_balanced_blocks(body, ["infobox"])

        cleaned = remove_non_anchor_elements(no_heading)
        self.pure_anchors = extract_pure_anchors(cleaned)
        self.plain = html_to_text(cleaned)
        self.article_plain = html_to_text(no_heading)
        self.article_plain_masked = html_to_text(mask_links(no_heading))
        self.link_list_text = "\n".join(
            inline(html_to_text(m.group(2)))
            for m in re.finditer(r"<(p|li|div)\b[^>]*>([\s\S]*?)</\1>", no_heading, re.I)
            if re.search(r"<a\b", m.group(2), re.I) and is_link_list(m.group(2)))

        self.image_alts = []
        for m in re.finditer(r"""<img[^>]*\balt=["']([^"']{15,})["']""", art, re.I):
            a = inline(decode(m.group(1)))
            if a and a not in self.image_alts:
                self.image_alts.append(a)

        paras = self._extract_paragraphs(self.anchor_candidate_html)
        if not paras:
            paras = self._extract_paragraphs(self.no_infobox)
        if not paras:
            paras = [s for s in split_sentences(html_to_text(self.no_infobox))
                     if not PROMO_RE.search(s) and not NEGATIVE_RE.search(s)]
        self.total_paragraphs = len(paras)
        self.paragraphs = paras[:20]
        self.marked, self.candidates = self._build_marked()

    def is_caption(self, t: str) -> bool:
        x = re.sub(r"[.\s]+$", "", t.lower())
        if len(x) < 15:
            return False
        for a in self.image_alts:
            y = re.sub(r"[.\s]+$", "", a.lower())
            if y and (x == y or (len(x) >= len(y) * 0.85 and y.startswith(x))
                      or (len(y) >= len(x) * 0.85 and x.startswith(y))):
                return True
        return False

    def _extract_paragraphs(self, src: str) -> list[str]:
        out = []
        for m in re.finditer(r"<p\b[^>]*>([\s\S]*?)</p>", src, re.I):
            inner = m.group(1)
            t = inline(html_to_text(inner))
            if len(t) < 60:
                continue
            link_text = inline(decode(TAG_RE.sub("", " ".join(re.findall(r"<a\b[^>]*>[\s\S]*?</a>", inner, re.I)))))
            if len(link_text) > len(t) * 0.6:
                continue
            if self.host:
                hrefs = re.findall(r"""href=["'](https?://[^"']+)["']""", inner, re.I)
                if any(host_of(h) and host_of(h) != self.host for h in hrefs):
                    continue  # đoạn có link ra domain khác
            if self.is_caption(t):
                continue
            if PROMO_RE.search(t) and len(t) < 140:
                continue
            if NEGATIVE_RE.search(t):
                continue
            if re.search(r":\s*\d*$", t):
                continue
            if t not in out:
                out.append(t)
        return out

    def _build_marked(self):
        """Toàn bài theo thứ tự gốc có nhãn khối; ⟦N⟧ = vị trí được phép chèn bên dưới."""
        block_re = re.compile(r"""<(h[2-6]|p|ul|ol|table)\b(?:[^>"']|"[^"]*"|'[^']*')*>([\s\S]*?)</\1\s*>""", re.I)
        li_re = re.compile(r"""<li\b(?:[^>"']|"[^"]*"|'[^']*')*>([\s\S]*?)</li\s*>""", re.I)
        idx_by_text = {}
        for i, p in enumerate(self.paragraphs):
            idx_by_text.setdefault(p, i + 1)
        lines, blocks, total, used = [], [], 0, set()
        for m in block_re.finditer(self.article_html):
            tag, inner = m.group(1).lower(), m.group(2)
            t = inline(html_to_text(inner))
            kind, n = "", None
            if tag.startswith("h"):
                if not t:
                    continue
                line, kind = "## " + t, "heading"
            elif tag == "table":
                line, kind = "[bảng số liệu]", "table"
            elif tag in ("ul", "ol"):
                items = ["    - " + (it[:120] + "…" if len(it) > 120 else it)
                         for it in (inline(html_to_text(x.group(1))) for x in li_re.finditer(inner)) if it]
                if not items:
                    continue
                line, kind = "[DANH SÁCH gạch đầu dòng]\n" + "\n".join(items), "list"
            elif re.search(r"<img\b", inner, re.I) and len(t) < 20:
                line, kind = "[ẢNH minh hoạ]", "image"
            elif not t:
                continue
            elif self.is_caption(t):
                line, kind = "[chú thích ảnh] " + t[:100], "caption"
            else:
                n = idx_by_text.get(t)
                if n in used:
                    n = None  # đoạn trùng chữ: chỉ đánh dấu lần xuất hiện đầu
                used.add(n)
                line, kind = t + (f"   ⟦{n}⟧" if n else ""), "para"
            if total + len(line) > 30000:
                lines.append("[…phần cuối bài bị cắt vì quá dài]")
                break
            lines.append(line)
            blocks.append((kind, n, t))
            total += len(line) + 1

        count = len(self.paragraphs)
        cands = []
        for bi, (kind, n, t) in enumerate(blocks):
            if not n:
                continue
            nxt = blocks[bi + 1][0] if bi + 1 < len(blocks) else "end"
            pos = (n - 1) / max(count - 1, 1)
            zone = "đầu" if pos < 0.35 else ("giữa" if pos < 0.70 else "cuối")
            cands.append({
                "n": n, "zone": zone, "next_block": nxt,
                "section_end": nxt == "heading",
                "outro": bool(OUTRO_RE.match(t)),
                "last_paragraph": n == count and self.total_paragraphs <= count,
                "text": t,
            })
        return "\n".join(lines), cands

    def casing_from_article(self, kw: str) -> str:
        if not kw:
            return ""
        kw_upper = kw == kw.upper()
        counts = {}
        for m in standalone_re(kw).finditer(self.article_plain):
            hit = m.group(0)
            if not kw_upper and hit == hit.upper() and re.search(r"[a-zA-Z" + VI + "]", hit):
                continue
            counts[hit] = counts.get(hit, 0) + 1
        return max(counts, key=counts.get) if counts else ""

    def canonical(self, raw: str) -> str:
        base = self.casing_from_article(raw) or raw or ""

        def unit(m):
            u = UNIT_RE.match(m.group(0).lower())
            return u.group(1) + u.group(2).upper() if u else m.group(0)
        return re.sub(r"\S+", unit, base)


def has_free_occurrence(text: str, mask: str, kw: str) -> bool:
    if not kw:
        return False
    usable = bool(mask) and len(mask) == len(text)
    for m in anchorable_re(kw).finditer(text):
        if not usable or "·" not in mask[m.start():m.end()]:
            return True
    return False


def analyze_pair(art: Article, keyword: str, url_dich: str) -> dict:
    target_norm, target_key = normalize_url(url_dich), url_key(url_dich)

    def is_target(href):
        hh = normalize_url(href)
        if target_norm and (hh == target_norm or hh.startswith(target_norm + "/") or hh.startswith(target_norm + "?")):
            return True
        return bool(target_norm) and url_key(href) == target_key

    matched = [a for a in art.pure_anchors if is_target(a["href"])]
    has_link = bool(matched)
    anchor_matched, existing = False, ""
    if has_link:
        with_kw = [a for a in matched if keyword and standalone_re(keyword).search(a["anchorText"])]
        anchor_matched = bool(with_kw)
        existing = (with_kw or matched)[0]["anchorText"]
    infobox_links = extract_pure_anchors(remove_non_anchor_elements(art.infobox_html)) if art.infobox_html else []
    is_infobox_link = has_link and any(is_target(a["href"]) for a in infobox_links)

    anchor_sentence = ""
    if has_link:
        for b in re.finditer(r"<(p|li|div)\b[^>]*>([\s\S]*?)</\1>", art.no_heading, re.I):
            bh = b.group(2)
            if not re.search(r"<a\b", bh, re.I):
                continue
            if not any(is_target(a["href"]) for a in extract_pure_anchors(bh)):
                continue
            if is_link_list(bh):
                continue  # khối danh sách link điều hướng: chỉ sửa cụm anchor
            bt = inline(html_to_text(bh))
            if not bt:
                continue
            hit = next((s for s in split_sentences(bt) if existing.lower() in s.lower()), None)
            anchor_sentence = hit or bt
            break
        if not anchor_sentence and existing:
            rx = re.compile(re.escape(existing), re.I)
            anchor_sentence = next((s for s in split_sentences(art.article_plain)
                                    if rx.search(s) and s[:50] not in art.link_list_text), "")

    kw_sentences = []
    if keyword:
        allp = split_sentences(art.article_plain)
        allm = split_sentences(art.article_plain_masked)
        aligned = len(allp) == len(allm)
        matched_s = [s for i, s in enumerate(allp)
                     if not PROMO_RE.search(s) and not LEADIN_RE.search(s)
                     and has_free_occurrence(s, allm[i] if aligned else "", keyword)]
        clean = [s for s in matched_s if not has_longer_variant(s, keyword)]
        messy = [s for s in matched_s if has_longer_variant(s, keyword)]
        kw_sentences = (clean + messy)[:8]
    infobox_plain = html_to_text(art.infobox_html)
    kw_sentences_info = [{"n": i + 1, "text": s,
                          "in_infobox": bool(infobox_plain and s[:60] in infobox_plain),
                          "has_longer_variant": has_longer_variant(s, keyword)}
                         for i, s in enumerate(kw_sentences)]

    if has_link and anchor_matched:
        bucket = "ok"
    elif has_link:
        bucket = "fixAnchor"
    elif kw_sentences:
        bucket = "insertText"
    else:
        bucket = "newContent"
    return {
        "keyword": keyword, "keyword_display": art.canonical(keyword), "url_dich": url_dich,
        "bucket": bucket, "has_link": has_link, "anchor_matched": anchor_matched,
        "existing_anchor_text": existing, "is_infobox_link": is_infobox_link,
        "anchor_sentence": anchor_sentence, "keyword_sentences": kw_sentences_info,
        "brand": brand_of(url_dich, art.url),
    }


def join_vi(items: list[str]) -> str:
    if len(items) <= 1:
        return items[0] if items else ""
    return ", ".join(items[:-1]) + " hoặc " + items[-1]


def group_pairs(pairs: list[dict]) -> list[dict]:
    """Mỗi nhánh việc = 1 nhóm = 1 dòng WF đi link. 'ok' không sinh dòng."""
    order, by = [], {}
    for p in pairs:
        if p["bucket"] == "ok":
            continue
        if p["bucket"] not in by:
            by[p["bucket"]] = []
            order.append(p["bucket"])
        by[p["bucket"]].append(p)
    groups = []
    for b in order:
        g = by[b]
        displays = [p["keyword_display"] for p in g if p["keyword_display"]]
        hint, relation = join_vi(displays), "sibling"
        if len(displays) > 1:
            parent, *children = sorted(displays, key=len)
            if all(c.lower().startswith(parent.lower() + " ") for c in children):
                relation, hint = "parent-child", "các dòng " + parent + " như " + join_vi(children)
        groups.append({
            "bucket": b, "keywords": [p["keyword"] for p in g],
            "anchor_text_E": "\n".join(displays), "link_F": "\n".join(p["url_dich"] for p in g),
            "keyword_phrase_hint": hint, "keyword_relation": relation, "pairs": g,
        })
    return groups


def fetch(url: str) -> str:
    res = subprocess.run(["curl", "-sL", "--max-time", "40", "-A", CURL_UA,
                          "-H", "Accept-Language: vi-VN,vi;q=0.9,en;q=0.8", url],
                         capture_output=True, text=True)
    return res.stdout


def analyze(url: str, pairs: list[tuple[str, str]], html_text: str | None = None) -> dict:
    raw = html_text if html_text is not None else fetch(url)
    art = Article(url, raw)
    out = {"url_bai_tin": url, "extract_ok": art.extract_ok, "container": art.container}
    if not art.extract_ok:
        out["error"] = "Không bóc được thân bài (container trượt / 404 / timeout) - báo fail, không đoán."
        return out
    analyzed = [analyze_pair(art, kw, u) for kw, u in pairs]
    groups = group_pairs(analyzed)
    out.update({
        "all_ok": all(p["bucket"] == "ok" for p in analyzed),
        "pairs": analyzed,
        "groups": groups,
        "paragraph_count": len(art.paragraphs),
        "candidates": art.candidates,
        "article_marked": art.marked,
    })
    return out


def split_lines(v) -> list[str]:
    return [s.strip() for s in str(v or "").splitlines() if s.strip()]


def make_pairs(kw_cell, url_cell) -> list[tuple[str, str]]:
    kws, urls = split_lines(kw_cell), split_lines(url_cell)
    n = min(len(kws), len(urls)) or 1
    return [(kws[i] if i < len(kws) else "", urls[i] if i < len(urls) else "") for i in range(n)]


def read_plan(spreadsheet_id: str) -> list[list[str]]:
    res = subprocess.run(["gws", "sheets", "+read", "--spreadsheet", spreadsheet_id,
                          "--range", f"'{PLAN_TAB}'!A1:G"], capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"[ERROR] gws read plan failed: {res.stderr}")
    return json.loads(res.stdout[res.stdout.find("{"):]).get("values", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze")
    a.add_argument("--url", required=True)
    a.add_argument("--pair", action="append", default=[], help='"keyword|url đích", lặp lại được')
    a.add_argument("--html-file")
    a.add_argument("--no-marked", action="store_true", help="Bỏ article_marked cho output gọn")
    p = sub.add_parser("plan")
    p.add_argument("--spreadsheet-id", default=PLAN_SHEET_ID)
    p.add_argument("--status", default="Run")
    p.add_argument("--limit", type=int, default=0, help="Chỉ xử lý N dòng đầu khớp status (0 = tất cả)")
    p.add_argument("--no-marked", action="store_true")
    args = ap.parse_args()

    if args.cmd == "analyze":
        pairs = [tuple((x.split("|", 1) + [""])[:2]) for x in args.pair] or [("", "")]
        html_text = open(args.html_file, encoding="utf-8").read() if args.html_file else None
        results = [analyze(args.url, [(k.strip(), u.strip()) for k, u in pairs], html_text)]
    else:
        rows = read_plan(args.spreadsheet_id)
        header = rows[0] if rows else []
        col = {name: i for i, name in enumerate(header)}
        need = ["Keyword cần chèn", "URL cần chèn", "URL bài tin", "Status"]
        if any(n not in col for n in need):
            sys.exit(f"[ERROR] Header tab {PLAN_TAB} thiếu cột: {need}. Header hiện có: {header}")
        results = []
        for i, r in enumerate(rows[1:], start=2):
            cell = lambda n: r[col[n]] if col[n] < len(r) else ""
            if cell("Status").strip() != args.status:
                continue
            if args.limit and len(results) >= args.limit:
                break
            res = analyze(cell("URL bài tin").strip(), make_pairs(cell("Keyword cần chèn"), cell("URL cần chèn")))
            res.update({"plan_row": i, "plan_keyword_cell": cell("Keyword cần chèn")})
            results.append(res)
    if args.no_marked:
        for r in results:
            r.pop("article_marked", None)
    json.dump(results, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
