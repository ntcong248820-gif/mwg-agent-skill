---
name: tgdd-infobox-nganh-hang-thuoc-tinh
description: "Viết, audit và chỉnh sửa Infobox cho trang NGÀNH HÀNG + THUỘC TÍNH của Thế Giới Di Động như Laptop Gaming, Laptop Văn phòng, Điện thoại 5G, Tai nghe Chống ồn, TV OLED hoặc Máy in hóa đơn. Dùng khi người đọc đã có tiêu chí, công dụng, công nghệ hoặc phân khúc cụ thể. Skill hướng dẫn research đúng sản phẩm trong URL danh mục, giải thích thuộc tính, lợi ích, tiêu chí chọn, đặc điểm các hãng mà không xếp hạng, CTA ưu đãi/chính sách và FAQ. Draft không tự bịa URL; internal link bắt buộc được chèn sau bằng content-html-optimizer."
---

# TGDĐ Infobox - Trang Ngành Hàng + Thuộc Tính (Type 3)

## Mục tiêu

Người đọc đã biết nhu cầu hoặc thuộc tính cần tìm nhưng chưa chốt sản phẩm. Nội dung phải giải thích thuộc tính, lợi ích, tiêu chí kỹ thuật, các nhóm lựa chọn và đặc điểm nổi bật của hãng hoặc dòng có mặt trong danh mục.

## Đầu vào

Bắt buộc có:

- **Tên ngành hàng + thuộc tính**
- **URL danh mục TGDĐ đang viết**

Có thể nhận thêm brief, đối tượng mục tiêu, điểm cần nhấn mạnh hoặc chương trình ưu đãi. Nếu URL chưa có, hỏi đúng một câu để lấy URL trước khi research vì URL quyết định phạm vi sản phẩm.

## Workflow bắt buộc

Đọc `references/workflow.md` trước và thực hiện tuần tự. Không tải toàn bộ reference vào context ngay từ đầu.

- Khi khoanh sản phẩm hoặc research: đọc `references/research-rules.md`.
- Khi xây outline: đọc `references/outline.md`.
- Khi viết nội dung chính: đọc `references/writing-rules.md` và `references/formatting-rules.md`.
- Khi viết phần mua tại TGDĐ: đọc `references/cta-rules.md`.
- Trước khi giao bài: đọc `references/final-checklist.md`.

## Quy tắc cứng

1. Chỉ nhắc sản phẩm cụ thể, model, giá và ví dụ mua hàng có trong URL danh
   mục người dùng cung cấp. Riêng section "Các thương hiệu {ngành hàng}
   {thuộc tính} phổ biến" được nhắc các hãng phổ biến khác trên thị trường ở
   mức đặc điểm chung, không kèm model/giá — xem ngoại lệ trong
   `references/research-rules.md`.
2. Không tự bịa URL nội bộ, không viết placeholder chèn link, không chèn link
   bằng tay khi đang viết draft. Internal link **là bắt buộc** và được chèn ở
   bước tối ưu HTML sau đó bằng skill `content-html-optimizer` (chạy với
   `--fetch-links`), lấy URL từ Sheet MWG đã kiểm chứng — không phải từ trí nhớ.
   Bản draft giao đi phải sạch link để bước optimizer làm đúng phần của nó;
   bài **chưa** qua bước chèn link thì **chưa** được coi là hoàn tất. Có 2
   ngoại lệ được chèn link tay ngay khi viết draft, cả hai đều bắt buộc verify
   URL thật trước khi chèn (không suy đoán, không lấy từ trí nhớ) — xem
   "Latest feedback rules" bên dưới và `references/formatting-rules.md`.
3. Không xếp hạng thương hiệu và không viết “hãng nào tốt nhất”.
4. Không mặc định phải audit giá, tồn hàng, khuyến mãi hoặc trạng thái kinh doanh theo ngày và khu vực.
5. Phần CTA tổng hợp ưu đãi và chính sách từ các sản phẩm trong danh mục rồi viết thành lợi ích mua hàng; không kể lại cách website hiển thị dữ liệu.
6. Dùng ngôn ngữ đơn giản, tránh từ báo cáo như “phân tầng”, “tier”, “level” khi có cách nói tự nhiên hơn.
7. Nếu brief hoặc yêu cầu người dùng xung đột với ví dụ cũ, ưu tiên workflow và reference trong skill này.

## Latest feedback rules

- Keep the TGDĐ purchase CTA compact: one section heading, a short lead, checklist bullets, and an optional short closing sentence. Do not create smaller headings inside this CTA.
- Before a comparison table, use one simple reader-facing lead sentence. Do not explain editorial choices or research methodology.
- Merge only headings that answer the same purchase question. The classification, brand, and highlighted-products sections each keep a distinct role and must not be merged. Read the detailed overrides in `references/formatting-rules.md`, `references/cta-rules.md`, and `references/final-checklist.md`.

- Trong bảng `Các sản phẩm ... tại Thế Giới Di Động`, **cột tên sản phẩm phải bọc link về đúng trang chi tiết của từng sản phẩm**, URL lấy thật từ trang danh mục (không suy từ mã SKU, không lấy từ Sheet keyword). Đây là ngoại lệ thứ nhất của quy tắc không chèn link tay/không chèn link trong `<table>`, và `content-html-optimizer` không tự làm bước này. Chi tiết ở `references/formatting-rules.md`.
- Section "Các thương hiệu ... phổ biến" phải có internal link thật cho tên hãng/dòng máy được nhắc tới, đặt ở dẫn đoạn hoặc kết đoạn (không đặt trong ô bảng). Đây là ngoại lệ thứ hai của quy tắc "không chèn link bằng tay khi đang viết draft" — verify URL bằng `curl` trước khi chèn, không suy đoán. Chi tiết ở `references/formatting-rules.md`.
- Không viết chú giải tiếng Anh trong ngoặc đơn nếu câu tiếng Việt phía trước đã đủ nghĩa, ví dụ "xem trước (preview)", "hiệu ứng màu sắc (Color Grading)", "nhà thiết kế đồ họa (Graphic Designer)" — bỏ phần ngoặc. Chỉ giữ ngoặc đơn khi nó thêm thông tin phân biệt thật (mã sản phẩm, tên viết tắt sẽ dùng lại nhiều lần, tên riêng công nghệ/switch/chuẩn màu).
- Không dùng cảm thán hoặc ví von đặt trong dấu ngoặc kép kiểu văn báo mạng, ví dụ "hụt hơi", "sát thủ phần cứng", "treo máy", "hồi sinh", "cánh tay phải". Đây là lối viết khoa trương vi phạm mục Giọng văn ở `references/writing-rules.md`; viết lại thành câu trung tính mô tả đúng hiện tượng.
- Câu trả lời FAQ phải là một đoạn văn liền mạch, **không được chèn `<ul>/<li>` bên trong câu trả lời** dù nội dung có nhiều ý — lỗi hay tái phạm nhất của mục FAQ dù `references/formatting-rules.md` đã có rule "không dùng bullet con". Nếu một câu hỏi có nhiều nhánh (ví dụ so sánh 2 lựa chọn), nối các nhánh bằng câu văn, không tách bullet.
- Mục "Tại sao nên mua / sử dụng...": Các lợi ích / tiêu chí con BẮT BUỘC PHẢI format thành heading con H4 (`#### ...` / `<h4>...</h4>`), tuyệt đối không dùng đoạn văn in đậm (`**...**` / `<p><strong>...</strong></p>`) giả heading, để chuẩn cấu trúc heading CMS và đảm bảo quy tắc phủ hình AI (`image-ai-generate`) luôn tạo hình riêng cho từng mục.
