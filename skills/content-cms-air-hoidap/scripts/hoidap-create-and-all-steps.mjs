/**
 * hoidap-create-and-all-steps.mjs — 2 bước mới của run-air-hoidap-cli.mjs:
 *
 *   --step create   tạo bài Hỏi Đáp mới trên /v2/Faq/NewsEdit?newsId=0 (hdCreateArticle).
 *                   Dry mặc định: dựng payload thật, kiểm mọi bất biến, lưu payload vào task. --live mới POST,
 *                   lấy newsId, đọc lại NewsEdit?newsId=<id> để so field, ghi sổ cms-created-hoidap.json.
 *   --step all      chạy không người trông: [create] → upload ảnh (tên đã có trên CDN chỉ bỏ qua khi TRÙNG
 *                   BYTE, lệch = dừng) → thay src → dry ghi + mọi bất biến → backup → ghi → verify server →
 *                   đợi 60s → ?clearcache=1 → nghiệm thu live (thử lại 1 lần). Không --live thì dừng sau dry.
 *
 * Mọi lỗi bất biến dừng TRƯỚC mọi POST. Exit ≠ 0 khi bất kỳ bước nào không đạt.
 */

import fs from 'node:fs';
import path from 'node:path';
import { CliError, TimeoutError, evaluate, removeInputFn, uploadToOwnInput, withRunner } from './cms-cli-mcp.mjs';
import {
  clearInflightMarker, formatTable, inflightDir, readInflightMarker, runStamp, sha256, writeInflightMarker, writeVerified,
} from './cms-cli-pipeline.mjs';
import {
  CDN_NEWS_BASE, imagesToUpload, ledgerClaim, ledgerRemove, ledgerUpsert, planImageUploads, readLedger, repoLedgerPath, replaceImageSrcs, slugError, verifyCdnBytes,
} from './cms-cli-air.mjs';
import { checkPage, paths, runLiveVerify, stepWrite } from './run-air-hoidap-cli.mjs';

const J = (v) => JSON.stringify(v);
const THUMB_INPUT = 'claudeHdThumb';
const IMG_INPUT = 'claudeHdImages';
const STATUS_ALIAS = { 1: '1', draft: '1', nhap: '1', 2: '2', actived: '2', 'xuat-ban': '2', 3: '3', pending: '3', 'cho-duyet': '3', 4: '4', approved: '4', 'da-duyet': '4' };
export const STATUS_LABEL = { 1: 'Nháp', 2: 'Xuất bản', 3: 'Chờ duyệt', 4: 'Đã duyệt' };
export const LIVE_URL = (slug, newsId) => `https://www.thegioididong.com/hoi-dap/${slug}-${newsId}`;
const list = (v) => (Array.isArray(v) ? v : String(v ?? '').split(',')).map((x) => String(x).trim()).filter(Boolean);

/**
 * Gom field tạo bài từ --create-file (JSON) + cờ (cờ đè file). Kiểm tĩnh TRƯỚC khi mở trình duyệt.
 * Trạng thái bắt buộc qua --status — không có mặc định, để không bao giờ xuất bản ngầm.
 */
