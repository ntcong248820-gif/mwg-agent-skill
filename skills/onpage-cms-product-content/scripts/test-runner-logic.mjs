/**
 * Regression test cho logic lõi của cms-bulk-insert-runner.js.
 * Chạy: node scripts/test-runner-logic.mjs   (không cần mạng, không đụng CMS)
 *
 * Chỉ test phần thuần logic: định vị, bọc anchor, splice, 6 bất biến, chẩn đoán
 * skip. Phần fetch/POST phải test trên CMS thật bằng dryRun.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ENT = { nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
const decode = (s) =>
  String(s)
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENT ? ENT[n.toLowerCase()] : m));

globalThis.document = {
  createElement: () => ({ set innerHTML(v) { this._v = decode(v); }, get value() { return this._v; } }),
};

const HERE = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(HERE, 'cms-bulk-insert-runner.js'), 'utf8')
  .replace(/if \(typeof window[\s\S]*$/, '');

const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(src + '\nexport { locate, wrapAnchors, checkInvariants, scanBlocks, norm, diffFields };').toString('base64')
);
const { locate, wrapAnchors, checkInvariants, norm, diffFields } = mod;

let pass = 0, fail = 0;
const t = (name, cond, extra) => {
  if (cond) { pass++; console.log('  ok  ', name); }
  else { fail++; console.log('  FAIL', name, extra ?? ''); }
};

// Đoạn thật: markup lồng + &nbsp; + đã có <a> sẵn, giống bài CMS.
const before =
  '<p style="text-align: justify;"><img alt="x" src="https://cdn/a.jpg" /></p>\n\n' +
  '<h3 style="text-align: justify;">Tiêu đề phụ của bài</h3>\n\n' +
  '<p style="text-align: justify;">iPhone 15 Plus<span style="color:#111">&nbsp;256 GB</span> ' +
  'được <a href="https://x.vn/a" title="t">nhiều người</a> chọn mua trong năm nay.</p>\n\n' +
  '<p>Đoạn khác hoàn toàn, không liên quan gì.</p>';

const oldText = 'iPhone 15 Plus 256 GB được nhiều người chọn mua trong năm nay.';
const sentence = 'Năm nay bạn có thể tham khảo thêm iPhone 18 Pro Max và iPhone 18 Pro bên cạnh iPhone 18.';
const links = [
  { anchor: 'iPhone 18', href: 'https://www.thegioididong.com/dtdd-apple-iphone-18-series' },
  { anchor: 'iPhone 18 Pro', href: 'https://www.thegioididong.com/dtdd/iphone-18-pro' },
  { anchor: 'iPhone 18 Pro Max', href: 'https://www.thegioididong.com/dtdd/iphone-18-pro-max' },
];

console.log('\n[1] định vị');
const hit = locate(before, oldText);
t('khớp đúng 1 đoạn <p> dù có markup lồng + &nbsp;', hit.ok && hit.block.tag === 'p', hit.reason);

console.log('\n[2] bọc anchor dài trước ngắn sau');
const wrapped = wrapAnchors(sentence, links);
t('không có <a> lồng nhau', !/<a[^>]*>[^<]*<a/.test(wrapped));
t('đủ 3 thẻ <a', (wrapped.match(/<a /g) || []).length === 3, wrapped);
t('anchor dài không bị cắt', wrapped.includes('>iPhone 18 Pro Max</a>') && wrapped.includes('>iPhone 18 Pro</a>') && wrapped.includes('>iPhone 18</a>'));
t('có target/rel chuẩn', (wrapped.match(/target="_blank" rel="noopener"/g) || []).length === 3);

console.log('\n[3] splice + 6 bất biến');
const insert = ' ' + wrapped;
const after = before.slice(0, hit.block.insertAt) + insert + before.slice(hit.block.insertAt);
const inv = checkInvariants({ before, after, insert, nLinks: 3, block: hit.block, oldText, plainSentence: sentence, sep: ' ' });
for (const [k, v] of Object.entries(inv)) t(k, v === true);
t('link cũ trong đoạn còn nguyên', after.includes('<a href="https://x.vn/a" title="t">nhiều người</a>'));
t('ảnh còn nguyên', after.includes('src="https://cdn/a.jpg"'));

console.log('\n[4] chống chèn 2 lần');
const twice = locate(after, oldText, sentence);
t('chạy lại trên bài đã chèn → không ghi lại', !twice.ok, twice.reason);
t('nhận đúng là "đã chèn ở lần chạy trước"', twice.already === true && twice.reason === 'đoạn đã được chèn ở lần chạy trước', twice.reason);
t('không truyền sentence → KHÔNG tự nhận là đã chèn (tránh ALREADY giả)', locate(after, oldText).already !== true);

console.log('\n[4b] oldText chỉ là câu đầu của đoạn dài hơn — KHÔNG phải đã chèn');
const longPara = '<p>iPhone 15 Plus 256 GB được nhiều người chọn mua trong năm nay. Máy còn có pin trâu và camera tốt.</p>';
const truncated = locate(longPara, oldText, sentence);
t('KHÔNG bị nhận nhầm là "đã chèn ở lần chạy trước" (false ALREADY)', !truncated.already, JSON.stringify(truncated));
t('lý do đúng: oldText chỉ là phần đầu của đoạn', truncated.reason === 'oldText chỉ là phần đầu của đoạn — cần nguyên đoạn', truncated.reason);

console.log('\n[4c] finding #5: đã chèn nhưng link SAI (href khác lần khai báo hiện tại) — không phải ALREADY');
const rightLinksCheck = locate(after, oldText, sentence, links);
t('truyền đúng links khớp lần chèn trước → ALREADY (không alreadyMismatch)', rightLinksCheck.already === true && !rightLinksCheck.alreadyMismatch, JSON.stringify(rightLinksCheck));
const wrongHrefLinks = [
  { anchor: 'iPhone 18', href: 'https://www.thegioididong.com/dtdd-apple-iphone-18-series' },
  { anchor: 'iPhone 18 Pro', href: 'https://SAI-HREF' },
  { anchor: 'iPhone 18 Pro Max', href: 'https://www.thegioididong.com/dtdd/iphone-18-pro-max' },
];
const wrongHrefCheck = locate(after, oldText, sentence, wrongHrefLinks);
t('href sai (1/3 link) → alreadyMismatch, KHÔNG phải already', wrongHrefCheck.alreadyMismatch === true && !wrongHrefCheck.already, JSON.stringify(wrongHrefCheck));
t('reason đúng: "đã chèn nhưng link khác"', wrongHrefCheck.reason === 'đã chèn nhưng link khác', wrongHrefCheck.reason);
t('không truyền links (undefined) → giữ hành vi cũ, vẫn ALREADY (tương thích ngược)', locate(after, oldText, sentence).already === true);

console.log('\n[4d] finding #4: diffFields() so field tĩnh trước/sau, bỏ qua field cho phép đổi');
const beforeFields = [{ name: 'txtSeoTitle', value: 'A' }, { name: 'hdType', value: '6' }, { name: 'txtContent', value: 'body cũ' }];
const afterFieldsSame = [{ name: 'txtSeoTitle', value: 'A' }, { name: 'hdType', value: '2' }, { name: 'txtContent', value: 'body mới' }];
t('txtContent/hdType đổi (whitelist) -> không tính là field khác', diffFields(beforeFields, afterFieldsSame, new Set(['txtContent', 'hdType'])).length === 0);
const afterFieldsDrift = [{ name: 'txtSeoTitle', value: 'BỊ ĐỔI' }, { name: 'hdType', value: '2' }, { name: 'txtContent', value: 'body mới' }];
t('field ngoài whitelist đổi -> liệt kê đúng tên', JSON.stringify(diffFields(beforeFields, afterFieldsDrift, new Set(['txtContent', 'hdType']))) === JSON.stringify(['txtSeoTitle']));

console.log('\n[5] đoạn là heading');
const h3 = locate(before, 'Tiêu đề phụ của bài');
t('phát hiện <h3>, không ghi', !h3.ok && h3.tag === 'h3', h3.reason);

console.log('\n[6] đoạn không tồn tại trong bài');
const gone = locate(before, 'Phụ kiện tablet Apple được thiết kế đồng bộ với hệ sinh thái.');
t('báo 0 match với similarity thấp', !gone.ok && !gone.already && gone.nearest[0].sim < 0.4, JSON.stringify(gone.nearest?.[0]));

console.log('\n[7] anchor lỗi phải ném lỗi, không ghi bừa');
t('anchor không có trong câu', (() => { try { wrapAnchors('câu không chứa gì', links); return false; } catch { return true; } })());
t('anchor lặp 2 lần', (() => { try { wrapAnchors('iPhone 18 và iPhone 18 nữa', [links[0]]); return false; } catch { return true; } })());

console.log(`\n=== pass ${pass} / fail ${fail} ===`);
process.exit(fail ? 1 : 0);
