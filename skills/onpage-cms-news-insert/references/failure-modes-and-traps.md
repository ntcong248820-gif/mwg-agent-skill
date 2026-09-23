# Các Bẫy Kỹ Thuật và Chẩn Đoán Lỗi trên News CMS

Tổng hợp các trường hợp lỗi thực tế đã được đo lường và chứng minh trong quá trình vận hành SEO trên hệ thống CMS MWG.

---

## 1. Tìm Chuỗi Plain Text trên HTML Thô Luôn Thất Bại

Các bài viết trên News CMS thường chứa các thẻ định dạng lồng nhau và HTML entity:
```html
<p>Chương trình đặt trước <span style="font-weight: bold;">iPhone 18&nbsp;Pro Max</span> chính thức bắt đầu...</p>
```
Nếu lấy cột "Nội dung cũ" (vốn là chuỗi văn bản thuần) và dùng `rawHtml.indexOf(oldText)`, kết quả luôn là `-1`.

**Giải pháp chuẩn:**
- Tách bạch 2 tầng: Dùng `DOMParser` để bóc tách văn bản, decode HTML entities và chuẩn hoá khoảng trắng (`U+00A0` thành space thường) nhằm **định vị chỉ số ký tự** (`insertAt`).
- Thực hiện ghép chuỗi (splice) trên **chuỗi thô (raw string)** để **ghi**, tuyệt đối không serialize lại toàn bộ cây DOM (tránh làm thay đổi định dạng toàn bài).

---

## 2. Ghi Đè Cả Đoạn Khiến Mất Link Cũ và Shortcode

Trong các bài PR, tin khuyến mãi hay ngân hàng, rất nhiều đoạn văn đã chứa sẵn link đối tác hoặc thẻ neo khác:
```html
<p>Xem thêm ưu đãi hoàn tiền từ <a href="https://..." title="Techcombank">ngân hàng đối tác</a> khi thanh toán.</p>
```
Nếu thay thế toàn bộ đoạn văn bằng câu mới, các liên kết hiện hữu này sẽ bị xoá sạch.

**Giải pháp chuẩn:**
- Mặc định sử dụng cơ chế **Append**: chèn câu văn mới vào ngay trước thẻ đóng `</p>`.
- Đoạn văn cũ và mọi liên kết, hình ảnh bên trong được giữ nguyên 100%.

---

## 3. Link Ngắn "Nuốt" Link Dài Khi Bọc Anchor

Ví dụ: Câu chèn có chứa cả 3 cụm từ:
- `iPhone 18` (link về trang Hub)
- `iPhone 18 Pro` (link về trang danh mục Pro)
- `iPhone 18 Pro Max` (link về trang chi tiết Pro Max)

Nếu bọc `iPhone 18` trước, cụm từ `iPhone 18 Pro Max` sẽ bị bọc thành:
`<a href="...">iPhone 18</a> Pro Max` -> Link bị gãy và cụm từ dài bị mất nghĩa.

**Giải pháp chuẩn:**
- Sắp xếp mảng links theo thứ tự **độ dài anchor giảm dần**.
- Thay thế từng anchor bằng một token tạm thời (placeholder duy nhất: `___NEWS_ANCHOR_i___`).
- Sau khi toàn bộ các từ khoá đã được chuyển thành token, tiến hành chuyển đổi token sang thẻ `<a>` hoàn chỉnh với đầy đủ thuộc tính `target="_blank" rel="noopener"`.

---

## 4. Bảo Toàn Trạng Thái Xuất Bản (`statusId`)

Trên News CMS, bài viết có các trạng thái vòng đời: Nháp (Draft), Chờ duyệt (Pending), Đã xuất bản (Published / Active).
Khi gửi `POST` cập nhật nội dung bài viết, form submission bắt buộc phải mang theo `statusId` hiện tại của bài.

**Hậu quả nếu bỏ sót:**
- Bài viết đang live trên trang tin bị chuyển về trạng thái Chưa xuất bản hoặc Mất hiển thị trên frontend.
- Runner tự động serialize toàn bộ thẻ `input/select/textarea` của form hiện tại, đảm bảo không một trường metadata nào bị rơi rớt.

---

## 5. Tránh Xa Trình Soạn Thảo TinyMCE UI

