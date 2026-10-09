/**
 * test-pim-product.mjs — test ghi field SP (title, description, bài viết) và product-ops trên server PIM giả
 * (không mạng, không trình duyệt).
 *
 *   node .claude/skills/onpage-mdm-khai-bao/scripts/test-pim-product.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { MdmError } from './mdm-core.mjs';
import { applyProductEdits, buildLeafUpdate, buildModelUpdate, leavesForPage } from './pim-product-core.mjs';
import { productWriteCommand, productOpsCommand, productRestoreCommand } from './pim-product-commands.mjs';
import { validateOpsSpec, planOps, sha256 } from './pim-content-ops.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };
const throwsCode = (fn, code) => { try { fn(); return false; } catch (e) { return e instanceof MdmError && e.exitCode === code; } };
const rejectsCode = async (p, code) => { try { await p; return false; } catch (e) { return e.exitCode === code; } };

const CFG = { category: { rootId: 'ROOT' }, pimCompanyId: '1', webOrigin: 'https://www.example.vn' };
const V = (data, locale = 'vi_VN') => [{ locale, data }];

console.log('\n# logic thuần');
{
  const { rawValues, changed } = applyProductEdits({ title: V('Cũ'), url: V('a') }, { title: 'Mới', description: 'Mô tả' });
  t('sửa title, tạo description locale vi_VN, giữ key khác', rawValues.title[0].data === 'Mới' && rawValues.description[0].locale === 'vi_VN' && rawValues.url[0].data === 'a' && changed.length === 2);
  t('field ngoài danh sách (keyword, url) bị từ chối', throwsCode(() => applyProductEdits({}, { keyword: 'x' }), 2) && throwsCode(() => applyProductEdits({}, { url: 'x' }), 2));
  const art = applyProductEdits({ product_articles: V('<p>cũ</p>', 'all') }, { product_articles: '<p>mới</p>', key_features: '<ul><li>a</li></ul>' }).rawValues;
  t('bài viết: giữ locale "all" của key có sẵn, key_features mới tạo locale "all"', art.product_articles[0].locale === 'all' && art.product_articles[0].data === '<p>mới</p>' && art.key_features[0].locale === 'all');
  t('giá trị rỗng bị từ chối', throwsCode(() => applyProductEdits({}, { title: '  ' }), 2));
  t('field nhiều locale → dừng', throwsCode(() => applyProductEdits({ title: [{ locale: 'vi_VN', data: 'a' }, { locale: 'en', data: 'b' }] }, { title: 'x' }), 2));
  t('giống hệt → không vào changed', applyProductEdits({ title: V('A') }, { title: 'A' }).changed.length === 0);

  const nodes = [
    { id: 'P1', lvl: 1, rawValues: '{}' },
    { id: 'L1', lvl: 2, rawValues: JSON.stringify({ url: V('sp-256') }) },
    { id: 'L2', lvl: 2, rawValues: JSON.stringify({ url: V('sp-256') }) },
    { id: 'L3', lvl: 2, rawValues: JSON.stringify({ url: V('sp-512') }) },
  ];
  t('leavesForPage: chỉ lá cấp sâu nhất có đúng url', leavesForPage(nodes, 'sp-256').map((n) => n.id).join() === 'L1,L2');

  const leaf = { id: 'L1', code: '100', rowVersion: 5, isActivated: true, modelId: 'P1', familyVariantId: 'LEAF-FV', categoryId: 'P1' };
  const p = buildLeafUpdate(leaf, { lvl: 2 }, { id: 'M', familyVariantId: 'MODEL-FV', categoryId: 'CAT' }, {}, CFG);
  t('payload lá: familyVariantId/categoryId lấy ở model, không lấy ở lá', p.familyVariantId === 'MODEL-FV' && p.categoryId === 'CAT' && p.rootId === 'M' && p.key === 'L1' && p.modelId === 'P1');

  const m = { code: '9', id: 'M', rowVersion: 3, categoryTeams: 'x', familyVariantId: null, isShowSync: true, error: false, familyId: 'F', isSync: true };
  const fam = { name: 'Họ', lableAttributeCode: 'product_name', imageAttributeCode: 'image', familyVariants: [{ id: 'fv' }] };
  const mp = buildModelUpdate(m, { product_name: V('Tên'), image: V([{ url: 'u.jpg' }]) }, fam, CFG);
  t('payload model: bỏ field thừa, thêm name/image/family', !('categoryTeams' in mp) && !('error' in mp) && mp.name === 'Tên' && mp.image === 'u.jpg' && mp.familyVariantOptions.length === 1 && mp.familyName === 'Họ');
  t('model thiếu product_name → dừng', throwsCode(() => buildModelUpdate(m, {}, fam, CFG), 2));
}

/** Server PIM giả: model "M" (có hoặc không biến thể), PIM gộp theo key, khoá rowVersion. */
function fakePim({ variant = true, conflictOn = null, withDesc = true, article = null } = {}) {
  const recs = {};
  const art = article == null ? {} : { product_articles: V(article, 'all') };
  const mk = (id, code, url) => ({ id, code, rowVersion: 1, isActivated: true, modelId: 'V256', rawValues: { url: V(url), title: V(`T ${id}`), ...(withDesc ? { description: V(`D ${id}`) } : {}), product_name: V('Tên SP'), ...art } });
  if (variant) { recs.L1 = mk('L1', '101', 'sp-256'); recs.L2 = mk('L2', '102', 'sp-256'); recs.L3 = mk('L3', '103', 'sp-512'); }
  const model = { id: 'M', code: '9', rowVersion: 1, familyId: 'F', familyVariantId: 'FV', categoryId: 'CAT', isActivated: true,
    rawValues: variant ? { product_name: V('Tên SP') } : { url: V('sp-256'), title: V('T M'), product_name: V('Tên SP'), ...art } };
  recs.M = model;
  const writes = [];
  const out = (r) => ({ ...r, rawValues: JSON.stringify(r.rawValues) });
  const s = {
    writes, recs,
    async post(api, p, body) {
      if (p === 'productvariant/getlist') return { object: [{ id: 'M', code: '9', name: 'SP', familyName: 'Họ' }] };
      if (p === 'productvariant/getlist4tree') {
        if (!variant) return { object: [] };
        return { object: [{ id: 'V256', lvl: 1, rawValues: '{}' }, ...['L1', 'L2', 'L3'].map((id) => ({ id, lvl: 2, name: `Màu: ${id}`, rawValues: JSON.stringify(recs[id].rawValues) }))] };
      }
      if (p === 'model/getinfor' || p === 'productvariant/getinfor') return { error: false, object: out(recs[body.id]) };
      if (p === 'datasource/getfamilyinfor') return { object: { name: 'Họ', lableAttributeCode: 'product_name', imageAttributeCode: 'image', familyVariants: [] } };
      if (p === 'model/update' || p === 'productvariant/update') {
        const r = recs[body.id];
        if (body.id === conflictOn || body.rowVersion !== r.rowVersion) return { error: true, errorReason: 'row_version', toastMessage: 'Phiên bản dữ liệu đã thay đổi' };
        writes.push(body.id);
        Object.assign(r.rawValues, body.rawValues); // PIM gộp theo key
        r.rowVersion++;
        return { error: false };
      }
      throw new Error(`path lạ ${p}`);
    },
  };
  return s;
}
// fetch giả trả trang core mới (không có header x-version) chứa modelCode
const page = async () => ({ status: 200, text: async () => '<a href="?modelCode=9">', headers: { get: () => null } });

