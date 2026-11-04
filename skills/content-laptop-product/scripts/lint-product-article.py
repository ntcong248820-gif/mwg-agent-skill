#!/usr/bin/env python3
"""Lint bài Content SP (product_articles) trước khi giao owner. Chỉ đọc file.

Dùng: lint-product-article.py BAI.html --category laptop|may-tinh-de-ban|man-hinh-may-tinh|may-in|phan-mem
         [--url /laptop/<slug>] [--facts facts.json]
facts.json: {"must": ["128GB", ...], "must_not": ["64GB", ...], "hedge_numbers": ["1000 TOPS", ...]}
  must     : chuỗi phải có trong chữ của bài
  must_not : chuỗi cấm (thông số của bản anh em, số đang mâu thuẫn chưa chốt)
  allow_must_not_in: ["Chọn bản"]  # mục so sánh bản anh em được nêu thông số bản kia
  hedge_numbers: số hãng công bố, câu chứa số đó phải có "theo hãng/theo NVIDIA/theo công bố..."
Exit 0 = không có ERROR; 1 = có ERROR (WARN không tính).
"""
import argparse, collections, html, json, re, sys

RANGE = {  # (h3 min, h3 max, từ min, từ max), đã tính box Đặc điểm nổi bật, bảng so sánh, FAQ
    "laptop": (6, 10, 750, 1600),
    "may-tinh-de-ban": (5, 8, 600, 1150),
    "man-hinh-may-tinh": (5, 7, 600, 1050),
    "may-in": (6, 11, 650, 1450),
    "phan-mem": (6, 9, 900, 1500),
}
HARDWARE = {"laptop", "may-tinh-de-ban", "man-hinh-may-tinh", "may-in"}
# FAQ hỏi điều đọc được ngay từ bảng thông số hoặc hỏi chung chung: không mang giá trị
OBVIOUS_Q = re.compile(r"bao nhiêu inch|nặng bao nhiêu|mấy màu|màu gì|có mấy (màu|phiên bản)|kích thước (là )?bao nhiêu|"
                       r"dùng chip gì|ra mắt (khi nào|năm nào)|có tốt không|có nên mua|có đáng mua|giá bao nhiêu|mua ở đâu", re.I)
BANNED = [r"đỉnh cao", r"vượt trội", r"đột phá", r"ấn tượng", r"nâng tầm", r"hoàn hảo", r"rõ rệt",
          r"theo dữ liệu", r"dữ liệu được cung cấp", r"trang sản phẩm (đang )?(hiển thị|ghi)", r"tại thời điểm kiểm tra", r"còn hàng", r"tạm hết hàng",
          r"mạnh nhất", r"tốt nhất", r"số 1\b", r"số một", r"đỉnh nhất", r"rẻ nhất", r"không đối thủ",
          r"\btôi\b", r"hàng đầu thế giới"]
PRICE = re.compile(r"\d[\d.,]*\s*(triệu|tr\b|đồng|đ\b|vnđ|₫)", re.I)
HEDGE = re.compile(r"theo (hãng|nvidia|msi|intel|amd|qualcomm|nhà sản xuất|công bố|thông số)|(hãng|nvidia|msi|intel|amd|qualcomm|microsoft) (công bố|cho biết)|công bố của", re.I)
CDN = ("cdn.tgdd.vn", "cdnv2.tgdd.vn")
JARGON = ["NPU", "TOPS", "VRR", "DCI-P3", "Tandem OLED", "OLED", "Pluton", "TPM", "Vapor Chamber", "LPDDR5x", "bộ nhớ hợp nhất",
          "TGP", "PWM", "VRAM", "DisplayHDR", "WUXGA", "Thunderbolt", "PCIe", "NVMe", "Windows on Arm", "bus"]
EXPLAIN = re.compile(r"là |mức chứng nhận|tức |nghĩa là|giúp|cho phép|dùng để|riêng cho|dải màu|đơn vị|buồng|\(")
DOMAIN_TYPO = re.compile(r"thegioidong\.com|thegioididong\.vn|thegioididong\.con")


