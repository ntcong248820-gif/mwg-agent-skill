#!/usr/bin/env node
/**
 * run-air-hoidap-cli.mjs — air bài Hỏi Đáp lên CMS Faq bằng 1 lệnh cho mỗi cổng duyệt.
 *
 * Bọc NGOÀI air-hoidap-runner.js / hoidap-body-tools.mjs / verify-hoidap-live.mjs (không sửa
 * chúng). Hai cổng user giữ nguyên, mỗi cổng = 1 lệnh dry rồi 1 lệnh --live:
 *
 *   --step upload           kiểm tên ảnh trên CDN (hdUploadImages dryRun)
 *   --step upload --live    upload (upload_file vào input TỰ TẠO, không chạm input của trang)
 *                           → lưu map → GET từng ảnh so byte với file local → thay src (replace)
 *   --step write            dry ghi → lưu dry-{id}.json → split-backup → diff cho user duyệt
 *   --step write --live     đòi dry-{id}.json đã duyệt (cùng HTML, cùng set) → dry lại → thân bài
 *                           phải trùng bản đã duyệt → backup pre-live lên đĩa, kiểm → guard hash
 *                           → ghi → verify server (runner) → đợi ~60s → clearcache → nghiệm thu
 *                           live (verify-hoidap-live.mjs), fail thì đợi 60s thử lại 1 lần.
 *
 *   --step create [--live]  tạo bài mới (newsId=0) — xem hoidap-create-and-all-steps.mjs
 *   --step all [--live]     không người trông: [create] → upload (idempotent theo byte) → thay src → dry +
 *                           bất biến → backup → ghi → verify server → 60s → clearcache → nghiệm thu live
 *   --profile mặc định <faq>.
 *
 *   node run-air-hoidap-cli.mjs --profile <faq> --task-dir tasks/<task> --news-id 1576257 \
 *     --workspace mwg-content-editor/content-workspaces/<slug> --step upload [--live]
 *   node run-air-hoidap-cli.mjs --profile <faq> --task-dir tasks/<task> --news-id 1576257 \
 *     --step write [--title ".."] [--meta-title ".."] [--meta-description ".."] [--expect-images N] \
 *     [--live --live-url https://www.thegioididong.com/hoi-dap/<slug>-1576257]
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import {
  CMS_ORIGIN, CliError, McpClient, PAGE_SHA256, TimeoutError, evaluate, openAndBind, removeInputFn, uploadToOwnInput, withRunner,
} from './cms-cli-mcp.mjs';
import {
  appendJsonl, clearInflightMarker, formatTable, inflightDir, parseArgs, readInflightMarker, requireTaskDir, runStamp, sha256, writeInflightMarker, writeVerified,
} from './cms-cli-pipeline.mjs';
import { imagesToUpload, runNode, verifyCdnBytes, waitThenVerify } from './cms-cli-air.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const RUNNER = path.join(HERE, 'air-hoidap-runner.js');
const TOOLS = path.join(HERE, 'hoidap-body-tools.mjs');
const VERIFY_LIVE = path.join(HERE, 'verify-hoidap-live.mjs');
const INPUT_ID = 'claudeHdImages';
export const DEFAULT_PROFILE = '<faq>';
const J = (v) => JSON.stringify(v);

export function paths(W, id) {
  const cb = path.join(W, 'data/raw/cms-backup');
  return {
    uploadJson: path.join(W, `data/raw/cms-upload-${id}.json`),
    cmsHtml: path.join(W, `data/processed/final-content-cms-${id}.html`),
    backupRoot: cb,
    dryJson: path.join(cb, `dry-${id}.json`),
    splitDir: path.join(cb, String(id)),
  };
}

const nonEmpty = (f) => { try { return fs.statSync(f).size > 0; } catch { return false; } };

export async function checkPage(client, newsId) {
  const p = await evaluate(client, `() => ({ id: document.getElementById('hdNewsId')?.value ?? null, body: !!document.getElementById('content_FaqNews') })`, 30000);
  if (!p.body) throw new CliError('tab không có #content_FaqNews — chưa đăng nhập hoặc sai trang, dừng');
  if (String(p.id) !== String(newsId)) throw new CliError(`tab đang mở newsId=${p.id}, tham số ${newsId} — dừng`);
}

async function stepUpload(ctx) {
  const { a, client, id, P, log, deps, runner, timeoutMs } = ctx;
  if (!a.workspace) throw new CliError('--step upload cần --workspace (content workspace có source/ và images-processed/)', 2);
  const srcHtml = path.resolve(a.html || path.join(a.workspace, 'source/final-content.html'));
  const imagesDir = path.resolve(a.workspace, 'images-processed');
  const files = imagesToUpload(fs.readFileSync(srcHtml, 'utf8'), imagesDir, { localOnly: true });
  if (a.live && fs.existsSync(P.uploadJson)) {
    throw new CliError(`${P.uploadJson} đã có — ảnh đã upload trước đó. CDN không xoá được; không upload lại. Xoá tay file map nếu chắc chắn cần.`);
  }
  log(`${files.length} ảnh HTML tham chiếu: ${files.map((f) => path.basename(f)).join(', ') || '(không có)'}`);
  await ctx.bind(id);
  await checkPage(client, id);

  let out = { status: a.live ? 'DONE' : 'DRY', uploaded: {}, missing: [], taken: [], wrongFolder: [] };
  if (files.length) {
    try {
      await uploadToOwnInput(client, INPUT_ID, files);
      out = await evaluate(client, withRunner(runner, `return await window.hdUploadImages(${J({ newsId: id, inputId: INPUT_ID, dryRun: !a.live })});`), timeoutMs);
    } catch (err) {
      if (!(err instanceof TimeoutError)) throw err;
      ctx.keepTab = true;
      log(`TIMEOUT khi upload — KHÔNG rõ ảnh đã lên chưa. HEAD từng file trên CDN trước khi chạy lại.`);
      return 1;
    } finally {
      try { await evaluate(client, removeInputFn([INPUT_ID]), 15000); } catch { /* tab đóng / timeout */ }
    }
  }
  if (!a.live) {
    log(formatTable(Object.entries(out.cdnHead || {}).map(([file, head]) => ({ file, head, free: head === 404 ? 'trống' : head === 200 ? 'ĐÃ CÓ' : '?' })), ['file', 'head', 'free']));
    const ok = out.status === 'DRY' && !(out.taken || []).length;
    log(ok ? 'Tên ảnh đều trống. Xin user xác nhận rồi chạy lại với --live để upload.' : `Không upload được: ${out.reason || 'tên đã có trên CDN: ' + (out.taken || []).join(', ')}`);
    return ok ? 0 : 1;
  }
  writeVerified(P.uploadJson, JSON.stringify(out, null, 1));
  log(`Kết quả upload → ${P.uploadJson}: ${out.status}`);
  if (out.status !== 'DONE' || (out.wrongFolder || []).length) {
    log(`Upload chưa đạt: missing=${J(out.missing || [])} wrongFolder=${J(out.wrongFolder || [])} ${out.reason || out.error || ''}`);
    return 1;
  }
  const bytes = await verifyCdnBytes(out.uploaded, imagesDir, deps.fetchFn || fetch);
  if (!bytes.ok) { log(`Ảnh trên CDN lệch file local: ${bytes.bad.join('; ')}`); return 1; }
  log(`CDN khớp byte ${Object.keys(out.uploaded).length}/${files.length} ảnh.`);
  fs.mkdirSync(path.dirname(P.cmsHtml), { recursive: true }); // replace của hoidap-body-tools không tự tạo thư mục
  const r = await runNode(TOOLS, ['replace', '--html', srcHtml, '--map', P.uploadJson, '--out', P.cmsHtml], deps.nodeExecFn);
  log(r.stdout || r.stderr);
  if (r.code !== 0) return 1;
  log(`Xong upload. Tiếp: --step write (dry) để lấy diff cho user duyệt.`);
  return 0;
}

