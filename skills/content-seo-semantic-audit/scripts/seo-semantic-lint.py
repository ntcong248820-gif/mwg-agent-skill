#!/usr/bin/env python3
"""Lint bài SEO semantic (Markdown) theo brief.json: đếm từ, từ khoá, brand, từ hạn chế,
cấu trúc H1/H2/H3, CTA, meta, định dạng, câu dài, mở câu lặp.

Thay phần WORD COUNTER và checklist đếm tay của quy trình tab "Thầy".
Chỉ dùng thư viện chuẩn, chạy được Python 3.8+.

    python3 seo-semantic-lint.py BAI.md --brief brief.json [--stage draft|final] [--json OUT.json]

Exit 1 khi có FAIL, 0 khi chỉ có WARN/INFO.
"""
import argparse
import json
import re
import sys
import unicodedata

EN_HINT = {
    "the", "and", "for", "with", "interview", "process", "form", "status", "sponsor",
    "petition", "checklist", "online", "file", "case", "step", "tips", "guide", "review",
    "service", "update", "deadline", "approve", "approved", "denied", "evidence", "green",
    "card", "check", "list", "top", "best", "how", "what", "why",
}
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐✅❌]")
WORD_EDGE_L, WORD_EDGE_R = r"(?<!\w)", r"(?!\w)"


def norm(s):
    s = unicodedata.normalize("NFC", s).lower()
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


def strip_md(s):
    s = re.sub(r"^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*)", "", s)
    return s.replace("**", "").replace("__", "")


def parse(md):
    """Trả về meta, danh sách block (type, level, text) theo thứ tự bài."""
    meta, blocks, para = None, [], []

    def flush():
        if para:
            blocks.append(("p", 0, " ".join(para)))
            para.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        m = re.match(r"^\s*(META|Meta description|Meta)\s*:\s*(.*)$", line, re.I)
        if m and meta is None and not blocks:
            meta = m.group(2).strip()
            continue
        h = re.match(r"^(#{1,3})\s+(.*)$", line)
        li = re.match(r"^\s*([-*+]|\d+[.)])\s+(.*)$", line)
        if h:
            flush()
            blocks.append(("h", len(h.group(1)), h.group(2).strip()))
        elif li:
            flush()
            blocks.append(("li", 0, li.group(2).strip()))
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
    flush()
    return meta, blocks


def find_spans(text, phrase):
    pat = re.compile(WORD_EDGE_L + re.escape(norm(phrase)) + WORD_EDGE_R)
    return [m.span() for m in pat.finditer(text)]


def count(text, phrase):
    return len(find_spans(text, phrase)) if phrase else 0


def standalone(text, phrase, others):
    """Số lần `phrase` đứng riêng, không nằm trong một cụm dài hơn thuộc `others`."""
    covers = []
    for o in others:
        if norm(o) != norm(phrase) and norm(phrase) in norm(o):
            covers += find_spans(text, o)
    return sum(1 for a, b in find_spans(text, phrase) if not any(x <= a and b <= y for x, y in covers))


def sentences(blocks):
    out = []
    for t, _, txt in blocks:
        if t == "h":
            continue
        for s in re.split(r"(?<=[.!?…])\s+", strip_md(txt)):
            if s.strip():
                out.append(s.strip())
    return out


