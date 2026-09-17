# Outline mặc định - Trang Ngành Hàng (Type 1)

Điều chỉnh tên section theo ngành hàng thực tế. Không bắt buộc giữ một section nếu research cho thấy nó không tạo thêm giá trị.

## Cấu trúc đề xuất

```markdown
## {Ngành hàng} chính hãng tại Thế Giới Di Động
Sapo 4-6 câu: ngành hàng là gì, phù hợp với ai, người đọc sẽ được tư vấn những gì.

### {Ngành hàng} là gì?
Giải thích ngắn gọn, dễ hiểu và nêu vai trò thực tế.

### Các thông số cần biết khi chọn {ngành hàng}
Mỗi thông số, công nghệ hoặc khái niệm kỹ thuật là một heading con (H4) riêng,
không trình bày dạng bảng so sánh. Xem `references/formatting-rules.md`.

### Các loại {ngành hàng} phổ biến
Phân loại sản phẩm theo MỘT tiêu chí rõ ràng (kiểu thiết kế, công nghệ, kích
thước, cách dùng). Không kể tên thương hiệu ở đây. **Mỗi loại là một H4 riêng**
viết 2-4 đoạn (cách hoạt động, điểm mạnh, giới hạn, ai nên chọn), không gom
thành checklist. Xem `references/formatting-rules.md`.

### Nên chọn {ngành hàng} nào theo nhu cầu?
Mỗi nhu cầu là một heading con (H4) riêng, ví dụ "{Ngành hàng} cho văn
phòng", "... cho chơi game", "... cho gia đình". Mỗi H4 nêu đặc điểm sản phẩm
phù hợp với nhu cầu đó. Xem `references/formatting-rules.md`.

### Các thương hiệu {ngành hàng} phổ biến
Bối cảnh thương hiệu trên thị trường, không giới hạn theo danh mục TGDĐ. Mở
đầu bằng bảng tổng hợp theo từng thương hiệu, sau đó mỗi thương hiệu là một
H4 dài khoảng 1 đoạn. Không xếp hạng, không nêu model/giá cụ thể ở section
này. Xem `references/research-rules.md` và `references/formatting-rules.md`.

### Các sản phẩm {ngành hàng} nổi bật tại Thế Giới Di Động
Bảng khoảng 5 sản phẩm bán chạy nhất trong URL danh mục, cột tên sản phẩm,
thông số chính và giá bán. Đây là section duy nhất nêu model và giá cụ thể.

### Chọn {ngành hàng} theo mức ngân sách
Mỗi mức ngân sách/phân khúc giá là một heading con (H4) riêng, nêu rõ đặc điểm
sản phẩm nhận được và giá trị so với số tiền bỏ ra ở mức giá đó. Xem
`references/formatting-rules.md`.

### Vì sao nên mua {ngành hàng} tại Thế Giới Di Động?
Viết theo references/cta-rules.md.

### Câu hỏi thường gặp
6-10 câu hỏi thực tế.
```

## Heading theo CMS Type 1

- Sapo dùng H2.
- Section chính dùng H3.
- Heading con và câu hỏi FAQ dùng H4.
- Không dùng H1.

## Giới hạn nội dung

- Không biến bài thành danh sách sản phẩm cụ thể. Model, giá và ví dụ sản
  phẩm chỉ được lấy từ URL danh mục, và chỉ xuất hiện trong section "Các sản
  phẩm ... nổi bật tại Thế Giới Di Động" và CTA.
- Section "Các thương hiệu ... phổ biến" được nhắc thương hiệu ngoài danh mục
  ở mức đặc điểm chung — xem `references/research-rules.md`.
- Không so sánh hoặc xếp hạng thương hiệu.
- Không thêm phần lịch sử dài nếu không giúp người đọc chọn mua.

## CTA presentation override

The "Vi sao nen mua ... tai The Gioi Di Dong?" section must use one main section heading, a short lead, and checklist bullets. Do not create a smaller heading for each benefit. Follow `references/cta-rules.md`.

## Ba section dễ trùng nhau - phân vai bắt buộc

Ba section nói về sản phẩm, mỗi section một nhiệm vụ riêng, không lẫn sang
nhau, vì lẫn vai là nguyên nhân chính khiến bài đọc như lặp lại:

| Section | Nhiệm vụ | Được nêu | Không được nêu |
| --- | --- | --- | --- |
| Các loại ... phổ biến | Phân loại sản phẩm theo tiêu chí | Kiểu/nhóm sản phẩm, đặc điểm từng kiểu | Tên thương hiệu, model, giá |
| Các thương hiệu ... phổ biến | Bối cảnh thương hiệu thị trường | Tên thương hiệu, định vị chung của hãng | Model, giá, tồn hàng |
| Các sản phẩm ... nổi bật tại TGDĐ | Lựa chọn cụ thể đang bán | Tên sản phẩm, thông số, giá | Xếp hạng hãng, nhận định hãng nào tốt hơn |

- Nếu một câu vừa nói kiểu sản phẩm vừa nói tên hãng, tách ra và đặt vào đúng
  section của nó.
- Câu nêu phạm vi TGDĐ đang kinh doanh thương hiệu nào chỉ xuất hiện 1 lần,
  ở section sản phẩm nổi bật, không rải khắp bài.
- Không tạo thêm section thứ tư lặp lại cùng nhóm sản phẩm.
