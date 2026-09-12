# Hợp đồng endpoint CMS

Áp cho `cms.thegioididong.com`. `site=1` TGDĐ, `site=2` ĐMX — **cùng một CMS,
cùng một session**, không phải 2 hệ thống.

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
