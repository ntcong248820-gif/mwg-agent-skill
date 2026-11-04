#!/usr/bin/env python3
"""Bước 8-9: ghi infobox (+ Title/Meta/Keyword nếu bai.json có) lên PIM, nghiệm thu web, cập nhật sheet.

  python3 ghi_pim.py <thư mục việc>                  chạy thử (dry): plan trong <việc>/data/processed/
  python3 ghi_pim.py <thư mục việc> --live           ghi thật (user đã cho phép sẵn: "viết xong air lên lun")
      [--cho-brand-filter]   cho ghi title_brand_filter/description_brand_filter (dùng chung mọi hãng của giá trị)
      [--de-bai-cu]          cho ghi đè khi field bài trên PIM đang có nội dung (skill chỉ viết mới)

Chặn ghi khi: kiem_pim.py còn LỖI, bai.json thiếu, rowVersion PIM đã đổi so với lúc tao_viec (exit 3 của mdm-cli).
Live: mdm-cli batch (backup cả bản ghi → ghi kèm rowVersion → đọc lại so từng byte) → verify-web (core mới, tối đa 20')
→ sheet: Title, Meta, Keyword PIM, Trạng thái PIM, Backup PIM, Note PIM, Cập nhật, Status=Done.

Site TopZone (TopZone chưa qua PIM, còn CMS) — mọi dạng trang (Hãng/Filter/Dòng filter) đều tạo bài News trên CMS TGDĐ
(NewsEdit?newsId=0&siteId=1) bằng cms_infobox_tz.mjs, đọc lại so nội dung:
- Tên: tiêu đề "TopZone <Tên> - Infobox", tag + meta "<Tên> - Infobox", url "<slug>-infobox-topzone".
- Dòng filter: Xuất bản (actived) + tick chuyên mục 2424 "Mô tả dòng sản phẩm". Hãng/Filter: Chờ duyệt (pending), không tick chuyên mục.
- Thumb = ảnh đầu anh-cdn.json. Trang live đang gắn News khác → chặn, cần --de-bai-cu (ghi đè bài đó).
- User tự khai báo ID bài vào ô "Link TOPZONE" ở CMS cũ (Category/Property) → sheet: Trạng thái PIM, Bản ghi PIM = ID + link CMS.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *


def slug_url(t):
    return re.sub(r'[^a-z0-9]+', '-', deaccent(t).lower().replace('đ', 'd')).strip('-')


TT_TZ = {'Dòng filter': ('actived', 'Xuất bản')}   # dạng khác: ('pending', 'Chờ duyệt')


def ghi_tz(tm, bai, html, a, live):
    n, cms = bai['dong'], bai.get('cms') or {}
    nid = cms.get('news_id') or ''
    dang_gan = cms.get('news_dang_gan') or ''
    if dang_gan and dang_gan != nid:
        if '--de-bai-cu' not in a: raise SystemExit('trang đang gắn infobox News %s. Skill chỉ viết mới: hỏi user, đồng ý thì thêm --de-bai-cu (ghi đè bài đó)' % dang_gan)
        nid = dang_gan
    tt, tt_ten = TT_TZ.get(bai['dang_trang'], ('pending', 'Chờ duyệt'))
    cdn = doc_json(os.path.join(tm, 'anh', 'anh-cdn.json'), {})
    thumb = next(iter(cdn.values()), {}).get('src', '')
    ten = bai.get('ten') or bai['keyword']
    args = ['ghi', '--html', html, '--tieu-de', 'TopZone %s - Infobox' % ten, '--tag', '%s - Infobox' % ten,
            '--url', slug_url(ten) + '-infobox-topzone', '--trang-thai', tt]
    if tt != 'actived': args.append('--khong-chuyen-muc')   # Hãng/Filter: không tick Mô tả dòng sản phẩm
    if thumb: args += ['--thumb', thumb]
    if nid: args += ['--id', str(nid)]
    code, kq = tz(args + (['--live'] if live else []))
    print(json.dumps(kq, ensure_ascii=False, indent=1))
    if code or kq.get('loi'):
        if live: ghi_dong(n, {'Trạng thái PIM': 'Lỗi', 'Note PIM': 'CMS TopZone: ' + str(kq.get('loi') or kq)[:300]})
        sys.exit(code or 1)
    if not live: print('DRY xong: xem trên rồi chạy lại kèm --live'); return
    if not kq.get('khop_noi_dung'): print('CẢNH BÁO: nội dung đọc lại khác bản ghi (CMS chuẩn hóa?), mở bài kiểm tay')
    bai.setdefault('cms', {})['news_id'] = str(kq['id']); ghi_json(os.path.join(tm, 'bai.json'), bai)
    da_gan = str(kq['id']) == str(dang_gan)
    link = 'https://cms.thegioididong.com/v2/News/NewsEdit?newsId=%s&siteId=1' % kq['id']
    if da_gan: trang, note = 'Đã ghi CMS', 'Cập nhật bài đang gắn, web cập nhật sau khi cache hết'
    elif tt == 'actived': trang, note = 'Chờ khai báo tay', 'Đã xuất bản News %s. Khai báo ID %s vào ô Link TOPZONE của dòng filter (CMS cũ Category/Property)' % (kq['id'], kq['id'])
    else: trang, note = 'Chờ duyệt', 'News %s để Chờ duyệt, chưa xuất bản' % kq['id']
    ghi_dong(n, {'Trạng thái PIM': trang, 'Status': 'Done', 'Bản ghi PIM': 'News %s (%s)' % (kq['id'], link),
                 'Note PIM': note + ('' if kq.get('khop_noi_dung') else ' | đọc lại lệch nội dung, kiểm tay'), 'Cập nhật': hom_nay()})
    print('News ID %s (%s, %s)\n  %s\n  %s' % (kq['id'], 'tạo mới' if kq.get('moi') else 'cập nhật', kq.get('trang_thai_sau') or tt_ten, link, note))


def main():
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    tm = os.path.abspath(os.path.expanduser(a[0])); live = '--live' in a
    bai = doc_json(os.path.join(tm, 'bai.json')); html = os.path.join(tm, 'bai_pim.html')
    if not bai or not os.path.exists(html): raise SystemExit('thiếu bai.json hoặc bai_pim.html')
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kiem_pim.py'), html], capture_output=True, text=True)
    if r.returncode: print(r.stdout); raise SystemExit('kiem_pim.py còn LỖI, không ghi')
    if ten_site(bai.get('site')) == 'TopZone': return ghi_tz(tm, bai, html, a, live)
    m = bai['mdm']; n = bai['dong']
    code, lk = mdm(['lookup', '--url', bai['path']])
    if code: raise SystemExit('lookup lỗi: %s' % lk)
    if lk['id'] != m['id']: raise SystemExit('bản ghi đổi: %s → %s' % (m['id'], lk['id']))
    hien = (lk.get('current', {}).get('article', {}).get('value') or {}).get('len', 0)
    if hien and '--de-bai-cu' not in a:
        raise SystemExit('field %s trên PIM đang có %d ký tự. Skill chỉ viết mới: hỏi user, đồng ý thì thêm --de-bai-cu' % (m['f_bai'], hien))
    st, canh = {}, []
    if bai.get('title'): st[m['f_title']] = bai['title']
    if bai.get('meta'): st[m['f_desc']] = bai['meta']
    if bai.get('kw_pim') and m.get('f_kw'): st[m['f_kw']] = bai['kw_pim']
    if m.get('variant') == 'brand-filter' and '--cho-brand-filter' not in a:
        for f in [k for k in st if k.endswith('_brand_filter')]:
            st.pop(f); canh.append('bỏ %s (dùng chung mọi hãng, cần --cho-brand-filter)' % f)
    viec = [{'cmd': 'write', 'screen': m['screen'], 'id': m['id'], 'set': st, 'setFile': {m['f_bai']: html}}]
    vp = os.path.join(tm, 'data', 'processed', 'viec.json'); os.makedirs(os.path.dirname(vp), exist_ok=True); ghi_json(vp, viec)
    args = ['batch', '--jobs', vp, '--task-dir', tm] + (['--live'] if live else [])
    code, kq = mdm(args, timeout=1200)
    led = os.path.join(tm, 'data', 'processed', 'mdm-batch-viec.jsonl')
    rec = json.loads(open(led).read().strip().splitlines()[-1]) if os.path.exists(led) else {}
    res = rec.get('result') or {}
    print(json.dumps({'batch': kq.get('status'), 'exit': code, 'viec': rec.get('status'), 'plan': res.get('planFile'),
                      'backup': res.get('backupFile'), 'rowVersion': [res.get('rowVersion'), res.get('rowVersionAfter')], 'field': list(st) + [m['f_bai']], 'canh': canh}, ensure_ascii=False, indent=1))
    if code == 3: ghi_dong(n, {'Trạng thái PIM': 'Lỗi', 'Note PIM': 'ROW_VERSION: bản ghi vừa bị sửa, đọc lại rồi chạy lại'}); sys.exit(3)
    if code: ghi_dong(n, {'Trạng thái PIM': 'Lỗi', 'Note PIM': str(rec.get('error') or kq)[:300]}); sys.exit(code)
    if not live:
        print('DRY xong: xem plan (before/after) rồi chạy lại kèm --live'); return
    ghi_dong(n, {'Trạng thái PIM': 'Đã ghi PIM', 'Backup PIM': res.get('backupFile', ''), 'Title': bai.get('title', ''), 'Meta': bai.get('meta', ''),
                 'Keyword PIM': bai.get('kw_pim', ''), 'Note PIM': 'rowVersion %s→%s. %s' % (res.get('rowVersion'), res.get('rowVersionAfter'), ' '.join(canh)), 'Cập nhật': hom_nay()})
    # nghiệm thu web core mới: title (nếu ghi) + H3 đầu
    h3 = re.search(r'<h3>(.*?)</h3>', open(html).read())
    vw = ['verify-web', '--url', bai['path'], '--task-dir', tm, '--expect-text', re.sub(r'<[^>]+>', '', h3.group(1)) if h3 else bai['keyword']]
    if m['f_title'] in st: vw += ['--expect-title', st[m['f_title']]]
    code, v = mdm(vw, timeout=1500)
    ok = v.get('verdict') == 'PASS'
    ghi_dong(n, {'Trạng thái PIM': 'Đã lên web' if ok else 'Đã ghi PIM', 'Status': 'Done',
                 'Note PIM': 'rowVersion %s→%s, web %s (%ss). %s' % (res.get('rowVersion'), res.get('rowVersionAfter'), v.get('verdict'), v.get('seconds'), ' '.join(canh))})
    print('verify-web:', v.get('verdict'), v.get('seconds'), 's', '' if ok else '(MDM có thể lan chậm tới 15 phút, chạy lại verify-web sau)')


if __name__ == '__main__':
    main()
