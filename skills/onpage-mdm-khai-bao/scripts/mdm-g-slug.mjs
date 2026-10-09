/**
 * mdm-g-slug.mjs — trang lọc `?g=slug` → giá trị Filter trong MDM (logic thuần, không mạng).
 *
 * Đo 06/10/2026: title/mô tả/infobox của `?g=slug` đến từ giá trị `tgdd_filter_atb` có `url` RỖNG;
 * slug `g=...` không nằm trong MDM mà catalog web phát ra trong HTML trang ngành hàng:
 *   ...,"code":448,"childFilter":[{"name":"Gaming","sortName":"","filterId":108,"logo":"...","url":"g=laptop-gaming",...
 * `code` của nhóm = mã dòng Filter (`filter_type_attribute_code`), `filterId` = `attribute_value`.
 * attribute_value LẶP ở nhiều dòng (màn hình: mã 1 có ở nhiều dòng) nên khoá nối đúng là
 * (mã dòng Filter, attribute_value), không phải riêng attribute_value.
 * Trang lọc giá `?p=` không có field SEO trong MDM (màn tgdd_filter_price): không hỗ trợ.
 */
import { MdmError } from './mdm-core.mjs';

export { listingQuery } from './mdm-core.mjs';

/**
 * HTML trang ngành hàng (core mới) → Map slug → [{group, filterId, name}].
 * Payload nhúng trong chuỗi JS nên dấu " bị escape thành \"; gỡ trước khi so.
 */
export function parseCatalogGSlugs(html) {
  const s = String(html).replace(/\\"/g, '"');
  const re = /"code":(\d+),"childFilter":\[|"name":"((?:[^"\\]|\\.)*)","sortName":"[^"]*","filterId":(\d+),"logo":"[^"]*","url":"g=([^"]*)"/g;
  const out = new Map();
  const seen = new Set();
  let group = null;
  let m;
  while ((m = re.exec(s))) {
    if (m[1] !== undefined) { group = m[1]; continue; }
    if (group === null) continue;
    const key = `${m[4]}|${group}|${m[3]}`;
    if (seen.has(key)) continue;
    seen.add(key);
    let name = m[2];
    try { name = JSON.parse(`"${m[2]}"`); } catch { /* giữ nguyên chuỗi thô */ }
    if (!out.has(m[4])) out.set(m[4], []);
    out.get(m[4]).push({ group, filterId: m[3], name });
  }
  return out;
}

/**
 * Slug g → giá trị Filter. filterValues: [{id, recordCode, attributeValue, url, name, filterName}].
 * Không có slug trong catalog, slug thuộc nhiều nhóm, hoặc không đúng 1 giá trị MDM → ném, không chọn bừa.
 */
export function resolveGSlug(slug, catalog, filterValues) {
  const entries = catalog.get(slug);
  if (!entries || !entries.length) {
    throw new MdmError(`slug g=${slug} không có trong catalog web của ngành hàng (đã thử ${catalog.size} slug g=) — kiểm slug thật trên trang`, 5);
  }
  if (entries.length > 1) {
    throw new MdmError(`slug g=${slug} thuộc ${entries.length} nhóm: ${entries.map((e) => `${e.group}/${e.filterId}`).join(', ')} — dừng, chỉ định --screen/--id`, 2);
  }
  const { group, filterId, name } = entries[0];
  const hits = filterValues.filter((v) => String(v.recordCode) === group && String(v.attributeValue) === filterId);
  if (hits.length !== 1) {
    throw new MdmError(`g=${slug} → dòng Filter ${group}, giá trị ${filterId} ("${name}"): MDM có ${hits.length} bản ghi khớp, cần đúng 1`, hits.length ? 2 : 5);
  }
  return hits[0];
}
