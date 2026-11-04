/**
 * Regression test thuần logic cho cms-content-ops-engine.js (mode apply-ops): từng loại op,
 * anchor entity-flex, anchor 0/2 lần -> SKIP, chồng lấn -> SKIP, 5 bất biến, idempotence.
 * Không cần mạng, không đụng CMS.
 *   node .claude/skills/onpage-cms-product-content/scripts/test-content-ops-engine.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const src = readFileSync(join(HERE, 'cms-content-ops-engine.js'), 'utf8').replace(/if \(typeof window[\s\S]*$/, '');
const mod = await import(
  'data:text/javascript;base64,' +
  Buffer.from(src + '\nexport { flexPattern, findOne, buildContentOps, checkOpsInvariants, allOpsAlreadyApplied, sha256Hex };').toString('base64')
);
const { findOne, buildContentOps, checkOpsInvariants, allOpsAlreadyApplied, sha256Hex } = mod;

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };

console.log('\n[1] findOne: literal, entity-flex, 0 lần, 2 lần');
{
  const raw = '<p>Máy hỗ trợ 5G và WiFi 6.</p>';
  t('literal khớp đúng 1', findOne(raw, '5G').ok);
  t('0 lần -> count 0', findOne(raw, 'không có trong bài').count === 0);
  const raw2 = '<p>AAA và AAA</p>';
  t('2 lần -> count 2, SKIP', findOne(raw2, 'AAA').count === 2 && !findOne(raw2, 'AAA').ok);
  // entity-flex: 'Ổ đĩa' có thể được CMS lưu bằng entity thập phân cho 'Ổ' (U+1F84 = 7892)
  const entityRaw = '<p>&#7892; đĩa cứng 512GB.</p>';
  t('entity thập phân khớp với text đã giải mã', findOne(entityRaw, 'Ổ đĩa cứng 512GB.').ok, findOne(entityRaw, 'Ổ đĩa cứng 512GB.'));
}

console.log('\n[2] buildContentOps: từng loại op');
{
  const raw = '<h3>Tiêu đề phụ</h3>\n<p>Camera chính 48MP, hỗ trợ chụp đêm.</p>\n<table><tr><td>Pin</td></tr></table>';
  const ops = [
    { id: 'A', type: 'replace', find: '48MP', new: '50MP' },
    { id: 'B', type: 'after_p', anchor: 'chụp đêm', new: '<p>Đoạn mới sau camera.</p>' },
    { id: 'C', type: 'before_h3', anchor: 'Tiêu đề phụ', new: '<h2>Mục lục</h2>\n' },
    { id: 'D', type: 'before_tr', anchor: 'Pin', new: '<tr><td>Sạc</td></tr>' },
  ];
  const r = buildContentOps(raw, ops);
  t('build ok', r.ok, r.reason);
  t('replace áp dụng', r.final.includes('50MP') && !r.final.includes('48MP'), r.final);
  t('after_p chèn đúng sau </p> của đoạn chứa anchor', r.final.includes('chụp đêm.</p>\n<p>Đoạn mới sau camera.</p>'), r.final);
  t('before_h3 chèn trước <h3', r.final.includes('<h2>Mục lục</h2>\n<h3>Tiêu đề phụ</h3>'), r.final);
  t('before_tr chèn trước <tr', r.final.includes('<tr><td>Sạc</td></tr><tr><td>Pin</td></tr>'), r.final);
  t('opsAllApplied đúng số lượng edits', r.edits.length === 4);
}

console.log('\n[3] anchor 0/2 lần -> SKIP với lý do rõ');
{
  const raw = '<p>Nội dung không liên quan.</p>';
  const zero = buildContentOps(raw, [{ id: 'X', type: 'replace', find: 'không tồn tại', new: 'y' }]);
  t('0 lần -> !ok, lý do nhắc "0 lần"', !zero.ok && /0 lần/.test(zero.reason), zero.reason);
  const dup = '<p>AAA và AAA</p>';
  const two = buildContentOps(dup, [{ id: 'Y', type: 'replace', find: 'AAA', new: 'BBB' }]);
  t('2 lần -> !ok, lý do nhắc "2 lần"', !two.ok && /2 lần/.test(two.reason), two.reason);
}

console.log('\n[4] 2 ops chồng lấn -> SKIP');
{
  const raw = '<p>Camera chính 48MP tốt.</p>';
  const overlap = buildContentOps(raw, [
    { id: 'O1', type: 'replace', find: 'chính 48MP', new: 'x' },
    { id: 'O2', type: 'replace', find: '48MP tốt', new: 'y' },
  ]);
  t('chồng lấn -> !ok, lý do nhắc cả 2 id', !overlap.ok && /O1/.test(overlap.reason) && /O2/.test(overlap.reason), overlap.reason);
}

console.log('\n[5] 5 bất biến apply-ops');
{
  const before = '<p style="text-align:justify;"><img src="a.jpg" /></p>\n<p>Camera 48MP <a href="https://x.vn">chi tiết</a> ở đây.</p>';
  const ops = [{ id: 'A', type: 'replace', find: '48MP', new: '50MP' }];
  const built = buildContentOps(before, ops);
  t('build ok', built.ok, built.reason);
  const inv = checkOpsInvariants({ before, after: built.final, edits: built.edits, opsLength: ops.length });
  for (const [k, v] of Object.entries(inv)) t(`bất biến ${k}`, v === true, JSON.stringify(inv));

  console.log('  -- oldLinksKept/oldImgsKept phải fail khi ops vô tình xoá mất link/ảnh gốc');
  const destructive = buildContentOps(before, [{ id: 'D', type: 'replace', find: before.slice(0, before.indexOf('<p>Camera')), new: '<p>đã xoá ảnh</p>' }]);
  t('destructive build ok (op vẫn định vị được)', destructive.ok, destructive.reason);
  const invD = checkOpsInvariants({ before, after: destructive.final, edits: destructive.edits, opsLength: 1 });
  t('oldImgsKept fail khi ảnh gốc bị xoá', invD.oldImgsKept === false, JSON.stringify(invD));
}

console.log('\n[6] idempotence: ops đã áp ở lần chạy trước -> allOpsAlreadyApplied');
{
  const before = '<p>Camera chính 48MP.</p>';
  const ops = [{ id: 'A', type: 'replace', find: '48MP', new: '50MP' }];
  t('trước khi áp: chưa already', !allOpsAlreadyApplied(before, ops));
  const built = buildContentOps(before, ops);
  t('sau khi áp: already', allOpsAlreadyApplied(built.final, ops), built.final);

  const beforeIns = '<p>Camera tốt.</p>';
  const opsIns = [{ id: 'B', type: 'after_p', anchor: 'Camera tốt', new: '<p>Thêm chi tiết.</p>' }];
  const builtIns = buildContentOps(beforeIns, opsIns);
  t('insertion op: sau khi áp -> already', allOpsAlreadyApplied(builtIns.final, opsIns));
  t('insertion op: trước khi áp -> chưa already', !allOpsAlreadyApplied(beforeIns, opsIns));
}

console.log('\n[7] sha256Hex khớp crypto.subtle trực tiếp');
{
  const h = await sha256Hex('hello');
  t('sha256("hello") đúng giá trị chuẩn', h === '2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824', h);
}

console.log(`\n=== pass ${pass} / fail ${fail} ===`);
process.exit(fail ? 1 : 0);