console.log('\n# luồng ghi SP');
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pim-test-'));
  const opts = (s, extra) => ({ url: '/laptop/sp-256', edits: { title: 'Mới', description: 'Desc mới' }, taskDir: tmp, fetchFn: page, ...extra });

  const s1 = fakePim();
  const dry = await productWriteCommand(s1, CFG, opts(s1, { live: false }));
  t('DRY: 2 lá của trang 256, không ghi gì', dry.status === 'DRY' && dry.records.length === 2 && s1.writes.length === 0);

  const live = await productWriteCommand(s1, CFG, opts(s1, { live: true }));
  t('live biến thể: ghi đủ 2 lá trang này, không đụng lá 512', live.status === 'WRITTEN' && s1.writes.join() === 'L1,L2' && s1.recs.L3.rawValues.title[0].data === 'T L3');
  t('rowVersion +1 mỗi lá, readback khớp', live.written.every((w) => w.ok && w.rowVersionAfter === 2));
  t('chạy lại cùng nội dung → NO_CHANGE', (await productWriteCommand(s1, CFG, opts(s1, { live: true }))).status === 'NO_CHANGE');

  const rs = await productRestoreCommand(s1, CFG, { backupFile: live.backupFile, taskDir: tmp, live: true });
  t('restore: cả 2 lá về title cũ', rs.status === 'RESTORED' && s1.recs.L1.rawValues.title[0].data === 'T L1' && s1.recs.L2.rawValues.title[0].data === 'T L2');

  const s2 = fakePim();
  const live2 = await productWriteCommand(s2, CFG, { ...opts(s2, { live: true }), edits: { title: 'Chỉ title' } });
  const rs2 = await productRestoreCommand(s2, CFG, { backupFile: live2.backupFile, taskDir: tmp, live: true });
  t('restore chỉ title (không thêm key) → RESTORED', rs2.status === 'RESTORED' && s2.recs.L1.rawValues.title[0].data === 'T L1');

  const s3 = fakePim({ conflictOn: 'L2' });
  t('row_version ở lá 2 → exit 3, lá 1 đã ghi', await rejectsCode(productWriteCommand(s3, CFG, opts(s3, { live: true })), 3) && s3.writes.join() === 'L1');

  const s4 = fakePim({ variant: false });
  const lm = await productWriteCommand(s4, CFG, opts(s4, { live: true }));
  t('SP không biến thể: ghi ở model', lm.status === 'WRITTEN' && s4.writes.join() === 'M' && s4.recs.M.rawValues.title[0].data === 'Mới');

  const s5 = fakePim();
  t('field cấm → exit 2 trước khi gọi mạng', await rejectsCode(productWriteCommand(s5, CFG, { ...opts(s5, { live: true }), edits: { url: 'sp-moi' } }), 2) && s5.writes.length === 0);
  t('thiếu --task-dir → exit 2', await rejectsCode(productWriteCommand(s5, CFG, { ...opts(s5, { live: true }), taskDir: undefined }), 2));

  const s6 = fakePim({ withDesc: false });
  const live6 = await productWriteCommand(s6, CFG, opts(s6, { live: true }));
  let restoreAddedKeyBlocked = false;
  try {
    // description chưa có lúc backup → restore phải dừng, không giả vờ đã khôi phục
    await productRestoreCommand(s6, CFG, { backupFile: live6.backupFile, taskDir: tmp, live: true });
  } catch (e) { restoreAddedKeyBlocked = e.exitCode === 2; }
  t('restore khi có key mới sau backup → exit 2', restoreAddedKeyBlocked);
}

