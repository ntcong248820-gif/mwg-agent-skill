# Quy tắc cấu trúc và định dạng

## Heading theo CMS Type 2

- Sapo dùng H2.
- Section chính dùng H3.
- Heading con và câu hỏi FAQ dùng H4.
- Không dùng H1.

## Chọn đúng dạng trình bày

- Dùng đoạn văn để giải thích nguyên nhân, tác động và nhận định.
- Dùng checklist khi có nhiều ý độc lập cần quét nhanh.
- Dùng bảng khi các đối tượng cần so sánh theo cùng bộ tiêu chí.
- Không xếp nhiều đoạn ngắn với nhãn in đậm để giả làm danh sách nếu checklist sẽ rõ hơn.

## Section có checklist hoặc bảng

Mỗi section phải đủ ba phần:

1. Dẫn đoạn tối thiểu 2 câu: đặt bối cảnh và giải thích vì sao danh sách ảnh hưởng đến lựa chọn.
2. Checklist hoặc bảng.
3. Kết đoạn 1-2 câu: giúp người đọc hiểu nên ưu tiên gì.

Không kết thúc section ngay sau bullet hoặc hàng cuối của bảng.

## Section “Tại sao nên...”

Section này (ví dụ: "Tại sao nên sử dụng...", "Tại sao nên mua...", "Tại sao nên chọn...") giải thích các lợi ích cốt lõi của ngành hàng hoặc dòng sản phẩm.

1. **Mỗi lợi ích / tiêu chí con BẮT BUỘC PHẢI là một heading con H4 riêng** (`#### [Tên lợi ích]` trong Markdown hoặc `<h4>[Tên lợi ích]</h4>` trong HTML).
2. **TUYỆT ĐỐI KHÔNG** dùng nhãn in đậm (`**...**` hoặc `<p><strong>...</strong></p>`) để giả làm heading. Việc dùng H4 là bắt buộc để:
   - Chuẩn cấu trúc ngữ nghĩa (semantic heading) CMS và mục lục (TOC).
   - Đảm bảo quy tắc phủ hình AI (`image-ai-generate`) tự động quét trúng từng H4 lá và tạo hình ảnh AI riêng biệt cho từng mục con này.
3. Mỗi H4 giải thích tối thiểu khoảng 3 câu:
   - Nêu cơ chế hoặc lý do tính năng tạo ra lợi ích.
   - Nêu tác động thực tế với người dùng.
   - Nêu điều kiện, ví dụ hoặc giới hạn để tránh khẳng định chung chung.

Ví dụ cấu trúc chuẩn:

```markdown
#### Hạn chế sai sót khi tính tiền

Mỗi sản phẩm được ghi nhận trên phần mềm trước khi hóa đơn được in, nên nhân viên không phải chép lại tên hàng, số lượng và giá bán. Dữ liệu được tổng hợp theo cùng một đơn giúp giảm nguy cơ bỏ sót mặt hàng hoặc cộng nhầm tổng tiền. Lợi ích này phát huy tốt khi thông tin sản phẩm và giá trong phần mềm đã được thiết lập chính xác.
```

## Section "Đặc điểm nổi bật của các hãng hoặc dòng sản phẩm"

Khi section có 2 hãng/dòng trở lên, trình bày đúng thứ tự sau, không đảo:

1. Một bảng tổng hợp đặc điểm theo từng hãng/dòng ngay đầu section (ví dụ:
   Hãng/Dòng, Điểm mạnh, Phân khúc giá, Phù hợp với) để người đọc nắm tổng
   quan trước khi đọc chi tiết.
2. Sau bảng, mỗi hãng/dòng viết thành một heading con (H4) riêng, dài 1-2
   đoạn, không xếp hạng.

Không đặt bảng tổng hợp ở cuối section sau khi đã trình bày chi tiết từng
hãng — bảng luôn đứng trước để đóng vai trò tổng quan.

## Section “Những sai lầm thường gặp”

Viết 2 câu dẫn, sau đó dùng checklist theo mẫu:

```markdown
- **[Sai lầm]:** [Hậu quả]. [Cách tránh hoặc cách kiểm tra].
```

Không tách từng sai lầm thành heading có một đoạn ngắn. Kết section bằng 1-2 câu nêu thứ tự ưu tiên khi kiểm tra.

## Đoạn văn

- Mỗi đoạn nên có 2-4 câu vừa phải.
- Một heading không dùng checklist hoặc bảng cần chiều sâu tương đương khoảng 4 câu, có thể chia thành 1-2 đoạn.
- Không kéo dài bằng câu lặp hoặc câu quảng cáo chung chung.

## FAQ

- Mỗi câu hỏi là heading con theo cấp được quy định trong `outline.md`.
- Câu trả lời là đoạn văn ngay bên dưới, không dùng bullet con.
- Trả lời trực tiếp trước, sau đó giải thích điều kiện hoặc ví dụ.
- Ưu tiên câu hỏi ảnh hưởng đến quyết định mua, khả năng tương thích, cách chọn và chính sách.

