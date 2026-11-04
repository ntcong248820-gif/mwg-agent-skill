#!/usr/bin/env node
/**
 * cms-blog.mjs — CLI một cửa cho bài Hỏi Đáp + Game App trên NEW CMS (newcms.thegioididong.com).
 * Mọi lệnh ghi chỉ chạy khi có --go; thiếu --go là chạy thử, in kế hoạch/diff rồi dừng.
 * Token tự lo (newcms-auth.mjs). --old-cms chuyển lệnh sang script CMS cũ (cms-content-create).
 *
 *   node cms-blog.mjs read <id> [--out <dir>]
 *   node cms-blog.mjs lookup categories [từ] | article-types | form-types | platforms | tags <từ> | shortcodes
 *   node cms-blog.mjs create --form form.json [--type hoi-dap|game-app] [--go]
 *   node cms-blog.mjs update <id> [--html f.html] [--dir ảnh] [--set field=giá-trị ...] [--go]
 *   node cms-blog.mjs air <id> --html f.html [--dir ảnh] [--set ...] [--publish] [--no-live] [--go]
 *   node cms-blog.mjs images <id> --html f.html [--dir ảnh] [--go]      → ghi <f>.cdn.html
 *   node cms-blog.mjs image-map <thư mục ảnh> [--out anh-cdn.json]     → map ảnh local cho chen_anh.py (chưa upload)
 *   node cms-blog.mjs status <id> --to draft|pending|approved|actived [--date dd/mm/yyyy] [--time HH:MM] [--go]
 *   node cms-blog.mjs publish <id> [--date dd/mm/yyyy] [--time HH:MM] [--keep-time] [--go]
 *   node cms-blog.mjs thumb <id> --file thumb.jpg [--go]
 *   node cms-blog.mjs sticky <id...> [--off] [--go]
 *   node cms-blog.mjs history <id> [--size 20]
 *   node cms-blog.mjs rollback <id> --log <newsLogId> [--go]         (Hỏi Đáp — log Game App không giữ HTML)
 *   node cms-blog.mjs live <id> [--html f.html] [--no-wait]
 *   node cms-blog.mjs delete <id> [--go]                             (xoá mềm)
 *   node cms-blog.mjs ensure | status-token | seed | install-keepalive | uninstall-keepalive
 */

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import * as A from './newcms-api.mjs';
import { harnessChromeProfile } from './newcms-auth.mjs';
import { normalizeForm, lintContent, OPTIONS, TYPES, toCmsDate, shape, imageSize } from './cms-blog-lint.mjs';
import {
  STATE_DIR, LEDGER, CDN_BASE, EDIT_URL, previewUrl, articleKind, bodyOf, slugOf, liveUrl, statusOf, statusLabel,
  normalizeStatus, saveChanges, backup, uploadToNews, uploadHtmlImages, verifyFields,
} from './cms-blog-core.mjs';
import { diffSummary, liveCheck, waitThenVerify, ledgerClaim, ledgerUpsert, ledgerRemove, readLedger } from './cms-cli-air.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---------- tham số ----------
const argv = process.argv.slice(2);
const cmd = argv[0];
const pos = [];
const flags = { set: [] };
for (let i = 1; i < argv.length; i++) {
  const a = argv[i];
  if (!a.startsWith('--')) { pos.push(a); continue; }
  const k = a.slice(2);
  const takesValue = ['form', 'type', 'html', 'dir', 'set', 'to', 'date', 'time', 'file', 'log', 'out', 'size', 'profile', 'every-hours'].includes(k);
  const v = takesValue ? argv[++i] : true;
  if (k === 'set') flags.set.push(v); else flags[k] = v;
}
const GO = !!flags.go;
const die = (msg, code = 2) => { console.error(`LỖI: ${msg}`); process.exit(code); };
const needId = () => { const id = Number(pos[0]); if (!(id > 0)) die(`thiếu newsId. Cách dùng: node cms-blog.mjs ${cmd} <newsId> ...`); return id; };
const readFile = (f, what) => { if (!f || !fs.existsSync(f)) die(`không thấy ${what} ${f ?? '(thiếu)'}`); return fs.readFileSync(f, 'utf8'); };
const show = (o) => console.log(JSON.stringify(o, null, 2));
const dry = (msg = 'Chạy thử, chưa ghi. Thêm --go để ghi thật.') => { console.log(`\n${msg}`); process.exit(0); };

