/**
 * mdm-commands-write.mjs — lệnh GHI: write (field SEO) và upload (ảnh), cả hai mặc định DRY.
 *
 * Luồng write --live (đã chứng minh bằng ghi thật 4 màn, 05/10/2026):
 *   đọc mới → áp sửa đúng key → chặn rơi key → backup cả bản ghi → POST kèm rowVersion vừa đọc
 *   → đọc lại → so tuyệt đối từng key + rowVersion phải tăng đúng 1.
 * Gặp row_version (có người ghi xen vào) thì DỪNG, không đọc lại rồi ghi đè.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { MdmError, applyEdits, assertNoDroppedKeys, buildUpdate, diffRaw, isRowVersionConflict, ENDPOINT } from './mdm-core.mjs';
import { readRecord } from './mdm-commands-lookup.mjs';

export const sha256 = (buf) => crypto.createHash('sha256').update(buf).digest('hex');
// Có mili-giây: 2 lần ghi trong cùng 1 giây không được đè file backup của nhau.
let seq = 0;
export const stamp = () => `${new Date().toISOString().replace(/[-:]/g, '').replace('Z', '').replace('T', '-').replace('.', '')}-${++seq}`;

function writeJson(file, data) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(data, null, 2));
  return file;
}

/** --set f=v / --set-file f=path → {field: string}. File đọc nguyên byte (utf8), không trim. */
export function collectEdits(sets = [], setFiles = []) {
  const edits = {};
  const take = (s, isFile) => {
    const i = s.indexOf('=');
    if (i < 1) throw new MdmError(`"${s}" phải dạng field=giá-trị`, 2);
    const f = s.slice(0, i);
    if (f in edits) throw new MdmError(`field "${f}" khai 2 lần`, 2);
    edits[f] = isFile ? fs.readFileSync(s.slice(i + 1), 'utf8') : s.slice(i + 1);
  };
  sets.forEach((s) => take(s, false));
  setFiles.forEach((s) => take(s, true));
  if (!Object.keys(edits).length) throw new MdmError('không có --set/--set-file nào', 2);
  return edits;
}

const summarize = (changed) => changed.map((c) => ({
  field: c.field,
  beforeLen: c.before == null ? null : String(c.before).length,
  afterLen: c.after.length,
  before: c.before != null && String(c.before).length <= 200 ? c.before : undefined,
  after: c.after.length <= 200 ? c.after : undefined,
  afterSha256: sha256(c.after),
}));

export async function writeCommand(s, cfg, { screen, id, edits, taskDir, live }) {
  if (!taskDir) throw new MdmError('thiếu --task-dir (backup và kết quả lưu trong task)', 2);
  const tag = `${screen}-${id.slice(0, 8)}-${stamp()}`;
  const info = await readRecord(s, cfg, screen, id);
  const before = info.rawValues;
  const { rawValues, changed } = applyEdits(screen, before, edits);
  if (!changed.length) return { status: 'NO_CHANGE', screen, id, rowVersion: info.rowVersion };
  assertNoDroppedKeys(before, rawValues);
  const payload = buildUpdate(screen, info, rawValues, cfg);
  const plan = { screen, id, rowVersion: info.rowVersion, changed: summarize(changed) };
  const planFile = writeJson(path.join(taskDir, 'data/processed', `mdm-plan-${tag}.json`), { ...plan, afterValues: Object.fromEntries(changed.map((c) => [c.field, c.after])) });
  if (!live) return { status: 'DRY', ...plan, planFile, next: 'xem plan rồi chạy lại kèm --live' };

  const backupFile = writeJson(path.join(taskDir, 'data/raw', `mdm-backup-${tag}.json`), info);
  const t0 = Date.now();
  const res = await s.post('mdm', ENDPOINT[screen].write, payload);
  const ms = Date.now() - t0;
  if (isRowVersionConflict(res)) {
    throw new MdmError(`ROW_VERSION: có người vừa sửa bản ghi (${res.toastMessage}). Không ghi gì. Đọc lại, đối chiếu thay đổi của họ rồi mới chạy lại — không ép.`, 3);
  }
  if (res.error) throw new MdmError(`server từ chối ghi: ${res.toastMessage || res.errorReason} (backup: ${backupFile})`, 1);

  const after = await readRecord(s, cfg, screen, id);
  const mismatch = diffRaw(rawValues, after.rawValues);
  const result = {
    status: mismatch.length === 0 && after.rowVersion === info.rowVersion + 1 ? 'WRITTEN' : 'VERIFY_FAIL',
    ...plan, ms, rowVersionAfter: after.rowVersion, mismatchKeys: mismatch, backupFile, planFile,
  };
  result.resultFile = writeJson(path.join(taskDir, 'data/processed', `mdm-write-${tag}.json`), result);
  if (result.status !== 'WRITTEN') throw new MdmError(`đọc lại không khớp (${mismatch.join(', ') || `rowVersion ${after.rowVersion}`}) — xem ${result.resultFile}, khôi phục bằng restore`, 1);
  return result;
}

