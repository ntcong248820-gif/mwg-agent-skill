---
name: tgdd-infobox-dong-san-pham
description: "Viết, audit và chỉnh sửa Infobox cho trang NGÀNH HÀNG + DÒNG SẢN PHẨM của Thế Giới Di Động như Laptop Asus ROG, Laptop HP EliteBook, iPhone Series, Samsung Galaxy S Series, MacBook Pro hoặc tai nghe Sony WH-1000XM. Dùng khi người đọc đã chọn hãng và dòng, cần phân biệt các sản phẩm hoặc phiên bản thực sự có trong URL danh mục, hiểu điểm nổi bật và chọn theo nhu cầu. Không nhắc model ngoài danh mục, không bắt buộc audit giá/tồn kho theo ngày-khu vực. Draft không tự bịa URL; internal link bắt buộc được chèn sau bằng content-html-optimizer."
---

# TGDĐ Infobox - Trang Ngành Hàng + Dòng Sản Phẩm (Type 4)

## Mục tiêu

Người đọc đã chọn hãng và dòng sản phẩm, có nhu cầu mua cao và cần phân biệt các phiên bản cụ thể. Đây là loại Infobox được phép phân tích model, nhưng chỉ model xuất hiện trong URL danh mục.

## Đầu vào

Bắt buộc có:

- **Tên dòng sản phẩm**
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

1. Chỉ nhắc sản phẩm có trong URL danh mục người dùng cung cấp.
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
- Merge headings that cover the same product group or purchase intent. Read the detailed overrides in `references/formatting-rules.md`, `references/cta-rules.md`, and `references/final-checklist.md`.
- Write the line overview and every knowledge section in the voice of someone introducing the product line. Never cite where the information came from ("trên trang chính thức của hãng", "theo website hãng"). Sources exist to make the sentence true, not to appear in it.
- The buying-guide section advises on the whole product line, not on the SKUs TGDĐ currently stocks. Do not open it by counting catalog items, and do not shrink the line to its sub-branch.
- Only two sections may mention Thế Giới Di Động or what it sells: `Các sản phẩm {dòng} tại Thế Giới Di Động` and the CTA. Read `references/writing-rules.md` and `references/outline.md` for the exact wording rules.

- Trong bảng `Các sản phẩm ... tại Thế Giới Di Động`, **cột tên sản phẩm phải bọc link về đúng trang chi tiết của từng sản phẩm**, URL lấy thật từ trang danh mục (không suy từ mã SKU, không lấy từ Sheet keyword). Đây là ngoại lệ duy nhất của quy tắc không chèn link trong `<table>`, và `content-html-optimizer` không tự làm bước này. Chi tiết ở `references/formatting-rules.md`.
- Mục "Tại sao nên mua / sử dụng...": Các lợi ích / tiêu chí con BẮT BUỘC PHẢI format thành heading con H4 (`#### ...` / `<h4>...</h4>`), tuyệt đối không dùng đoạn văn in đậm (`**...**` / `<p><strong>...</strong></p>`) giả heading, để chuẩn cấu trúc heading CMS và đảm bảo quy tắc phủ hình AI (`image-ai-generate`) luôn tạo hình riêng cho từng mục.