async function load(id) {
  const rec = await A.newsSelect(id);
  if (!rec) die(`không đọc được newsId=${id}`);
  if (rec.isDeleted === 1) console.warn(`CẢNH BÁO: bài ${id} đang ở trạng thái đã xoá`);
  return rec;
}
const summary = (rec) => ({
  newsId: rec.newsId, loai: articleKind(rec), title: rec.title, url: slugOf(rec), trang_thai: statusLabel(rec),
  activedDate: rec.activedDate, noi_bat: rec.isSticked === 1, thumbnail: rec.thumbnailImage, body: shape(bodyOf(rec)),
  edit: EDIT_URL[articleKind(rec)](rec.newsId), preview: previewUrl(rec) || undefined, live: liveUrl(rec),
});

/** --set field=value → changes. Field đặt tên như newsselect; vài tên tắt cho tiện. */
const SET_ALIAS = { meta_title: 'metaTitle', meta_desc: 'metaDescription', tags: 'metaKeyword', keyword: 'metaKeyword', article_type: 'articleType', products: 'productIdList', product_related: 'productIdList', child_category: 'listChildThreadId', parent_category: 'listParentThreadId', thumb: 'thumbnailImage', platforms: 'platformIdList', form_game_app: 'formGameApp' };
const SETTABLE = { 'hoi-dap': ['title', 'url', 'metaTitle', 'metaDescription', 'metaKeyword', 'schema', 'articleType', 'productIdList', 'listChildThreadId', 'listParentThreadId', 'thumbnailImage', 'isSticked', 'isHideBannerVccorp', 'activedDate'], 'game-app': ['title', 'url', 'metaTitle', 'metaDescription', 'schema', 'formGameApp', 'isGame', 'platformIdList', 'productIdList', 'thumbnailImage', 'isSticked', 'isHideBannerVccorp', 'isFeature', 'isPin', 'activedDate'] };
function parseSets(kind) {
  const ch = {};
  for (const s of flags.set) {
    const i = String(s).indexOf('=');
    if (i < 1) die(`--set phải dạng field=giá-trị (nhận "${s}")`);
    const k = SET_ALIAS[s.slice(0, i)] || s.slice(0, i);
    if (!SETTABLE[kind].includes(k)) die(`--set ${k} không hỗ trợ cho ${kind}. Được: ${SETTABLE[kind].join(', ')}`);
    const v = s.slice(i + 1);
    ch[k] = /^is[A-Z]/.test(k) ? Number(v) : v;
  }
  return ch;
}
function lintSets(kind, ch) {
  const err = [];
  const L = (s) => [...String(s)].length;
  if (ch.title !== undefined && L(ch.title) > TYPES[kind].maxTitle) err.push(`title ${L(ch.title)} > ${TYPES[kind].maxTitle}`);
  if (ch.metaTitle !== undefined && L(ch.metaTitle) > 70) err.push(`metaTitle ${L(ch.metaTitle)} > 70`);
  if (ch.metaDescription !== undefined && L(ch.metaDescription) > 170) err.push(`metaDescription ${L(ch.metaDescription)} > 170`);
  if (ch.url !== undefined && !/^[a-z0-9]+(-[a-z0-9]+)*$/.test(ch.url)) err.push(`url "${ch.url}" sai dạng`);
  if (ch.metaKeyword !== undefined && ch.metaKeyword.split(',').filter(Boolean).length > 5) err.push('metaKeyword tối đa 5 từ khoá');
  if (ch.articleType !== undefined && !OPTIONS.dang_bai_viet.includes(ch.articleType)) err.push(`articleType "${ch.articleType}" không có trong CMS`);
  return err;
}

