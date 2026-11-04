#!/usr/bin/env node
/*
 * hoidap-body-tools.mjs — xử lý file LOCAL quanh lượt air bài Hỏi Đáp. Không gọi mạng.
 *
 *   node hoidap-body-tools.mjs replace --html final-content.html --map upload-map.json --out final-content-cms.html
 *       Thay src="images-processed/{file}" bằng URL CDN trả về từ hdUploadImages.
 *       Assert: mọi ảnh local đều có URL, thay ngược lại ra đúng file gốc từng byte.
 *
 *   node hoidap-body-tools.mjs split-backup --json dry-or-run-result.json --dir data/raw/cms-backup/{newsId}
 *       Tách `backup` trong kết quả hdWriteArticle thành before.html / page.html / fields.json.
 *
 *   node hoidap-body-tools.mjs diff --before before.html --after final-content-cms.html
 *       Tóm tắt diff cho user duyệt: độ dài, số ảnh/link/heading, heading thêm/bớt, ảnh thêm/bớt.
 */
import fs from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const cmd = args[0];
const opt = k => { const i = args.indexOf('--' + k); return i > 0 ? args[i + 1] : null; };
const need = k => { const v = opt(k); if (!v) { console.error(`thiếu --${k}`); process.exit(2); } return v; };
const die = (msg, extra) => { console.error(JSON.stringify({ status: 'ABORT', reason: msg, ...extra }, null, 1)); process.exit(1); };

const strip = s => s.replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
const headings = h => [...h.matchAll(/<(h[1-6])\b[^>]*>([\s\S]*?)<\/\1>/gi)].map(m => `${m[1].toLowerCase()}: ${strip(m[2])}`);
const imgFiles = h => [...h.matchAll(/<img\b[^>]*?\bsrc=["']([^"']+)["']/gi)].map(m => m[1].split('/').pop());

if (cmd === 'replace') {
  const htmlPath = need('html'), mapPath = need('map'), out = need('out');
  const src = fs.readFileSync(htmlPath, 'utf8');
  let map = JSON.parse(fs.readFileSync(mapPath, 'utf8'));
  if (map.uploaded) map = map.uploaded;                     // nhận thẳng kết quả hdUploadImages
  const locals = [...new Set([...src.matchAll(/src=(["'])images-processed\/([^"']+)\1/g)].map(m => m[2]))];
  const missing = locals.filter(n => !map[n]);
  if (missing.length) die('ảnh local chưa có URL CDN — upload chưa xong', { missing });
  let out1 = src;
  for (const n of locals) out1 = out1.split(`images-processed/${n}`).join(map[n]);
  let back = out1;
  for (const n of locals) back = back.split(map[n]).join(`images-processed/${n}`);
  if (back !== src) die('thay ngược không ra file gốc — URL CDN trùng chuỗi có sẵn trong bài, kiểm tay');
  if (/images-processed\//.test(out1)) die('vẫn còn chuỗi images-processed/ sau khi thay');
  fs.writeFileSync(out, out1);
  console.log(JSON.stringify({ status: 'OK', replaced: locals.length, out, lenBefore: src.length, lenAfter: out1.length }, null, 1));
} else if (cmd === 'split-backup') {
  const j = JSON.parse(fs.readFileSync(need('json'), 'utf8'));
  const b = j.backup || j;
  if (!b || typeof b.content_FaqNews_DB !== 'string') die('không thấy backup.content_FaqNews_DB trong file');
  const dir = need('dir');
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'before.html'), b.content_FaqNews_DB);
  if (b.fullPageHtml) fs.writeFileSync(path.join(dir, 'page.html'), b.fullPageHtml);
  fs.writeFileSync(path.join(dir, 'fields.json'), JSON.stringify({ newsId: b.newsId, at: b.at, cates: b.cates, fields: b.fields }, null, 1));
  console.log(JSON.stringify({ status: 'OK', dir, bodyLen: b.content_FaqNews_DB.length, pageLen: (b.fullPageHtml || '').length }, null, 1));
} else if (cmd === 'diff') {
  const a = fs.readFileSync(need('before'), 'utf8'), b = fs.readFileSync(need('after'), 'utf8');
  const ha = headings(a), hb = headings(b), ia = imgFiles(a), ib = imgFiles(b);
  const count = (h, re) => (h.match(re) || []).length;
  console.log(JSON.stringify({
    len: [a.length, b.length],
    imgs: [ia.length, ib.length], links: [count(a, /<a\s/gi), count(b, /<a\s/gi)],
    shortcodes: [count(a, /\[[A-Z][A-Za-z_]+ /g), count(b, /\[[A-Z][A-Za-z_]+ /g)],
    headingsRemoved: ha.filter(x => !hb.includes(x)), headingsAdded: hb.filter(x => !ha.includes(x)),
    imgsRemoved: ia.filter(x => !ib.includes(x)), imgsAdded: ib.filter(x => !ia.includes(x)),
  }, null, 1));
} else {
  console.error('dùng: replace | split-backup | diff (xem đầu file)');
  process.exit(2);
}
