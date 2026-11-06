---
name: toi-uu-content-sp-outdate
description: >
  Rà soát và tối ưu lại bài infobox sản phẩm (Apple/TGDĐ) đã cũ, còn giữ nội dung
  lỗi thời kiểu "vừa ra mắt", ngày mở bán/đặt trước, giá và ưu đãi cũ, chip đặt tên
  sai (ví dụ "A18 Bionic"), sapo chưa tối ưu AIO, FAQ "có gì mới" không còn hợp lý,
  mục "giá bao nhiêu?" chưa nằm đầu bài, mục TGDĐ viết dạng bullet chung chung,
  chuỗi H3 đặc điểm nổi bật chưa gom lại, hoặc còn dính link ảnh rác `<a href="">`.
  Dùng khi user đưa một bài HTML sản phẩm đã đăng lâu (product không còn mới) và
  muốn cập nhật lại cho đúng thực tế hiện tại mà KHÔNG đổi nội dung khác ngoài phạm
  vi được liệt kê. Giá luôn phải lấy đúng số liệu sống từ link sản phẩm trong bài,
  KHÔNG được bịa hay ước lượng giá.
user-invocable: true
when_to_use: >
  Trigger khi user đưa nguyên bài HTML infobox sản phẩm (thường Apple/TGDĐ) đã cũ và
  yêu cầu: bỏ nội dung lỗi thời (mở bán/pre-order/"vừa ra mắt"), verify giá + ưu đãi
  mới nhất từ link sản phẩm trong bài, viết lại sapo theo kiểu định nghĩa tối ưu AIO,
  đổi FAQ "có gì mới" thành "có nên mua ở thời điểm này", đưa mục "giá bao nhiêu?" lên
  đầu bài, viết lại/thêm mục mua tại TGDĐ, gom chuỗi H3 đặc điểm nổi bật thành 1 khối
  "Đánh giá... chi tiết, có nên mua ở thời điểm hiện tại không?", sửa lỗi factual khi được xác nhận, gỡ
  link ảnh trống `<a href="">`, hoặc lặp lại đúng các bước này cho một bài sản phẩm
  khác cùng dòng.
category: content-ops
keywords: [infobox, apple, tgdd, outdate, sapo, aio, faq, mo-ban, ra-mat, chip, href-rong, seo, gia-ban-nhieu, san-pham-lien-quan, co-nen-mua]
metadata:
  author: content02@thegioididong.com
  version: "2.8.0"
---

# Tối Ưu Content Sản Phẩm Đã Cũ (toi-uu-content-sp-outdate)

Đóng gói lại toàn bộ quy trình đã dùng để tối ưu bài infobox iPhone 16e / iPhone 16e 512GB — cho phép lặp lại y hệt cho các bài sản phẩm khác đã đăng lâu, không còn "mới ra mắt".

## Khi Nào Dùng

User đưa nguyên bài HTML infobox sản phẩm (thường Apple, có thể mở rộng sang sản phẩm khác trên TGDĐ) đã đăng được một thời gian, cần rà lại các phần đã lỗi thời hoặc chưa tối ưu, nhưng **tuyệt đối không đổi nội dung ngoài phạm vi liệt kê dưới đây** nếu user không yêu cầu thêm.

## Nguyên Tắc Bất Biến

- Chỉ sửa đúng phần được liệt kê trong skill này hoặc phần user chỉ định thêm trong lượt hội thoại. Không tự ý viết lại, rút gọn hay thêm ý ở các đoạn khác.
- Nếu phát hiện lỗi factual (sai tên chip, sai thông số, sai ngày...) mà user **chưa** yêu cầu sửa, chỉ nêu ra để user xác nhận, không tự sửa. Chỉ sửa sau khi user xác nhận (ví dụ user trả lời "sửa đi", "ừa đúng rồi sửa luôn").
- Giữ nguyên toàn bộ heading hierarchy, bảng so sánh, box liên quan, kết bài, trừ phần đang xử lý.
- **Giá luôn phải lấy đúng số liệu sống từ link sản phẩm trong bài (bước 3) — tuyệt đối không bịa, không ước lượng, không suy đoán giá dựa trên trí nhớ hay giá của bản dung lượng/màu khác.** Nếu không truy cập được link để lấy giá sống, báo cho user biết, không tự điền số liệu thay thế.
- **Không được xóa bất kỳ link nội bộ nào đang có sẵn trong bài** (link trong box "Sản phẩm liên quan", bảng so sánh, kết bài, sapo...) vì các link này đang phục vụ SEO. Khi di chuyển hoặc viết lại một đoạn có chứa link, phải giữ nguyên href + anchor text gốc, chỉ được thêm link mới nếu user yêu cầu riêng.
- Áp dụng chung với chuẩn viết/format ở skill `viet-infobox-apple` (văn phong, HTML compact cho CMS TinyMCE, bold `<strong>` vừa đủ, không dùng gạch ngang dài). H2 không bold; H3/H4/H5/H6 bắt buộc bọc `<strong>` toàn bộ tiêu đề.
- **Luôn chạy checklist `tranh-van-phong-ai` trên TOÀN BỘ bài, kể cả các đoạn giữ nguyên/không nằm trong phạm vi bước đang xử lý** — không chỉ áp dụng cho phần mới viết. Dấu hiệu cơ học dễ quét (em-dash `—`/`–`, cụm sáo rỗng lặp lại như "lựa chọn lý tưởng/hoàn hảo") thì chủ động sửa luôn không cần hỏi lại; các sửa đổi văn phong này liệt kê ngắn gọn vào "Các điểm đã fix". Nếu phát hiện văn phong AI ở đoạn không định đụng tới nhưng việc sửa sẽ làm thay đổi ý/cấu trúc câu đáng kể, nêu ra ở "Thông tin cần confirm" thay vì tự sửa.
- **Sản phẩm không phải điện thoại (phụ kiện, tai nghe, sạc, cáp...) thường không khớp hết các bước của skill này** (không có mở bán/pre-order, không có FAQ, không có tên chip, không có bảng giá dạng bảng, có thể không có ảnh). Các bước không áp dụng được thì bỏ qua, không cố ép khuôn — chỉ note rõ trong "Thông tin cần confirm" là bước nào N/A và vì sao, không im lặng bỏ qua.
- **Khi thêm nội dung mới (không phải chỉnh câu chữ/format nội dung sẵn có) — ví dụ thông số, tính năng, ngày ra mắt, chi tiết kỹ thuật chưa có trong bài — phải lấy thông tin từ Apple (trang chính hãng/newsroom) hoặc nguồn công nghệ nước ngoài uy tín (The Verge, MacRumors, 9to5Mac, Engadget...), không tự suy đoán hay lấy từ trí nhớ không kiểm chứng.** Nêu rõ nguồn đã tham khảo trong "Thông tin cần confirm" để user tự đối chiếu. Riêng số liệu giá/ưu đãi vẫn theo nguyên tắc lấy từ link sản phẩm TGDĐ trong bài (không phải từ Apple/nguồn ngoài).
- Khi viết/sửa lại một đoạn có chứa link cũ, nếu câu văn quanh link đó chứa thông tin sai (ví dụ tuyên bố tương thích/tính năng không đúng với sản phẩm được link tới) → sửa lại câu cho đúng thực tế nhưng **vẫn giữ nguyên link gốc**, không xóa link chỉ vì câu văn quanh nó bị sai.

