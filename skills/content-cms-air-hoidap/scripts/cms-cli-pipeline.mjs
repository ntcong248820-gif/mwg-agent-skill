/**
 * cms-cli-pipeline.mjs — tham số, backup có kiểm, log từng dòng, và pipeline
 * "dry tất cả → backup lên đĩa → ghi từng dòng" dùng chung cho CLI chèn link CMS.
 *
 * BẢN COPY Y HỆT trong scripts/ của 4 skill CMS — xem đầu cms-cli-mcp.mjs.
 *
 * Luật cứng của pipeline:
 *   - rows rỗng = lỗi (exit 2), không bao giờ "pass".
 *   - dry của BẤT KỲ dòng nào không đạt = không ghi dòng nào.
 *   - không có file backup (tồn tại, không rỗng) trên đĩa = không ghi dòng đó.
 *   - mỗi dòng 1 lần evaluate, timeout riêng; kết quả ghi ra đĩa ngay khi xong dòng.
 *   - timeout / lỗi / FAIL giữa lô = dừng lô (không chạy song song dòng tiếp theo
 *     trong khi dòng cũ có thể vẫn đang chạy trong trang).
 *   - exit 0 chỉ khi mọi dòng DONE / ALREADY (live) hoặc DRY / ALREADY (dry).
 */

import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { CliError, McpClient, TimeoutError, evaluate, openAndBind } from './cms-cli-mcp.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

/** --key value | --key=value | --flag. Tham số không khai báo trong spec → lỗi (tránh gõ nhầm --liv). */
export function parseArgs(argv, { values = [], booleans = [] }) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (!a.startsWith('--')) throw new CliError(`tham số lạ: ${a}`, 2);
    let [k, v] = a.slice(2).split(/=(.*)/s);
    if (booleans.includes(k)) { out[k] = true; continue; }
    if (!values.includes(k)) throw new CliError(`không hỗ trợ --${k}`, 2);
    if (v === undefined) {
      v = argv[++i];
      if (v === undefined) throw new CliError(`--${k} thiếu giá trị`, 2);
    }
    out[k] = v;
  }
  return out;
}

export const sha256 = (s) => crypto.createHash('sha256').update(String(s), 'utf8').digest('hex');

