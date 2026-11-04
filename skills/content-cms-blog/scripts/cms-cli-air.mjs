/**
 * cms-cli-air.mjs — phần chung của CLI air bài (Hỏi Đáp, Infobox): chọn ảnh theo HTML,
 * kiểm tên trên CDN, nghiệm thu byte ảnh đã upload, thay src, diff, nghiệm thu trang live.
 *
 * BẢN COPY Y HỆT trong scripts/ của content-cms-air-hoidap, content-cms-air-infobox và content-cms-blog
 * (skill-sync không mang file ngoài thư mục skill). Test parity ở
 * onpage-cms-news-insert/scripts/test-cms-cli-news.mjs.
 */

import fs from 'node:fs';
import path from 'node:path';
import { execFile as nodeExecFile } from 'node:child_process';
import { CliError, sleep } from './cms-cli-mcp.mjs';

export const CDN_NEWS_BASE = (newsId) => `https://cdnv2.tgdd.vn/mwg-static/common/News/${newsId}/`;

const imgSrcs = (html) => [...String(html).matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map((m) => m[1]);

/**
 * Ảnh cần upload = file trong `imagesDir` mà HTML tham chiếu (theo tên file cuối src).
 * `localOnly`: chỉ tính src tương đối (images-processed/...) — kiểu Hỏi Đáp.
 * Src tương đối trỏ tới file không có trong thư mục → lỗi (thiếu ảnh local).
 */
export function imagesToUpload(html, imagesDir, { localOnly = false } = {}) {
  const have = new Set(fs.existsSync(imagesDir) ? fs.readdirSync(imagesDir) : []);
  const names = new Set();
  const missingLocal = [];
  for (const src of imgSrcs(html)) {
    const isRemote = /^https?:\/\//i.test(src);
    if (localOnly && isRemote) continue;
    const name = decodeURIComponent(src.split('/').pop().split('?')[0]);
    if (have.has(name)) names.add(name);
    else if (!isRemote) missingLocal.push(src);
  }
  if (missingLocal.length) throw new CliError(`HTML tham chiếu ảnh local không có trong ${imagesDir}: ${missingLocal.slice(0, 5).join(', ')}`);
  return [...names].sort().map((n) => path.join(imagesDir, n));
}

/** HEAD từng tên trên CDN: 404 = trống, 200 = đã có (CMS từ chối ghi đè, không xoá được). */
export async function cdnHeadCheck(base, files, fetchFn = fetch) {
  const out = {};
  for (const f of files) {
    const name = path.basename(f);
    try { out[name] = (await fetchFn(base + encodeURIComponent(name), { method: 'HEAD', cache: 'no-store' })).status; } catch { out[name] = 'ERR'; }
  }
  return { heads: out, taken: Object.keys(out).filter((n) => out[n] === 200), errors: Object.keys(out).filter((n) => out[n] === 'ERR') };
}

/** Nghiệm thu từ ngoài: GET từng URL đã upload, so từng byte với file local. */
export async function verifyCdnBytes(uploaded, imagesDir, fetchFn = fetch) {
  const bad = [];
  for (const [name, url] of Object.entries(uploaded || {})) {
    try {
      const r = await fetchFn(url, { cache: 'no-store' });
      if (r.status !== 200) { bad.push(`${name}: HTTP ${r.status}`); continue; }
      const remote = Buffer.from(await r.arrayBuffer());
      const local = fs.readFileSync(path.join(imagesDir, name));
      if (!remote.equals(local)) bad.push(`${name}: lệch byte (${remote.length}/${local.length})`);
    } catch (e) { bad.push(`${name}: ${e.message}`); }
  }
  return { ok: bad.length === 0, bad };
}

/**
 * Thay src ảnh theo tên file bằng URL CDN vừa upload. Assert phép đảo ngược:
 * thay ngược lại phải ra đúng HTML gốc từng byte, không thì có chỗ khác bị đụng → dừng.
 */
export function replaceImageSrcs(html, uploaded) {
  const pairs = [];
  for (const src of new Set(imgSrcs(html))) {
    const name = decodeURIComponent(src.split('/').pop().split('?')[0]);
    const url = uploaded[name];
    if (url && url !== src) pairs.push([src, url]);
  }
  let out = html;
  for (const [from, to] of pairs) {
    if (html.includes(to)) throw new CliError(`URL mới đã có sẵn trong bài (${to}) — thay ngược không kiểm được, kiểm tay`);
    out = out.split(`"${from}"`).join(`"${to}"`).split(`'${from}'`).join(`'${to}'`);
  }
  let back = out;
  for (const [from, to] of pairs) back = back.split(`"${to}"`).join(`"${from}"`).split(`'${to}'`).join(`'${from}'`);
  if (back !== html) throw new CliError('thay ngược không ra HTML gốc — có chỗ khác bị đụng, dừng');
  return { html: out, replaced: pairs.length };
}

const strip = (s) => s.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
const headingsOf = (h) => [...h.matchAll(/<(h[1-6])\b[^>]*>([\s\S]*?)<\/\1>/gi)].map((m) => `${m[1].toLowerCase()}: ${strip(m[2])}`);

/** Diff tóm tắt cho user duyệt: độ dài, ảnh, link, heading thêm/bớt. */
export function diffSummary(before, after) {
  const ha = headingsOf(before), hb = headingsOf(after);
  const ia = imgSrcs(before).map((s) => s.split('/').pop()), ib = imgSrcs(after).map((s) => s.split('/').pop());
  const n = (h, re) => (h.match(re) || []).length;
  return {
    len: [before.length, after.length], imgs: [ia.length, ib.length], links: [n(before, /<a\s/gi), n(after, /<a\s/gi)],
    headingsRemoved: ha.filter((x) => !hb.includes(x)), headingsAdded: hb.filter((x) => !ha.includes(x)),
    imgsRemoved: ia.filter((x) => !ib.includes(x)), imgsAdded: ib.filter((x) => !ia.includes(x)),
  };
}

// Trang live encode lại ký tự Latin-1 thành named entity (&ecirc; &aacute;...) dù DB lưu ký tự thô.
const NAMED = { nbsp: 160, quot: 34, amp: 38, lt: 60, gt: 62, apos: 39, ndash: 8211, mdash: 8212, lsquo: 8216, rsquo: 8217, ldquo: 8220, rdquo: 8221, hellip: 8230, Ntilde: 0xd1, ntilde: 0xf1 };
const L1 = { grave: [0xc0, 0xc8, 0xcc, 0xd2, 0xd9], acute: [0xc1, 0xc9, 0xcd, 0xd3, 0xda, 0xdd], circ: [0xc2, 0xca, 0xce, 0xd4, 0xdb], tilde: [0xc3, null, null, 0xd5, null] };
const VOW = { grave: 'AEIOU', acute: 'AEIOUY', circ: 'AEIOU', tilde: 'AEIOU' };
for (const [k, codes] of Object.entries(L1)) codes.forEach((c, i) => { if (c) { NAMED[VOW[k][i] + k] = c; NAMED[VOW[k][i].toLowerCase() + k] = c + 32; } });
export const decodeEntities = (s) => s.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n)).replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
  .replace(/&([A-Za-z]+);/g, (m, n) => (NAMED[n] ? String.fromCodePoint(NAMED[n]) : m));