def text_of(s):
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--category", required=True, choices=RANGE)
    ap.add_argument("--url", help="đường dẫn trang, vd /laptop/msi-...; bật kiểm self-link ở mở bài")
    ap.add_argument("--facts")
    a = ap.parse_args()
    src = open(a.file, encoding="utf8").read()
    txt = text_of(src)
    words = len(txt.split())
    errs, warns = [], []
    E, W = errs.append, warns.append

    h3 = re.findall(r"<h3[^>]*>(.*?)</h3>", src, flags=re.S)
    lo, hi, wlo, whi = RANGE[a.category]
    if re.search(r"<h[12]\b", src):
        E("có <h1>/<h2>: h2 của trang đã dùng cho tab Thông số/Thông tin sản phẩm, bài chỉ dùng <h3>")
    # box Đặc điểm nổi bật: phần tử đầu tiên, trước h3 đầu
    first_h3 = src.find("<h3")
    head = src[:first_h3] if first_h3 >= 0 else ""
    if a.category in HARDWARE:
        if "đặc điểm nổi bật" not in text_of(head).lower() or "<ul" not in head:
            E("thiếu box Đặc điểm nổi bật (div + <ul>) trước <h3> đầu tiên")
        else:
            nli = head.count("<li")
            if not 3 <= nli <= 6:
                W(f"box Đặc điểm nổi bật có {nli} dòng, chuẩn 4-5")
    # FAQ: h3 cuối "Câu hỏi thường gặp", câu hỏi là h4
    faq_i = max((m.start() for m in re.finditer(r"<h3[^>]*>[^<]*(Câu hỏi thường gặp|Một số câu hỏi)", src)), default=-1)
    if a.category in HARDWARE and faq_i < 0:
        E("thiếu mục FAQ (<h3>Câu hỏi thường gặp về ...</h3> + câu hỏi <h4>) ở cuối bài")
    if faq_i >= 0:
        if src.find("<h3", faq_i + 3) >= 0:
            E("mục FAQ phải là <h3> cuối cùng của bài")
        qs = [text_of(q) for q in re.findall(r"<h4[^>]*>(.*?)</h4>", src[faq_i:], flags=re.S)]
        if not 2 <= len(qs) <= 4:
            E(f"FAQ có {len(qs)} câu hỏi <h4>, chuẩn 2-4")
        for q in qs:
            if not q.endswith("?"):
                E(f"câu hỏi FAQ không kết thúc bằng '?': {q[:60]}")
            if OBVIOUS_Q.search(q):
                E(f"câu hỏi FAQ hiển nhiên/chung chung (đọc được từ thông số hoặc 'có nên mua'): {q[:70]}")
        if "theo ước tính" in text_of(src[faq_i:]).lower():
            E("FAQ trả lời bằng 'theo ước tính' (không nguồn)")
        # Câu trả lời đẩy người đọc đi hỏi chỗ khác = chưa có chứng cứ chắc chắn, phải bỏ câu hỏi
        m = re.search(r"hỏi (nhân viên|cửa hàng|tổng đài)|liên hệ (cửa hàng|tổng đài|hãng)|chưa (rõ|xác nhận|có thông tin)|"
                      r"tùy (lô|đợt|thị trường)|nguồn (lệch|khác nhau)", text_of(src[faq_i:]), re.I)
        if m:
            E(f"FAQ có câu trả lời không chắc ('{m.group(0)}'): không có chứng cứ chắc chắn thì bỏ câu hỏi")
    if re.search(r"<h4\b", src[:faq_i] if faq_i >= 0 else src) or re.search(r"<h5\b", src):
        W("có <h4>/<h5> ngoài FAQ: thân bài chỉ dùng h3")
    for h in h3:
        if re.match(r"\s*\d+[.)]", text_of(h)):
            W(f"<h3> đánh số (bài SP dùng h3 không số): {text_of(h)[:50]}")
    if not lo <= len(h3) <= hi:
        E(f"số <h3> = {len(h3)}, khoảng chuẩn {lo}-{hi}")
    if not wlo <= words <= whi:
        (E if words < wlo * 0.8 or words > whi * 1.3 else W)(f"{words} từ, khoảng chuẩn {wlo}-{whi}")
    for h in h3:
        t = text_of(h)
        if not t:
            E("có <h3> rỗng")
        elif len(t.split()) > 60 and h is not h3[0]:
            W(f"<h3> dài {len(t.split())} từ ở mục thân: heading nên ngắn")

    links = re.findall(r"<a\b([^>]*)>(.*?)</a>", src, flags=re.S)
    hrefs = []
    for attrs, inner in links:
        m = re.search(r'href="([^"]*)"', attrs)
        href = m.group(1) if m else ""
        hrefs.append(href)
        if not href:
            continue  # <a> rỗng bọc ảnh là mẫu có thật
        if DOMAIN_TYPO.search(href):
            E(f"domain sai: {href}")
        if href.startswith("http://"):
            E(f"link http (phải https): {href}")
        if "thegioididong.com" in href and 'target="_blank"' not in attrs:
            W(f"link thiếu target=_blank: {href}")
        if "thegioididong.com" in href and "rel=" not in attrs:
            W(f"link thiếu rel=noopener: {href}")
        if "thegioididong.com" in href and "title=" not in attrs:
            W(f"link thiếu title: {href}")
        if re.search(r"\?(q|keyword|search)=|/tag/|/tim-kiem|/ldp", href):
            E(f"link tìm kiếm/tag/ldp bị cấm: {href}")
    dup = [h for h, n in collections.Counter(h.split("#")[0].rstrip("/") for h in hrefs if h).items() if n > 1]
    for d in dup:
        E(f"URL được link nhiều lần (mỗi URL 1 lần/bài): {d}")
    nlink = len([h for h in hrefs if h])
    if a.category != "phan-mem" and not 4 <= nlink <= 9:
        W(f"{nlink} link, mẫu đang chạy 4-9")
    if a.url:
        first = next((h for h in hrefs if h), "")
        if first.replace("https://www.thegioididong.com", "").split("?")[0].rstrip("/") != a.url.rstrip("/"):
            E("link đầu tiên không phải self-link về trang SP (mẫu: anchor = tên đầy đủ + mã, nằm ở mở bài)")

    for p in BANNED:
        for m in re.finditer(p, txt, flags=re.I):
            E(f"cụm cấm '{m.group(0)}': …{txt[max(0, m.start()-30):m.end()+30]}…")
    # rule kế thừa từ skill viết infobox/viet-blog: dấu câu, thuật ngữ, xưng hô
    if ";" in txt:
        W("có dấu ';' (viet-blog: không dùng; thay bằng chấm hoặc liên từ)")
    for para in re.findall(r"<p[^>]*>(.*?)</p>", src, flags=re.S):
        pt = text_of(para)
        if pt.count(":") >= 1 and not re.search(r"\d:\d|Virtual:X", pt) or pt.replace("Virtual:X", "").count(":") > 1:
            W(f"dấu ':' trong văn xuôi (infobox: không thay động từ, tối đa 1/đoạn và chỉ trước danh sách): …{pt[:60]}…")
    for h in h3:
        if ":" in text_of(h):
            W(f"heading có dấu ':' (viet-blog: không kiểu 'Về X: ...'): {text_of(h)[:60]}")
    sentences0 = re.split(r"(?<=[.!?])\s+", txt)
    for term in JARGON:
        first = next((sn for sn in sentences0 if re.search(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", sn)), None)
        nxt = sentences0[sentences0.index(first) + 1] if first and sentences0.index(first) + 1 < len(sentences0) else ""
        if first and not EXPLAIN.search(first) and not EXPLAIN.search(nxt) and len(first.split()) < 60 and term not in ("OLED", "bus", "NVMe", "PCIe", "LPDDR5x", "Thunderbolt"):
            W(f"thuật ngữ '{term}' xuất hiện lần đầu chưa kèm giải thích bằng lời thường: …{first[:80]}…")
    if not re.search(r"\bbạn\b", txt, flags=re.I):
        W("không xưng 'bạn' lần nào (infobox: viết có tương tác với người đọc)")
    for m in re.finditer(r"(?<!bên )(?<!của )\bmình\b", txt, flags=re.I):
        W(f"xưng 'mình' (bài SP viết ngôi thứ ba): …{txt[max(0, m.start()-30):m.end()+30]}…")
    for m in PRICE.finditer(txt):
        W(f"có số giống giá '{m.group(0)}': giá biến động, không đưa vào bài")

    for im in re.findall(r"<img\b[^>]*>", src):
        alt = re.search(r'alt="([^"]*)"', im)
        ti = re.search(r'title="([^"]*)"', im)
        sc = re.search(r'src="([^"]*)"', im)
        if not alt or not alt.group(1).strip():
            E("ảnh thiếu alt")
        if not ti or (alt and ti.group(1) != alt.group(1)):
            W("title ảnh nên giống alt (mẫu đang chạy)")
        if sc and not sc.group(1).startswith("https://" ) :
            E(f"ảnh src không https: {sc.group(1)[:60]}")
        elif sc and not any(c in sc.group(1) for c in CDN):
            W(f"ảnh không ở CDN TGDĐ (chưa upload?): {sc.group(1)[:70]}")
    if "<ul" in src and "list-style" not in src:
        E("<ul>/<ol> thiếu style trực tiếp (list-style: disc; padding-left: 25px): CSS web tắt bullet")
    for tb in re.findall(r"<table\b.*?</table>", src, flags=re.S):
        if "border" not in tb:
            E("<table> chưa có border/style trực tiếp (CSS web không tự kẻ bảng)")
        rows = tb.count("<tr")
        if not 4 <= rows <= 12:
            W(f"bảng có {rows} dòng (kể cả dòng tiêu đề), chuẩn so sánh 5-10 dòng dữ liệu")
        if PRICE.search(text_of(tb)):
            E("bảng so sánh có giá (không đưa giá vào bài SP)")
        # Header cột SP phải là tên đầy đủ, không ghi "bản này" hay chỉ mã máy
        for th in re.findall(r"<th\b[^>]*>(.*?)</th>", tb, flags=re.S)[1:]:
            t = text_of(th).strip()
            if re.search(r"\b(bản|máy|sản phẩm|mẫu) này\b", t, re.I) or len(t.split()) < 3:
                E(f"header bảng '{t}' phải là tên đầy đủ của SP (vd MSI Prestige N16 Flip AI+ C1XMT 016VN)")

    if a.facts:
        f = json.load(open(a.facts, encoding="utf8"))
        norm = lambda s: re.sub(r"\s+", "", s.lower())
        nt = norm(txt)
        for s in f.get("must", []):
            if norm(s) not in nt:
                E(f"thiếu thông số bắt buộc: {s}")
        # must_not được phép xuất hiện trong mục so sánh bản anh em (h3 chứa 1 trong allow_must_not_in)
        body = src
        for key in f.get("allow_must_not_in", []):
            body = re.sub(r"<h3[^>]*>[^<]*" + re.escape(key) + r"[^<]*</h3>.*?(?=<h3|</div>\s*$|$)", "", body, flags=re.S)
        nt_strict = norm(text_of(body))
        for s in f.get("must_not", []):
            if norm(s) in nt_strict:
                E(f"có chuỗi cấm (thông số bản khác/chưa chốt): {s}")
        sentences = re.split(r"(?<=[.!?])\s+", txt)
        for s in f.get("hedge_numbers", []):
            for sen in sentences:
                if norm(s) in norm(sen) and not HEDGE.search(sen):
                    E(f"số hãng công bố '{s}' không kèm 'theo hãng/theo NVIDIA…': {sen[:90]}…")

    print(f"{a.file}: {words} từ, h3={len(h3)}, link={nlink}, ảnh={src.count('<img')}")
    for e in errs:
        print("ERROR", e)
    for w in warns:
        print("WARN ", w)
    print("KẾT QUẢ:", "ĐẠT" if not errs else f"{len(errs)} ERROR")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
