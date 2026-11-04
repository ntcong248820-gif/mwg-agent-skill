/**
 * newcms-api.mjs — đọc/ghi bài Hỏi Đáp + Game App trên NEW CMS qua API bus/cms (Bearer tự lo bởi
 * newcms-auth.mjs). Bắt chước đúng cách app newcms.thegioididong.com lưu bài (đọc từ bundle 02/11/2026):
 *
 * Hỏi Đáp (/Faq/NewsEdit): thân bài ở `description`. Cập nhật = đọc bản ghi gốc (newsselect), lọc theo
 *   allowlist UPDATE_FIELDS, đè field đổi, POST News/newsupdate → Cms/news/updatecategory (1226) →
 *   News/newslogadd. Thêm mới = News/newsadd (allowlist ADD_FIELDS) → id ở `status`.
 * Game App (/GameApp/EditNews): thân bài ở `content`. Một endpoint Cmsgameapp/cmsgameappnewssave cho cả
 *   thêm mới (không newsId) lẫn cập nhật; backend tự giữ field không gửi.
 *
 * Không in token. Lỗi API ném Error có message của server.
 */

import fs from 'node:fs';
import path from 'node:path';
import { newcmsFetch, readSession } from './newcms-auth.mjs';

export const FAQ_CATEGORY_ID = 1226;
export const GAMEAPP_CATEGORY_ID = 2002;
export const SITE_ID = 1;

// Allowlist field app gửi khi thêm mới / cập nhật (so khớp không phân biệt hoa thường).
const ADD_LIST = 'aisummary.isshowsummary.isshowvoice.aivoiceurl.ishidebannervccorp.activedcustomerid.activeddate.activeduser.approvedcustomerid.approveddate.approveduser.articletype.bhxtype.calories.categoryid.content.contentask.cooktime.createdcustomerid.createduser.createduseremail.description.detailimage.device.devicetoken.districtidlist.doctorid.eventidlist.extenallink.facebookposturl.facecommentidlist.formgameapp.grouptype.icpid.icpurl.ipcreated.isactived.isadminanswer.isadvisory.isallowrate.isapproved.isautonewtype.iscanyoudoit.iscommentallow.isdraft.isfaq.isfeature.isfilmh4.isfollowemail.isgallery.isgame.isgameapp.ishide.isliveblog.ismanual.isnewtab.ispin.isprivate.israte.isreviewed.isshowcomment.isstatusreader.issticked.istechnews.isuseranswer.isvideo.isvideotrailer.keyword.labelcolor.labelid.labelname.listautonewtype.listchildthreadid.listparentthreadid.listproductcategoryid.listrelatenewsid.manuid.metadescription.metakeyword.metatitle.mobilecontent.offdate.openpromotionfromdate.openpromotiontodate.pinposition.placeidlist.placemobileidlist.postalid.posttype.preptime.productcategoryid.productidlist.provinceidlist.publiceditorname.publiceditorscore.publicemail.publicfacebook.publicfullname.publicphone.publicreason.publicscore.readeremail.readergender.readerimage.readername.readerphonenumber.recipecategory.recipeyield.relateproductid.schema.shortdescription.shorttitle.siteid.smallthumbnailimage.socialid.storeid.tags.thumbnailimage.thumbnailimagemedium.thumbnailmobile.title.totaltime.typeofservice.updateurlcount.url.userid.videoduration.videolink';
const UPDATE_LIST = 'aisummary.isshowsummary.isshowvoice.aivoiceurl.ishidebannervccorp.activedcustomerid.activeddate.activeduser.approvedcustomerid.approveddate.approveduser.articletype.bhxtype.calories.categoryid.content.contentask.cooktime.description.detailimage.districtidlist.doctorid.eventidlist.extenallink.facebookposturl.facecommentidlist.formgameapp.grouptype.hottopicid.icpid.icpurl.isactived.isadminanswer.isadvisory.isallowrate.isapproved.isautonewtype.iscanyoudoit.iscommentallow.isdraft.iseditedctv.isfaq.isfeature.isfilmh4.isfollowemail.isgallery.isgame.isgameapp.ishide.isliveblog.ismanual.isnewtab.ispin.israte.isreviewed.isshowcomment.isstatusreader.issticked.isvideo.isvideotrailer.keyword.labelcolor.labelid.labelname.likecounter.listautonewtype.listchildthreadid.listparentthreadid.listproductcategoryid.listrelatenewsid.manuid.metadescription.metakeyword.metatitle.mobilecontent.newsid.offdate.openpromotionfromdate.openpromotiontodate.pinposition.placeidlist.placemobileidlist.postalid.posttype.preptime.productcategoryid.productidlist.provinceidlist.publiceditorname.publiceditorscore.publicemail.publicfacebook.publicfullname.publicphone.publicreason.publicscore.readeremail.readergender.readerimage.readername.readerphonenumber.recipecategory.recipeyield.relateproductid.schema.shortdescription.shorttitle.siteid.smallthumbnailimage.storeid.tags.thumbnailimage.thumbnailimagemedium.thumbnailmobile.title.totaltime.typeofservice.updatedcustomerid.updateduser.updateurlcount.url.userid.videoduration.videolink';
export const ADD_FIELDS = new Set(ADD_LIST.split('.'));
export const UPDATE_FIELDS = new Set(UPDATE_LIST.split('.'));

