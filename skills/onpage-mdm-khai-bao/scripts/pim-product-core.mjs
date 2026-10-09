/**
 * pim-product-core.mjs — logic thuần cho ghi field SP trên PIM (không mạng): Title, Description,
 * bài viết `product_articles`, đặc điểm nổi bật `key_features`.
 *
 * Hai kiểu sản phẩm (đo thật 05–06/10/2026):
 * - SP thường (không biến thể): title/description nằm ở MODEL → `model/update`.
 * - SP có biến thể (vd MacBook): title/description nằm ở từng LÁ Màu → `productvariant/update`,
 *   rowVersion riêng từng lá; ghi 1 lá KHÔNG lan sang lá khác, nên 1 trang = ghi đủ mọi lá Màu của
 *   Phiên bản đó.
 *
 * Khác MDM: PIM gộp theo key (bỏ key không xoá field), getinfor trả rawValues là CHUỖI JSON,
 * field SEO dùng locale "vi_VN". Payload dựng lại đúng shape giao diện PIM gửi khi bấm Lưu (đã so
 * khớp request thật).
 */
import { MdmError } from './mdm-core.mjs';

/**
 * Field SP được phép ghi, kèm locale khi field chưa có trên bản ghi (đo 09/10/2026: title/description
 * lưu `vi_VN`; bài viết `product_articles` và đặc điểm nổi bật `key_features` lưu `all`).
 */
export const PRODUCT_FIELD_LOCALE = { title: 'vi_VN', description: 'vi_VN', product_articles: 'all', key_features: 'all' };
export const PRODUCT_FIELDS = Object.keys(PRODUCT_FIELD_LOCALE);
/** Field HTML dài (bài viết) — ghi bằng --set-file hoặc product-ops, plan chỉ in độ dài + sha256. */
export const PRODUCT_HTML_FIELDS = ['product_articles', 'key_features'];

export const parseRaw = (rv) => (typeof rv === 'string' ? JSON.parse(rv) : rv || {});

/**
 * Áp sửa vào bản sao rawValues SP. Key đã có phải đúng 1 entry; chưa có thì tạo theo locale đã đo của
 * field (PRODUCT_FIELD_LOCALE). Không ghi rỗng: PIM gộp theo key nên "xoá" bài là ghi "" — việc đó
 * phải làm tay. Trả {rawValues, changed:[{field, before, after}]}.
 */
export function applyProductEdits(rawValues, edits) {
  const out = JSON.parse(JSON.stringify(rawValues || {}));
  const changed = [];
  for (const [field, value] of Object.entries(edits)) {
    if (!PRODUCT_FIELDS.includes(field)) throw new MdmError(`field "${field}" không được ghi cho sản phẩm (cho phép: ${PRODUCT_FIELDS.join(', ')})`, 2);
    if (typeof value !== 'string') throw new MdmError(`giá trị field "${field}" phải là chuỗi`, 2);
    if (!value.trim()) throw new MdmError(`field "${field}" rỗng — không ghi trống (xoá nội dung phải làm tay trên PIM)`, 2);
    const cur = out[field];
    if (cur !== undefined && (!Array.isArray(cur) || cur.length !== 1)) {
      throw new MdmError(`field "${field}" có ${Array.isArray(cur) ? cur.length : 'không phải mảng'} entry — không đoán locale, dừng`, 2);
    }
    const before = cur === undefined ? undefined : cur[0].data;
    if (before === value) continue;
    out[field] = cur === undefined ? [{ locale: PRODUCT_FIELD_LOCALE[field], data: value }] : [{ ...cur[0], data: value }];
    changed.push({ field, before, after: value });
  }
  return { rawValues: out, changed };
}

/** Lá biến thể của đúng trang: lá cấp sâu nhất có url = slug trang. */
export function leavesForPage(treeNodes, slug) {
  const nodes = treeNodes || [];
  if (!nodes.length) return [];
  const deepest = Math.max(...nodes.map((n) => n.lvl));
  return nodes.filter((n) => n.lvl === deepest && (parseRaw(n.rawValues).url || [])[0]?.data === slug);
}

/**
 * Body productvariant/update cho 1 lá. leaf = getinfor của lá, node = nút cây (lvl), model =
 * model/getinfor của model gốc (familyVariantId, categoryId lấy ở model — getinfor lá trả giá trị
 * khác giao diện gửi).
 */
export function buildLeafUpdate(leaf, node, model, rawValues, cfg) {
  return {
    localeCode: 'vi_VN', code: leaf.code, id: leaf.id, lvl: node.lvl, rootId: model.id, key: leaf.id,
    rawValues, rowVersion: leaf.rowVersion, isActivated: leaf.isActivated,
    familyVariantId: model.familyVariantId, rootCategoryId: cfg.category.rootId, categoryId: model.categoryId,
    companyId: cfg.pimCompanyId, modelId: leaf.modelId,
  };
}

const MODEL_DROP = new Set(['categoryTeams', 'familyVariantId', 'familyVariantCode', 'isShowSync', 'rowOrder', 'errorNote', 'error']);

/** Body model/update cho SP không biến thể. family = datasource/getfamilyinfor của model. */
export function buildModelUpdate(model, rawValues, family, cfg) {
  const img = (rawValues.image || [])[0]?.data;
  const name = (rawValues.product_name || [])[0]?.data;
  if (!name) throw new MdmError(`model ${model.code} thiếu product_name — không dựng được payload`, 2);
  const out = { localeCode: 'vi_VN' };
  for (const [k, v] of Object.entries(model)) if (!MODEL_DROP.has(k) && k !== 'rawValues') out[k] = v;
  return {
    ...out, code: model.code, name, image: Array.isArray(img) && img[0] ? img[0].url : null,
    attributeGroups: null, attributes: null,
    lableAttributeCode: family.lableAttributeCode, imageAttributeCode: family.imageAttributeCode, familyName: family.name,
    familyVariants: family.familyVariants, familyVariantOptions: family.familyVariants,
    rootCategoryId: cfg.category.rootId, companyId: cfg.pimCompanyId, rawValues,
  };
}
