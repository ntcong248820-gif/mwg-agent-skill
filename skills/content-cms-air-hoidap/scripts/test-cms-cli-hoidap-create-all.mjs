/**
 * Test --step create / --step all của run-air-hoidap-cli.mjs bằng MCP giả + fetch giả, và phạm vi dò
 * heading cũ của nghiệm thu live (liveCheck + verify-hoidap-live.mjs). Không trình duyệt, không CMS:
 * trang live giả chạy trên http 127.0.0.1.
 *   node .claude/skills/content-cms-air-hoidap/scripts/test-cms-cli-hoidap-create-all.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import http from 'node:http';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { main } from './run-air-hoidap-cli.mjs';
import { withRunner } from './cms-cli-mcp.mjs';
import { ledgerUpsert, liveCheck, planImageUploads, repoLedgerPath, slugError } from './cms-cli-air.mjs';
import { createFakeMcp, evalResult, textResult, pagesResult, never } from './cms-cli-fake-mcp.mjs';
import { inflightDir, readInflightMarker, writeInflightMarker } from './cms-cli-pipeline.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const rejects = async (p) => { try { await p; return null; } catch (e) { return e; } };

const ID = 1382098, NEW_ID = 1600123;
const ROOT = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-cli-hd2-'));
const CW = path.join(ROOT, 'cw');
fs.mkdirSync(path.join(CW, 'source'), { recursive: true });
fs.mkdirSync(path.join(CW, 'images-processed'), { recursive: true });
const IMG = { 'a-mot.jpg': Buffer.from('AAAA-bytes'), 'b-hai.jpg': Buffer.from('BBBB-bytes') };
for (const [n, b] of Object.entries(IMG)) fs.writeFileSync(path.join(CW, 'images-processed', n), b);
const SRC = `<h2>Mục một</h2><p>${'x'.repeat(600)}</p><p><img src="images-processed/a-mot.jpg" alt="một"></p><h2>Mục hai</h2><p><img src="images-processed/b-hai.jpg" alt="hai"></p>`;
fs.writeFileSync(path.join(CW, 'source/final-content.html'), SRC);
const CDN = (n, id = ID) => `https://cdnv2.tgdd.vn/mwg-static/common/News/${id}/${n}`;
let taskN = 0;
const taskRoots = [];
// Sổ tạo bài giờ ở CẤP REPO (tasks/_state/, suy từ segment "/tasks/" trong path) — mỗi newTask() cần
// một "repo giả" RIÊNG (mkdtemp base riêng) để các kịch bản test không chia sẻ nhầm ledger với nhau,
// đúng như hành vi cũ (mỗi task-dir độc lập) nhưng vẫn đi qua đúng code path repoLedgerPath thật.
const newTask = () => { const base = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-cli-hd2-task-')); taskRoots.push(base); const d = path.join(base, 'tasks', `t${++taskN}`); fs.mkdirSync(d, { recursive: true }); return d; };
const SPEC = { title: 'Top 5 laptop học tập tốt nhất', url: 'top-5-laptop-hoc-tap', metaTitle: 'Top 5 laptop học tập tốt nhất 2026', metaDescription: 'Gợi ý 5 laptop học tập bền, pin lâu.', keywords: ['laptop học tập', 'laptop sinh viên'], articleType: 'Top sản phẩm', childCategories: ['1673'] };
const specFile = (over = {}) => { const f = path.join(ROOT, `spec-${Math.random().toString(36).slice(2)}.json`); fs.writeFileSync(f, JSON.stringify({ ...SPEC, ...over })); return f; };

/** chrome-profile giả nhớ URL vừa mở → list_pages trả đúng tab đó (tạo xong mở tab bài mới). */
function profileFake(state) {
  return (bin, args, _o, cb) => {
    const url = args[args.length - 1];
    state.opened.push(url);
    state.tok = `tk${state.opened.length}`;
    cb(null, JSON.stringify({ bind_selector: `cdp-open=${state.tok}`, open_marker: `cdp-open=${state.tok}`, opened_url: url, profile_key: 'hd', profile_marker: 'cdp-profile=hd' }));
  };
}

