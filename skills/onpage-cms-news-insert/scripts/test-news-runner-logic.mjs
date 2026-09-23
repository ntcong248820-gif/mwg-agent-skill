/**
 * Regression test cho logic lõi của cms-news-bulk-insert-runner.js.
 * Chạy: node scripts/test-news-runner-logic.mjs (không cần mạng, không đụng CMS)
 *
 * Test toàn bộ phần thuần logic: định vị đoạn có entity/span, bọc anchor dài trước ngắn sau,
 * splice raw string, 6 bất biến, chống chèn đúp, cấm heading, báo lỗi anchor.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ENT = { nbsp: ' ', amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
const decode = (s) =>
  String(s)
    .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_, d) => String.fromCodePoint(+d))
    .replace(/&([a-z]+);/gi, (m, n) => (n.toLowerCase() in ENT ? ENT[n.toLowerCase()] : m));

globalThis.document = {
  createElement: () => ({
    set innerHTML(v) { this._v = decode(v); },
    get value() { return this._v; },
  }),
};

const HERE = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(HERE, 'cms-news-bulk-insert-runner.js'), 'utf8')
  .replace(/if \(typeof window[\s\S]*$/, '');

const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(src + '\nexport { locate, wrapAnchors, checkInvariants, scanBlocks, norm };').toString('base64')
);
const { locate, wrapAnchors, checkInvariants, norm } = mod;

let pass = 0, fail = 0;
const t = (name, cond, extra) => {
  if (cond) {
    pass++;
    console.log('  ok  ', name);
  } else {
    fail++;
    console.log('  FAIL', name, extra ?? '');
  }
};

// Mẫu HTML bài Tin tức thực tế: có ảnh CDN, shortcode, thẻ lồng &nbsp; và link có sẵn
const before =
  '<p style="text-align: justify;"><img alt="banner" src="https://cdnv2.tgdd.vn/mwg-static/common/News/0/iphone-18-banner.jpg" /></p>\n\n' +
  '<h3 style="text-align: justify;">1. Ưu đãi đặt trước iPhone 18 tại Thế Giới Di Động</h3>\n\n' +
  '<p style="text-align: justify;">Khách hàng tham gia đặt trước <span style="font-weight: bold;">iPhone 18&nbsp;series</span> ' +
  'sẽ nhận được nhiều khuyến mãi hấp dẫn từ <a href="https://www.thegioididong.com/tin-tuc/khuyen-mai" title="Khuyến mãi">hệ thống</a> trong tháng 9.</p>\n\n' +
  '<p>Chi tiết chương trình áp dụng trên toàn quốc cho mọi khách hàng mua sắm trực tuyến hoặc tại siêu thị.</p>';

const oldText = 'Khách hàng tham gia đặt trước iPhone 18 series sẽ nhận được nhiều khuyến mãi hấp dẫn từ hệ thống trong tháng 9.';
const sentence = 'Người dùng quan tâm có thể xem thông số của iPhone 18 Pro Max và đặt cọc iPhone 18 Pro sớm để nhận suất giao máy đợt đầu.';
const links = [
  { anchor: 'iPhone 18 Pro Max', href: 'https://www.thegioididong.com/dtdd/iphone-18-pro-max', title: 'iPhone 18 Pro Max' },
  { anchor: 'iPhone 18 Pro', href: 'https://www.thegioididong.com/dtdd/iphone-18-pro', title: 'iPhone 18 Pro' },
];

console.log('\n[1] Định vị đoạn văn');
const hit = locate(before, oldText);
t('Khớp đúng duy nhất 1 đoạn <p> dù có span lồng và &nbsp;', hit.ok && hit.block.tag === 'p', hit.reason);

console.log('\n[2] Bọc anchor dài trước ngắn sau');
const wrapped = wrapAnchors(sentence, links);
t('Không bị lỗi link lồng nhau', !/<a[^>]*>[^<]*<a/.test(wrapped));
t('Đủ 2 thẻ <a', (wrapped.match(/<a /g) || []).length === 2, wrapped);
t('Anchor dài không bị anchor ngắn cắt xén', wrapped.includes('>iPhone 18 Pro Max</a>') && wrapped.includes('>iPhone 18 Pro</a>'));
t('Có đầy đủ thuộc tính target="_blank" rel="noopener"', (wrapped.match(/target="_blank" rel="noopener"/g) || []).length === 2);

console.log('\n[3] Splice và kiểm tra 6 bất biến');
const insert = ' ' + wrapped;
const after = before.slice(0, hit.block.insertAt) + insert + before.slice(hit.block.insertAt);
const inv = checkInvariants({
  before,
  after,
  insert,
  nLinks: 2,
  block: hit.block,
  oldText,
  plainSentence: sentence,
  sep: ' ',
});
for (const [k, v] of Object.entries(inv)) {
  t(`Bất biến: ${k}`, v === true);
}
t('Link cũ "hệ thống" trong đoạn được bảo toàn 100%', after.includes('<a href="https://www.thegioididong.com/tin-tuc/khuyen-mai" title="Khuyến mãi">hệ thống</a>'));
t('Ảnh CDN được giữ nguyên 100%', after.includes('src="https://cdnv2.tgdd.vn/mwg-static/common/News/0/iphone-18-banner.jpg"'));

console.log('\n[4] Cơ chế chống chèn đúp lần 2');
const twice = locate(after, oldText);
t('Chạy lại trên bài đã chèn -> tự động bỏ qua (không ghi lặp)', !twice.ok, twice.reason);
t('Chẩn đoán chính xác lý do: "đoạn đã được chèn ở lần chạy trước"', twice.already === true && twice.reason === 'đoạn đã được chèn ở lần chạy trước');

console.log('\n[5] Chặn chèn vào heading');
const h3 = locate(before, '1. Ưu đãi đặt trước iPhone 18 tại Thế Giới Di Động');
t('Phát hiện đoạn khớp là <h3> và từ chối chèn', !h3.ok && h3.tag === 'h3', h3.reason);

console.log('\n[6] Xử lý đoạn không tồn tại');
const missing = locate(before, 'Nội dung này hoàn toàn không có trong bài viết.');
t('Báo match 0 và trả về similarity thấp', !missing.ok && !missing.already && missing.nearest[0].sim < 0.3, JSON.stringify(missing.nearest?.[0]));

console.log('\n[7] Kiểm tra validation anchor');
t('Báo lỗi khi anchor khai báo không có trong câu chèn', (() => {
  try {
    wrapAnchors('Câu này không có từ khoá cần link', links);
    return false;
  } catch {
    return true;
  }
})());
t('Báo lỗi khi anchor xuất hiện nhiều hơn 1 lần trong câu', (() => {
  try {
    wrapAnchors('Xem iPhone 18 Pro Max và iPhone 18 Pro Max màu mới', [links[0]]);
    return false;
  } catch {
    return true;
  }
})());

console.log(`\n=== Kết quả: PASS ${pass} / FAIL ${fail} ===`);
process.exit(fail ? 1 : 0);
