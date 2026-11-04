#!/usr/bin/env node
/**
 * run-cms-product-content-cli.mjs — can thiệp mục "Nội dung bài viết" (hdType=2, hoặc
 * HotReason ở site 16) của bài sản phẩm CMS bằng 1 lệnh, 2 mode chọn bằng `--mode`:
 *
 *   --mode insert-link (mặc định)  — chèn 1 câu kèm internal link vào cuối 1 đoạn <p> có sẵn.
 *   --mode apply-ops               — áp nhiều "ops" (replace/after_p/before_h3/before_p/before_tr)
 *                                    đã fact-check sẵn, guard bằng sha256 nội dung TRƯỚC khi ghi.
 *
 * Bọc NGOÀI cms-bulk-insert-runner.js + cms-content-ops-engine.js (không sửa 2 file đó qua CLI
 * này ngoài việc nối chuỗi source). Luồng như CLI bài tin: mở tab đúng profile (chrome-profile +
 * cdp-open token) → dry từng bài → backup (_before + full trang edit + payload) lên đĩa, đọc lại
 * kiểm → --live mới ghi từng bài, guard hash thân bài ngay trước khi ghi. Exit 0 chỉ khi mọi
 * dòng DONE/ALREADY (live) hoặc DRY/ALREADY (dry).
 *
 *   node run-cms-product-content-cli.mjs --profile <key> --task-dir tasks/<task> --file rows.json [--live]
 *   node run-cms-product-content-cli.mjs --profile <key> --task-dir tasks/<task> \
 *     --pid 335308 --site 1 --old-text "..." --sentence "..." --anchor "..." --url "https://..." [--live]
 *
 * rows.json mode insert-link: [{ row, pid, site, name?, oldText, sentence, links:[{anchor, href, title?}] }]
 * rows.json mode apply-ops:   [{ row, pid, site, name?, field, expectedBeforeSha256, ops:[...] }]
 *   — apply-ops CHỈ chạy qua --file (ops là object phức tạp, không diễn đạt được bằng cờ dòng lệnh).
 *
 * --field txtContent (mặc định ở insert-link) | hotReason — field chứa thân bài. Site 16
 * (TopZone) đảo vai: bài ở HotReason, txtContent chỉ là gallery; site 16 BẮT BUỘC truyền --field.
 * Mode apply-ops BẮT BUỘC --field ở MỌI site (không có mặc định), vì rows.json luôn khai field
 * tường minh theo spec ops. Áp cho mọi dòng của lô.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { CMS_ORIGIN, CliError, PAGE_SHA256, withRunner } from './cms-cli-mcp.mjs';
import { runInsertCli, sha256, validateInsertRow } from './cms-cli-pipeline.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RUNNER = path.join(HERE, 'cms-bulk-insert-runner.js');
const OPS_ENGINE = path.join(HERE, 'cms-content-ops-engine.js');
// Đo thật ~8s/dòng; 120s dư mà vẫn dưới protocolTimeout 180s của CDP.
const DEFAULT_ROW_TIMEOUT_SEC = 120;

const J = (v) => JSON.stringify(v);

export const FIELDS = ['txtContent', 'hotReason'];
export const MODES = ['insert-link', 'apply-ops'];
const SITES = [1, 2, 16];
const OPS_INSERT_TYPES = ['after_p', 'before_h3', 'before_p', 'before_tr'];

/**
 * Bundle runnerCode + ops engine thành 1 khối chạy TRONG page context: nối chuỗi source
 * (không import ESM ở đó) — cms-content-ops-engine.js ĐỨNG TRƯỚC để cms-bulk-insert-runner.js
 * gọi thẳng `buildContentOps`/`checkOpsInvariants`/`allOpsAlreadyApplied`/`sha256Hex` cùng scope.
 * Nối luôn cho cả mode insert-link (không gọi tới) — không đổi hành vi, chỉ thêm hàm không dùng.
 */
