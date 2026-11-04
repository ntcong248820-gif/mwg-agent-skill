// Dùng chung cho các script của skill: mở form CMS bằng profile Chrome CMS_CHROME_PROFILE, đọc lại bài.
// 2 mode, chọn bằng cờ `--mode hoi-dap|game-app` (hoặc biến CMS_MODE; mặc định hoi-dap):
//   hoi-dap  → CMS Faq  (v2/Faq/NewsEdit)
//   game-app → CMS News (v2/News/NewsEdit?siteId=1), chuyên mục 2002 "Tin Game App"
// Cờ --mode bị lấy khỏi process.argv ở đây nên script gọi lib vẫn đọc argv như cũ.
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { McpClient, openAndBind, evaluate, toolText } from '../../onpage-mdm-khai-bao/scripts/cms-cli-mcp.mjs';

export { evaluate, toolText };
export const PROFILE = process.env.CMS_CHROME_PROFILE;
if (!PROFILE) { console.error('Thiếu biến môi trường CMS_CHROME_PROFILE (key profile của chrome-profile đã đăng nhập CMS). Xem blog-hoi-dap-tron-goi/SETUP.md'); process.exit(2); }
export const BLOG_ROOT = process.env.BLOG_ROOT || path.join(os.homedir(), 'blog-hoi-dap');
const argv = process.argv;
const mi = argv.findIndex((a) => a === '--mode' || a.startsWith('--mode='));
let rawMode = process.env.CMS_MODE || 'hoi-dap';
if (mi >= 0) { rawMode = argv[mi].includes('=') ? argv[mi].split('=')[1] : argv[mi + 1]; argv.splice(mi, argv[mi].includes('=') ? 1 : 2); }
export const MODE = rawMode;
export const MODES = {
  'hoi-dap': {
    ten: 'Hỏi Đáp', editor: 'content_FaqNews', prefix: 'https://cms.thegioididong.com/v2/Faq/NewsEdit',
    edit: (id) => `https://cms.thegioididong.com/v2/Faq/NewsEdit?newsId=${id}`,
    status: { 1: 'Nháp', 2: 'Xuất bản', 3: 'Chờ duyệt', 4: 'Đã duyệt' },
  },
  'game-app': {
    ten: 'Game App', editor: 'contentNewsAva', prefix: 'https://cms.thegioididong.com/v2/News/NewsEdit',
    edit: (id) => `https://cms.thegioididong.com/v2/News/NewsEdit?newsId=${id}&siteId=1`,
    status: { draft: 'Nháp', pending: 'Chờ duyệt', approved: 'Đã duyệt', actived: 'Xuất bản' },
    chuyen_muc: { id: '2002', ten: 'Tin Game App' },
  },
};
if (!MODES[MODE]) { console.error(`--mode phải là ${Object.keys(MODES).join(' | ')}, nhận "${MODE}"`); process.exit(2); }
export const M = MODES[MODE];
export const EDIT = M.edit;
/** Script chưa hỗ trợ game-app gọi hàm này đầu file để dừng sớm, không ghi nhầm vào CMS Faq. */
export function onlyHoiDap(ten) { if (MODE !== 'hoi-dap') { console.error(`${ten} mới hỗ trợ mode hoi-dap (CMS Faq). Mode ${MODE} chưa có.`); process.exit(2); } }
export const OUT_DIR = path.join(BLOG_ROOT, '_cms-tao-bai');
export const REGISTRY = path.join(OUT_DIR, 'da-tao.json');
export const OPTIONS = JSON.parse(fs.readFileSync(new URL('../references/cms-options.json', import.meta.url), 'utf8'));
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const HERE = path.dirname(new URL(import.meta.url).pathname);
// chrome-profile cần --force để mở tab mới khi profile đã có tab CMS
const BRIDGE = path.join(os.homedir(), '.local/bin/devtools-mcp-bridge');
if (!process.env.CHROME_DEVTOOLS_MCP_BIN && fs.existsSync(BRIDGE)) process.env.CHROME_DEVTOOLS_MCP_BIN = BRIDGE;
process.env.CHROME_PROFILE_BIN ||= path.join(HERE, 'cp-force.sh');

