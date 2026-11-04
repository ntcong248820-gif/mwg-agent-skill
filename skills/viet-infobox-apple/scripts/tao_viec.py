#!/usr/bin/env python3
"""Bước 0: nhận dòng tab skill_infobox → thư mục việc + tra bản ghi PIM.

  python3 tao_viec.py <số dòng> [<số dòng>...]     hoặc   python3 tao_viec.py --run   (mọi dòng Status = Run)

Mỗi dòng: kiểm cột bắt buộc (URL trang, Dạng trang, Keyword), tạo ~/viet-content-infobox/infobox-pim/<slug>/,
ghi bai.json (dữ liệu dòng + nơi ghi), sheet: Status=Doing, Bản ghi PIM. Không ghi gì lên PIM/CMS.
- Site TGDĐ: mdm lookup URL → lookup.json (noi_ghi = pim). Lookup lỗi → Status=Lỗi + Cảnh báo.
- Site TopZone: chưa qua PIM, còn CMS. Mọi dạng trang → noi_ghi = tz_news (bài News CMS TGDĐ site 1 chuyên mục 2424,
  Dòng filter Xuất bản, Hãng/Filter Chờ duyệt; user tự khai báo ID ở CMS cũ). Trang live đã có infobox → báo như PIM (skill chỉ viết mới).
- Cột Ghi chú có dạng outline (≥ 3 dòng heading: "#", "H3:", "1.", "1.1.", "-") → lưu outline_user.md, bước outline lấy làm khung.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *

KW_FIELD = {'brand': 'seo_keyword', 'filter-value': 'main_keyword', 'category': 'seo_keyword'}
DONG_HEADING = re.compile(r'^\s*(#{1,4}\s|H[2-4]\s*[:.\-)]|\d+(\.\d+)*[.)]\s|[-*•+]\s)', re.I)


def la_outline(t):
    dong = [x for x in str(t or '').splitlines() if x.strip()]
    return len(dong) >= 3 and sum(bool(DONG_HEADING.match(x)) for x in dong) >= 3


def tz_hien_tai(url):
    """Infobox đang chạy trên trang TopZone: (newsId hay '', số ký tự chữ). Khối nằm sau <!--Bài viết sale-->."""
    try: h = fetch(url)
    except Exception as e: return '', -1
    i = h.find('<!--Bài viết sale-->')
    if i < 0: return '', 0
    k = h.find('<div class="bg-article', i)
    khoi = h[i:k if k > 0 else i + 400000]
    ids = re.findall(r'common/News/(\d{6,})/', khoi)
    chu = re.sub(r'<[^>]+>', ' ', khoi)
    return (max(set(ids), key=ids.count) if ids else ''), len(re.sub(r'\s+', ' ', chu).strip())


def bai_chung(n, d, site, path, slug, dang, kw):
    return {
        'dong': n, 'site': site, 'url': SITES[site]['goc'] + path, 'path': path, 'slug': slug,
        'dang_trang': dang, 'keyword': kw, 'kw_phu': tach(d.get('KW phụ (ko bắt buộc)')),
        'url_cps': d.get('URL CellphoneS (ko bắt buộc)', '').strip(), 'url_truoc': d.get('URL infobox dòng trước (ko bắt buộc)', '').strip(),
        'link_tk': tach(d.get('Link tham khảo (ko bắt buộc)')), 'ghi_chu': d.get('Ghi chú (ko bắt buộc)', '').strip(),
        'title': '', 'meta': '', 'lien_quan': [], 'ngay': hom_nay(),
    }


def luu(tm, bai):
    cu = doc_json(os.path.join(tm, 'bai.json'), {})
    for k in ('title', 'meta', 'lien_quan', 'ten_muc_mua', 'ten_box', 'ten'):   # giữ phần Claude đã điền nếu chạy lại
        if cu.get(k): bai[k] = cu[k]
    if (cu.get('cms') or {}).get('news_id') and bai.get('cms') is not None and not bai['cms'].get('news_id'):
        bai['cms']['news_id'] = cu['cms']['news_id']   # bài News TopZone đã tạo ở lần chạy trước → cập nhật, không tạo trùng
    if la_outline(bai['ghi_chu']):
        open(os.path.join(tm, 'outline_user.md'), 'w').write(bai['ghi_chu'].strip() + '\n')
        bai['outline_user'] = 'outline_user.md'
    ghi_json(os.path.join(tm, 'bai.json'), bai)


def lam_tz(n, d, path, slug, dang, kw, tm):
    bai = bai_chung(n, d, 'TopZone', path, slug, dang, kw)
    bai['ten'] = kw
    canh = []
    nid, dai = tz_hien_tai(bai['url'])
    bai['noi_ghi'] = 'tz_news'
    bai['cms'] = {'loai': 'News site 1, chuyên mục 2424', 'news_id': '', 'news_dang_gan': nid, 'bai_hien_tai_len': max(dai, 0)}
    if dai < 0: canh.append('không tải được trang live để kiểm infobox đang chạy')
    ghi_ban = 'CMS TGDĐ News 2424 (tạo mới khi ghi, %s; user khai báo ID ở CMS cũ)' % ('Xuất bản' if dang == 'Dòng filter' else 'Chờ duyệt')
    if nid: ghi_ban = 'TopZone: trang đang gắn News %s' % nid
    luu(tm, bai)
    ghi_dong(n, {'Status': 'Doing', 'Bản ghi PIM': ghi_ban, 'Cảnh báo': ' | '.join(canh), 'Cập nhật': hom_nay()})
    print('dòng %d → %s\n  %s%s%s' % (n, tm, ghi_ban, ('\n  LƯU Ý: ' + ' | '.join(canh)) if canh else '',
          '\n  outline user → outline_user.md' if bai.get('outline_user') else ''))
    if (bai.get('cms') or {}).get('news_dang_gan'):
        print('  CẢNH BÁO: trang đã có infobox (News %s). Skill này chỉ VIẾT MỚI: hỏi user trước khi ghi đè.' % bai['cms']['news_dang_gan'])


def lam(n):
    d = doc_dong(n)
    url, dang, kw = d.get('URL trang', '').strip(), d.get('Dạng trang', '').strip(), d.get('Keyword', '').strip()
    thieu = [k for k, v in (('URL trang', url), ('Dạng trang', dang), ('Keyword', kw)) if not v]
    if thieu:
        ghi_dong(n, {'Status': 'Pending', 'Cảnh báo': 'Thiếu cột: ' + ', '.join(thieu)}); print('dòng %d: thiếu %s' % (n, thieu)); return
    site = ten_site(d.get('Site') or url)
    path = duong_dan(url); slug = path.strip('/').split('?')[0].replace('/', '-')
    if site == 'TopZone': slug = 'tz-' + slug   # tránh trùng thư mục với trang TGDĐ cùng tên
    tm = thu_muc(slug); os.makedirs(os.path.join(tm, 'anh', 'goc'), exist_ok=True)
    if site == 'TopZone': return lam_tz(n, d, path, slug, dang, kw, tm)
    code, lk = mdm(['lookup', '--url', path])
    if code or not lk.get('id'):
        ghi_dong(n, {'Status': 'Lỗi', 'Cảnh báo': 'mdm lookup lỗi (exit %s): %s' % (code, str(lk.get('loi') or lk)[:300])})
        print('dòng %d: lookup lỗi' % n, lk); return
    ghi_json(os.path.join(tm, 'lookup.json'), lk)
    cur = lk.get('current', {})
    can_trang = {'Hãng': ['brand'], 'Filter': ['filter-value'], 'Dòng filter': ['filter-value']}.get(dang, [])
    canh = []
    if can_trang and lk['screen'] not in can_trang:
        canh.append('Dạng trang "%s" nhưng PIM là màn %s' % (dang, lk['screen']))
    if lk.get('note'): canh.append(lk['note'])
    bai = bai_chung(n, d, site, path, slug, dang, kw)
    bai.update({
        'noi_ghi': 'pim',
        'mdm': {'screen': lk['screen'], 'id': lk['id'], 'variant': lk.get('variant'), 'rowVersion': lk.get('rowVersion'),
                'f_title': cur.get('title', {}).get('field'), 'f_desc': cur.get('description', {}).get('field'),
                'f_bai': cur.get('article', {}).get('field'), 'f_kw': KW_FIELD.get(lk['screen']),
                'bai_hien_tai_len': (cur.get('article', {}).get('value') or {}).get('len', 0), 'note': lk.get('note', '')},
        'ten': (lk.get('value') or lk.get('brand') or {}).get('name', ''),
    })
    luu(tm, bai)
    ghi_dong(n, {'Status': 'Doing', 'Bản ghi PIM': '%s %s (%s, rowVersion %s)' % (lk['screen'], lk['id'], lk.get('variant'), lk.get('rowVersion')),
                 'Cảnh báo': ' | '.join(canh), 'Cập nhật': hom_nay()})
    if bai.get('outline_user'): print('  outline user → outline_user.md')
    print('dòng %d → %s\n  PIM: %s %s, field bài %s (hiện %s ký tự)%s' % (n, tm, lk['screen'], lk['id'], bai['mdm']['f_bai'],
          bai['mdm']['bai_hien_tai_len'], ('\n  LƯU Ý: ' + ' | '.join(canh)) if canh else ''))
    if bai['mdm']['bai_hien_tai_len']:
        print('  CẢNH BÁO: trang đã có infobox. Skill này chỉ VIẾT MỚI: hỏi user trước khi ghi đè.')


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    if a == ['--run']:
        h = header(); rows = doc_range(TAB + '!A1:%s' % col(len(h) - 1))
        dong = [i + 2 for i, r in enumerate(bang(rows)) if r.get('Status', '').strip() == 'Run']
        print('dòng Status=Run:', dong)
    else:
        dong = [int(x) for x in a]
    for n in dong: lam(n)
