/**
 * test-apply-ops-runner-e2e.mjs — chạy THẬT cmsBulkInsert({ mode:'apply-ops' }) bằng
 * fetch/DOMParser giả (cùng cơ chế test-product-runner-e2e.mjs): guard sha256(live) ==
 * expectedBeforeSha256 -> ABORT nếu lệch; hotReason happy path chỉ ghi HotReason; verify
 * mismatch -> FAIL; ALREADY (idempotence).
 *   node .claude/skills/onpage-cms-product-content/scripts/test-apply-ops-runner-e2e.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createHash } from 'node:crypto';

const sha256 = (s) => createHash('sha256').update(s, 'utf8').digest('hex');

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
let postHandler = () => ({ ok: true, json: { status: 1 } });

globalThis.fetch = async (url, opts) => {
  if (opts && opts.method === 'POST') {
    postCalls.push({ url, body: String(opts.body), raw: opts.body });
    const r = postHandler(url, opts.body);
    return { ok: r.ok !== false, status: r.status ?? 200, json: async () => (r.json ?? { status: 1 }) };
  }
  if (!readQueue.length) throw new Error('test lỗi: GET thừa, readQueue rỗng');
  const spec = readQueue.shift();
  return { ok: true, status: 200, text: async () => JSON.stringify(spec) };
};

const HERE = dirname(fileURLToPath(import.meta.url));
const opsEngineSrc = readFileSync(join(HERE, 'cms-content-ops-engine.js'), 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
const runnerSrc = readFileSync(join(HERE, 'cms-bulk-insert-runner.js'), 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(`${opsEngineSrc}\n${runnerSrc}\nexport { cmsBulkInsert };`).toString('base64')
);
const { cmsBulkInsert } = mod;

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };

const BASE_TXT = '<p>Camera chính 48MP, hỗ trợ chụp đêm.</p>';
const OPS = [{ id: 'A', type: 'replace', find: '48MP', new: '50MP' }];
const AFTER_TXT = '<p>Camera chính 50MP, hỗ trợ chụp đêm.</p>';
const FORM_FIELDS = [{ name: 'txtSeoTitle', value: 'iPhone 18 Pro' }, { name: 'cboStatus', value: '2' }];
const spec = (over = {}) => ({ content: BASE_TXT, formFields: FORM_FIELDS, ...over });
const ROW = { row: 1, pid: 335308, site: 1, field: 'txtContent', expectedBeforeSha256: sha256(BASE_TXT), ops: OPS };

console.log('\n# apply-ops: dry đạt qua build + 5 bất biến -> DRY');
{
  readQueue = [spec()];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: true });
  const rec = r.rows[0];
  t('status DRY', rec.status === 'DRY', rec.status);
  t('_after đúng bản đã áp ops', rec._after === AFTER_TXT, rec._after);
  t('không POST khi dryRun', postCalls.length === 0);
}

console.log('\n# apply-ops: sha256 live khác expectedBeforeSha256 -> ABORT, 0 POST');
{
  readQueue = [spec({ content: '<p>Nội dung đã bị ai đó sửa tay.</p>' })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: true });
  const rec = r.rows[0];
  t('status ABORT', rec.status === 'ABORT', rec.status);
  t('lý do nhắc expectedBeforeSha256', /expectedBeforeSha256/.test(rec.reason || ''), rec.reason);
  t('không GET thêm / không POST', postCalls.length === 0);
}

console.log('\n# apply-ops: ghi thật -> DONE, verify byte-exact + không field khác đổi');
{
  readQueue = [spec(), spec(), spec({ content: AFTER_TXT })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status DONE', rec.status === 'DONE', JSON.stringify(rec.verify || rec.reason));
  t('POST tới /v2/Product/Submit', postCalls.length === 1 && postCalls[0].url === '/v2/Product/Submit', postCalls.map((c) => c.url));
  t('body mang đúng nội dung final', postCalls[0].body.includes(encodeURIComponent(AFTER_TXT).replace(/%20/g, '+')) || decodeURIComponent(postCalls[0].body).includes(AFTER_TXT));
}

console.log('\n# apply-ops: field khác bị đổi ngoài ý muốn sau ghi -> FAIL');
{
  readQueue = [spec(), spec(), spec({ content: AFTER_TXT, formFields: [{ name: 'txtSeoTitle', value: 'BỊ ĐỔI' }, { name: 'cboStatus', value: '2' }] })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status FAIL', rec.status === 'FAIL', rec.status);
  t('lý do liệt kê txtSeoTitle', /txtSeoTitle/.test(rec.reason || ''), rec.reason);
}

console.log('\n# apply-ops: re-GET trước POST lệch (người khác đang sửa) -> SKIP, 0 POST');
{
  readQueue = [spec(), spec({ content: '<p>Ai đó vừa sửa xong khi ta re-GET.</p>' })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status SKIP', rec.status === 'SKIP', rec.status);
  t('0 POST', postCalls.length === 0);
}

console.log('\n# apply-ops: hotReason happy path — chỉ HotReason đổi, multipart UpdateHTML');
{
  const HR_FIELDS = [
    { name: 'ProductID', value: '370982' }, { name: 'SiteID', value: '16' }, { name: 'LangID', value: 'vi-VN' },
    { name: 'HTMLDescription', value: '[desktop][/desktop] gallery' }, { name: 'HotReason', value: BASE_TXT },
    { name: 'SaveAllProductHTML', value: 'on', type: 'checkbox', checked: true },
  ];
  const HR = { contentSel: '#hotreason', formSel: '#myForm' };
  const hrSpec = (over = {}) => ({ ...HR, content: BASE_TXT, formFields: HR_FIELDS, ...over });
  const HR_ROW = { row: 2, pid: 370982, site: 16, field: 'hotReason', expectedBeforeSha256: sha256(BASE_TXT), ops: OPS };
  const savedFields = HR_FIELDS.map((f) => (f.name === 'HotReason' ? { ...f, value: AFTER_TXT } : f));
  readQueue = [hrSpec(), hrSpec(), hrSpec({ content: AFTER_TXT, formFields: savedFields })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [HR_ROW], dryRun: false });
  const rec = r.rows[0];
  const fd = postCalls[0]?.raw;
  t('status DONE', rec.status === 'DONE', JSON.stringify(rec.verify || rec.reason));
  t('POST tới /Product/Edit (không phải v2)', postCalls.length === 1 && postCalls[0].url === '/Product/Edit', postCalls.map((c) => c.url));
  t('body là multipart FormData', fd instanceof FormData);
  t('HotReason = bản final, đúng 1 giá trị', fd?.getAll('HotReason').length === 1 && fd.get('HotReason') === AFTER_TXT);
  t('có nút UpdateHTML', fd?.get('UpdateHTML') === 'Lưu lại');
  t('SaveAllProductHTML bị gỡ dù đang tick', fd && !fd.has('SaveAllProductHTML'));
  t('HTMLDescription gửi lại nguyên giá trị (chỉ HotReason đổi)', fd?.get('HTMLDescription') === '[desktop][/desktop] gallery');
}

console.log('\n# apply-ops: idempotence — ops đã áp ở lần chạy trước -> ALREADY, 0 POST');
{
  readQueue = [spec({ content: AFTER_TXT })];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [ROW], dryRun: false });
  const rec = r.rows[0];
  t('status ALREADY', rec.status === 'ALREADY', rec.status);
  t('0 POST', postCalls.length === 0);
}

console.log('\n# apply-ops: anchor khớp 0 lần (đã bị đổi khác) -> SKIP với lý do rõ');
{
  const badOps = [{ id: 'Z', type: 'replace', find: 'không có trong bài', new: 'x' }];
  const row = { ...ROW, ops: badOps, expectedBeforeSha256: sha256(BASE_TXT) };
  readQueue = [spec()];
  postCalls = [];
  const r = await cmsBulkInsert({ mode: 'apply-ops', rows: [row], dryRun: true });
  t('status SKIP', r.rows[0].status === 'SKIP', r.rows[0].status);
  t('lý do nhắc 0 lần', /0 lần/.test(r.rows[0].reason || ''), r.rows[0].reason);
}

console.log('\n# đối chứng: mode insert-link mặc định vẫn chạy được sau khi bundle ops engine');
{
  readQueue = [{ content: '<p>iPhone 18 Plus được nhiều người chọn mua.</p>', formFields: FORM_FIELDS }];
  const r = await cmsBulkInsert({ rows: [{ row: 1, pid: 1, site: 1, oldText: 'iPhone 18 Plus được nhiều người chọn mua.', sentence: 'Xem thêm.', links: [{ anchor: 'thêm', href: 'https://x.vn' }] }], dryRun: true });
  t('insert-link vẫn DRY bình thường (không bị ops engine ảnh hưởng)', r.rows[0].status === 'DRY', r.rows[0].status);
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
