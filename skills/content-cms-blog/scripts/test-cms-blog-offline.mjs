/**
 * test-cms-blog-offline.mjs — test không mạng, không CMS cho content-cms-blog: luật form, trạng thái,
 * payload Game App, nghiệm thu live trên trang giả.
 *   node .claude/skills/content-cms-blog/scripts/test-cms-blog-offline.mjs
 */
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { slugCms, toCmsDate, normalizeForm, lintContent, articleKind } from './cms-blog-lint.mjs';
import { statusOf, normalizeStatus, gameAppPayload, slugOf, liveUrl, verifyFields } from './cms-blog-core.mjs';
import { liveCheck } from './cms-cli-air.mjs';

let pass = 0, fail = 0;
const t = (name, cond, extra) => { if (cond) { pass++; console.log('  ok  ', name); } else { fail++; console.log('  FAIL', name, extra ?? ''); } };

console.log('\n# luật form');
t('slugCms bỏ dấu, đ→d', slugCms('Đánh giá MacBook Air M5') === 'danh-gia-macbook-air-m5');
t('slugCms ≤50 cắt ở ranh giới cụm', slugCms('MacBook Air M5 có tốt không? Đánh giá chi tiết sau 3 tháng sử dụng thực tế').length <= 50);
t('toCmsDate dd/mm/yyyy HH:MM', toCmsDate('05/11/2026', '02:00') === '2026-11-05T02:00:00');
t('toCmsDate ngày sai → null', toCmsDate('31/02/2026') === null);

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'cms-blog-test-'));
fs.writeFileSync(path.join(dir, 'body.html'), '<h2>A</h2><p>x</p>');
fs.writeFileSync(path.join(dir, 'thumb.jpg'), 'x');
const base = { keyword: 'macbook', title: 'MacBook có tốt không', thumb: 'thumb.jpg', child_category: '1703', meta_desc: 'mô tả', tags: ['macbook', 'apple'], content_file: 'body.html' };
const hd = normalizeForm(base, { kind: 'hoi-dap', baseDir: dir });
t('form Hỏi Đáp hợp lệ không lỗi', hd.err.length === 0, hd.err);
t('chuyên mục cha tự điền theo con', hd.v.parent === '1656');
t('không publish_date → Chờ duyệt', hd.v.status === 'pending');
const hd2 = normalizeForm({ ...base, publish_date: '01/01/2099' }, { kind: 'hoi-dap', baseDir: dir });
t('có publish_date → Xuất bản hẹn 02:00', hd2.v.status === 'actived' && hd2.v.activedDate === '2099-01-01T02:00:00');
t('ngày đã qua → lỗi', normalizeForm({ ...base, publish_date: '01/01/2020' }, { kind: 'hoi-dap', baseDir: dir }).err.some((e) => e.includes('đã qua')));
t('tags thiếu keyword → lỗi', normalizeForm({ ...base, tags: ['apple', 'mac'] }, { kind: 'hoi-dap', baseDir: dir }).err.some((e) => e.includes('keyword')));
t('cặp chuyên mục sai → lỗi', normalizeForm({ ...base, parent_category: '1637' }, { kind: 'hoi-dap', baseDir: dir }).err.some((e) => e.includes('không thuộc')));
t('url Hỏi Đáp > 84 → lỗi', normalizeForm({ ...base, url: 'a'.repeat(85) }, { kind: 'hoi-dap', baseDir: dir }).err.some((e) => e.includes('> 84')));
const ga = normalizeForm({ ...base, form_game_app: 'CODE game', platforms: '2,3', publish_date: '01/01/2099' }, { kind: 'game-app', baseDir: dir });
t('Game App: Xuất bản = approved', ga.v.status === 'approved', ga.v.status);
t('Game App thiếu form_game_app → lỗi', normalizeForm(base, { kind: 'game-app', baseDir: dir }).err.some((e) => e.includes('form_game_app')));

const c = await lintContent('<html><p>- gạch đầu dòng</p><img src="a.jpg"></html>', { checkRemote: false });
t('nội dung: <html> → lỗi', c.err.some((e) => e.includes('<html>')));
t('nội dung: bullet trong <p> + ảnh thiếu alt → cảnh báo', c.warn.some((w) => w.includes('bullet')) && c.warn.some((w) => w.includes('alt')));

console.log('\n# trạng thái + payload');
const faq = { newsId: 9, categoryId: 1226, listCategoryId: '1226', isGameApp: 0, isDraft: 0, isActived: 1, isApproved: 0 };
const gar = { newsId: 77, listCategoryId: '2002', isGameApp: 1, isDraft: 0, isActived: 1, url: 'code-abc-77', title: 'T', content: '<p>c</p>', platformIdList: '2,3', formGameApp: 'CODE game' };
t('nhận loại bài', articleKind(faq) === 'hoi-dap' && articleKind(gar) === 'game-app');
t('Hỏi Đáp isActived=1 → actived', statusOf(faq) === 'actived');
t('Game App isActived=1 → approved (Xuất bản)', statusOf(gar) === 'approved');
t('normalizeStatus publish theo loại', normalizeStatus('game-app', 'publish') === 'approved' && normalizeStatus('hoi-dap', 'xuat-ban') === 'actived');
t('slug Game App cắt -id', slugOf(gar) === 'code-abc' && liveUrl(gar) === 'https://www.thegioididong.com/game-app/code-abc-77');
const p = gameAppPayload(gar, { content: '<p>mới</p>' });
t('payload Game App: url không -id, giữ dạng bài, platform để server giữ', p.url === 'code-abc' && p.formGameApp === 'CODE game' && p.platformIdList === undefined && p.status === 'approved' && p.content === '<p>mới</p>');
t('verifyFields bắt lệch thân bài', verifyFields({ ...faq, description: '<p>a</p>' }, { body: '<p>b</p>' }).length === 1);

console.log('\n# nghiệm thu live (trang giả)');
const fakeFetch = (page) => async () => ({ status: 200, text: async () => page });
const filler = 'menu khuyến mãi chân trang '.repeat(5000); // trang thật ~450k ký tự ngoài thân bài
const para = (n) => Array.from({ length: n }, (_, i) => `<p>Đoạn số ${i} nói về MacBook màu bạc và cách chọn máy phù hợp nhu cầu.</p>`).join('');
const mine = `<p>[Product_Promotion listid="1,2" title="ĐỪNG BỎ LỠ"]</p><h2>Mục một</h2>${para(30)}`;
const livePage = `<html><body>${filler}<div>ĐỪNG BỎ LỠ MacBook Air 29.990.000đ</div><h2>Mục một</h2>${para(30)}${filler}</body></html>`;
const ok = await liveCheck({ url: 'https://x/y', html: mine, clearcache: false, fetchFn: fakeFetch(livePage) });
t('trang dài + shortcode đầu bài → PASS', ok.pass, ok.fingerprint);
const stale = `<html><body>${filler}<h2>Mục một</h2>${para(30).replace('Đoạn số 15', 'Đoạn CŨ 15').slice(0, 1200)}${para(30).slice(-400)}${filler}</body></html>`;
const bad = await liveCheck({ url: 'https://x/y', html: `<h2>Mục một</h2>${para(30)}`, clearcache: false, fetchFn: fakeFetch(stale) });
t('cache cũ ngắn hơn hẳn (đầu/cuối khớp) → FAIL', !bad.pass, bad.fingerprint);

fs.rmSync(dir, { recursive: true, force: true });
console.log(`\n${pass} pass, ${fail} fail`);
process.exit(fail ? 1 : 0);