function hdFake({ create = () => ({ status: 'DONE', stage: 'verify', newsId: NEW_ID, ms: 400, verify: { urlGot: SPEC.url }, failedVerify: [], warn: [] }),
  createDry = (fn) => ({ status: 'DRY', payload: { txtTitle: SPEC.title, txtUrl: SPEC.url, cboStatus: fn.match(/"status":"(\d)"/)?.[1], LstChildCategory: '1673', LstParentCategory: '1656' }, parentOpts: ['1656'], bodyLen: 40, placeholderBody: true }),
  writeDry = (fn, st) => ({ status: 'DRY', willWrite: { len: 900, imgs: 2 } }), write = () => ({ status: 'DONE', ms: 300, verify: { trimEndEqual: true } }),
  upload = () => ({ status: 'DONE', uploaded: { 'b-hai.jpg': CDN('b-hai.jpg') }, missing: [], wrongFolder: [] }),
  publish = () => ({ status: 'DONE', ms: 200, verify: { trangThaiDaXuatBan: true, bodyKhongDoi: true, chuyenMucGiu: true, fieldKhacBiDoi: [] } }),
  publishDry = () => ({ status: 'DRY', checks: { dungBai: true, formKhopServer: true, dangDungTrangThaiKyVong: true } }),
  onLive = () => {}, onCreate = () => {}, onPublish = () => {}, createHang = false } = {}) {
  const st = { opened: [], tok: null, files: 0 };
  const curId = () => (st.opened.at(-1) || '').match(/newsId=(\d+)/)?.[1] ?? null;
  const fake = createFakeMcp({
    tools: {
      list_pages: () => pagesResult(st.opened.length ? [{ id: 5 + st.opened.length, url: `${st.opened.at(-1)}#cdp-profile=hd&cdp-open=${st.tok}` }] : []),
      take_snapshot: () => textResult('uid=1_1 RootWebArea "CMS"\n  uid=1_9 button "claudeHdImages"\n  uid=1_8 button "claudeHdThumb"'),
      upload_file: ({ filePaths }) => { st.files = filePaths.length; st.lastUpload = filePaths; return textResult('ok'); },
      evaluate_script: ({ function: fn }) => {
        if (fn.includes('return await window.hdCreateArticle(')) {
          if (fn.includes('"dryRun":false')) { onCreate(st); return createHang ? never() : evalResult(create()); }
          return evalResult(createDry(fn));
        }
        if (fn.includes('return await window.hdUploadImages(')) return evalResult(upload());
        if (fn.includes('return await window.hdPublishArticle(')) {
          if (fn.includes('"dryRun":false')) { onPublish(st); return evalResult(publish()); }
          return evalResult(publishDry());
        }
        if (fn.includes('return await window.hdWriteArticle(')) {
          if (fn.includes('"dryRun":false')) { onLive(st); return evalResult(write()); }
          const out = writeDry(fn, st);
          return evalResult({ checks: {}, changes: {}, ...out, backup: { newsId: Number(curId()), at: 'x', content_FaqNews_DB: '<h2>Bài cũ</h2><p>cũ</p>', fields: { txtUrl: 'top-laptop-hoc-tap' }, cates: { parent: ['1656'], child: ['1673'] }, fullPageHtml: '<html>page</html>' } });
        }
        if (fn.includes("setAttribute('aria-label'")) return evalResult({ id: 'x', hasName: false, inForm: false });
        if (fn.includes('.files.length')) return evalResult(st.files);
        if (fn.includes("getElementById('hdNewsId')?.value ?? null")) return evalResult({ id: curId(), body: true });
        if (fn.includes('.remove()')) return evalResult('ok');
        throw new Error('evaluate không mong đợi: ' + fn.slice(0, 80));
      },
    },
  });
  fake.st = st;
  return fake;
}

/** CDN giả: heads[name] = 200|404; bytes khác thì trả 'khác'. */
function fetcher({ heads = {}, remote = IMG } = {}) {
  const calls = [];
  const fn = async (url, opts = {}) => {
    calls.push({ url, method: opts.method || 'GET' });
    const n = decodeURIComponent(url.split('/').pop());
    if (opts.method === 'HEAD') return { status: heads[n] ?? 404 };
    return { status: 200, arrayBuffer: async () => remote[n] ?? Buffer.from('?') };
  };
  fn.calls = calls;
  return fn;
}
let verifyCalls = 0;
const verifyArgs = [];
const nodeExec = (bin, args, opts, cb) => {
  if (args[0].endsWith('verify-hoidap-live.mjs')) { verifyCalls++; verifyArgs.push(args.join(' ')); return cb(null, JSON.stringify({ pass: true, headings: '2/2', images: '2/2', oldHeadingsStillLive: [] }), ''); }
  return execFile(bin, args, opts, cb);
};
const sleeps = [];
const run = (fake, W, argv, fetchFn = fetcher()) => main(['--task-dir', W, '--timeout-sec', '0.3', ...argv], {
  spawnFn: fake.spawnFn, execFileFn: profileFake(fake.st), nodeExecFn: nodeExec, fetchFn, sleepFn: async (ms) => { sleeps.push(ms); }, log: process.env.DEBUG ? console.log : () => {}, tasksRoot: path.dirname(W),
});
const evals = (fake, s) => fake.calls.filter((c) => c.name === 'evaluate_script' && c.args.function.includes(s));
const ledger = (W) => { try { return JSON.parse(fs.readFileSync(repoLedgerPath(W, 'hoidap'), 'utf8')); } catch { return null; } };