const text = (s) => decodeEntities(s.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
const liveHeads = (h) => [...h.matchAll(/<(h[2-4])\b[^>]*>([\s\S]*?)<\/\1>/gi)].map((m) => text(m[2])).filter(Boolean);

/**
 * Nghiệm thu trang live: (tuỳ chọn) ?clearcache=1 rồi đọc URL TRƠN; heading + tên ảnh của
 * bản gửi phải có mặt, heading chỉ-có-ở-bản-cũ không được còn.
 *
 * Fingerprint nội dung (#12): heading/ảnh không đổi mà chỉ sửa chữ (không thêm/bớt heading
 * hay ảnh) thì 2 kiểm trên vẫn PASS dù trang live còn cache cũ. Thêm: 200 ký tự đầu + 200 ký
 * tự cuối của TEXT bản mới (đã strip tag + shortcode) phải có mặt trên live, và đoạn live từ đầu tới cuối
 * thân bài phải dài xấp xỉ text bản mới — bắt được ca "giữ nguyên heading/ảnh, chỉ đổi câu chữ, cache cũ".
 * Shortcode ([Product_Promotion …]) live render thành khối khác nên bỏ khỏi fingerprint; bài có shortcode
 * thì live chỉ được dài hơn, không bị chặn trần. Độ dài đo trên đoạn thân bài, không phải text cả trang
 * (cả trang ~450k ký tự — so cả trang thì trang thật nào cũng FAIL, đo 02/11/2026 bài 1467850, 1602135).
 */
const FINGERPRINT_LEN = 200;
export async function liveCheck({ url, html, old = null, clearcache = true, fetchFn = fetch }) {
  const UA = { headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh) mwg-cms-cli-verify' } };
  if (clearcache) await (await fetchFn(url + (url.includes('?') ? '&' : '?') + 'clearcache=1', UA)).text();
  const res = await fetchFn(url, UA);
  const live = await res.text();
  const liveText = text(live);
  const liveH = liveHeads(live);
  const mine = liveHeads(html);
  const myImgs = [...new Set(imgSrcs(html).map((s) => s.split('/').pop()))];
  const oldOnly = old ? liveHeads(old).filter((x) => !mine.includes(x)) : [];
  const SHORTCODE = /\[\/?[A-Za-z_]+(?:\s[^\]]*)?\]/g;
  const hasShortcode = SHORTCODE.test(html);
  // Fingerprint lấy từ đoạn text dài nhất giữa các shortcode (đầu/cuối của nó), không lấy chỗ dính shortcode.
  const myText = text(html.replace(SHORTCODE, '\u0000')).split('\u0000').map((x) => x.trim()).sort((a, b) => b.length - a.length)[0] || '';
  const fpHead = myText.slice(0, FINGERPRINT_LEN);
  const fpTail = myText.length > FINGERPRINT_LEN ? myText.slice(-FINGERPRINT_LEN) : fpHead;
  const hi = liveText.indexOf(fpHead);
  const ti = hi < 0 ? -1 : liveText.indexOf(fpTail, hi);
  const fingerprintPresent = myText.length === 0 || (hi >= 0 && ti >= 0);
  const span = hi >= 0 && ti >= 0 ? ti + fpTail.length - hi : -1;
  const lenTolerance = Math.max(80, Math.round(myText.length * 0.2));
  const lengthWithinTolerance = myText.length === 0 || (span >= 0 && span >= myText.length - lenTolerance && (hasShortcode || span <= myText.length + lenTolerance));
  const out = {
    url, http: res.status,
    headingsMissing: mine.filter((x) => !liveText.includes(x)).slice(0, 10), headings: mine.length,
    imagesMissing: myImgs.filter((n) => !live.includes(n)), images: myImgs.length,
    // Chỉ dò trong thẻ heading của trang live: shortcode khuyến mãi render tên SP động vào thân bài,
    // dò full text báo giả (đo 24/09/2026 bài 1382098: "Dell 15 DC15255" nằm trong box GIẢM SỐC).
    oldHeadingsStillLive: oldOnly.filter((x) => liveH.some((h) => h.includes(x)) && !mine.some((m) => m.includes(x))).slice(0, 10),
    fingerprint: { present: fingerprintPresent, lengthWithinTolerance, myTextLen: myText.length, liveSpanLen: span, hasShortcode },
  };
  out.pass = out.http === 200 && !out.headingsMissing.length && !out.imagesMissing.length && !out.oldHeadingsStillLive.length
    && fingerprintPresent && lengthWithinTolerance;
  return out;
}