## Các Bước Xử Lý

### 1. Bỏ nội dung lỗi thời về ngày mở bán/đặt trước

Khi sản phẩm đã ra mắt lâu (không còn trong giai đoạn mở bán/pre-order), heading dạng `Apple [Sản phẩm] bao giờ mở bán?` hoặc biến thể tương tự cần đổi thành `[Sản phẩm] ra mắt khi nào?`, và nội dung bên dưới rút gọn chỉ còn ngày ra mắt chính thức, bỏ hẳn mốc đặt trước và mốc mở bán chính thức (không còn giá trị tham khảo với sản phẩm đã cũ).

Mẫu:
```html
<h3 style="text-align: justify;">[Sản phẩm] ra mắt khi nào?</h3><p style="text-align: justify;">[Sản phẩm] được Apple ra mắt vào ngày [ngày ra mắt].</p>
```

### 2. Đổi FAQ "có gì mới" thành "có nên mua ở thời điểm này"

FAQ dạng `Điện thoại [Sản phẩm] có gì mới?` không còn phù hợp với sản phẩm đã cũ (không có gì "mới" để nói). Đổi thành format `Có nên mua [Sản phẩm] ở thời điểm này?`, viết theo đúng chuẩn đã có ở `viet-infobox-apple` (mục "H3 Có Nên Mua Ở Thời Điểm Này"):

- Trả lời thẳng "Có," hoặc "Không," + lý do chính, không vòng vo.
- Nêu nhanh các trang bị/tính năng còn đáng chú ý, bold từng tên bằng `<strong>`.
- Câu cuối tổng kết giá trị còn lại của máy so với phân khúc giá, không cần CTA chuyển tiếp sang heading khác nếu đây đang nằm trong khối FAQ (khác với H3 đứng riêng ngoài FAQ).

Mẫu:
```html
<h4 style="text-align: justify;"><strong>Có nên mua [Sản phẩm] ở thời điểm này?</strong></h4><p style="text-align: justify;">Có, <strong>[Sản phẩm]</strong> vẫn đáng mua nếu bạn cần một chiếc [loại sản phẩm] chính hãng, [đặc điểm 1], tích hợp <strong>[công nghệ]</strong> và có mức giá dễ tiếp cận hơn các dòng cao cấp. Máy vẫn giữ nhiều điểm mạnh như chip <strong>[chip]</strong>, camera <strong>[camera]</strong> và [đặc điểm khác], đủ đáp ứng tốt nhu cầu học tập, làm việc, chụp ảnh, quay video và giải trí hằng ngày.</p>
```

### 3. Verify giá và ưu đãi mới nhất

Vào đúng link sản phẩm được chèn trong bài (thường ở sapo hoặc box liên quan) để lấy giá và danh sách ưu đãi hiện tại. Nếu giá/ưu đãi trong bài đã khớp với dữ liệu mới nhất, giữ nguyên, không sửa thừa. Nếu lệch, cập nhật đúng số liệu mới.

