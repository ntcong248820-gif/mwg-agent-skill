#!/usr/bin/env python3
"""Bước 3: giao Antigravity viết bai.md cho infobox PIM, Claude QC sau.

  python3 giao_anti.py <thư mục việc> [--model pro|flash] [--timeout 25m] [--sua "góp ý cần viết lại"]

Cần trong thư mục việc: bai.json, outline.md (Claude đã duyệt, có nguồn heading), research.json (du_kien có nguồn),
tgdd.json, nguon_outline.json. Script gói brief_viet.md (vai trò + chống bịa + rule văn phong skill + rule outline
+ quy ước markdown infobox + outline + dữ kiện), gọi anti-run.mjs (app mode, workspace ~/viet-content-infobox),
chờ bai.md và ~/viet-content-infobox/tasks/viet-infobox/<slug>/anti_report.md (dòng cuối "Status: done").
Lỗi/timeout → in "ANTI_LOI: ..." exit 2: Claude tự viết bước này và ghi vào Cảnh báo.
"""
import fcntl, json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pim import *

WORKSPACE = os.path.expanduser('~/viet-content-infobox')
ANTI_RUN = os.path.expanduser('~/mwg-agent-crew/scripts/anti-run.mjs')
VAN_PHONG_AI = os.path.expanduser('~/.claude/skills/_shared/tranh-van-phong-ai.md')

MD_INFOBOX = '''```
## Sapo 2 câu (đúng 1 dòng ##): câu 1 định nghĩa/tóm tắt có KW chính (AIO), câu 2 bài tổng hợp những gì. Không link.

### 1. <Dòng> giá bao nhiêu tiền?

Đoạn tối đa 4 dòng desktop (~380 ký tự, 40-65 từ), câu đầu trả lời thẳng heading. Ý dài thì tách thành 2-3 đoạn, mỗi đoạn 1 ý. H3 giá luôn có 2 đoạn văn TRƯỚC bảng giá đầu tiên.

[VIDEO https://youtu.be/<id>]   ← video YouTube của Apple (kênh Apple/Apple Vietnam) về {TEN}, đặt ĐẦU BÀI GIỮA đoạn 1 và đoạn 2 của heading đầu tiên (không bao giờ sát bảng, bảng giá nằm sau đoạn 2). Chỉ lấy URL có trong DU_KIEN (kèm nguồn), không tự nghĩ ra ID. Không có video thì bỏ dòng này.

#### 1.1. Bảng giá <model> mới nhất

| **Phiên bản** | **Giá tại {TEN}** |
|---|---|
| iPhone 18 Pro 256GB | 38.990.000đ |

Đoạn phân tích ngắn sau bảng (bắt buộc, không để 2 bảng liền nhau).

*Giá <KW chính> cập nhật ngày {ngay}, có thể thay đổi theo thời gian, chi tiết truy cập {WEB} hoặc liên hệ hotline {HL} để biết thông tin chính xác nhất.*

### 4. <Dòng> có gì mới?

#### 4.1. Heading đặc điểm nổi bật (rule H4 đặc điểm)

1-3 đoạn giải thích có số liệu, mỗi đoạn tối đa 4 dòng desktop (~380 ký tự), đoạn nào dài thì tách theo ý.

- **Nhãn**: nội dung (list cấp 1)
+ list cấp 2

{MUA}

### n+1. Ưu đãi khi mua <dòng> tại {TEN}

Câu dẫn + list ưu đãi CHỈ lấy từ DU_KIEN (ưu đãi live). Không có dữ kiện ưu đãi thì viết 1 đoạn chung (trả góp, thu cũ đổi mới theo điều kiện áp dụng), không số.

### n+2. Câu hỏi thường gặp về <dòng>

#### Câu hỏi không đánh số?

Trả lời câu đầu trực tiếp, 2-4 câu.

*Kết bài in nghiêng 2-3 câu: tóm giá trị, hợp với ai, CTA mua tại {TEN} + hotline {HL}.*
```
- H3 đánh số "1.", H4 con đánh số "1.1." (trừ H4 câu hỏi FAQ và H4 kiểu câu hỏi trong mục review/chọn mua: không số).
- ĐỘ DÀI ĐOẠN (BẮT BUỘC): mỗi đoạn văn tối đa 4 dòng khi xem desktop = tối đa ~380 ký tự (kể cả đoạn trong Mua, Ưu đãi, FAQ, kết bài). Quá thì tách thành nhiều đoạn theo ý, cách nhau 1 dòng trống. Tách là chia ý, KHÔNG cắt cho ngắn: mỗi đoạn vẫn phải có số liệu/tên tính năng cụ thể từ DU_KIEN. Cấm câu chung chung vô nghĩa (vd "chạy macOS cài sẵn, có Apple Intelligence, khả dụng tùy ngôn ngữ và khu vực"). Heading không đủ dữ kiện cụ thể thì bỏ hẳn heading.
- Không chèn link, không ảnh/[IMG], không box Bài viết liên quan, không shortcode: Claude làm sau.
- Không dấu ";", không gạch ngang dài, không chữ "niêm yết", không gọi sản phẩm là "thiết bị".'''


