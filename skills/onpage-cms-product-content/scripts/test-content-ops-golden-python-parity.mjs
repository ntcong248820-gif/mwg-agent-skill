/**
 * test-content-ops-golden-python-parity.mjs — golden test: bản build của JS
 * (buildContentOps trong cms-content-ops-engine.js) phải byte-identical với script Python
 * gốc build-doc-bo-sung-highlight.py cho 2 key thật đã fact-check (`pro_cms`, `promax`) của
 * tasks/260907-canh-launching-iphone-18/work-items/260925-toi-uu-noi-dung-bai-sp-iphone-18-duo/
 * data/processed/additions-final-v4.json.
 *
 * Chạy python3 KHÔNG --create-doc/--update-doc (không đụng Google Doc, không mạng).
 *   node .claude/skills/onpage-cms-product-content/scripts/test-content-ops-golden-python-parity.mjs
 */
import { readFileSync, mkdtempSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
// .claude/skills/onpage-cms-product-content/scripts -> repo root -> tasks/.../260925-.../
const TASK_DIR = resolve(HERE, '..', '..', '..', '..', 'tasks',
  '260907-canh-launching-iphone-18', 'work-items', '260925-toi-uu-noi-dung-bai-sp-iphone-18-duo');
const PY_SCRIPT = join(TASK_DIR, 'scripts', 'build-doc-bo-sung-highlight.py');
const SPEC_FILE = join(TASK_DIR, 'data', 'processed', 'additions-final-v4.json');

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };

const src = readFileSync(join(HERE, 'cms-content-ops-engine.js'), 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(src + '\nexport { buildContentOps };').toString('base64')
);
const { buildContentOps } = mod;

const spec = JSON.parse(readFileSync(SPEC_FILE, 'utf8'));
const KEYS = ['pro_cms', 'promax'];
const tmpRoot = mkdtempSync(join(tmpdir(), 'cms-ops-golden-'));

try {
  for (const key of KEYS) {
    console.log(`\n# key "${key}"`);
    const entry = spec[key];
    t(`spec có key "${key}"`, !!entry, Object.keys(spec));
    if (!entry) continue;

    const baseFile = join(TASK_DIR, entry.base);
    // Python: open(...).read().lstrip('﻿') — bỏ BOM đầu file nếu có. JS đọc utf8 rồi
    // tự strip BOM giống hệt, để build() nhận đúng cùng 1 chuỗi input như bên Python.
    const rawWithBom = readFileSync(baseFile, 'utf8');
    const raw = rawWithBom.replace(/^﻿/, '');
    t(`base "${entry.base}" không rỗng`, raw.length > 0);

    const jsResult = buildContentOps(raw, entry.ops);
    t('JS buildContentOps ok (mọi op định vị được đúng 1 lần, không chồng lấn)', jsResult.ok, jsResult.reason);
    if (!jsResult.ok) continue;

    const outFile = join(tmpRoot, `${key}.html`);
    execFileSync('python3', [PY_SCRIPT, '--spec', SPEC_FILE, '--key', key, '--out', outFile], { cwd: TASK_DIR, stdio: ['ignore', 'pipe', 'pipe'] });
    const pyFinal = readFileSync(outFile, 'utf8');

    t(`JS final === Python final (byte-for-byte, ${jsResult.final.length} ký tự)`, jsResult.final === pyFinal,
      jsResult.final.length !== pyFinal.length
        ? `độ dài lệch: JS ${jsResult.final.length} vs Python ${pyFinal.length}`
        : (() => {
          for (let i = 0; i < jsResult.final.length; i++) {
            if (jsResult.final[i] !== pyFinal[i]) return `lệch tại ký tự ${i}: JS "${jsResult.final.slice(i, i + 40)}" vs PY "${pyFinal.slice(i, i + 40)}"`;
          }
          return 'độ dài bằng nhau, không tìm ra điểm lệch (không nên xảy ra)';
        })());
    t(`áp đúng ${entry.ops.length} ops`, jsResult.edits.length === entry.ops.length);
  }
} finally {
  rmSync(tmpRoot, { recursive: true, force: true });
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
