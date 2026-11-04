/**
 * test-product-runner-e2e.mjs — chạy THẬT cmsBulkInsert() (không chỉ hàm thuần logic như
 * test-runner-logic.mjs) bằng fetch/DOMParser giả, để kiểm finding #4 (field khác bị đổi
 * sau ghi) vốn nằm trong nhánh POST/verify, không tách được thành hàm thuần.
 *   node .claude/skills/onpage-cms-product-content/scripts/test-product-runner-e2e.mjs
 *
 * Cùng cơ chế giả lập với test-news-runner-e2e.mjs: fetch GET trả JSON "docSpec" làm
 * .text(); DOMParser.parseFromString JSON.parse thẳng, dựng doc chỉ với đúng API runner
 * cần (#txtContent, #frmProductSubmit, form.elements).
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ENT = { nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
const decode = (s) =>
  String(s)
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENT ? ENT[n.toLowerCase()] : m));

globalThis.document = {
  createElement: () => ({
    set innerHTML(v) { this._v = decode(v); },
    get value() { return this._v; },
  }),
};

function buildDoc(spec) {
  const textarea = { value: spec.content };
  const formEls = (spec.formFields || []).map((f) => ({
    name: f.name, value: f.value ?? '', disabled: false, tagName: 'INPUT',
    type: f.type || 'hidden', checked: f.checked ?? true, selectedOptions: [],
  }));
  const form = { elements: formEls };
  return {
    querySelector(sel) {
      if (sel === (spec.contentSel || '#txtContent')) return textarea;
      if (sel === (spec.formSel || '#frmProductSubmit')) return form;
      return null;
    },
  };
}

globalThis.DOMParser = class {
  parseFromString(html) { return buildDoc(JSON.parse(html)); }
};

let readQueue = [];
let postCalls = [];
let getCalls = [];
let postHandler = () => ({ ok: true, json: { status: 1 } });

globalThis.fetch = async (url, opts) => {
  if (opts && opts.method === 'POST') {
    postCalls.push({ url, body: String(opts.body), raw: opts.body });
    const r = postHandler(url, opts.body);
    return { ok: r.ok !== false, status: r.status ?? 200, json: async () => (r.json ?? { status: 1 }) };
  }
  getCalls.push(url);
  if (!readQueue.length) throw new Error('test lỗi: GET thừa, readQueue rỗng — kiểm lại kịch bản');
  const spec = readQueue.shift();
  return { ok: true, status: 200, text: async () => JSON.stringify(spec) };
};

const HERE = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(HERE, 'cms-bulk-insert-runner.js'), 'utf8')
  .replace(/if \(typeof window[\s\S]*$/, '');
const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(src + '\nexport { cmsBulkInsert };').toString('base64')
);
const { cmsBulkInsert } = mod;

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };

const BASE_RAW = '<p>iPhone 18 Plus được nhiều người chọn mua trong năm nay.</p>';
const OLD_TEXT = 'iPhone 18 Plus được nhiều người chọn mua trong năm nay.';
const SENTENCE = 'Xem thêm chi tiết tại đây.';
const LINKS = [{ anchor: 'đây', href: 'https://www.thegioididong.com/dtdd/iphone-18' }];
const FORM_FIELDS = [{ name: 'txtSeoTitle', value: 'iPhone 18 Plus giá tốt' }, { name: 'cboStatus', value: '2' }];
const ROW = { row: 1, pid: 335308, site: 1, oldText: OLD_TEXT, sentence: SENTENCE, links: LINKS };
const spec = (over = {}) => ({ content: BASE_RAW, formFields: FORM_FIELDS, ...over });

console.log('\n# finding #4: field khác (ngoài txtContent/hdType) bị đổi sau ghi -> FAIL');
{
  const first = spec();
  const fresh = spec();
  const saved = spec({ formFields: [{ name: 'txtSeoTitle', value: 'BỊ ĐỔI KHÁC Ý MUỐN' }, { name: 'cboStatus', value: '2' }] });
  readQueue = [first, fresh, saved];
  postCalls = [];
  const r = await cmsBulkInsert({ rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status FAIL khi field khác (txtSeoTitle) bị đổi ngoài ý muốn', rec.status === 'FAIL', rec.status);
  t('lý do liệt kê đúng field bị đổi', /field khác bị đổi ngoài ý muốn.*txtSeoTitle/.test(rec.reason || ''), rec.reason);
  t('verify.fieldKhacBiDoi liệt kê đúng', rec.verify?.fieldKhacBiDoi?.includes('txtSeoTitle'), rec.verify?.fieldKhacBiDoi);
}

console.log('\n# đối chứng: hdType đổi (2 = mục Nội dung bài viết, luôn ép) KHÔNG bị coi là field lạ');
{
  const after = BASE_RAW.replace('</p>', ` ${SENTENCE.replace('đây', '<a title="đây" href="https://www.thegioididong.com/dtdd/iphone-18" target="_blank" rel="noopener">đây</a>')}</p>`);
  // hdType có mặt trong form TRƯỚC ghi với giá trị khác 2 (vd mục khác đang active) —
  // runner luôn ép về '2', không được tính là "field khác bị đổi ngoài ý muốn".
  const first = spec({ formFields: [...FORM_FIELDS, { name: 'hdType', value: '6' }] });
  const fresh = spec({ formFields: [...FORM_FIELDS, { name: 'hdType', value: '6' }] });
  const saved = spec({ content: after, formFields: [...FORM_FIELDS, { name: 'hdType', value: '2' }] });
  readQueue = [first, fresh, saved];
  postCalls = [];
  const r = await cmsBulkInsert({ rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status DONE — hdType đổi 6->2 không bị tính là field lạ', rec.status === 'DONE', JSON.stringify(rec.verify || rec.reason));
  t('fieldKhacBiDoi rỗng', (rec.verify?.fieldKhacBiDoi || []).length === 0, rec.verify?.fieldKhacBiDoi);
}

console.log('\n# field hotReason (site 16): đọc/ghi form trang cũ /Product/Edit, multipart UpdateHTML');
const HR = { contentSel: '#hotreason', formSel: '#myForm' };
const HR_FIELDS = [
  { name: 'ProductID', value: '370982' }, { name: 'SiteID', value: '16' }, { name: 'LangID', value: 'vi-VN' },
  { name: 'HTMLDescription', value: '[desktop][/desktop] gallery' }, { name: 'HotReason', value: BASE_RAW },
  { name: 'SaveAllProductHTML', value: 'on', type: 'checkbox', checked: true },
];
const HR_ROW = { ...ROW, pid: 370982, site: 16, field: 'hotReason' };
const hrAfter = BASE_RAW.replace('</p>', ` ${SENTENCE.replace('đây', '<a title="đây" href="https://www.thegioididong.com/dtdd/iphone-18" target="_blank" rel="noopener">đây</a>')}</p>`);
const hrSpec = (over = {}) => ({ ...HR, content: BASE_RAW, formFields: HR_FIELDS, ...over });
{
  const savedFields = HR_FIELDS.map((f) => (f.name === 'HotReason' ? { ...f, value: hrAfter } : f));
  readQueue = [hrSpec(), hrSpec(), hrSpec({ content: hrAfter, formFields: savedFields })];
  postCalls = []; getCalls = [];
  const r = await cmsBulkInsert({ rows: [HR_ROW], dryRun: false });
  const rec = r.rows[0];
  const fd = postCalls[0]?.raw;
  t('hotReason: DONE', rec.status === 'DONE', JSON.stringify(rec.verify || rec.reason));
  t('hotReason: GET trang cũ /Product/Edit?productID=..&site=16', getCalls.every((u) => u === '/Product/Edit?productID=370982&site=16'), getCalls);
  t('hotReason: POST tới /Product/Edit (không phải /v2/Product/Submit)', postCalls.length === 1 && postCalls[0].url === '/Product/Edit', postCalls.map((c) => c.url));
  t('hotReason: body là FormData (multipart)', fd instanceof FormData);
  t('hotReason: HotReason = bài mới, đúng 1 giá trị', fd?.getAll('HotReason').length === 1 && fd.get('HotReason') === hrAfter);
  t('hotReason: có nút UpdateHTML', fd?.get('UpdateHTML') === 'Lưu lại');
  t('hotReason: "Lưu tất cả các site" bị gỡ dù đang tick', fd && !fd.has('SaveAllProductHTML'));
  t('hotReason: không gửi hdType', fd && !fd.has('hdType'));
  t('hotReason: HTMLDescription gửi lại nguyên giá trị', fd?.get('HTMLDescription') === '[desktop][/desktop] gallery');
}
{
  const bad = HR_FIELDS.map((f) => (f.name === 'SiteID' ? { ...f, value: '1' } : f));
  readQueue = [hrSpec({ formFields: bad }), hrSpec({ formFields: bad })];
  postCalls = [];
  const r = await cmsBulkInsert({ rows: [HR_ROW], dryRun: false });
  t('hotReason: form SiteID lệch → ABORT, 0 POST', r.rows[0].status === 'ABORT' && postCalls.length === 0, r.rows[0].reason);
}
{
  const savedFields = HR_FIELDS.map((f) => (f.name === 'HotReason' ? { ...f, value: hrAfter } : f.name === 'HTMLDescription' ? { ...f, value: 'BỊ ĐỔI' } : f));
  readQueue = [hrSpec(), hrSpec(), hrSpec({ content: hrAfter, formFields: savedFields })];
  postCalls = [];
  const r = await cmsBulkInsert({ rows: [HR_ROW], dryRun: false });
  t('hotReason: HTMLDescription đổi sau ghi → FAIL', r.rows[0].status === 'FAIL' && /HTMLDescription/.test(r.rows[0].reason || ''), r.rows[0].reason);
}
{
  postHandler = () => ({ ok: false, status: 500 });
  readQueue = [hrSpec(), hrSpec()];
  const r = await cmsBulkInsert({ rows: [HR_ROW], dryRun: false });
  t('hotReason: POST HTTP 500 → FAIL (đã gửi, không phải ABORT)', r.rows[0].status === 'FAIL', r.rows[0].reason);
  postHandler = () => ({ ok: true, json: { status: 1 } });
}
{
  readQueue = [spec()];
  getCalls = [];
  const r = await cmsBulkInsert({ rows: [ROW], dryRun: true });
  t('mặc định (không field) vẫn đọc /v2/Product/Edit như cũ', r.rows[0].status === 'DRY' && getCalls[0] === '/v2/Product/Edit?site=1&productId=335308', getCalls);
  readQueue = [];
  const r2 = await cmsBulkInsert({ rows: [{ ...ROW, field: 'bogus' }], dryRun: true });
  t('field lạ → ERROR, không GET', r2.rows[0].status === 'ERROR' && /không hỗ trợ/.test(r2.rows[0].reason), r2.rows[0].reason);
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