MUA = {
    'TGDĐ': '### n. Mua <dòng> ở đâu chính hãng, uy tín, giá tốt?\n\n3 đoạn theo mẫu (đại lý ủy quyền Apple / các phiên bản đang bán / giá minh bạch + ưu đãi theo thời điểm). '
            'Script tự thêm box "Lý do nên mua" + kênh mua sau các đoạn này.',
    'TopZone': '### n. Mua <dòng> tại TopZone\n\n2-3 đoạn: TopZone là hệ thống bán lẻ ủy quyền Apple (chỉ số liệu có trong DU_KIEN, vd số cửa hàng), các phiên bản đang bán, '
               'hỗ trợ trả góp/thu cũ đổi mới theo điều kiện áp dụng. Script tự thêm list kênh mua (topzone.vn, hotline 1900.9696.42) sau các đoạn này. Không box "Lý do nên mua".',
}


def md_infobox(bai, ngay):
    st = site_cua(bai)
    return (MD_INFOBOX.replace('{MUA}', MUA[ten_site(bai.get('site'))]).replace('{TEN}', st['ten']).replace('{WEB}', st['web'])
            .replace('{HL}', st['hotline']).replace('{ngay}', ngay))


def doc(p, mac=''):
    return open(p).read() if os.path.exists(p) else mac


def tom_tgdd(p):
    d = doc_json(p, [])
    ra = []
    for x in d if isinstance(d, list) else [d]:
        sp = x.get('product')
        if sp:
            ra.append({'ten': sp.get('ten'), 'url': sp.get('url'), 'thong_so': sp.get('thong_so'),
                       'phien_ban': [{'size': v.get('size'), 'gia': v.get('gia_text')} for v in sp.get('phien_ban', []) if v.get('size')]})
    return json.dumps(ra, ensure_ascii=False, indent=1) if ra else '(không có)'


def bao_cao(slug):
    d = os.path.join(WORKSPACE, 'tasks', 'viet-infobox', slug); os.makedirs(d, exist_ok=True)
    return os.path.join(d, 'anti_report.md')


def skill_rule():
    """Phần văn phong/AIO của SKILL.md viet-infobox-apple (bỏ phần HTML TinyMCE vì PIM dựng bằng script)."""
    s = doc(os.path.join(SKILL, 'SKILL.md'))
    giu = []
    for muc in ('Vai Trò', 'Nguyên Tắc Chung', 'Body Bài Viết', 'Tối Ưu AI Overview (AIO)', 'FAQ', 'Độ Chính Xác Với Apple', 'Bảng So Sánh'):
        m = re.search(r'^## %s\n(.*?)(?=^## )' % re.escape(muc), s, re.S | re.M)
        if m: giu.append('### ' + muc + '\n' + m.group(1).strip())
    return '\n\n'.join(giu)