// ---------- CMS cũ (dự phòng) ----------
async function oldCms() {
  const cand = [path.resolve(HERE, '../../cms-content-create/scripts'), path.resolve(HERE, '../../../../.claude/skills/cms-content-create/scripts')];
  const dir = cand.find((d) => fs.existsSync(d));
  const air = [path.resolve(HERE, '../../content-cms-air-hoidap/scripts/run-air-hoidap-cli.mjs')].find((f) => fs.existsSync(f));
  const go = GO ? ['--go'] : [];
  const OLD_STATUS = { draft: '1', actived: '2', pending: '3', approved: '4' };
  let script, args;
  switch (cmd) {
    case 'create': script = 'tao_bai.mjs'; args = [flags.form, ...((flags.type || 'hoi-dap') === 'game-app' ? ['--mode', 'game-app'] : []), ...go]; break;
    case 'update': script = 'cap_nhat_noi_dung.mjs'; args = [pos[0], flags.html, ...go]; break;
    case 'publish': script = 'xuat_ban.mjs'; args = [pos[0], ...go, ...(flags['keep-time'] ? ['--giu-gio'] : [])]; break;
    case 'thumb': script = 'doi_thumb.mjs'; args = [pos[0], flags.file, ...go]; break;
    case 'status': script = 'doi_trang_thai.mjs'; args = [pos[0], OLD_STATUS[normalizeStatus('hoi-dap', flags.to)]]; if (!GO) dry('CMS cũ: doi_trang_thai.mjs không có chạy thử. Thêm --go để đổi.'); break;
    case 'sticky': script = 'tick_noi_bat.mjs'; args = [...pos, ...go]; break;
    case 'air':
      if (!air) die('không thấy content-cms-air-hoidap/run-air-hoidap-cli.mjs');
      console.log(`CMS cũ: air dùng ${air} — xem SKILL.md của content-cms-air-hoidap cho tham số (--workspace, --step...).`);
      process.exit(spawnSync(process.execPath, ['--preserve-symlinks', '--preserve-symlinks-main', air, ...argv.slice(1).filter((a) => a !== '--old-cms')], { stdio: 'inherit' }).status ?? 1);
      break;
    default: die(`--old-cms không hỗ trợ lệnh "${cmd}"`);
  }
  if (!dir) die('không thấy skill cms-content-create (CMS cũ) trên máy này');
  // Script cũ đòi CMS_CHROME_PROFILE: lấy từ harness.config (cms.chromeProfiles.faq) nếu chưa đặt.
  const env = { ...process.env, CMS_CHROME_PROFILE: process.env.CMS_CHROME_PROFILE || (await harnessChromeProfile('faq')) || '' };
  if (args.some((a) => a === undefined)) die('thiếu tham số cho lệnh CMS cũ');
  console.log(`CMS cũ → ${script} ${args.join(' ')}`);
  process.exit(spawnSync(process.execPath, ['--preserve-symlinks', '--preserve-symlinks-main', path.join(dir, script), ...args], { stdio: 'inherit', env }).status ?? 1);
}

