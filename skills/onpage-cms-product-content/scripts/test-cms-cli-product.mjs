/**
 * Test run-cms-product-content-cli.mjs bằng MCP giả (không trình duyệt, không CMS, không mạng).
 * Nhánh chung của pipeline (timeout giữa lô, tab sai token, parity 4 bản copy) đã test đủ ở
 * onpage-cms-news-insert/scripts/test-cms-cli-news.mjs; ở đây test phần riêng bài sản phẩm.
 *   node .claude/skills/onpage-cms-product-content/scripts/test-cms-cli-product.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { main, productAdapter } from './run-cms-product-content-cli.mjs';
import { createFakeMcp, evalResult, pagesResult, fakeChromeProfile } from './cms-cli-fake-mcp.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const rejects = async (p) => { try { await p; return null; } catch (e) { return e; } };

const ROOT = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-cli-sp-'));
// tasksRoot giả — --task-dir/--backup-dir giờ bắt buộc realpath nằm trong tasks/ CHUẨN
// của repo (finding #13); tiêm deps.tasksRoot để test dùng thư mục tạm.
const TASKS_ROOT = path.join(ROOT, 'tasks');
const TASK = path.join(TASKS_ROOT, '260924-test');
fs.mkdirSync(TASK, { recursive: true });
const TAB = 'https://cms.thegioididong.com/v2/Product/Edit?site=1&productId=335308#cdp-profile=prof&cdp-open=tk';
const row = (n, pid, site = 1) => ({ row: n, pid, site, oldText: `Đoạn ${pid}.`, sentence: 'Xem iPhone 18 ngay.', links: [{ anchor: 'iPhone 18', href: 'https://www.thegioididong.com/dtdd/iphone-18' }] });
const rowsFile = (rows) => { const f = path.join(ROOT, `r${Math.random()}.json`); fs.writeFileSync(f, JSON.stringify(rows)); return f; };

function fakeSp({ dry = () => 'DRY', live = () => 'DONE' } = {}) {
  return createFakeMcp({
    tools: {
      list_pages: () => pagesResult([{ id: 3, url: TAB }]),
      evaluate_script: ({ function: fn }) => {
        const pid = Number((fn.match(/"pid":(\d+)/) || [])[1]);
        if (fn.includes('"dryRun":false')) return evalResult({ rows: [{ pid, status: live(pid), _before: `B${pid}`, _after: `A${pid}` }] });
        const st = dry(pid);
        return evalResult({ rows: [{ pid, status: st, _before: `B${pid}`, _after: `A${pid}`, ...(st === 'DRY' ? { _beforePage: `<html>${pid}</html>` } : {}) }] });
      },
    },
  });
}
const run = (fake, argv, extraDeps = {}) => main(['--profile', 'prof', '--task-dir', TASK, ...argv], {
  spawnFn: fake.spawnFn, execFileFn: fakeChromeProfile('tk', 'prof'), sleepFn: async () => {}, log: () => {}, tasksRoot: TASKS_ROOT, ...extraDeps,
});
const lastDir = () => {
  const d = path.join(TASK, 'data/raw/content-backup');
  // Bỏ qua _inflight (thư mục marker cố định, không phải backup theo lô).
  return path.join(d, fs.readdirSync(d).filter((n) => !n.startsWith('_')).sort().pop());
};
const liveN = (fake) => fake.calls.filter((c) => c.name === 'evaluate_script' && c.args.function.includes('"dryRun":false')).length;

{
  const ad = productAdapter(fs.readFileSync(path.join(HERE, 'cms-bulk-insert-runner.js'), 'utf8'));
  let ok = true;
  try { new Function(`return (${ad.dryCode(row(1, 5))})`); new Function(`return (${ad.liveCode(row(1, 5), { beforeSha: 'x' })})`); } catch { ok = false; }
  t('dryCode/liveCode với runner thật là JS hợp lệ', ok);
  t('dryCode lấy thêm full trang edit để backup', ad.dryCode(row(1, 5)).includes('fieldSpec("txtContent").editPath(1, 5)'));
  const hr = { ...row(1, 5, 16), field: 'hotReason' };
  t('hotReason: dryCode backup trang cũ, liveCode guard đọc đúng field',
    ad.dryCode(hr).includes('fieldSpec("hotReason").editPath(16, 5)') && ad.liveCode(hr, { beforeSha: 'x' }).includes('fetchEdit(16, 5, "hotReason")'));
  t('key mặc định giữ nguyên, hotReason thêm -hr', ad.key(row(1, 5)) === 'sp-5-s1' && ad.key(hr) === 'sp-5-s16-hr');
}
{
  const fake = fakeSp();
  const code = await run(fake, ['--file', rowsFile([row(1, 11), row(2, 22)])]);
  const dir = lastDir();
  t('dry đạt → exit 0, không ghi', code === 0 && liveN(fake) === 0, code);
  t('backup before + page + payload trên đĩa', ['before.html', 'before-page.html', 'payload.json'].every((s) => fs.statSync(path.join(dir, `sp-11-s1-${s}`)).size > 0));
  t('tab mở đúng trang Product/Edit', fake.calls.some((c) => c.name === 'select_page' && c.args.pageId === 3));
}
{
  const fake = fakeSp({ dry: (p) => (p === 22 ? 'SKIP' : 'DRY') });
  const code = await run(fake, ['--live', '--file', rowsFile([row(1, 11), row(2, 22)])]);
  t('live + 1 dòng dry fail → exit 1, 0 lần ghi', code === 1 && liveN(fake) === 0, code);
}
{
  const fake = fakeSp({ live: (p) => (p === 22 ? 'FAIL' : 'DONE') });
  const code = await run(fake, ['--live', '--file', rowsFile([row(1, 11), row(2, 22)])]);
  const res = JSON.parse(fs.readFileSync(path.join(lastDir(), 'run-result.json'), 'utf8')).results;
  t('live có FAIL → exit 1', code === 1, code);
  t('dòng DONE + dòng FAIL đều ghi vào run-result', res[0].status === 'DONE' && res[1].status === 'FAIL');
}
{
  const fake = fakeSp();
  const code = await run(fake, ['--live', '--file', rowsFile([row(1, 11)])]);
  t('live DONE hết → exit 0', code === 0 && liveN(fake) === 1, code);
  t('MCP đóng', fake.killed);
}
{
  const fake = fakeSp();
  let e = await rejects(run(fake, ['--file', rowsFile([row(1, 11, 3)])]));
  t('site ngoài 1/2 → lỗi exit 2', e?.exitCode === 2, e?.message);
  e = await rejects(run(fake, ['--file', rowsFile([])]));
  t('rows rỗng → lỗi exit 2', e?.exitCode === 2 && /rows rỗng/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--file', rowsFile([row(1, 11), row(2, 11)])]));
  t('trùng bài trong lô → lỗi', /trùng bài/.test(e?.message || ''), e?.message);
  t('tham số sai thì không spawn MCP', fake.spawned === 0);
}

{
  const fake = fakeSp();
  let e = await rejects(run(fake, ['--file', rowsFile([row(1, 11, 16)])]));
  t('site 16 không --field → lỗi exit 2, gợi ý hotReason', e?.exitCode === 2 && /--field hotReason/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--field', 'bogus', '--file', rowsFile([row(1, 11)])]));
  t('--field lạ → lỗi exit 2', e?.exitCode === 2 && /không hỗ trợ/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--field', 'hotReason', '--file', rowsFile([{ ...row(1, 11, 16), field: 'txtContent' }])]));
  t('field trong rows khác --field → lỗi exit 2', e?.exitCode === 2 && /khai 1 chỗ/.test(e.message), e?.message);
  t('tham số sai (field) thì không spawn MCP', fake.spawned === 0);
}
{
  const fake = fakeSp();
  // --backup-dir riêng: lastDir() theo tên có thể chọn nhầm thư mục -live cùng giây của test trước.
  const dir = path.join(TASK, 'data/raw/content-backup/hr-dry');
  const code = await run(fake, ['--field=hotReason', '--backup-dir', dir, '--file', rowsFile([row(1, 11, 16)])]);
  const dryFn = fake.calls.find((c) => c.name === 'evaluate_script')?.args.function || '';
  t('--field hotReason site 16: dry đạt → exit 0', code === 0 && liveN(fake) === 0, code);
  t('row gửi runner mang field hotReason', dryFn.includes('"field":"hotReason"'));
  t('backup đặt tên sp-11-s16-hr-*', fs.statSync(path.join(dir, 'sp-11-s16-hr-before.html')).size > 0);
}
{
  const fake = fakeSp();
  const code = await run(fake, ['--file', rowsFile([row(1, 11)])]);
  const dryFn = fake.calls.find((c) => c.name === 'evaluate_script')?.args.function || '';
  t('không --field: row mang field txtContent (hành vi cũ)', code === 0 && dryFn.includes('"field":"txtContent"'));
}

console.log('\n# --mode apply-ops: validation + wiring qua CLI (giả MCP, không đụng ops engine thật)');
const opsRow = (n, pid, site = 1, over = {}) => ({
  row: n, pid, site, field: 'txtContent',
  expectedBeforeSha256: 'a'.repeat(64),
  ops: [{ id: 'A', type: 'replace', find: 'x', new: 'y' }],
  ...over,
});
{
  const fake = fakeSp();
  let e = await rejects(run(fake, ['--mode', 'bogus', '--file', rowsFile([opsRow(1, 11)])]));
  t('--mode lạ → lỗi exit 2', e?.exitCode === 2 && /không hỗ trợ/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--pid', '11', '--site', '1']));
  t('apply-ops không --file → lỗi exit 2 (không có cờ dòng lệnh cho ops)', e?.exitCode === 2 && /chỉ chạy qua --file/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--file', rowsFile([{ ...opsRow(1, 11), field: undefined }])]));
  t('apply-ops thiếu field → lỗi exit 2', e?.exitCode === 2 && /bắt buộc --field/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--field', 'txtContent', '--file', rowsFile([{ ...opsRow(1, 11), expectedBeforeSha256: 'ngắn' }])]));
  t('apply-ops expectedBeforeSha256 sai định dạng → lỗi exit 2', e?.exitCode === 2 && /expectedBeforeSha256/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--field', 'txtContent', '--file', rowsFile([{ ...opsRow(1, 11), ops: [] }])]));
  t('apply-ops ops rỗng → lỗi exit 2', e?.exitCode === 2 && /ops/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--field', 'txtContent', '--file', rowsFile([{ ...opsRow(1, 11), ops: [{ id: 'A', type: 'replace', find: 'x' }] }])]));
  t('apply-ops op replace thiếu new → lỗi exit 2', e?.exitCode === 2 && /find\/new/.test(e.message), e?.message);
  e = await rejects(run(fake, ['--mode', 'apply-ops', '--field', 'txtContent', '--file', rowsFile([{ ...opsRow(1, 11), ops: [{ id: 'A', type: 'la-gi-do' }] }])]));
  t('apply-ops op type lạ → lỗi exit 2', e?.exitCode === 2 && /type lạ/.test(e.message), e?.message);
  t('tham số sai (mode/ops) thì không spawn MCP', fake.spawned === 0);
}
{
  const fake = fakeSp();
  const dir = path.join(TASK, 'data/raw/content-backup/ops-dry');
  const code = await run(fake, ['--mode', 'apply-ops', '--field', 'txtContent', '--backup-dir', dir, '--file', rowsFile([opsRow(1, 11)])]);
  const dryFn = fake.calls.find((c) => c.name === 'evaluate_script')?.args.function || '';
  t('apply-ops dry đạt → exit 0, không ghi', code === 0 && liveN(fake) === 0, code);
  t('row gửi runner mang mode apply-ops + ops', dryFn.includes('"mode":"apply-ops"') && dryFn.includes('"ops":'));
  t('backup đặt tên sp-11-s1-ops-* (hậu tố -ops, không đụng key insert-link)', fs.statSync(path.join(dir, 'sp-11-s1-ops-before.html')).size > 0);
}
{
  const fake = fakeSp();
  const dir = path.join(TASK, 'data/raw/content-backup/ops-hr-dry');
  const code = await run(fake, ['--mode', 'apply-ops', '--field', 'hotReason', '--backup-dir', dir, '--file', rowsFile([opsRow(1, 11, 16, { field: 'hotReason' })])]);
  t('apply-ops + hotReason: dry đạt → exit 0', code === 0 && liveN(fake) === 0, code);
  t('backup đặt tên sp-11-s16-hr-ops-* (2 hậu tố cộng dồn)', fs.statSync(path.join(dir, 'sp-11-s16-hr-ops-before.html')).size > 0);
}

fs.rmSync(ROOT, { recursive: true, force: true });
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
