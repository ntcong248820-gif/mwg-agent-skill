# Hợp đồng API MDM/PIM (đã đối chiếu request thật 05–06/10/2026)

Mọi lệnh là `POST` JSON tới `{mdm.apiBase}{path}` hoặc `{mdm.pimApiBase}{path}`, header
`Authorization: Bearer <access_token>`. Token: IndexedDB `keyval-store` → store `keyval` → key
`MDM_TOKEN` (tab MDM) hoặc `Token` (tab PIM) → `.access_token` (UUID 36 ký tự). JWT `kc_tokens` trong
localStorage **không** dùng được. Token MDM gọi được cả API PIM. ID màn lấy từ config (`config.example.json`).

## rawValues

`{field: [{locale, data}]}`. MDM dùng `locale: "all"`; PIM có field `vi_VN`.
`getinfor` MDM trả **object**; PIM `model/getinfor`, `productvariant/getinfor` trả **chuỗi JSON**.

## Danh mục — `tgdd_category` (cây)

| Việc | Path | Body |
| --- | --- | --- |
| Cả cây | `datatobject/getlistbyroot` | `{objectId, rootId}` → 143 nút, field ở `raw_values` |
| Đọc | `datatobject/getinfor` | `{localeCode, tableId, id, isTranslation:true}` |
| Ghi | `datatobject/update` | object getinfor + `{localeCode, key:id, functionId, keyStartValue:1, keyIncrease:"code", isIncrementKey:true, foreignReferences:[]}` |

`datatobject/getdatatobjectroot` trả NullPointer — không dùng. Field khác: `url`, `code` (= mã danh
mục dùng ở Hãng/Filter, Laptop = 17), `cms_category_id` (Laptop = 44), `keyword_suggest`, cờ `is_*`.

## Hãng — `tgdd_brand_category`

| Việc | Path | Body |
| --- | --- | --- |
| Danh sách | `dataobject/getlist` | `{objectId, functionId, objectCode:"tgdd_brand_category", pageSize, pageIndex, filterParams:[{key:"category_code", value:"17"}], listOrderBy:[]}` |
| Đọc | `dataobject/getinfor` | `{id, tableId, functionId, objectId}` |
| Ghi | `dataobject/update` | `{id, objectId, tableId, rowVersion, isActivated, recordCode, rawValues, functionId, foreignReferences:[], isIncrementKey:true, keyStartValue:1, keyIncrease:"code"}` |

`getlist` **không lọc được theo url** → lấy theo danh mục rồi so. `brand_code` (vd `33-Hp`) không
phải manuId CMS. Field khác: `url`, `logo`, `brand_code`, `related_filter_id`, `display_order`.

## Filter — `tgdd_filter_atb`

Dòng Filter = bản ghi (`dataobject`), giá trị = quan hệ (`datarelation`).

| Việc | Path | Body |
| --- | --- | --- |
| Dòng Filter của danh mục | `dataobject/getlist` | như Hãng, `objectCode:"tgdd_filter_atb"` |
| Giá trị của 1 dòng | `datarelation/getlist2` | `{dataObjectId, functionId, objectId, relationId, filterParams:[{key:"filter_type_attribute_code", value:<record_code dòng>}], pageIndex, pageSize, listOrderBy:null}` |
| Đọc giá trị | `datarelation/getinfor` | `{dataRelation:{id}, relationId}` |
| Ghi giá trị | `datarelation/update` | `{isIncrementKey:false, keyIncrease:"", keyStartValue:null, dataRelation:<object getinfor>, dataObjectId, objectCode:"tgdd_filter_atb", objectId, recordCode:<mã dòng, vd "448">, referenceCode:"filter_type_attribute_code", relationId}` |

`getlist2` lọc được `{key:"url"}` nhưng **chỉ trong 1 dòng** (`dataObjectId`). Laptop: 14 dòng, 171
giá trị, 12 giá trị trống url.

## Ghép URL web

| Trang | URL | Field SEO |
| --- | --- | --- |
| Danh mục | `/{url danh mục}` | `seo_*` |
| Hãng | `/{danh mục}-{url hãng}` (vd `laptop-hp-compaq`) | `seo_*`, `brand_cate_article` |
| Filter / Dòng | `/{danh mục}-{url giá trị}` (url giá trị chỉ là phần đuôi) | `title`, `description`, `filter_inforbox` |
| Hãng + Filter | `/{danh mục}-{url hãng}-{url giá trị}` | `title_brand_filter`, `description_brand_filter` — web thay `[HÃNG]` bằng tên hãng |

Dòng Filter có 2 URL cùng 200, tự canonical: `laptop-neo` (Filter) và `laptop-apple-macbook-neo`
(Hãng+Filter).

## Ảnh — `s3/cdnput` (service PIM, dùng cho cả ô MDM)

Multipart: `resourceName=pim_product`, `localeCode=vi_VN`,
`allowedExtensions=gif,jpeg,jpg,png,tiff,webp`, `multipartFile`. Trả `object.filePath` = URL đầy đủ
`https://cdnv2.tgdd.vn/pim/cdn/images/{yyyymm}/{tên gốc}{HHmmss}.{đuôi}`.

## Sản phẩm PIM (chỉ đọc)

| Việc | Path | Body |
| --- | --- | --- |
| Tìm | `productvariant/getlist` | `{keyword:<mã PIM hoặc tên>, pageIndex, pageSize, companyId, filterParams:[{key:"rootCategoryId",value}, {key:"searchType",value:2}]}` |
| Cây biến thể | `productvariant/getlist4tree` | `{rootCategoryId, companyId, filterParams:[{key:"ModelId", value:<id model>}]}` — không có rowVersion |
| Đọc lá | `productvariant/getinfor` | `{id, isTranslation:true, rootCategoryId, companyId}` — thiếu rootCategoryId trả `object:null` im lặng |
| Đọc model | `model/getinfor` | `{id, isTranslation:true, categoryId:null, rootCategoryId, companyId}` |
| Lịch sử | `productvariant/getchanginglog` | `{resouceId, resourceCode, rootCategoryId, companyId}` (chú ý `resouceId`) |
| Ghi (KHÔNG dùng) | `productvariant/update`, `model/update` | đã đo được; xem traps |

Mã PIM ≠ ID CMS (Acer 205799 ↔ CMS 115368). HTML trang SP core mới có `modelCode=<mã PIM>`.
SP có biến thể (toàn MacBook, 31/176 model Laptop): field SEO ở **lá Màu**; 1 trang = mọi lá Màu của
1 Phiên bản; `product_articles`/`key_features` chép trên mọi lá.
