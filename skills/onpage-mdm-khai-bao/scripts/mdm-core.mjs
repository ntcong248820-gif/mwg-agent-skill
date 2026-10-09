/**
 * mdm-core.mjs — logic thuần của skill MDM (không mạng, không trình duyệt) để test bằng Node.
 *
 * Gồm: danh sách field SEO được phép ghi theo màn, dựng payload update đúng shape giao diện MDM
 * gửi (đã đối chiếu request thật 05/10/2026), áp sửa vào rawValues, chặn rơi key, so readback,
 * và giải URL trang web → màn + bản ghi.
 *
 * MDM ghi ĐÈ CẢ BẢN GHI: key nào thiếu trong rawValues gửi lên là field đó bị xoá. Vì vậy payload
 * luôn dựng từ bản getinfor vừa đọc, chỉ đổi đúng key được sửa.
 */

/** Field SEO được phép ghi theo màn. Ngoài danh sách = từ chối (url, code, cờ is_*, thứ tự…). */
export const WRITABLE_FIELDS = {
  category: ['seo_title', 'seo_description', 'seo_article'],
  brand: ['seo_title', 'seo_description', 'seo_keyword', 'brand_cate_article'],
  'filter-value': [
    'title', 'description', 'title_brand_filter', 'description_brand_filter',
    'main_keyword', 'filter_inforbox', 'filter_value_tooltip',
  ],
};

export const SCREENS = Object.keys(WRITABLE_FIELDS);

/** Website public — không phải giá trị nội bộ nên không để trong file config. */
export const WEB_ORIGIN = 'https://www.thegioididong.com';

export class MdmError extends Error {
  constructor(message, exitCode = 1) {
    super(message);
    this.exitCode = exitCode;
  }
}

/** Đọc data của 1 key rawValues dạng [{locale, data}] (MDM) — lấy entry đầu. */
export function rawGet(rawValues, key) {
  const v = rawValues?.[key];
  if (Array.isArray(v)) return v.length ? v[0].data : undefined;
  return v;
}

/**
 * Áp sửa vào bản sao rawValues. edits = {field: newString}.
 * - field phải nằm trong WRITABLE_FIELDS[screen];
 * - key đã có thì phải đúng 1 entry (nhiều locale = không đoán, dừng);
 * - key chưa có thì tạo [{locale:'all', data}] như giao diện MDM.
 * Trả {rawValues, changed:[{field, before, after}]}; field không đổi giá trị bị bỏ khỏi changed.
 */
export function applyEdits(screen, rawValues, edits) {
  const allow = WRITABLE_FIELDS[screen];
  if (!allow) throw new MdmError(`màn "${screen}" không hỗ trợ — chọn ${SCREENS.join(' | ')}`, 2);
  const out = JSON.parse(JSON.stringify(rawValues || {}));
  const changed = [];
  for (const [field, value] of Object.entries(edits)) {
    if (!allow.includes(field)) throw new MdmError(`field "${field}" không được ghi ở màn ${screen} (cho phép: ${allow.join(', ')})`, 2);
    if (typeof value !== 'string') throw new MdmError(`giá trị field "${field}" phải là chuỗi`, 2);
    const cur = out[field];
    if (cur !== undefined && (!Array.isArray(cur) || cur.length !== 1)) {
      throw new MdmError(`field "${field}" có ${Array.isArray(cur) ? cur.length : 'không phải mảng'} entry — không đoán locale, dừng`, 2);
    }
    const before = cur === undefined ? undefined : cur[0].data;
    if (before === value) continue;
    if (cur === undefined) out[field] = [{ locale: 'all', data: value }];
    else out[field] = [{ ...cur[0], data: value }];
    changed.push({ field, before, after: value });
  }
  return { rawValues: out, changed };
}

/** MDM xoá field bị thiếu → chặn mọi payload làm rơi key của bản vừa đọc. */
export function assertNoDroppedKeys(beforeRaw, afterRaw) {
  const dropped = Object.keys(beforeRaw || {}).filter((k) => !(k in (afterRaw || {})));
  if (dropped.length) throw new MdmError(`payload làm rơi key ${dropped.join(', ')} — MDM sẽ xoá các field này, dừng`, 2);
}