Không bao giờ thực hiện chèn nội dung thông qua API của TinyMCE (`tinymce.activeEditor.setContent(...)`):
- TinyMCE tự động tái định dạng (re-format, clean HTML) toàn bộ bài viết, làm phình dung lượng và lệch hàng trăm ký tự.
- TinyMCE không tự động kích hoạt sự kiện `change` lên textarea bên dưới, dẫn đến nguy cơ form submit lưu dữ liệu rỗng hoặc dữ liệu cũ.
- Chạy headless qua `fetch()` trực tiếp lên endpoint HTTP là phương pháp duy nhất đảm bảo byte-exact.

---

## 6. Phân Biệt Ba Trường Hợp `SKIP`

Khi một dòng bài viết bị bỏ qua (`SKIP`), cần phân loại rõ nguyên nhân:

| Phân loại | Dấu hiệu nhận biết | Bản chất thực tế | Hướng xử lý |
| :--- | :--- | :--- | :--- |
| **Đã chèn trước đó** (`already: true`) | Đoạn văn trong bài bắt đầu bằng đúng `oldText` và có độ dài lớn hơn | Đã hoàn thành ở đợt chạy trước, an toàn bỏ qua | Ghi nhận DONE trên sheet |
| **Đoạn là Heading** (`tag: h1..h6`) | Đoạn tìm thấy khớp 100% text nhưng nằm trong `<h3>` hoặc `<h2>` | Rule cấm đặt link trong thẻ tiêu đề | Báo cáo user để chọn đoạn văn `<p>` khác |
| **Không tìm thấy đoạn** (`match: 0`) | Không có block nào khớp, similarity của các đoạn gần nhất thấp | Nội dung bài viết trên CMS đã bị biên tập lại, hoặc dữ liệu sheet lấy nhầm nguồn | Trả về nhân sự lập sheet để cập nhật lại câu neo |

---

## 7. Độ Trễ Cache Frontend

Sau khi CMS lưu thành công, hệ thống cache CDN và Varnish của `thegioididong.com/tin-tuc/` có thể trễ từ 5 đến 15 phút.
- **Không bao giờ dùng trang live để kết luận script chạy lỗi hay chưa lưu**.
- Luôn tin cậy vào kết quả kiểm tra `verify byte-exact` trực tiếp từ CMS GET request.

---

## Bẫy: mất tick chuyên mục sau khi ghi

**Triệu chứng:** runner báo `DONE` hết, thân bài đúng byte-exact, link chèn đủ —
nhưng bên Tin tức báo bài mất sạch tick chuyên mục cha-con.

**Nguyên nhân:** chuyên mục **không nằm trong form**. Checkbox `name='NewsCate'`
luôn `checked=false` (chỉ là UI chọn); dữ liệu thật ở `<ul class="sticker newscategory">`
do server render. CMS gộp nó thành `LstCategoryId`/`LstCategoryName` khi Save.
`serializeArray()` bỏ qua hết → POST không kèm chuyên mục → CMS xoá sạch.

**Không phải** do DOMParser không chạy JS. Chạy trong Chrome thật cũng mất y hệt.

**Phòng:** bất biến `taxonomyKept` — đọc sticker trước khi ghi, bơm lại 4 field
`Lst*`, chặn POST nếu số lượng lệch, và verify lại sticker sau khi ghi.

**Phát hiện sớm từ ngoài:** quét `BreadcrumbList` trên trang live. Vị trí 3 trả tên
chuyên mục thật; mất sạch thì rơi về `Bài viết tin tức`. Nhớ chờ cache frontend.

**Nếu đã lỡ mất:** backup của runner cũ **không cứu được** vì chỉ lưu thân bài.
Phải dựng lại từ nguồn ngoài — export có cột `listcategoryname`, Wayback, hoặc
suy luận từ bài analogue cùng dạng rồi nhờ bên Tin tức duyệt.

## Bẫy: TinyMCE reformat thân bài

Đừng lấy thân bài từ TinyMCE hay từ `getDataSubmitNews()`. Đo trên một bài tin:
DB 3.978 byte, payload CMS 4.008 byte. Luôn GET tĩnh `#contentNewsAva` để lấy bytes
thật, và assert hash trước khi POST.
