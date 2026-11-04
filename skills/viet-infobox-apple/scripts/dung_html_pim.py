#!/usr/bin/env python3
"""Bước 6: bai.md (đã chèn link, Claude duyệt) → HTML dán field infobox PIM (CKEditor 5), đúng format đo trên live.

  python3 dung_html_pim.py <thư mục việc> [-o bai_pim.html]

Đọc: bai.md, bai.json (ten_muc_mua, ten_box, lien_quan [{url,title,anchor}]),
     anh/ke-hoach-anh.json [{"file","sau_doan","alt","nguon"="Apple"}] + anh/anh-cdn.json (nếu có).
Tự làm: sapo <h2>, heading không bold, bảng figure.table (thead đen chữ vàng), list, câu ngày cập nhật giá
(đổi ngày về HÔM NAY), box vàng "Lý do nên mua" + kênh mua sau các đoạn của mục Mua, [VIDEO url] → embed,
kết bài in nghiêng + hotline, box "📖 Bài viết liên quan", ảnh figure.image + caption "... Nguồn: X".
Format chi tiết: references/dinh-dang-pim.md. Chạy kiem_pim.py ngay sau.
Site TopZone (bai.json site): format TinyMCE của bài News infobox TopZone (đo trên 1598413): style inline margin, H4 <strong>,
ảnh <p><img>, bảng viền xám không tô màu, mục Mua = đoạn văn + list kênh mua topzone.vn/1900.9696.42 (không box vàng),
box "Xem thêm các bài viết liên quan" viền xám, kết bài <em>.
"""
import html as H_, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *
from dung_html import parse_md, inline, esc, esca   # viet-blog

SIEU_THI = 'https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong'
NGAY_RE = re.compile(r'(cập nhật ngày\s*)\d{1,2}/\d{1,2}/\d{4}')
TEL_RE = re.compile(r'<a href="tel:(\d+)">([^<]+)</a>')
TH = 'background-color:#000000;border-color:#cccccc;box-sizing:border-box;color:#ffe14c;overflow-wrap:anywhere;padding:8px 10px;text-align:center;vertical-align:middle;white-space:normal;width:%s%%;word-break:break-word;'
TD = 'border-color:#cccccc;box-sizing:border-box;overflow-wrap:anywhere;padding:8px 10px;text-align:left;vertical-align:middle;white-space:normal;word-break:break-word;'
TD_SO = 'border-color:#cccccc;box-sizing:border-box;padding:8px 10px;text-align:center;vertical-align:middle;white-space:nowrap;'
LA_MUA = re.compile(r'^mua\s+.+(ở đâu|tại (thế giới di động|tgdđ|topzone))', re.I)
SO_RE = re.compile(r'^\s*(\*\*)?[\d.,]+\s?(đ|₫|triệu|tr)?(\*\*)?\s*$', re.I)