export async function stepWrite(ctx) {
  const { a, client, id, P, log, deps, runner, timeoutMs, W } = ctx;
  const htmlPath = path.resolve(a.html || P.cmsHtml);
  if (!nonEmpty(htmlPath)) throw new CliError(`không thấy HTML bản CMS ${htmlPath} — chạy --step upload --live trước hoặc truyền --html`, 2);
  const body = fs.readFileSync(htmlPath, 'utf8');
  const set = {};
  if (a.title) set.title = a.title;
  if (a['meta-title']) set.metaTitle = a['meta-title'];
  if (a['meta-description']) set.metaDescription = a['meta-description'];
  const expectImages = a['expect-images'] != null ? Number(a['expect-images']) : null;
  const cli = { htmlSha256: sha256(body), htmlPath, set, expectImages };
  const dryCode = withRunner(runner, `return await window.hdWriteArticle(${J({ newsId: id, html: body, set, expectImages, dryRun: true })});`);

  if (!a.live) {
    await ctx.bind(id);
    await checkPage(client, id);
    const out = await evaluate(client, dryCode, timeoutMs);
    writeVerified(P.dryJson, JSON.stringify({ ...out, _cli: cli }, null, 1));
    const split = await runNode(TOOLS, ['split-backup', '--json', P.dryJson, '--dir', P.splitDir], deps.nodeExecFn);
    if (split.code !== 0) { log(split.stderr); return 1; }
    const diff = await runNode(TOOLS, ['diff', '--before', path.join(P.splitDir, 'before.html'), '--after', htmlPath], deps.nodeExecFn);
    log(`Backup: ${P.splitDir} (before.html / page.html / fields.json)\nDiff cho user duyệt:\n${diff.stdout}`);
    log(`checks: ${J(out.checks || {})}\nchanges: ${J(out.changes || {})}`);
    ctx.report.writeDry = out;
    // --step all dry: ảnh chưa upload (URL dự đoán) thì anhSongHet fail là đúng dự kiến — chỉ tha đúng các URL đó.
    const pendingOnly = out.status === 'ABORT' && J(out.failed) === J(['anhSongHet']) && ctx.pendingUrls?.size
      && (out.deadImg || []).every((d) => ctx.pendingUrls.has(d.replace(/^\S+ /, '')));
    if (pendingOnly) { log(`Dry đạt trừ ${out.deadImg.length} ảnh chưa upload (đúng dự kiến — chỉ lên CDN ở --live).`); return 0; }
    if (out.status !== 'DRY') { log(`ABORT — bất biến fail: ${J(out.failed || [])} ${out.reason || ''}. Sửa nguồn, không ép ghi.`); return 1; }
    log('Dry đạt. Đưa diff cho user duyệt rồi chạy lại cùng lệnh với --live --live-url <URL live>.');
    return 0;
  }

  // --- live ---
  if (!a['live-url'] && !a['skip-live-verify']) throw new CliError('--live cần --live-url để nghiệm thu trang live (hoặc --skip-live-verify nếu cố ý bỏ)', 2);
  if (!nonEmpty(P.dryJson)) throw new CliError(`chưa có ${P.dryJson} — chạy --step write không --live để user duyệt diff trước`, 2);
  const approved = JSON.parse(fs.readFileSync(P.dryJson, 'utf8'));
  if (approved.status !== 'DRY') throw new CliError('dry đã lưu không đạt (status khác DRY) — không ghi', 1);
  if (approved._cli?.htmlSha256 !== cli.htmlSha256 || J(approved._cli?.set) !== J(set) || approved._cli?.expectImages !== expectImages) {
    throw new CliError('HTML / set / expect-images khác bản dry user đã duyệt — chạy lại dry để duyệt diff mới', 1);
  }
  await ctx.bind(id);
  await checkPage(client, id);
  const fresh = await evaluate(client, dryCode, timeoutMs);
  if (fresh.status !== 'DRY') { log(`Dry ngay trước khi ghi không đạt: ${J(fresh.failed || [])} ${fresh.reason || ''} — không ghi`); return 1; }
  const dbBody = fresh.backup?.content_FaqNews_DB;
  const currentSha = typeof dbBody === 'string' ? sha256(dbBody) : null;
  const intendedSha = sha256(body);
  // Marker in-flight (skill hoidap, bước write): phục hồi trạng thái ghi dở từ lần chạy trước
  // TRƯỚC khi áp guard "đã đổi kể từ lúc duyệt" — nếu không, guard sẽ báo nhầm "đã đổi" khi
  // thật ra lần ghi trước ĐÃ THÀNH CÔNG (server = intended) chỉ là process bị kill trước khi
  // đọc được kết quả.
  const idir = inflightDir(W, 'cms-backup');
  const markerKey = `hd-write-${id}`;
  const marker = readInflightMarker(idir, markerKey);
  let already = null; // kết quả ALREADY tổng hợp khi phục hồi phát hiện đã ghi xong từ trước
  if (marker) {
    if (currentSha === marker.row?.intendedSha) {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — CMS đã có bản mới (khớp intended sha) -> DONE_RECOVERED, không ghi lại.`);
      clearInflightMarker(idir, markerKey);
      already = { status: 'ALREADY', ms: 0, verify: null };
    } else if (currentSha === marker.beforeSha) {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — CMS vẫn ở bản cũ -> SAFE_PROCEED, ghi lại bình thường.`);
      clearInflightMarker(idir, markerKey);
    } else {
      log(`[recover] marker ghi dở từ ${marker.at} (pid ${marker.pid}) — thân bài hiện tại không khớp intended lẫn before -> NEEDS_MANUAL_CHECK, GIỮ marker, kiểm tay bài ${id} trước khi chạy lại.`);
      return 1;
    }
  }
  if (!already && (typeof dbBody !== 'string' || sha256(dbBody) !== sha256(approved.backup?.content_FaqNews_DB ?? ''))) {
    log('Thân bài trên CMS đã đổi kể từ lúc user duyệt diff — không ghi. Chạy lại dry.');
    return 1;
  }
  const stamp = runStamp();
  const preJson = path.join(P.backupRoot, `pre-live-${id}-${stamp}.json`);
  const preDir = path.join(P.splitDir, `pre-live-${stamp}`);
  writeVerified(preJson, JSON.stringify({ ...fresh, _cli: cli }, null, 1));
  const split = await runNode(TOOLS, ['split-backup', '--json', preJson, '--dir', preDir], deps.nodeExecFn);
  const need = ['before.html', 'page.html', 'fields.json'].map((f) => path.join(preDir, f));
  if (split.code !== 0 || !need.every(nonEmpty)) { log(`Backup pre-live thiếu (${need.filter((f) => !nonEmpty(f)).join(', ')}) — KHÔNG ghi`); return 1; }
  log(`Backup pre-live: ${preDir}`);

  let out;
  if (already) {
    out = already;
  } else {
    // Marker NGAY TRƯỚC evaluate ghi thật — nếu tiến trình bị kill giữa chừng, lần chạy sau
    // đọc được dấu vết này để phục hồi thay vì đoán mò.
    writeInflightMarker(idir, { key: markerKey, row: { step: 'write', intendedSha }, beforeSha: currentSha });
    const liveCode = withRunner(runner, `${PAGE_SHA256}
const __raw = await fetch('/v2/Faq/NewsEdit?newsId=${id}&_=' + Date.now(), { credentials: 'same-origin' }).then((r) => r.text());
const __cur = new DOMParser().parseFromString(__raw, 'text/html').getElementById('content_FaqNews');
if (!__cur) return { status: 'ABORT', reason: 'guard: không đọc được thân bài hiện tại' };
if ((await __sha256(__cur.value)) !== ${J(sha256(dbBody))}) return { status: 'ABORT', reason: 'guard: thân bài đổi sau lúc backup' };
return await window.hdWriteArticle(${J({ newsId: id, html: body, set, expectImages, dryRun: false })});`);
    try {
      out = await evaluate(client, liveCode, timeoutMs);
    } catch (err) {
      // Timeout hay lỗi thường đều có thể xảy ra SAU KHI POST đã gửi — không phân biệt được,
      // coi là UNKNOWN và GIỮ marker in-flight để lần sau tự phục hồi (không đoán DONE/FAIL).
      ctx.keepTab = true;
      log(`${err instanceof TimeoutError ? 'TIMEOUT' : 'LỖI'} khi ghi — KHÔNG rõ đã ghi chưa (UNKNOWN). Đọc CMS bài ${id} trước khi chạy lại. Backup: ${preDir}. Marker in-flight giữ nguyên.`);
      return 1;
    }
    // Kết quả dứt khoát (DONE/FAIL/ABORT/ALREADY) — xoá marker, không còn "không rõ".
    clearInflightMarker(idir, markerKey);
  }
  const runJson = path.join(P.backupRoot, `run-${id}-${stamp}.json`);
  writeVerified(runJson, JSON.stringify(out, null, 1));
  ctx.report.write = { status: out.status, ms: out.ms, verify: out.verify, backup: preDir };
  log(`Kết quả ghi → ${runJson}: ${out.status} (${out.ms ?? '?'}ms)\nverify: ${J(out.verify || out.failed || out.reason)}`);
  // ALREADY (#7): thân bài + field set đã khớp DB từ trước — không POST, coi như đạt (không phải lỗi).
  if (out.status !== 'DONE' && out.status !== 'ALREADY') { log('Ghi không đạt — dừng, đọc verify, so afterBody với file gửi.'); return 1; }
  if (out.status === 'ALREADY') log('Thân bài trên CMS đã khớp bản gửi từ trước — không POST lại.');

  // #9: bài chưa Xuất bản (trạng thái tạo ≠ 2) mà không có --publish đang chờ đổi trạng thái thì
  // nghiệm thu live trên URL nhiều khả năng 404 — không phải lỗi ghi. Bỏ qua, ghi rõ lý do, exit 0.
  if (ctx.liveSkipUnpublished && !a['skip-live-verify']) {
    ctx.report.live = { pass: true, skipped: 'LIVE_SKIPPED_UNPUBLISHED' };
    log('Bỏ nghiệm thu live: LIVE_SKIPPED_UNPUBLISHED (bài chưa Xuất bản, không có --publish).');
    return 0;
  }
  if (a['skip-live-verify']) { log('CẢNH BÁO: bỏ nghiệm thu live theo --skip-live-verify — CHƯA chứng minh trang live đã đổi.'); return 0; }
  // --publish (Hỏi Đáp): chuỗi all phải ghi xong RỒI mới đổi trạng thái, RỒI mới nghiệm thu live (bài
  // chỉ thật sự live sau khi publish) — hoãn nghiệm thu live ở đây, stepAll gọi lại sau khi publish xong.
  if (ctx.deferLiveVerify) { ctx._deferredLiveArgs = { htmlPath, preDir, stamp }; log('Ghi đạt — hoãn nghiệm thu live tới sau bước xuất bản.'); return 0; }
  return await runLiveVerify(ctx, { htmlPath, preDir, stamp });
}

