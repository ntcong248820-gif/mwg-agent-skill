"""Hàm dùng chung cho quy trình infobox PIM trọn gói (tab skill_infobox → PIM/MDM)."""
import json, os, re, subprocess, sys, time
VB = os.path.expanduser('~/.claude/skills/viet-blog/scripts')
sys.path.insert(0, VB)
from _chung import gws, doc_range, bang, fetch, chuan, deaccent, SHEET, CACHE, UA   # noqa: F401

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = 'skill_infobox'
GOC = os.path.expanduser('~/viet-content-infobox/infobox-pim')   # nằm trong workspace Antigravity
ANH = os.path.expanduser('~/.claude/skills/blog-hoi-dap-tron-goi/scripts')
MDM_CLI = os.path.expanduser('~/.claude/skills/onpage-mdm-khai-bao/scripts/mdm-cli.mjs')
MDM_ENV = {**os.environ, 'CHROME_DEVTOOLS_MCP_BIN': os.path.expanduser('~/.local/bin/devtools-mcp-bridge'),
           'MDM_CONFIG': os.path.join(SKILL, 'mdm.config.json')}
HOTLINE, HOTLINE_TEL, WEB = '1900 232 460', '1900232460', 'thegioididong.com'   # mặc định TGDĐ, bài TopZone dùng SITES
CMS_TZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cms_infobox_tz.mjs')

# Site → thông số dựng bài. TopZone: không tô màu bảng/chữ, link topzone.vn, hotline 1900.9696.42 (format đo trên bài 1598413).
SITES = {
    'TGDĐ': {'goc': 'https://www.thegioididong.com', 'web': 'thegioididong.com', 'ten': 'Thế Giới Di Động',
             'hotline': '1900 232 460', 'tel': '1900232460'},
    'TopZone': {'goc': 'https://www.topzone.vn', 'web': 'topzone.vn', 'ten': 'TopZone',
                'hotline': '1900.9696.42', 'tel': '1900969642'},
}


def ten_site(v):
    """Chuẩn hóa giá trị cột Site / bai.json['site'] / URL → 'TGDĐ' | 'TopZone'."""
    return 'TopZone' if re.search(r'topzone|^\s*top\s*$', str(v or ''), re.I) else 'TGDĐ'


def site_cua(bai):
    return SITES[ten_site((bai or {}).get('site'))]


def tz(args, timeout=600):
    """Gọi cms_infobox_tz.mjs (CMS News HTTP cookie). Trả (exit code, JSON)."""
    p = subprocess.run(['node', CMS_TZ] + args, capture_output=True, text=True, timeout=timeout)
    i = min([k for k in (p.stdout.find('{'), p.stdout.find('[')) if k >= 0] or [-1])
    try: kq = json.loads(p.stdout[i:]) if i >= 0 else {}
    except json.JSONDecodeError: kq = {}
    if p.returncode and not kq: kq = {'loi': (p.stderr or p.stdout)[-600:].strip()}
    return p.returncode, kq


def mdm(args, timeout=900):
    """Gọi mdm-cli qua DevTools hub (Allow 1 lần/ngày). Trả (exit code, JSON cuối stdout hoặc {})."""
    p = subprocess.run(['node', MDM_CLI] + args, capture_output=True, text=True, env=MDM_ENV, timeout=timeout)
    out, kq = p.stdout, {}
    i = out.find('{')
    if i >= 0:
        try: kq = json.loads(out[i:])
        except json.JSONDecodeError:
            j = out.rfind('\n{')   # nhiều object: lấy cái cuối
            try: kq = json.loads(out[j + 1:]) if j >= 0 else {}
            except json.JSONDecodeError: kq = {}
    if p.returncode and not kq: kq = {'loi': (p.stderr or out)[-800:].strip()}
    return p.returncode, kq


def header():
    return [str(x).strip() for x in doc_range(TAB + '!1:1')[0]]


def col(i):
    s = ''
    i += 1
    while i: i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s


def doc_dong(n):
    h = header()
    r = (doc_range('%s!A%d:%s%d' % (TAB, n, col(len(h) - 1), n)) or [[]])[0]
    return {h[i]: (r[i] if i < len(r) else '') for i in range(len(h))}


def ghi_dong(n, gia_tri):
    """gia_tri: {tên header: giá trị}. Tra cột theo tên header, không theo chữ cái."""
    h = header()
    data = []
    for k, v in gia_tri.items():
        if k not in h: raise SystemExit('tab %s không có cột "%s"' % (TAB, k))
        data.append({'range': '%s!%s%d' % (TAB, col(h.index(k)), n), 'values': [[v]]})
    gws(['sheets', 'spreadsheets', 'values', 'batchUpdate', '--params', json.dumps({'spreadsheetId': SHEET})],
        {'valueInputOption': 'USER_ENTERED', 'data': data})


def tach(v):
    return [x.strip() for x in re.split(r'[\n,;]+', str(v or '')) if x.strip()]


def duong_dan(url):
    u = str(url or '').strip().split('#')[0]
    u = re.sub(r'^https?://(www\.)?(thegioididong\.com|topzone\.vn)', '', u)
    return u if u.startswith('/') else '/' + u


def thu_muc(slug):
    return os.path.join(GOC, slug)


def doc_json(p, mac=None):
    return json.load(open(p)) if os.path.exists(p) else mac


def ghi_json(p, d):
    json.dump(d, open(p, 'w'), ensure_ascii=False, indent=1)


def hom_nay():
    return time.strftime('%d/%m/%Y')