// ---------- lệnh ----------
async function cmdRead() {
  const rec = await load(needId());
  const out = flags.out || path.join(STATE_DIR, String(rec.newsId));
  fs.mkdirSync(out, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  fs.writeFileSync(path.join(out, `read-${stamp}.json`), JSON.stringify(rec, null, 1));
  fs.writeFileSync(path.join(out, `read-${stamp}.body.html`), bodyOf(rec));
  show(summary(rec));
  console.log(`Đã lưu bản ghi + thân bài: ${out}/read-${stamp}.*`);
}

async function cmdLookup() {
  const what = pos[0];
  const kw = pos.slice(1).join(' ').toLowerCase();
  if (what === 'categories') {
    for (const [id, c] of Object.entries(OPTIONS.chuyen_muc_con)) if (!kw || c.ten.toLowerCase().includes(kw)) console.log(`${id}\t${c.ten}\tcha: ${c.cha.join(',')}`);
  } else if (what === 'article-types') console.log((await A.faqArticleTypes()).join('\n'));
  else if (what === 'form-types') console.log((await A.gameAppFormTypes()).join('\n'));
  else if (what === 'platforms') for (const p of await A.gameAppPlatforms()) console.log(`${p.platformId}\t${p.platformName}`);
  else if (what === 'tags') { if (!kw) die('thiếu từ khoá: lookup tags <từ>'); for (const t of await A.tagSearch(kw, { size: 20 })) console.log(`${t.tagId}\t${t.tagName}`); }
  else if (what === 'shortcodes') for (const s of await A.shortcodeList()) console.log(`${s.group ?? ''}\t${s.label ?? ''}\t${s.code ?? s.value ?? ''}`);
  else die('lookup categories [từ] | article-types | form-types | platforms | tags <từ> | shortcodes');
}

async function cmdCreate() {
  const formFile = flags.form || die('thiếu --form form.json');
  const f = JSON.parse(readFile(formFile, 'form'));
  const kind = flags.type || f.type || 'hoi-dap';
  const { v, err, warn } = normalizeForm(f, { kind, baseDir: path.dirname(path.resolve(formFile)) });
  let html = '';
  if (v.contentFile && fs.existsSync(v.contentFile)) {
    html = fs.readFileSync(v.contentFile, 'utf8');
    const c = await lintContent(html);
    err.push(...c.err); warn.push(...c.warn);
  }
  let images = [];
  try { images = (await import('./cms-cli-air.mjs')).imagesToUpload(html, v.imagesDir, { localOnly: true }); } catch (e) { err.push(e.message); }
  if (kind === 'game-app' && v.tags.length) warn.push('Game App không có ô tags/metaKeyword trên NEW CMS — bỏ qua tags');
  console.log(`# Tạo bài ${kind} trên NEW CMS\n`);
  show({ title: v.title, url: v.url, chuyen_muc: kind === 'hoi-dap' ? `${v.child} ${v.childName ?? ''} / cha ${v.parent}` : '2002 Game App', dang_bai: kind === 'hoi-dap' ? v.articleType : v.formGameApp,
    trang_thai: v.status, xuat_ban_luc: v.activedDate || '(không hẹn)', thumb: v.thumb || v.thumbUrl, anh_trong_bai: images.map((x) => path.basename(x)), body: shape(html) });
  for (const w of warn) console.log(`  CẢNH BÁO: ${w}`);
  if (err.length) { for (const e of err) console.log(`  LỖI: ${e}`); die(`${err.length} lỗi, không tạo bài`, 3); }
  if (!GO) dry();

  const key = `${kind}:${v.url}`;
  const { prior } = ledgerClaim(LEDGER, key, { status: 'PENDING', kind, title: v.title });
  if (prior) die(`slug này đã tạo trước đó (${prior.status}${prior.newsId ? `, newsId ${prior.newsId}` : ''}, ${prior.at}). Bài đã có thì dùng update/air; muốn tạo lại thì xoá dòng "${key}" trong ${LEDGER}.`, 4);

  let id;
  try {
    // 1) Tạo nháp (chưa có thư mục ảnh vì chưa có id). Thumb tạm = thumb_url nếu có.
    const common = { title: v.title, url: v.url, metaTitle: v.metaTitle, metaDescription: v.metaDesc, schema: v.schema, isHideBannerVccorp: v.hideBannerVccorp, isSticked: 1, thumbnailImage: v.thumbUrl || '' };
    if (kind === 'hoi-dap') {
      id = await A.faqAdd({ status: 'draft', ...common, description: html, metaKeyword: v.tags.join(','), listparentthreadid: v.parent, listchildthreadid: v.child, articletype: v.articleType, productidlist: v.productRelated });
    } else {
      // Server Game App từ chối tạo khi thiếu thumb (HTTP 400) mà thư mục News/{id} chưa có → thumb tạm qua
      // PostImage (tên hash), có id rồi bước 2 thay bằng bản giữ tên trong News/{id}.
      if (!common.thumbnailImage) common.thumbnailImage = await A.postImage(v.thumb, { type: 2 });
      const r = await A.gameAppSave({ ...common, content: html, isGame: v.isGame, formGameApp: v.formGameApp, activedDate: A.cmsDate(), status: 'draft', platformIdList: v.platforms || undefined, productIdList: v.productRelated || undefined, isGallery: 0, isVideo: 0, isFeature: 0, isCanYouDoIt: 0, isPin: 0 });
      id = r.newsId;
      if (!(id > 0)) throw new Error(`Game App không trả newsId: ${r.message}`);
    }
    ledgerUpsert(LEDGER, { key, status: 'PENDING', kind, newsId: id, title: v.title });
    console.log(`Đã tạo nháp newsId=${id}`);

    // 2) Upload thumb + ảnh bài vào News/{id}, giữ tên file.
    let thumbnailImage = v.thumbUrl;
    if (v.thumb) thumbnailImage = (await uploadToNews(id, [v.thumb])).uploaded[path.basename(v.thumb)];
    const up = await uploadHtmlImages(id, html, v.imagesDir);

    // 3) Ghi bản cuối: thân bài đã thay src, thumb, trạng thái đích.
    const rec = await load(id);
    const changes = { body: up.html, thumbnailImage, status: v.status, isSticked: 1, activedDate: v.activedDate || A.cmsDate() };
    const after = await saveChanges(rec, changes);
    const bad = verifyFields(after, { body: up.html, title: v.title, url: v.url, metaTitle: v.metaTitle, metaDescription: v.metaDesc, thumbnailImage, isSticked: 1 });
    if (statusOf(after) !== v.status) bad.push(`trạng thái: muốn ${v.status}, server ${statusOf(after)}`);
    if (kind === 'hoi-dap' && (String(after.listChildThreadId) !== v.child || String(after.listParentThreadId) !== v.parent)) bad.push(`chuyên mục: server ${after.listParentThreadId}/${after.listChildThreadId}`);
    ledgerUpsert(LEDGER, { key, status: bad.length ? 'VERIFY_FAIL' : 'DONE', kind, newsId: id, title: v.title });
    show(summary(after));
    if (bad.length) die(`đọc lại lệch:\n  ${bad.join('\n  ')}`, 5);
    console.log(`\nOK: tạo xong bài ${id}, ${up.files.length} ảnh bài + thumb trong ${CDN_BASE(id)}`);
    if (v.status === 'actived' || v.status === 'approved') console.log('Lưu ý: hẹn giờ xuất bản trên NEW CMS — kiểm trang live sau giờ hẹn (lệnh live).');
  } catch (e) {
    if (!id) ledgerRemove(LEDGER, key);
    die(`${e.message}${id ? `\nBài nháp ${id} đã tạo — sửa lỗi rồi chạy update ${id} để ghi tiếp, đừng tạo lại.` : ''}`, 1);
  }
}

/** update / air dùng chung: thân bài mới (tuỳ chọn) + --set, upload ảnh local, ghi, đọc lại so byte. */
async function writeUpdate({ publish = false } = {}) {
  const id = needId();
  const rec = await load(id);
  const kind = articleKind(rec);
  const changes = parseSets(kind);
  const err = lintSets(kind, changes);
  let html;
  if (flags.html) {
    html = readFile(flags.html, 'file HTML');
    const c = await lintContent(html);
    err.push(...c.err);
    for (const w of c.warn) console.log(`  CẢNH BÁO: ${w}`);
  }
  if (html === undefined && !Object.keys(changes).length && !publish) die('không có gì để ghi: cần --html và/hoặc --set');
  const imagesDir = flags.dir || (flags.html ? path.dirname(path.resolve(flags.html)) : '');
  let files = [];
  if (html !== undefined) try { files = (await import('./cms-cli-air.mjs')).imagesToUpload(html, imagesDir, { localOnly: true }); } catch (e) { err.push(e.message); }
  console.log(`# ${cmd} bài ${id} (${kind}, ${statusLabel(rec)}): ${rec.title}\n`);
  if (html !== undefined) show({ diff: diffSummary(bodyOf(rec), html), anh_se_upload: files.map((f) => path.basename(f)) });
  for (const [k, val] of Object.entries(changes)) console.log(`  ${k}: ${JSON.stringify(rec[k])} → ${JSON.stringify(val)}`);
  if (publish) console.log(`  trạng thái: ${statusLabel(rec)} → Xuất bản (${flags.date ? `${flags.date} ${flags.time || '02:00'}` : 'ngay lúc ghi'})`);
  if (err.length) { for (const e of err) console.log(`  LỖI: ${e}`); die(`${err.length} lỗi, không ghi`, 3); }
  if (!GO) dry();

  console.log(`Backup: ${backup(rec)}`);
  if (html !== undefined) {
    const up = await uploadHtmlImages(id, html, imagesDir);
    changes.body = up.html;
    if (up.files.length) {
      const out = `${flags.html.replace(/\.html?$/i, '')}.cdn.html`;
      fs.writeFileSync(out, up.html);
      console.log(`Đã upload ${up.files.length} ảnh, bản HTML đã thay src: ${out}`);
    }
  }
  if (publish) Object.assign(changes, publishChanges(rec));
  const after = await saveChanges(rec, changes);
  const { status, ...expect } = changes;
  const bad = verifyFields(after, expect);
  if (status && statusOf(after) !== status) bad.push(`trạng thái: muốn ${status}, server ${statusOf(after)}`);
  show(summary(after));
  if (bad.length) die(`đọc lại lệch:\n  ${bad.join('\n  ')}`, 5);
  console.log('\nOK: đọc lại khớp từng byte.');
  return after;
}

function publishChanges(rec) {
  const kind = articleKind(rec);
  let activedDate = A.cmsDate();
  if (flags['keep-time']) activedDate = rec.activedDate;
  if (flags.date) activedDate = toCmsDate(flags.date, flags.time || '02:00') || die(`--date ${flags.date} --time ${flags.time} sai dạng dd/mm/yyyy HH:MM`);
  return { status: normalizeStatus(kind, 'actived'), activedDate };
}

async function cmdAir() {
  if (!flags.html) die('air cần --html');
  const publish = !!flags.publish;
  const after = await writeUpdate({ publish });
  if (flags['no-live'] || statusOf(after) === 'draft' || statusOf(after) === 'pending') { if (!flags['no-live']) console.log('Bài chưa xuất bản — bỏ qua nghiệm thu live.'); return; }
  await verifyLive(after, bodyOf(after));
}

async function verifyLive(rec, html, { wait = true } = {}) {
  const url = liveUrl(rec);
  const run = () => liveCheck({ url, html });
  const r = wait ? await waitThenVerify(run) : await run();
  show(r);
  if (!r.pass) die(`trang live chưa khớp bản đã ghi: ${url}`, 6);
  console.log(`OK: live khớp ${url}`);
}

async function cmdImages() {
  const id = needId();
  const html = readFile(flags.html, 'file HTML');
  const dir = flags.dir || path.dirname(path.resolve(flags.html));
  const files = (await import('./cms-cli-air.mjs')).imagesToUpload(html, dir, { localOnly: true });
  console.log(`Ảnh local cần upload vào ${CDN_BASE(id)}:\n  ${files.map((f) => path.basename(f)).join('\n  ') || '(không có)'}`);
  if (!GO || !files.length) dry();
  const up = await uploadHtmlImages(id, html, dir);
  const out = `${flags.html.replace(/\.html?$/i, '')}.cdn.html`;
  fs.writeFileSync(out, up.html);
  show(up.uploaded);
  console.log(`OK: ${up.files.length} ảnh đã lên CDN, đúng từng byte. HTML đã thay src: ${out} (chưa ghi vào bài)`);
}

/**
 * Map ảnh local → {src: tên file, width, height} cùng khuôn anh-cdn.json của blog-hoi-dap-tron-goi, để chen_anh.py
 * chèn thẻ ảnh với src local; create/update upload và thay src sau. Cỡ hiển thị = CMS (rộng 845, giữ tỉ lệ). Bỏ thumb.
 */
async function cmdImageMap() {
  const dir = pos[0] || die('thiếu thư mục ảnh: image-map <thư mục>');
  const out = flags.out || path.join(dir, 'anh-cdn.json');
  const map = {};
  for (const f of fs.readdirSync(dir).filter((n) => /\.(jpe?g|png|webp)$/i.test(n) && !/-thumb(-\d+)?\./i.test(n)).sort()) {
    const d = imageSize(path.join(dir, f));
    if (!d?.w) die(`không đọc được kích thước ${f}`);
    const width = Math.min(845, d.w);
    map[f] = { src: f, width, height: Math.round((width * d.h) / d.w) };
  }
  fs.writeFileSync(out, JSON.stringify(map, null, 1));
  console.log(`${Object.keys(map).length} ảnh → ${out} (src = tên file local; create/update sẽ upload vào News/{id} và thay src)`);
}

async function cmdStatus({ publish = false } = {}) {
  const id = needId();
  const rec = await load(id);
  const kind = articleKind(rec);
  let changes;
  if (publish) changes = publishChanges(rec);
  else {
    changes = { status: normalizeStatus(kind, flags.to || die('thiếu --to draft|pending|approved|actived')) };
    if (flags.date) changes.activedDate = toCmsDate(flags.date, flags.time || '02:00') || die('--date/--time sai dạng');
  }
  console.log(`Bài ${id} (${kind}): ${statusLabel(rec)} → ${kind === 'game-app' && changes.status === 'approved' ? 'Xuất bản' : { draft: 'Nháp', pending: 'Chờ duyệt', approved: 'Đã duyệt', actived: 'Xuất bản' }[changes.status]}${changes.activedDate ? `, ngày đăng ${changes.activedDate}` : ''}`);
  if (!GO) dry();
  console.log(`Backup: ${backup(rec)}`);
  const after = await saveChanges(rec, changes);
  const bad = verifyFields(after, { activedDate: changes.activedDate });
  if (statusOf(after) !== changes.status) bad.push(`trạng thái server: ${statusOf(after)}`);
  if (bodyOf(after) !== bodyOf(rec)) bad.push('thân bài bị đổi khi đổi trạng thái');
  show(summary(after));
  if (bad.length) die(bad.join('\n  '), 5);
  console.log('OK');
}

async function cmdThumb() {
  const id = needId();
  const file = flags.file || die('thiếu --file thumb.jpg');
  if (!fs.existsSync(file)) die(`không thấy ${file}`);
  const rec = await load(id);
  console.log(`Thumb bài ${id}: ${rec.thumbnailImage} → ${CDN_BASE(id)}${path.basename(file)}`);
  if (!GO) dry();
  console.log(`Backup: ${backup(rec)}`);
  const url = (await uploadToNews(id, [path.resolve(file)])).uploaded[path.basename(file)];
  const after = await saveChanges(rec, { thumbnailImage: url });
  const bad = verifyFields(after, { thumbnailImage: url, body: bodyOf(rec) });
  if (bad.length) die(bad.join('\n  '), 5);
  console.log(`OK: thumb = ${url}`);
}

async function cmdSticky() {
  const ids = pos.map(Number).filter((n) => n > 0);
  if (!ids.length) die('thiếu newsId');
  const val = flags.off ? 0 : 1;
  for (const id of ids) {
    const rec = await load(id);
    console.log(`${id}: isSticked ${rec.isSticked} → ${val}${rec.isSticked === val ? ' (đã đúng, bỏ qua)' : ''}`);
    if (!GO || rec.isSticked === val) continue;
    backup(rec);
    const after = await saveChanges(rec, { isSticked: val });
    if (after.isSticked !== val || bodyOf(after) !== bodyOf(rec)) die(`${id}: đọc lại lệch`, 5);
  }
  if (!GO) dry();
  console.log('OK');
}

async function cmdHistory() {
  const id = needId();
  const rows = await A.newsLog(id, { size: Number(flags.size) || 20 });
  for (const r of rows) console.log(`${r.newsLogId}\t${r.updatedDate}\t${r.updatedUser}\t${r.description ? `${r.description.length} ký tự HTML` : '(không lưu HTML)'}`);
  if (!rows.length) console.log('(không có lịch sử)');
}

async function cmdRollback() {
  const id = needId();
  const logId = Number(flags.log) || die('thiếu --log <newsLogId> (xem lệnh history)');
  const rec = await load(id);
  if (articleKind(rec) !== 'hoi-dap') die('rollback chỉ cho Hỏi Đáp: lịch sử Game App không giữ HTML');
  let row;
  for (let page = 0; page < 20 && !row; page++) {
    const rows = await A.newsLog(id, { page, size: 50 });
    row = rows.find((r) => Number(r.newsLogId) === logId);
    if (rows.length < 50) break;
  }
  if (!row?.description) die(`không thấy bản log ${logId} có HTML`);
  console.log(`Rollback ${id} về bản ${logId} (${row.updatedDate}, ${row.updatedUser})`);
  show(diffSummary(bodyOf(rec), row.description));
  if (!GO) dry();
  console.log(`Backup: ${backup(rec)}`);
  const after = await saveChanges(rec, { body: row.description });
  if (bodyOf(after) !== row.description) die('đọc lại lệch', 5);
  console.log('OK: đã khôi phục thân bài.');
}

async function cmdLive() {
  const rec = await load(needId());
  const html = flags.html ? readFile(flags.html, 'file HTML') : bodyOf(rec);
  if (statusOf(rec) === 'draft' || statusOf(rec) === 'pending') console.warn(`CẢNH BÁO: bài đang ${statusLabel(rec)}, trang live có thể chưa có.`);
  await verifyLive(rec, html, { wait: !flags['no-wait'] });
}

async function cmdDelete() {
  const rec = await load(needId());
  console.log(`Xoá mềm bài ${rec.newsId} (${articleKind(rec)}, ${statusLabel(rec)}): ${rec.title}`);
  if (!GO) dry();
  console.log(`Backup: ${backup(rec, 'before-delete')}`);
  await A.newsDelete(rec.newsId);
  const after = await A.newsSelect(rec.newsId).catch(() => null);
  console.log(`OK: đã xoá mềm (đọc lại: ${after ? `isDeleted=${after.isDeleted}` : 'không còn đọc được'})`);
  for (const r of readLedger(LEDGER).filter((x) => x.newsId === rec.newsId)) ledgerRemove(LEDGER, r.key);
}

function cmdAuth() {
  const map = { ensure: 'ensure', 'status-token': 'status', seed: 'seed', 'install-keepalive': 'install-keepalive', 'uninstall-keepalive': 'uninstall-keepalive' };
  const extra = [...(flags.profile ? ['--profile', flags.profile] : []), ...(flags['every-hours'] ? ['--every-hours', flags['every-hours']] : [])];
  process.exit(spawnSync(process.execPath, [path.join(HERE, 'newcms-auth.mjs'), map[cmd], ...extra], { stdio: 'inherit' }).status ?? 1);
}

const CMDS = {
  read: cmdRead, lookup: cmdLookup, create: cmdCreate, update: () => writeUpdate(), air: cmdAir, images: cmdImages,
  status: () => cmdStatus(), publish: () => cmdStatus({ publish: true }), thumb: cmdThumb, sticky: cmdSticky,
  history: cmdHistory, rollback: cmdRollback, live: cmdLive, delete: cmdDelete, 'image-map': cmdImageMap,
};
if (['ensure', 'status-token', 'seed', 'install-keepalive', 'uninstall-keepalive'].includes(cmd)) cmdAuth();
else if (!CMDS[cmd]) { console.log(fs.readFileSync(fileURLToPath(import.meta.url), 'utf8').split('*/')[0].split('\n').filter((l) => l.startsWith(' *')).map((l) => l.replace(/^ \* ?/, '')).join('\n')); process.exit(cmd ? 2 : 0); }
else if (flags['old-cms']) await oldCms();
else await CMDS[cmd]().catch((e) => die(e.message, 1));
