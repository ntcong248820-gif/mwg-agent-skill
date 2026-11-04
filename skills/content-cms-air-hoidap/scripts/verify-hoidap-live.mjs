#!/usr/bin/env node
/*
 * verify-hoidap-live.mjs — nghiệm thu trang Hỏi Đáp LIVE sau khi ghi CMS.
 *
 *   node verify-hoidap-live.mjs --url https://www.thegioididong.com/hoi-dap/{slug}-{id} \
 *        --html final-content-cms.html [--old before.html] [--title "H1 mới"] [--meta-title "..."] [--clearcache]
 *
 * --clearcache: gọi {url}?clearcache=1 trước rồi mới đọc URL trơn. CHỈ dùng khi đã
 *               qua ~60 giây kể từ lúc ghi CMS — gọi sớm là đóng băng bài cũ vào cache.
 * Đọc URL trơn (thứ người dùng thật thấy), đếm heading + tên file ảnh khớp bản gửi lên,
 * và (nếu có --old) heading của bản cũ còn sót.
 */
import fs from 'node:fs';

const args = process.argv.slice(2);
const opt = k => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : null; };
const has = k => args.includes('--' + k);
const url = opt('url'), htmlPath = opt('html');
if (!url || !htmlPath) { console.error('cần --url và --html'); process.exit(2); }

// Trang live encode lại ký tự Latin-1 thành named entity (&ecirc; &aacute; &otilde;...)
// dù DB lưu ký tự thô — nên phải decode cả hai phía trước khi so text.
const NAMED = { nbsp: 160, quot: 34, amp: 38, lt: 60, gt: 62, apos: 39, ndash: 8211, mdash: 8212, lsquo: 8216, rsquo: 8217,
  ldquo: 8220, rdquo: 8221, hellip: 8230, laquo: 171, raquo: 187, deg: 176, times: 215, copy: 169, reg: 174, trade: 8482 };
const L1 = { grave: [0xC0, 0xC8, 0xCC, 0xD2, 0xD9], acute: [0xC1, 0xC9, 0xCD, 0xD3, 0xDA, 0xDD], circ: [0xC2, 0xCA, 0xCE, 0xD4, 0xDB], tilde: [0xC3, null, null, 0xD5, null] };
const VOW = { grave: 'AEIOU', acute: 'AEIOUY', circ: 'AEIOU', tilde: 'AEIOU' };
for (const [k, codes] of Object.entries(L1)) codes.forEach((c, i) => { if (c) { NAMED[VOW[k][i] + k] = c; NAMED[VOW[k][i].toLowerCase() + k] = c + 32; } });
NAMED.Ntilde = 0xD1; NAMED.ntilde = 0xF1;
const decode = s => s.replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n)).replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
  .replace(/&([A-Za-z]+);/g, (m, n) => (NAMED[n] ? String.fromCodePoint(NAMED[n]) : m));
const text = s => decode(s.replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').trim();
const heads = h => [...h.matchAll(/<(h[2-4])\b[^>]*>([\s\S]*?)<\/\1>/gi)].map(m => text(m[2])).filter(Boolean);
const imgs = h => [...new Set([...h.matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map(m => m[1].split('/').pop()))];
const UA = { headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh) verify-hoidap-live' } };

const mine = fs.readFileSync(htmlPath, 'utf8');
const old = opt('old') ? fs.readFileSync(opt('old'), 'utf8') : null;

if (has('clearcache')) {
  const r = await fetch(url + (url.includes('?') ? '&' : '?') + 'clearcache=1', UA);
  await r.text();
}
const res = await fetch(url, UA);
const live = await res.text();
const liveText = text(live);
const liveH = heads(live);
const h1 = (live.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i) || [])[1];
const titleTag = (live.match(/<title>([\s\S]*?)<\/title>/i) || [])[1];

const myHeads = heads(mine), myImgs = imgs(mine);
const oldOnly = old ? heads(old).filter(x => !myHeads.includes(x)) : [];
const out = {
  url, http: res.status, cache: res.headers.get('x-cache-status') || res.headers.get('x-cache') || null,
  h1: h1 ? text(h1) : null, titleTag: titleTag ? text(titleTag) : null,
  h1Ok: opt('title') ? (h1 && text(h1) === opt('title')) : undefined,
  titleOk: opt('meta-title') ? (titleTag && text(titleTag).startsWith(opt('meta-title'))) : undefined,
  headings: `${myHeads.filter(x => liveText.includes(x)).length}/${myHeads.length}`,
  headingsMissing: myHeads.filter(x => !liveText.includes(x)).slice(0, 10),
  images: `${myImgs.filter(n => live.includes(n)).length}/${myImgs.length}`,
  imagesMissing: myImgs.filter(n => !live.includes(n)),
  // Chỉ dò trong thẻ heading live: shortcode khuyến mãi render tên SP động, dò full text báo giả.
  // Heading cũ là chuỗi con của heading mới (vd "MacBook Neo 13 inch A18 Pro" ⊂ "... 8GB/256GB") thì không tính.
  oldHeadingsStillLive: old ? oldOnly.filter(x => liveH.some(h => h.includes(x)) && !myHeads.some(m => m.includes(x))).slice(0, 10) : undefined,
};
out.pass = out.http === 200 && out.headingsMissing.length === 0 && out.imagesMissing.length === 0
  && out.h1Ok !== false && out.titleOk !== false && (!old || out.oldHeadingsStillLive.length === 0);
console.log(JSON.stringify(out, null, 1));
process.exit(out.pass ? 0 : 1);