/**
 * Đợi rồi mới nghiệm thu live: gọi clearcache sớm hơn ~60s sau khi ghi là đóng băng bài cũ.
 * Fail lần đầu → đợi thêm rồi thử đúng 1 lần nữa.
 */
export async function waitThenVerify(verifyFn, { delayMs = 60000, attempts = 2, sleepFn = sleep, log = console.log } = {}) {
  let last;
  for (let i = 0; i < attempts; i++) {
    log(`Đợi ${Math.round(delayMs / 1000)}s trước khi clearcache + nghiệm thu live (lần ${i + 1}/${attempts})...`);
    await sleepFn(delayMs);
    last = await verifyFn();
    if (last.pass) return last;
  }
  return last;
}

/**
 * Kế hoạch upload idempotent cho chạy không người trông (--step all): HEAD từng tên trên CDN.
 *   404 → cần upload · 200 + byte trùng file local → dùng lại URL, không upload
 *   200 + byte lệch → XUNG ĐỘT (CDN không xoá/ghi đè được) · lỗi mạng → lỗi.
 * Có xung đột hoặc lỗi thì caller phải dừng trước mọi POST.
 */
export async function planImageUploads(base, files, fetchFn = fetch) {
  const plan = { upload: [], reuse: {}, conflicts: [], errors: [] };
  for (const f of files) {
    const name = path.basename(f);
    const url = base + encodeURIComponent(name);
    let status;
    try { status = (await fetchFn(url, { method: 'HEAD', cache: 'no-store' })).status; } catch (e) { plan.errors.push(`${name}: HEAD ${e.message}`); continue; }
    if (status === 404) { plan.upload.push(f); continue; }
    if (status !== 200) { plan.errors.push(`${name}: HEAD ${status}`); continue; }
    try {
      const r = await fetchFn(url, { cache: 'no-store' });
      const remote = Buffer.from(await r.arrayBuffer());
      if (remote.equals(fs.readFileSync(f))) plan.reuse[name] = url;
      else plan.conflicts.push(`${name}: tên đã có trên CDN nhưng lệch byte (${remote.length}/${fs.statSync(f).size}) — đổi tên file`);
    } catch (e) { plan.errors.push(`${name}: GET ${e.message}`); }
  }
  return plan;
}

/** Slug URL CMS: chữ thường không dấu, số, gạch nối đơn; không gạch đầu/cuối. Trả chuỗi lỗi hoặc null. */
export function slugError(slug, max = 100) {
  if (!slug) return 'url rỗng';
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) return `url "${slug}" sai dạng (chỉ a-z 0-9 và gạch nối đơn)`;
  if (slug.length > max) return `url dài ${slug.length}>${max}`;
  return null;
}

