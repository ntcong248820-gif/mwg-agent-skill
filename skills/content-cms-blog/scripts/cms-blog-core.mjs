/**
 * cms-blog-core.mjs — phần dùng chung của CLI content-cms-blog: nhận loại bài, đọc trạng thái, dựng payload
 * lưu đúng như app NEW CMS (Hỏi Đáp qua faqUpdate, Game App qua cmsgameappnewssave gửi đủ form),
 * upload ảnh vào thư mục riêng của bài, backup, sổ chống tạo trùng.
 */

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { newsSelect, faqUpdate, faqStatusFields, gameAppSave, uploadFilesCms, cmsDate } from './newcms-api.mjs';
import { imagesToUpload, planImageUploads, verifyCdnBytes, replaceImageSrcs } from './cms-cli-air.mjs';
import { articleKind, TYPES } from './cms-blog-lint.mjs';

export const STATE_DIR = process.env.CMS_BLOG_STATE_DIR || path.join(os.homedir(), '.local/state/cms-blog');
export const LEDGER = path.join(STATE_DIR, 'created.json');
/** Ảnh upload qua UploadFilesCms (giữ tên file) nằm ở bucket webmwg, không phải mwg-static như CMS cũ. */
export const CDN_BASE = (id) => `https://cdnv2.tgdd.vn/webmwg/common/News/${id}/`;
export const EDIT_URL = { 'hoi-dap': (id) => `https://newcms.thegioididong.com/Faq/NewsEdit?newsId=${id}`, 'game-app': (id) => `https://newcms.thegioididong.com/GameApp/EditNews?newID=${id}` };
/** Xem trước bài chưa xuất bản — chỉ Hỏi Đáp đã đo được (staging). */
export const previewUrl = (rec) => (articleKind(rec) === 'hoi-dap' ? `https://staging.thegioididong.com/hoi-dap/xem-truoc/${slugOf(rec)}-${rec.newsId}` : '');

export const bodyField = (kind) => TYPES[kind].bodyField;
export const bodyOf = (rec) => String(rec?.[bodyField(articleKind(rec))] ?? '');
/** Slug không kèm -newsId (app Game App cắt đuôi -id trước khi gửi lại). */
export const slugOf = (rec) => String(rec?.url ?? '').replace(new RegExp(`-${rec?.newsId}$`), '');
export const liveUrl = (rec) => TYPES[articleKind(rec)].live(slugOf(rec), rec.newsId);

/** Trạng thái đọc từ cờ — Hỏi Đáp: draft|pending|approved|actived; Game App: draft|pending|approved (approved = Xuất bản). */
export function statusOf(rec) {
  if (articleKind(rec) === 'game-app') return rec.isActived === 1 ? 'approved' : rec.isDraft === 1 ? 'draft' : 'pending';
  return rec.isDraft === 1 ? 'draft' : rec.isActived === 1 ? 'actived' : rec.isApproved === 1 ? 'approved' : 'pending';
}
export const STATUS_LABEL = { draft: 'Nháp', pending: 'Chờ duyệt', approved: 'Đã duyệt', actived: 'Xuất bản' };
export const statusLabel = (rec) => (articleKind(rec) === 'game-app' && statusOf(rec) === 'approved' ? 'Xuất bản' : STATUS_LABEL[statusOf(rec)]);

/** Đổi tên trạng thái người dùng gõ sang giá trị API theo loại bài ("actived"/"publish" của Game App = approved). */
export function normalizeStatus(kind, s) {
  const v = String(s || '').toLowerCase();
  const map = { nhap: 'draft', draft: 'draft', 'cho-duyet': 'pending', pending: 'pending', 'da-duyet': 'approved', approved: 'approved', 'xuat-ban': 'actived', publish: 'actived', actived: 'actived' };
  const st = map[v];
  if (!st) throw new Error(`trạng thái "${s}" không hợp lệ (draft | pending | approved | actived)`);
  return kind === 'game-app' && st === 'actived' ? 'approved' : st;
}

/** Payload Game App giống app gửi khi bấm Lưu: đủ form từ bản ghi, đè `changes`; platform/product không đổi thì để undefined (server giữ). */
export function gameAppPayload(rec, changes = {}) {
  const pick = (k, d) => (changes[k] !== undefined ? changes[k] : rec[k] ?? d);
  return {
    newsId: rec.newsId,
    title: pick('title', ''), url: changes.url !== undefined ? changes.url : slugOf(rec), content: pick('content', ''),
    thumbnailImage: pick('thumbnailImage', ''), isGame: changes.isGame !== undefined ? changes.isGame : rec.isGameApp ?? 1,
    formGameApp: pick('formGameApp', ''), metaTitle: pick('metaTitle', ''), metaDescription: pick('metaDescription', ''),
    schema: pick('schema', ''), activedDate: pick('activedDate', cmsDate()), status: changes.status ?? statusOf(rec),
    platformIdList: changes.platformIdList, productIdList: changes.productIdList,
    isGallery: pick('isGallery', 0), isVideo: pick('isVideo', 0), isSticked: pick('isSticked', 0), isFeature: pick('isFeature', 0),
    isCanYouDoIt: pick('isCanYouDoIt', 0), isPin: pick('isPin', 0), isHideBannerVccorp: pick('isHideBannerVccorp', 0),
  };
}

