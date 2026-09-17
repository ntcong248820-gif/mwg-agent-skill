# Section Planning Rules & Định Mức Số Ảnh

Quy tắc quyết định số lượng và vị trí tạo ảnh mới trong một bài viết. Áp dụng chuẩn **Tạo mới 100% hình ảnh bằng AI** (không reuse ảnh cũ).

## 1. Công thức tính tổng số hình trong bài

Nguyên tắc: **Phủ trọn toàn bộ các section lá** của bài viết, ngoại trừ 4 nhóm bị loại trừ cứng (bao gồm Sapo).

$$\text{Tổng số ảnh} = \sum \text{H3 độc lập} + \sum \text{H4 lá còn lại}$$

- **H3 độc lập (không có H4 con):** Mỗi H3 độc lập làm đúng 1 ảnh (ví dụ: `Tổng quan về laptop Lenovo Legion`).
- **H3 có các H4 con (heading nhóm):** **Không** làm ảnh ở heading H3 cha, mà **phủ trọn toàn bộ các H4 lá con (mỗi H4 lá = 1 ảnh)**:
  - Ví dụ: Mục *Laptop Lenovo Legion có gì nổi bật?* có 6 H4 nhỏ → **làm đủ 6 ảnh**.
  - Mục *Tại sao nên sử dụng / mua...?* có 8 H4 nhỏ → **làm đủ 8 ảnh**.
  - Mục *Các dòng laptop Lenovo Legion và cách phân biệt* có 3 H4 nhỏ → **làm đủ 3 ảnh** (ngoại trừ phần bảng ở đầu heading nếu có).
  - Mục *Hướng dẫn chọn mua theo nhu cầu* có 4 H4 nhỏ → **làm đủ 4 ảnh**.

---

## 2. BẮT BUỘC LOẠI TRỪ CỨNG (Tuyệt đối KHÔNG làm ảnh cho 4 nhóm này)

| # | Nhóm loại trừ | Dấu hiệu nhận diện | Lý do loại trừ |
|---|---|---|---|
| 1 | **Sapo mở bài (H2)** | Đoạn Sapo mở đầu bài viết ngay sau tiêu đề chính H1 | Sapo không cần làm ảnh AI nữa, tập trung hình ảnh vào các mục phân tích cụ thể phía dưới |
| 2 | **Vì sao nên mua tại Thế Giới Di Động** | Section CTA/chính sách: "Vì sao nên mua tại Thế Giới Di Động", "Lý do nên mua tại TGDĐ", chính sách bảo hành, đổi trả, trả góp | Nội dung dịch vụ bán hàng/CTA, không cần ảnh minh họa sản phẩm |
| 3 | **Câu hỏi thường gặp (FAQ)** | "Câu hỏi thường gặp", "FAQ", danh sách các heading H4 dạng câu hỏi liên tiếp ở cuối bài | Khối text hỏi đáp ngắn, chèn ảnh gây loãng và ngắt mạch đọc |
| 4 | **Khối nội dung chứa bảng biểu (`<table>`)** | Bảng thông số chính, bảng giá, bảng tổng hợp 4 cột dòng máy/giá/cấu hình | **Đúng khối đã có bảng thì KHÔNG làm hình** — bảng đã trực quan hóa dữ liệu đó. Loại trừ này **không lan sang H4 anh em cùng H3**: H3 có bảng tổng hợp đầu section rồi xẻ thành H4 con thì mỗi H4 con vẫn làm 1 ảnh. Rule phủ H4 lá **thắng** rule loại trừ bảng. Chỉ bỏ hẳn ảnh khi H3 độc lập (không H4 con) và toàn bộ nội dung là bảng. |

---

## 3. KHÔNG được skip nhầm

Cụm từ giá trị chung trong heading **không** biến section thành loại bảng giá/khuyến mãi:

- Ví dụ: "mức giá hợp lý", "giá tốt", "đáng đồng tiền", "trong tầm giá vừa phải".
- Đây là tiểu mục tư vấn chọn mua phân khúc giá (ví dụ H4: *Chọn Lenovo Legion khi ngân sách vừa phải*), **vẫn phải làm ảnh bình thường**. Chỉ skip khi section đó **thực sự chứa thẻ `<table>`** hoặc là section chính sách/bảo hành.

## Output plan

Mỗi section giữ lại phải có đủ:

```
sectionIndex, heading, imageType, needsRealProductReference,
referenceProductId (nếu có), referenceMatchStatus, imageInputHighlights (2-4 ý),
visualBrief (1-2 câu tả cảnh cần vẽ)
```

`imageInputHighlights` rút từ **nội dung thật của section**, không bịa thông số.