/**
 * Sổ bài đã tạo — chốt chống tạo trùng. Nằm ở CẤP REPO (`<repo>/tasks/_state/cms-created-<skill>.json`),
 * KHÔNG theo từng task-dir (#10 review 24/09/2026): tạo lại cùng slug từ task khác (work-item vs task
 * cha), hoặc 2 worker chạy song song, đều đọc sổ theo-task-dir rỗng → tạo trùng. Một sổ chung cố định +
 * khoá file (`wx`) + ghi atomic (tmp rồi rename) đóng đường race đó.
 */
export function repoRootFromTaskDir(W) {
  const abs = path.resolve(W);
  const marker = `${path.sep}tasks${path.sep}`;
  const idx = abs.indexOf(marker);
  if (idx === -1) throw new CliError(`--task-dir phải nằm dưới <repo>/tasks/ (đang: ${abs})`);
  return abs.slice(0, idx);
}
export function repoLedgerPath(W, skillName) {
  return path.join(repoRootFromTaskDir(W), 'tasks/_state', `cms-created-${skillName}.json`);
}

export function readLedger(file) {
  if (!fs.existsSync(file)) return [];
  const raw = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!Array.isArray(raw)) throw new CliError(`${file} không phải mảng — sửa tay trước khi tạo bài`);
  return raw;
}

/** Ghi atomic: tmp (tên riêng theo pid) rồi rename — không bao giờ để file ở trạng thái nửa-ghi. */
function writeLedgerAtomic(file, rows) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = `${file}.tmp-${process.pid}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  fs.writeFileSync(tmp, JSON.stringify(rows, null, 1));
  fs.renameSync(tmp, file);
}

/**
 * Khoá file kiểu `wx` (O_EXCL — atomic "tạo nếu chưa có", tiêu chuẩn cho lock đơn giản trên 1 máy).
 * Có tiến trình khác giữ khoá thì spin-wait ngắn tới 5s rồi báo lỗi rõ (không treo vô hạn).
 */
function withLedgerLock(file, fn) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const lockFile = `${file}.lock`;
  const deadline = Date.now() + 5000;
  for (;;) {
    try { fs.writeFileSync(lockFile, String(process.pid), { flag: 'wx' }); break; }
    catch (e) {
      if (e.code !== 'EEXIST') throw e;
      if (Date.now() > deadline) throw new CliError(`không lấy được khoá ${lockFile} trong 5s — tiến trình khác đang ghi sổ, hoặc lock cũ bị kẹt (xoá tay ${lockFile} nếu chắc chắn không ai đang chạy)`);
      const until = Date.now() + 25;
      while (Date.now() < until) { /* spin ngắn — ledger nhỏ, giữ khoá vài ms */ }
    }
  }
  try { return fn(); } finally { try { fs.unlinkSync(lockFile); } catch { /* đã xoá / chưa từng có */ } }
}

export function ledgerUpsert(file, entry) {
  return withLedgerLock(file, () => {
    const rows = readLedger(file).filter((r) => r.key !== entry.key);
    rows.push({ ...entry, at: new Date().toISOString() });
    writeLedgerAtomic(file, rows);
    return rows;
  });
}
export function ledgerRemove(file, key) {
  return withLedgerLock(file, () => {
    const rows = readLedger(file).filter((r) => r.key !== key);
    writeLedgerAtomic(file, rows);
    return rows;
  });
}

/**
 * Kiểm trùng + ghi PENDING trong CÙNG MỘT khoá — đóng cửa sổ race giữa "đọc sổ thấy trống" và
 * "ghi PENDING" (2 worker/2 task-dir cùng đọc trống rồi cùng ghi thì 1 trong 2 phải thua).
 * Trả `{ prior: null }` khi claim thành công (đã ghi PENDING), `{ prior: <dòng cũ> }` khi đã có.
 */
export function ledgerClaim(file, key, pendingEntry) {
  return withLedgerLock(file, () => {
    const rows = readLedger(file);
    const prior = rows.find((r) => r.key === key);
    if (prior) return { prior };
    const next = [...rows, { ...pendingEntry, key, at: new Date().toISOString() }];
    writeLedgerAtomic(file, next);
    return { prior: null };
  });
}

/** Chạy 1 script node của skill (không sửa script), trả { code, stdout, stderr }. */
export function runNode(script, args, execFileFn = nodeExecFile) {
  return new Promise((resolve) => {
    execFileFn(process.execPath, [script, ...args], { maxBuffer: 64 * 1024 * 1024 }, (err, stdout, stderr) => {
      resolve({ code: err ? (typeof err.code === 'number' ? err.code : 1) : 0, stdout: String(stdout || ''), stderr: String(stderr || '') });
    });
  });
}