/** Mở trang sửa bài (id=0 là tạo mới), thử lại vì hub hay báo "No page found". Chỉ dùng TRƯỚC khi POST. */
export async function openEdit(id, roots, tries = 4) {
  let last;
  for (let t = 1; t <= tries; t++) {
    const c = new McpClient({ roots });
    try {
      await c.connect();
      await openAndBind(c, { profile: PROFILE, url: EDIT(id), expectUrlPrefix: M.prefix });
      await sleep(8000);
      const ok = await evaluate(c, `() => !!(window.tinymce && tinymce.get('${M.editor}') && document.querySelector('#submitEditNews') && document.querySelector('#hdNewsId'))`, 60000);
      if (ok === true) return c;
      throw new Error('form chưa sẵn sàng');
    } catch (e) {
      last = e;
      try { await c.close?.(); } catch {}
      console.error(`mở ${EDIT(id)} lần ${t} lỗi: ${String(e.message).slice(0, 200)}`);
      await sleep(10000);
    }
  }
  throw last;
}

/** Hàm chạy trong trang: GET lại NewsEdit?newsId=id, đọc giá trị server đang lưu. */
const READ_FN_HOIDAP = (id) => `async () => {
  const h = await (await fetch('/v2/Faq/NewsEdit?newsId=${id}', { credentials: 'same-origin', cache: 'no-store' })).text();
  const d = new DOMParser().parseFromString(h, 'text/html');
  const q = (n) => d.querySelector('[name="' + n + '"]');
  const sel = (n) => { const e = q(n); return e ? [...e.querySelectorAll('option')].filter(o => o.hasAttribute('selected')).map(o => o.value) : null; };
  const content = (d.querySelector('#content_FaqNews') || {}).value || '';
  return {
    id: (q('hdNewsId') || {}).value, title: (q('txtTitle') || {}).value, url: (q('txtUrl') || {}).value,
    thumb: (q('thumbnailNews') || {}).value, child: sel('cboChildCategory'), parent: sel('cboParentCategory'),
    article_type: sel('cboArticleType'), product_related: (q('hdListProductRelated') || {}).value,
    meta_title: (q('txtMetaTitle') || {}).value, meta_desc: (q('txtMetaDescription') || {}).value,
    tags: (q('hdListKeyword') || {}).value, schema: (q('txtSchema') || {}).value, status: sel('cboStatus'),
    date: (q('txtDate') || {}).value, hour: sel('txtHour'), minute: sel('txtMinute'),
    content_len: content.length, content
  };
}`;

/** Mode game-app: đọc NewsEdit?newsId=id&siteId=1. status = [giá trị hdCurrentStatus]; child = id chuyên mục ở sticker. */
const READ_FN_GAMEAPP = (id) => `async () => {
  const h = await (await fetch('/v2/News/NewsEdit?newsId=${id}&siteId=1&_=' + Date.now(), { credentials: 'same-origin', cache: 'no-store' })).text();
  const d = new DOMParser().parseFromString(h, 'text/html');
  const q = (n) => d.querySelector('#submitEditNews [name="' + n + '"]');
  const content = (d.getElementById('contentNewsAva') || {}).value || '';
  const st = (d.getElementById('hdCurrentStatus') || {}).value;
  return {
    id: (d.getElementById('hdNewsId') || {}).value, title: (q('txtTitle') || {}).value, url: (q('txtUrl') || {}).value,
    thumb: (q('thumbnailNews') || {}).value, meta_title: (q('txtMetaTitle') || {}).value, meta_desc: (q('txtMetaDescription') || {}).value,
    tags: (q('txtTag') || {}).value, meta_keyword: (q('txtMetaKeyword') || {}).value,
    status: st ? [st] : [], categories: [...d.querySelectorAll('ul.sticker.newscategory li[data-id]')].map(li => li.getAttribute('data-id')),
    content_len: content.length, content
  };
}`;
export const READ_FN = MODE === 'game-app' ? READ_FN_GAMEAPP : READ_FN_HOIDAP;

/** Đếm cấu trúc HTML để so nội dung (TinyMCE chuẩn hoá lại khoảng trắng, thêm tbody...). */
export const plainText = (html) => html.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
export function shape(html) {
  const n = (re) => (html.match(re) || []).length;
  const text = plainText(html);
  return { h2: n(/<h2\b/g), h3: n(/<h3\b/g), h4: n(/<h4\b/g), p: n(/<p\b/g), li: n(/<li\b/g), a: n(/<a\b/g), img: n(/<img\b/g), table: n(/<table\b/g), text_len: text.length };
}

export function loadRegistry() {
  try { return JSON.parse(fs.readFileSync(REGISTRY, 'utf8')); } catch { return []; }
}
export function saveRegistry(list) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(REGISTRY, JSON.stringify(list, null, 1));
}
export const STATUS = M.status;