- Đổi tên cột/tiêu đề bảng giá từ "Giá bán tại Thế Giới Di Động" thành **"Giá bán tham khảo"**.
- Xóa hẳn cột "Giá bán quốc tế" (USD/số liệu quốc tế) khỏi bảng giá nếu có — không cần đối chiếu hay cập nhật cột này.
- **Với từng SKU/dòng trong bảng giá: chỉ cập nhật giá khi lấy được giá sống từ đúng link sản phẩm đó.** Nếu dòng đó **không có link để check** (không tìm được URL sản phẩm tương ứng để verify), hoặc có link nhưng sản phẩm đang **hết hàng/ngừng kinh doanh** → giữ nguyên giá cũ đã có sẵn trong bài, không xóa dòng, không tự đoán/ước lượng giá mới cho SKU đó. Không nhắc đến tình trạng hết hàng/ngừng kinh doanh trong nội dung bài (không viết "hết hàng", "ngừng kinh doanh", "sắp về hàng"...) — chỉ âm thầm giữ nguyên số liệu cũ.
- Không viết vào bài các câu kiểu "giá đã đối chiếu trên website", "giá cập nhật theo website chính thức"... trong đoạn văn mô tả — chỉ cần đưa đúng số liệu, không cần nêu nguồn/quá trình verify trong câu văn.
- **Bắt buộc thêm 1 dòng lưu ý ngay sau bảng giá** (đặt trong `<i>` hoặc `<em>`, ngay dưới bảng, trước khi sang nội dung khác), theo đúng mẫu:
  ```html
  <p style="text-align: justify;"><i>Lưu ý: Giá bán được cập nhật ngày [ngày xử lý bài, định dạng dd/mm/yyyy], có thể thay đổi theo thời gian, tuỳ thuộc vào CTKM.</i></p>
  ```
  Ngày điền vào là **ngày thực hiện việc tối ưu bài** (ngày hôm nay khi xử lý), không phải ngày ra mắt sản phẩm. Nếu bài gốc đã có sẵn dòng lưu ý dạng cũ (ví dụ ghi ngày cũ, hoặc câu chữ khác) → thay bằng đúng mẫu này với ngày mới, không giữ ngày cũ.

### 4. Viết lại sapo theo kiểu định nghĩa tối ưu AIO

Sapo/mở bài không dùng heading `<h2>`/`<h3>`, xuất `<p>` thường (đúng theo yêu cầu format hiện tại, khác với chuẩn H2 sapo cũ của `viet-infobox-apple` — chuẩn này ưu tiên khi user yêu cầu tối ưu AIO). Theo khuôn định nghĩa:

```
[Sản phẩm] là mẫu [loại sản phẩm] giá tốt của Apple, ra mắt vào [ngày ra mắt]. Máy sở hữu màn hình [loại màn hình] [kích thước], chip [chip] mạnh mẽ, hỗ trợ Apple Intelligence, camera [tên camera] [MP], và [đặc điểm nổi bật khác, ví dụ thời lượng pin/ROM], mang đến trải nghiệm sử dụng ấn tượng trong tầm giá.
```

- Giữ link sản phẩm bọc quanh tên sản phẩm ngay đầu câu (anchor gốc trong bài, không đổi URL/title).
- Không lạm dụng bold, không thêm CTA đọc bài trong câu định nghĩa này (khác với mở bài thường).
- **Câu mở đầu bắt buộc nêu ngày ra mắt/thời điểm Apple giới thiệu ngay từ đầu**, theo 1 trong 2 khuôn:
  - `[Sản phẩm] ra mắt/được Apple giới thiệu ngày [ngày], ...`
  - `Ra mắt ngày [ngày], [Sản phẩm] ...`
- Ngày ra mắt là **thông tin mới cần thêm vào bài** (nếu bài gốc chưa có) → áp dụng đúng nguyên tắc bất biến "lấy nguồn từ Apple/nguồn công nghệ nước ngoài uy tín" (Wikipedia sản phẩm, MacRumors, 9to5Mac, The Verge...), không suy đoán. Nếu chỉ xác định được mốc tháng/năm (không có ngày cụ thể, ví dụ phụ kiện đi kèm sự kiện ra mắt máy chính), dùng mốc tháng/năm và nêu rõ trong "Thông tin cần confirm" là chưa tìm được ngày chính xác, để user tự bổ sung nếu cần.
- **Nếu bài gốc đã có sẵn 1 box "Đặc điểm nổi bật của [sản phẩm]"** (dạng đoạn bullet gạch đầu dòng ngắn, thường có style riêng như viền/nền nổi bật, liệt kê nhanh các đặc điểm chính) → **di chuyển box này lên vị trí NGAY ĐẦU BÀI, đứng TRƯỚC cả đoạn sapo**, giữ nguyên 100% nội dung/link bên trong, không viết lại. Đây là ngoại lệ về vị trí so với mặc định (sapo luôn ở đầu) vì box đặc điểm nổi bật đóng vai trò tóm tắt nhanh, ưu tiên hiển thị trước cả phần định nghĩa sapo.

### 5. Sửa lỗi factual chỉ khi được xác nhận

Ví dụ điển hình: chip Apple từ dòng A17 Pro/A18 trở lên không còn dùng tên hậu tố "Bionic" (chỉ các chip cũ hơn A16 mới có "Bionic"). Khi phát hiện lỗi kiểu này:

- Nêu rõ lỗi và vị trí xuất hiện (có thể xuất hiện nhiều chỗ, cả chữ thường/chữ hoa đầu câu — rà kỹ toàn bài, không chỉ 1 lần match).
- Chỉ sửa sau khi user xác nhận.
- Sau khi sửa, grep lại toàn bài để chắc chắn không còn sót instance nào (khác biệt hoa/thường ở đầu câu dễ bị `replace_all` với case chính xác bỏ sót).

### 6. Gỡ link ảnh trống `<a href="">`

TGDĐ có convention bọc ảnh bằng `<a href=""><img .../></a>` để phục vụ lightbox/zoom JS phía CMS — đây **không phải lỗi**, chỉ gỡ khi user yêu cầu rõ ("bỏ hết link ảnh đi"). Khi gỡ:

- Chỉ xóa các cặp `<a href="">...</a>` có href rỗng bọc `<img>`, giữ nguyên mọi `<a href="...">` có URL thật (link nội bộ, link sản phẩm khác) không đụng tới.
- Dùng regex/perl slurp-mode scoped chính xác để tránh xóa nhầm link thật.
- Verify lại bằng đếm số lượng `<a href="">` còn lại (phải bằng 0) và số `<img>` không đổi.

### 7. Gửi lại HTML

Sau khi hoàn tất các bước được yêu cầu trong lượt hiện tại, tự động gửi luôn full HTML minified sẵn sàng dán CMS (một dòng, không xuống dòng giữa block), không cần hỏi lại "có cần gửi không" — xem thêm `feedback-gui-full-html-khong-can-hoi` trong memory.

**Format cột "Các điểm đã fix/tối ưu" và "Thông tin cần confirm" (khi ghi vào Google Sheet):** cột này phục vụ **team content đối chiếu với bài gốc để duyệt trước khi up web** — người đọc là dân content/SEO, không phải người đã theo dõi toàn bộ quá trình chat. Vì vậy:

- Trình bày dạng gạch đầu dòng (`-`), mỗi ý 1 dòng, ngắn gọn, không viết thành đoạn văn dài.
- Mỗi bullet phải nêu rõ **đã thay đổi gì so với bài gốc** (kiểu "trước → sau" hoặc "bản gốc có X, đã đổi thành Y"), không viết chung chung kiểu "đã tối ưu mục A" mà không nói rõ khác gì so với gốc. Ví dụ đạt chuẩn: `Sapo: thêm câu mở nêu ngày ra mắt "..." (bản gốc không có thông tin này)`. Ví dụ chưa đạt: `Đã tối ưu lại sapo`.
- Với mục bị viết lại/cấu trúc lại hẳn (ví dụ đổi heading, gộp nhiều H3 thành 1 khối) → nêu rõ tên/heading cũ và tên/heading mới để content dễ dò trong bài.
- Không gộp nhiều thay đổi khác nhau vào 1 dòng.

### 8. Đưa mục "[Sản phẩm] giá bao nhiêu?" lên đầu bài

- Nếu bài **đã có** mục này (dù đang nằm ở giữa/cuối bài) → **di chuyển nguyên khối lên ngay sau sapo**, trước mọi heading khác. Giữ nguyên nội dung + link bên trong (chỉ cập nhật giá theo bước 3 nếu lệch).
- Nếu bài **chưa có** → tạo mới, đặt ngay đầu (sau sapo), nội dung **ngắn gọn**: giá bán hiện tại (lấy đúng số liệu sống từ link sản phẩm — không bịa) + CTKM đang áp dụng tại TGDĐ nếu có. Không lan sang thông số kỹ thuật, không CTA dài dòng.

Mẫu heading: `<h3 style="text-align: justify;"><strong>[Sản phẩm] giá bao nhiêu?</strong></h3>`

### 9. Viết mới hoặc tối ưu lại mục mua tại Thế Giới Di Động

- Nếu bài **chưa có** mục nào viết về TGDĐ → thêm mới, viết theo đúng format chuẩn bên dưới.
- Nếu bài **đã có** mục này nhưng đang ở dạng cũ/chưa đạt chuẩn (dấu hiệu: liệt kê bullet `•` nhiều lý do chung chung như "chất lượng đảm bảo", "giá cạnh tranh", "uy tín nhiều năm", "trả chậm linh hoạt"... không có số liệu/ưu đãi cụ thể, không bold entity, không đúng format HTML TGDĐ) → **viết lại theo chuẩn**, không giữ nguyên bản cũ.
- Nếu mục cũ có chứa link nội bộ ở đoạn bị xóa/viết lại (ví dụ link sản phẩm liên quan khác) → **phải giữ lại link đó**, chèn vào vị trí phù hợp trong bản mới (không được để mất link — xem thêm nguyên tắc bất biến).
- Wording, chính sách nêu ra (bảo hành, trả góp, thu cũ đổi mới, đa dạng màu/dung lượng...) phải **thêm bớt cho phù hợp loại sản phẩm thật** — không copy máy móc cho mọi sản phẩm. Ví dụ: phụ kiện giá rẻ (tai nghe, cáp sạc...) thường không có "thu cũ đổi mới" hay "đa dạng dung lượng/màu" như điện thoại — bỏ các ý không đúng thực tế của sản phẩm đó.

**Format chuẩn (đã chốt, thay cho mẫu H3 đơn giản trước đây):**