/** Ghi lại rawValues của file backup (khôi phục). Vẫn kèm rowVersion hiện tại + so lại từng byte. */
export async function restoreCommand(s, cfg, { backupFile, screen, taskDir, live }) {
  const backup = JSON.parse(fs.readFileSync(backupFile, 'utf8'));
  const cur = await readRecord(s, cfg, screen, backup.id);
  const diff = diffRaw(backup.rawValues, cur.rawValues);
  if (!diff.length) return { status: 'ALREADY', id: backup.id, rowVersion: cur.rowVersion };
  if (!live) return { status: 'DRY', id: backup.id, keysToRestore: diff, rowVersion: cur.rowVersion };
  writeJson(path.join(taskDir, 'data/raw', `mdm-before-restore-${screen}-${backup.id.slice(0, 8)}-${stamp()}.json`), cur);
  const res = await s.post('mdm', ENDPOINT[screen].write, buildUpdate(screen, cur, backup.rawValues, cfg));
  if (isRowVersionConflict(res)) throw new MdmError(`ROW_VERSION khi khôi phục: ${res.toastMessage} — dừng`, 3);
  if (res.error) throw new MdmError(`server từ chối khôi phục: ${res.toastMessage}`, 1);
  const after = await readRecord(s, cfg, screen, backup.id);
  const left = diffRaw(backup.rawValues, after.rawValues);
  return { status: left.length ? 'VERIFY_FAIL' : 'RESTORED', id: backup.id, rowVersionAfter: after.rowVersion, mismatchKeys: left };
}

const EXT_MIME = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif', webp: 'image/webp' };
const MAX_BYTES = 8 * 1024 * 1024;

/**
 * Upload 1 ảnh lên CDN qua s3/cdnput (đo 05/10/2026: 0,8s, không nén lại, tên = tên gốc + hậu tố
 * giờ HHmmss, thư mục pim/cdn/images/{yyyymm}/). Server KHÔNG chặn trùng tên → chạy lại là up
 * thêm bản mới; sổ ledger theo sha256 trong task chặn việc đó. Không có API xoá ảnh.
 */
export async function uploadCommand(s, cfg, { file, taskDir, live, fetchFn = fetch }) {
  if (!taskDir) throw new MdmError('thiếu --task-dir (sổ ảnh đã up nằm trong task)', 2);
  const ext = path.extname(file).slice(1).toLowerCase();
  if (!EXT_MIME[ext]) throw new MdmError(`đuôi .${ext} không hỗ trợ (jpg, jpeg, png, gif, webp)`, 2);
  const buf = fs.readFileSync(file);
  if (buf.length > MAX_BYTES) throw new MdmError(`ảnh ${buf.length} byte > 8 MB`, 2);
  const hash = sha256(buf);
  const ledgerFile = path.join(taskDir, 'data/processed', 'mdm-upload-ledger.json');
  const ledger = fs.existsSync(ledgerFile) ? JSON.parse(fs.readFileSync(ledgerFile, 'utf8')) : {};
  if (ledger[hash]) return { status: 'REUSED', file: path.basename(file), url: ledger[hash].url, note: 'ảnh này (cùng byte) đã up trước đó — dùng lại URL' };
  if (!live) return { status: 'DRY', file: path.basename(file), bytes: buf.length, sha256: hash, next: 'chạy lại kèm --live để up' };

  const [r] = await s.run([{ api: 'pim', upload: { b64: buf.toString('base64'), name: path.basename(file), mime: EXT_MIME[ext], allowedExtensions: 'gif,jpeg,jpg,png,tiff,webp' } }]);
  if (!r || !r.ok || !r.json) throw new MdmError(`upload lỗi: ${r && (r.error || r.text)}`, 1);
  if (r.json.error || !r.json.object || !r.json.object.filePath) throw new MdmError(`server từ chối ảnh: ${r.json.toastMessage}`, 1);
  const url = r.json.object.filePath.startsWith('http') ? r.json.object.filePath : `https://cdnv2.tgdd.vn/${r.json.object.filePath}`;
  ledger[hash] = { url, file: path.basename(file), bytes: buf.length, at: new Date().toISOString() };
  fs.mkdirSync(path.dirname(ledgerFile), { recursive: true });
  fs.writeFileSync(ledgerFile, JSON.stringify(ledger, null, 2));
  const head = await fetchFn(url, { method: 'HEAD' });
  const cdnBytes = Number(head.headers.get('content-length'));
  return { status: cdnBytes === buf.length ? 'UPLOADED' : 'UPLOADED_SIZE_MISMATCH', file: path.basename(file), url, bytes: buf.length, cdnStatus: head.status, cdnBytes, ms: r.ms };
}
