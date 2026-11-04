# Hợp đồng endpoint CMS

Áp cho `cms.thegioididong.com`. `site=1` TGDĐ, `site=2` ĐMX, `site=16` TopZone — **cùng
một CMS, cùng một session**, không phải nhiều hệ thống.

Hai trang edit cho cùng một sản phẩm: v2 `/v2/Product/Edit` (form `#frmProductSubmit`) và trang
cũ `/Product/Edit?productID=..&site=..` (form `#myForm`). `txtContent` (v2) và `HTMLDescription`
(trang cũ) là **cùng một field** (byte-identical, đo 6/6 ca). `HotReason` **chỉ có ở trang cũ**.

## Đọc

```
GET /v2/Product/Edit?site={1|2}&productId={pid}
```

Nội dung bài nằm ở `#txtContent` (một `<textarea>`), đọc bằng `.value`.

`DOMParser` ở bước này **chỉ** để lấy `textarea.value` và để serialize form.
Không bao giờ dùng `body.innerHTML` của nội dung bài để dựng lại HTML: nó
serialize lại toàn bộ, biến `U+00A0` thành `&nbsp;` và làm lệch hàng chục dòng
không liên quan đến đoạn đang sửa.

Nếu không thấy `#txtContent` → gần như chắc chắn là **mất session**, không phải
pid sai. Kiểm tra bằng cách mở tay 1 trang edit.

## Ghi

```
POST /v2/Product/Submit
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
```

Body = `jQuery('#frmProductSubmit').serializeArray()` (~72-73 field) với 2 field
bị ghi đè:

| Field | Giá trị |
| --- | --- |
| `txtContent` | HTML mới, đầy đủ cả bài |
| `hdType` | `2` |

Thành công: `{"status": 1, "error": "Cập nhật bài viết hoàn tất."}`
(`error` mang thông điệp thành công — đừng đọc tên field mà kết luận là lỗi.)

## Bản đồ `hdType`

| Giá trị | Mục |
| --- | --- |
| 1 | Thông tin chung |
| **2** | **Nội dung bài viết** ← duy nhất skill này được ghi |
| 4 | SEO |
| 6 | Tổng quan |

Sai `hdType` là ghi đè nhầm mục khác của sản phẩm.

## Tương đương `serializeArray()`

Khi chạy headless trên document đã `DOMParser` thì không có jQuery. Quy tắc phải
khớp đúng hành vi jQuery:

- bỏ field không có `name`
- bỏ field `disabled`
- bỏ `input` type `submit`, `button`, `reset`, `image`, `file`
- bỏ `checkbox` / `radio` không `checked`
- `select` nhiều lựa chọn → mỗi option được chọn là một cặp name/value
- còn lại lấy `.value`

## Không có rollback

Mục "Lịch sử cập nhật" của CMS ghi **ai / lúc nào / mục nào**, có diff cho Thông
số kỹ thuật nhưng **không có diff cho Bài viết**, và chỉ giữ **20 entry**.

Hệ quả bắt buộc: backup `txtContent` ra file **trước** mỗi lần ghi. Không backup
thì một lần ghi sai là mất bài, không khôi phục được từ CMS.

## Chống đè bài người khác

Người khác có thể đang sửa tay cùng lúc (đã xảy ra thật: 20 dòng, 04:08-04:31).
Bắt buộc **re-GET sát trước POST** và so với bản đã định vị; lệch thì bỏ dòng,
không ghi. Không có cơ chế khoá nào khác.

## Ghi HotReason (`--field hotReason`, site 16 TopZone)

Site 16 đảo vai: bài ở `HotReason`, `HTMLDescription`/`txtContent` là gallery. Site 1/2 ngược lại
(`HotReason` là gallery ~1-5KB). Đo 25/09/2026, 370977 + 370982.

| pid | site | `HotReason` | `HTMLDescription` = `txtContent` |
| --- | --- | --- | --- |
| 370977 | 1 / 2 / 16 | 5.286 / 5.275 / **33.505** | **58.401** / **47.518** / 5.186 |
| 370982 | 1 / 2 / 16 | 5.277 / 1.364 / **34.998** | **49.809** / **49.076** / 5.230 |

**Đọc**: `GET /Product/Edit?productID={pid}&site={site}` → `#hotreason` (`textarea name=HotReason`).
Có sẵn trong HTML server trả về, không cần chạy JS.

**Ghi** (suy từ HTML/JS trang; **đã kiểm bằng POST thật 26/09/2026** — 370982, 370977 site 16, mode `apply-ops`: HotReason lưu byte-exact đúng HTML gửi, `diffFields` 0 field khác; 2 rủi ro dưới **không xảy ra**):

```
POST /Product/Edit
Content-Type: multipart/form-data (trình duyệt tự sinh boundary)
body = serializeForm(#myForm) (~127 cặp) + HotReason=<bài mới> + UpdateHTML=Lưu lại
```

- Nút "Lưu lại" của box "Bài viết mô tả TGDD/DMX/Topzone" là `input[type=submit][name=UpdateHTML]`
  → submit **cả form**, full-page. Server phân mục bằng **tên nút** (`UpdateHTML` vs `UpdateDetail`),
  không có `hdType`. Các mục khác lưu bằng AJAX riêng (`UpdateGeneral`, `UpdateSEO`…).
- Box chứa: `HotReason`, `HTMLDescription`, `HtmlSlider`, `ShortDescription`, `Advantage`,
  `DisAdvantage`, `PromotionLink`, `Area`, file `contentFile`/`DUserManual`, checkbox `SaveAllProductHTML`.
- `SaveAllProductHTML` = **"Lưu tất cả các site"**. Runner luôn gỡ khỏi payload.
- `validateSubmitContent()` chỉ ép `LangID=vi-VN` cho site 1/2/10/14/16 → runner chặn (ABORT) khi
  `LangID`, `ProductID`, `SiteID` của form lệch dòng đang ghi.
- Không có anti-forgery token. Phản hồi là trang HTML, không phải JSON → thành công chỉ xác định
  bằng GET lại: byte-exact `HotReason` + `diffFields` trên toàn bộ form trang cũ (chỉ `HotReason`
  được đổi). Đo 25/09: 2 lần GET liên tiếp cho 127 field giống hệt → không có field dao động gây FAIL giả.
- `/v2/Product/Submit` **không ghi được** `HotReason` (v2 không có field này).

Rủi ro chỉ lộ ra ở lần ghi thật đầu tiên (nên pilot 1 bài):

1. UI đi qua CKEditor (`updateElement`) trước submit; runner gửi HTML thô. Server/CKEditor có
   normalize không → byte-exact sẽ báo `FAIL` nếu có.
2. `UpdateHTML` có ghi field ngoài box từ payload không. Payload gửi lại nguyên giá trị đang có,
   và `diffFields` bắt mọi field đổi.