def brief(tm, sua):
    bai = doc_json(os.path.join(tm, 'bai.json'))
    ngay = hom_nay()
    st = site_cua(bai); ten = st['ten']
    out_md, rp = os.path.join(tm, 'bai.md'), bao_cao(bai['slug'])
    ghi_chu = '(outline của user đã nằm trong OUTLINE CUỐI, giữ đúng)' if bai.get('outline_user') else (bai.get('ghi_chu') or '(không)')
    phan = [
        '# VIỆC CỦA BẠN: viết infobox %s %s (trang %s %s) dạng markdown' % (bai['keyword'], ten_site(bai.get('site')), bai['dang_trang'], bai['url']),
        'Bạn là người viết. Người điều phối (Claude) đã lên outline + dữ kiện, sau đó sẽ QC số liệu, chèn link, ảnh, dựng HTML PIM. Bạn CHỈ viết nội dung.',
        f'- Ghi bài markdown vào: {out_md} (ghi đè).',
        f'- Xong thì ghi {rp}: tự soát (số H3/H4, số câu FAQ, ý nào thiếu dữ kiện đã bỏ), mục "Nguồn từng ý", dòng cuối đúng "Status: done".',
        '- Không mở file bài cũ nào khác trong workspace. Heading của CellphoneS/infobox dòng trước chỉ để hiểu khung, KHÔNG chép câu chữ.',
        f'- Ngày hôm nay: {ngay}. Mọi câu ngày cập nhật giá = hôm nay.',
        '\n## CHỐNG BỊA THÔNG TIN (BẮT BUỘC, vi phạm là bài bị loại)\n'
        '- CHỈ viết dữ kiện (số đo, tên tính năng, chất liệu, giá, ngày, màu, dung lượng, ưu đãi, so sánh hơn kém) có trong DU_KIEN hoặc DỮ LIỆU GIÁ bên dưới. Kiến thức nền của bạn KHÔNG phải nguồn.\n'
        '- Giá CHỈ lấy từ DỮ LIỆU GIÁ (giá tại %s), viết "Giá ... tại %s là ...", không chữ "niêm yết", không lấy giá Apple trừ khi DU_KIEN ghi rõ để so sánh.\n'
        '- Bài đăng trên %s: chỉ nhắc %s là nơi mua, hotline %s. Không nhắc site khác của MWG.\n' % (ten, ten, st['web'], ten, st['hotline'])
        + 
        '- Không tin đồn/rò rỉ, kể cả ghi rõ là tin đồn. Chỉ bản bán tại Việt Nam (tính năng/màu/dung lượng theo Apple VN).\n'
        '- Ý không có dữ kiện thì BỎ HẲN, không viết "chưa công bố/chưa có thông tin", không câu chung chung kéo dài. Ngoại lệ: heading dạng "có X không" mà nguồn không nêu X → viết "không có X" + cách thay thế có trong nguồn.\n'
        '- Mục "Nguồn từng ý" trong báo cáo: mỗi đoạn có số liệu/tính năng 1 dòng "đoạn ... <- du_kien số N / tgdd.json". Đoạn không chỉ ra nguồn thì xóa khỏi bai.md.\n',
        '\n## THÔNG TIN BÀI\n- Trang: %s (%s)\n- Từ khóa chính: %s\n- Từ khóa phụ (rải tự nhiên ở FAQ/kết bài, không heading riêng, không câu nhét gượng): %s\n- Ghi chú của user: %s' % (
            bai['url'], bai['dang_trang'], bai['keyword'], ', '.join(bai.get('kw_phu', [])) or '(không)', ghi_chu),
    ]
    if sua:
        phan.append('\n## GÓP Ý CẦN SỬA (viết lại bai.md hiện có theo góp ý, giữ phần không bị góp ý)\n' + sua
                    + '\n\n### BÀI HIỆN TẠI\n' + doc(os.path.join(CACHE, 'infobox_cu', bai['slug'], 'bai_truoc_anti.md')))
    phan += [
        '\n## RULE H4 ĐẶC ĐIỂM NỔI BẬT + QUY TẮC OUTLINE\n' + doc(os.path.join(SKILL, 'references', 'outline-infobox.md')).split('## H4 ĐẶC ĐIỂM NỔI BẬT', 1)[-1],
        '\n## VĂN PHONG (skill viet-infobox-apple)\n' + skill_rule(),
        '\n## TRÁNH VĂN PHONG AI\n' + doc(VAN_PHONG_AI),
        '\n## QUY ƯỚC FILE bai.md\n' + md_infobox(bai, ngay),
        '\n## OUTLINE CUỐI (giữ đúng heading, thứ tự, cấp; bỏ chú thích nguồn <!-- -->)\n' + doc(os.path.join(tm, 'outline.md')),
        '\n## DU_KIEN, PAA, GSC (RESEARCH)\n' + doc(os.path.join(tm, 'research.json')),
        '\n## DỮ LIỆU GIÁ (giá từng phiên bản tại %s)\n' % ten + tom_tgdd(os.path.join(tm, 'tgdd.json')),
    ]
    p = os.path.join(tm, 'brief_viet.md'); open(p, 'w').write('\n'.join(phan))
    return p, out_md, rp


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit()
    tm = os.path.abspath(os.path.expanduser(a[0]))
    model = a[a.index('--model') + 1] if '--model' in a else 'pro'
    to = a[a.index('--timeout') + 1] if '--timeout' in a else '25m'
    sua = a[a.index('--sua') + 1] if '--sua' in a else ''
    if not tm.startswith(WORKSPACE + '/'):
        print('ANTI_LOI: thư mục việc phải nằm trong %s' % WORKSPACE); sys.exit(2)
    for f in ('bai.json', 'outline.md', 'research.json'):
        if not os.path.exists(os.path.join(tm, f)): print('ANTI_LOI: thiếu %s' % f); sys.exit(2)
    slug = doc_json(os.path.join(tm, 'bai.json'))['slug']
    cat = os.path.join(CACHE, 'infobox_cu', slug); os.makedirs(cat, exist_ok=True)
    for f in os.listdir(tm):   # bài cũ cất ra ngoài workspace để Anti không chép lại
        if re.match(r'bai(_.+)?\.(md|html)$', f): shutil.move(os.path.join(tm, f), os.path.join(cat, f))
    if os.path.exists(os.path.join(cat, 'bai.md')): shutil.copy(os.path.join(cat, 'bai.md'), os.path.join(cat, 'bai_truoc_anti.md'))
    bp, out_md, rp = brief(tm, sua)
    if os.path.exists(rp): os.remove(rp)
    lenh = ['node', ANTI_RUN, '--mode', 'app', '--model', model, '--title', 'viet-infobox: ' + slug,
            '--workspace', WORKSPACE, '--evidence', rp, '--timeout', to,
            '--prompt', 'Đọc kỹ toàn bộ file %s rồi làm đúng việc trong đó. File đó là toàn bộ yêu cầu.' % bp]
    khoa = open(os.path.join(CACHE, 'anti.lock'), 'w'); print('Chờ hàng đợi Antigravity...', flush=True)
    fcntl.flock(khoa, fcntl.LOCK_EX); print('Bắt đầu giao Anti: %s' % time.strftime('%H:%M:%S'), flush=True)
    try: p = subprocess.run(lenh, capture_output=True, text=True, env={**os.environ, 'MWG_CREW_ROLE': 'worker'})
    finally: fcntl.flock(khoa, fcntl.LOCK_UN)
    i = p.stdout.find('{'); kq = {}
    try: kq = json.loads(p.stdout[i:]) if i >= 0 else {}
    except json.JSONDecodeError: pass
    ok = os.path.exists(out_md) and os.path.getmtime(out_md) > os.path.getmtime(bp) and os.path.exists(rp) and re.search(r'^Status:\s*done', doc(rp), re.I | re.M)
    if not ok:
        print('ANTI_LOI: status=%s. %s' % (kq.get('status', '?'), (p.stderr or p.stdout)[-500:].strip())); sys.exit(2)
    print('ANTI_OK: %s (%ss)\n--- anti_report.md ---\n%s' % (out_md, kq.get('durationSec'), doc(rp)))
