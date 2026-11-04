# TGDĐ HTML Formatter Reference

Chuẩn hóa và tạo mã HTML tĩnh tối ưu SEO, chuẩn Mobile-First cho các thành phần bài viết Thế Giới Di Động (TGDĐ): bảng giá sản phẩm, bảng so sánh thông số kỹ thuật và khung thông tin điểm nổi bật/kênh liên hệ theo chuẩn CMS TinyMCE.

## Thế Giới Di Động (TGDĐ) HTML Components & Format Standard (CMS TinyMCE & Mobile-First)

Reference này định nghĩa toàn diện các quy chuẩn kỹ thuật, cấu trúc mã HTML tĩnh chuẩn SEO, cơ chế tự tương thích với trình soạn thảo CMS TinyMCE và hiển thị hoàn hảo trên giao diện Mobile (iOS Safari / Android Chrome).

---

## 1. BỘ NGUYÊN TẮC VÀNG CHO CMS TINYMCE & MOBILE-FIRST

### 📱 Tối ưu giao diện Mobile (Mobile-First):
1. **Chống tràn màn hình (Viewport Containment)**: Mọi bảng bắt buộc được bọc trong 1 thẻ `<div style="width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; box-sizing: border-box;">`.
2. **Khóa tỷ lệ & Giữ dáng bảng**: Bảng đặt `min-width: 620px; max-width: 100%; width: 100%; table-layout: fixed;` giúp nội dung trên mobile thoáng đãng, người dùng lướt ngón tay cuộn ngang mượt mà, không bị ép nát chữ.
3. **Chống lỗi Font-Boosting trên iOS**: Khai báo rõ `font-size: 14px; line-height: 1.5; color: #333333;` trực tiếp trên bảng để iOS Safari không tự phóng to chữ làm lệch cấu trúc.
4. **Quy chuẩn Danh sách & Bullet (QUAN TRỌNG - Tránh lỗi dấu tròn rỗng `◦`)**:
   - **Tuyệt đối KHÔNG gán inline style `padding-left` hoặc `margin` vào thẻ `<ul>`** (như `style="padding-left: 18px;"`). TinyMCE sẽ nhận diện nhầm đây là danh sách cấp 2 (nested list) và tự động đổi dấu chấm tròn đen `•` sang hình tròn rỗng `◦` kèm theo khoảng thụt lề sâu 30-40px gây lỗi giao diện.
   - Luôn sử dụng thẻ danh sách nguyên bản: `<ul>` và `<li>` sạch (không gắn inline style list), hoặc sử dụng định dạng đoạn văn gạch đầu dòng `<p>- <strong>...</strong> ...</p>` khi cần căn lề trái phẳng 100%.
5. **Chống gãy số điện thoại Hotline**: Số Hotline và giá tiền luôn có `white-space: nowrap;` để không bị ngắt đôi số trên mobile.

### ⚙️ Tương thích tuyệt đối với CMS TinyMCE:
1. **Kháng cơ chế Tự Động Sửa Lỗi của TinyMCE**:
   - Sử dụng các thẻ HTML cơ bản và sạch (`div`, `table`, `tr`, `th`, `td`, `a`, `ul`, `li`, `p`, `strong`).
   - Mọi thuộc tính kích thước, viền, khoảng cách đều dùng **style inline** trên thẻ bọc ngoài. Không dùng class/id hay thẻ `<style>` ngoài (tránh bị TinyMCE thanh lọc khi lưu bài).
2. **Không cố định chiều cao & Không ngắt dòng thừa**:
   - Tuyệt đối không khai báo `height` hoặc `line-height` quá cứng trên ô/dòng để TinyMCE không tự chèn các giá trị pixel thừa khi người dùng kéo thả.
   - Giữ mã HTML liền mạch giữa các thẻ đóng và mở (tránh chèn nhiều dòng trống `\n\n` khiến TinyMCE tự tạo thẻ `<p>&nbsp;</p>` gây giãn khoảng cách quá rộng).