```html
<h3><strong>Mua [tên sản phẩm] chính hãng, giá tốt tại Thế Giới Di Động</strong></h3>
<p>Thế Giới Di Động là <strong>đại lý ủy quyền của Apple tại Việt Nam</strong>, cung cấp [loại sản phẩm] chính hãng với thông tin nguồn gốc, giá bán và chính sách bảo hành được công bố rõ ràng. Đây là địa chỉ phù hợp với người muốn mua [tên sản phẩm] an tâm, có thể xem hàng trực tiếp và nhận hỗ trợ trong suốt quá trình sử dụng.</p>
<p>[Đoạn 2: nêu các phiên bản/lựa chọn liên quan đang có tại TGDĐ, hoặc phụ kiện liên quan — GIỮ LINK gốc nếu đoạn cũ có link ở đây].</p>
<p>Bên cạnh yếu tố chính hãng, Thế Giới Di Động còn giúp người mua tối ưu chi phí nhờ <strong>giá niêm yết minh bạch và các chương trình ưu đãi theo từng thời điểm</strong>. [Câu bổ sung tùy chính sách thật áp dụng được cho sản phẩm — trả góp/thu cũ đổi mới/giảm giá trực tiếp, chỉ nêu cái có thật].</p>
<div style="width: 100%; max-width: 100%; margin: 18px 0; padding: 16px 20px; background-color: #fff9e6; border: 1px solid #f2c94c; border-left: 5px solid #f5b700; border-radius: 8px; box-sizing: border-box; color: #222222;">
<p style="margin: 0 0 12px 0; padding: 0 0 10px 0; border-bottom: 1.5px solid #ebd27b; font-weight: bold; color: #111111;">Lý do nên mua [tên sản phẩm] tại Thế Giới Di Động</p>
<ul>
<li><strong>[Tên sản phẩm] chính hãng</strong>, có thông tin nguồn gốc, giá bán và chính sách bảo hành rõ ràng.</li>
<li><strong>Giá niêm yết minh bạch</strong>, dễ kiểm tra, không phát sinh chi phí ẩn khi thanh toán.</li>
<li>[Chính sách ưu đãi thật đang áp dụng — giảm giá/quà tặng/trả góp/thu cũ đổi mới, tùy sản phẩm].</li>
<li>[Điểm phù hợp thực tế khác, ví dụ đa dạng lựa chọn nếu đúng, hoặc đóng gói/kiểm tra hàng trước khi thanh toán].</li>
<li>Hỗ trợ bảo hành, đổi trả và tư vấn kỹ thuật theo chính sách áp dụng tại thời điểm mua hàng.</li>
<li><a style="color: #0066cc; text-decoration: none; font-weight: bold;" title="Hệ thống siêu thị Thế Giới Di Động" href="https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong" target="_blank" rel="noopener">Hệ thống siêu thị Thế Giới Di Động</a> rộng khắp, thuận tiện để xem hàng, nhận hàng, bảo hành hoặc yêu cầu hỗ trợ trực tiếp.</li>
<li>Có thể đặt hàng online, chọn giao tận nơi hoặc nhận tại siêu thị tùy tình trạng sản phẩm ở từng khu vực.</li>
</ul>
</div>
<p style="margin: 16px 0 8px 0; font-weight: bold; color: #222222;">Bạn có thể kiểm tra giá và đặt mua [tên sản phẩm] qua các kênh:</p>
<ul style="margin: 0; padding-left: 20px;">
<li style="margin-bottom: 6px;">Cửa hàng trực tuyến: <a style="color: #0066cc; font-weight: 600;" title="Thế Giới Di Động" href="https://www.thegioididong.com/" target="_blank" rel="noopener">thegioididong.com</a></li>
<li>Hotline tư vấn và hỗ trợ khách hàng: <a style="color: #d9381e; font-weight: bold; text-decoration: none;" href="tel:1900232460">1900 232 460</a> (8:00 - 21:30)</li>
</ul>
```

**Lưu ý format khi dán vào CMS:** không set cứng `font-size`/`line-height` cho box và các đoạn/list trong mục này — để chữ ăn theo mặc định của trang, tránh bị to/lệch hẳn so với phần nội dung xung quanh (đã từng xảy ra khi set `font-size: 15px` trong khi phần còn lại của bài không set gì). Chỉ giữ style cho màu sắc, border, spacing của box.

**Lưu ý link "Cửa hàng trực tuyến":** anchor text là tên miền chung (`thegioididong.com`) nên trỏ về **trang chủ** `https://www.thegioididong.com/`, không trỏ về link sản phẩm cụ thể (khác với các link khác trong bài luôn trỏ đúng trang sản phẩm/danh mục liên quan).

### 10. Gom chuỗi H3 đặc điểm nổi bật thành 1 khối "Đánh giá... chi tiết, có nên mua ở thời điểm hiện tại không?"

Khi bài có chuỗi nhiều H3 liệt kê đặc điểm/tính năng nổi bật kiểu bài "vừa ra mắt" (ví dụ: thiết kế, hiệu năng, AI, camera/quay dựng, màn hình, pin, kết nối...) đứng riêng lẻ:

- Thêm 1 heading **H3** mới ngay trước chuỗi đó: `Đánh giá [tên sản phẩm] chi tiết, có nên mua ở thời điểm hiện tại không?`.
- Nội dung `<p>` bên dưới: **2-3 câu trả lời trực tiếp** (Có/Không + lý do cốt lõi, văn phong như bước 2) + **1 câu dẫn dắt** xuống các đặc điểm phía dưới.
- **Hạ cấp toàn bộ các H3 đặc điểm cũ xuống H4**, nằm lồng bên dưới H3 mới. Nội dung chi tiết trong từng H4 giữ nguyên y hệt, chỉ đổi cấp heading + bọc `<strong>` theo chuẩn H4.
- Nếu bài đã có sẵn 1 mục ý nghĩa trùng lặp ở chỗ khác (kể cả FAQ "có nên mua ở thời điểm này" từ bước 2) → **bỏ bớt, chỉ giữ 1 chỗ duy nhất** (chỗ mới gom ở đây) để tránh lặp ý.

Cấu trúc mẫu:
```
H3: Đánh giá [tên sản phẩm] chi tiết, có nên mua ở thời điểm hiện tại không?
   <p>...2-3 câu trả lời + 1 câu dẫn dắt...</p>
   H4: [đặc điểm 1]
   H4: [đặc điểm 2]
   ...
```