{
  const runner = fs.readFileSync(path.join(HERE, 'air-hoidap-runner.js'), 'utf8');
  let ok = true;
  try { new Function(`return (${withRunner(runner, 'return await window.hdCreateArticle({});')})`); } catch { ok = false; }
  t('runner có hdCreateArticle, JS hợp lệ', ok && runner.includes('window.hdCreateArticle'));
  t('slugError bắt dấu/hoa/gạch kép', slugError('Top-laptop') && slugError('top--laptop') && slugError('top-laptop-') && slugError('laptop-học') && !slugError('top-5-laptop'));
}

console.log('\n# create — kiểm tĩnh trước khi mở trình duyệt');
{
  const fake = hdFake();
  let e = await rejects(run(fake, newTask(), ['--step', 'create', '--create-file', specFile()]));
  t('thiếu --status → exit 2', e?.exitCode === 2 && /--status/.test(e.message), e?.message);
  e = await rejects(run(fake, newTask(), ['--step', 'create', '--create-file', specFile({ url: 'Top Laptop' }), '--status', '3']));
  t('slug sai dạng → exit 2', e?.exitCode === 2 && /sai dạng/.test(e.message), e?.message);
  e = await rejects(run(fake, newTask(), ['--step', 'create', '--create-file', specFile({ childCategories: [], title: 'x'.repeat(71) }), '--status', '3']));
  t('chuyên mục rỗng + title >70 báo cùng lúc', /childCategories rỗng/.test(e?.message) && /title 71>70/.test(e?.message), e?.message);
  e = await rejects(run(fake, newTask(), ['--step', 'create', '--create-file', specFile(), '--status', '3', '--news-id', '5']));
  t('create kèm --news-id → từ chối', e?.exitCode === 2, e?.message);
  t('mọi lỗi trên ném trước khi spawn MCP', fake.spawned === 0);
}

console.log('\n# create — dry');
{
  const W = newTask();
  const fake = hdFake();
  const code = await run(fake, W, ['--step', 'create', '--create-file', specFile(), '--status', 'pending']);
  const saved = fs.readdirSync(path.join(W, 'data/raw/cms-create'));
  t('dry create → exit 0', code === 0, code);
  t('mở đúng trang tạo mới newsId=0', fake.st.opened[0]?.endsWith('/v2/Faq/NewsEdit?newsId=0'));
  t('status alias pending → 3 trong payload', /"status":"3"/.test(evals(fake, 'hdCreateArticle(')[0]?.args.function || ''));
  t('payload lưu vào data/raw/cms-create', saved.some((f) => f.startsWith('create-dry-hoidap-top-5-laptop-hoc-tap')));
  t('không có lời gọi dryRun:false', evals(fake, '"dryRun":false').length === 0);
  t('không ghi sổ bài đã tạo', ledger(W) === null);
  const bad = hdFake({ createDry: () => ({ status: 'ABORT', failed: ['chuyenMucConCo'], childBad: ['9999'] }) });
  t('trang báo bất biến fail → exit 1', (await run(bad, newTask(), ['--step', 'create', '--create-file', specFile(), '--status', '3'])) === 1);
}

console.log('\n# create — live (MCP giả)');
{
  const W = newTask();
  let pendingBeforePost = false;
  const fake = hdFake({ onCreate: () => { pendingBeforePost = ledger(W)?.[0]?.status === 'PENDING'; } });
  const code = await run(fake, W, ['--step', 'create', '--create-file', specFile(), '--status', '2', '--live']);
  const L = ledger(W);
  t('live create → exit 0', code === 0, code);
  t('dry trong trang chạy trước POST', evals(fake, '"dryRun":true').length === 1 && evals(fake, '"dryRun":false').length === 1);
  t('sổ ghi PENDING TRƯỚC lúc POST', pendingBeforePost);
  t('sổ có newsId + liveUrl', L?.[0]?.newsId === NEW_ID && L[0].liveUrl === `https://www.thegioididong.com/hoi-dap/${SPEC.url}-${NEW_ID}`, L);
  const e = await rejects(run(hdFake(), W, ['--step', 'create', '--create-file', specFile(), '--status', '2', '--live']));
  t('tạo lại cùng url → từ chối, chỉ đường --news-id', /không tạo lần 2/.test(e?.message || '') && e.message.includes(`--news-id ${NEW_ID}`), e?.message);

  const W2 = newTask();
  const f2 = hdFake({ create: () => ({ status: 'FAIL', stage: 'submit', cmsReply: { status: -1, error: 'Url đã tồn tại' } }) });
  t('CMS trả lỗi (không id) → exit 1', (await run(f2, W2, ['--step', 'create', '--create-file', specFile(), '--status', '3', '--live'])) === 1);
  t('sổ giữ FAIL_NO_ID để chặn tạo lại mù', ledger(W2)?.[0]?.status === 'FAIL_NO_ID');
  const e2 = await rejects(run(hdFake(), W2, ['--step', 'create', '--create-file', specFile(), '--status', '3', '--live']));
  t('lần sau bị chặn tới khi người kiểm CMS', /kiểm danh sách bài|Kiểm danh sách/i.test(e2?.message || ''), e2?.message);

  const W3 = newTask();
  const f3 = hdFake({ createHang: true });
  t('timeout khi tạo → exit 1, giữ tab, sổ PENDING', (await run(f3, W3, ['--step', 'create', '--create-file', specFile(), '--status', '3', '--live'])) === 1
    && !f3.calls.some((c) => c.name === 'close_page') && ledger(W3)?.[0]?.status === 'PENDING');
}

