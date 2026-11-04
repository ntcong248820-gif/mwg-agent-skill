#!/usr/bin/env python3
"""Bước 7: lint HTML infobox PIM trước khi ghi.

  python3 kiem_pim.py <thư mục việc | file.html> [--link]

LỖI (thoát 1, ghi_pim.py không cho ghi):
- H3 chỉ có đúng 1 H4 con (chia heading phải từ 2 H4)
- không đúng 1 <h2> ở đầu bài, còn markdown sót (**, [x](y), ##), placeholder [..]
- dấu ";", gạch ngang dài, chữ "niêm yết", gọi sản phẩm là "thiết bị"
- H3 không đánh số liên tục 1..n, H4 con không đúng tiền tố số H3 cha, H4 câu hỏi FAQ có đánh số
- H4 đặc điểm nổi bật (mục "có gì mới"/"tại sao"/"đặc điểm") có dấu ":" hoặc dài > 18 từ
- < 3 ảnh, ảnh sát bảng (trên/dưới), 2 bảng liền nhau
- câu ngày cập nhật giá không phải hôm nay
- thiếu mục Mua / box Lý do nên mua / box Bài viết liên quan / kết bài in nghiêng có hotline
- 1 URL nội bộ link 2 lần trong thân bài (trừ box liên quan, Mua)
--link: HEAD mọi link + ảnh (viet-blog kiem_link.py), link chết là LỖI.
- đoạn <p> dài hơn 400 ký tự (> 4 dòng desktop, tách theo ý, user chốt 30/10/2026)
CẢNH BÁO: đoạn thân bài < 150 ký tự (nội dung mỏng, có phải câu chung chung?), 2 heading liền nhau đều không ảnh (ngoài FAQ), chữ dày > 1.500 ký tự không ảnh/bảng chen.
Site lấy từ bai.json cạnh file (mặc định TGDĐ). TopZone: hotline tel:1900969642, mục Mua cần list kênh mua topzone.vn (không box
"Lý do nên mua"), box "Xem thêm các bài viết liên quan", link nội bộ chỉ topzone.vn, không tô màu (color/background ngoài caption #777777).
"""
import html as H_, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *

BLOCK = re.compile(r'<(h2|h3|h4|p|ul|figure|div)\b[^>]*>.*?</\1>', re.S)
DAC_DIEM = re.compile(r'có gì mới|tại sao|đặc điểm|điểm nổi bật|nên mua .* (lúc|thời điểm) này', re.I)
FAQ = re.compile(r'câu hỏi|thắc mắc|hỏi đáp', re.I)