### 11. Đảm bảo bài luôn có kết bài in nghiêng + CTA

Bài phải kết thúc bằng 1 đoạn **in nghiêng** (`<em>`) tổng kết ngắn gọn giá trị sản phẩm, kèm CTA mua hàng trỏ về đúng link sản phẩm trong bài.

- Nếu bài **đã có** kết bài in nghiêng → giữ nguyên, không viết lại (trừ khi user yêu cầu).
- Nếu bài **chưa có** (như phát hiện lần đầu ở bài tai nghe MMTN2 — dừng đột ngột sau mục mua TGDĐ, không có đoạn tổng kết) → **thêm mới vào cuối bài**, đặt sau mục mua tại TGDĐ (bước 9), theo mẫu:

```html
<p style="text-align: justify;"><em>[Tên sản phẩm] là [tóm tắt 1 câu về giá trị/đối tượng phù hợp]. Bạn có thể mua [tên sản phẩm] chính hãng, giá tốt tại <a href="https://www.thegioididong.com/" target="_blank" title="Mua [tên sản phẩm] tại Thế Giới Di Động" rel="">thegioididong.com</a>.</em></p>
```

- CTA phải tự nhiên, không dùng cụm sáo rỗng ("Đừng bỏ lỡ", "Còn chần chờ gì nữa") — theo `tranh-van-phong-ai` mục 7.
- **Quan trọng — quy tắc chung cho MỌI link có anchor text là tên miền trần `thegioididong.com`**: bất cứ chỗ nào trong bài (kết bài, mục mua TGDĐ, hay bất kỳ đoạn nào khác) mà anchor text hiển thị đúng y chữ `thegioididong.com` (không phải tên sản phẩm/danh mục), link đó **luôn luôn phải trỏ về trang chủ** `https://www.thegioididong.com/`, **không được trỏ về link sản phẩm cụ thể trong bài**. Lý do: anchor text là tên miền chung nên phải dẫn đúng nghĩa đen tới đúng trang đó, tránh gây hiểu lầm/che dấu link thật khi hover. Các link khác có anchor text là tên sản phẩm/tính năng (ví dụ "Mua iPhone 15 128GB tại đây") vẫn trỏ đúng URL sản phẩm/danh mục liên quan như bình thường.

### 12. Thêm mục "Một số câu hỏi thường gặp" nếu bài chưa có

- **Bài nào đã có khối FAQ rồi thì không cần bổ sung** (dù FAQ đó không đặt tên đúng "Một số câu hỏi thường gặp", không đủ câu hỏi trong ngân hàng tham khảo, hay không có sẵn câu "[Tên sản phẩm] ra mắt khi nào?"). Chỉ áp dụng các bước liên quan khác (bước 2, bước 5...) lên đúng nội dung FAQ đã có, tuyệt đối không chèn thêm câu hỏi mới hay tạo thêm khối FAQ thứ hai. Bước 12 này **chỉ kích hoạt khi bài hoàn toàn chưa có FAQ**.
- Nếu bài **chưa có** khối FAQ nào → thêm mới **H3: Một số câu hỏi thường gặp**, đặt gần cuối bài (trước hoặc sau kết bài tùy mạch bài, ưu tiên trước kết bài ở bước 11), bên trong là các câu hỏi dạng **H4**, mỗi câu kèm `<p>` trả lời ngắn gọn.
- Câu hỏi đầu tiên bắt buộc là `[Tên sản phẩm] ra mắt khi nào?` — trả lời tái dùng đúng thông tin ngày ra mắt đã verify ở bước 1/bước 4 (không viết lại thông tin khác, không bịa thêm).
- Chọn thêm 1-2 câu hỏi khác cho phù hợp loại sản phẩm, từ ngân hàng câu hỏi tham khảo dưới đây (không bắt buộc dùng hết, chọn câu nào có thông tin thật để trả lời):

**Ngân hàng câu hỏi tham khảo (chọn theo loại sản phẩm, không cần dùng hết):**

- *Mua hàng/giá:* `[Sản phẩm] có đang được giảm giá không?`, `Mua [sản phẩm] trả góp 0% được không?`, `[Sản phẩm] có được thu cũ đổi mới không?`, `Nên mua [sản phẩm] chính hãng hay xách tay?`
- *So sánh:* `[Sản phẩm] khác gì so với [đời trước/bản thấp hơn]?`, `Có nên chọn [sản phẩm] thay vì [đối thủ cùng tầm giá]?`, `[Sản phẩm] phiên bản/dung lượng nào đáng mua nhất?`
- *Thông số/kỹ thuật (tùy loại sp):* `[Sản phẩm] pin dùng được bao lâu?`, `[Sản phẩm] có chống nước không?`, `[Sản phẩm] tương thích với thiết bị nào?`, `[Sản phẩm] bảo hành bao lâu, ở đâu?`
- *Quyết định mua:* `Ai nên mua [sản phẩm] này?`, `[Sản phẩm] có đáng nâng cấp từ [đời cũ] không?`, `Nhược điểm của [sản phẩm] là gì?`
- *Mua ở đâu:* `Mua [sản phẩm] chính hãng ở đâu uy tín, giá tốt?`

- Mỗi câu trả lời chỉ dùng thông tin **đã có trong bài hoặc đã verify** (giá/thông số lấy từ link sản phẩm, thông tin sản phẩm lấy từ Apple/nguồn uy tín theo nguyên tắc bất biến) — không tự bịa câu trả lời cho có đủ số lượng câu hỏi.
- Format heading H4 bọc `<strong>` theo chuẩn chung; văn phong ngắn gọn, trả lời thẳng, rà theo `tranh-van-phong-ai`.

