#!/usr/bin/env node
// Infobox TopZone (trang Filter/Dòng filter topzone.vn/<dòng>) = bài News site 1 (TGDĐ), chuyên mục 2424 "Mô tả dòng sản phẩm",
// bài cũ đặt "<Tên> - Infobox TopZone" (1598413, 1598414, 1583112). Cú pháp user chốt 29/10/2026 (như bài TGDĐ "TGDĐ iPhone 18 series - Infobox"):
// tiêu đề "TopZone <Tên> - Infobox", tag + meta "<Tên> - Infobox", url "<slug>-infobox-topzone" (đuôi -topzone tránh trùng url bài TGDĐ cùng site 1).
// Dòng filter: actived (Xuất bản) + tick chuyên mục 2424. Hãng/Filter: pending (Chờ duyệt), KHÔNG tick chuyên mục (--khong-chuyen-muc). User tự gắn ID vào ô "Link TOPZONE" ở CMS cũ Category/Property.
// HTTP thẳng bằng cookie CMS (cms-tz-http, profile ntvy-193118), không mở tab. Không in cookie.
//
//   node cms_infobox_tz.mjs tim "<cụm tiêu đề>"                       → [{id, tieu_de, trang_thai}] bài 2424 site 1 khớp
//   node cms_infobox_tz.mjs doc <newsId> [-o file.html]                → thông tin bài + độ dài nội dung
//   node cms_infobox_tz.mjs ghi --html f.html --tieu-de "<Tên> - Infobox TopZone" --url <slug>-infobox-topzone
//        --tag "<Tên> - Infobox" --trang-thai actived|pending [--khong-chuyen-muc] [--thumb <url CDN>] [--id <newsId>] [--live]                    → id 0/không có: tạo mới; có id: cập nhật nội dung
//   Không --live = dry: dựng payload, kiểm guard, không POST.
import fs from 'node:fs';
import { cmsFetch, chuanHoaNoiDung } from '/Users/nguyentuongvy/.claude/skills/cms-topzone-tao-bai/scripts/cms-tz-http.mjs';
import { parseForm, decode } from '/Users/nguyentuongvy/.claude/skills/cms-faq-tao-bai/scripts/cms-http.mjs';

const ROOT = 'https://cms.thegioididong.com/v2/';
const SITE = 1;
const CATE = { id: '2424', name: 'Mô tả dòng sản phẩm' };

function stickers(html, cls) {
  const i = html.indexOf(`sticker ${cls}`);
  if (i < 0) return [];
  const ul = html.slice(i, html.indexOf('</ul>', i));
  return [...ul.matchAll(/<li\b[^>]*data-id="([^"]*)"[^>]*data-name="([^"]*)"/g)].map((m) => ({ id: m[1], name: decode(m[2]) }));
}
const hidden = (html, id) => decode((html.match(new RegExp(`<input[^>]*id="${id}"[^>]*value="([^"]*)"`)) || [])[1] || '');

async function doc(id) {
  const r = await cmsFetch(`${ROOT}News/NewsEdit?newsId=${id}&siteId=${SITE}`);
  if (r.status !== 200) throw new Error(`NewsEdit ${id}: HTTP ${r.status}`);
  const html = await r.text();
  const { fields, selects } = parseForm(html);
  return { fields, selects, cates: stickers(html, 'newscategory'), formats: stickers(html, 'newspostformat'), productCate: hidden(html, 'hdListCategory') };
}

async function tim(kw) {
  const q = new URLSearchParams({ activedDate: '', approvedDate: '', siteId: String(SITE), categoryId: CATE.id, postFormatId: '-1', kw, status: 'all', groupType: '-1' });
  const t = await (await cmsFetch(`${ROOT}News/NewsList?${q}`)).text();
  return [...t.matchAll(/<tr[\s\S]*?<\/tr>/g)].map((m) => decode(m[0].replace(/<[^>]+>/g, ' ')).replace(/\s+/g, ' ').trim())
    .map((x) => x.match(/^(\d{6,})\s+(.+?)\s+-\s+(Xuất bản|Nháp|Chờ duyệt|Đã duyệt|Đã xóa)/)).filter(Boolean)
    .map((m) => ({ id: m[1], tieu_de: m[2], trang_thai: m[3] }));
}

