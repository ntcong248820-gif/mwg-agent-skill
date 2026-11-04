# Hợp đồng endpoint — CMS Hỏi Đáp (`/v2/Faq/`)

Đo read-only 24/09/2026, profile Chrome `<faq>`, bài 1576257 / 1440516 / 1382098.
Nguồn: `/v2/Scripts/faq.js` (1.039 dòng), HTML tĩnh `GET /v2/Faq/NewsEdit?newsId=…`, DOM live.
**Không có POST nào được gửi** trong lúc đo. Mục đánh dấu *(suy từ code)* chưa thấy thật.

## 1. Trang sửa

```
GET /v2/Faq/NewsEdit?newsId={ID}          (không cần siteId; hdSiteId = 1)
```

Script: `manage.js?v=46`, `faq.js`, `tinymce.min.js`. Form `#submitEditNews` (không `action`).
Nút "Cập nhật" = `<a onclick="SubmitNewsEdit()">`.

### Field (`GetAllFormData('#submitEditNews')` → 27 key)

| Key | Ý nghĩa | Ví dụ 1576257 |
| --- | --- | --- |
| `txtTitle` | Tiêu đề = **H1** live | TOP 5 laptop cho học sinh cấp 1, cấp 2 tốt |
| `txtUrl` | slug (live = `/hoi-dap/{txtUrl}-{ID}`) | top-laptop-cho-hoc-sinh |
| `thumbnailNews` / `…Width` / `…Height` | thumbnail (`common/Common/…`) | |
| `cboChildCategory` | `<select multiple id=lst_childcate>` 82 option — **chỉ giữ giá trị cuối** | 1673 (#PC - Laptop Windows) |
| `cboParentCategory` | `<select multiple id=lst_parentcate>` 2 option | 1656 (#Máy tính - Laptop - Tablet) |
| `cboArticleType` | Dạng bài (14 option) | Top sản phẩm |
| `hdListProductRelated` | SP liên quan | (rỗng) |
| `content_FaqNews` | textarea thân bài (serializeArray đổi `\n`→`\r\n`) | 9.699 ký tự |
| `txtMetaTitle` | thẻ `<title>` live (+ " - Thegioididong.com") | …tốt nên mua |
| `txtMetaDescription` | meta description | 159 ký tự |
| `hdListKeyword` | keyword, phẩy | |
| `txtSchema` | schema tuỳ biến | (rỗng) |
| `cboStatus` | 4 option; `2` = Xuất bản | 2 |
| `txtDate` / `txtHour` / `txtMinute` | ngày đăng = `datePublished` live (giờ 00:00 khớp thật) | 07/07/2026 0 0 |
| `hdNewsId` `hdSiteId` `hdCurrentUrl` `hdCurrentStatus` `hdCurrentName` | hidden | |
| `hdIsCTV` `hdIsCTVFAQ` `hdIsTTSFAQ` `hdIsSkipSecurity` | quyền; tài khoản đo = 0/0/0/0 | |

Checkbox `cbIsHideBannerVCCorp`, `cbIsHot`, `cbIsHide`: cả 3 bài mẫu đều không tick →
vắng khỏi payload (serializeArray bỏ checkbox không tick). Nếu bài nào có tick, trạng thái
tick nằm ở thuộc tính `checked` tĩnh và form live giữ đúng — runner so `formKhopServer`.

## 2. Ghi bài — `SubmitNewsEdit()` trong `faq.js`

```js
var data = GetAllFormData('#submitEditNews');
data.LstParentCategory = $('#lst_parentcate').val().join(' ');   // nối DẤU CÁCH
data.LstChildCategory  = $('#lst_childcate').val().join(' ');
data.ContentNews = tinymce.get("content_FaqNews").getContent();  // server ghi field này
$.ajax({ url: rootUrl + 'Faq/SubmitNewsEdit' + skipTxt, type: 'POST', data: data,
  success: function (e) {
    if (e.status > 0) { alert(e.error); window.location.href = '/v2/Faq/NewsEdit?newsId=' + e.status; }
    else alert(e.error);
  } });
```

```http
POST /v2/Faq/SubmitNewsEdit[?skip=1 khi #hdIsSkipSecurity == "1"]
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
```

Payload runner = 27 key + `LstParentCategory` + `LstChildCategory` + `ContentNews` = 30 key,
`jQuery.param(data)`.

Response *(suy từ code)*: `{ status, error }`; `status > 0` = thành công, giá trị là newsId
(trang điều hướng tới bài đó); `≤ 0` = lỗi, `error` là thông báo.

Client guard (không phải ràng buộc server): CTV/TTS không được chuyển Xuất bản → Nháp, không
được Xuất bản. Không có validate độ dài phía client như News.

## 3. Upload ảnh thân bài — `UploadManyImages(files)` trong `faq.js`

```js
formData.append("ID", $("#hdNewsId").val());
formData.append("type", 3);
files.forEach((f,i) => formData.append('file' + i, f));
$.ajax({ url: rootUrl + 'Common/UploadManyImages', type: 'POST', data: formData,
         processData: false, contentType: false,
         success: function (dataRs) { $("#imagesFolderUpload .previewsImages").prepend(dataRs); } });
```

Cùng endpoint với bài tin News, **không gửi `site`**. Response thành công = HTML fragment
(preview), lỗi = JSON `{status:-1,error}` (hành vi đo ở News 18/09). Ảnh bài hiện có nằm ở
`https://cdnv2.tgdd.vn/mwg-static/common/News/{newsId}/{file}` → thư mục riêng từng bài.
Giới hạn client 10MB/file (`#allImagesNews` change handler).

Trang có **2 `input#allImagesNews`** (name `allImagesNews`, ngoài form); chỉ cái đầu có
change handler (→ upload ngay). `#fileUploadContentNews` (trong form, không name) có handler
html5Uploader. Runner dùng input tự tạo, không name, không handler.

## 4. Upload thumbnail (tham khảo, runner không dùng)

`#thumbnailNews` html5Uploader → `POST /v2/Common/PostImage?type=56&productId={ID}&categoryId=-1&siteId=-1&dentination=&isSetHeight=True&isValidateImg=True`
→ JSON `{status, error, imageUrl, width, height}`; ghi vào `thumbnailNews*`.

## 5. TinyMCE

Editor duy nhất `content_FaqNews`. Nút ảnh (`imageupload`) mở `OpenUploadManyImages()` — chèn
`<p><img … class='lazy' onclick='OpenUploadManyImages()'/></p>`. Handler `change` →
`tinyMCE.triggerSave()` (ghi bản reformat vào textarea). Đo 1576257: textarea 9.699 ·
`getContent()` 11.814.

## 6. Trang live

`https://www.thegioididong.com/hoi-dap/{txtUrl}-{newsId}`. `<h1>` = `txtTitle`,
`<title>` = `txtMetaTitle` + " - Thegioididong.com", `datePublished` = txtDate 00:00,
`dateModified` = lần lưu cuối. Live encode ký tự Latin-1 thành named entity (`&ecirc;`).
Không thấy header `x-cache-status` trên `/hoi-dap/`. `?clearcache=1` áp dụng mọi loại trang
(owner, 19/09) — đợi ~1 phút sau khi ghi.

## 7. Bẫy đã kiểm so với bài tin News

| Bẫy News | Faq |
| --- | --- |
| Checkbox `NewsCate` luôn unchecked, chuyên mục ở sticker | **Không có**. Chuyên mục là option `selected` tĩnh, đọc được |
| Thiếu `LstCategoryId` = mất chuyên mục | **Tương tự**: `LstParentCategory`/`LstChildCategory` do JS tổng hợp, `GetAllFormData` chỉ giữ giá trị cuối multi-select |
| `ContentNews` vs textarea | **Giống**: server đọc `ContentNews` |
| `&amp;` → `&` sau lưu | Chưa kiểm (cần ghi thật) |
| 2 input file trùng id, 1 cái có 2 handler | Tương tự: 2 `#allImagesNews`, cái đầu có handler |

## 8. Tạo bài mới — `NewsEdit?newsId=0` (đo read-only 24/09/2026, CHƯA POST thật)

Nguồn: DOM trang `newsId=0` + `faq.js` (39.350 byte) + `manage.js?v=46`. Không bấm submit, không gọi Submit/Upload/PostImage.

| Điểm | Giá trị đo |
| --- | --- |
| `hdNewsId` / `hdSiteId` | `0` / `1` |
| `GetAllFormData` | 25 key (multi-select rỗng + 3 checkbox không tick vắng mặt) → runner thêm `cboChildCategory`, `cboParentCategory`, `LstParentCategory`, `LstChildCategory`, `ContentNews` = 30 key như bài có sẵn |
| Nhãn `(*)` | Tiêu đề, URL, Tiêu đề SEO, Meta Description, Keyword - Tags |
| maxlength | `txtTitle` 70 (bài cũ có tiêu đề dài hơn → giới hạn chỉ ở client), `txtMetaTitle` 70, `txtMetaDescription` 170; URL đếm "/ 100" |
| `cboStatus` | `1` Nháp · `2` Xuất bản · `3` Chờ duyệt (**mặc định**) · `4` Đã duyệt. `hdCurrentStatus=3` |
| Dạng bài `cboArticleType` | 13 option + rỗng (`Top sản phẩm`, `Tư vấn chọn mua`, `Hướng dẫn sử dụng - mẹo - thủ thuật`, …) |
| Chuyên mục con `#lst_childcate` | 82 option (+`-1`); `onchange="loadParentCate()"` |
| Chuyên mục cha `#lst_parentcate` | **rỗng** cho tới khi chọn con: `POST /v2/Faq/LoadHtmlParentCate` `lstChildCate=<id,id>&listParentThreadID=` → HTML `<option>`. Đo 1673 → `<option value="-1">…</option><option value="1656">#Máy tính - Laptop - Tablet (1656)</option>` (endpoint đọc; gọi 1 lần lúc research) |
| Keyword | `hdListKeyword` = các từ nối `,`; UI giới hạn 5 (`AddToListKeyword`) |
| URL tự sinh | `getUrlFromName` onblur tiêu đề: bỏ dấu, ký tự lạ → `-`, cắt 50 ký tự tại dấu `-`, chỉ khi `hdCurrentUrl` rỗng. CLI không dùng — nhận url khai rõ |
| Validate client | **Không có** ngoài quyền CTV/TTS (`hdIsCTVFAQ`/`hdIsTTSFAQ`=0 ở tài khoản đo). Server là cổng duy nhất → runner tự chặn |
| Thumbnail | `#thumbnailNews` html5Uploader → `POST /v2/Common/PostImage?type=56&productId=0&categoryId=-1&siteId=-1&dentination=&isSetHeight=True&isValidateImg=True`, FormData `uploadedFile` → JSON `{status, error, imageUrl, width, height}` → ghi `thumbnailNews` / `…Width` / `…Height`. Không đánh dấu bắt buộc. Bài cũ lưu width/height `0` |
| Submit | `SubmitNewsEdit()` như mục 2; thành công `e.status > 0` → `alert` + điều hướng `/v2/Faq/NewsEdit?newsId=' + e.status` ⇒ với bài mới `status` là newsId mới *(suy từ code)* |
| Ảnh thân bài | `UploadManyImages` gửi `ID=$('#hdNewsId')` → ở trang tạo mới là `0` → rơi vào `common/News/0/`. **Phải tạo bài trước**, upload sau trên `NewsEdit?newsId=<id>` |