console.log('\n# sổ PENDING còn sót (process chết ngay sau khi claim) → rerun ABORT, 0 POST tạo lại');
{
  // Mô phỏng đúng ca "chết giữa chừng": ledgerClaim() đã ghi PENDING (process trước đó bị
  // kill NGAY SAU claim, trước cả khi POST tạo bài) — rerun phải ABORT ở bước kiểm sớm
  // (readLedger prior check), không được tự POST lại mù.
  const W = newTask();
  const url = 'pending-ledger-orphan-test';
  ledgerUpsert(repoLedgerPath(W, 'hoidap'), { key: `hoidap:${url}`, status: 'PENDING', url, title: 'x', createdStatus: '3' });
  const fake = hdFake();
  const e = await rejects(run(fake, W, ['--step', 'create', '--create-file', specFile({ url }), '--status', '3', '--live']));
  t('rerun với sổ PENDING sót lại → ABORT (thông điệp rõ ràng), exit ≠ 0', e?.exitCode >= 1 && /có thể đã tạo bài mà không nhận được newsId/.test(e?.message || ''), e?.message);
  t('0 lần mở trình duyệt (chặn trước khi spawn MCP)', fake.spawned === 0, fake.spawned);
  t('sổ vẫn PENDING (không tự đổi trạng thái)', ledger(W)?.[0]?.status === 'PENDING', ledger(W));
}

console.log('\n# all — bài có sẵn');
{
  // a-mot.jpg đã có trên CDN, trùng byte → dùng lại; b-hai.jpg 404 → upload.
  const W = newTask();
  sleeps.length = 0; verifyCalls = 0;
  const order = [];
  const fake = hdFake({
    writeDry: (fn, st) => { order.push('dry'); return fn.includes(CDN('b-hai.jpg')) && !order.includes('upload') ? { status: 'ABORT', failed: ['anhSongHet'], deadImg: [`404 ${CDN('b-hai.jpg')}`] } : { status: 'DRY', willWrite: { len: 900, imgs: 2 } }; },
    upload: () => { order.push('upload'); return { status: 'DONE', uploaded: { 'b-hai.jpg': CDN('b-hai.jpg') }, missing: [], wrongFolder: [] }; },
    onLive: () => order.push('live'),
  });
  const code = await run(fake, W, ['--step', 'all', '--news-id', String(ID), '--workspace', CW, '--expect-images', '2', '--live'], fetcher({ heads: { 'a-mot.jpg': 200 } }));
  const html = fs.readFileSync(path.join(W, `data/processed/final-content-cms-${ID}.html`), 'utf8');
  t('all --live happy → exit 0', code === 0, code);
  t('chỉ upload file 404 (b-hai.jpg)', fake.st.lastUpload?.length === 1 && fake.st.lastUpload[0].endsWith('b-hai.jpg'), fake.st.lastUpload);
  t('thứ tự: pre-dry → upload → dry lại → dry sát lúc ghi (guard) → ghi', order.join(',') === 'dry,upload,dry,dry,live', order);
  t('HTML CMS dùng URL CDN cho cả 2 ảnh', html.includes(CDN('a-mot.jpg')) && html.includes(CDN('b-hai.jpg')) && !html.includes('images-processed/'));
  t('đợi 60s rồi mới nghiệm thu live', sleeps[0] === 60000 && verifyCalls === 1, { sleeps, verifyCalls });
  t('backup pre-live có trên đĩa', fs.readdirSync(path.join(W, `data/raw/cms-backup/${ID}`)).some((d) => d.startsWith('pre-live-')));
  t('URL live suy từ txtUrl backup khi không truyền --live-url', verifyArgs.at(-1)?.includes('https://www.thegioididong.com/hoi-dap/top-laptop-hoc-tap-1382098'), verifyArgs.at(-1));
}
{
  const W = newTask();
  const fake = hdFake({ writeDry: () => ({ status: 'ABORT', failed: ['anhSongHet'], deadImg: [`404 ${CDN('b-hai.jpg')}`, `404 ${CDN('a-mot.jpg')}`] }) });
  const code = await run(fake, W, ['--step', 'all', '--news-id', String(ID), '--workspace', CW], fetcher());
  t('all dry: ảnh chưa up chết đúng dự kiến → exit 0', code === 0, code);
  t('all dry: không upload, không ghi', evals(fake, 'return await window.hdUploadImages(').length === 0 && evals(fake, '"dryRun":false').length === 0 && !fake.calls.some((c) => c.name === 'upload_file'));
}
{
  const fake = hdFake({ writeDry: () => ({ status: 'ABORT', failed: ['giuUrl'] }) });
  const code = await run(fake, newTask(), ['--step', 'all', '--news-id', String(ID), '--workspace', CW, '--live'], fetcher());
  t('all --live: bất biến fail ở pre-dry → exit 1', code === 1, code);
  t('... dừng TRƯỚC mọi POST (không upload, không ghi)', evals(fake, 'return await window.hdUploadImages(').length === 0 && evals(fake, '"dryRun":false').length === 0 && !fake.calls.some((c) => c.name === 'upload_file'));
}
{
  const fake = hdFake();
  const code = await run(fake, newTask(), ['--step', 'all', '--news-id', String(ID), '--workspace', CW, '--live'], fetcher({ heads: { 'a-mot.jpg': 200 }, remote: { 'a-mot.jpg': Buffer.from('khác hẳn') } }));
  t('tên đã có trên CDN nhưng lệch byte → exit 1, không mở trình duyệt', code === 1 && fake.spawned === 0, { code, spawned: fake.spawned });
}
{
  const fake = hdFake({ writeDry: () => ({ status: 'ABORT', failed: ['anhSongHet'], deadImg: ['404 https://cdnv2.tgdd.vn/khac.jpg'] }) });
  t('dry: ảnh chết KHÔNG thuộc danh sách chờ up → không tha, exit 1', (await run(fake, newTask(), ['--step', 'all', '--news-id', String(ID), '--workspace', CW], fetcher())) === 1);
}