export function readBundledRunnerCode() {
  const opsEngine = fs.readFileSync(OPS_ENGINE, 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
  const runner = fs.readFileSync(RUNNER, 'utf8');
  return `${opsEngine}\n${runner}`;
}

export function productAdapter(runnerCode, mode = 'insert-link') {
  // Mặc định giữ nguyên key cũ (marker in-flight/backup của lô cũ vẫn khớp); hotReason thêm
  // hậu tố -hr; apply-ops thêm hậu tố -ops (không đụng key insert-link cùng pid/site/field).
  const key = (r) => `sp-${r.pid}-s${r.site}${r.field === 'hotReason' ? '-hr' : ''}${mode === 'apply-ops' ? '-ops' : ''}`;
  const runOpts = (r, extra) => (mode === 'apply-ops' ? { mode: 'apply-ops', keepHtml: true, rows: [r], ...extra } : { keepHtml: true, rows: [r], ...extra });
  // Mặc định 'txtContent' chỉ áp dụng khi field vắng mặt — thực tế chỉ xảy ra ở test gọi
  // adapter trực tiếp (bỏ qua normalizeRow); ở CLI thật, normalizeRow luôn set field trước.
  const fieldOf = (r) => r.field || 'txtContent';

  return {
    key,
    // Runner không giữ full trang edit — wrapper lấy thêm để backup đủ (form, field khác).
    dryCode: (r) => withRunner(runnerCode, `const res = await cmsBulkInsert(${J(runOpts(r, { dryRun: true }))});
if (res.rows[0] && (res.rows[0].status === 'DRY')) {
  res.rows[0]._beforePage = await fetch(fieldSpec(${J(fieldOf(r))}).editPath(${J(r.site)}, ${J(r.pid)}), { credentials: 'same-origin' }).then((x) => x.text());
}
return res;`),
    judgeDry(out) {
      const r = out?.rows?.[0];
      if (!r) return { status: 'ERROR', reason: 'runner không trả dòng nào' };
      if (r.status === 'DRY') return { status: 'DRY' };
      if (mode === 'apply-ops') {
        // apply-ops: runner tự trả status ALREADY trực tiếp (không cần suy qua cờ .already
        // như insert-link, vì không có khái niệm "SKIP nhưng thật ra đã chèn đúng").
        return { status: r.status || 'ERROR', reason: r.reason };
      }
      if (r.status === 'SKIP' && r.already) return { status: 'ALREADY', reason: r.reason };
      // Đã chèn ở lần chạy trước NHƯNG link sai — không phải ALREADY, không nằm trong
      // OK_DRY nên pipeline tự dừng cả lô, không ghi dòng nào (finding #5).
      if (r.status === 'ALREADY_MISMATCH') return { status: 'ALREADY_MISMATCH', reason: r.reason };
      return { status: r.status || 'ERROR', reason: r.reason };
    },
    backupFiles(r, out) {
      const x = out.rows[0];
      return [
        { name: `${key(r)}-before.html`, content: x._before },
        { name: `${key(r)}-before-page.html`, content: x._beforePage },
        { name: `${key(r)}-payload.json`, content: JSON.stringify(r, null, 2) },
        { name: `${key(r)}-dry-after.html`, content: x._after },
      ];
    },
    beforeText: (out) => out.rows[0]._before,
    liveCode: (r, { beforeSha }) => withRunner(runnerCode, `${PAGE_SHA256}
const cur = await fetchEdit(${J(r.site)}, ${J(r.pid)}, ${J(fieldOf(r))});
if ((await __sha256(cur.raw)) !== ${J(beforeSha)}) return { guard: 'CHANGED_SINCE_BACKUP', curLen: cur.raw.length };
return await cmsBulkInsert(${J(runOpts(r, { dryRun: false }))});`),
    judgeLive(out, { beforeSha, row }) {
      if (out?.guard) return { status: 'SKIP', reason: 'thân bài đổi sau lúc backup — không ghi, chạy lại để lấy backup mới' };
      const x = out?.rows?.[0];
      if (!x) return { status: 'ERROR', reason: 'runner không trả dòng nào' };
      const afterFiles = x._after ? [{ name: `${key(row)}-after.html`, content: x._after }] : [];
      if (mode === 'apply-ops') {
        if (typeof x._before === 'string' && sha256(x._before) !== beforeSha) {
          return { status: 'BACKUP_MISMATCH', reason: `runner đọc bản khác backup (status runner ${x.status}) — kiểm tay`, afterFiles };
        }
        return { status: x.status || 'ERROR', reason: x.reason, afterFiles };
      }
      if (x.status === 'SKIP' && x.already) return { status: 'ALREADY', reason: x.reason, afterFiles };
      if (typeof x._before === 'string' && sha256(x._before) !== beforeSha) {
        return { status: 'BACKUP_MISMATCH', reason: `runner đọc bản khác backup (status runner ${x.status}) — kiểm tay`, afterFiles };
      }
      return { status: x.status || 'ERROR', reason: x.reason, afterFiles };
    },
  };
}

function rowsFromArgs(a, mode) {
  if (mode === 'apply-ops') {
    throw new CliError('mode apply-ops chỉ chạy qua --file rows.json (ops là object phức tạp, không có cờ dòng lệnh)', 2);
  }
  if (!a.pid && !a['old-text'] && !a.sentence) {
    throw new CliError('cần --file rows.json hoặc bộ --pid --site --old-text --sentence --anchor --url', 2);
  }
  return [{
    row: 1,
    pid: a.pid,
    site: a.site || 1,
    name: a.name || null,
    oldText: a['old-text'],
    sentence: a.sentence,
    links: a.anchor && a.url ? [{ anchor: a.anchor, href: a.url, title: a.anchor }] : [],
  }];
}

/** Đọc 1 cờ giá trị đơn (--field/--mode) trước khi giao argv cho pipeline chung. */
function pickFlag(argv, name) {
  let v;
  const re = new RegExp(`^--${name}(?:=(.*))?$`, 's');
  for (let i = 0; i < argv.length; i++) {
    const m = re.exec(argv[i]);
    if (m) v = m[1] ?? argv[i + 1];
  }
  return v;
}

export function pickField(argv) {
  const v = pickFlag(argv, 'field');
  if (v === undefined) return null;
  if (!FIELDS.includes(v)) throw new CliError(`--field ${v} không hỗ trợ — chỉ ${FIELDS.join(' | ')}`, 2);
  return v;
}

export function pickMode(argv) {
  const v = pickFlag(argv, 'mode');
  if (v === undefined) return 'insert-link';
  if (!MODES.includes(v)) throw new CliError(`--mode ${v} không hỗ trợ — chỉ ${MODES.join(' | ')}`, 2);
  return v;
}

/** Kiểm 1 dòng apply-ops: pid, field bắt buộc, expectedBeforeSha256 dạng hex sha256, ops đủ field theo type. */
export function validateOpsRow(r) {
  const miss = [];
  if (!r.pid) miss.push('pid');
  if (!r.field) miss.push('field');
  if (!r.expectedBeforeSha256 || !/^[0-9a-f]{64}$/i.test(r.expectedBeforeSha256)) miss.push('expectedBeforeSha256 (phải là hex sha256, 64 ký tự)');
  if (!Array.isArray(r.ops) || !r.ops.length) {
    miss.push('ops');
  } else {
    r.ops.forEach((op, i) => {
      if (!op || typeof op.type !== 'string') { miss.push(`ops[${i}].type`); return; }
      if (op.type === 'replace') {
        if (typeof op.find !== 'string' || !op.find || typeof op.new !== 'string') miss.push(`ops[${i}] (replace) thiếu find/new`);
      } else if (OPS_INSERT_TYPES.includes(op.type)) {
        if (typeof op.anchor !== 'string' || !op.anchor || typeof op.new !== 'string') miss.push(`ops[${i}] (${op.type}) thiếu anchor/new`);
      } else {
        miss.push(`ops[${i}].type lạ "${op.type}" — chỉ replace | ${OPS_INSERT_TYPES.join(' | ')}`);
      }
    });
  }
  if (miss.length) throw new CliError(`dòng ${r.row ?? '?'} thiếu/sai: ${miss.join(', ')}`, 2);
}

function normalizeRow(r, field, mode) {
  const out = { ...r, pid: Number(r.pid), site: Number(r.site || 1) };
  const at = `dòng ${r.row ?? '?'}`;
  if (!SITES.includes(out.site)) throw new CliError(`${at}: site ${out.site} không thuộc 1 (TGDĐ) / 2 (ĐMX) / 16 (TopZone)`, 2);

  if (mode === 'apply-ops') {
    if (!field) throw new CliError(`${at}: mode apply-ops bắt buộc --field (txtContent | hotReason) — không có mặc định`, 2);
    if (r.field !== undefined && r.field !== field) {
      throw new CliError(`${at}: field "${r.field}" trong rows khác --field ${field} — khai 1 chỗ thôi`, 2);
    }
    out.field = field;
    validateOpsRow(out);
    return out;
  }

  if (r.field !== undefined && r.field !== (field ?? 'txtContent')) {
    throw new CliError(`${at}: field "${r.field}" trong rows khác --field ${field ?? 'txtContent'} — khai 1 chỗ thôi`, 2);
  }
  if (out.site === 16 && !field) {
    throw new CliError(`${at}: site 16 (TopZone) bài nằm ở HotReason, không phải txtContent — truyền --field hotReason (hoặc --field txtContent nếu chủ đích sửa gallery)`, 2);
  }
  out.field = field ?? 'txtContent';
  validateInsertRow(out, 'pid');
  return out;
}

export const main = async (argv, deps = {}) => {
  const mode = pickMode(argv);
  const field = pickField(argv);
  return runInsertCli(argv, deps, {
    backupSub: 'content-backup',
    extraValues: ['pid', 'site', 'name', 'old-text', 'sentence', 'anchor', 'url', 'field', 'mode'],
    rowsFromArgs: (a) => rowsFromArgs(a, mode),
    normalizeRow: (r) => normalizeRow(r, field, mode),
    dupKey: (r) => `${r.pid}-${r.site}`,
    tabUrl: (r) => `${CMS_ORIGIN}/v2/Product/Edit?site=${r.site}&productId=${r.pid}`,
    expectUrlPrefix: `${CMS_ORIGIN}/v2/Product/Edit`,
    runnerPath: RUNNER,
    adapter: () => productAdapter(readBundledRunnerCode(), mode),
    defaultTimeoutSec: DEFAULT_ROW_TIMEOUT_SEC,
    // Đo 24/09/2026: profile này mở được Product/Edit; <faq> bị accessdeny ở trang này.
    defaultProfile: '<profile-chrome>',
  });
};

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (err) => { console.error('LỖI:', err.message); process.exit(err.exitCode || 1); },
  );
}