/** Dựng body update cho từng màn từ object getinfor vừa đọc + rawValues đã sửa. */
export function buildUpdate(screen, info, rawValues, cfg) {
  if (screen === 'category') {
    return {
      ...info, localeCode: 'vi_VN', rawValues, key: info.id, functionId: cfg.category.functionId,
      keyStartValue: 1, keyIncrease: 'code', isIncrementKey: true, foreignReferences: [],
    };
  }
  if (screen === 'brand') {
    return {
      localeCode: 'vi_VN', id: info.id, objectId: cfg.brand.objectId, tableId: cfg.brand.tableId,
      rowVersion: info.rowVersion, isActivated: info.isActivated, recordCode: info.recordCode, rawValues,
      functionId: cfg.brand.functionId, foreignReferences: [], isIncrementKey: true, keyStartValue: 1, keyIncrease: 'code',
    };
  }
  if (screen === 'filter-value') {
    const recordCode = String(rawGet(info.rawValues, 'filter_type_attribute_code') ?? '');
    if (!recordCode) throw new MdmError('giá trị Filter thiếu filter_type_attribute_code — không biết dòng Filter cha', 2);
    return {
      localeCode: 'vi_VN', isIncrementKey: false, keyIncrease: '', keyStartValue: null,
      dataRelation: { ...info, rawValues }, dataObjectId: info.dataObjectId, objectCode: 'tgdd_filter_atb',
      objectId: cfg.filter.objectId, recordCode, referenceCode: 'filter_type_attribute_code', relationId: cfg.filter.relationId,
    };
  }
  throw new MdmError(`màn "${screen}" không hỗ trợ`, 2);
}

/** Body getinfor theo màn. */
export function buildGetInfor(screen, id, cfg) {
  if (screen === 'category') return { localeCode: 'vi_VN', tableId: cfg.category.tableId, id, isTranslation: true };
  if (screen === 'brand') return { localeCode: 'vi_VN', id, tableId: cfg.brand.tableId, functionId: cfg.brand.functionId, objectId: cfg.brand.objectId };
  if (screen === 'filter-value') return { localeCode: 'vi_VN', dataRelation: { id }, relationId: cfg.filter.relationId };
  throw new MdmError(`màn "${screen}" không hỗ trợ`, 2);
}

export const ENDPOINT = {
  category: { read: 'datatobject/getinfor', write: 'datatobject/update' },
  brand: { read: 'dataobject/getinfor', write: 'dataobject/update' },
  'filter-value': { read: 'datarelation/getinfor', write: 'datarelation/update' },
};

/** JSON ổn định (key sắp xếp) để so bản đọc lại với bản kỳ vọng, không phụ thuộc thứ tự key. */
export function stableStringify(v) {
  if (Array.isArray(v)) return `[${v.map(stableStringify).join(',')}]`;
  if (v && typeof v === 'object') return `{${Object.keys(v).sort().map((k) => `${JSON.stringify(k)}:${stableStringify(v[k])}`).join(',')}}`;
  return JSON.stringify(v);
}

/**
 * So rawValues đọc lại với rawValues đã gửi. MDM lưu y nguyên từng byte (không trim, không đổi
 * entity) nên so tuyệt đối. Trả danh sách key lệch (rỗng = khớp).
 */
export function diffRaw(expected, actual) {
  const keys = new Set([...Object.keys(expected || {}), ...Object.keys(actual || {})]);
  return [...keys].filter((k) => stableStringify(expected?.[k]) !== stableStringify(actual?.[k])).sort();
}

/** Lỗi khoá phiên bản: server từ chối vì có người ghi xen vào. */
export function isRowVersionConflict(res) {
  return !!res && res.error === true && res.errorReason === 'row_version';
}

/** Tham số theo dõi/cache không đổi trang đích — bỏ qua. `amp;x` là dấu vết `&amp;` trong link cũ. */
const IGNORED_PARAM = /^(itm_.*|utm_.*|gclid|fbclid|clearcache|amp;.*)$/i;