### 13. Đánh số thứ tự heading

Làm ở **bước cuối cùng**, sau khi mọi thay đổi cấu trúc (di chuyển, gộp, thêm mục) đã chốt xong — vì số thứ tự phụ thuộc vào trật tự heading cuối cùng trong bài.

- Mọi **H3** trong bài được đánh số tuần tự từ `1.` theo đúng thứ tự xuất hiện trong bài (sapo không tính vì không có heading).
- Mọi **H4** là con của 1 H3 thì đánh số theo dạng `[số H3 cha].[số thứ tự trong H3 đó]`, bắt đầu lại từ `.1` ở mỗi H3 mới.
- Số đặt ở đầu tiêu đề, trong cùng thẻ `<strong>`, cách tên heading 1 khoảng trắng. Ví dụ:

```html
<h3><strong>1. Tai nghe có dây Apple MMTN2 giá bao nhiêu?</strong></h3>
<h3><strong>2. Đánh giá tai nghe có dây Apple MMTN2 chi tiết, có nên mua ở thời điểm hiện tại không?</strong></h3>
<h4><strong>2.1 Thiết kế trẻ trung, hiện đại</strong></h4>
<h4><strong>2.2 Trải nghiệm âm thanh trong trẻo</strong></h4>
<h3><strong>3. Mua tai nghe có dây Apple MMTN2 chính hãng, giá tốt tại Thế Giới Di Động</strong></h3>
<h3><strong>4. Một số câu hỏi thường gặp</strong></h3>
<h4><strong>4.1 Tai nghe có dây Apple MMTN2 ra mắt khi nào?</strong></h4>
<h4><strong>4.2 Tai nghe có dây Apple MMTN2 tương thích với thiết bị nào?</strong></h4>
```

- Nếu bài đã có H3/H4 đánh số từ trước theo đúng logic này → giữ nguyên, chỉ đánh số lại nếu thứ tự/số lượng heading đã thay đổi do các bước trên.
- Không đánh số H2 (nếu có) và không đánh số cho kết bài (không có heading).

### 14. Check số lượng ảnh, đề xuất bổ sung nếu thiếu

Đếm số thẻ `<img>` trong bài (HTML gốc, trước khi tối ưu — vì đây là việc kiểm tra hiện trạng, không phải việc mình tự chèn ảnh).

- Nếu bài có **0 ảnh** → ghi vào cột **"Đề xuất Content bổ sung"**: `Bài chưa có ảnh - Bổ sung tối thiểu 3 ảnh cho bài`
- Nếu bài có **1-2 ảnh** (dưới 3) → ghi: `Bổ sung tối thiểu 3 ảnh cho bài`
- Nếu bài có **từ 3 ảnh trở lên** → để trống cột này, không cần ghi gì.
- Đây chỉ là **đề xuất cho team Content**, không phải việc tự chèn ảnh vào bài — không tự ý thêm thẻ `<img>` hay ảnh minh họa nào vào HTML.

### 15. Sắp xếp lại đúng thứ tự cấu trúc bài (làm sau cùng, trước khi đánh số heading ở bước 13)

Sau khi đã áp dụng xong các bước nội dung ở trên, rà lại toàn bộ bài và **sắp xếp lại thứ tự các khối theo đúng trình tự chuẩn sau** (di chuyển nguyên khối, giữ nguyên nội dung/link bên trong từng khối, không viết lại):

1. Box "Đặc điểm nổi bật của [sản phẩm]" (nếu bài có box này — xem bước 4).
2. Sapo (đoạn mở đầu AIO, không heading).
3. H3: "[Sản phẩm] giá bao nhiêu?" (bước 8).
4. H3: "Đánh giá [sản phẩm] chi tiết, có nên mua ở thời điểm hiện tại không?" + toàn bộ các H4 con lồng bên dưới (bước 10).
5. H3 so sánh với sản phẩm cùng dòng (ví dụ so sánh các phiên bản dung lượng/màu/size khác) — **nếu bài có sẵn mục này**.
6. H3 so sánh với đời trước (ví dụ iPhone 17 so với iPhone 16) — **nếu bài có sẵn mục này**.
7. **Bất kỳ H3 nào khác phát sinh** không thuộc các mục đã liệt kê ở trên/dưới (ví dụ: mục về phụ kiện đi kèm, mục về công nghệ riêng, mục về hệ sinh thái...) → xếp vào đây, **ngay trước** mục "Mua... chính hãng, giá tốt tại TGDĐ". Giữ nguyên nội dung, không tự tạo mới.
8. H3: "Mua [sản phẩm] chính hãng, giá tốt tại Thế Giới Di Động" (bước 9).
9. H3: "Một số câu hỏi thường gặp" + mỗi câu hỏi là 1 H4 con (bước 12).
10. Kết bài in nghiêng (`<em>`) + CTA, không có heading riêng (bước 11) — luôn là khối cuối cùng của bài.

Lưu ý:
- Chỉ áp dụng bước này cho các khối **đã có sẵn trong bài** hoặc **đã được tạo mới ở các bước trước** — không tự bịa thêm mục nào chỉ để lấp đầy thứ tự.
- Việc này chỉ là sắp xếp lại vị trí, không đổi nội dung bên trong từng khối.
- Sau khi sắp xếp xong đúng thứ tự này mới thực hiện đánh số heading ở bước 13 (đánh số theo thứ tự xuất hiện sau khi đã sắp xếp lại).

