/**
 * Test run-air-hoidap-cli.mjs bằng MCP giả. Không trình duyệt, không CMS, không mạng:
 * fetch CDN và verify-hoidap-live được thay bằng bản giả; hoidap-body-tools chạy thật (local).
 *   node .claude/skills/content-cms-air-hoidap/scripts/test-cms-cli-hoidap.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { EventEmitter } from 'node:events';
import { fileURLToPath } from 'node:url';
import { main } from './run-air-hoidap-cli.mjs';
import { withRunner } from './cms-cli-mcp.mjs';
import { createFakeMcp, evalResult, textResult, pagesResult, fakeChromeProfile, never } from './cms-cli-fake-mcp.mjs';
import { inflightDir, readInflightMarker, sha256, writeInflightMarker } from './cms-cli-pipeline.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const rejects = async (p) => { try { await p; return null; } catch (e) { return e; } };

const ID = 1576257;
const ROOT = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-cli-hd-'));
const CW = path.join(ROOT, 'cw');
fs.mkdirSync(path.join(CW, 'source'), { recursive: true });
fs.mkdirSync(path.join(CW, 'images-processed'), { recursive: true });
const IMG = { 'a-mot.jpg': Buffer.from('AAAA-bytes'), 'b-hai.jpg': Buffer.from('BBBB-bytes') };
for (const [n, b] of Object.entries(IMG)) fs.writeFileSync(path.join(CW, 'images-processed', n), b);
const SRC = `<h2>Mục một</h2><p>${'x'.repeat(600)}</p><p><img src="images-processed/a-mot.jpg" alt="một"></p><h2>Mục hai</h2><p><img src="images-processed/b-hai.jpg" alt="hai"></p>`;
fs.writeFileSync(path.join(CW, 'source/final-content.html'), SRC);
const CDN = (n) => `https://cdnv2.tgdd.vn/mwg-static/common/News/${ID}/${n}`;
let taskN = 0;
const newTask = () => { const d = path.join(ROOT, 'tasks', `t${++taskN}`); fs.mkdirSync(d, { recursive: true }); return d; };
const TAB = `https://cms.thegioididong.com/v2/Faq/NewsEdit?newsId=${ID}#cdp-profile=hd&cdp-open=tk`;
const DB_BODY = '<h2>Bài cũ</h2><p>cũ</p>';

function hdFake({ upload = (dry) => (dry ? { status: 'DRY', cdnHead: { 'a-mot.jpg': 404, 'b-hai.jpg': 404 }, taken: [] } : { status: 'DONE', uploaded: { 'a-mot.jpg': CDN('a-mot.jpg'), 'b-hai.jpg': CDN('b-hai.jpg') }, missing: [], wrongFolder: [] }),
  dryDb = () => DB_BODY, write = () => ({ status: 'DONE', ms: 31000, verify: { trimEndEqual: true } }), onLive = () => {}, liveHang = false } = {}) {
  let uploaded = 0;
  return createFakeMcp({
    tools: {
      list_pages: () => pagesResult([{ id: 5, url: TAB }]),
      take_snapshot: () => textResult('uid=1_1 RootWebArea "CMS"\n  uid=1_9 button "claudeHdImages"\n  uid=1_10 button "allImagesNews"'),
      upload_file: ({ filePaths }) => { uploaded = filePaths.length; return textResult('ok'); },
      evaluate_script: ({ function: fn }) => {
        // Code nạp runner chứa sẵn cả chuỗi '.files.length' / 'hdNewsId' → xét lời gọi runner trước.
        if (fn.includes('return await window.hdUploadImages(')) return evalResult(upload(fn.includes('"dryRun":true')));
        if (fn.includes('return await window.hdWriteArticle(')) {
          if (fn.includes('"dryRun":false')) { onLive(); return liveHang ? never() : evalResult(write()); }
          return evalResult({ status: 'DRY', checks: { dungBai: true }, changes: {}, backup: { newsId: ID, at: 'x', content_FaqNews_DB: dryDb(), fields: { txtUrl: 'u' }, cates: { parent: ['1'], child: ['2'] }, fullPageHtml: '<html>page</html>' } });
        }
        if (fn.includes("setAttribute('aria-label'")) return evalResult({ id: 'claudeHdImages', hasName: false, inForm: false });
        if (fn.includes('.files.length')) return evalResult(uploaded);
        if (fn.includes("getElementById('hdNewsId')?.value ?? null")) return evalResult({ id: String(ID), body: true });
        if (fn.includes('.remove()')) return evalResult('ok');
        if (false) {
          if (fn.includes('"dryRun":false')) { onLive(); return liveHang ? never() : evalResult(write()); }
          return evalResult({ status: 'DRY', checks: { dungBai: true }, changes: {}, backup: { newsId: ID, at: 'x', content_FaqNews_DB: dryDb(), fields: { txtUrl: 'u' }, cates: { parent: ['1'], child: ['2'] }, fullPageHtml: '<html>page</html>' } });
        }
        throw new Error('evaluate không mong đợi: ' + fn.slice(0, 80));
      },
    },
  });
}

const fetchOk = async (url) => ({ status: 200, arrayBuffer: async () => IMG[url.split('/').pop()] });
const fetchBad = async () => ({ status: 200, arrayBuffer: async () => Buffer.from('khác') });
let verifyCalls = 0;
const nodeExec = (verifyPass) => (bin, args, opts, cb) => {
  if (args[0].endsWith('verify-hoidap-live.mjs')) {
    verifyCalls++;
    const ok = verifyPass(verifyCalls);
    return cb(ok ? null : Object.assign(new Error('fail'), { code: 1 }), JSON.stringify({ pass: ok, headings: '2/2', images: '2/2' }), '');
  }
  return execFile(bin, args, opts, cb); // hoidap-body-tools chạy thật, local
};
const sleeps = [];
const run = (fake, W, argv, { fetchFn = fetchOk, verifyPass = () => true, signalSource, exitFn } = {}) => main(
  ['--profile', 'hd', '--task-dir', W, '--news-id', String(ID), '--timeout-sec', '0.3', ...argv],
  {
    spawnFn: fake.spawnFn, execFileFn: fakeChromeProfile('tk', 'hd'), nodeExecFn: nodeExec(verifyPass), fetchFn,
    sleepFn: async (ms) => { sleeps.push(ms); }, log: process.env.DEBUG ? console.log : () => {}, tasksRoot: path.join(ROOT, 'tasks'),
    ...(signalSource ? { signalSource } : {}), ...(exitFn ? { exitFn } : {}),
  },
);
const evals = (fake, s) => fake.calls.filter((c) => c.name === 'evaluate_script' && c.args.function.includes(s));

{
  const runner = fs.readFileSync(path.join(HERE, 'air-hoidap-runner.js'), 'utf8');
  let ok = true;
  try { new Function(`return (${withRunner(runner, 'return await window.hdWriteArticle({});')})`); } catch { ok = false; }
  t('runner thật + tail là JS hợp lệ', ok);
}

console.log('\n# upload');
{
  const W = newTask();
  const fake = hdFake();
  const code = await run(fake, W, ['--workspace', CW, '--step', 'upload']);
  const up = fake.calls.find((c) => c.name === 'upload_file');
  t('dry upload → exit 0', code === 0, code);
  t('upload_file vào input tự tạo (uid từ snapshot theo aria-label)', up?.args.uid === '1_9');
  t('đủ 2 ảnh HTML tham chiếu, đường tuyệt đối', up?.args.filePaths.length === 2 && up.args.filePaths.every(path.isAbsolute));
  t('dry gọi hdUploadImages dryRun:true', evals(fake, 'return await window.hdUploadImages(').length === 1 && evals(fake, '"dryRun":false').length === 0);
  t('xoá input sau khi xong', evals(fake, '.remove()').length === 1);
  t('không tạo map khi dry', !fs.existsSync(path.join(W, `data/raw/cms-upload-${ID}.json`)));
}
{
  const fake = hdFake({ upload: () => ({ status: 'DRY', cdnHead: { 'a-mot.jpg': 200, 'b-hai.jpg': 404 }, taken: ['a-mot.jpg'] }) });
  t('dry upload có tên đã chiếm → exit 1', (await run(fake, newTask(), ['--workspace', CW, '--step', 'upload'])) === 1);
}
{
  const W = newTask();
  const fake = hdFake();
  const code = await run(fake, W, ['--workspace', CW, '--step', 'upload', '--live']);
  const out = path.join(W, `data/processed/final-content-cms-${ID}.html`);
  t('live upload → exit 0', code === 0, code);
  t('map upload lưu trên đĩa', fs.existsSync(path.join(W, `data/raw/cms-upload-${ID}.json`)));
  t('replace thật: HTML bản CMS dùng URL CDN, không còn images-processed/', fs.existsSync(out) && fs.readFileSync(out, 'utf8').includes(CDN('a-mot.jpg')) && !fs.readFileSync(out, 'utf8').includes('images-processed/'));
  const e = await rejects(run(hdFake(), W, ['--workspace', CW, '--step', 'upload', '--live']));
  t('live upload lần 2 (map đã có) → từ chối, không upload lại', /đã có/.test(e?.message || ''), e?.message);
}
{
  const W = newTask();
  const code = await run(hdFake(), W, ['--workspace', CW, '--step', 'upload', '--live'], { fetchFn: fetchBad });
  t('ảnh CDN lệch byte → exit 1, không thay src', code === 1 && !fs.existsSync(path.join(W, `data/processed/final-content-cms-${ID}.html`)));
}

console.log('\n# write');
const prepTask = async () => { const W = newTask(); await run(hdFake(), W, ['--workspace', CW, '--step', 'upload', '--live']); return W; };
{
  const W = await prepTask();
  const fake = hdFake();
  let e = await rejects(run(fake, W, ['--step', 'write', '--live', '--live-url', 'https://www.thegioididong.com/hoi-dap/x-1576257']));
  t('write --live khi chưa có dry đã duyệt → từ chối exit 2', e?.exitCode === 2 && /duyệt diff/.test(e.message), e?.message);
  e = await rejects(run(fake, W, ['--step', 'write', '--live']));
  t('write --live thiếu --live-url → từ chối', /--live-url/.test(e?.message || ''), e?.message);
  t('từ chối trước khi mở trình duyệt', fake.spawned === 0);

  const code = await run(fake, W, ['--step', 'write']);
  const split = path.join(W, `data/raw/cms-backup/${ID}`);
  t('write dry → exit 0', code === 0, code);
  t('dry json + before/page/fields trên đĩa', ['before.html', 'page.html', 'fields.json'].every((f) => fs.statSync(path.join(split, f)).size > 0) && fs.existsSync(path.join(W, `data/raw/cms-backup/dry-${ID}.json`)));

  const e2 = await rejects(run(hdFake(), W, ['--step', 'write', '--title', 'Tiêu đề khác', '--live', '--live-url', 'https://x/hoi-dap/y']));
  t('set khác bản dry đã duyệt → từ chối', /khác bản dry/.test(e2?.message || ''), e2?.message);

  const f3 = hdFake({ dryDb: () => '<p>có người vừa sửa</p>' });
  t('thân bài đổi từ lúc duyệt → exit 1, không ghi', (await run(f3, W, ['--step', 'write', '--live', '--live-url', 'https://x/hoi-dap/y'])) === 1 && evals(f3, '"dryRun":false').length === 0);

  let preLiveOnDisk = false;
  sleeps.length = 0; verifyCalls = 0;
  const f4 = hdFake({ onLive: () => {
    const d = path.join(split); preLiveOnDisk = fs.readdirSync(d).some((x) => x.startsWith('pre-live-') && ['before.html', 'page.html', 'fields.json'].every((f) => fs.statSync(path.join(d, x, f)).size > 0));
  } });
  const c4 = await run(f4, W, ['--step', 'write', '--live', '--live-url', 'https://www.thegioididong.com/hoi-dap/x-1576257'], { verifyPass: (n) => n >= 2 });
  t('live DONE + live verify pass lần 2 → exit 0', c4 === 0, c4);
  t('backup pre-live có trên đĩa TRƯỚC lúc gọi ghi', preLiveOnDisk);
  t('liveCode có guard hash thân bài', evals(f4, '"dryRun":false')[0]?.args.function.includes('guard: thân bài đổi sau lúc backup'));
  t('đợi 60s trước mỗi lần nghiệm thu live (2 lần)', sleeps.length === 2 && sleeps.every((ms) => ms === 60000), sleeps);

  const f5 = hdFake({ write: () => ({ status: 'FAIL', verify: { byteExact: false } }) });
  verifyCalls = 0;
  t('runner FAIL → exit 1, không nghiệm thu live', (await run(f5, W, ['--step', 'write', '--live', '--live-url', 'https://x/hoi-dap/y'])) === 1 && verifyCalls === 0);

  const f6 = hdFake({ liveHang: true });
  t('timeout khi ghi → exit 1, giữ tab', (await run(f6, W, ['--step', 'write', '--live', '--live-url', 'https://x/hoi-dap/y'])) === 1 && !f6.calls.some((c) => c.name === 'close_page') && f6.killed);
  t('timeout khi ghi (UNKNOWN) → marker in-flight VẪN CÒN (không rõ đã POST hay chưa)', readInflightMarker(inflightDir(W, 'cms-backup'), `hd-write-${ID}`)?.key === `hd-write-${ID}`);
  t('timeout khi ghi → evaluate KHÔNG được gọi lại (đúng 1 lần cho POST ghi thật)', evals(f6, '"dryRun":false').length === 1);
  fs.rmSync(path.join(inflightDir(W, 'cms-backup'), `hd-write-${ID}.json`), { force: true });
}

console.log('\n# marker in-flight (write): 3 ca phục hồi từ lần chạy trước bị dừng giữa chừng');
{
  const W = await prepTask();
  await run(hdFake(), W, ['--step', 'write']); // dry đã duyệt (baseline body = DB_BODY)
  const finalHtml = fs.readFileSync(path.join(W, `data/processed/final-content-cms-${ID}.html`), 'utf8');
  const idir = inflightDir(W, 'cms-backup');
  const key = `hd-write-${ID}`;
  const liveUrl = ['--live-url', 'https://www.thegioididong.com/hoi-dap/x-1576257'];

  // Ca 1 — DONE_RECOVERED: CMS hiện tại đã có ĐÚNG bản intended (lần ghi trước thật ra đã
  // thành công, chỉ process bị kill trước khi đọc được kết quả).
  writeInflightMarker(idir, { key, row: { step: 'write', intendedSha: sha256(finalHtml) }, beforeSha: sha256('bản khác hẳn') });
  let posted1 = 0;
  const f1 = hdFake({ dryDb: () => finalHtml, onLive: () => { posted1++; } });
  const c1 = await run(f1, W, ['--step', 'write', '--live', ...liveUrl]);
  t('DONE_RECOVERED: exit 0', c1 === 0, c1);
  t('DONE_RECOVERED: marker đã xoá', readInflightMarker(idir, key) === null);
  t('DONE_RECOVERED: không POST lại', posted1 === 0);

  // Ca 2 — SAFE_PROCEED: CMS vẫn ở bản backup cũ -> an toàn ghi lại bình thường.
  writeInflightMarker(idir, { key, row: { step: 'write', intendedSha: sha256(finalHtml) }, beforeSha: sha256(DB_BODY) });
  let posted2 = 0;
  const f2 = hdFake({ onLive: () => { posted2++; } }); // dryDb mặc định = DB_BODY
  const c2 = await run(f2, W, ['--step', 'write', '--live', ...liveUrl]);
  t('SAFE_PROCEED: exit 0', c2 === 0, c2);
  t('SAFE_PROCEED: marker đã xoá sau khi ghi xong (DONE)', readInflightMarker(idir, key) === null);
  t('SAFE_PROCEED: vẫn ghi lại bình thường (1 lần POST)', posted2 === 1);

  // Ca 3 — NEEDS_MANUAL_CHECK: CMS ở trạng thái khác cả intended lẫn before.
  writeInflightMarker(idir, { key, row: { step: 'write', intendedSha: sha256(finalHtml) }, beforeSha: sha256(DB_BODY) });
  const f3 = hdFake({ dryDb: () => '<p>một bản hoàn toàn khác</p>' });
  const c3 = await run(f3, W, ['--step', 'write', '--live', ...liveUrl]);
  t('NEEDS_MANUAL_CHECK: exit 1', c3 === 1, c3);
  t('NEEDS_MANUAL_CHECK: marker VẪN CÒN (chưa có kết luận rõ ràng)', readInflightMarker(idir, key)?.key === key);
  t('NEEDS_MANUAL_CHECK: không POST', evals(f3, '"dryRun":false').length === 0);
  fs.rmSync(path.join(idir, `${key}.json`), { force: true });
}

console.log('\n# SIGTERM giữa lúc ghi — ghi "interrupted" vào run-log, đóng tab/MCP, thoát qua exitFn');
{
  const W = await prepTask();
  await run(hdFake(), W, ['--step', 'write']); // dry đã duyệt
  const fake = hdFake({ liveHang: true });
  const signalSource = new EventEmitter();
  const exitCalls = [];
  const exitFn = (code) => exitCalls.push(code);
  const p = run(fake, W, ['--step', 'write', '--live', '--live-url', 'https://www.thegioididong.com/hoi-dap/x-1576257'], { signalSource, exitFn });
  p.catch(() => {}); // promise không bao giờ resolve (evaluate hang) — tránh unhandledRejection
  await new Promise((r) => setTimeout(r, 30)); // để main() chạy tới lúc await evaluate() (đang hang)
  signalSource.emit('SIGTERM');
  await new Promise((r) => setTimeout(r, 150)); // client.close() poll this.exited mỗi 50ms
  t('exitFn được gọi với code 130', exitCalls[0] === 130, exitCalls);
  const logLines = fs.readFileSync(path.join(W, 'data/raw/cms-backup/run-log.jsonl'), 'utf8').trim().split('\n').map((l) => JSON.parse(l));
  t('run-log có dòng "interrupted" khi bị SIGTERM', logLines.some((l) => l.phase === 'signal' && l.signal === 'SIGTERM' && /interrupted/.test(l.note)), logLines);
  t('MCP được đóng khi nhận SIGTERM', fake.killed);
  fs.rmSync(path.join(inflightDir(W, 'cms-backup'), `hd-write-${ID}.json`), { force: true });
}

fs.rmSync(ROOT, { recursive: true, force: true });
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