console.log('\n# all --create-file');
{
  // Không --publish: tạo ở status 3 (Chờ duyệt) → ghi xong PHẢI hoãn/bỏ nghiệm thu live
  // (LIVE_SKIPPED_UNPUBLISHED, #9) vì bài chưa Xuất bản, không phải lỗi ghi.
  const W = newTask();
  sleeps.length = 0; verifyCalls = 0;
  let uploaded = false;
  const both = [`404 ${CDN('a-mot.jpg', NEW_ID)}`, `404 ${CDN('b-hai.jpg', NEW_ID)}`];
  const fake = hdFake({
    upload: () => { uploaded = true; return { status: 'DONE', uploaded: { 'a-mot.jpg': CDN('a-mot.jpg', NEW_ID), 'b-hai.jpg': CDN('b-hai.jpg', NEW_ID) }, missing: [], wrongFolder: [] }; },
    writeDry: () => (uploaded ? { status: 'DRY', willWrite: { len: 900, imgs: 2 } } : { status: 'ABORT', failed: ['anhSongHet'], deadImg: both }),
  });
  const code = await run(fake, W, ['--step', 'all', '--create-file', specFile(), '--status', '3', '--workspace', CW, '--live'], fetcher());
  t('all --create-file --live (không publish): create → upload → ghi → exit 0', code === 0, code);
  t('upload nhắm đúng newsId mới', evals(fake, 'return await window.hdUploadImages(')[0]?.args.function.includes(`"newsId":${NEW_ID}`));
  t('tab tạo mới (newsId=0) rồi tab bài mới', fake.st.opened[0].endsWith('newsId=0') && fake.st.opened.some((u) => u.endsWith(`newsId=${NEW_ID}`)));
  t('ghi thật nhắm bài mới', evals(fake, '"dryRun":false').some((c) => c.args.function.includes(`"newsId":${NEW_ID}`) && c.args.function.includes('hdWriteArticle')));
  t('#9: bài chưa Xuất bản, không --publish → KHÔNG gọi nghiệm thu live', evals(fake, 'return await window.hdPublishArticle(').length === 0 && verifyCalls === 0, verifyCalls);
}
console.log('\n# all --create-file --publish (owner 24/09/2026: create 3 → ghi → publish → live verify)');
{
  const W = newTask();
  sleeps.length = 0; verifyCalls = 0;
  const order = [];
  let uploaded = false;
  const both = [`404 ${CDN('a-mot.jpg', NEW_ID)}`, `404 ${CDN('b-hai.jpg', NEW_ID)}`];
  const fake = hdFake({
    upload: () => { uploaded = true; return { status: 'DONE', uploaded: { 'a-mot.jpg': CDN('a-mot.jpg', NEW_ID), 'b-hai.jpg': CDN('b-hai.jpg', NEW_ID) }, missing: [], wrongFolder: [] }; },
    writeDry: () => (uploaded ? { status: 'DRY', willWrite: { len: 900, imgs: 2 } } : { status: 'ABORT', failed: ['anhSongHet'], deadImg: both }),
    onLive: () => order.push('write'), onPublish: () => order.push('publish'),
  });
  const code = await run(fake, W, ['--step', 'all', '--create-file', specFile(), '--status', '3', '--workspace', CW, '--live', '--publish'], fetcher());
  t('--publish: create(3) → ghi → xuất bản → nghiệm thu live → exit 0', code === 0, code);
  t('thứ tự: ghi TRƯỚC xuất bản', order.join(',') === 'write,publish', order);
  t('publish nhắm đúng newsId mới, expectCurrentStatus 3', evals(fake, 'return await window.hdPublishArticle(').some((c) => c.args.function.includes(`"newsId":${NEW_ID}`) && c.args.function.includes('"expectCurrentStatus":"3"')));
  t('nghiệm thu live CHẠY SAU khi publish xong', verifyCalls === 1 && verifyArgs.at(-1)?.includes(`https://www.thegioididong.com/hoi-dap/${SPEC.url}-${NEW_ID}`), { verifyCalls, last: verifyArgs.at(-1) });
  t('sổ ghi published sau khi --publish đạt', !!ledger(W).find((r) => r.newsId === NEW_ID)?.published);
}
{
  // --publish chỉ dùng với --status 1/3 (#8): status 2 (Xuất bản ngay) không có nghĩa gì để "publish thêm".
  const e = await rejects(run(hdFake(), newTask(), ['--step', 'all', '--create-file', specFile(), '--status', '2', '--workspace', CW, '--publish']));
  t('--publish + --status 2 → từ chối (không xuất bản ngầm thân bài tạm)', e?.exitCode === 2 && /--publish chỉ dùng/.test(e?.message || ''), e?.message);
}
{
  // stepPublish standalone: từ chối bài không nằm trong sổ, hoặc sổ ghi createdStatus khác 3.
  const W = newTask();
  const e1 = await rejects(run(hdFake(), W, ['--step', 'publish', '--news-id', '999999']));
  t('--step publish: newsId không có trong sổ → từ chối', e1?.exitCode === 2 && /không có trong sổ/.test(e1?.message || ''), e1?.message);
}