def lint(md, brief, stage="final"):
    res = []

    def add(level, check, msg):
        res.append({"level": level, "check": check, "msg": msg})

    meta, blocks = parse(md)
    body_text = norm(" ".join(strip_md(t) for _, _, t in blocks))
    heads = [(lvl, norm(t)) for typ, lvl, t in blocks if typ == "h"]
    h1 = [t for lvl, t in heads if lvl == 1]
    h2_idx = [i for i, b in enumerate(blocks) if b[0] == "h" and b[1] == 2]
    paras = [norm(strip_md(t)) for typ, _, t in blocks if typ == "p"]
    first_h2 = h2_idx[0] if h2_idx else len(blocks)
    intro = [norm(t) for typ, _, t in blocks[:first_h2] if typ == "p"]
    sapo = intro[0] if intro else ""

    # 1. Số từ
    words = [w for w in re.findall(r"\S+", body_text) if re.search(r"\w", w)]
    so_tu = brief.get("so_tu", {})
    n = len(words)
    add("INFO", "so_tu", "%d từ (không tính META)" % n)
    if so_tu.get("toi_da") and n > so_tu["toi_da"]:
        add("FAIL", "so_tu", "%d từ > tối đa %d" % (n, so_tu["toi_da"]))
    if so_tu.get("muc_tieu") and n < 0.8 * so_tu["muc_tieu"]:
        add("WARN", "so_tu", "%d từ < 80%% mục tiêu %d" % (n, so_tu["muc_tieu"]))

    # 2. Cấu trúc
    if len(h1) != 1:
        add("FAIL", "cau_truc", "Có %d H1, cần đúng 1" % len(h1))
    spec = brief.get("cau_truc_h2") or []
    if spec and len(h2_idx) != len(spec):
        add("FAIL", "cau_truc", "Có %d H2, brief cần %d" % (len(h2_idx), len(spec)))
    for k, start in enumerate(h2_idx):
        end = h2_idx[k + 1] if k + 1 < len(h2_idx) else len(blocks)
        sec = blocks[start + 1:end]
        n_h3 = sum(1 for b in sec if b[0] == "h" and b[1] == 3)
        has_list = any(b[0] == "li" for b in sec)
        if k < len(spec):
            want = spec[k]
            if n_h3 != want.get("h3", 0):
                add("FAIL", "cau_truc", "H2 #%d có %d H3, cần %d" % (k + 1, n_h3, want.get("h3", 0)))
            if want.get("checklist") and not has_list:
                add("FAIL", "cau_truc", "H2 #%d thiếu checklist (danh sách gạch đầu dòng/số)" % (k + 1))
    if not sapo:
        add("FAIL", "sapo", "Không có đoạn sapo ngay sau H1")

    # 3-5. Từ khoá
    kw = brief.get("kw_chinh", "")
    phu = brief.get("kw_phu", [])
    caps = brief.get("tan_suat_toi_da", {})
    all_phrases = [kw] + phu + list(caps)
    if kw:
        if not h1 or count(h1[0], kw) == 0:
            add("FAIL", "kw_chinh", "H1 thiếu từ khoá chính nguyên cụm")
        if count(sapo, kw) == 0:
            add("FAIL", "kw_chinh", "Sapo thiếu từ khoá chính nguyên cụm")
        want = brief.get("kw_chinh_nguyen_cum")
        alone = standalone(body_text, kw, all_phrases)
        add("INFO", "kw_chinh", "'%s' đứng riêng %d lần, tính cả trong biến thể %d lần" % (kw, alone, count(body_text, kw)))
        if want is not None and alone != want:
            add("FAIL", "kw_chinh", "'%s' đứng riêng %d lần, cần đúng %d (H1 + sapo)" % (kw, alone, want))
    for p in phu:
        c = count(body_text, p)
        if c == 0:
            add("FAIL", "kw_phu", "Thiếu biến thể '%s'" % p)
        elif c > 1 and p not in caps:
            add("WARN", "kw_phu", "Biến thể '%s' xuất hiện %d lần, brief yêu cầu 1" % (p, c))
    for p, cap in caps.items():
        c = count(body_text, p)
        if c > cap:
            add("FAIL", "tan_suat", "'%s' %d lần > tối đa %d" % (p, c, cap))

    # 6-7. Brand
    brand = brief.get("brand", "")
    if brand:
        b = count(body_text, brand)
        want = brief.get("brand_so_lan")
        add("INFO", "brand", "'%s' %d lần" % (brand, b))
        if want is not None and b != want:
            add("FAIL", "brand", "'%s' %d lần, cần %d" % (brand, b, want))
        pos = brief.get("brand_tieu_de", {})
        if pos.get("h1") and (not h1 or count(h1[0], brand) == 0):
            add("FAIL", "brand", "H1 thiếu brand")
        h2_texts = [norm(blocks[i][2]) for i in h2_idx]
        for k in range(min(pos.get("h2", 0), len(h2_texts))):
            if count(h2_texts[k], brand) == 0:
                add("FAIL", "brand", "H2 #%d thiếu brand" % (k + 1))
        if brief.get("brand_sapo", True) and count(sapo, brand) == 0:
            add("FAIL", "brand", "Sapo thiếu brand")
        if paras and count(paras[-1], brand) == 0:
            add("FAIL", "brand", "Đoạn kết thiếu brand")
        rng = brief.get("brand_tong_ca_thay_the")
        if rng:
            tot = b + sum(count(body_text, t) for t in brief.get("brand_thay_the", []))
            lvl = "INFO" if rng[0] <= tot <= rng[1] else "WARN"
            add(lvl, "brand_da_dang", "Brand + cách gọi thay thế = %d (khoảng %d-%d)" % (tot, rng[0], rng[1]))

    # 8-9. Từ hạn chế, đếm thêm
    mx = brief.get("tu_han_che_toi_da", 3)
    for w in brief.get("tu_han_che", []):
        c = count(body_text, w)
        if c > mx:
            add("FAIL", "tu_han_che", "'%s' %d lần > %d" % (w, c, mx))
    for w, rng in (brief.get("dem_them") or {}).items():
        c = count(body_text, w)
        if not rng[0] <= c <= rng[1]:
            add("WARN", "dem_them", "'%s' %d lần, khoảng %d-%d" % (w, c, rng[0], rng[1]))

    # 10-11. CTA, meta
    cta = brief.get("cta_ket")
    if cta and norm(cta) not in body_text:
        add("FAIL", "cta", "Thiếu nguyên văn câu CTA kết bài")
    mt = brief.get("meta_toi_da", 140)
    if meta is None:
        add("FAIL" if stage == "final" else "WARN", "meta", "Thiếu dòng META:")
    else:
        if len(meta) >= mt:
            add("FAIL", "meta", "Meta %d ký tự, cần dưới %d" % (len(meta), mt))
        else:
            add("INFO", "meta", "Meta %d ký tự" % len(meta))

    # 12. Định dạng
    if re.search(r"\*\*|__|<b>|<strong>", md):
        add("FAIL", "dinh_dang", "Có in đậm")
    if re.search(r"(?<![*\w])\*[^*\s][^*]*\*(?!\*)", md):
        add("WARN", "dinh_dang", "Còn in nghiêng (dấu * đơn), bỏ trước khi giao")
    if EMOJI.search(md):
        add("FAIL", "dinh_dang", "Có icon/emoji")
    if "```" in md:
        add("FAIL", "dinh_dang", "Có khối code")

    # 13. Tiếng Anh xen
    allow = {norm(a) for a in brief.get("cho_phep_tieng_anh", [])} | set(norm(brand).split())
    hits = set()
    for w in re.findall(r"[A-Za-z][A-Za-z'-]+", unicodedata.normalize("NFC", " ".join(t for _, _, t in blocks))):
        lw = w.lower()
        if lw in allow or w.isupper() or re.match(r"^[A-Z]-?\d", w):
            continue
        if lw in EN_HINT or re.search(r"[fjwz]", lw):
            hits.add(w)
    if hits:
        add("WARN", "tieng_anh", "Từ tiếng Anh cần chuyển sang tiếng Việt: " + ", ".join(sorted(hits)))

    # 14-15. Câu dài, mở câu lặp
    sents = sentences(blocks)
    long_max = brief.get("cau_dai_toi_da", 35)
    longs = [s for s in sents if len(s.split()) > long_max]
    for s in longs:
        add("WARN", "cau_dai", "%d từ: %s…" % (len(s.split()), " ".join(s.split()[:10])))
    openers = {}
    for s in sents:
        key = " ".join(norm(s).split()[:2])
        openers[key] = openers.get(key, 0) + 1
    for k, v in sorted(openers.items(), key=lambda x: -x[1]):
        if v >= 3 and len(k) > 3:
            add("WARN", "mo_cau_lap", "'%s…' mở đầu %d câu" % (k, v))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("article")
    ap.add_argument("--brief", required=True)
    ap.add_argument("--stage", choices=["draft", "final"], default="final")
    ap.add_argument("--json")
    a = ap.parse_args()
    with open(a.article, encoding="utf-8") as f:
        md = f.read()
    with open(a.brief, encoding="utf-8") as f:
        brief = json.load(f)
    res = lint(md, brief, a.stage)
    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    for r in sorted(res, key=lambda r: order[r["level"]]):
        print("%-4s  %-14s %s" % (r["level"], r["check"], r["msg"]))
    fails = sum(r["level"] == "FAIL" for r in res)
    warns = sum(r["level"] == "WARN" for r in res)
    print("\nTổng: %d FAIL, %d WARN" % (fails, warns))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"fail": fails, "warn": warns, "items": res}, f, ensure_ascii=False, indent=2)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
