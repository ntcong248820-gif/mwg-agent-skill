/**
 * test-mdm-check-web.mjs — `lookup --check-web`: so MDM với core mới (fetch giả, không mạng).
 *
 *   node .claude/skills/onpage-mdm-khai-bao/scripts/test-mdm-check-web.mjs
 */
import { expectedFromRaw, articleFragments, compareWeb, checkWeb } from './mdm-check-web.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const R = (data) => [{ locale: 'all', data }];

const P = (n) => `Đoạn văn số ${n} nói về laptop gaming hiệu năng cao, tản nhiệt tốt và màn hình tần số quét lớn.`;
const ART = `<h2>${P(1)}</h2><p>${P(2)}</p><p>${P(3)}</p><p>${P(4)}</p><p>${P(5)}</p>`;
const FIELDS = { title: 'title_brand_filter', description: 'description_brand_filter', article: 'filter_inforbox' };
const RAW = { title_brand_filter: R('Laptop Gaming [HÃNG] giá tốt'), description_brand_filter: R('Mua Laptop [HÃNG] chính hãng'), filter_inforbox: R(ART) };
const page = (title, desc, body) => `<html><head><title>${title}</title><meta name="description" content="${desc}"></head><body>${body}<script>self.__x="${ART.replace(/"/g, '\\"')}"</script></body></html>`;
const resp = (html, server, version) => ({ status: 200, text: async () => html, headers: { get: (k) => (k === 'x-app-server' ? server : k === 'x-version' ? version : null) } });

console.log('\n# expectedFromRaw / articleFragments');
{
  const e = expectedFromRaw(FIELDS, RAW, 'Asus');
  t('thay [HÃNG] bằng tên hãng ở title + mô tả', e.title === 'Laptop Gaming Asus giá tốt' && e.description === 'Mua Laptop Asus chính hãng');
  t('không hãng → giữ nguyên [HÃNG]', expectedFromRaw(FIELDS, RAW, null).title === 'Laptop Gaming [HÃNG] giá tốt');
  t('field trống/thiếu → null', expectedFromRaw(FIELDS, { filter_inforbox: R('') }, null).article === null && expectedFromRaw(FIELDS, {}, null).title === null);
  const f = articleFragments(ART);
  t('mảnh lấy từ các khối khác nhau, ≤60 ký tự', f.length >= 2 && f.every((x) => x.length <= 60) && new Set(f).size === f.length);
  t('bài ngắn → lấy cả bài', articleFragments('<p>ngắn</p>').join('') === 'ngắn');
}

console.log('\n# compareWeb');
{
  const exp = expectedFromRaw(FIELDS, RAW, 'Asus');
  const ok = compareWeb(page('Laptop Gaming Asus giá tốt', 'Mua Laptop Asus chính hãng', ART), exp);
  t('khớp title + mô tả + bài', ok.title.status === 'KHOP' && ok.description.status === 'KHOP' && ok.article.status === 'KHOP', JSON.stringify(ok));
  const bad = compareWeb(page('Mẫu tự sinh', 'Mua Laptop Asus chính hãng', '<p>trống</p>'), exp);
  t('title lệch → LECH kèm cả 2 giá trị', bad.title.status === 'LECH' && bad.title.mdm === 'Laptop Gaming Asus giá tốt' && bad.title.web === 'Mẫu tự sinh');
  t('bài có trong payload script nhưng không có trong thân trang → LECH (không đọc thành khớp)', bad.article.status === 'LECH' && bad.article.found === 0, JSON.stringify(bad.article));
  const empty = compareWeb(page('T', 'D', ''), { title: null, description: null, article: null });
  t('MDM trống → MDM_TRONG, không phán lệch', empty.title.status === 'MDM_TRONG' && empty.article.status === 'MDM_TRONG' && empty.title.web === 'T');
}

console.log('\n# checkWeb');
{
  const exp = expectedFromRaw(FIELDS, RAW, 'Asus');
  const good = page('Laptop Gaming Asus giá tốt', 'Mua Laptop Asus chính hãng', ART);
  const NEW = 'BE-webfe-tmdt-tgdd.vn-80';
  const mk = (seq) => { let i = 0; return async () => seq[Math.min(i++, seq.length - 1)]; };
  const noSleep = async () => {};
  const r1 = await checkWeb('u', exp, { fetchFn: mk([resp(good, 'BE-Web-80', 'Mwg-1'), resp(good, NEW, null), resp(good, NEW, null), resp(good, NEW, null)]), sleepFn: noSleep });
  t('bỏ lượt core cũ, đủ 3 lượt core mới → KHOP', r1.verdict === 'KHOP' && r1.samples === 3 && r1.attempts === 4, JSON.stringify(r1));
  const r2 = await checkWeb('u', exp, { fetchFn: mk([resp(good, 'BE-Web-80', 'Mwg-1')]), sleepFn: noSleep, tries: 3 });
  t('không lượt nào vào core mới → KHONG_DO_DUOC (không đọc thành khớp)', r2.verdict === 'KHONG_DO_DUOC' && r2.samples === 0);
  const old = page('Mẫu tự sinh', 'Mua Laptop Asus chính hãng', ART);
  const r3 = await checkWeb('u', exp, { fetchFn: mk([resp(good, NEW, null), resp(old, NEW, null), resp(good, NEW, null)]), sleepFn: noSleep });
  t('lượt khớp lượt lệch (node lan dở) → CHAP_CHON, verdict LECH', r3.verdict === 'LECH' && r3.fields.title.status === 'CHAP_CHON', JSON.stringify(r3.fields.title));
  const r4 = await checkWeb('u', exp, { fetchFn: async () => { throw new Error('mạng'); }, sleepFn: noSleep, tries: 2 });
  t('lỗi mạng → KHONG_DO_DUOC, không ném', r4.verdict === 'KHONG_DO_DUOC');
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