console.log('\n# marker in-flight (publish): 3 ca phục hồi từ lần chạy trước bị dừng giữa chừng');
{
  const pubId = 1690001;
  const idir = (W) => inflightDir(W, 'cms-backup');
  const key = `hd-publish-${pubId}`;
  const prep = () => {
    const W = newTask();
    ledgerUpsert(repoLedgerPath(W, 'hoidap'), { key: 'hoidap:publish-marker-test', newsId: pubId, url: 'publish-marker-test', title: 'x', createdStatus: '3' });
    return W;
  };

  // Ca 1 — DONE_RECOVERED: dry-check hiện tại trả ABORT vì bài ĐÃ ở trạng thái 2 (Xuất bản) —
  // lần trước thật ra đã đổi trạng thái thành công, process chỉ bị kill trước khi đọc kết quả.
  {
    const W = prep();
    writeInflightMarker(idir(W), { key, row: { step: 'publish', intendedStatus: '2' }, beforeSha: 'x' });
    let posted = 0;
    const fake = hdFake({ publishDry: () => ({ status: 'ABORT', reason: 'trạng thái hiện tại (2) khác kỳ vọng (3)', currentStatus: '2' }), onPublish: () => { posted++; } });
    const code = await run(fake, W, ['--step', 'publish', '--news-id', String(pubId)]);
    t('DONE_RECOVERED: exit 0', code === 0, code);
    t('DONE_RECOVERED: marker đã xoá', readInflightMarker(idir(W), key) === null);
    t('DONE_RECOVERED: không đổi trạng thái lại (0 POST)', posted === 0);
    t('DONE_RECOVERED: sổ đã đánh dấu published', !!ledger(W).find((r) => r.newsId === pubId)?.published);
  }
  // Ca 2 — SAFE_PROCEED: dry-check vẫn thấy bài Chờ duyệt (status 3) -> an toàn xuất bản lại.
  {
    const W = prep();
    writeInflightMarker(idir(W), { key, row: { step: 'publish', intendedStatus: '2' }, beforeSha: 'x' });
    let posted = 0;
    const fake = hdFake({ onPublish: () => { posted++; } }); // publishDry mặc định = DRY (status 3)
    const code = await run(fake, W, ['--step', 'publish', '--news-id', String(pubId), '--live']);
    t('SAFE_PROCEED: exit 0', code === 0, code);
    t('SAFE_PROCEED: marker đã xoá sau khi xuất bản xong', readInflightMarker(idir(W), key) === null);
    t('SAFE_PROCEED: vẫn xuất bản lại bình thường (1 lần POST)', posted === 1);
  }
  // Ca 3 — NEEDS_MANUAL_CHECK: dry-check trả trạng thái không rõ ràng (không phải "đã publish"
  // cũng không phải "vẫn chờ duyệt") -> GIỮ marker, không đoán, không POST.
  {
    const W = prep();
    writeInflightMarker(idir(W), { key, row: { step: 'publish', intendedStatus: '2' }, beforeSha: 'x' });
    const fake = hdFake({ publishDry: () => ({ status: 'ABORT', reason: 'sai trang — cần /v2/Faq/NewsEdit' }) });
    const code = await run(fake, W, ['--step', 'publish', '--news-id', String(pubId), '--live']);
    t('NEEDS_MANUAL_CHECK: exit 1', code === 1, code);
    t('NEEDS_MANUAL_CHECK: marker VẪN CÒN', readInflightMarker(idir(W), key)?.key === key);
    t('NEEDS_MANUAL_CHECK: không đổi trạng thái sổ', !ledger(W).find((r) => r.newsId === pubId)?.published);
  }
}