/** Nghiệm thu live tách riêng để stepAll gọi lại SAU khi --publish đổi trạng thái xong (#9). */
export async function runLiveVerify(ctx, { htmlPath, preDir, stamp }) {
  const { a, id, P, log, deps } = ctx;
  const extra = [...(a.title ? ['--title', a.title] : []), ...(a['meta-title'] ? ['--meta-title', a['meta-title']] : [])];
  const verify = await waitThenVerify(async () => {
    const r = await runNode(VERIFY_LIVE, ['--clearcache', '--url', a['live-url'], '--html', htmlPath, '--old', path.join(preDir, 'before.html'), ...extra], deps.nodeExecFn);
    let j = {};
    try { j = JSON.parse(r.stdout); } catch { j = { raw: r.stdout.slice(0, 300), stderr: r.stderr.slice(0, 300) }; }
    return { ...j, pass: r.code === 0 && j.pass === true };
  }, { sleepFn: deps.sleepFn, log, delayMs: deps.liveDelayMs ?? 60000 });
  writeVerified(path.join(P.backupRoot, `live-verify-${id}-${stamp}.json`), JSON.stringify(verify, null, 1));
  ctx.report.live = verify;
  log(`Nghiệm thu live: ${verify.pass ? 'PASS' : 'FAIL'} — headings ${verify.headings ?? '?'}, images ${verify.images ?? '?'}`);
  return verify.pass ? 0 : 1;
}

