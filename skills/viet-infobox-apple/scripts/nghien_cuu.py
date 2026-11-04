#!/usr/bin/env python3
"""Bước 1: thu nguyên liệu outline + dữ kiện cho 1 việc infobox.

  python3 nghien_cuu.py <thư mục việc>

Ghi vào thư mục việc:
- tgdd.json: listing trang đích (SP, giá, urlInfo) bằng viet-blog tgdd.py lay.
- nguon_outline.json: heading H2-H4 của trang CellphoneS (cột URL CellphoneS) và infobox TGDĐ dòng trước
  (cột URL infobox dòng trước), bỏ heading thẻ sản phẩm/khung listing.
- goi_y.json: Google gợi ý cho keyword + kw phụ (viet-blog goi_y.py).
- research.json: khung {du_kien: [], paa: [], gsc: []} nếu chưa có. Claude điền du_kien (Apple VN, Newsroom,
  trang TGDĐ, nguồn nước ngoài uy tín, mỗi ý kèm nguồn) và gsc (MCP gscServer get_advanced_search_analytics,
  page = URL trang, 28 ngày, query có impression).
Cột trống thì bỏ qua nguồn đó và in nhắc Claude tự tìm.
"""
import html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *

BO = re.compile(r'^(danh sách sản phẩm|thông tin ngành hàng|bộ lọc|sản phẩm (đã xem|tương tự)|tin tức|đánh giá|hỏi đáp|xem thêm)', re.I)
THE_SP = re.compile(r'\b\d+\s?(GB|TB)\b(\s*\|.*)?$|\|\s*Chính hãng', re.I)


def heading(url):
    try: s = fetch(url)
    except Exception as e: return {'url': url, 'loi': str(e)[:200], 'h': []}
    hs = []
    for m in re.finditer(r'<(h[2-4])[^>]*>(.*?)</\1>', s, re.S):
        t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))).strip()
        if not t or BO.match(t) or (THE_SP.search(t) and len(t) < 60): continue
        hs.append([m.group(1), t[:200]])
    return {'url': url, 'h': hs}


def tz_listing(url):
    """Listing TopZone không có ItemList: đọc card (data-name, data-price, href) → cùng khuôn tgdd.json (mỗi card 1 product)."""
    h = fetch(url)
    ra = [{'url': url, 'title': (re.search(r'<title>(.*?)</title>', h, re.S) or [None, ''])[1].strip(), 'list': [], 'product': None}]
    for m in re.finditer(r"<a href='(/[^']+)'[^>]*data-name=\"([^\"]+)\"[^>]*data-price=\"([\d.]+)\"", h):
        u, ten, gia = 'https://www.topzone.vn' + m.group(1), m.group(2), float(m.group(3))
        if any(x['product'] and x['product']['url'] == u for x in ra): continue
        txt = '{:,.0f}đ'.format(gia).replace(',', '.') if gia else 'Liên hệ'
        ra[0]['list'].append({'url': u, 'ten': ten, 'gia': gia})
        ra.append({'url': u, 'product': {'ten': ten, 'url': u, 'thong_so': None, 'phien_ban': [{'size': ten, 'gia': gia, 'gia_text': txt, 'url': u}]}})
    return ra


def main(tm):
    bai = doc_json(os.path.join(tm, 'bai.json'))
    if not bai: raise SystemExit('chưa có bai.json, chạy tao_viec.py trước')
    py = sys.executable
    tj = os.path.join(tm, 'tgdd.json')
    if ten_site(bai.get('site')) == 'TopZone':
        d = tz_listing(bai['url']); ghi_json(tj, d)
        print('tgdd.json (TopZone): %d sản phẩm trên listing, giá lấy từ card' % len(d[0]['list']))
    else: tgdd_lay(py, bai, tj)
    nguon(tm, bai, py)


def tgdd_lay(py, bai, tj):
    r = subprocess.run([py, os.path.join(VB, 'tgdd.py'), 'lay', bai['url'], '-o', tj], capture_output=True, text=True)
    # Listing không có giá: lấy thêm từng trang SP (giá từng dung lượng) của listing, tối đa 20 trang
    ds = (doc_json(tj, [{}]) or [{}])[0].get('list') or []
    sp = list(dict.fromkeys(x['url'] for x in ds if x.get('url')))[:20]
    if sp:
        r = subprocess.run([py, os.path.join(VB, 'tgdd.py'), 'lay', bai['url']] + sp + ['-o', tj], capture_output=True, text=True)
    print('tgdd.json: listing + %d trang SP. %s' % (len(sp), (r.stdout or r.stderr).strip()[-200:]))


def nguon(tm, bai, py):
    ng = {}
    nhac = []
    for k, cot in (('cps', 'url_cps'), ('tgdd_truoc', 'url_truoc')):
        if bai.get(cot):
            ng[k] = heading(bai[cot]); print('%s: %d heading%s' % (k, len(ng[k]['h']), (' LỖI ' + ng[k]['loi']) if ng[k].get('loi') else ''))
        else: nhac.append(cot)
    ghi_json(os.path.join(tm, 'nguon_outline.json'), ng)
    r = subprocess.run([py, os.path.join(VB, 'goi_y.py'), bai['keyword']] + bai.get('kw_phu', [])[:3], capture_output=True, text=True)
    try: gy = json.loads(r.stdout[r.stdout.find('{'):] if '{' in r.stdout else r.stdout[r.stdout.find('['):])
    except Exception: gy = r.stdout.strip().splitlines()
    ghi_json(os.path.join(tm, 'goi_y.json'), gy)
    print('goi_y.json:', len(gy.get('tong_hop', [])) if isinstance(gy, dict) else len(gy), 'truy vấn gợi ý')
    rp = os.path.join(tm, 'research.json')
    if not os.path.exists(rp): ghi_json(rp, {'du_kien': [], 'paa': [], 'gsc': []})
    if bai.get('outline_user'):
        print('OUTLINE USER: %s có sẵn → dùng làm khung outline.md (giữ heading/thứ tự của user, chỉ bổ sung nguồn, kw GSC, mục bắt buộc còn thiếu)' % bai['outline_user'])
    if nhac: print('NHẮC: cột %s trống → Claude tự tìm trang CellphoneS / infobox TGDĐ dòng liền trước tương ứng, rồi chạy lại.' % ', '.join(nhac))
    print('TIẾP: Claude kéo GSC (page=%s) vào research.json.gsc, điền du_kien có nguồn, rồi dựng outline.md theo references/outline-infobox.md' % bai['url'])


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit()
    main(os.path.abspath(os.path.expanduser(sys.argv[1])))
