# Hợp đồng endpoint — air bài Infobox lên News CMS

Đo sống 18/09/2026 trên News CMS TGDĐ. Mọi con số dưới đây là đo thật, không suy đoán.
`{newsId}` trong tài liệu này là placeholder.

---

## 1. Upload ảnh — `UploadManyImages`

```http
POST /v2/Common/UploadManyImages
Content-Type: multipart/form-data
```

| Field | Giá trị |
| --- | --- |
| `ID` | `#hdNewsId` — **quyết định thư mục đích** |
| `site` | `#hdSiteId` (1 TGDĐ · 2 ĐMX · 16 TopZone) |
| `type` | `3` |
| `file0`, `file1`, … | các file ảnh, nhiều file trong 1 request |

**Thành công** → trả **HTML fragment** (không phải JSON). Rút URL bằng regex:

```
https://cdnv2.tgdd.vn/mwg-static/common/News/{ID}/{tên file}
```

**Thất bại** → JSON `{"status":-1,"error":"Tên file đã tồn tại"}`.
CMS **từ chối ghi đè** — đây là chốt idempotent miễn phí, chạy lại không nhân đôi.

Đo thật: 11 ảnh / 1 request = 9,9s. 1 ảnh = 3,0s. Giới hạn 10MB mỗi file.
File lên CDN **khớp byte tuyệt đối** với file gốc; EXIF (Artist, Copyright,
ImageDescription) giữ nguyên.

### Thư mục đích = `hdNewsId` tại thời điểm upload

| Trang | `hdNewsId` | Ảnh vào |
| --- | --- | --- |
| Bài đã có ID | `{newsId}` | `common/News/{newsId}/` |
| Trang tạo mới `newsId=0` | `0` | `common/News/0/` — kho chung |

Không phải "CMS luôn đẩy vào `/News/0/`". Ảnh lịch sử nằm ở `/News/0/` chỉ vì được
upload lúc bài chưa có ID. Muốn ảnh gọn theo bài thì **tạo bài trước, lấy `newsId`,
rồi mới upload**.

### Đường upload KHÁC — đừng nhầm

`PostImage?type=56` (nút ảnh trong TinyMCE) là endpoint khác hẳn:

| | `UploadManyImages` | `PostImage?type=56` |
| --- | --- | --- |
| Thư mục | `common/News/{ID}/` | `tgdd/Common/` kho chung |
| Nhận News ID | có | **không** (thêm `productId` vẫn vô tác dụng, đã thử) |
| Chất lượng | giữ nguyên byte | **nén lại** 299.280 → 138.109 |
| File/request | nhiều | 1 |
| Response | HTML | JSON có `imageUrl` |

Các `type` khác của `PostImage`: `2` Html Description (trang Hãng/Product) ·
`78` thumbnail bài tin · `12` ảnh nhỏ/lớn sản phẩm.

---

## 2. Ghi thân bài — `SubmitNewsEdit`

```http
POST /v2/News/SubmitNewsEdit
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
```

Payload = `getDataSubmitNews()` (40 field), serialize bằng `jQuery.param(data)`.

### Field thân bài: `ContentNews`, KHÔNG phải `contentNewsAva`

Dòng cuối `getDataSubmitNews()`:

```js
var data = GetAllFormData('#submitEditNews');                     // có contentNewsAva (textarea)
data.ContentNews = tinymce.get("contentNewsAva").getContent();    // ← server ghi CÁI NÀY
```

| Mục tiêu | Payload |
| --- | --- |
| **Đổi thân bài** | set `data.ContentNews = html` (và `contentNewsAva` cho khớp) |
| **Chỉ sửa chuyên mục, giữ thân bài** | **xoá** `ContentNews` khỏi payload |

Áp nhầm là mất trắng một lượt POST **mà không có lỗi nào**: CMS vẫn trả
`{"status":1,"error":"Cập nhật bài tin thành công."}` trong 265ms còn thân bài y nguyên.
POST ghi thật (bài 40K, 12 ảnh) mất **31s**. Nhanh bất thường = không ghi gì.