/** Lọc object theo allowlist (key so khớp lowercase), bỏ null/undefined. */
export function pickAllowed(obj, allow) {
  const out = {};
  for (const [k, v] of Object.entries(obj || {})) if (v != null && allow.has(k.toLowerCase())) out[k] = v;
  return out;
}

/** Chuỗi user app ghi vào createdUser/updatedUser: "{username} - {fullname}". */
export function cmsUser() {
  const s = readSession();
  const u = String(s?.username || '').trim();
  const n = String(s?.fullname || '').trim();
  return u && n ? `${u} - ${n}` : u || n || 'admin';
}

/** "YYYY-MM-DDTHH:mm:ss" giờ máy — đúng format app gửi. */
export function cmsDate(d = new Date()) {
  const p = (x) => String(x).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

async function api(method, p, { params, body } = {}) {
  const qs = params ? `?${new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]))}` : '';
  const res = await newcmsFetch(`/api/v1/${p}${qs}`, {
    method,
    headers: body !== undefined ? { 'Content-Type': 'application/json', Accept: '*/*' } : { Accept: '*/*' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const j = await res.json().catch(() => null);
  if (!res.ok || j?.isError === true) {
    const msg = j?.message || j?.error?.details || j?.error || res.statusText;
    throw new Error(`${method} ${p} → HTTP ${res.status}: ${typeof msg === 'string' ? msg : JSON.stringify(msg)}`);
  }
  return j;
}

const firstRow = (j) => (Array.isArray(j?.data) ? j.data[0] : Array.isArray(j?.object) ? j.object[0] : j?.data ?? j?.object) ?? null;

/** Đọc bài (dùng chung Hỏi Đáp + Game App). */
export async function newsSelect(newsId) {
  return firstRow(await api('GET', 'News/newsselect', { params: { newsid: newsId } }));
}

/** Trạng thái Hỏi Đáp → cờ: draft | pending | approved | actived (Xuất bản). */
export function faqStatusFields(status, user = cmsUser()) {
  const f = { isDraft: +(status === 'draft'), isActived: +(status === 'actived'), isApproved: +(status === 'approved' || status === 'actived') };
  if (status === 'actived') f.activedUser = user;
  if (status === 'approved') Object.assign(f, { approveduser: user, approveddate: cmsDate() });
  return f;
}

export async function addLog(newsId, { description = '', shortInfo = '', content = '' } = {}) {
  return api('POST', 'News/newslogadd', { body: { newsId, shortInfo, content, description, updatedUser: cmsUser() } }).catch(() => null);
}

export async function updateCategories(newsId, cateIds = String(FAQ_CATEGORY_ID)) {
  return api('POST', 'Cms/news/updatecategory', { body: { newsid: newsId, cateids: String(cateIds) } });
}

/**
 * Cập nhật bài Hỏi Đáp: chỉ đổi field trong `changes` (camelCase như newsselect, vd { description, metaTitle }).
 * Mọi field khác giữ nguyên từ bản ghi gốc. Trả bản ghi đọc lại sau khi lưu.
 */
export async function faqUpdate(newsId, changes, { log = true } = {}) {
  const orig = await newsSelect(newsId);
  if (!orig) throw new Error(`không đọc được newsId=${newsId}`);
  const user = cmsUser();
  const mine = { ...changes, updatedUser: user };
  const keys = new Set(Object.keys(mine).map((k) => k.toLowerCase()).concat('newsid'));
  const base = {};
  for (const [k, v] of Object.entries(pickAllowed(orig, UPDATE_FIELDS))) if (!keys.has(k.toLowerCase())) base[k] = v;
  await api('POST', 'News/newsupdate', { body: pickAllowed({ ...base, ...mine, newsId }, UPDATE_FIELDS) });
  await updateCategories(newsId).catch(() => {});
  if (log) await addLog(newsId, { description: changes.description ?? orig.description ?? '', shortInfo: orig.shortDescription ?? '', content: orig.content ?? '' });
  return newsSelect(newsId);
}

/**
 * Thêm bài Hỏi Đáp. `fields` camelCase: title, url, description, thumbnailImage, metaTitle, metaDescription,
 * metaKeyword, listparentthreadid, listchildthreadid, articletype, productidlist, activedDate, status…
 * Trả newsId mới.
 */
export async function faqAdd({ status = 'draft', ...fields }) {
  const user = cmsUser();
  const body = pickAllowed({
    categoryId: FAQ_CATEGORY_ID, postType: 2, siteId: SITE_ID, tags: fields.metaKeyword,
    isHide: 0, isHideBannerVccorp: 0, isSticked: 0, activedDate: cmsDate(),
    ...fields, ...faqStatusFields(status, user), createdUser: user,
  }, ADD_FIELDS);
  const j = await api('POST', 'News/newsadd', { body });
  const id = Number(j?.status ?? firstRow(j));
  if (!(id > 0)) throw new Error(`newsadd không trả newsId: ${JSON.stringify(j).slice(0, 200)}`);
  await updateCategories(id).catch(() => {});
  return id;
}

/**
 * Lưu bài Game App (thêm mới khi không có newsId). Trường: title, url (không kèm -id), content,
 * thumbnailImage, isGame (1 game/0 app), formGameApp, metaTitle, metaDescription, schema, activedDate,
 * status (draft|pending|approved), platformIdList, productIdList (chỉ gửi khi đổi), cờ isGallery…
 * Trả { newsId, message }.
 */
export async function gameAppSave(payload) {
  const s = readSession();
  const j = await api('POST', 'Cmsgameapp/cmsgameappnewssave', {
    body: { ...payload, currentUser: cmsUser(), fullName: s?.fullname || '', isCtv: false, customerId: 0, siteId: SITE_ID },
  });
  const r = firstRow(j);
  return { newsId: Number(r) > 0 ? Number(r) : Number(payload.newsId) || -1, message: String(j?.message ?? '') };
}

/** Xoá mềm (bài vào mục "đã xoá" trên CMS, khôi phục được). */
export async function newsDelete(newsId) {
  return api('POST', 'News/newsdel', { params: { newsid: newsId, deleteduser: cmsUser() } });
}

/**
 * Upload ảnh qua bus/common/PostImage (đường app dùng cho ảnh TinyMCE type=2 và thumbnail).
 * Trả URL CDN. `type`: 2 ảnh nội dung, 80 thumbnail tin (NewsThumbnail80), 56 NewsThumbnail.
 */
export async function postImage(filePath, { type = 2, extra = {} } = {}) {
  const buf = fs.readFileSync(filePath);
  const name = path.basename(filePath);
  const mime = /\.png$/i.test(name) ? 'image/png' : /\.gif$/i.test(name) ? 'image/gif' : /\.webp$/i.test(name) ? 'image/webp' : 'image/jpeg';
  const fd = new FormData();
  fd.append('file', new Blob([buf], { type: mime }), name);
  const qs = new URLSearchParams({ type: String(type), siteId: String(SITE_ID), ...extra });
  const res = await newcmsFetch(`/api/v1/bus/common/PostImage?${qs}`, { method: 'POST', body: fd });
  const j = await res.json().catch(() => null);
  if (!res.ok || j?.status === -1 || !j?.imageUrl) throw new Error(`PostImage lỗi HTTP ${res.status}: ${j?.error || j?.message || ''}`);
  return j.imageUrl;
}

/**
 * Upload GIỮ TÊN FILE vào thư mục chỉ định (đường app dùng cho upload CDN có PathFolder).
 * Mặc định ra https://cdnv2.tgdd.vn/webmwg/common/News/{newsId}/<tên-file> — bucket `webmwg`, không phải
 * `mwg-static` như CMS cũ (đo 02/11/2026). Trả URL CDN. Dùng cho ảnh bài cần tên file chuẩn SEO.
 */
export async function uploadFilesCms(filePath, { pathFolder, appName = 'common', siteId = SITE_ID, keepFileName = true, checkExits = false } = {}) {
  if (!pathFolder) throw new Error('thiếu pathFolder (vd News/<newsId>)');
  const name = path.basename(filePath);
  const fd = new FormData();
  for (const [k, v] of Object.entries({ SiteId: siteId, AppName: appName, PathFolder: pathFolder, KeepFileName: keepFileName, CheckExits: checkExits, IsHash: false, ExpiredSecond: 0 })) fd.append(k, String(v));
  fd.append('Files', new Blob([fs.readFileSync(filePath)], { type: /\.png$/i.test(name) ? 'image/png' : /\.webp$/i.test(name) ? 'image/webp' : 'image/jpeg' }), name);
  const res = await newcmsFetch('https://webapi.thegioididong.com/gw/bus-automation-tmdt/api/Upload/UploadFilesCms', { method: 'POST', body: fd, headers: { Accept: 'text/plain' } });
  const j = await res.json().catch(() => null);
  const row = Array.isArray(j?.data) ? j.data[0] : null;
  if (!res.ok || !row?.fileNameCDN) throw new Error(`UploadFilesCms lỗi HTTP ${res.status}: ${row?.errorMessage || j?.errorMessage || j?.message || ''}`);
  return row.fileNameCDN;
}

/** Lịch sử sửa bài — mỗi bản ghi giữ NGUYÊN `description` (HTML thân bài) lúc đó → dùng để đối chiếu / rollback. */
export async function newsLog(newsId, { page = 0, size = 20 } = {}) {
  const j = await api('GET', 'Cms/newslog/srh', { params: { newsid: newsId, currentpage: page, recordperpage: size } });
  return Array.isArray(j?.data) ? j.data : [];
}

/** Danh mục shortcode CMS (screen=news; siteid 1 TGDĐ). Trả [{name, code…}]. */
export async function shortcodeList({ screen = 'news', siteId = SITE_ID } = {}) {
  const j = await api('GET', 'Shortcode/list', { params: { siteid: siteId, screen } });
  return Array.isArray(j?.data) ? j.data : [];
}

/** Tìm tag có sẵn (ô Keyword - Tags, tối đa 5 từ khoá/bài). */
export async function tagSearch(keyword, { size = 10 } = {}) {
  const j = await api('GET', 'Cms/tagmanagement/search', { params: { siteid: SITE_ID, currentpage: 0, recordperpage: size, keyword } });
  return (Array.isArray(j?.data) ? j.data : []).map((t) => ({ tagId: t.tagId, tagName: t.tagName }));
}

/** Danh sách cách nhau dấu phẩy lưu trong 1 htmlinfo (3724 dạng bài Hỏi Đáp, 3620 dạng bài Game App; 3648 là Vào bếp), đã giải entity. */
export async function htmlInfoList(htmlid) {
  const j = await api('GET', 'Cms/htmlinfo/get', { params: { htmlid } });
  const html = String(firstRow(j)?.content ?? '');
  const txt = html.replace(/<[^>]*>/g, '').replace(/&([a-z]+);/gi, (m, e) => ({ agrave: 'à', aacute: 'á', ocirc: 'ô', ograve: 'ò', atilde: 'ã', amp: '&', nbsp: ' ' }[e.toLowerCase()] ?? m));
  return txt.split(',').map((s) => s.trim()).filter(Boolean);
}
export const faqArticleTypes = () => htmlInfoList(3724);
export const gameAppFormTypes = () => htmlInfoList(3620);

/** Nền tảng Game App (Android, iOS…) cho platformIdList. */
export async function gameAppPlatforms() {
  const j = await api('GET', 'Cmsgameapp/cmsgameappplatformsrh');
  return Array.isArray(j?.data) ? j.data : Array.isArray(j?.object) ? j.object : [];
}

/** Link xem trước bài chưa xuất bản (Hỏi Đáp: staging; Game App: www …/xem-truoc-). */
export const previewUrl = {
  faq: (url, newsId) => `https://staging.thegioididong.com/hoi-dap/xem-truoc/${url}-${newsId}`,
  faqLive: (url, newsId) => `https://www.thegioididong.com/hoi-dap/${url}-${newsId}`,
};