console.log('\n# bài viết SP: thay nguyên + sửa từng chỗ (product-ops)');
{
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'pim-ops-'));
  const ART = '<h3>Thiết kế</h3>\n<p>Máy nặng 1,5 kg, vỏ nhôm.</p>\n<p>Màn hình 15,6 inch <a href="https://x.vn/a">Full HD</a>.</p>\n<img src="https://cdn/1.jpg">';
  const base = { url: '/laptop/sp-256', taskDir: tmp, fetchFn: page };

  // thay nguyên bài (product-write + HTML) trên SP có biến thể
  const s1 = fakePim({ article: ART });
  const NEW = `<h3>Bài mới</h3>${'<p>Nội dung renew dài hơn 200 ký tự để plan chỉ in độ dài và sha256.</p>'.repeat(4)}`;
  const dry = await productWriteCommand(s1, CFG, { ...base, edits: { product_articles: NEW }, live: false });
  t('DRY thay bài: plan in len/sha (không in nguyên bài), có file before/after .html',
    dry.status === 'DRY' && dry.records[0].changed[0].after.len === NEW.length && fs.readFileSync(dry.htmlFiles.product_articles.after, 'utf8') === NEW && fs.readFileSync(dry.htmlFiles.product_articles.before, 'utf8') === ART);
  const w1 = await productWriteCommand(s1, CFG, { ...base, edits: { product_articles: NEW }, live: true });
  t('live thay bài: ghi đủ 2 lá của trang, giữ locale all, đọc lại khớp', w1.status === 'WRITTEN' && s1.writes.join() === 'L1,L2' && s1.recs.L2.rawValues.product_articles[0].data === NEW && s1.recs.L2.rawValues.product_articles[0].locale === 'all' && s1.recs.L3.rawValues.product_articles[0].data === ART);
  t('restore bài: về bản cũ', (await productRestoreCommand(s1, CFG, { backupFile: w1.backupFile, taskDir: tmp, live: true })).status === 'RESTORED' && s1.recs.L1.rawValues.product_articles[0].data === ART);

  // kiểm file ops (không mạng)
  const SHA = sha256(ART);
  const spec = validateOpsSpec({ field: 'product_articles', expectedBeforeSha256: SHA, ops: [
    { id: 'A1', type: 'replace', find: '1,5 kg', new: '1,45 kg' },
    { id: 'A2', type: 'after_p', anchor: 'vỏ nhôm', new: '<p>Bản lề mở 180 độ.</p>' },
  ] });
  t('file ops: field title → exit 2 (title dùng product-write)', throwsCode(() => validateOpsSpec({ ...spec, field: 'title' }), 2));
  t('file ops: sha sai định dạng → exit 2', throwsCode(() => validateOpsSpec({ ...spec, expectedBeforeSha256: 'abc' }), 2));
  t('file ops: type lạ / id trùng / thiếu find → exit 2',
    throwsCode(() => validateOpsSpec({ ...spec, ops: [{ id: 1, type: 'delete', find: 'x', new: '' }] }), 2)
    && throwsCode(() => validateOpsSpec({ ...spec, ops: [{ id: 1, type: 'replace', find: 'a', new: 'b' }, { id: 1, type: 'replace', find: 'c', new: 'd' }] }), 2)
    && throwsCode(() => validateOpsSpec({ ...spec, ops: [{ id: 1, type: 'replace', new: 'b' }] }), 2));

  // planOps thuần
  const p = planOps(spec, [{ label: 'x', value: ART }]);
  t('planOps: áp 2 op, đủ 5 bất biến, link/ảnh cũ còn', p.status === 'OK' && p.after.includes('1,45 kg') && p.after.includes('<p>Bản lề mở 180 độ.</p>') && Object.values(p.invariants).every(Boolean) && p.after.includes('<a href="https://x.vn/a">'));
  t('planOps: 2 lá khác nhau → exit 3 (không đoán)', throwsCode(() => planOps(spec, [{ label: 'a', value: ART }, { label: 'b', value: ART + ' ' }]), 3));
  t('planOps: anchor khớp 0 lần → exit 2', throwsCode(() => planOps({ ...spec, ops: [{ id: 'Z', type: 'replace', find: 'không có', new: 'chuỗi thay chưa từng có' }] }, [{ label: 'a', value: ART }]), 2));
  t('planOps: op xoá link cũ → phá oldLinksKept → exit 2', throwsCode(() => planOps({ ...spec, ops: [{ id: 'L', type: 'replace', find: '<a href="https://x.vn/a">Full HD</a>', new: 'Full HD' }] }, [{ label: 'a', value: ART }]), 2));

  // product-ops end-to-end trên server giả
  const s2 = fakePim({ article: ART });
  const od = await productOpsCommand(s2, CFG, { ...base, spec, live: false });
  t('product-ops DRY: plan có ops + invariants, chưa ghi', od.status === 'DRY' && od.ops.edits.length === 2 && s2.writes.length === 0);
  const ol = await productOpsCommand(s2, CFG, { ...base, spec, live: true });
  t('product-ops live: ghi 2 lá, bài sau = kết quả ops', ol.status === 'WRITTEN' && s2.writes.join() === 'L1,L2' && s2.recs.L1.rawValues.product_articles[0].data === p.after);
  t('product-ops chạy lại → ALREADY, không ghi thêm', (await productOpsCommand(s2, CFG, { ...base, spec, live: true })).status === 'ALREADY' && s2.writes.length === 2);

  const s3 = fakePim({ article: ART.replace('vỏ nhôm', 'vỏ nhựa') });
  t('product-ops: bài đã bị sửa sau fact-check → exit 3, không ghi', await rejectsCode(productOpsCommand(s3, CFG, { ...base, spec, live: true }), 3) && s3.writes.length === 0);

  const s4 = fakePim({ variant: false, article: ART });
  const om = await productOpsCommand(s4, CFG, { ...base, spec, live: true });
  t('product-ops SP không biến thể: ghi ở model', om.status === 'WRITTEN' && s4.writes.join() === 'M' && s4.recs.M.rawValues.product_articles[0].data === p.after);
}

console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