export const runStamp = (d = new Date()) => {
  const p = (n) => String(n).padStart(2, '0');
  return `${String(d.getFullYear()).slice(2)}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
};

/**
 * Thư mục tasks/ CHUẨN của repo, suy từ vị trí file này: scripts -> skill -> skills ->
 * .claude -> repo root -> tasks. Dùng làm mặc định cho requireUnderTasksRoot — không phải
 * path bất kỳ chứa chữ "tasks" (vd /tmp/tasks, ~/tasks) như luật cũ, tránh backup rơi ra
 * ngoài repo. `tasksRoot` tiêm được qua tham số cho test dùng thư mục tạm làm "tasks/" giả.
 */
export function defaultTasksRoot() {
  return path.resolve(HERE, '..', '..', '..', '..', 'tasks');
}

/**
 * realpath của `p` dù `p` chưa tồn tại (vd --backup-dir sẽ mkdir sau): tìm tổ tiên gần
 * nhất còn tồn tại, realpath tổ tiên đó (giải symlink, vd /var -> /private/var trên
 * macOS), rồi ghép lại phần đuôi chưa tồn tại. Thiếu bước này thì so sánh path chưa
 * tồn tại (không realpath) với tasksRoot ĐÃ realpath luôn lệch nhau trên máy có symlink.
 */
function realpathEvenIfMissing(p) {
  const abs = path.resolve(p);
  try { return fs.realpathSync(abs); } catch { /* p chưa tồn tại — đi tìm tổ tiên còn tồn tại */ }
  const tail = [];
  let cur = abs;
  while (true) {
    const parent = path.dirname(cur);
    if (parent === cur) return abs; // đụng root mà vẫn không tồn tại — trả nguyên abs
    tail.unshift(path.basename(cur));
    cur = parent;
    try { return path.join(fs.realpathSync(cur), ...tail); } catch { /* tiếp tục lên tổ tiên xa hơn */ }
  }
}

/**
 * Bắt buộc `p` nằm TRONG `tasksRoot`, so bằng realpath cả 2 bên để chặn symlink / `..`
 * đi vòng ra ngoài. `p` có thể chưa tồn tại (vd --backup-dir sẽ mkdir sau).
 */
export function requireUnderTasksRoot(p, label, tasksRoot = defaultTasksRoot()) {
  const real = realpathEvenIfMissing(p);
  const realRoot = realpathEvenIfMissing(tasksRoot);
  if (real !== realRoot && !real.startsWith(realRoot + path.sep)) {
    throw new CliError(`${label} phải nằm trong ${realRoot} (thực tế: ${real})`, 2);
  }
  return real;
}

/**
 * Thư mục task phải tồn tại và nằm TRONG `tasks/` chuẩn của repo (không phải path bất kỳ
 * chứa chữ "tasks") — backup không bao giờ rơi ra gốc repo hay /tmp, ~/tasks...
 */
export function requireTaskDir(taskDir, { tasksRoot } = {}) {
  if (!taskDir) throw new CliError('thiếu --task-dir (tasks/{task}) — backup phải nằm trong task folder', 2);
  const abs = path.resolve(taskDir);
  if (!fs.existsSync(abs) || !fs.statSync(abs).isDirectory()) throw new CliError(`--task-dir không tồn tại: ${taskDir}`, 2);
  return requireUnderTasksRoot(abs, '--task-dir', tasksRoot);
}

/** Ghi file rồi đọc lại: tồn tại, không rỗng, đúng số byte. Không đạt → ném lỗi. */
export function writeVerified(file, content) {
  if (typeof content !== 'string' || content.length === 0) throw new CliError(`nội dung rỗng, không ghi ${path.basename(file)}`);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
  const bytes = Buffer.byteLength(content, 'utf8');
  const st = fs.statSync(file);
  if (st.size !== bytes || st.size === 0) throw new CliError(`ghi ${file} lệch byte (${st.size}/${bytes})`);
  return { file, bytes, sha256: sha256(content) };
}

/** Kiểm lại trên đĩa ngay trước khi ghi CMS: mọi file backup bắt buộc còn đó, không rỗng, đúng hash. */
export function backupStillOnDisk(files) {
  if (!Array.isArray(files) || !files.length) return false;
  return files.every((f) => {
    try {
      const buf = fs.readFileSync(f.file, 'utf8');
      return buf.length > 0 && sha256(buf) === f.sha256;
    } catch { return false; }
  });
}

/**
 * Marker "đang ghi dở" — ghi ra đĩa NGAY TRƯỚC mỗi lần POST ghi thật, xoá khi đã có kết
 * quả rõ ràng. Nằm ở thư mục CỐ ĐỊNH theo task+skill (không phải backupDir có timestamp
 * của từng lần chạy), để lần chạy sau (process khác, backupDir khác) vẫn thấy dấu vết nếu
 * tiến trình trước bị kill giữa lúc ghi (SIGKILL, mất mạng, agent bị dừng đột ngột).
 */
export function inflightDir(taskDir, backupSub) {
  return path.join(taskDir, 'data/raw', backupSub, '_inflight');
}

export function inflightMarkerFile(dir, key) {
  return path.join(dir, `${key}.json`);
}

export function writeInflightMarker(dir, { key, row, beforeSha }) {
  fs.mkdirSync(dir, { recursive: true });
  const file = inflightMarkerFile(dir, key);
  fs.writeFileSync(file, JSON.stringify({ key, row: row ?? null, beforeSha: beforeSha ?? null, at: new Date().toISOString(), pid: process.pid }, null, 2));
  return file;
}

/** Xoá marker khi đã có kết quả rõ ràng. Lỗi bỏ qua: file có thể đã mất/chưa từng ghi. */
export function clearInflightMarker(dir, key) {
  try { fs.unlinkSync(inflightMarkerFile(dir, key)); } catch { /* đã xoá hoặc chưa từng có */ }
}

/** Đọc marker còn sót từ lần chạy trước — null nếu không có / hỏng file. */
export function readInflightMarker(dir, key) {
  try { return JSON.parse(fs.readFileSync(inflightMarkerFile(dir, key), 'utf8')); } catch { return null; }
}

export function appendJsonl(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.appendFileSync(file, JSON.stringify({ at: new Date().toISOString(), ...obj }) + '\n');
}

/** Bỏ field nặng (_before, _after, backup, fullPageHtml...) trước khi ghi log/in màn hình. */
export function stripHeavy(v) {
  if (Array.isArray(v)) return v.map(stripHeavy);
  if (!v || typeof v !== 'object') return v;
  const out = {};
  for (const [k, x] of Object.entries(v)) {
    if (k.startsWith('_') || k === 'backup' || k === 'afterBody' || k === 'fullPageHtml') continue;
    out[k] = stripHeavy(x);
  }
  return out;
}

export function formatTable(rows, cols) {
  const cell = (r, c) => String(r[c] ?? '').replace(/\s+/g, ' ').slice(0, 90);
  const w = cols.map((c) => Math.max(c.length, ...rows.map((r) => cell(r, c).length)));
  const line = (vals) => vals.map((v, i) => v.padEnd(w[i])).join(' | ');
  return [line(cols), w.map((n) => '-'.repeat(n)).join('-|-'), ...rows.map((r) => line(cols.map((c) => cell(r, c))))].join('\n');
}

export const OK_DRY = new Set(['DRY', 'ALREADY']);
export const OK_LIVE = new Set(['DONE', 'ALREADY']);
// UNKNOWN: lỗi/timeout XẢY RA SAU khi evaluate ghi thật đã gửi — có thể POST đã tới CMS,
// không được coi là "chắc chắn chưa ghi" (finding #11). Luôn dừng lô, giữ marker in-flight.
const STOP_LIVE = new Set(['FAIL', 'ABORT', 'ERROR', 'UNKNOWN', 'BACKUP_MISMATCH']);

/**
 * Adapter mỗi skill cung cấp:
 *   key(row)                      → chuỗi định danh ổn định, dùng làm tên file
 *   dryCode(row)                  → JS function string, chạy runner dryRun + keepHtml cho 1 dòng
 *   judgeDry(out)                 → { status: 'DRY'|'ALREADY'|<khác>, reason }
 *   backupFiles(row, out)         → [{ name, content }] — TẤT CẢ bắt buộc, rỗng là không ghi
 *   beforeText(out)               → thân bài gốc (để guard hash lúc ghi)
 *   liveCode(row, { beforeSha })  → JS function string: guard hash rồi chạy runner dryRun:false
 *   judgeLive(out, { beforeSha, row }) → { status, reason, afterFiles?: [{name, content}] }
 */
export async function runRowPipeline({ rows, adapter, client, live, backupDir, idir, rowTimeoutMs, log = console.log }) {
  if (!Array.isArray(rows) || rows.length === 0) throw new CliError('rows rỗng — không có gì để chạy (coi là FAIL)', 2);
  const logFile = path.join(backupDir, 'run-log.jsonl');
  const results = rows.map((row) => ({ key: adapter.key(row), row: row.row ?? null, status: 'NOT_RUN', reason: null }));
  const save = () => fs.writeFileSync(path.join(backupDir, 'run-result.json'), JSON.stringify({ live, results }, null, 2));
  fs.mkdirSync(backupDir, { recursive: true });

  // Pha 1 — dry mọi dòng, ghi backup ngay khi dry xong dòng đó.
  for (let i = 0; i < rows.length; i++) {
    const res = results[i];
    log(`[dry ${i + 1}/${rows.length}] ${res.key}`);
    let out;
    try {
      out = await evaluate(client, adapter.dryCode(rows[i]), rowTimeoutMs);
    } catch (err) {
      res.status = err instanceof TimeoutError ? 'TIMEOUT' : 'ERROR';
      res.reason = `dry: ${err.message}`;
      appendJsonl(logFile, { phase: 'dry', ...res });
      return finish(results, live, log, 'dry', save);
    }
    const j = adapter.judgeDry(out);
    res.status = j.status;
    res.reason = j.reason ?? null;
    res.dry = stripHeavy(out?.rows?.[0] ?? out);
    // Marker ghi dở còn sót từ lần chạy trước (tiến trình bị kill giữa lúc ghi): dry-check
    // vừa đọc CMS TƯƠI nên đủ để phân loại — không cần gọi thêm evaluate nào khác.
    if (idir) {
      const marker = readInflightMarker(idir, res.key);
      if (marker) {
        if (res.status === 'ALREADY') {
          res.recovered = 'DONE_RECOVERED';
          log(`[recover] ${res.key}: marker ghi dở từ ${marker.at} (pid ${marker.pid}) — CMS đã có bản mới -> coi ALREADY, không ghi lại.`);
          clearInflightMarker(idir, res.key);
        } else if (res.status === 'DRY') {
          res.recovered = 'SAFE_PROCEED';
          log(`[recover] ${res.key}: marker ghi dở từ ${marker.at} (pid ${marker.pid}) — CMS vẫn ở bản cũ -> an toàn để ghi lại.`);
          clearInflightMarker(idir, res.key);
        } else {
          res.recovered = 'NEEDS_MANUAL_CHECK';
          log(`[recover] ${res.key}: marker ghi dở từ ${marker.at} (pid ${marker.pid}) — trạng thái hiện tại "${res.status}" không rõ ràng -> GIỮ marker, cần kiểm tay trước khi chạy lại.`);
        }
      }
    }
    if (j.status === 'DRY') {
      try {
        res.backupFiles = adapter.backupFiles(rows[i], out).map((f) => writeVerified(path.join(backupDir, f.name), f.content));
        res.beforeSha = sha256(adapter.beforeText(out));
      } catch (err) {
        res.status = 'NO_BACKUP';
        res.reason = err.message;
      }
    }
    appendJsonl(logFile, { phase: 'dry', ...stripHeavy(res) });
  }
  save();
  const dryOk = results.every((r) => OK_DRY.has(r.status));
  if (!live) return finish(results, live, log, null, save);
  if (!dryOk) {
    log('Dry có dòng không đạt → KHÔNG ghi dòng nào.');
    return finish(results, live, log, 'dry', save);
  }

  // Pha 2 — ghi từng dòng, mỗi dòng 1 evaluate.
  for (let i = 0; i < rows.length; i++) {
    const res = results[i];
    if (res.status !== 'DRY') continue;
    if (!backupStillOnDisk(res.backupFiles)) {
      res.status = 'NO_BACKUP';
      res.reason = 'file backup mất / rỗng / lệch hash ngay trước khi ghi — không ghi';
      appendJsonl(logFile, { phase: 'live', ...stripHeavy(res) });
      save();
      continue;
    }
    log(`[ghi ${i + 1}/${rows.length}] ${res.key}`);
    // Marker NGAY TRƯỚC evaluate ghi thật — bằng chứng "đang ghi dở" nếu tiến trình bị kill
    // giữa chừng (SIGKILL không kịp chạy finally). Chỉ xoá khi có kết quả DỨT KHOÁT bên dưới.
    if (idir) writeInflightMarker(idir, { key: res.key, row: res.row, beforeSha: res.beforeSha });
    const t0 = Date.now();
    let out;
    try {
      out = await evaluate(client, adapter.liveCode(rows[i], { beforeSha: res.beforeSha }), rowTimeoutMs);
    } catch (err) {
      // Timeout HAY lỗi thường đều có thể xảy ra SAU khi POST đã gửi đi (transport chết,
      // tab đóng giữa chừng...) — không có cách nào phân biệt chắc chắn "chưa ghi" ở đây,
      // nên gộp thành UNKNOWN thay vì coi lỗi thường là "chắc chắn chưa ghi" (finding #11).
      // Marker in-flight GIỮ NGUYÊN — lần chạy sau đọc CMS tươi để phân loại (finding #3).
      const timeout = err instanceof TimeoutError;
      res.status = 'UNKNOWN';
      res.reason = `${timeout ? 'timeout' : 'lỗi'} khi gọi ghi: ${err.message} — KHÔNG rõ đã ghi hay chưa (có thể POST đã gửi), đọc CMS dòng này trước khi chạy lại`;
      res.ms = Date.now() - t0;
      appendJsonl(logFile, { phase: 'live', ...stripHeavy(res) });
      save();
      log('Dừng lô sau lỗi/timeout không rõ trạng thái — các dòng sau giữ NOT_RUN. Marker in-flight được giữ lại.');
      return finish(results, live, log, null, save);
    }
    const j = adapter.judgeLive(out, { beforeSha: res.beforeSha, row: rows[i] });
    res.status = j.status;
    res.reason = j.reason ?? null;
    res.ms = Date.now() - t0;
    res.live = stripHeavy(out?.rows?.[0] ?? out);
    for (const f of j.afterFiles || []) {
      try { res.after = writeVerified(path.join(backupDir, f.name), f.content); } catch { /* after là bằng chứng phụ */ }
    }
    // Kết quả dứt khoát (kể cả FAIL/ABORT/SKIP) — không còn "không rõ", xoá marker.
    if (idir) clearInflightMarker(idir, res.key);
    appendJsonl(logFile, { phase: 'live', ...stripHeavy(res) });
    save();
    if (STOP_LIVE.has(res.status)) {
      log(`Dừng lô: ${res.key} → ${res.status}. Kiểm tay trước khi chạy tiếp.`);
      break;
    }
  }
  return finish(results, live, log, null, save);
}

function finish(results, live, log, stoppedAt, save) {
  const ok = live ? OK_LIVE : OK_DRY;
  if (live && stoppedAt !== 'dry') {
    for (const r of results) {
      if (r.status === 'DRY') { r.status = 'NOT_RUN'; r.reason = 'dry đạt nhưng chưa ghi — lô dừng trước dòng này'; }
    }
  }
  save();
  log('\n' + formatTable(results, ['key', 'row', 'status', 'reason']));
  const allOk = results.every((r) => ok.has(r.status));
  log(`\n${live ? 'LIVE' : 'DRY-RUN'}: ${results.filter((r) => ok.has(r.status)).length}/${results.length} đạt${stoppedAt === 'dry' ? ' — dry fail, không ghi gì' : ''}.`);
  if (!live && allOk) log('Dry đạt hết. Chạy lại cùng lệnh với --live để ghi thật.');
  return { results, exitCode: allOk ? 0 : 1 };
}

/** Đọc rows từ file JSON: mảng, hoặc { rows: [...] }. */
export function readRowsFile(file) {
  let raw;
  try { raw = JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { throw new CliError(`không đọc được --file ${file}: ${e.message}`, 2); }
  const rows = Array.isArray(raw) ? raw : Array.isArray(raw?.rows) ? raw.rows : null;
  if (!rows) throw new CliError('--file phải là mảng rows hoặc { rows: [...] }', 2);
  return rows;
}

/** Kiểm 1 dòng chèn link: đủ oldText, sentence, links[{anchor, href}] và anchor có trong câu. */
export function validateInsertRow(r, idField) {
  const miss = [];
  if (!r[idField]) miss.push(idField);
  if (!r.oldText || !String(r.oldText).trim()) miss.push('oldText');
  if (!r.sentence || !String(r.sentence).trim()) miss.push('sentence');
  if (!Array.isArray(r.links) || !r.links.length) miss.push('links');
  else r.links.forEach((l, i) => {
    if (!l || !l.anchor || !l.href) miss.push(`links[${i}].anchor/href`);
    else if (!String(r.sentence || '').includes(l.anchor)) miss.push(`links[${i}] anchor "${l.anchor}" không có trong sentence`);
  });
  if (miss.length) throw new CliError(`dòng ${r.row ?? '?'} thiếu/sai: ${miss.join(', ')}`, 2);
}

/**
 * Khung chung của CLI chèn link theo lô (bài tin, bài sản phẩm). Mỗi skill chỉ khai:
 *   spec = { backupSub, extraValues, rowsFromArgs(a), normalizeRow(r), dupKey(r),
 *            tabUrl(firstRow), expectUrlPrefix, runnerPath, adapter(runnerCode),
 *            defaultTimeoutSec, defaultProfile? }
 * defaultProfile: dùng khi --profile không truyền. Đo 24/09/2026 (chrome-profile open,
 * không --live): "<faq>" mở được Faq/NewsEdit + News/NewsEdit nhưng bị
 * /v2/accessdeny ở Product/Edit; "<profile-chrome>" mở được Product/Edit. Không khai
 * defaultProfile thì --profile vẫn bắt buộc như trước.
 * deps.tasksRoot: ghi đè thư mục tasks/ chuẩn của repo — CHỈ dùng cho test (mô phỏng
 * tasks/ giả trong thư mục tạm); không truyền thì dùng đúng tasks/ thật của repo.
 * deps.signalSource / deps.exitFn: tiêm được cho test SIGTERM/SIGINT (mặc định process
 * thật + process.exit) — xem khối bắt tín hiệu bên dưới.
 * Trả exit code. MCP luôn được đóng; tab chỉ đóng khi không có dòng UNKNOWN (finding #11).
 */
export async function runInsertCli(argv, deps, spec) {
  const log = deps.log || console.log;
  const a = parseArgs(argv, {
    values: ['profile', 'task-dir', 'backup-dir', 'file', 'timeout-sec', ...spec.extraValues],
    booleans: ['live', 'keep-tab'],
  });
  if (!a.profile) {
    if (!spec.defaultProfile) throw new CliError('thiếu --profile (key chrome-profile có quyền CMS) — không có mặc định', 2);
    a.profile = spec.defaultProfile;
    log(`(không truyền --profile, dùng mặc định "${a.profile}")`);
  }
  const taskDir = requireTaskDir(a['task-dir'], { tasksRoot: deps.tasksRoot });
  const rows = (a.file ? readRowsFile(a.file) : spec.rowsFromArgs(a)).map(spec.normalizeRow);
  if (!rows.length) throw new CliError('rows rỗng — không có gì để chạy (coi là FAIL)', 2);
  const keys = rows.map(spec.dupKey);
  const dupes = [...new Set(keys.filter((k, i) => keys.indexOf(k) !== i))];
  if (dupes.length) throw new CliError(`trùng bài trong cùng lô: ${dupes.join(', ')} — gộp câu hoặc tách lô`, 2);

  const backupDir = path.resolve(a['backup-dir'] || path.join(taskDir, 'data/raw', spec.backupSub, `${runStamp()}-${a.live ? 'live' : 'dry'}`));
  if (a['backup-dir']) requireUnderTasksRoot(backupDir, '--backup-dir', deps.tasksRoot ?? defaultTasksRoot());
  // Marker in-flight nằm CỐ ĐỊNH theo task+skill (không theo timestamp lô) — xem #3.
  const idir = inflightDir(taskDir, spec.backupSub);
  const rowTimeoutMs = Number(a['timeout-sec'] || spec.defaultTimeoutSec) * 1000;
  const client = deps.client || new McpClient({ spawnFn: deps.spawnFn });
  let pageId = null;
  let keepTab = !!a['keep-tab'];

  // Bắt SIGTERM/SIGINT: process bị kill giữa lúc chạy (agent bị dừng, máy shutdown...)
  // vẫn phải ghi lại dấu "interrupted" vào run-log trước khi thoát, và cố đóng tab/MCP
  // thay vì bỏ mặc — marker in-flight (nếu đang ghi dở) KHÔNG bị đụng vào ở đây, để lần
  // chạy sau tự phân loại qua dry-check (finding #3).
  const signalSource = deps.signalSource || process;
  const exitFn = deps.exitFn || ((code) => process.exit(code));
  let cleanedUpOnSignal = false;
  const handleSignal = async (sig) => {
    if (cleanedUpOnSignal) return;
    cleanedUpOnSignal = true;
    try {
      appendJsonl(path.join(backupDir, 'run-log.jsonl'), {
        phase: 'signal', signal: sig, note: 'interrupted — CLI bị dừng giữa chừng, kiểm tay dòng đang ghi (marker in-flight nếu có) trước khi chạy lại',
      });
    } catch { /* backupDir có thể chưa kịp mkdir — không chặn việc thoát an toàn */ }
    log(`\nNhận ${sig} — dừng, đóng tab/MCP trước khi thoát.`);
    try { if (pageId != null) await client.callTool('close_page', { pageId }, 5000); } catch { /* tab đã đóng hoặc lỗi — ưu tiên thoát an toàn */ }
    try { await client.close(); } catch { /* đã đóng */ }
    exitFn(130);
  };
  const onSigterm = () => { handleSignal('SIGTERM'); };
  const onSigint = () => { handleSignal('SIGINT'); };
  signalSource.on('SIGTERM', onSigterm);
  signalSource.on('SIGINT', onSigint);

  try {
    log('[1/3] Kết nối chrome-devtools-mcp...');
    await client.connect();
    log(`[2/3] Mở tab CMS bằng profile "${a.profile}", bám theo cdp-open token...`);
    ({ pageId } = await openAndBind(client, {
      profile: a.profile, url: spec.tabUrl(rows[0]), expectUrlPrefix: spec.expectUrlPrefix,
      execFileFn: deps.execFileFn, sleepFn: deps.sleepFn,
    }));
    log(`[3/3] ${a.live ? 'DRY rồi GHI THẬT' : 'DRY-RUN'} ${rows.length} dòng — backup: ${backupDir}`);
    const runnerCode = fs.readFileSync(spec.runnerPath, 'utf8');
    const { exitCode, results } = await runRowPipeline({
      rows, adapter: spec.adapter(runnerCode), client, live: !!a.live, backupDir, idir, rowTimeoutMs, log,
    });
    // UNKNOWN: runner có thể vẫn đang chạy trong tab — đóng tab là cắt ngang bước verify.
    if (results.some((r) => r.status === 'UNKNOWN')) keepTab = true;
    return exitCode;
  } finally {
    signalSource.off('SIGTERM', onSigterm);
    signalSource.off('SIGINT', onSigint);
    if (pageId != null && !keepTab) {
      try { await client.callTool('close_page', { pageId }, 15000); } catch { /* tab cuối hoặc đã đóng */ }
    }
    await client.close();
  }
}