## Checklist Trước Khi Gửi

- [ ] Heading mở bán/đặt trước đã đổi thành "ra mắt khi nào?" và chỉ còn ngày ra mắt.
- [ ] FAQ "có gì mới" đã đổi thành "có nên mua ở thời điểm này" theo đúng khuôn mẫu.
- [ ] Giá/ưu đãi đã verify qua link sản phẩm trong bài, cập nhật nếu lệch.
- [ ] Tiêu đề bảng giá là "Giá bán tham khảo", đã xóa cột "Giá bán quốc tế".
- [ ] Sản phẩm không có link để check giá, hoặc hết hàng/ngừng kinh doanh: không nhắc tình trạng trong bài, giữ nguyên giá cũ nếu đang có trong bảng, không tự đoán giá mới.
- [ ] Có dòng lưu ý `<i>Lưu ý: Giá bán được cập nhật ngày [ngày xử lý bài], có thể thay đổi theo thời gian, tuỳ thuộc vào CTKM.</i>` ngay sau bảng giá, dùng đúng ngày xử lý bài (không phải ngày cũ).
- [ ] Không có câu kiểu "giá đã đối chiếu trên website" trong nội dung.
- [ ] Sapo đã viết lại theo khuôn định nghĩa AIO, không còn định dạng heading.
- [ ] Không tự sửa lỗi factual nào chưa được user xác nhận.
- [ ] Nếu đã gỡ `<a href="">` rỗng: 0 anchor rỗng còn lại, số `<img>` không đổi, mọi link thật còn nguyên.
- [ ] Mục "[Sản phẩm] giá bao nhiêu?" đã nằm ngay đầu bài (sau sapo), giá lấy đúng từ link sản phẩm, không bịa số liệu.
- [ ] Mục mua tại TGDĐ đã có và đúng chuẩn (không còn dạng bullet liệt kê chung chung nếu trước đó là bản cũ).
- [ ] Nếu bài có chuỗi H3 đặc điểm nổi bật: đã gom vào 1 khối H3 "Đánh giá... chi tiết, có nên mua ở thời điểm hiện tại không?" + hạ các đặc điểm xuống H4, không còn mục trùng ý ở chỗ khác.
- [ ] Không xóa bất kỳ link nội bộ nào đang có sẵn trong bài (Sản phẩm liên quan, bảng so sánh, kết bài...); nếu câu văn quanh link bị sai thực tế thì sửa câu, không xóa link.
- [ ] Đã rà `tranh-van-phong-ai` trên TOÀN BỘ bài (kể cả đoạn giữ nguyên) — hết em-dash, hết cụm sáo rỗng lặp lại.
- [ ] Thứ tự các khối trong bài đúng chuẩn bước 15: (box đặc điểm nổi bật nếu có) → sapo → giá bao nhiêu → Đánh giá...chi tiết + H4 con → so sánh cùng dòng (nếu có) → so sánh đời trước (nếu có) → H3 khác phát sinh (nếu có, đặt trước mục Mua TGDĐ) → Mua tại TGDĐ → Câu hỏi thường gặp (mỗi câu 1 H4) → kết bài in nghiêng (luôn cuối cùng).
- [ ] Nếu sản phẩm không phải điện thoại: đã note rõ bước nào N/A và vì sao trong "Thông tin cần confirm", không im lặng bỏ qua.
- [ ] Nếu có thêm nội dung/thông tin mới chưa từng có trong bài: đã lấy từ Apple hoặc nguồn công nghệ nước ngoài uy tín, có nêu nguồn tham khảo trong "Thông tin cần confirm".
- [ ] Câu mở đầu sapo đã nêu ngày ra mắt/thời điểm Apple giới thiệu ngay từ đầu theo khuôn đã chốt.
- [ ] Bài đã có kết bài in nghiêng (`<em>`) + CTA mua chính hãng giá tốt tại thegioididong.com.
- [ ] Mọi link có anchor text đúng y chữ "thegioididong.com" (kết bài, mục mua TGDĐ...) đều trỏ về trang chủ `https://www.thegioididong.com/`, không trỏ về link sản phẩm cụ thể.
- [ ] Nếu bài có sẵn box "Đặc điểm nổi bật của [sản phẩm]" → đã di chuyển lên đầu bài, đứng trước sapo.
- [ ] Bài đã có mục "Một số câu hỏi thường gặp" (nếu chưa có sẵn FAQ khác) với câu đầu "[Tên sản phẩm] ra mắt khi nào?" + 1-2 câu khác phù hợp sản phẩm, mọi câu trả lời đều có căn cứ thật, không bịa.
- [ ] Tất cả H3 đã đánh số tuần tự `1.`, `2.`... theo đúng thứ tự trong bài; H4 con của H3 nào đánh số `[số H3].1`, `[số H3].2`... đúng logic, làm sau cùng khi cấu trúc heading đã chốt.
- [ ] Đã đếm số `<img>` trong bài gốc; nếu 0 ảnh hoặc dưới 3 ảnh đã ghi đề xuất vào cột "Đề xuất Content bổ sung" đúng câu chữ đã chốt, không tự chèn ảnh vào bài.
- [ ] Không đổi bất kỳ nội dung nào ngoài phạm vi được yêu cầu.
- [ ] HTML xuất ra dạng minified một dòng, đúng chuẩn dán CMS TinyMCE.
- [ ] Đã gửi lại full HTML ngay, không hỏi lại.
