# Hợp đồng Endpoint CMS News

Áp dụng cho CMS Thế Giới Di Động (`cms.thegioididong.com`). Hệ thống quản lý bài viết tin tức dùng chung một phiên đăng nhập (session) cho cả 3 trang tin thuộc tập đoàn.

---

## 1. Bản đồ Site ID (`siteId`)

| `siteId` | Hệ thống trang tin | Domain frontend | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **`1`** | **Tin tức Thế Giới Di Động** | `thegioididong.com/tin-tuc` | Tin công nghệ, NPI launching, khuyến mại, tài chính ngân hàng |
| **`2`** | **Kinh nghiệm hay Điện Máy Xanh** | `dienmayxanh.com/kinh-nghiem-hay` | Hướng dẫn sử dụng, mẹo vặt gia dụng, đồ bếp, điện lạnh |
| **`16`** | **Tekzone TopZone** | `topzone.vn/tekzone` | Chuyên trang hệ sinh thái Apple, thủ thuật iOS/macOS |

---

## 2. Thao tác Đọc (Read)

```http
GET /v2/News/NewsEdit?newsId={newsId}&siteId={siteId}
```

- **Mục tiêu**: Lấy mã nguồn HTML nguyên bản của bài viết tại thời điểm hiện tại.
- **Vị trí nội dung**: Nằm trong thẻ `<textarea id="txtContent" name="txtContent">` (hoặc `#Content`).
- **Cách lấy an toàn**: Dùng `textarea.value` trên document đã được parse qua `DOMParser`.
- **Nguyên tắc bất biến**:
  * **KHÔNG** sử dụng `body.innerHTML` của tài liệu để dựng lại toàn bài. Việc này sẽ biến đổi các ký tự khoảng trắng không ngắt `U+00A0` thành `&nbsp;`, làm lệch hàng chục dòng HTML không liên quan.
  * Nếu không tìm thấy textarea: kiểm tra lại session đăng nhập (hết hạn cookie phiên) hoặc `newsId` không tồn tại.

---

## 3. Thao tác Ghi (Submit / Update)

```http
POST /v2/News/NewsEdit
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
X-Requested-With: XMLHttpRequest
```

*(Lưu ý: Submit endpoint được xác định tự động từ thuộc tính `action` của thẻ `<form>`, mặc định là `/v2/News/NewsEdit` hoặc submit controller tương ứng).*

### Payload Form

Dữ liệu gửi lên là kết quả serialize toàn bộ các trường của form bài tin (tương đương `jQuery(form).serializeArray()`), với trường nội dung được ghi đè:

| Trường Form | Giá trị xử lý | Ý nghĩa |
| :--- | :--- | :--- |
| **`txtContent`** | HTML mới đã splice và qua 6 bất biến | Thay thế toàn bộ phần thân bài viết |
| **`newsId`** | Giữ nguyên từ bài gốc | Định danh bài tin tức |
| **`siteId`** | Giữ nguyên từ bài gốc | Phân hệ site (1, 2, 16) |
| **`statusId` / `Status`** | **BẮT BUỘC giữ nguyên** | Bảo toàn trạng thái đã xuất bản (Published). Tuyệt đối không để rỗng hoặc reset về Draft/Chờ duyệt |
| `__RequestVerificationToken` | Giữ nguyên từ form | Token chống giả mạo CSRF |
| **`LstCategoryId` / `LstCategoryName`** | **BẮT BUỘC dựng lại từ sticker** | Chuyên mục cha-con. Xem mục 3.1 — thiếu là CMS bỏ tick sạch |
| **`LstPostFormatId` / `LstPostFormatName`** | **BẮT BUỘC dựng lại từ sticker** | Hình thức bài, cùng cơ chế |
| Các trường khác (Title, Lead...) | Giữ nguyên từ form | Bảo toàn SEO meta |

### 3.1 Bẫy chết người: chuyên mục KHÔNG nằm trong form

`serializeArray()` **không bao giờ** lấy được chuyên mục. Lý do:

- Checkbox `input[name='NewsCate']` (khoảng 146 ô) **luôn `checked=false`**, kể cả
  trên trang thật đã chạy đủ JS. Nó chỉ là UI để chọn.
- HTML tĩnh cũng **không ô nào** mang thuộc tính `checked`.
- Chuyên mục đang gán nằm ở **`<ul class="sticker newscategory">`**, server render
  sẵn dạng `<li data-id="31" id="liCate_31">#Khuyến mãi</li>`.
- Khi bấm Save, `getDataSubmitNews()` của CMS gộp sticker đó thành `LstCategoryId`
  (vd `"31,1169"`) và `LstCategoryName` (vd `"#Khuyến mãi,Mới Nhất"`).

Submit mà thiếu `LstCategoryId` = CMS hiểu "không còn chuyên mục nào" = **xoá sạch**.
Đây là nguyên nhân một sự cố thực tế (32/33 bài mất chuyên mục trong một lô chạy).

Runner đọc sticker bằng `readStickers(doc)` — chạy được trên DOMParser vì sticker là
HTML tĩnh — rồi bơm lại 4 field `Lst*` trước khi POST.

### 3.2 Bẫy thứ hai: TinyMCE reformat thân bài

**Đừng bao giờ** lấy thân bài từ `getDataSubmitNews()` hay từ TinyMCE. Đo thật trên
một bài tin: DB có **3.978 byte**, payload mặc định của CMS có **4.008 byte** ở
`contentNewsAva` và **4.753 byte** ở `ContentNews`. Bấm Save bình thường là viết đè
thân bài.

Nếu buộc phải đi qua payload của CMS (vd chỉ sửa chuyên mục), phải GET tĩnh lấy
`#contentNewsAva` rồi **ghi đè lại** vào payload, và assert hash khớp trước khi POST.

---

## 4. Kiểm soát Xung đột và Chống Clobbering

1. **Người dùng khác sửa tay song song**:
   Trước khi gửi `POST`, runner luôn thực hiện **re-GET sát trước khi lưu** và so sánh với bản ban đầu:
   ```js
   if (fresh.raw !== first.raw) {
     throw new Error("nội dung đổi giữa lúc đọc và lúc ghi — có người đang sửa song song");
   }
   ```
2. **Không có tính năng Revert/Rollback trên CMS**:
   CMS không hỗ trợ diff HTML bài viết trong lịch sử cập nhật. Bắt buộc caller phải lưu bản backup `_before` và `_after` vào một thư mục backup trước khi ghi nhận hoàn tất.

---

## 5. Bước Xác minh Sau Ghi (Verification)

Sau khi `POST` thành công:
1. Runner thực hiện thêm một lượt `GET /v2/News/NewsEdit` độc lập.
2. Kiểm tra `saved.raw === after` (khớp byte-exact từng ký tự).
3. Kiểm tra sự xuất hiện của 100% URL đích trong thuộc tính `href` của bài viết đã lưu.
4. **Đọc lại `ul.sticker.newscategory` và so với bản trước khi ghi.** Lệch một phần tử
   là `FAIL` — dừng cả lô, đừng chạy tiếp.
5. Chỉ khi cả 3 điều kiện thỏa mãn, bài viết mới được gán `DONE`.

Nghiệm thu từ ngoài, không cần đăng nhập CMS: trang live có `BreadcrumbList`, phần tử
vị trí 3 trả **tên chuyên mục thật**; bài mất sạch chuyên mục rơi về nhãn mặc định
`Bài viết tin tức`. Lưu ý frontend có cache, đổi xong phải chờ vài phút mới thấy.