3. **Tránh đè/tràn văn bản trong Editor**: Áp dụng `overflow-wrap: anywhere; word-break: break-word; white-space: normal;` cho tất cả các cột chứa câu văn bản để TinyMCE render đúng trong cả chế độ Visual (Trực quan) và Source (Mã nguồn).
4. **Viền bảng khi dán qua PIM (chốt 09/10/2026, đã kiểm tra thực tế)**:
   - Skill vẫn xuất `border: 1px solid #cccccc;` đầy đủ trên mọi `th`/`td`, không tách `border-style`/`border-color` thiếu độ dày.
   - PIM (CKEditor) khi lưu sẽ bọc bảng trong `<figure class="table">` và **cắt `border` về chỉ còn `border-color:#cccccc`** (mất độ dày + kiểu viền), kể cả ô đã ghi đúng shorthand. Không phải lỗi skill.
   - Hiện viền hay không phụ thuộc CSS từng template: trang bài tin/category (`#article__content__cate td { border-width: 1px }`) vẫn có viền. Trang sản phẩm `/dtdd/...` (`#description-text-detail`) không có rule này nên viền = 0px, bảng mất viền (lỗi thật ở bài iPhone 18 Pro Max 256GB).
   - Bài mô tả trên trang sản phẩm: sau khi lưu PIM phải mở trang live kiểm tra viền bảng. Nếu mất viền, sửa HTML không giải quyết được vì PIM sẽ lọc lại, cần báo team web thêm rule viền cho `#description-text-detail td, th`.
   - **Cách xử lý đã test live OK (12/10/2026, bài iPhone 18 Pro Max)**: dùng viền nền (bg-grid) thay border. `<table>` style: `background-color:#cccccc;border-collapse:separate;border-spacing:1px;` (thay `border-collapse:collapse`). Mỗi `<td>`/`<th>` chưa có nền thì thêm `background-color:#ffffff;` đầu style (ô header nền #000000 giữ nguyên). PIM giữ được background nên viền 1px xám hiện đúng.
   - Heading bài đi PIM: H2/H3 không bọc `<strong>`, H4 vẫn bọc `<strong>` (CSS trang để H4 weight 400). Chỉ áp dụng bài ĐÃ qua PIM.

---

## 2. FORMAT 1: BẢNG GIÁ SẢN PHẨM (3 CỘT)
> **Mục đích**: Niêm yết danh sách sản phẩm/SKU gồm: Tên sản phẩm (Cột 1) - Giá gốc (Cột 2) - Giá ưu đãi tại TGDĐ (Cột 3).

### Quy cách thiết kế:
- **Tỷ lệ cột**: Tên sản phẩm: `46%` | Giá gốc: `27%` | Giá ưu đãi: `27%`.
- **Dòng tiêu đề (`<th>`)**: Nền đen `#000000`, chữ vàng TGDĐ `#FFE14C`, căn giữa (`text-align: center;`), `font-weight: bold;`.
- **Cột Tên sản phẩm (`<td>` 1)**: Căn lề trái (`text-align: left;`), tự xuống dòng khi tên dài: `white-space: normal; overflow-wrap: anywhere; word-break: break-word;`. Thẻ `<a>` mở tab mới `target="_blank" rel="noopener noreferrer"`.
- **Cột Giá (`<td>` 2 & 3)**: Căn giữa (`text-align: center;`), giữ trên 1 dòng duy nhất: `white-space: nowrap;`.

### Khung HTML mẫu Bảng Giá:
```html
<div style="width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; box-sizing: border-box;">
<table style="width: 100%; min-width: 620px; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5; color: #333333;">
<tr>
<th style="width: 46%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">Tên sản phẩm</th>
<th style="width: 27%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: nowrap;">Giá gốc</th>
<th style="width: 27%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: nowrap;">Giá ưu đãi tại TGDĐ</th>
</tr>
<tr>
<td style="width: 46%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;"><a href="[URL_SẢN_PHẨM]" target="_blank" rel="noopener noreferrer">[TÊN_SẢN_PHẨM]</a></td>
<td style="width: 27%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; white-space: nowrap;">[GIÁ_GỐC]</td>
<td style="width: 27%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; white-space: nowrap;">[GIÁ_ƯU_ĐÃI]</td>
</tr>
</table>
</div>
```

---

## 3. FORMAT 2: BẢNG SO SÁNH THÔNG SỐ KỸ THUẬT (SPEC TABLE)
> **Mục đích**: Bảng đối chiếu cấu hình giữa các dòng máy/phiên bản với nhiều đoạn văn bản kỹ thuật dài (Chip, RAM, Màn hình, Pin...).

### Quy cách thiết kế:
- **Tỷ lệ cột**: Tiêu chí: `24%` | Model 1: `38%` | Model 2: `38%`.
- **Dòng tiêu đề (`<th>`)**: Nền đen `#000000`, chữ vàng TGDĐ `#FFE14C`, căn giữa (`text-align: center;`), `font-weight: bold;`.
- **Tất cả các ô dữ liệu (`<td>`)**: 
  - Đều sử dụng: `white-space: normal; overflow-wrap: anywhere; word-break: break-word;` để nội dung dài tự động xuống dòng linh hoạt. **Tuyệt đối không dùng `white-space: nowrap;`** trên các cột chứa thông số.
  - Căn lề trái (`text-align: left;`) để câu chữ thẳng hàng, dễ so sánh trực quan.

### Khung HTML mẫu Bảng So Sánh:
```html
<div style="width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; box-sizing: border-box;">
<table style="width: 100%; min-width: 620px; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5; color: #333333;">
<tr>
<th style="width: 24%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">Tiêu chí</th>
<th style="width: 38%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">[TÊN_MODEL_1]</th>
<th style="width: 38%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #FFE14C; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">[TÊN_MODEL_2]</th>
</tr>
<tr>
<td style="width: 24%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">[TÊN_TIÊU_CHÍ]</td>
<td style="width: 38%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">[THÔNG_SỐ_MODEL_1]</td>
<td style="width: 38%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">[THÔNG_SỐ_MODEL_2]</td>
</tr>
</table>
</div>
```

---

## 4. FORMAT 3: BOX THÔNG TIN ĐIỂM NỔI BẬT & KÊNH ĐẶT HÀNG (CALLOUT BOX)
> **Mục đích**: Khung ghi chú nhận diện TGDĐ (viền vàng, nền vàng nhạt) tóm tắt điểm nổi bật, lý do mua hàng và các kênh liên hệ đặt hàng/hotline.

### Quy cách thiết kế:
- **Cấu trúc thẻ `<div>` Semantic**: Dùng 1 thẻ `<div>` bọc ngoài duy nhất có `box-sizing: border-box; border-radius: 4px;` giúp tương thích hoàn hảo trên CMS TinyMCE, không bị lỗi lồng thẻ phức tạp của `<table> 1x1`, đồng thời giúp Googlebot trích xuất danh sách `<ul>`, `<li>` lên **Google Featured Snippets (Top 0)**.
- **Màu sắc & Điểm nhấn**:
  - Nền vàng nhạt: `background-color: #fff9e6;`
  - Viền khung: `border: 1px solid #f2c94c;`
  - Viền nhấn trái 5px (Left Accent): `border-left: 5px solid #f5b700;`
  - Gạch phân cách tiêu đề box: `border-bottom: 1.5px solid #ebd27b;`
- **Tối ưu Danh sách & Bullet (Khắc phục hoàn toàn lỗi vòng tròn rỗng `◦`)**:
  - `padding: 14px 16px;` cho toàn bộ thẻ box ngoài.
  - Sử dụng thẻ `<ul>` và `<li>` sạch **nguyên bản (không gắn inline style margin/padding lên `<ul>`)** để TinyMCE hiển thị đúng dấu chấm tròn đen `•` chuẩn mực.
  - Hotline: Link màu đỏ `#d9381e`, in đậm `font-weight: bold;`, dùng `white-space: nowrap;` và giao thức `href="tel:[SỐ_ĐIỆN_THOẠI]"` để bấm gọi trực tiếp trên điện thoại.

### Khung HTML mẫu Box Thông Tin & Kênh Liên Hệ:
```html
<!-- BOX THÔNG TIN / ĐIỂM NỔI BẬT -->
<div style="width: 100%; max-width: 100%; box-sizing: border-box; background-color: #fff9e6; border: 1px solid #f2c94c; border-left: 5px solid #f5b700; padding: 14px 16px; margin: 16px 0; border-radius: 4px; font-size: 14px; line-height: 1.6; color: #333333;">
<p style="margin: 0 0 10px 0; padding-bottom: 6px; border-bottom: 1.5px solid #ebd27b; font-size: 16px; font-weight: bold; color: #111111; line-height: 1.4;">[TIÊU_ĐỀ_BOX]</p>
<ul>
<li><strong>[TỪ_KHÓA_ĐẬM]</strong>: [Nội dung chi tiết 1]</li>
<li><strong>[TỪ_KHÓA_ĐẬM]</strong>: [Nội dung chi tiết 2]</li>
<li>[Nội dung chi tiết 3]</li>
<li><a style="color: #0066cc; text-decoration: none; font-weight: bold;" title="[TIÊU_ĐỀ_LINK]" href="[URL_LIÊN_KẾT]" target="_blank" rel="noopener noreferrer">[ANCHOR_TEXT]</a> [Nội dung kèm link]</li>
</ul>
</div>

<!-- KHU VỰC KÊNH LIÊN HỆ / MUA HÀNG -->
<p style="margin: 16px 0 8px 0; font-weight: bold; color: #222222; font-size: 15px; line-height: 1.5;">[TIÊU_ĐỀ_KÊNH_MUA_HÀNG_HOẶC_HỖ_TRỢ]</p>
<ul>
<li>[TÊN_KÊNH_ONLINE]: <a style="color: #0066cc; font-weight: 600;" title="[TIÊU_ĐỀ_LINK]" href="[URL_TRANG_CHỦ_HOẶC_SẢN_PHẨM]" target="_blank" rel="noopener noreferrer">[TÊN_MIỀN_HOẶC_ĐƯỜNG_DẪN]</a></li>
<li>[TÊN_HOTLINE]: <a style="color: #d9381e; font-weight: bold; text-decoration: none; white-space: nowrap;" href="tel:[SỐ_ĐIỆN_THOẠI_LIỀN]">[SỐ_ĐIỆN_THOẠI_CÓ_KHOẢNG_TRẮNG]</a> ([KHUNG_GIỜ_HOẠT_ĐỘNG])</li>
</ul>
```
