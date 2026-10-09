/**
 * pim-content-ops.mjs — sửa TỪNG CHỖ trong bài viết SP trên PIM (lệnh `product-ops`), không mạng.
 *
 * Dùng lại nguyên bộ máy ops của skill CMS bài SP (`cms-content-ops-engine.js`, bản copy byte-identical
 * của skill CMS bài SP): 5 loại op replace / after_p / before_h3 / before_p / before_tr,
 * định vị khớp ĐÚNG 1 lần (flex theo entity), chặn op chồng nhau, 5 bất biến (reversible, oldLinksKept,
 * oldImgsKept, changed, opsAllApplied), nhận diện "đã áp rồi" (ALREADY).
 *
 * File ops (JSON):
 *   {"field":"product_articles","expectedBeforeSha256":"<sha256 hex của bài lúc fact-check ops>",
 *    "ops":[{"id":"A1","type":"replace","find":"…","new":"…"}, {"id":"A2","type":"after_p","anchor":"…","new":"<p>…</p>"}]}
 *
 * Guard sha256 là chốt "bài đang sống trên PIM vẫn đúng là bài đã fact-check ops": lệch là dừng, không ghi.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { MdmError } from './mdm-core.mjs';
import { PRODUCT_HTML_FIELDS } from './pim-product-core.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
// Engine là file thuần (không ESM) để nạp được cả trong trang CMS; ở Node bỏ khối gán window rồi import qua data-url.
const engineSrc = fs.readFileSync(path.join(HERE, 'cms-content-ops-engine.js'), 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
const engine = await import(`data:text/javascript;base64,${Buffer.from(`${engineSrc}\nexport { buildContentOps, checkOpsInvariants, allOpsAlreadyApplied };`).toString('base64')}`);

export const OP_TYPES = ['replace', 'after_p', 'before_h3', 'before_p', 'before_tr'];
export const sha256 = (s) => crypto.createHash('sha256').update(String(s)).digest('hex');

/** Kiểm file ops (không mạng). Trả {field, expectedBeforeSha256, ops}. Sai → exit 2. */
export function validateOpsSpec(spec) {
  if (!spec || typeof spec !== 'object' || Array.isArray(spec)) throw new MdmError('file ops phải là object {field, expectedBeforeSha256, ops}', 2);
  const { field, expectedBeforeSha256: sha, ops } = spec;
  if (!PRODUCT_HTML_FIELDS.includes(field)) throw new MdmError(`ops chỉ áp cho ${PRODUCT_HTML_FIELDS.join(' | ')} (nhận "${field}") — title/description dùng product-write`, 2);
  if (typeof sha !== 'string' || !/^[0-9a-f]{64}$/.test(sha)) throw new MdmError('expectedBeforeSha256 phải là sha256 hex 64 ký tự của bài lúc fact-check ops', 2);
  if (!Array.isArray(ops) || !ops.length) throw new MdmError('ops rỗng', 2);
  const ids = new Set();
  ops.forEach((op, i) => {
    const where = `op #${i + 1}`;
    if (!op || typeof op !== 'object') throw new MdmError(`${where}: không phải object`, 2);
    if (op.id == null || ids.has(String(op.id))) throw new MdmError(`${where}: thiếu id hoặc id trùng`, 2);
    ids.add(String(op.id));
    if (!OP_TYPES.includes(op.type)) throw new MdmError(`${where} (${op.id}): type "${op.type}" không có — dùng ${OP_TYPES.join(' | ')}`, 2);
    if (typeof op.new !== 'string') throw new MdmError(`${where} (${op.id}): thiếu "new"`, 2);
    const loc = op.type === 'replace' ? 'find' : 'anchor';
    if (typeof op[loc] !== 'string' || !op[loc]) throw new MdmError(`${where} (${op.id}): ${op.type} cần "${loc}"`, 2);
  });
  return { field, expectedBeforeSha256: sha, ops };
}

export function loadOpsFile(file) {
  let spec;
  try { spec = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { throw new MdmError(`đọc --ops ${file} lỗi: ${e.message}`, 2); }
  return validateOpsSpec(spec);
}

/**
 * Áp ops lên NỘI DUNG HIỆN TẠI của mọi bản ghi đích (model, hoặc mọi lá Màu của trang).
 * befores: [{label, value}] — value là bài đang có (chuỗi, '' nếu chưa có).
 * Trả {status:'ALREADY'} khi mọi bản ghi đã chứa kết quả ops, hoặc {status:'OK', after, edits, invariants}.
 * Ném: exit 3 khi bài lệch bản fact-check (người khác vừa sửa, hoặc các lá đang khác nhau);
 *      exit 2 khi ops không định vị được / chồng nhau / phá bất biến.
 */
export function planOps(spec, befores) {
  if (!befores.length) throw new MdmError('không có bản ghi đích', 2);
  if (befores.every((b) => engine.allOpsAlreadyApplied(b.value, spec.ops))) return { status: 'ALREADY' };
  const off = befores.map((b) => ({ label: b.label, sha256: sha256(b.value), len: b.value.length })).filter((x) => x.sha256 !== spec.expectedBeforeSha256);
  if (off.length) {
    throw new MdmError(`ABORT: bài hiện tại lệch bản đã fact-check ops (expectedBeforeSha256) ở ${off.length}/${befores.length} bản ghi: ${off.map((x) => `${x.label} sha ${x.sha256.slice(0, 12)}… (${x.len} ký tự)`).join('; ')}. Không ghi gì — đọc lại bài, fact-check lại ops trên bản mới.`, 3);
  }
  const before = befores[0].value; // mọi bản ghi cùng sha → cùng nội dung
  const built = engine.buildContentOps(before, spec.ops);
  if (!built.ok) throw new MdmError(`ops không áp được: ${built.reason}`, 2);
  const invariants = engine.checkOpsInvariants({ before, after: built.final, edits: built.edits, opsLength: spec.ops.length });
  const broken = Object.entries(invariants).filter(([, ok]) => !ok).map(([k]) => k);
  if (broken.length) throw new MdmError(`ops phá bất biến ${broken.join(', ')} — không ghi`, 2);
  return {
    status: 'OK', after: built.final, invariants,
    edits: built.edits.map((e) => ({ id: e.id, at: e.start, removedLen: e.origText.length, insertedLen: e.new.length })),
  };
}