console.log('\n# xuất bản: lỗi sau khi gọi POST → UNKNOWN, giữ marker in-flight');
{
  const pubId = 1690002;
  const W = newTask();
  ledgerUpsert(repoLedgerPath(W, 'hoidap'), { key: 'hoidap:publish-unknown-test', newsId: pubId, url: 'publish-unknown-test', title: 'x', createdStatus: '3' });
  const fake = hdFake({ publish: () => ({ status: 'UNKNOWN', reason: 'mất session khi đọc lại', ms: 900 }) });
  const code = await run(fake, W, ['--step', 'publish', '--news-id', String(pubId), '--live']);
  t('UNKNOWN sau publish → exit 1, không đoán DONE', code === 1, code);
  t('UNKNOWN: marker in-flight VẪN CÒN', readInflightMarker(inflightDir(W, 'cms-backup'), `hd-publish-${pubId}`)?.key === `hd-publish-${pubId}`);
  t('UNKNOWN: sổ chưa đánh dấu published', !ledger(W).find((r) => r.newsId === pubId)?.published);
}
{
  const W = newTask();
  const fake = hdFake({ writeDry: (fn) => (fn.includes('images-processed') ? { status: 'ABORT', failed: ['khongConAnhLocal'] } : { status: 'DRY', willWrite: { len: 1, imgs: 2 } }) });
  const code = await run(fake, W, ['--step', 'all', '--create-file', specFile(), '--status', '3', '--workspace', CW], fetcher());
  t('all --create-file dry: dừng sau create dry, exit 0', code === 0 && evals(fake, '"dryRun":false').length === 0 && evals(fake, 'return await window.hdWriteArticle(').length === 0, code);
  const e = await rejects(run(hdFake(), newTask(), ['--step', 'all', '--create-file', specFile(), '--status', '3', '--workspace', CW, '--title', 'x']));
  t('all --create-file cấm --title (tránh nhập nhằng)', e?.exitCode === 2, e?.message);
}

console.log('\n# planImageUploads');
{
  const files = Object.keys(IMG).map((n) => path.join(CW, 'images-processed', n));
  const p1 = await planImageUploads(`https://cdnv2.tgdd.vn/mwg-static/common/News/${ID}/`, files, fetcher({ heads: { 'a-mot.jpg': 200 } }));
  t('200 + trùng byte → reuse; 404 → upload', Object.keys(p1.reuse).join() === 'a-mot.jpg' && p1.upload.length === 1 && !p1.conflicts.length);
  const p2 = await planImageUploads('https://x/', files, async () => { throw new Error('mạng'); });
  t('lỗi mạng → errors, không upload', p2.errors.length === 2 && p2.upload.length === 0);
}

console.log('\n# nghiệm thu live: heading cũ chỉ dò trong thẻ heading');
{
  const MINE = `<h2>Top laptop học tập</h2><p>${'y'.repeat(50)}</p><h3>Asus Vivobook 15</h3>`;
  const OLD = '<h2>Top laptop học tập</h2><h3>Dell 15 DC15255</h3>';
  const promo = '<div class="promo"><span>GIẢM SỐC</span><a>Dell 15 DC15255</a></div>';
  // #12: liveCheck đòi fingerprint (TEXT thân bài) có mặt liền mạch trên live — nhúng nguyên MINE (không
  // chen promo vào giữa) để mô phỏng đúng ca "trang live đã thật sự mang bản mới"; promo là nội dung
  // KHÁC (widget khuyến mãi) nằm ngoài luồng thân bài, không được chen vào giữa làm đứt mạch fingerprint.
  const pageOk = `<html><h1>x</h1>${MINE}${promo}</html>`;
  const pageBad = `<html>${MINE}<h3>Dell 15 DC15255</h3></html>`;
  const f = (html) => async () => ({ status: 200, text: async () => html });
  const ok = await liveCheck({ url: 'https://x/y', html: MINE, old: OLD, clearcache: false, fetchFn: f(pageOk) });
  const bad = await liveCheck({ url: 'https://x/y', html: MINE, old: OLD, clearcache: false, fetchFn: f(pageBad) });
  t('liveCheck: tên SP cũ trong khối promo (không phải heading) → PASS', ok.pass && ok.oldHeadingsStillLive.length === 0, ok);
  t('liveCheck: tên SP cũ trong <h3> → FAIL', !bad.pass && bad.oldHeadingsStillLive[0] === 'Dell 15 DC15255', bad);

  const server = http.createServer((req, res) => { res.writeHead(200, { 'content-type': 'text/html' }); res.end(req.url.startsWith('/bad') ? pageBad : pageOk); });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  fs.writeFileSync(path.join(ROOT, 'mine.html'), MINE);
  fs.writeFileSync(path.join(ROOT, 'old.html'), OLD);
  const script = path.join(HERE, 'verify-hoidap-live.mjs');
  const runV = (u) => new Promise((r) => execFile(process.execPath, [script, '--url', `http://127.0.0.1:${port}${u}`, '--html', path.join(ROOT, 'mine.html'), '--old', path.join(ROOT, 'old.html')], (err, stdout) => r({ code: err ? err.code : 0, j: JSON.parse(stdout) })));
  const vOk = await runV('/ok'), vBad = await runV('/bad');
  server.close();
  t('verify-hoidap-live: promo chứa tên SP cũ → PASS (exit 0)', vOk.code === 0 && vOk.j.pass && vOk.j.oldHeadingsStillLive.length === 0, vOk);
  t('verify-hoidap-live: <h3> tên SP cũ → FAIL (exit 1)', vBad.code === 1 && vBad.j.oldHeadingsStillLive.includes('Dell 15 DC15255'), vBad);
}