export const CREATE_VALUES = ['create-file', 'status', 'url', 'keywords', 'article-type', 'child-category', 'parent-category', 'thumbnail', 'thumbnail-url', 'create-html'];

export async function main(argv, deps = {}) {
  const log = deps.log || console.log;
  const a = parseArgs(argv, {
    values: ['profile', 'task-dir', 'news-id', 'workspace', 'step', 'html', 'title', 'meta-title', 'meta-description', 'expect-images', 'live-url', 'timeout-sec', ...CREATE_VALUES],
    booleans: ['live', 'keep-tab', 'skip-live-verify', 'publish'],
  });
  // Profile có quyền CMS (xác nhận 24/09/2026); --profile truyền tay vẫn đè.
  if (!a.profile) a.profile = DEFAULT_PROFILE;
  // deps.tasksRoot: chỉ test tiêm (thư mục tasks/ giả) — production luôn dùng defaultTasksRoot() của cms-cli-pipeline.mjs.
  const W = requireTaskDir(a['task-dir'], { tasksRoot: deps.tasksRoot });
  if (!['upload', 'write', 'create', 'all', 'publish'].includes(a.step)) throw new CliError('--step phải là upload | write | create | all | publish', 2);
  const creating = a.step === 'create' || (a.step === 'all' && !!a['create-file']);
  const id = a['news-id'] != null ? Number(a['news-id']) : null;
  if (creating && id != null) throw new CliError('tạo bài mới thì không truyền --news-id (newsId do CMS cấp)', 2);
  if (!creating && (!Number.isInteger(id) || id <= 0)) throw new CliError('--news-id phải là số > 0 (bài Hỏi Đáp đã có); tạo bài mới dùng --step create hoặc --step all --create-file', 2);
  const client = deps.client || new McpClient({ spawnFn: deps.spawnFn });
  const ctx = {
    a, client, id, log, deps, W, P: id ? paths(W, id) : null, keepTab: !!a['keep-tab'], pageId: null, boundUrl: null, connected: false,
    runner: fs.readFileSync(RUNNER, 'utf8'), report: {},
    timeoutMs: Number(a['timeout-sec'] || 180) * 1000,
  };
  // Bám tab theo newsId; gọi lại cùng bài thì dùng lại tab, đổi bài (tạo xong → ghi) thì đóng tab cũ mở tab mới.
  ctx.bind = async (newsId = ctx.id) => {
    const url = `${CMS_ORIGIN}/v2/Faq/NewsEdit?newsId=${newsId}`;
    if (ctx.boundUrl === url) return;
    if (!ctx.connected) { await client.connect(); ctx.connected = true; }
    if (ctx.pageId != null) { try { await client.callTool('close_page', { pageId: ctx.pageId }, 15000); } catch { /* đã đóng */ } ctx.pageId = null; }
    ({ pageId: ctx.pageId } = await openAndBind(client, {
      profile: a.profile, url, expectUrlPrefix: `${CMS_ORIGIN}/v2/Faq/NewsEdit`, execFileFn: deps.execFileFn, sleepFn: deps.sleepFn,
    }));
    ctx.boundUrl = url;
  };

  // Bắt SIGTERM/SIGINT: process bị kill giữa lúc chạy (agent bị dừng, máy shutdown...) vẫn
  // phải ghi lại dấu "interrupted" vào run-log trước khi thoát, và cố đóng tab/MCP thay vì bỏ
  // mặc — marker in-flight (nếu đang ghi dở) KHÔNG bị đụng vào ở đây, lần chạy sau tự phục hồi.
  const signalSource = deps.signalSource || process;
  const exitFn = deps.exitFn || ((code) => process.exit(code));
  let cleanedUpOnSignal = false;
  const handleSignal = async (sig) => {
    if (cleanedUpOnSignal) return;
    cleanedUpOnSignal = true;
    try {
      appendJsonl(path.join(W, 'data/raw/cms-backup', 'run-log.jsonl'), {
        phase: 'signal', signal: sig, note: 'interrupted — CLI bị dừng giữa chừng, kiểm tay marker in-flight (nếu có) trước khi chạy lại',
      });
    } catch { /* thư mục backup có thể chưa kịp mkdir — không chặn việc thoát an toàn */ }
    log(`\nNhận ${sig} — dừng, đóng tab/MCP trước khi thoát.`);
    try { if (ctx.pageId != null) await client.callTool('close_page', { pageId: ctx.pageId }, 5000); } catch { /* tab đã đóng hoặc lỗi — ưu tiên thoát an toàn */ }
    try { await client.close(); } catch { /* đã đóng */ }
    exitFn(130);
  };
  const onSigterm = () => { handleSignal('SIGTERM'); };
  const onSigint = () => { handleSignal('SIGINT'); };
  signalSource.on('SIGTERM', onSigterm);
  signalSource.on('SIGINT', onSigint);

  try {
    if (a.step === 'upload') return await stepUpload(ctx);
    if (a.step === 'write') return await stepWrite(ctx);
    const { stepCreate, stepAll, stepPublish } = await import('./hoidap-create-and-all-steps.mjs');
    if (a.step === 'publish') return await stepPublish(ctx);
    return a.step === 'create' ? (await stepCreate(ctx)).code : await stepAll(ctx);
  } finally {
    signalSource.off('SIGTERM', onSigterm);
    signalSource.off('SIGINT', onSigint);
    if (ctx.pageId != null && !ctx.keepTab) {
      try { await client.callTool('close_page', { pageId: ctx.pageId }, 15000); } catch { /* đã đóng */ }
    }
    await client.close();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main(process.argv.slice(2)).then(
    (code) => process.exit(code),
    (err) => { console.error('LỖI:', err.message); process.exit(err.exitCode || 1); },
  );
}