export function readCreateSpec(a, { allowFieldFlags = true } = {}) {
  let file = {};
  if (a['create-file']) {
    try { file = JSON.parse(fs.readFileSync(a['create-file'], 'utf8')); } catch (e) { throw new CliError(`không đọc được --create-file: ${e.message}`, 2); }
  }
  if (!allowFieldFlags && (a.title || a['meta-title'] || a['meta-description'])) {
    throw new CliError('--step all --create-file: field bài mới lấy từ file; bỏ --title/--meta-title/--meta-description', 2);
  }
  const base = a['create-file'] ? path.dirname(path.resolve(a['create-file'])) : process.cwd();
  const rel = (p) => (p ? path.resolve(base, p) : null);
  const pick = (flag, key) => a[flag] ?? file[key];
  const spec = {
    title: String(pick('title', 'title') ?? '').trim(),
    url: String(pick('url', 'url') ?? '').trim(),
    metaTitle: String(pick('meta-title', 'metaTitle') ?? '').trim(),
    metaDescription: String(pick('meta-description', 'metaDescription') ?? '').trim(),
    keywords: list(pick('keywords', 'keywords')),
    articleType: String(pick('article-type', 'articleType') ?? '').trim(),
    childCategories: list(pick('child-category', 'childCategories')),
    parentCategories: list(pick('parent-category', 'parentCategories')),
    thumbnail: a.thumbnail ? path.resolve(a.thumbnail) : rel(file.thumbnail),
    thumbnailUrl: String(pick('thumbnail-url', 'thumbnailUrl') ?? '').trim(),
    htmlPath: a['create-html'] ? path.resolve(a['create-html']) : rel(file.html),
  };
  if (file.status != null && a.status != null && STATUS_ALIAS[String(file.status).toLowerCase()] !== STATUS_ALIAS[String(a.status).toLowerCase()]) {
    throw new CliError(`--status ${a.status} khác status trong --create-file (${file.status}) — thống nhất lại`, 2);
  }
  spec.status = a.status == null ? null : STATUS_ALIAS[String(a.status).toLowerCase()] ?? null;
  const err = [];
  if (a.status == null) err.push('thiếu --status (1 Nháp | 2 Xuất bản | 3 Chờ duyệt | 4 Đã duyệt) — không có mặc định');
  else if (!spec.status) err.push(`--status "${a.status}" không hợp lệ`);
  // #8/#9: --publish tự đổi trạng thái SAU khi ghi xong — tạo sẵn ở "2 Xuất bản" (nhất là với thân bài
  // tạm) hay "4 Đã duyệt" (không phải trạng thái CLI biết xuất bản từ đâu) không có nghĩa gì ở đây.
  if (a.publish && spec.status && !['1', '3'].includes(spec.status)) {
    err.push('--publish chỉ dùng khi --status là 1 (Nháp) hoặc 3 (Chờ duyệt) — không xuất bản ngầm thân bài tạm');
  }
  if (!spec.title) err.push('title rỗng'); else if (spec.title.length > 70) err.push(`title ${spec.title.length}>70`);
  // CMS chỉ báo lỗi ở bước GHI thân bài: "Url sau khi thêm tên miền + Id đã vượt quá 100 ký tự" — tức
  // len("https://www.thegioididong.com/hoi-dap/") 38 + slug + "-" + newsId 7 số ≤ 100 → slug ≤ 54. Kiểm ngay lúc
  // tạo, vì đổi URL bài đã tạo là việc CLI cấm (giuUrl) nên slug quá dài = phải bỏ bài đã tạo, tạo lại.
  const se = slugError(spec.url, 54); if (se) err.push(se);
  if (!spec.metaTitle) err.push('metaTitle rỗng'); else if (spec.metaTitle.length > 70) err.push(`metaTitle ${spec.metaTitle.length}>70`);
  if (!spec.metaDescription) err.push('metaDescription rỗng'); else if (spec.metaDescription.length > 170) err.push(`metaDescription ${spec.metaDescription.length}>170`);
  if (!spec.keywords.length || spec.keywords.length > 5) err.push(`keywords phải 1–5 từ (đang ${spec.keywords.length})`);
  if (spec.keywords.some((k) => /[,<>"]/.test(k))) err.push('keyword không được chứa , < > "');
  if (!spec.childCategories.length) err.push('childCategories rỗng — chuyên mục con bắt buộc');
  if ([...spec.childCategories, ...spec.parentCategories].some((c) => !/^\d+$/.test(c))) err.push('id chuyên mục phải là số');
  if (spec.thumbnail && spec.thumbnailUrl) err.push('chỉ dùng 1 trong thumbnail (file) / thumbnailUrl');
  if (spec.thumbnail) {
    if (!fs.existsSync(spec.thumbnail)) err.push(`thumbnail không tồn tại: ${spec.thumbnail}`);
    else if (!/\.(jpe?g|png|gif)$/i.test(spec.thumbnail)) err.push('thumbnail phải jpg/png/gif');
    else if (fs.statSync(spec.thumbnail).size > 10485760) err.push('thumbnail >10MB');
  }
  if (spec.thumbnailUrl && !/^https:\/\/cdnv2\.tgdd\.vn\//.test(spec.thumbnailUrl)) err.push('thumbnailUrl phải là URL cdnv2.tgdd.vn');
  spec.html = null;
  if (spec.htmlPath) {
    if (!fs.existsSync(spec.htmlPath)) err.push(`html không tồn tại: ${spec.htmlPath}`);
    else {
      spec.html = fs.readFileSync(spec.htmlPath, 'utf8');
      if (/<img\b[^>]*?\bsrc=["'](?!https?:)/i.test(spec.html)) err.push('html tạo bài còn ảnh local — tạo bằng thân bài tạm rồi để --step all upload + ghi');
    }
  }
  if (err.length) throw new CliError(`field tạo bài không đạt:\n  - ${err.join('\n  - ')}`, 2);
  return spec;
}

const pageFields = (s) => ({
  title: s.title, url: s.url, metaTitle: s.metaTitle, metaDescription: s.metaDescription, keywords: s.keywords,
  articleType: s.articleType, childCategories: s.childCategories, parentCategories: s.parentCategories,
  status: s.status, thumbnailUrl: s.thumbnailUrl || '', html: s.html,
});

/** Trả { code, newsId, liveUrl }. Chỉ --live mới POST; mọi thứ trước đó là đọc. */
export async function stepCreate(ctx, { allowFieldFlags = true } = {}) {
  const { a, client, log, runner, timeoutMs, W } = ctx;
  const spec = readCreateSpec(a, { allowFieldFlags });
  const ledgerFile = repoLedgerPath(W, 'hoidap');
  const key = `hoidap:${spec.url}`;
  // Kiểm sớm (fail nhanh trước khi mở trình duyệt) — cửa chính chặn race là ledgerClaim ngay trước POST.
  const prior = readLedger(ledgerFile).find((r) => r.key === key);
  if (prior) {
    throw new CliError(prior.newsId
      ? `url "${spec.url}" đã tạo newsId=${prior.newsId} (sổ ${ledgerFile}) — không tạo lần 2. Chạy tiếp bằng --news-id ${prior.newsId}.`
      : `sổ ${ledgerFile} có dòng ${prior.status} cho url "${spec.url}" — lần trước có thể đã tạo bài mà không nhận được newsId. Kiểm danh sách bài Hỏi Đáp trên CMS trước; xoá dòng đó bằng tay nếu chắc chắn chưa tạo.`);
  }
  log(`Tạo bài Hỏi Đáp: "${spec.title}" · url=${spec.url} · trạng thái ${spec.status} (${STATUS_LABEL[spec.status]}) · thân bài ${spec.html ? 'từ file' : 'TẠM (1 đoạn) — ghi thân thật bằng --step write/all'}`);
  if (spec.status === '2' && !spec.html) log('CẢNH BÁO: Xuất bản với thân bài tạm → trang live hiện bài 1 đoạn cho tới khi bước ghi chạy xong.');

  await ctx.bind(0);
  const p = await evaluate(client, `() => ({ id: document.getElementById('hdNewsId')?.value ?? null, body: !!document.getElementById('content_FaqNews') })`, 30000);
  if (!p.body || String(p.id) !== '0') throw new CliError(`tab không phải trang tạo mới Hỏi Đáp (hdNewsId=${p.id}) — chưa đăng nhập hoặc sai trang, dừng`);

  const call = (dryRun, thumb) => withRunner(runner, `return await window.hdCreateArticle(${J({ fields: pageFields(spec), thumbInputId: thumb ? THUMB_INPUT : null, dryRun })});`);
  const stamp = runStamp();
  const dir = path.join(W, 'data/raw/cms-create');
  const dry = await evaluate(client, call(true, !!spec.thumbnail), timeoutMs);
  writeVerified(path.join(dir, `create-dry-hoidap-${spec.url}-${stamp}.json`), JSON.stringify({ ...dry, _spec: { ...spec, html: spec.html ? `(${spec.html.length} ký tự)` : null } }, null, 1));
  const P = dry.payload || {};
  log(formatTable([
    ['txtTitle', P.txtTitle], ['txtUrl', P.txtUrl], ['txtMetaTitle', P.txtMetaTitle], ['txtMetaDescription', P.txtMetaDescription],
    ['hdListKeyword', P.hdListKeyword], ['cboArticleType', P.cboArticleType], ['cboStatus', P.cboStatus],
    ['LstChildCategory', P.LstChildCategory], ['LstParentCategory', `${P.LstParentCategory ?? ''} (trang gợi ý: ${(dry.parentOpts || []).join(' ') || '-'})`],
    ['thumbnail', spec.thumbnail ? `file ${path.basename(spec.thumbnail)} (PostImage lúc --live)` : (P.thumbnailNews || '(không)')],
    ['ContentNews', `${dry.bodyLen ?? '?'} ký tự${dry.placeholderBody ? ' (tạm)' : ''}`],
  ].map(([field, value]) => ({ field, value })), ['field', 'value']));
  ctx.report.createDry = dry;
  if (dry.status !== 'DRY') { log(`ABORT tạo bài — bất biến fail: ${J(dry.failed || [])} ${dry.reason || ''} ${dry.childBad?.length ? 'chuyên mục con lạ: ' + dry.childBad : ''}`); return { code: 1 }; }
  if (!a.live) { log(`Dry tạo bài đạt (payload ${Object.keys(P).length} key → ${dir}). Chạy lại với --live để tạo thật.`); return { code: 0 }; }

  // --- live: thumbnail (nếu có) → claim (kiểm trùng + ghi PENDING atomic, 1 khoá) → POST tạo → đọc lại ---
  try {
    if (spec.thumbnail) await uploadToOwnInput(client, THUMB_INPUT, [spec.thumbnail]);
    const claim = ledgerClaim(ledgerFile, key, { status: 'PENDING', url: spec.url, title: spec.title, createdStatus: spec.status });
    if (claim.prior) {
      const p = claim.prior;
      throw new CliError(p.newsId
        ? `url "${spec.url}" đã tạo newsId=${p.newsId} (sổ ${ledgerFile}) — không tạo lần 2. Chạy tiếp bằng --news-id ${p.newsId}.`
        : `sổ ${ledgerFile} có dòng ${p.status} cho url "${spec.url}" — lần trước có thể đã tạo bài mà không nhận được newsId. Kiểm danh sách bài Hỏi Đáp trên CMS trước; xoá dòng đó bằng tay nếu chắc chắn chưa tạo.`);
    }
    let out;
    try {
      out = await evaluate(client, call(false, !!spec.thumbnail), timeoutMs);
    } catch (err) {
      if (!(err instanceof TimeoutError)) throw err;
      ctx.keepTab = true;
      log(`TIMEOUT khi tạo bài — KHÔNG rõ đã tạo chưa. Sổ giữ PENDING để chặn tạo trùng. Kiểm CMS (tìm url "${spec.url}").`);
      return { code: 1 };
    }
    writeVerified(path.join(dir, `create-run-hoidap-${spec.url}-${stamp}.json`), JSON.stringify(out, null, 1));
    ctx.report.create = out;
    if (!out.newsId) {
      // Thumbnail lỗi = chưa POST tạo bài → gỡ dòng PENDING. Submit lỗi không có id → giữ chặn (FAIL_NO_ID) cho người kiểm.
      if (out.stage === 'thumbnail') ledgerRemove(ledgerFile, key);
      else ledgerUpsert(ledgerFile, { key, status: 'FAIL_NO_ID', url: spec.url, createdStatus: spec.status, reply: out.cmsReply ?? null });
      log(`Tạo bài không đạt (${out.stage}): ${J(out.cmsReply ?? out.thumb ?? out.reason)}`);
      return { code: 1 };
    }
    if (out.status === 'UNKNOWN') {
      // #2: POST đã đi (có newsId) nhưng đọc lại lỗi — KHÔNG đoán DONE hay FAIL. Sổ giữ UNKNOWN (không
      // phải PENDING, không phải DONE) để lần sau vẫn bị chặn tạo trùng, và người kiểm biết cần làm gì.
      ledgerUpsert(ledgerFile, { key, status: 'UNKNOWN', newsId: out.newsId, url: spec.url, createdStatus: spec.status, reason: out.reason });
      log(`Tạo bài: POST đã gửi (newsId=${out.newsId}) nhưng đọc lại KHÔNG RÕ (${out.reason}). Sổ ghi UNKNOWN — kiểm tay CMS bài ${out.newsId} trước khi dùng tiếp.`);
      return { code: 1, newsId: out.newsId };
    }
    const slug = out.verify?.urlGot || spec.url;
    const liveUrl = LIVE_URL(slug, out.newsId);
    ledgerUpsert(ledgerFile, { key, status: out.status, newsId: out.newsId, url: slug, liveUrl, createdStatus: spec.status, failedVerify: out.failedVerify, warn: out.warn, ms: out.ms });
    log(`Đã tạo newsId=${out.newsId} (${out.ms}ms) → ${liveUrl}\nđọc lại: ${J(out.verify)}${out.warn?.length ? `\nCẢNH BÁO (không chặn): ${out.warn.join(', ')} đọc lại không khớp` : ''}`);
    if (out.status !== 'DONE') { log(`Đọc lại lệch: ${out.failedVerify.join(', ')} — bài ĐÃ tạo, kiểm tay trước khi ghi tiếp.`); return { code: 1, newsId: out.newsId, liveUrl }; }
    return { code: 0, newsId: out.newsId, liveUrl, createdStatus: spec.status };
  } finally {
    if (spec.thumbnail) { try { await evaluate(client, removeInputFn([THUMB_INPUT]), 15000); } catch { /* tab đóng */ } }
  }
}

/**
 * --step publish [--live] --news-id <id> — đổi bài Hỏi Đáp CLI đã tạo từ Chờ duyệt sang Xuất bản.
 * NGOẠI LỆ DUY NHẤT cho bất biến "giữ nguyên trạng thái": chỉ chạy cho bài NẰM TRONG sổ tạo bài
 * (repoLedgerPath), và chỉ khi sổ ghi createdStatus = '3' (Chờ duyệt) — không tự xuất bản bài Nháp,
 * bài không do CLI này tạo, hay bài sổ đã đánh dấu đã xuất bản trước đó.
 */
export async function stepPublish(ctx) {
  const { a, client, id, log, runner, timeoutMs, W } = ctx;
  const ledgerFile = repoLedgerPath(W, 'hoidap');
  const rows = readLedger(ledgerFile);
  const entry = rows.find((r) => r.newsId === id);
  if (!entry) throw new CliError(`newsId=${id} không có trong sổ ${ledgerFile} — chỉ xuất bản bài do CLI này tạo (không tìm thấy dòng nào có newsId đó)`, 2);
  if (String(entry.createdStatus) !== '3') throw new CliError(`sổ ghi trạng thái lúc tạo = ${entry.createdStatus} (khác 3 Chờ duyệt) — không tự xuất bản bài này`, 2);
  if (entry.published) throw new CliError(`newsId=${id} đã xuất bản lúc ${entry.published} (sổ ${ledgerFile})`, 2);

  await ctx.bind(id);
  await checkPage(client, id);
  const call = (dryRun) => withRunner(runner, `return await window.hdPublishArticle(${J({ newsId: id, expectCurrentStatus: '3', dryRun })});`);
  // Marker in-flight (skill hoidap, bước publish): dry-check dưới đây đọc CMS TƯƠI — đủ để phân
  // loại marker ghi dở còn sót TRƯỚC khi áp kết luận ABORT/DRY thường (khác #3 shared: ở đây
  // dry-check tự nhiên trả ABORT với currentStatus khi trạng thái đã đổi, không cần đọc thêm).
  const idir = inflightDir(W, 'cms-backup');
  const markerKey = `hd-publish-${id}`;
  const marker = readInflightMarker(idir, markerKey);
  const dry = await evaluate(client, call(true), timeoutMs);
  ctx.report.publishDry = dry;
  if (marker) {
    if (dry.status === 'ABORT' && dry.currentStatus === '2') {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — bài đã Xuất bản (currentStatus=2) -> DONE_RECOVERED, không đổi lại.`);
      clearInflightMarker(idir, markerKey);
      ledgerUpsert(ledgerFile, { ...entry, published: new Date().toISOString(), recovered: 'DONE_RECOVERED' });
      log(`Đã xuất bản newsId=${id} (phục hồi từ marker) — trạng thái Xuất bản.`);
      return 0;
    }
    if (dry.status === 'DRY') {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — bài vẫn Chờ duyệt -> SAFE_PROCEED, xuất bản lại bình thường.`);
      clearInflightMarker(idir, markerKey);
    } else {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — trạng thái hiện tại không rõ ràng (${dry.status} ${dry.reason || ''}) -> NEEDS_MANUAL_CHECK, GIỮ marker, kiểm tay bài ${id} trước khi chạy lại.`);
      return 1;
    }
  }
  if (dry.status !== 'DRY') { log(`ABORT xuất bản — bất biến fail: ${J(dry.failed || [])} ${dry.reason || ''}`); return 1; }
  if (!a.live) { log('Dry xuất bản đạt (bài đang Chờ duyệt, mọi field khác giữ nguyên). Chạy lại với --live để đổi trạng thái thật.'); return 0; }

  // Marker NGAY TRƯỚC evaluate đổi trạng thái thật.
  writeInflightMarker(idir, { key: markerKey, row: { step: 'publish', intendedStatus: '2' }, beforeSha: sha256('3') });
  let out;
  try {
    out = await evaluate(client, call(false), timeoutMs);
  } catch (err) {
    // UNKNOWN: timeout/lỗi có thể xảy ra SAU khi POST đã gửi — giữ marker, không đoán.
    ctx.keepTab = true;
    log(`${err instanceof TimeoutError ? 'TIMEOUT' : 'LỖI'} khi xuất bản — KHÔNG rõ đã đổi trạng thái chưa (UNKNOWN). Kiểm CMS bài ${id} trước khi chạy lại. Marker in-flight giữ nguyên.`);
    return 1;
  }
  const stamp = runStamp();
  writeVerified(path.join(W, 'data/raw/cms-backup', `publish-${id}-${stamp}.json`), JSON.stringify(out, null, 1));
  ctx.report.publish = out;
  if (out.status === 'UNKNOWN') {
    log(`Xuất bản: đã POST nhưng đọc lại KHÔNG RÕ (${out.reason}). Marker in-flight GIỮ NGUYÊN, sổ giữ nguyên (chưa đánh dấu published) — kiểm tay CMS bài ${id} trước khi làm tiếp.`);
    return 1;
  }
  // Kết quả dứt khoát (DONE/FAIL/ABORT) — xoá marker.
  clearInflightMarker(idir, markerKey);
  if (out.status !== 'DONE') { log(`Xuất bản không đạt: ${J(out.verify || out.reason)}`); return 1; }
  ledgerUpsert(ledgerFile, { ...entry, published: new Date().toISOString(), publishMs: out.ms });
  log(`Đã xuất bản newsId=${id} (${out.ms}ms) — trạng thái Xuất bản, thân bài/chuyên mục/field khác giữ nguyên.`);
  return 0;
}

/**
 * Kế hoạch ảnh (chỉ đọc): HEAD từng tên trên CDN; tên đã có phải trùng byte (dùng lại), lệch = xung đột.
 * URL của ảnh chưa up được DỰ ĐOÁN = base + tên (UploadManyImages giữ nguyên tên, thư mục News/{id}/).
 */
async function planForAll(ctx, srcHtml, imagesDir) {
  const { id, log, deps } = ctx;
  const files = imagesToUpload(srcHtml, imagesDir, { localOnly: true });
  const base = CDN_NEWS_BASE(id);
  const plan = await planImageUploads(base, files, deps.fetchFn || fetch);
  ctx.report.upload = { total: files.length, reuse: Object.keys(plan.reuse).length, upload: plan.upload.length, conflicts: plan.conflicts, errors: plan.errors };
  log(`Ảnh: ${files.length} tham chiếu · ${Object.keys(plan.reuse).length} đã có trên CDN (trùng byte, dùng lại) · ${plan.upload.length} cần upload`);
  const map = { ...plan.reuse };
  const pendingUrls = new Set();
  for (const f of plan.upload) { const u = base + encodeURIComponent(path.basename(f)); map[path.basename(f)] = u; pendingUrls.add(u); }
  return { plan, map, pendingUrls, ok: !plan.conflicts.length && !plan.errors.length };
}

/** Upload đúng các file 404 của kế hoạch, lưu map, so byte. Trả { code, uploaded }. */
async function uploadPending(ctx, plan, imagesDir) {
  const { client, id, log, deps, runner, timeoutMs, P } = ctx;
  await ctx.bind(id);
  await checkPage(client, id);
  let out;
  try {
    await uploadToOwnInput(client, IMG_INPUT, plan.upload);
    out = await evaluate(client, withRunner(runner, `return await window.hdUploadImages(${J({ newsId: id, inputId: IMG_INPUT, dryRun: false })});`), timeoutMs);
  } catch (err) {
    if (!(err instanceof TimeoutError)) throw err;
    ctx.keepTab = true;
    log('TIMEOUT khi upload — KHÔNG rõ ảnh đã lên chưa. Chạy lại --step all: ảnh đã lên + trùng byte sẽ được dùng lại.');
    return { code: 1 };
  } finally {
    try { await evaluate(client, removeInputFn([IMG_INPUT]), 15000); } catch { /* tab đóng */ }
  }
  const prev = fs.existsSync(P.uploadJson) ? JSON.parse(fs.readFileSync(P.uploadJson, 'utf8')) : {};
  writeVerified(P.uploadJson, JSON.stringify({ ...out, uploaded: { ...(prev.uploaded || {}), ...plan.reuse, ...(out.uploaded || {}) } }, null, 1));
  if (out.status !== 'DONE' || (out.wrongFolder || []).length) { log(`Upload chưa đạt: ${J({ status: out.status, missing: out.missing, wrongFolder: out.wrongFolder, reason: out.reason || out.error })}`); return { code: 1 }; }
  const bytes = await verifyCdnBytes(out.uploaded, imagesDir, deps.fetchFn || fetch);
  if (!bytes.ok) { log(`Ảnh CDN lệch file local: ${bytes.bad.join('; ')}`); return { code: 1 }; }
  ctx.report.upload.uploadedMs = out.ms;
  return { code: 0, uploaded: out.uploaded };
}

/** Dry ghi qua stepWrite (lưu dry json + backup split). tolerate = tập URL ảnh chưa upload được phép "chết". */
async function writeDry(ctx, htmlPath, tolerate) {
  const { a } = ctx;
  const live = a.live;
  a.html = htmlPath;
  a.live = false;
  ctx.pendingUrls = tolerate;
  try { return await stepWrite(ctx); } finally { a.live = live; ctx.pendingUrls = null; }
}

/** --step all. Trả exit code; luôn in bảng tóm tắt + tổng thời gian. */
export async function stepAll(ctx) {
  const { a, log, W } = ctx;
  const t0 = Date.now();
  const rows = [];
  const add = (step, status, detail) => rows.push({ step, status, detail: detail ?? '' });
  const done = (code) => {
    log(`\n${formatTable(rows, ['step', 'status', 'detail'])}\n\n${a.live ? 'LIVE' : 'DRY'} --step all: ${code === 0 ? 'ĐẠT' : 'KHÔNG ĐẠT'} · tổng ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    return code;
  };
  if (a['expect-images'] != null && !Number.isInteger(Number(a['expect-images']))) throw new CliError('--expect-images phải là số nguyên', 2);

  // 0. HTML nguồn: --html, hoặc workspace/source/final-content.html. Có ảnh local thì cần --workspace.
  if (!a.html && !a.workspace) throw new CliError('--step all cần --workspace (có source/ + images-processed/) hoặc --html', 2);
  const srcPath = path.resolve(a.html || path.join(a.workspace, 'source/final-content.html'));
  if (!fs.existsSync(srcPath)) throw new CliError(`không thấy HTML nguồn ${srcPath}`, 2);
  const src = fs.readFileSync(srcPath, 'utf8');
  const hasLocal = /<img\b[^>]*?\bsrc=["'](?!https?:)/i.test(src);
  if (hasLocal && !a.workspace) throw new CliError('HTML có ảnh local nhưng thiếu --workspace (images-processed/)', 2);
  const imagesDir = a.workspace ? path.resolve(a.workspace, 'images-processed') : null;
  if (hasLocal) imagesToUpload(src, imagesDir, { localOnly: true }); // thiếu file local → ném lỗi trước khi mở trình duyệt

  // 1. Tạo bài (nếu --create-file) — bất biến của create chặn trước POST tạo.
  let createdStatus = null;
  if (a['create-file']) {
    const c = await stepCreate(ctx, { allowFieldFlags: false });
    add('create', c.code === 0 ? (a.live ? 'DONE' : 'DRY') : 'FAIL', c.newsId ? `newsId=${c.newsId} · ${c.liveUrl}` : (ctx.report.createDry?.failed || []).join(',') || 'payload đạt');
    if (c.code !== 0) return done(1);
    if (!a.live) { add('upload/write', 'SKIP', 'dry dừng sau create — upload/ghi cần newsId thật'); return done(0); }
    ctx.id = c.newsId;
    ctx.P = paths(W, c.newsId);
    if (!a['live-url']) a['live-url'] = c.liveUrl;
    createdStatus = c.createdStatus;
    // #9: bài chưa Xuất bản (tạo ở 1/3) mà không --publish thì trang live nhiều khả năng chưa có gì —
    // hoãn nghiệm thu (LIVE_SKIPPED_UNPUBLISHED), không phải lỗi ghi. Có --publish thì hoãn tới sau publish (#9 + đơn giản hoá bằng deferLiveVerify).
    if (createdStatus !== '2') ctx.deferLiveVerify = true;
    if (createdStatus !== '2' && !a.publish) ctx.liveSkipUnpublished = true;
  }
  const { id, P } = ctx;

  // 2. Kế hoạch ảnh (đọc) → HTML với URL dự đoán → PRE-DRY ghi: mọi bất biến trừ "ảnh sống" của ảnh chưa up.
  //    Fail ở đây = dừng TRƯỚC upload (upload là POST không đảo ngược).
  let cmsHtmlPath = srcPath;
  let planned = null;
  if (hasLocal) {
    planned = await planForAll(ctx, src, imagesDir);
    const u = ctx.report.upload;
    if (!planned.ok) {
      add('plan ảnh', 'FAIL', [...u.conflicts, ...u.errors].join(' | '));
      return done(1);
    }
    add('plan ảnh', 'OK', `${u.reuse} dùng lại (trùng byte) · ${u.upload} cần up`);
    const rep = replaceImageSrcs(src, planned.map);
    if (/<img\b[^>]*?\bsrc=["'](?!https?:)/i.test(rep.html)) { add('replace', 'FAIL', 'còn src local sau khi thay'); return done(1); }
    writeVerified(P.cmsHtml, rep.html);
    cmsHtmlPath = P.cmsHtml;
    add('replace', 'DONE', `${rep.replaced} src → ${path.basename(P.cmsHtml)}`);
  } else add('plan ảnh', 'SKIP', 'HTML không có ảnh local');

  const pre = await writeDry(ctx, cmsHtmlPath, planned?.pendingUrls);
  const wd = ctx.report.writeDry || {};
  const ph = planned?.pendingUrls?.size ? ` (chờ up ${planned.pendingUrls.size} ảnh)` : '';
  add('write dry', pre === 0 ? 'DRY' : 'ABORT', pre === 0 ? `${wd.willWrite?.len ?? '?'} ký tự, ${wd.willWrite?.imgs ?? '?'} ảnh${ph} · backup ${path.relative(W, P.splitDir)}` : (wd.failed || []).join(',') || wd.reason || '');
  if (pre !== 0) return done(1);
  if (!a.live) return done(0);

  // 3. Upload ảnh 404 → so byte → URL trả về phải đúng URL dự đoán; rồi dry lại KHÔNG tha gì.
  if (planned?.plan.upload.length) {
    const up = await uploadPending(ctx, planned.plan, imagesDir);
    add('upload', up.code === 0 ? 'DONE' : 'FAIL', up.code === 0 ? `${Object.keys(up.uploaded).length} ảnh, khớp byte` : 'xem log');
    if (up.code !== 0) return done(1);
    const drift = Object.entries(up.uploaded).filter(([n, url]) => planned.map[n] !== url);
    if (drift.length) {
      const rep = replaceImageSrcs(src, { ...planned.map, ...up.uploaded });
      writeVerified(P.cmsHtml, rep.html);
      log(`URL CDN trả về khác dự đoán ở ${drift.length} ảnh — đã thay lại theo URL thật.`);
    }
    const again = await writeDry(ctx, cmsHtmlPath, null);
    add('write dry 2', again === 0 ? 'DRY' : 'ABORT', again === 0 ? 'ảnh đã sống, bất biến đạt' : (ctx.report.writeDry?.failed || []).join(','));
    if (again !== 0) return done(1);
  }

  // 4. Ghi thật → verify server → đợi 60s → clearcache → nghiệm thu live (stepWrite làm hết).
  if (!a['live-url'] && !a['skip-live-verify']) {
    const slug = String(ctx.report.writeDry?.backup?.fields?.txtUrl || '').trim();
    if (!slug) { add('write live', 'FAIL', 'không suy được URL live từ backup — truyền --live-url'); return done(1); }
    a['live-url'] = LIVE_URL(slug, id);
  }
  a.html = cmsHtmlPath;
  const code = await stepWrite(ctx);
  const w = ctx.report.write;
  const wOk = w?.status === 'DONE' || w?.status === 'ALREADY';
  add('write live', w?.status || 'FAIL', w ? `${w.ms ?? '?'}ms · server verify ${wOk ? (w.status === 'ALREADY' ? 'đã khớp từ trước' : 'khớp') : 'LỆCH'}` : 'không ghi (xem log)');
  if (code !== 0 && !ctx.deferLiveVerify) { const lv0 = ctx.report.live; if (lv0) add('live verify', lv0.pass ? 'PASS' : 'FAIL', `${a['live-url']} · heading ${lv0.headings ?? '?'} · ảnh ${lv0.images ?? '?'}${lv0.oldHeadingsStillLive?.length ? ' · heading cũ còn ' + lv0.oldHeadingsStillLive.length : ''}`); return done(code); }
  if (code !== 0) return done(code);

  // --publish (owner 24/09/2026): ghi xong + verify server đạt RỒI mới đổi Chờ duyệt -> Xuất bản.
  // Đây là bước RIÊNG, tường minh — không gộp vào hdWriteArticle (đó là ngoại lệ duy nhất cho giuTrangThai).
  if (a.publish && createdStatus && createdStatus !== '2') {
    const pubCode = await stepPublish(ctx);
    const pub = ctx.report.publish || ctx.report.publishDry;
    add('publish', pubCode === 0 ? (a.live ? 'DONE' : 'DRY') : (pub?.status || 'FAIL'), pub ? J(pub.verify || pub.reason || pub.checks) : '');
    if (pubCode !== 0) return done(1);
  }

  // Nghiệm thu live: hoãn ở stepWrite (ctx.deferLiveVerify) cho tới đây — chỉ chạy khi bài thật sự đã
  // live (status 2 ngay từ đầu, hoặc vừa --publish xong). #9: bỏ hẳn nếu vẫn chưa Xuất bản.
  if (ctx.deferLiveVerify) {
    if (a['skip-live-verify']) { add('live verify', 'SKIP', '--skip-live-verify'); return done(0); }
    if (ctx.liveSkipUnpublished) { add('live verify', 'SKIP', 'LIVE_SKIPPED_UNPUBLISHED (bài chưa Xuất bản, không có --publish)'); return done(0); }
    const lvCode = await runLiveVerify(ctx, ctx._deferredLiveArgs);
    const lv = ctx.report.live;
    add('live verify', lv?.pass ? 'PASS' : 'FAIL', `${a['live-url']} · heading ${lv?.headings ?? '?'} · ảnh ${lv?.images ?? '?'}${lv?.oldHeadingsStillLive?.length ? ' · heading cũ còn ' + lv.oldHeadingsStillLive.length : ''}`);
    return done(lvCode);
  }
  const lv = ctx.report.live;
  if (a['skip-live-verify']) add('live verify', 'SKIP', '--skip-live-verify');
  else if (lv) add('live verify', lv.pass ? 'PASS' : 'FAIL', `${a['live-url']} · heading ${lv.headings ?? '?'} · ảnh ${lv.images ?? '?'}${lv.oldHeadingsStillLive?.length ? ' · heading cũ còn ' + lv.oldHeadingsStillLive.length : ''}`);
  return done(code);
}