def chu(s):
    return re.sub(r'\s+', ' ', H_.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def bo_so(t):
    return re.sub(r'^\d+(\.\d+)*\.\s*', '', t).strip()


def table_pim(rows):
    n = max(len(r) for r in rows)
    head = rows[0] + [''] * (n - len(rows[0]))
    la_gia = [j > 0 and bool(re.search('giá', re.sub(r'\*', '', c), re.I)) for j, c in enumerate(head)]
    w = [40] + [round(60 / (n - 1))] * (n - 1) if n > 1 else [100]
    th = ''.join('<th style="%s"><strong>%s</strong></th>' % (TH % w[j], re.sub(r'</?strong>', '', inline(c))) for j, c in enumerate(head))
    body = ''
    for r in rows[1:]:
        r = r + [''] * (n - len(r))
        body += '<tr>' + ''.join('<td style="%s">%s</td>' % (TD_SO if (la_gia[j] or (j and SO_RE.match(c))) else TD, inline(c)) for j, c in enumerate(r)) + '</tr>'
    return ('<div style="-webkit-overflow-scrolling:touch;box-sizing:border-box;margin:16px 0;max-width:100%;overflow-x:auto;width:100%;">'
            '<figure class="table" style="max-width:100%;min-width:620px;width:100%;"><table style="border-collapse:collapse;color:#333333;font-size:14px;line-height:1.5;margin:0;table-layout:fixed;">'
            '<thead><tr>' + th + '</tr></thead><tbody>' + body + '</tbody></table></figure></div>')


def ital(t, ket):
    t = NGAY_RE.sub(lambda m: m.group(1) + hom_nay(), t)
    v = inline(t)
    if ket:
        v = TEL_RE.sub(lambda m: '</i><a style="color:#d9381e;text-decoration:none;white-space:nowrap;" href="tel:%s"><i><strong>%s</strong></i></a><i>' % (m.group(1), m.group(2)), v)
    else:
        v = TEL_RE.sub(lambda m: '</i><a href="tel:%s" title="%s"><i>%s</i></a><i>' % (m.group(1), m.group(2), m.group(2)), v)
    return ('<p><i>' + v + '</i></p>').replace('<i></i>', '')


def video(u):
    m = re.search(r'(?:youtu\.be/|v=|embed/)([\w-]{11})', u)
    if not m: return ''
    return ('<figure class="media"><div data-oembed-url="%s"><div style="position:relative;height:0;padding-bottom:56.2493%%;">'
            '<iframe src="https://www.youtube.com/embed/%s" style="position:absolute;width:100%%;height:100%%;top:0;left:0;" frameborder="0" '
            'allow="autoplay; encrypted-media" allowfullscreen=""></iframe></div></div></figure>') % (esca(u), m.group(1))


def mua_box(ten):
    li = ['<strong>%s chính hãng</strong>, có thông tin nguồn gốc, giá bán và chính sách bảo hành rõ ràng.' % esc(ten),
          '<strong>Giá bán minh bạch</strong>, dễ kiểm tra theo từng phiên bản, màu sắc và dung lượng.',
          'Thường xuyên có ưu đãi giảm giá, ưu đãi thanh toán hoặc phiếu mua hàng tùy phiên bản và thời điểm.',
          'Hỗ trợ <strong>trả góp và thu cũ đổi mới</strong>, giúp giảm số tiền cần thanh toán ban đầu theo điều kiện áp dụng.',
          'Hỗ trợ bảo hành, đổi trả và tư vấn kỹ thuật theo chính sách áp dụng tại thời điểm mua hàng.',
          '<a title="Hệ thống siêu thị Thế Giới Di Động" href="%s" target="_blank" rel="noopener">Hệ thống siêu thị Thế Giới Di Động</a> rộng khắp, thuận tiện để xem máy, nhận hàng, bảo hành hoặc yêu cầu hỗ trợ trực tiếp.' % SIEU_THI,
          'Có thể đặt hàng online, chọn giao tận nơi hoặc nhận tại siêu thị tùy tình trạng sản phẩm ở từng khu vực.']
    return ('<div style="width:100%;max-width:100%;margin:14px 0;padding:14px 16px;background-color:#fff9e6;border:1px solid #f2c94c;border-left:5px solid #f5b700;border-radius:8px;box-sizing:border-box;color:#222222;font-size:15px;line-height:1.6;">'
            '<p style="margin:0 0 10px 0;padding:0 0 8px 0;border-bottom:1.5px solid #ebd27b;font-size:18px;line-height:1.4;font-weight:bold;color:#111111;">Lý do nên mua {ten} tại Thế Giới Di Động</p>'
            '<ul>{li}</ul></div>'
            '<p style="margin:16px 0 8px 0;font-weight:bold;color:#222222;font-size:15px;line-height:1.6;">Bạn có thể kiểm tra giá và đặt mua {ten} qua các kênh:</p>'
            '<ul style="margin:0;padding-left:20px;font-size:15px;line-height:1.6;"><li style="margin-bottom:6px;">Cửa hàng trực tuyến: '
            '<a style="color:#0066cc;font-weight:600;" title="Thế Giới Di Động" href="https://www.thegioididong.com/" target="_blank" rel="noopener">thegioididong.com</a></li>'
            '<li>Hotline tư vấn và hỗ trợ khách hàng: <a style="color:#d9381e;font-weight:bold;text-decoration:none;" href="tel:{tel}">{hl}</a> (8:00 - 21:30)</li></ul>'
            ).format(ten=esc(ten), li=''.join('<li>%s</li>' % x for x in li), tel=HOTLINE_TEL, hl=HOTLINE)


def box_lien_quan(ten, ds):
    li = ''.join('<li><a style="color:#0066cc;font-weight:500;text-decoration:none;" href="%s" title="%s" target="_blank" rel="noopener">%s</a></li>'
                 % (esca(x['url']), esca(x.get('title') or x.get('anchor')), esc(x.get('anchor') or x.get('title'))) for x in ds)
    return ('<div style="width:100%;max-width:100%;box-sizing:border-box;background-color:#fff9e6;border:1px solid #f2c94c;border-left:5px solid #f5b700;padding:14px 16px;margin:20px 0;border-radius:6px;font-size:14px;line-height:1.6;color:#333333;">'
            '<div style="margin:0 0 10px 0;padding-bottom:6px;border-bottom:1.5px solid #ebd27b;font-size:16px;font-weight:bold;color:#111111;display:flex;align-items:center;">📖 Bài viết liên quan đến {ten}</div>'
            '<div style="max-height:260px;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-right:6px;"><ul>{li}</ul></div></div>').format(ten=esc(ten), li=li)


def anh_html(a, cdn):
    c = cdn[a['file']]; w, h = int(c.get('width') or 1200), int(c.get('height') or 675)
    alt = a['alt'].rstrip('. ')
    return ('<figure class="image"><img style="aspect-ratio:%d/%d;display:block;margin-left:auto;margin-right:auto;" src="%s" alt="%s" width="%d" height="%d" title="%s"></figure>'
            '<p class="titleOfImages" style="color:#777777;font-size:15px;text-align:center;">%s. Nguồn: %s</p>') % (w, h, esca(c['src']), esca(alt), w, h, esca(alt), esc(alt), esc(a.get('nguon') or 'Apple'))


# ---- TopZone (TinyMCE, không tô màu) ----
TZ_P = '<p style="margin: 0 0 10px 0; line-height: 1.6;">%s</p>'
TZ_UL = '<ul style="margin: 0 0 10px 0; padding-left: 18px; line-height: 1.6;">%s</ul>'
TZ_TH = 'width: %s%%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;'
TZ_TD = 'box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: %s; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;'
TZ_TEL = '<a style="font-weight: bold; text-decoration: none; white-space: nowrap;" href="tel:%s">%s</a>'


def tz_heading(t, txt):
    st = {'h2': 'margin: 0 0 10px 0; line-height: 1.6;', 'h3': 'margin: 20px 0 10px 0;', 'h4': 'margin: 16px 0 8px 0;'}[t]
    v = inline(txt)
    return '<%s style="%s">%s</%s>' % (t, st, '<strong>%s</strong>' % v if t == 'h4' else v, t)


def tz_table(rows):
    n = max(len(r) for r in rows)
    head = rows[0] + [''] * (n - len(rows[0]))
    w = [40] + [round(60 / (n - 1))] * (n - 1) if n > 1 else [100]
    th = ''.join('<th style="%s">%s</th>' % (TZ_TH % w[j], re.sub(r'</?strong>', '', inline(c))) for j, c in enumerate(head))
    body = ''
    for r in rows[1:]:
        r = r + [''] * (n - len(r))
        body += '<tr>' + ''.join('<td style="%s">%s</td>' % (TZ_TD % ('center' if j and SO_RE.match(c) else 'left'), inline(c)) for j, c in enumerate(r)) + '</tr>'
    return ('<div style="width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; box-sizing: border-box;">'
            '<table style="width: 100%; min-width: 620px; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5;">'
            '<tbody><tr>' + th + '</tr>' + body + '</tbody></table></div>')


def tz_ital(t, st):
    t = NGAY_RE.sub(lambda m: m.group(1) + hom_nay(), t)
    v = TEL_RE.sub(lambda m: '</em>' + TZ_TEL % (m.group(1), m.group(2)) + '<em>', inline(t))
    return ('<p style="margin: 0 0 10px 0; line-height: 1.6;"><em>' + v + '</em></p>').replace('<em></em>', '')


def tz_video(u):
    m = re.search(r'(?:youtu\.be/|v=|embed/)([\w-]{11})', u)
    if not m: return ''
    return ('<div style="position: relative; width: 100%%; padding-bottom: 56.25%%; height: 0; overflow: hidden; margin: 16px 0;">'
            '<iframe style="position: absolute; top: 0; left: 0; width: 100%%; height: 100%%; border: 0;" title="YouTube video" '
            'src="https://www.youtube.com/embed/%s" width="560" height="314" frameborder="0" allowfullscreen="allowfullscreen"></iframe></div>') % m.group(1)


def tz_kenh_mua(st):
    return TZ_UL % ('<li><strong>Cửa hàng trực tuyến</strong>: <a href="https://www.topzone.vn" target="_blank" rel="noopener noreferrer">topzone.vn</a></li>'
                    '<li><strong>Hotline tư vấn và hỗ trợ khách hàng</strong>: ' + TZ_TEL % (st['tel'], st['hotline']) + ' (8:00 - 21:30)</li>')


def tz_lien_quan(ds):
    li = ''.join('<li><a href="%s" target="_blank" rel="noopener">%s</a></li>' % (esca(x['url']), esc(x.get('anchor') or x.get('title'))) for x in ds)
    return ('<div style="width: 100%; max-width: 100%; box-sizing: border-box; border: 1px solid #cccccc; border-left: 5px solid #cccccc; padding: 14px 16px; margin: 20px 0; border-radius: 6px; font-size: 14px; line-height: 1.6;">'
            '<div style="margin: 0 0 10px 0; padding-bottom: 6px; border-bottom: 1px solid #cccccc; font-size: 16px; font-weight: bold;">Xem thêm các bài viết liên quan</div>'
            '<div style="max-height: 320px; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-right: 6px;"><ul style="margin: 0; padding-left: 18px;">' + li + '</ul></div></div>')


def tz_anh(a, cdn):
    c = cdn[a['file']]; w, h = int(c.get('width') or 1200), int(c.get('height') or 675)
    alt = a['alt'].rstrip('. ')
    return ('<p><img style="display: block; margin-left: auto; margin-right: auto;" title="%s" src="%s" alt="%s" width="%d" height="%d" /></p>'
            '<p class="titleOfImages" style="font-size: 15px; color: #777777; text-align: center;">%s. Nguồn: %s</p>') % (esca(alt), esca(c['src']), esca(alt), w, h, esc(alt), esc(a.get('nguon') or 'Apple'))


def ul_html(items, tz_):
    noi = ''.join('<li>%s%s</li>' % (a, ('<ul>' + ''.join('<li>%s</li>' % c for c in con) + '</ul>') if con else '') for a, con in items)
    return TZ_UL % noi if tz_ else '<ul>' + noi + '</ul>'


def dung(tm):
    bai = doc_json(os.path.join(tm, 'bai.json'))
    st = site_cua(bai); tz_ = st['ten'] == 'TopZone'
    md = open(os.path.join(tm, 'bai.md')).read()
    bl = parse_md(md)
    ra = []   # [(loai, html)]
    i, n = 0, len(bl)
    trong_mua, ten_mua = False, bai.get('ten_muc_mua') or ''
    co_ket = max([k for k, b in enumerate(bl) if b['type'] == 'ital' and 'cập nhật ngày' not in b['text']] or [-1])

    def dong_mua():
        nonlocal trong_mua
        if trong_mua: ra.append(('mua', tz_kenh_mua(st) if tz_ else mua_box(ten_mua or bai['keyword']))); trong_mua = False

    while i < n:
        b = bl[i]; t = b['type']
        if t in ('h2', 'h3', 'h4'):
            if t in ('h2', 'h3'): dong_mua()
            txt = re.sub(r'\*\*', '', b['text'])
            if t == 'h3' and LA_MUA.search(bo_so(txt)):
                trong_mua = True
                if not ten_mua:
                    m = re.search(r'^mua\s+(.+?)\s+(ở đâu|chính hãng|tại)', bo_so(txt), re.I)
                    ten_mua = m.group(1) if m else bai['keyword']
            ra.append((t, tz_heading(t, txt) if tz_ else '<%s>%s</%s>' % (t, inline(txt), t)))
        elif t == 'li':
            items = []
            while i < n and bl[i]['type'] == 'li':
                x = bl[i]
                if x['mark'] == '+' and items: items[-1][1].append(inline(x['text']))
                else: items.append([inline(x['text']), []])
                i += 1
            ra.append(('ul', ul_html(items, tz_)))
            continue
        elif t == 'table': ra.append(('table', tz_table(b['rows']) if tz_ else table_pim(b['rows'])))
        elif t == 'ital': ra.append(('ket' if i == co_ket else 'gia', tz_ital(b['text'], st) if tz_ else ital(b['text'], i == co_ket)))
        elif t == 'p':
            m = re.match(r'^\[VIDEO\s+(\S+)\]$', b['text'], re.I)
            if m: ra.append(('video', tz_video(m.group(1)) if tz_ else video(m.group(1))))
            else: ra.append(('p', TZ_P % inline(b['text']) if tz_ else '<p>%s</p>' % inline(b['text'])))
        elif t == 'sc': print('BỎ shortcode (PIM không dùng):', b['text'][:80], file=sys.stderr)
        i += 1
    dong_mua()
    # ảnh
    kp, kc = os.path.join(tm, 'anh', 'ke-hoach-anh.json'), os.path.join(tm, 'anh', 'anh-cdn.json')
    if os.path.exists(kp):
        plan, cdn = doc_json(kp, []), doc_json(kc, {})
        for a in plan:
            if a['file'] not in cdn: raise SystemExit('ảnh %s chưa có trong anh-cdn.json (chạy up_anh.mjs)' % a['file'])
            khop = [k for k, (lo, h) in enumerate(ra) if a['sau_doan'] in chu(h)]
            if len(khop) != 1: raise SystemExit('sau_doan "%s" khớp %d block, cần đúng 1' % (a['sau_doan'][:50], len(khop)))
            ra.insert(khop[0] + 1, ('anh', tz_anh(a, cdn) if tz_ else anh_html(a, cdn)))
    if bai.get('lien_quan'):
        ra.append(('lienquan', tz_lien_quan(bai['lien_quan']) if tz_ else box_lien_quan(bai.get('ten_box') or ten_mua or bai['keyword'], bai['lien_quan'])))
    else: print('CẢNH BÁO: bai.json chưa có lien_quan → thiếu box Bài viết liên quan', file=sys.stderr)
    return ra


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    tm = os.path.abspath(os.path.expanduser(a[0]))
    out = a[a.index('-o') + 1] if '-o' in a else os.path.join(tm, 'bai_pim.html')
    ra = dung(tm)
    open(out, 'w').write(''.join(h for _, h in ra))
    dem = {}
    for lo, _ in ra: dem[lo] = dem.get(lo, 0) + 1
    print('%s: %d ký tự | %s' % (out, os.path.getsize(out), ', '.join('%s %d' % kv for kv in dem.items())))