console.log('\n# #10: sổ tạo bài cấp repo — 2 task-dir KHÁC NHAU cùng repo phải chặn được tạo trùng');
{
  // Mô phỏng "task khác" (work-item vs task cha, hoặc 2 worker song song): 2 task-dir SIBLING dưới
  // CÙNG MỘT tasks/ — trước fix #10, mỗi task-dir có sổ riêng (rỗng) nên cả 2 đều tạo được, ra 2 bài trùng.
  const crossBase = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-cli-hd2-cross-'));
  const W1 = path.join(crossBase, 'tasks', 'task-cha'); fs.mkdirSync(W1, { recursive: true });
  const W2 = path.join(crossBase, 'tasks', 'work-item-con'); fs.mkdirSync(W2, { recursive: true });
  const urlOver = { url: 'infobox-cross-task-dir-test' };
  const code1 = await run(hdFake(), W1, ['--step', 'create', '--create-file', specFile(urlOver), '--status', '3', '--live']);
  t('task-dir 1 tạo được (sổ trống)', code1 === 0, code1);
  const e2 = await rejects(run(hdFake(), W2, ['--step', 'create', '--create-file', specFile(urlOver), '--status', '3', '--live']));
  t('task-dir 2 (khác task, cùng repo) → BỊ CHẶN tạo trùng bởi sổ cấp repo', /không tạo lần 2/.test(e2?.message || ''), e2?.message);
  t('cả 2 task-dir đọc CÙNG MỘT sổ (repoLedgerPath)', repoLedgerPath(W1, 'hoidap') === repoLedgerPath(W2, 'hoidap'));
  fs.rmSync(crossBase, { recursive: true, force: true });
}

console.log('\n# #2: tạo bài — đọc lại thất bại (mất session) → UNKNOWN, không đoán DONE/FAIL');
{
  const W = newTask();
  const fake = hdFake({ create: () => ({ status: 'UNKNOWN', stage: 'readback', newsId: 1700999, ms: 500, reason: 'không thấy #content_FaqNews — mất session hoặc sai newsId' }) });
  const code = await run(fake, W, ['--step', 'create', '--create-file', specFile({ url: 'unknown-readback-test' }), '--status', '3', '--live']);
  t('UNKNOWN readback → exit 1 (không đoán thành công)', code === 1, code);
  const row = ledger(W)?.find((r) => r.newsId === 1700999);
  t('sổ ghi UNKNOWN (không PENDING, không DONE) kèm newsId + lý do', row?.status === 'UNKNOWN' && !!row.reason, row);
  const e = await rejects(run(hdFake(), W, ['--step', 'create', '--create-file', specFile({ url: 'unknown-readback-test' }), '--status', '3', '--live']));
  t('lần sau vẫn bị chặn tạo trùng (sổ giữ newsId dù UNKNOWN, chỉ đường --news-id)', /không tạo lần 2/.test(e?.message || '') && e.message.includes('--news-id 1700999'), e?.message);
}

console.log('\n# #7: thân bài đã khớp DB từ trước → ALREADY, không POST, exit 0 (coi như đạt)');
{
  const W = newTask();
  const htmlArg = ['--html', path.join(CW, 'source/final-content.html')];
  await run(hdFake(), W, ['--step', 'write', '--news-id', String(ID), ...htmlArg], fetcher()); // dry trước để có dry-{id}.json đã duyệt
  const fake = hdFake({ write: () => ({ status: 'ALREADY', checks: {} }) });
  const code = await run(fake, W, ['--step', 'write', '--news-id', String(ID), ...htmlArg, '--live', '--live-url', 'https://www.thegioididong.com/hoi-dap/x-1382098'], fetcher());
  t('ALREADY → exit 0 (coi như đạt, không phải lỗi)', code === 0, code);
}

fs.rmSync(ROOT, { recursive: true, force: true });
for (const b of taskRoots) fs.rmSync(b, { recursive: true, force: true });
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