def chu(s): return re.sub(r'\s+', ' ', H_.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def tach_block(s):
    """Tách block cấp cao nhất (div lồng nhau tính 1 block)."""
    ra, i = [], 0
    while i < len(s):
        m = re.compile(r'<(h2|h3|h4|p|ul|figure|div)\b').search(s, i)
        if not m: break
        tag, dau, d, j = m.group(1), m.start(), 1, m.end()
        it = re.compile(r'<(/?)%s\b' % tag)
        while d:
            k = it.search(s, j)
            if not k: j = len(s); break
            d += -1 if k.group(1) else 1; j = k.end()
        end = s.find('>', j) + 1
        blk = s[dau:end]
        loai = tag
        if tag == 'figure' and 'class="image"' in blk[:40]: loai = 'anh'
        elif tag == 'p' and re.match(r'<p[^>]*>\s*<img\b', blk): loai = 'anh'
        elif tag == 'div' and '<iframe' in blk and '<table' not in blk: loai = 'video'
        elif tag == 'figure' and 'class="media"' in blk[:40]: loai = 'video'
        elif tag == 'div' and '<table' in blk: loai = 'table'
        elif tag == 'div' and ('📖' in blk or 'Xem thêm các bài viết liên quan' in blk): loai = 'lienquan'
        elif tag == 'div' and 'Lý do nên mua' in blk: loai = 'mua'
        elif tag == 'ul' and 'Cửa hàng trực tuyến' in blk: loai = 'mua'
        elif tag == 'p' and 'titleOfImages' in blk[:60]: loai = 'caption'
        ra.append((loai, blk)); i = end
    return ra


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    p = os.path.abspath(os.path.expanduser(a[0]))
    f = os.path.join(p, 'bai_pim.html') if os.path.isdir(p) else p
    s = open(f).read()
    st = site_cua(doc_json(os.path.join(os.path.dirname(f), 'bai.json'), {})); tz_ = st['ten'] == 'TopZone'
    goc = re.escape(st['goc'])
    loi, canh = [], []
    bl = [b for b in tach_block(s) if b[0] != 'caption']
    text = chu(s)
    # khung
    if not bl or bl[0][0] != 'h2': loi.append('block đầu phải là <h2> sapo')
    if len(re.findall(r'<h2\b', s)) != 1: loi.append('phải đúng 1 <h2>, đang có %d' % len(re.findall(r'<h2\b', s)))
    if re.search(r'\*\*|\]\(https?:|^#{2,4} ', text, re.M): loi.append('còn markdown sót: ' + re.search(r'.{0,30}(\*\*|\]\(https?:|#{2,4} ).{0,30}', text).group(0))
    for m in re.finditer(r'\[[^\]]{0,40}(sản phẩm|URL|TITLE|ANCHOR|NGÀY)[^\]]*\]', text): loi.append('placeholder sót: ' + m.group(0))
    # văn phong
    tx = re.sub(r'&\w+;|&#\d+;', ' ', re.sub(r'<[^>]+>', ' ', s))
    for kt, ten in ((';', 'dấu ;'), ('—', 'gạch ngang dài'), ('–', 'gạch ngang dài')):
        for m in re.finditer(re.escape(kt), tx): loi.append('%s: ...%s...' % (ten, tx[max(0, m.start() - 40):m.end() + 20].strip()))
    for m in re.finditer(r'niêm yết', text, re.I): loi.append('"niêm yết": ...%s...' % text[max(0, m.start() - 50):m.end() + 20])
    # "thiết bị" hợp lệ khi nói thiết bị khác/"trên thiết bị" (on-device); gọi chính sản phẩm là "thiết bị" thì sửa thành máy/sản phẩm
    for m in re.finditer(r'thiết bị', text, re.I): canh.append('"thiết bị" (gọi SP là máy/sản phẩm?): ...%s...' % text[max(0, m.start() - 50):m.end() + 20])
    # heading
    so3, cha, trong_faq, trong_dd = 0, '', False, False
    # H3 chia H4 thì phải có từ 2 H4 trở lên (user chốt 29/10/2026), 1 H4 lẻ thì bỏ heading, để nội dung dưới H3
    cur, dem4 = '', {}
    for lo, h in bl:
        if lo == 'h3': cur = chu(h); dem4[cur] = 0
        elif lo == 'h4' and cur: dem4[cur] += 1
    for k, v in dem4.items():
        if v == 1: loi.append('H3 chỉ có 1 H4 con (phải từ 2 trở lên, không thì bỏ H4): "%s"' % k[:70])
    for lo, h in bl:
        if lo == 'h3':
            t = chu(h); so3 += 1
            m = re.match(r'^(\d+)\.\s', t)
            if not m or int(m.group(1)) != so3: loi.append('H3 phải đánh số %d.: "%s"' % (so3, t[:70]))
            cha = m.group(1) if m else ''
            trong_faq, trong_dd = bool(FAQ.search(t)), bool(DAC_DIEM.search(t))
        elif lo == 'h4':
            t = chu(h)
            m = re.match(r'^(\d+)\.(\d+)\.\s', t)
            if trong_faq:
                if re.match(r'^\d', t): loi.append('H4 FAQ không đánh số: "%s"' % t[:70])
            elif m and m.group(1) != cha: loi.append('H4 "%s" sai tiền tố, H3 cha là %s.' % (t[:60], cha))
            if trong_dd:
                core = re.sub(r'^\d+\.\d+\.\s*', '', t)
                if ':' in core: loi.append('H4 đặc điểm có dấu ":" (rule heading SEO, không giải thích): "%s"' % core)
                if len(core.split()) > 18: loi.append('H4 đặc điểm quá dài (%d từ): "%s"' % (len(core.split()), core))
            if '<strong' in h and not tz_: canh.append('H4 có <strong> (CSS đã đậm, không cần): "%s"' % t[:60])
    # độ dài đoạn: tối đa 4 dòng desktop (~100 ký tự/dòng), user chốt 30/10/2026
    for lo, h in bl:
        if lo != 'p': continue
        t_ = chu(h); n_ = len(t_)
        if n_ > 400: loi.append('đoạn dài %d ký tự (> 4 dòng desktop, tách theo ý): "%s..."' % (n_, t_[:60]))
        elif n_ < 150 and not t_.endswith(':') and 'cập nhật ngày' not in t_ and not re.search(r'tel:', h): canh.append('đoạn mỏng %d ký tự (câu chung chung?): "%s"' % (n_, t_[:70]))
    # ảnh / bảng
    anh = [k for k, (lo, _) in enumerate(bl) if lo == 'anh']
    if len(anh) < 3: loi.append('ít hơn 3 ảnh (%d)' % len(anh))
    for k in range(len(bl) - 1):
        a1, a2 = bl[k][0], bl[k + 1][0]
        if {a1, a2} == {'video', 'table'}: loi.append('video sát bảng (cần đoạn văn ở giữa): "%s"' % chu(bl[k][1] if a1 == 'table' else bl[k + 1][1])[:60])
        if {a1, a2} == {'anh', 'table'}: loi.append('ảnh sát bảng quanh: "%s"' % chu(bl[k][1] if a1 == 'table' else bl[k + 1][1])[:60])
        if a1 == a2 == 'table': loi.append('2 bảng liền nhau, cần đoạn văn ở giữa: "%s"' % chu(bl[k][1])[:60])
    # phân bổ ảnh (cảnh báo)
    muc, trong_faq = [], False
    for lo, h in bl:
        if lo == 'h3': trong_faq = bool(FAQ.search(chu(h)))
        if lo in ('h3', 'h4') and not trong_faq: muc.append([chu(h)[:50], False])
        elif lo in ('anh', 'video') and muc: muc[-1][1] = True
    for x, y in zip(muc, muc[1:]):
        if not x[1] and not y[1]: canh.append('2 heading liền không ảnh: "%s" / "%s"' % (x[0], y[0]))
    dai = 0
    for lo, h in bl:
        if lo in ('p', 'ul'): dai += len(chu(h))
        elif lo in ('anh', 'video', 'table'): dai = 0
        if dai > 1500: canh.append('chữ dày > 1.500 ký tự không ảnh/bảng, tới: "%s"' % chu(h)[:50]); dai = 0
    # ngày giá
    for m in re.finditer(r'cập nhật ngày\s*(\d{1,2}/\d{1,2}/\d{4})', text):
        if m.group(1) != hom_nay(): loi.append('ngày cập nhật %s, phải %s' % (m.group(1), hom_nay()))
    if 'cập nhật ngày' not in text: loi.append('thiếu câu "Giá ... cập nhật ngày ..." sau mục giá')
    # khối bắt buộc
    if not any(lo == 'h3' and re.search(r'\bmua\b.*(ở đâu|thế giới di động|tgdđ|topzone)', chu(h), re.I) for lo, h in bl): loi.append('thiếu H3 Mua ... ở đâu chính hãng, uy tín, giá tốt?')
    if not any(lo == 'mua' for lo, _ in bl):
        loi.append('thiếu list kênh mua "Cửa hàng trực tuyến: topzone.vn" sau mục Mua' if tz_ else 'thiếu box "Lý do nên mua ... tại Thế Giới Di Động"')
    if not any(lo == 'lienquan' for lo, _ in bl): loi.append('thiếu box "%s"' % ('Xem thêm các bài viết liên quan' if tz_ else '📖 Bài viết liên quan'))
    if not re.search(r'<p[^>]*><(i|em)>(?:(?!</p>).)*tel:%s' % st['tel'], s): loi.append('thiếu kết bài in nghiêng có hotline %s' % st['hotline'])
    if tz_:
        for m in re.finditer(r'(?<![-\w])(color|background(-color)?)\s*:\s*([^;"]+)', s):
            if m.group(3).strip().lower() != '#777777': loi.append('TopZone không tô màu: "%s"' % m.group(0)[:60])
        for u in re.findall(r'<a [^>]*href="(https?://[^"]+)"', s):
            if re.search(r'thegioididong\.com|dienmayxanh\.com', u): loi.append('bài TopZone link sang site khác: %s' % u)
        if re.search(r'Thế Giới Di Động|1900 232 460|thegioididong', chu(s), re.I): loi.append('bài TopZone còn nhắc Thế Giới Di Động/hotline TGDĐ')
    # link lặp trong thân
    than = ''.join(h for lo, h in bl if lo not in ('lienquan', 'mua'))
    dem = {}
    for u in re.findall(r'<a [^>]*href="(%s[^"#?]*)"' % goc, than): dem[u.rstrip('/')] = dem.get(u.rstrip('/'), 0) + 1
    for u, c in dem.items():
        if c > 1 and not re.search('he-thong-(sieu-thi|cua-hang)', u) and u != st['goc']: loi.append('link lặp %d lần: %s' % (c, u))
    if '--link' in a:
        r = subprocess.run([sys.executable, os.path.join(VB, 'kiem_link.py'), f], capture_output=True, text=True)
        print(r.stdout.strip()[-1500:])
        if re.search(r'chết [1-9]', r.stdout): loi.append('có link chết (xem trên)')
        for u in re.findall(r'<img [^>]*src="([^"]+)"', s):
            try: fetch(u, head=True)
            except Exception as e: loi.append('ảnh lỗi %s: %s' % (u, e))
    print('%s: %d block, %d ảnh, %d bảng, %d H3, %d link nội bộ' % (os.path.basename(f), len(bl), len(anh), sum(lo == 'table' for lo, _ in bl),
          sum(lo == 'h3' for lo, _ in bl), len(dem)))
    if canh: print('CẢNH BÁO:\n- ' + '\n- '.join(dict.fromkeys(canh)))
    if loi: print('LỖI:\n- ' + '\n- '.join(dict.fromkeys(loi))); sys.exit(1)
    print('OK')


if __name__ == '__main__':
    main()
