# Hợp đồng endpoint — air bài Infobox lên CMS (mode --news và --brand)

Đo sống 18/09/2026 trên `cms.thegioididong.com`, bài LOQ `newsId=1581619`. Mọi con số
dưới đây là đo thật, không suy đoán.

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
| Bài đã có ID | `1581619` | `common/News/1581619/` |
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
Thêm `?skip=1` khi `#hdIsSkipSecurity` = `1`.

### Field thân bài: `ContentNews`, KHÔNG phải `contentNewsAva`

Dòng cuối `getDataSubmitNews()` trong `/v2/Scripts/news_v2.js`:

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

### Ba nguồn nội dung lệch nhau — đo trên chính bài 1581619

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
= CMS hiểu "bỏ tick toàn bộ" → mất sạch chuyên mục (sự cố 17/09/2026, 32/33 bài).

Bài Infobox bắt buộc: `data-id="2424"` = **"Mô tả dòng sản phẩm"**.
Bài tạo mới có **0 sticker** → phải chủ động set. Bài cũ → giữ nguyên.

Nghiệm thu từ ngoài, không cần đăng nhập CMS: trang live có `BreadcrumbList`, phần tử
vị trí 3 trả tên chuyên mục thật; bài mất sạch rơi về nhãn `Bài viết tin tức`.

---

## 4. Tạo bài mới — field bắt buộc

Rút từ `validateSubmitNews()` (client-side, nhưng phản ánh ràng buộc server):

Tiêu đề ≤130 · Url ≤100 (kể cả domain + Id) · Ngành hàng kinh doanh
(`cboProductCategory`, 572 option) · Dạng bài · Chuyên mục · Nội dung · **Thumbnail** ·
Editor/biên tập · Tag · Title SEO ≤70 · Meta Description ≤170 · Meta keyword ≤170 ·
Bài tin liên quan ≤500.

`cboStatus`: `draft` | `pending` (mặc định bài mới) | `approved` | `actived`.
Quyền ở `#hdIsActiveRole` / `#hdIsApproveRole`; tài khoản có đủ 2 quyền thì cả hai đều `1`.

---

## 5. Trang NewsEdit — chi tiết DOM cần biết

- Form chính `#submitEditNews`: 273 field (bài mới) / tương đương (bài cũ).
- **2 element trùng id `fileUploadContentNews`.** Element thứ nhất có **2 change
  handler** (chạm là upload 2 lần); element thứ hai **không có handler** — dùng nó làm
  input nạp liệu qua CDP.
- `#contentNewsAva` là textarea thân bài; `#hdNewsId`, `#hdSiteId`, `#hdCurrentStatus`,
  `#hdIsSkipSecurity` là hidden field cần đọc.

---

## 6. Mode `--brand` — trang Hãng `ManufactureEdit`

Đo sống 19/09/2026 trên `manuId=122` (HP) `categoryId=44` (laptop) `site=1`.

```http
POST /v2/Product/ManufactureSubmit
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

Payload = `GetAllFormData('#frmManufactureSubmit')`, serialize bằng `jQuery.param(data)`.

### Form serialize 1:1 — KHÔNG có bẫy taxonomy

```
formFieldCount: 44   dataKeyCount: 44
missingFromData: []  synthesized: []
```

Không `ul.sticker`, không field nào do JS tổng hợp. Khác bản chất với `NewsEdit`.

### Bẫy duy nhất: `cbIsActived`

```js
function GetAllFormData(form) {
    var unindexed_array = $(form).serializeArray();     // ← BỎ checkbox không tick
    var indexed_array = {};
    $.map(unindexed_array, function (n, i) { indexed_array[n['name']] = n['value']; });
    return indexed_array;
}
```

| Trạng thái | Số key |
| --- | --- |
| có tick | 44 |
| bỏ tick | **43** — `cbIsActived` biến mất |

Giá trị là chuỗi `"Sử dụng"`, element **không có `id`** (chỉ `name`), nên
`getElementById('cbIsActived')` trả `null`. Mất key này nhiều khả năng = tắt hãng.

### Bốn editor TinyMCE, drift trên field ta ghi

`txtHtmlDescription` · `txtDescription` · `txtIntroDescription` · `txtReturnPolicy`.

| Nguồn | Độ dài |
| --- | --- |
| DB thật (`textarea`) | 22.023 |
| TinyMCE `getContent()` | 26.485 |
| `GetAllFormData()` | **22.154** |

### Hàm submit và response

```js
$.ajax({ url: rootUrl+"Product/ManufactureSubmit", type:"POST",
         data: GetAllFormData("#frmManufactureSubmit"),
  success: function(n){ n.status==-1 ? alert(n.error)
    : (alert(n.status==1 ? "Thêm mới thành công." : "Cập nhật thành công."),
       window.location.href = rootUrl+"Product/Manufacture?categoryId="+n.error) } })
```

Không validate client, không tham số `skip`. **Thành công là điều hướng đi trang khác**
→ phải POST bằng `fetch`, đừng gọi `ManufactureSubmit()`.

| `status` | Nghĩa |
| --- | --- |
| `-1` | Lỗi, đọc `error` |
| `1` | Thêm mới |
| còn lại | Cập nhật — giá trị **chính là `manuId`**; `error` mang `categoryId` |

Đo thật lần ghi đầu: `{"status":122,"error":"44"}`, **1.184ms**, `byteExact: true`,
43/43 field khác không đổi. **Mode này không có tín hiệu thời gian** — 1,2s là ghi thật,
đừng đem ngưỡng ~30s của `--news` sang.

### Đẩy ra front-end: đợi ~1 phút rồi `?clearcache=1`

Ghi xong CMS chưa hiện ngoài trang live. Cache nằm ở origin, **không tự hết hạn sớm**:
đo thật sau 15 phút vẫn trả bài cũ, `x-cache-status: MISS` (tức không phải cache biên),
và `?nocache=` không có tác dụng.

Tham số đúng là **`?clearcache=1`**, dùng được cho **mọi loại trang**.

**Thứ tự quan trọng: ghi → đợi ~1 phút → clearcache → nghiệm thu.** `clearcache` dựng
lại cache ngay tại thời điểm gọi, nên gọi ngay sau khi ghi là đóng băng đúng bài cũ vào
cache mới — hỏng hơn lúc chưa gọi.

Nó purge thật, không phải bypass — gọi xong thì **URL trơn** cũng trả nội dung mới, nên
nghiệm thu phải làm trên URL trơn chứ không phải URL có tham số.

Đo thật trên `/laptop-hp-compaq`: gọi `?clearcache=1` một lần → URL trơn trả 28/28
heading mới, 17/17 tên file ảnh, 0 heading cũ.

Vẫn ra bài cũ sau khi gọi → gọi lại sau ~1 phút trước đã. Vẫn cũ thì mới nghi ghi nhầm
chỗ; phép loại trừ là grep heading của bản **cũ trong DB** lên trang live: còn khớp =
đúng field nhưng sai chỗ khác, khớp 0 = ghi nhầm field hoặc nhầm trang.

## 7. Ngoài scope — trang ngành hàng

`POST /Category/UpdateCategory`, payload `{arrParam: ArrParams}` là **mảng theo vị trí,
không phải field có tên**, nội dung lấy qua `CKEDITOR.getData()`. CMS đổi thứ tự là ghi
nhầm ô → rủi ro cao, khuyến nghị làm tay.