/**
 * Lưu thay đổi cho 1 bài, đúng đường của loại bài. `changes` dùng tên field như newsselect (camelCase);
 * thân bài truyền qua khoá `body`, trạng thái qua `status`. Trả bản ghi đọc lại.
 */
export async function saveChanges(rec, changes) {
  const kind = articleKind(rec);
  const { body, status, ...rest } = changes;
  if (kind === 'game-app') {
    const ch = { ...rest };
    if (body !== undefined) ch.content = body;
    if (status) ch.status = status;
    const r = await gameAppSave(gameAppPayload(rec, ch));
    if (!(r.newsId > 0)) throw new Error(`lưu Game App không trả newsId: ${r.message}`);
    return newsSelect(rec.newsId);
  }
  const ch = { ...rest };
  if (body !== undefined) ch.description = body;
  if (rest.metaKeyword !== undefined) ch.tags = rest.metaKeyword;
  if (status) Object.assign(ch, faqStatusFields(status));
  return faqUpdate(rec.newsId, ch);
}

/** Lưu bản ghi đầy đủ trước khi ghi. Trả đường dẫn. */
export function backup(rec, tag = 'before') {
  const dir = path.join(STATE_DIR, String(rec.newsId));
  fs.mkdirSync(dir, { recursive: true });
  const stamp = new Date().toISOString().replace(/[:.]/g, '-');
  const file = path.join(dir, `${stamp}-${tag}.json`);
  fs.writeFileSync(file, JSON.stringify(rec, null, 1));
  fs.writeFileSync(file.replace(/\.json$/, '.body.html'), bodyOf(rec));
  return file;
}

/**
 * Upload danh sách file vào News/{id} (giữ tên). HEAD trước: tên đã có + cùng byte → dùng lại;
 * khác byte → dừng (CDN không ghi đè được, phải đổi tên). Nghiệm thu từng byte sau upload.
 * Trả { uploaded: {tên: url}, reused, fresh }.
 */
export async function uploadToNews(id, files, { log = console.log } = {}) {
  if (!files.length) return { uploaded: {}, reused: 0, fresh: 0 };
  const base = CDN_BASE(id);
  const plan = await planImageUploads(base, files);
  if (plan.conflicts.length || plan.errors.length) throw new Error(`không upload được:\n  ${[...plan.conflicts, ...plan.errors].join('\n  ')}`);
  const uploaded = { ...plan.reuse };
  for (const f of plan.upload) {
    const url = await uploadFilesCms(f, { pathFolder: `News/${id}` });
    uploaded[path.basename(f)] = url;
    log(`  upload ${path.basename(f)} → ${url}`);
  }
  const dirs = [...new Set(files.map((f) => path.dirname(f)))];
  for (const d of dirs) {
    const part = Object.fromEntries(Object.entries(uploaded).filter(([n]) => files.some((f) => path.dirname(f) === d && path.basename(f) === n)));
    const v = await verifyCdnBytes(part, d);
    if (!v.ok) throw new Error(`ảnh trên CDN lệch file local:\n  ${v.bad.join('\n  ')}`);
  }
  return { uploaded, reused: Object.keys(plan.reuse).length, fresh: plan.upload.length };
}

/** Ảnh local trong HTML → upload vào News/{id} → HTML đã thay src. Không có ảnh local thì trả nguyên. */
export async function uploadHtmlImages(id, html, imagesDir, opts) {
  const files = imagesToUpload(html, imagesDir, { localOnly: true });
  if (!files.length) return { html, files: [], uploaded: {} };
  const { uploaded } = await uploadToNews(id, files, opts);
  const out = replaceImageSrcs(html, uploaded).html;
  const left = [...out.matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map((m) => m[1]).filter((s) => !/^https?:\/\//i.test(s));
  if (left.length) throw new Error(`còn src ảnh local sau khi thay: ${left.slice(0, 5).join(', ')}`);
  return { html: out, files, uploaded };
}

/** So các field đã ghi với bản đọc lại; trả danh sách lệch. Thân bài so từng byte. */
export function verifyFields(after, expect) {
  const bad = [];
  for (const [k, want] of Object.entries(expect)) {
    if (want === undefined) continue;
    const got = k === 'body' ? bodyOf(after) : k === 'url' ? slugOf(after) : after[k];
    if (String(got ?? '') !== String(want ?? '')) bad.push(`${k}: muốn ${JSON.stringify(String(want).slice(0, 80))}, server ${JSON.stringify(String(got ?? '').slice(0, 80))}`);
  }
  return bad;
}

export { articleKind };
