/**
 * test-mdm-core.mjs — test logic thuần + luồng ghi chạy trên server giả (không mạng, không trình duyệt).
 *
 *   node .claude/skills/onpage-mdm-khai-bao/scripts/test-mdm-core.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {
  applyEdits, assertNoDroppedKeys, buildUpdate, diffRaw, isRowVersionConflict, parseWebUrl,
  categoryCandidates, resolveRest, seoFieldsFor, MdmError,
} from './mdm-core.mjs';
import { checkPage, pollUntil, extractTitle } from './mdm-web-verify.mjs';
import { writeCommand, restoreCommand, uploadCommand, collectEdits } from './mdm-commands-write.mjs';
import { parseArgs } from './mdm-cli.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const throwsCode = (fn, code) => { try { fn(); return false; } catch (e) { return e instanceof MdmError && e.exitCode === code; } };
const rejectsCode = async (p, code) => { try { await p; return false; } catch (e) { return e.exitCode === code; } };

const CFG = {
  category: { objectId: 'OBJ-C', tableId: 'TBL-C', functionId: 'FN-C', rootId: 'ROOT' },
  brand: { objectId: 'OBJ-B', tableId: 'TBL-B', functionId: 'FN-B' },
  filter: { objectId: 'OBJ-F', tableId: 'TBL-F', functionId: 'FN-F', relationId: 'REL-F' },
  webOrigin: 'https://www.example.vn',
};
const R = (data) => [{ locale: 'all', data }];

console.log('\n# applyEdits / chặn rơi key');
{
  const raw = { url: R('ky-thuat'), title: R('Cũ'), filter_type_attribute_code: R('448') };
  const { rawValues, changed } = applyEdits('filter-value', raw, { title: 'Mới  hai dấu cách &amp;', filter_inforbox: '<h2>x</h2>' });
  t('đổi title giữ nguyên byte (không trim, không giải entity)', rawValues.title[0].data === 'Mới  hai dấu cách &amp;');
  t('field chưa có → tạo locale all', JSON.stringify(rawValues.filter_inforbox) === JSON.stringify(R('<h2>x</h2>')));
  t('changed đủ 2 field', changed.length === 2);
  t('không đụng bản gốc', raw.title[0].data === 'Cũ');
  t('giá trị giống cũ → không tính là đổi', applyEdits('filter-value', raw, { title: 'Cũ' }).changed.length === 0);
  t('field ngoài danh sách (url) bị từ chối', throwsCode(() => applyEdits('filter-value', raw, { url: 'x' }), 2));
  t('màn lạ bị từ chối', throwsCode(() => applyEdits('product', raw, { title: 'x' }), 2));
  t('nhiều locale → dừng', throwsCode(() => applyEdits('category', { seo_title: [{ locale: 'vi', data: 'a' }, { locale: 'en', data: 'b' }] }, { seo_title: 'c' }), 2));
  t('rơi key → dừng', throwsCode(() => assertNoDroppedKeys({ a: 1, b: 2 }, { a: 1 }), 2));
  t('không rơi key → qua', (assertNoDroppedKeys({ a: 1 }, { a: 1, b: 2 }), true));
}

console.log('\n# buildUpdate đúng shape request giao diện');
{
  const cat = buildUpdate('category', { id: 'C1', rowVersion: 11, rawValues: {}, objectCode: 'tgdd_category' }, { seo_title: R('x') }, CFG);
  t('category: key = id, functionId, isIncrementKey, rowVersion giữ', cat.key === 'C1' && cat.functionId === 'FN-C' && cat.isIncrementKey === true && cat.rowVersion === 11 && cat.rawValues.seo_title);
  const br = buildUpdate('brand', { id: 'B1', rowVersion: 5, isActivated: true, recordCode: '1069', rawValues: {} }, { seo_title: R('y') }, CFG);
  t('brand: objectId/tableId/functionId từ config', br.objectId === 'OBJ-B' && br.tableId === 'TBL-B' && br.functionId === 'FN-B' && br.recordCode === '1069' && br.rowVersion === 5);
  const fv = buildUpdate('filter-value', { id: 'V1', rowVersion: 7, dataObjectId: 'DO1', rawValues: { filter_type_attribute_code: R('448') } }, { filter_type_attribute_code: R('448'), title: R('z') }, CFG);
  t('filter-value: recordCode = mã dòng Filter cha, dataRelation mang rawValues mới', fv.recordCode === '448' && fv.dataRelation.rawValues.title[0].data === 'z' && fv.dataRelation.rowVersion === 7 && fv.relationId === 'REL-F' && fv.isIncrementKey === false);
  t('filter-value thiếu mã dòng cha → dừng', throwsCode(() => buildUpdate('filter-value', { id: 'V', rawValues: {} }, {}, CFG), 2));
}

console.log('\n# so readback / row_version');
{
  t('khớp tuyệt đối dù khác thứ tự key', diffRaw({ a: R('1'), b: R('2') }, { b: [{ data: '2', locale: 'all' }], a: R('1') }).length === 0);
  t('lệch 1 dấu cách bị bắt', diffRaw({ a: R('x ') }, { a: R('x') }).join() === 'a');
  t('row_version nhận đúng', isRowVersionConflict({ error: true, errorReason: 'row_version' }) && !isRowVersionConflict({ error: false }));
}

console.log('\n# tra URL');
{
  t('trang listing', parseWebUrl('https://www.example.vn/laptop-ky-thuat', CFG.webOrigin).slug === 'laptop-ky-thuat');
  t('trang SP', parseWebUrl('/laptop/macbook-neo', CFG.webOrigin).kind === 'product');
  t('khác domain bị từ chối', throwsCode(() => parseWebUrl('https://evil.vn/laptop', CFG.webOrigin), 2));
  const cats = [{ url: 'may-tinh' }, { url: 'may-tinh-de-ban' }, { url: 'laptop' }];
  t('danh mục dài nhất trước', categoryCandidates('may-tinh-de-ban-hp', cats)[0].url === 'may-tinh-de-ban');
  const brands = [{ id: 'b-dell', url: 'dell' }, { id: 'b-apple', url: 'apple-macbook' }];
  const values = [{ id: 'v-kt', url: 'ky-thuat' }, { id: 'v-neo', url: 'neo' }];
  t('filter', resolveRest('ky-thuat', { brands, filterValues: values }).id === 'v-kt');
  t('hãng', resolveRest('dell', { brands, filterValues: values }).screen === 'brand');
  const bf = resolveRest('dell-ky-thuat', { brands, filterValues: values });
  t('hãng + filter → field *_brand_filter', bf.variant === 'brand-filter' && seoFieldsFor(bf).title === 'title_brand_filter');
  t('dòng có tiền tố hãng (apple-macbook-neo)', resolveRest('apple-macbook-neo', { brands, filterValues: values }).id === 'v-neo');
  t('không khớp → null', resolveRest('khong-co', { brands, filterValues: values }) === null);
  t('mơ hồ → dừng', throwsCode(() => resolveRest('dell', { brands, filterValues: [{ id: 'v-dell', url: 'dell' }] }), 2));
}

console.log('\n# nghiệm thu web');
{
  const html = '<html><head><title>Laptop &amp; PC  giá tốt</title><meta name="description" content="Mô tả"></head><body><h2>Tiêu đề</h2><p>Đoạn   văn</p></body></html>';
  t('title giải entity, giữ 2 dấu cách', extractTitle(html) === 'Laptop & PC  giá tốt');
  t('đạt title + desc + text', checkPage(html, { title: 'Laptop & PC  giá tốt', description: 'Mô tả', text: 'Tiêu đề Đoạn văn' }).pass);
  t('title thiếu 1 dấu cách → trượt', !checkPage(html, { title: 'Laptop & PC giá tốt' }).pass);
  const resp = (body, version) => ({ status: 200, text: async () => body, headers: { get: (k) => (k === 'x-version' ? version : null) } });
  const seq = [resp('<title>cũ</title>'), resp('<title>mới</title>', 'Mwg-6.9'), resp('<title>mới</title>'), resp('<title>mới</title>')];
  let i = 0;
  const r = await pollUntil('u', { title: 'mới' }, { samples: 2, intervalSec: 0, maxMinutes: 1, fetchFn: async () => seq[Math.min(i++, seq.length - 1)], sleepFn: async () => {} });
  t('mẫu core cũ bị bỏ qua, cần 2 mẫu core mới liên tiếp', r.verdict === 'PASS' && r.history.filter((h) => h.skipped).length === 1);
}

console.log('\n# luồng ghi trên server giả');
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'mdm-test-'));
  const store = { id: 'B1', rowVersion: 5, isActivated: true, recordCode: '1069', rawValues: { seo_title: R('Cũ'), url: R('dell') } };
  const calls = [];
  const fake = (mode = 'ok') => ({
    async post(api, p, body) {
      calls.push(p);
      if (p.endsWith('getinfor')) return { error: false, object: JSON.parse(JSON.stringify(store)) };
      if (p.endsWith('update')) {
        if (mode === 'conflict' || body.rowVersion !== store.rowVersion) return { error: true, errorReason: 'row_version', toastMessage: 'Phiên bản dữ liệu đã thay đổi' };
        store.rawValues = mode === 'trim' ? { ...body.rawValues, seo_title: R(body.rawValues.seo_title[0].data.trim()) } : body.rawValues;
        store.rowVersion += 1;
        return { error: false, object: true };
      }
      throw new Error(`không mong đợi ${p}`);
    },
  });
  const dry = await writeCommand(fake(), CFG, { screen: 'brand', id: 'B1', edits: { seo_title: 'Mới ' }, taskDir: tmp, live: false });
  t('dry: không gọi update', dry.status === 'DRY' && !calls.some((c) => c.endsWith('update')));
  const live = await writeCommand(fake(), CFG, { screen: 'brand', id: 'B1', edits: { seo_title: 'Mới ' }, taskDir: tmp, live: true });
  t('live: WRITTEN, rowVersion +1, có backup', live.status === 'WRITTEN' && live.rowVersionAfter === 6 && fs.existsSync(live.backupFile));
  t('backup giữ bản cũ', JSON.parse(fs.readFileSync(live.backupFile, 'utf8')).rawValues.seo_title[0].data === 'Cũ');
  t('url không bị rơi', store.rawValues.url[0].data === 'dell');
  t('không đổi gì → NO_CHANGE', (await writeCommand(fake(), CFG, { screen: 'brand', id: 'B1', edits: { seo_title: 'Mới ' }, taskDir: tmp, live: true })).status === 'NO_CHANGE');
  t('row_version → exit 3', await rejectsCode(writeCommand(fake('conflict'), CFG, { screen: 'brand', id: 'B1', edits: { seo_title: 'Khác' }, taskDir: tmp, live: true }), 3));
  t('server trim → VERIFY_FAIL exit 1', await rejectsCode(writeCommand(fake('trim'), CFG, { screen: 'brand', id: 'B1', edits: { seo_title: 'Có cách ' }, taskDir: tmp, live: true }), 1));
  const rs = await restoreCommand(fake(), CFG, { backupFile: live.backupFile, screen: 'brand', taskDir: tmp, live: true });
  t('restore về đúng bản backup', rs.status === 'RESTORED' && store.rawValues.seo_title[0].data === 'Cũ', JSON.stringify(rs) + ' ' + store.rawValues.seo_title[0].data);

  const img = path.join(tmp, 'a.png');
  fs.writeFileSync(img, Buffer.from([1, 2, 3]));
  let ups = 0;
  const upS = { async run() { ups++; return [{ ok: true, ms: 5, json: { error: false, object: { filePath: 'https://cdn.example/a123.png' } } }]; } };
  const head = async () => ({ status: 200, headers: { get: () => '3' } });
  const u1 = await uploadCommand(upS, CFG, { file: img, taskDir: tmp, live: true, fetchFn: head });
  const u2 = await uploadCommand(upS, CFG, { file: img, taskDir: tmp, live: true, fetchFn: head });
  t('upload lần 2 cùng byte → REUSED, không up lại', u1.status === 'UPLOADED' && u2.status === 'REUSED' && ups === 1);
  t('đuôi lạ bị từ chối', await rejectsCode(uploadCommand(upS, CFG, { file: path.join(tmp, 'a.svg'), taskDir: tmp, live: true }), 2));
}

console.log('\n# CLI');
{
  const a = parseArgs(['write', '--screen', 'brand', '--set', 'seo_title=A=B', '--set', 'seo_keyword=k', '--live']);
  t('parseArgs: --set lặp, --live bool', a._[0] === 'write' && a.set.length === 2 && a.live === true);
  t('collectEdits: giữ dấu = trong giá trị', collectEdits(['seo_title=A=B']).seo_title === 'A=B');
  t('collectEdits: khai trùng field → dừng', throwsCode(() => collectEdits(['a=1', 'a=2']), 2));
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