async function ghi({ html, tieuDe, url, tag, trangThai = 'pending', coChuyenMuc = true, thumb, id = 0, live = false }) {
  if (!['actived', 'pending'].includes(trangThai)) throw new Error(`trạng thái ${trangThai} không hợp lệ (actived|pending)`);
  const content = chuanHoaNoiDung(fs.readFileSync(html, 'utf8'));
  const p = await doc(id);
  const data = { ...p.fields };
  if (!id) {
    const meta = tag || tieuDe;
    Object.assign(data, { txtTitle: tieuDe, txtUrl: url, txtTag: meta, txtMetaTitle: meta, txtMetaDescription: meta, txtMetaKeyword: meta,
      thumbnailNews: thumb || '', cboStatus: trangThai });
  }
  const cates = id ? p.cates : (coChuyenMuc ? [CATE] : []);
  if (coChuyenMuc && !cates.some((c) => c.id === CATE.id)) throw new Error(`bài ${id} không thuộc chuyên mục 2424, không ghi`);
  data.LstProductCategory = p.productCate;
  data.LstCategoryName = cates.map((c) => c.name).join(',');
  data.LstCategoryId = cates.map((c) => c.id).join(',');
  data.LstPostFormatName = p.formats.map((c) => c.name).join(',');
  data.LstPostFormatId = p.formats.map((c) => c.id).join(',');
  data.LstBannerPlace = (p.selects.ddlBannerPlace || []).join(',');
  data.LstBannerPlaceMobile = (p.selects.ddlBannerPlaceMobile || []).join(',');
  data.LstHotTopic = (p.selects.ddlHotTopic || []).join(',');
  data.contentNewsAva = content;
  data.ContentNews = content;
  if (String(data.hdNewsId) !== String(id)) throw new Error('payload sai hdNewsId, không POST');
  if (String(data.hdSiteId) !== String(SITE)) throw new Error(`payload siteId ${data.hdSiteId}, cần ${SITE} (infobox TopZone là bài site TGDĐ), không POST`);
  if (!data.txtTitle || !data.txtUrl || !data.txtTag) throw new Error('thiếu tiêu đề/url/tag, không POST');
  if (data.cboStatus === 'actived' && !data.thumbnailNews) throw new Error('bài Xuất bản thiếu thumbnail, không POST');
  const tom = { id: Number(id), moi: !id, tieu_de: data.txtTitle, url: data.txtUrl, tag: data.txtTag, trang_thai: data.cboStatus, chuyen_muc: data.LstCategoryName, thumb: data.thumbnailNews, noi_dung: content.length };
  if (!live) return { ...tom, dry: true };
  const skip = data.hdIsSkipSecurity === '1' ? '?skip=1' : '';
  const r = await cmsFetch(`${ROOT}News/SubmitNewsEdit${skip}`, {
    method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' }, body: new URLSearchParams(data).toString(),
  });
  const t = await r.text();
  let kq; try { kq = JSON.parse(t); } catch { kq = { status: -999, error: `HTTP ${r.status} ${t.slice(0, 200)}` }; }
  if (!(kq.status >= 1)) throw new Error('CMS từ chối: ' + JSON.stringify(kq).slice(0, 300));
  const newId = kq.status > 1 ? kq.status : Number(id);
  const lai = await doc(newId);   // nghiệm thu: đọc lại so nội dung
  const khop = chuanHoaNoiDung(lai.fields.contentNewsAva || '') === content;
  return { ...tom, id: newId, khop_noi_dung: khop, chuyen_muc_sau: lai.cates.map((c) => c.id).join(','), trang_thai_sau: lai.fields.cboStatus };
}

const a = process.argv.slice(2);
const opt = (k) => (a.includes(k) ? a[a.indexOf(k) + 1] : undefined);
try {
  let kq;
  if (a[0] === 'tim') kq = await tim(a[1] || '');
  else if (a[0] === 'doc') {
    const p = await doc(Number(a[1]));
    const c = p.fields.contentNewsAva || '';
    if (opt('-o')) fs.writeFileSync(opt('-o'), c);
    kq = { id: p.fields.hdNewsId, site: p.fields.hdSiteId, tieu_de: p.fields.txtTitle, url: p.fields.txtUrl, trang_thai: p.fields.cboStatus, chuyen_muc: p.cates, thumb: p.fields.thumbnailNews, noi_dung: c.length };
  } else if (a[0] === 'ghi') {
    kq = await ghi({ html: opt('--html'), tieuDe: opt('--tieu-de'), url: opt('--url'), tag: opt('--tag'), trangThai: opt('--trang-thai') || 'pending', coChuyenMuc: !a.includes('--khong-chuyen-muc'), thumb: opt('--thumb'), id: Number(opt('--id') || 0), live: a.includes('--live') });
  } else { console.error('Lệnh: tim | doc | ghi (xem đầu file)'); process.exit(2); }
  console.log(JSON.stringify(kq, null, 1));
} catch (e) { console.log(JSON.stringify({ loi: String(e.message || e).slice(0, 400) })); process.exit(1); }
