---
name: tgdd-infobox-nganh-hang
description: "Viết, audit và chỉnh sửa Infobox cho trang NGÀNH HÀNG tổng của Thế Giới Di Động như Laptop, Điện thoại, Tai nghe, Máy tính bảng, Tivi, Máy ảnh, Loa hoặc Smartwatch. Dùng khi chủ thể chỉ là một ngành hàng, không kèm hãng, dòng hay thuộc tính. Skill hướng dẫn research sản phẩm thực sự có trong URL danh mục, xây outline, viết nội dung tư vấn dễ hiểu, giới thiệu đặc điểm các thương hiệu mà không xếp hạng, tổng hợp ưu đãi/chính sách thành CTA và kiểm tra chất lượng trước khi giao bài."
---

# TGDĐ Infobox - Trang Ngành Hàng (Type 1)

## Mục tiêu

Người đọc đang khám phá ngành hàng và chưa chốt thương hiệu. Nội dung phải giúp họ hiểu sản phẩm, thông số quan trọng, các nhóm nhu cầu, đặc điểm riêng của những thương hiệu đang có sản phẩm trong danh mục và cách chọn phù hợp.

## Đầu vào

Bắt buộc có:

- **Tên ngành hàng**
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
   mục người dùng cung cấp. Riêng section "Các thương hiệu {ngành hàng} phổ
   biến" được nhắc các hãng phổ biến khác trên thị trường ở mức đặc điểm
   chung, không kèm model/giá — xem ngoại lệ trong
   `references/research-rules.md`.
2. Không tự bịa URL nội bộ, không viết placeholder chèn link, không chèn link
   bằng tay khi đang viết draft. Internal link **là bắt buộc** và được chèn ở
   bước tối ưu HTML sau đó bằng skill `content-html-optimizer` (chạy với
   `--fetch-links`), lấy URL từ Sheet MWG đã kiểm chứng — không phải từ trí nhớ.
   Bản draft giao đi phải sạch link để bước optimizer làm đúng phần của nó;
   bài **chưa** qua bước chèn link thì **chưa** được coi là hoàn tất.
3. Không xếp hạng thương hiệu và không viết “hãng nào tốt nhất”.
4. Không mặc định phải audit giá, tồn hàng, khuyến mãi hoặc trạng thái kinh doanh theo ngày và khu vực.
5. Phần CTA tổng hợp ưu đãi và chính sách từ các sản phẩm trong danh mục rồi viết thành lợi ích mua hàng; không kể lại cách website hiển thị dữ liệu.
6. Dùng ngôn ngữ đơn giản, tránh từ báo cáo như “phân tầng”, “tier”, “level” khi có cách nói tự nhiên hơn.
7. Nếu brief hoặc yêu cầu người dùng xung đột với ví dụ cũ, ưu tiên workflow và reference trong skill này.

## Latest feedback rules

- Keep the TGDĐ purchase CTA compact: one section heading, a short lead, checklist bullets, and an optional short closing sentence. Do not create smaller headings inside this CTA.
- Before a comparison table, use one simple reader-facing lead sentence. Do not explain editorial choices or research methodology.
- Merge only headings that answer the same purchase question. The classification, brand, and highlighted-products sections each keep a distinct role and must not be merged. Read the detailed overrides in `references/formatting-rules.md`, `references/cta-rules.md`, and `references/final-checklist.md`.

- Trong bảng `Các sản phẩm ... tại Thế Giới Di Động`, **cột tên sản phẩm phải bọc link về đúng trang chi tiết của từng sản phẩm**, URL lấy thật từ trang danh mục (không suy từ mã SKU, không lấy từ Sheet keyword). Đây là ngoại lệ duy nhất của quy tắc không chèn link trong `<table>`, và `content-html-optimizer` không tự làm bước này. Chi tiết ở `references/formatting-rules.md`.
- Mục "Tại sao nên mua / sử dụng...": Các lợi ích / tiêu chí con BẮT BUỘC PHẢI format thành heading con H4 (`#### ...` / `<h4>...</h4>`), tuyệt đối không dùng đoạn văn in đậm (`**...**` / `<p><strong>...</strong></p>`) giả heading, để chuẩn cấu trúc heading CMS và đảm bảo quy tắc phủ hình AI (`image-ai-generate`) luôn tạo hình riêng cho từng mục.