## Simple lead-in before tables - latest rule

This rule overrides the earlier requirement for a minimum two-sentence lead before a table.

- Use one direct, reader-facing sentence before a comparison table.
- Preferred pattern: "De hieu ro hon ve su khac nhau giua ..., cac ban co the tham khao bang duoi day:"
- Adapt the subject naturally to the category and write the final sentence in Vietnamese with diacritics.
- Do not describe editorial decisions such as "the table focuses on...", "price is not used as a criterion", or "the data below represents...".
- After the table, add 1-2 concise sentences that help the reader choose or identify the main difference.

## Do not repeat headings for the same product group

- Before writing, compare the intent of all planned headings. Merge headings that introduce, describe, and compare the same product group.
- Do not create one section for the brand or line and another section immediately below for the same products unless the two sections answer clearly different purchase questions.
- Prefer one complete section containing the short introduction, comparison table, and buying takeaway.
- If product differences were already covered sufficiently in a needs-based section, do not repeat the same model descriptions in a second product section.

## CTA checklist format

- Use only the main CTA section heading.
- Inside the CTA, use a short lead plus checklist bullets with bold labels; do not use smaller headings for each benefit.
- The general table/checklist lead rules do not force a long lead for this CTA. Keep it compact.

## Bảng sản phẩm tại TGDĐ: tên sản phẩm phải là link về trang sản phẩm

Trong section `Các sản phẩm ... tại Thế Giới Di Động`, mọi ô ở **cột tên sản
phẩm** phải được bọc link trỏ về **đúng trang chi tiết của chính sản phẩm đó**.
Người đọc bảng để so, rồi click để mua — bảng không có link là cắt đúng bước đó.

Đây là **ngoại lệ** của quy tắc "không chèn link trong `<table>`". Ngoại lệ chỉ
áp cho cột tên sản phẩm của bảng liệt kê sản phẩm, không mở cho cột nào khác và
không mở cho bảng khác (bảng thông số, bảng so sánh dòng con...).

### Lấy URL ở đâu

**Không** lấy từ Sheet keyword. Trang chi tiết sản phẩm (SKU) không nằm trong
Sheet đó — Sheet chỉ có URL danh mục và URL bài viết. Lấy trực tiếp từ **trang
danh mục** đang viết:

```bash
curl -s -m 30 -A "Mozilla/5.0" "https://www.thegioididong.com/{category-slug}" -o /tmp/cat.html
```

Trong HTML danh mục, mỗi sản phẩm là một khối có `data-name` (tên đầy đủ kèm mã
SKU) và thẻ `<a href='/laptop/...'>` — **href dùng dấu nháy đơn**, nên regex viết
theo `"` sẽ trượt hết. Ghép SKU trong `data-name` với `href` để ra URL.

Mã SKU theo hãng có độ dài khác nhau — đếm lại trước khi viết regex, đừng đoán:

| Dạng | Ví dụ | Regex |
| --- | --- | --- |
| Lenovo | `83M0002YVN` | `83[A-Z0-9]{6}VN` |
| Acer | `NH.QVYSV.001` | `NH\.[A-Z0-9]{5}\.\d{3}` |

Đếm sai một ký tự thì regex trả 0 kết quả và trông y như "danh mục không có sản
phẩm nào" — đã xảy ra thật với cả hai dạng trên.

### Ràng buộc

- Link phải là URL thật đọc được từ trang danh mục. **Không suy URL từ mã SKU.**
- Mỗi sản phẩm link về đúng trang của nó; không dồn nhiều sản phẩm về một URL.
- Anchor là **toàn bộ tên sản phẩm trong ô**, kèm mã SKU nếu ô có mã. Không cắt lẻ.
- Dùng `rel="noopener noreferrer" target="_blank"` như mọi link khác trong bài.
- Rule "1 URL 1 link" của internal link **không** áp cho các link này: đây là link
  sản phẩm, mỗi dòng một URL riêng nên không có chuyện trùng.
- Bước này `content-html-optimizer` **không tự làm** — script vẫn chặn link trong
  `<table>`. Phải làm thủ công, xem mục "product listing table" của skill đó.

### Lấy URL thì lấy luôn giá

Trang danh mục có sẵn giá hiển thị, nên đọc luôn trong cùng lượt curl và đối
chiếu với cột giá trong bảng. Giá hiển thị nằm ở `class="price"`; khi sản phẩm
đang giảm thì có 2 giá, **giá đầu là giá bán, giá sau là giá gạch** — lấy giá
đầu. Không dùng `data-price`: đó là giá gốc chưa giảm, lệch tới hàng chục triệu.
Giá lệch thì sửa số **và** sửa luôn mốc ngày cập nhật trong bài.