/** Tách query của URL listing → {g} hoặc ném exit 2 với tham số chưa hỗ trợ. */
export function listingQuery(searchParams) {
  let g = null;
  for (const [k, v] of searchParams) {
    if (IGNORED_PARAM.test(k)) continue;
    if (k === 'g') {
      if (!v) throw new MdmError('?g= rỗng', 2);
      if (g !== null) throw new MdmError('nhiều tham số ?g= — chỉ hỗ trợ một', 2);
      g = v;
    } else if (k === 'p') {
      throw new MdmError('trang lọc giá ?p= không có bản ghi MDM để ghi (màn tgdd_filter_price chỉ có mức giá, không có title/mô tả/infobox — đo lại 09/10/2026); title là mẫu cố định của web. chờ IT khởi tạo vùng khai báo SEO cho Filter giá', 2);
    } else {
      throw new MdmError(`tham số ?${k}= chưa hỗ trợ — bỏ query hoặc tra tay rồi dùng --screen/--id`, 2);
    }
  }
  return { g };
}

/** URL web → slug. Trang SP có 2 đoạn (/laptop/ten-sp) → kind product. */
export function parseWebUrl(url, webOrigin) {
  let u;
  try { u = new URL(url, webOrigin); } catch { throw new MdmError(`URL không hợp lệ: ${url}`, 2); }
  if (webOrigin && u.origin !== new URL(webOrigin).origin) throw new MdmError(`URL không thuộc ${webOrigin}: ${url}`, 2);
  const parts = u.pathname.split('/').filter(Boolean);
  if (parts.length === 1) return { kind: 'listing', slug: parts[0], g: listingQuery(u.searchParams).g };
  if (parts.length === 2) return { kind: 'product', category: parts[0], slug: parts[1] };
  throw new MdmError(`không nhận dạng được loại trang: ${u.pathname}`, 2);
}

/** Danh mục có url là tiền tố của slug, dài nhất trước (may-tinh-de-ban trước may-tinh). */
export function categoryCandidates(slug, categories) {
  return categories
    .filter((c) => c.url && (slug === c.url || slug.startsWith(`${c.url}-`)))
    .sort((a, b) => b.url.length - a.url.length);
}

/**
 * Giải phần còn lại sau tiền tố danh mục.
 * brands: [{id, url, name}] của danh mục; filterValues: [{id, url, name, recordCode, filterName}].
 * Trả {screen, id, variant, ...} hoặc null; nhiều cách hiểu → ném lỗi, không chọn bừa.
 */
export function resolveRest(rest, { brands, filterValues }) {
  const hits = [];
  for (const v of filterValues) if (v.url === rest) hits.push({ screen: 'filter-value', id: v.id, variant: 'filter', value: v });
  for (const b of brands) {
    if (b.url === rest) hits.push({ screen: 'brand', id: b.id, variant: 'brand', brand: b });
    if (rest.startsWith(`${b.url}-`)) {
      const tail = rest.slice(b.url.length + 1);
      for (const v of filterValues) if (v.url === tail) hits.push({ screen: 'filter-value', id: v.id, variant: 'brand-filter', brand: b, value: v });
    }
  }
  if (hits.length > 1) {
    throw new MdmError(`"${rest}" khớp ${hits.length} cách: ${hits.map((h) => `${h.variant}:${h.id}`).join(', ')} — dừng, chỉ định --screen/--id`, 2);
  }
  return hits[0] || null;
}

/** Field SEO mặc định cần xem theo kiểu trang (trang Hãng+Filter dùng bộ *_brand_filter). */
export function seoFieldsFor(resolved) {
  if (resolved.screen === 'category') return { title: 'seo_title', description: 'seo_description', article: 'seo_article' };
  if (resolved.screen === 'brand') return { title: 'seo_title', description: 'seo_description', article: 'brand_cate_article' };
  if (resolved.variant === 'brand-filter') return { title: 'title_brand_filter', description: 'description_brand_filter', article: 'filter_inforbox' };
  return { title: 'title', description: 'description', article: 'filter_inforbox' };
}