### Ba nguồn nội dung lệch nhau — đo trên cùng một bài

| Nguồn | Độ dài |
| --- | --- |
| DB thật (GET tĩnh `#contentNewsAva`) | 17.456 |
| `getDataSubmitNews().contentNewsAva` | 17.622 ← TinyMCE format lại |
| `getDataSubmitNews().ContentNews` | 20.986 |

Luôn ghi đè bằng HTML của mình. Đừng lấy bất kỳ bản nào ở trên làm nguồn.

### Response

| `status` | Nghĩa |
| --- | --- |
| `> 1` | **Chính là `newsId` mới** (bài vừa tạo) |
| `== 1` | Cập nhật bài cũ thành công |
| `<= 0` | Lỗi, đọc `error` |

---

## 3. Taxonomy — bẫy mất chuyên mục

Chuyên mục đang gán **chỉ** nằm ở `<ul class="sticker newscategory"><li data-id="…">`.
Checkbox `input[name='NewsCate']` luôn `checked=false` — chỉ là UI chọn.

`getDataSubmitNews()` gộp sticker thành `LstCategoryId` / `LstCategoryName`
(cùng cơ chế: `LstPostFormatId` / `LstPostFormatName`). Submit thiếu `LstCategoryId`
= CMS hiểu "bỏ tick toàn bộ" → **mất sạch chuyên mục, không có thông báo lỗi nào**.
Đã xảy ra thật trên production với gần trọn một lô bài.

Bài tạo mới có **0 sticker** → phải chủ động set. Bài cũ → giữ nguyên.

Nghiệm thu từ ngoài, không cần đăng nhập CMS: trang live có `BreadcrumbList`, phần tử
vị trí 3 trả tên chuyên mục thật; bài mất sạch rơi về nhãn `Bài viết tin tức`.

---

## 4. Tạo bài mới — field bắt buộc

Rút từ `validateSubmitNews()` (client-side, nhưng phản ánh ràng buộc server):

Tiêu đề ≤130 · Url ≤100 (kể cả domain + Id) · Ngành hàng kinh doanh
(`cboProductCategory`) · Dạng bài · Chuyên mục · Nội dung · **Thumbnail** ·
Editor/biên tập · Tag · Title SEO ≤70 · Meta Description ≤170 · Meta keyword ≤170 ·
Bài tin liên quan ≤500.

`cboStatus`: `draft` | `pending` (mặc định bài mới) | `approved` | `actived`.
Tài khoản không đủ quyền thì không đặt được `approved`/`actived`.

---

## 5. Trang NewsEdit — chi tiết DOM cần biết

- Form chính `#submitEditNews`.
- **2 element trùng id `fileUploadContentNews`.** Element thứ nhất có **2 change
  handler** (chạm là upload 2 lần); element thứ hai **không có handler** — dùng nó làm
  input nạp liệu qua CDP.
- `#contentNewsAva` là textarea thân bài; `#hdNewsId`, `#hdSiteId`, `#hdCurrentStatus`
  là hidden field cần đọc.

---

## 6. Ngoài scope — 2 loại trang Infobox khác

Infobox có 4 nhãn loại trang nhưng chỉ 3 endpoint:

| Loại | Endpoint | Ghi chú |
| --- | --- | --- |
| Filter (ngành hàng + dòng) | `/v2/News/NewsEdit` | **skill này** |
| Hãng | `POST /v2/Product/ManufactureSubmit`, `GetAllFormData('#frmManufactureSubmit')`, nội dung ở `txtHtmlDescription` | chưa làm |
| Ngành hàng | `POST /Category/UpdateCategory`, payload `{arrParam: ArrParams}` **mảng vị trí**, nội dung lấy qua `CKEDITOR.getData()` | rủi ro cao, nên làm tay |

Payload trang Ngành hàng là **mảng theo vị trí, không phải field có tên** — CMS đổi
thứ tự là ghi nhầm ô. Đó là lý do khuyến nghị làm tay.
