/**
 * cms-blog-lint.mjs — luật khai báo bài Hỏi Đáp / Game App trước khi ghi NEW CMS. Port từ tao_bai.mjs
 * (cms-content-create) — hàm thuần, không gọi mạng trừ HEAD ảnh, để test được.
 */

import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const OPTIONS = JSON.parse(fs.readFileSync(path.join(HERE, '..', 'references', 'cms-options.json'), 'utf8'));

export const TYPES = {
  'hoi-dap': { maxTitle: 70, maxUrl: 84, bodyField: 'description', categoryId: 1226, live: (url, id) => `https://www.thegioididong.com/hoi-dap/${url}-${id}` },
  'game-app': { maxTitle: 130, maxUrl: 92, bodyField: 'content', categoryId: 2002, live: (url, id) => `https://www.thegioididong.com/game-app/${url}-${id}` },
};

/** Loại bài từ bản ghi newsselect. */
export function articleKind(rec) {
  return rec?.isGameApp === 1 || String(rec?.listCategoryId ?? '').split(',').includes('2002') ? 'game-app' : 'hoi-dap';
}

const slugRaw = (s) => s.toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
const NOI = new Set(['va', 'hay', 'hoac', 'cua', 'voi', 'cho', 'de', 'la', 'o', 'tai', 'trong', 'khi', 'nhu', 'thi', 'ma', 'co', 'cac', 'nhung', 'mot', 'lua']);
/** Slug từ tiêu đề, ≤ max; cắt ở ranh giới cụm (? , : - …) cho URL đọc có nghĩa, không kết thúc bằng từ nối. */
export function slugCms(s, max = 50) {
  const full = slugRaw(s);
  if (full.length <= max) return full;
  let acc = '';
  for (const c of s.split(/[?!,:;.\u2013\u2014()|]+|\s-\s/).map(slugRaw).filter(Boolean)) {
    const nx = acc ? `${acc}-${c}` : c;
    if (nx.length > max) break;
    acc = nx;
  }
  if (acc.split('-').length >= 3) return acc;
  let t = full.slice(0, max);
  t = full[max] === '-' ? t : t.slice(0, t.lastIndexOf('-'));
  const w = t.split('-');
  while (w.length > 3 && NOI.has(w[w.length - 1])) w.pop();
  return w.join('-');
}

