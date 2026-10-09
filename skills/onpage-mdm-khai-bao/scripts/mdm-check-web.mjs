/**
 * mdm-check-web.mjs — so giá trị SEO trong MDM với trang core mới (chỉ đọc), dùng cho `lookup --check-web`.
 *
 * Title/mô tả so tuyệt đối sau giải entity (MDM lưu y nguyên byte). Infobox so 3 mảnh chữ lấy từ 3 khối
 * khác nhau của bài MDM (core mới dựng lại HTML infobox nên không so byte). Trang Hãng+Filter: web thay
 * `[HÃNG]` bằng tên hãng nên kỳ vọng cũng thay. Chỉ tính lượt có `x-app-server` core mới; không đo được
 * lượt nào thì báo KHONG_DO_DUOC chứ không đọc thành "khớp".
 */
import { rawGet } from './mdm-core.mjs';
import { fetchCoreMoi, extractTitle, extractMetaDescription, bodyText, squash } from './mdm-web-verify.mjs';

/** Giá trị SEO MDM đang giữ cho kiểu trang này (đã thay [HÃNG] nếu là Hãng+Filter). */
export function expectedFromRaw(fields, rawValues, brandName) {
  const sub = (v) => (typeof v === 'string' && brandName ? v.replaceAll('[HÃNG]', brandName) : v);
  const get = (k) => {
    const v = rawGet(rawValues, k);
    return typeof v === 'string' && v !== '' ? v : null;
  };
  return {
    title: sub(get(fields.title)),
    description: sub(get(fields.description)),
    article: get(fields.article),
  };
}

/** 3 mảnh chữ (≤60 ký tự) từ 3 khối khác nhau của bài MDM; bài ngắn thì lấy cả bài. */
export function articleFragments(html) {
  const blocks = String(html).split(/<\/(?:p|h[1-6]|li|td)>/i).map((b) => bodyText(b)).filter((b) => b.length >= 60);
  if (!blocks.length) {
    const all = bodyText(html);
    return all ? [all.slice(0, 60)] : [];
  }
  const pick = [0.2, 0.5, 0.8].map((q) => blocks[Math.min(blocks.length - 1, Math.floor(q * blocks.length))]);
  return [...new Set(pick)].map((b) => b.slice(0, 60));
}

/** So 1 trang HTML với giá trị MDM kỳ vọng. Trả mỗi field: {status, mdm, web}. */
export function compareWeb(html, expected) {
  const out = {};
  const text = bodyText(html);
  const cmp = (key, web) => {
    const mdm = expected[key];
    if (mdm == null) return { status: 'MDM_TRONG', web };
    return { status: web === mdm ? 'KHOP' : 'LECH', mdm, web };
  };
  out.title = cmp('title', extractTitle(html));
  out.description = cmp('description', extractMetaDescription(html));
  if (expected.article == null) {
    out.article = { status: 'MDM_TRONG' };
  } else {
    const frags = articleFragments(expected.article);
    const found = frags.filter((f) => text.includes(squash(f))).length;
    out.article = { status: found === frags.length ? 'KHOP' : 'LECH', mdmLen: expected.article.length, fragments: frags.length, found };
  }
  return out;
}

/** Đo `samples` lượt core mới (lấy lại tối đa `tries` lần khi rơi node core cũ), gom verdict. */
export async function checkWeb(url, expected, { fetchFn, samples = 3, tries = 8, sleepFn } = {}) {
  const sleep = sleepFn || ((ms) => new Promise((r) => setTimeout(r, ms)));
  const runs = [];
  let attempts = 0;
  while (runs.length < samples && attempts < tries) {
    attempts++;
    let r;
    try { r = await fetchCoreMoi(url, fetchFn); } catch { r = null; }
    if (r && r.status === 200 && r.coreMoi) runs.push(compareWeb(r.html, expected));
    else await sleep(1000);
  }
  if (!runs.length) return { verdict: 'KHONG_DO_DUOC', samples: 0, attempts, note: 'không lượt nào vào core mới (x-app-server webfe, HTTP 200)' };
  const fields = {};
  let anyLech = false;
  for (const k of ['title', 'description', 'article']) {
    const statuses = runs.map((x) => x[k].status);
    const status = statuses.every((s) => s === statuses[0]) ? statuses[0] : 'CHAP_CHON';
    fields[k] = { ...runs[0][k], status, perSample: statuses };
    if (status === 'LECH' || status === 'CHAP_CHON') anyLech = true;
  }
  return { verdict: anyLech ? 'LECH' : 'KHOP', samples: runs.length, attempts, fields };
}