const len = (s) => [...String(s)].length;
const pad = (n) => String(n).padStart(2, '0');
export const todayVN = (d = new Date()) => `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;

/** "dd/mm/yyyy" + "HH:MM" → "YYYY-MM-DDTHH:MM:00" (giờ máy), null nếu sai. */
export function toCmsDate(ddmmyyyy, hhmm = '02:00') {
  const m = String(ddmmyyyy).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  const t = String(hhmm).match(/^(\d{1,2}):(\d{2})$/);
  if (!m || !t) return null;
  const d = new Date(+m[3], +m[2] - 1, +m[1], +t[1], +t[2]);
  if (d.getDate() !== +m[1]) return null;
  return `${m[3]}-${m[2]}-${m[1]}T${pad(t[1])}:${t[2]}:00`;
}

/** Ảnh local (src không phải http) trong HTML. */
export const localImgs = (html) => [...String(html).matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map((m) => m[1]).filter((s) => !/^https?:\/\//i.test(s));

/** Kiểm thân bài — dùng chung cho create/update. */
export async function lintContent(html, { fetchFn = fetch, checkRemote = true } = {}) {
  const err = [], warn = [];
  if (!html) { err.push('thân bài rỗng'); return { err, warn }; }
  if (/<(html|body|head)\b/i.test(html)) err.push('thân bài không được có <html>/<body>/<head>');
  const plain = html.replace(/<[^>]+>/g, ' ');
  const old = [...plain.matchAll(/cập nhật (?:vào )?(?:ngày )?(\d{1,2}\/\d{1,2}\/\d{4})/gi)].map((m) => m[1]).filter((d) => d !== todayVN());
  if (old.length) err.push(`ngày "cập nhật" chưa phải hôm nay ${todayVN()}: ${[...new Set(old)].join(', ')}`);
  if (/thiết bị/i.test(plain)) warn.push('có chữ "thiết bị": iPhone/sản phẩm TGDĐ gọi "sản phẩm"/"máy"');
  if (/<p[^>]*>\s*(?:[-•]|&bull;)\s/i.test(html)) warn.push('có <p> bắt đầu bằng "-"/"•": bullet phải là <ul><li>');
  if (/đặt trước|đặt cọc|tin đồn|rò rỉ/i.test(plain)) warn.push('có từ đặt trước/đặt cọc/tin đồn/rò rỉ, kiểm lại');
  for (const m of html.matchAll(/<img\b[^>]*>/g)) if (!/\balt="[^"]+"/.test(m[0])) warn.push(`ảnh thiếu alt: ${m[0].slice(0, 100)}`);
  if (checkRemote) {
    const remote = [...html.matchAll(/<img\b[^>]*?\bsrc=["'](https?:\/\/[^"']+)["']/gi)].map((m) => m[1]);
    const bad = [];
    for (const u of [...new Set(remote)]) {
      try { const r = await fetchFn(u, { method: 'HEAD' }); if (r.status !== 200) bad.push(`${r.status} ${u}`); } catch { bad.push(`ERR ${u}`); }
    }
    if (bad.length) err.push(`ảnh lỗi trong bài:\n    ${bad.join('\n    ')}`);
  }
  return { err, warn };
}

/**
 * Chuẩn hoá + kiểm form.json tạo bài (schema của cms-content-create, thêm khoá game-app).
 * Trả { v, err, warn } — v là giá trị đã chuẩn hoá, đường dẫn đã resolve theo thư mục form.
 */
export function normalizeForm(f, { kind, baseDir, now = new Date() }) {
  const T = TYPES[kind];
  if (!T) throw new Error(`type "${kind}" không hợp lệ (hoi-dap | game-app)`);
  const abs = (p) => (p ? path.resolve(baseDir, String(p).replace(/^~(?=\/)/, process.env.HOME)) : '');
  const v = {
    kind,
    keyword: String(f.keyword || '').trim(),
    title: String(f.title || '').trim(),
    url: String(f.url || '').trim() || slugCms(f.title || ''),
    thumb: abs(f.thumb),
    thumbUrl: String(f.thumb_url || '').trim(),
    child: String(f.child_category ?? (kind === 'hoi-dap' ? '2023' : '')),
    parent: String(f.parent_category ?? ''),
    articleType: f.article_type || (kind === 'hoi-dap' ? 'Tư vấn chọn mua' : ''),
    productRelated: String(f.product_related || '').replace(/\s+/g, ''),
    metaTitle: String(f.meta_title || f.title || '').trim(),
    metaDesc: String(f.meta_desc || '').trim(),
    tags: (f.tags || []).map((t) => String(t).trim().toLowerCase()).filter(Boolean),
    contentFile: abs(f.content_file),
    imagesDir: abs(f.images_dir) || (f.content_file ? path.dirname(abs(f.content_file)) : baseDir),
    schema: f.schema || '',
    hideBannerVccorp: f.hide_banner_vccorp ? 1 : 0,
    publishDate: String(f.publish_date || '').trim(),
    publishTime: String(f.publish_time || '02:00').trim(),
    status: f.status || '',
    // game-app
    isGame: f.is_game === undefined ? 1 : +!!f.is_game,
    formGameApp: String(f.form_game_app || '').trim(),
    platforms: String(f.platforms || '').replace(/\s+/g, ''),
  };
  const err = [], warn = [];
  // trạng thái: publish_date có ngày → Xuất bản hẹn giờ; trống → Chờ duyệt (luật owner 24/10/2026)
  if (!v.status) v.status = v.publishDate ? 'actived' : 'pending';
  if (!['draft', 'pending', 'approved', 'actived'].includes(v.status)) err.push(`status "${v.status}" không hợp lệ`);
  if (v.publishDate) {
    v.activedDate = toCmsDate(v.publishDate, v.publishTime);
    if (!v.activedDate) err.push(`publish_date "${v.publishDate}" / publish_time "${v.publishTime}" phải dạng dd/mm/yyyy HH:MM`);
    else {
      const d = new Date(v.activedDate);
      if (d < new Date(now.getFullYear(), now.getMonth(), now.getDate())) err.push(`ngày xuất bản ${v.publishDate} đã qua`);
      else if (d < now) warn.push(`${v.publishTime} ngày ${v.publishDate} đã qua, bài lên ngay khi lưu`);
    }
  }
  if (!v.keyword && kind === 'hoi-dap') err.push('thiếu keyword chính');
  if (!v.title) err.push('thiếu title'); else if (len(v.title) > T.maxTitle) err.push(`title ${len(v.title)} > ${T.maxTitle} ký tự`);
  if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(v.url)) err.push(`url "${v.url}" chỉ được a-z 0-9 và "-"`);
  if (v.url.length > T.maxUrl) err.push(`url ${v.url.length} > ${T.maxUrl} ký tự (hoi-dap/ hoặc game-app/ + url + -newsId phải ≤ 100)`);
  else if (kind === 'hoi-dap' && v.url.length > 54) warn.push(`url ${v.url.length} ký tự: NEW CMS nhận, nhưng CMS cũ chặn > 54 (đường --old-cms sẽ lỗi)`);
  else if (v.url.length > 50) warn.push(`url ${v.url.length} ký tự (CMS tự sinh tối đa 50)`);
  if (!v.metaTitle) err.push('thiếu meta title'); else if (len(v.metaTitle) > 70) err.push(`meta title ${len(v.metaTitle)} > 70`);
  if (!v.metaDesc) err.push('thiếu meta description');
  else if (len(v.metaDesc) > 170) err.push(`meta description ${len(v.metaDesc)} > 170`);
  else if (len(v.metaDesc) > 160) warn.push(`meta description ${len(v.metaDesc)} > 160 (khuyến cáo)`);
  if (kind === 'hoi-dap') {
    const cm = OPTIONS.chuyen_muc_con[v.child];
    if (!cm) err.push(`chuyên mục con ${v.child} không có trong CMS (xem lookup categories)`);
    else {
      if (!v.parent) v.parent = cm.cha[0] || '';
      if (!cm.cha.includes(v.parent)) err.push(`chuyên mục cha ${v.parent} không thuộc con ${v.child} (${cm.ten}); cha hợp lệ: ${cm.cha.join(', ')}`);
      v.childName = cm.ten;
    }
    if (!OPTIONS.dang_bai_viet.includes(v.articleType)) err.push(`dạng bài viết "${v.articleType}" không có trong CMS`);
    if (v.tags.length < 2 || v.tags.length > 5) err.push(`tags có ${v.tags.length}, cần 2-5`);
    if (v.keyword && !v.tags.includes(v.keyword.toLowerCase())) err.push('tags phải có keyword chính');
  } else {
    if (v.tags.length > 5) err.push(`tags có ${v.tags.length}, tối đa 5`);
    if (!v.formGameApp) err.push('thiếu form_game_app (Dạng bài Game App — xem lookup form-types)');
    if (!v.platforms) warn.push('chưa khai platforms (nền tảng) — xem lookup platforms');
    else if (!/^\d+(,\d+)*$/.test(v.platforms)) err.push('platforms phải là ID số, cách dấu phẩy');
    if (v.status === 'actived') v.status = 'approved'; // Game App: "approved" mang nhãn Xuất bản
  }
  if (v.productRelated && !/^\d+(,\d+)*$/.test(v.productRelated)) err.push('product_related phải là ID số, cách dấu phẩy');
  if (new Set(v.tags).size !== v.tags.length) err.push('tags bị lặp');
  if (v.tags.some((t) => /[,<>"]/.test(t))) err.push('tag không được chứa , < > "');
  if (!v.thumb && !v.thumbUrl) err.push('thiếu thumb (file) hoặc thumb_url');
  if (v.thumb) {
    if (!fs.existsSync(v.thumb)) err.push(`không thấy file thumb ${v.thumb}`);
    else {
      const dim = imageSize(v.thumb);
      const want = [560, 292]; // Hỏi Đáp và Game App cùng cỡ (đo bài thật 02/11/2026)
      if (dim && (dim.w !== want[0] || dim.h !== want[1])) warn.push(`thumb ${dim.w}x${dim.h}, CMS khuyến nghị ${want.join('x')}`);
      const kb = fs.statSync(v.thumb).size / 1024;
      if (kb > 300) warn.push(`thumb ${kb.toFixed(0)}KB, nên nén < 300KB`);
      if (!/^[a-z0-9]+(-[a-z0-9]+)*\.(jpe?g|png|webp)$/.test(path.basename(v.thumb))) warn.push(`tên thumb "${path.basename(v.thumb)}" nên kebab-case không dấu`);
    }
  } else if (v.thumbUrl && !/^https:\/\/cdnv2\.tgdd\.vn\//.test(v.thumbUrl)) err.push('thumb_url phải là cdnv2.tgdd.vn');
  if (!v.contentFile || !fs.existsSync(v.contentFile)) err.push(`không đọc được content_file ${v.contentFile}`);
  return { v, err, warn };
}

/** Kích thước ảnh bằng sips (macOS); null nếu không đọc được. */
export function imageSize(file) {
  try {
    const o = execFileSync('sips', ['-g', 'pixelWidth', '-g', 'pixelHeight', file], { encoding: 'utf8' });
    return { w: +(o.match(/pixelWidth: (\d+)/) || [])[1], h: +(o.match(/pixelHeight: (\d+)/) || [])[1] };
  } catch { return null; }
}

/** Đếm cấu trúc thân bài để so trước/sau. */
export function shape(html) {
  const c = (re) => (String(html).match(re) || []).length;
  return { h2: c(/<h2\b/gi), h3: c(/<h3\b/gi), p: c(/<p\b/gi), li: c(/<li\b/gi), a: c(/<a\b/gi), img: c(/<img\b/gi), table: c(/<table\b/gi), text_len: String(html).replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim().length };
}
