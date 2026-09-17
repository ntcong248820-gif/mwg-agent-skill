---
name: tgdd-review-outline-infobox
description: "Review, audit và so sánh outline Infobox của Thế Giới Di Động / Điện máy XANH với outline đối thủ (CellphoneS, Nguyễn Kim, FPT Shop, Điện Máy Chợ Lớn...) để tìm cách ontop. Dùng khi người dùng đưa outline hoặc URL danh mục và nói review outline, chấm outline, so sánh với đối thủ, outline mình thiếu gì, cần bổ sung gì để lên top, audit mục lục bài infobox hoặc vì sao đối thủ đang trên mình. Skill đối chiếu outline với danh sách sản phẩm thật trong URL danh mục, chấm theo 6 nhóm lỗi, chỉ ra điểm mạnh - điểm yếu của cả hai bên và trả về outline đề xuất đúng cấp heading CMS."
---

# Review outline Infobox TGDĐ / ĐMX

## Mục tiêu

Người dùng có một outline Infobox (đã đăng hoặc đang draft) và muốn biết: outline đang tốt/dở chỗ nào, đối thủ hơn ở đâu, cần sửa gì để vượt lên. Kết quả phải là một bản review có thứ tự ưu tiên và một outline thay thế dùng được ngay, không phải một danh sách nhận xét chung chung.

Điểm khác biệt của skill này so với việc "đọc outline rồi nhận xét": mọi kết luận đều được đối chiếu với **danh sách sản phẩm thật trong URL danh mục**. Phần lớn lỗi nặng nhất của Infobox (viết hãng không bán, thiếu hãng bán chạy, nhắc sản phẩm đã gỡ) chỉ lộ ra khi mở danh mục lên xem.

## Đầu vào

Bắt buộc:

- **Outline cần review** (dán text, ảnh mục lục, hoặc URL trang).
- **URL danh mục TGDĐ/ĐMX** của trang đó.

Nên có nhưng không bắt buộc:

- Outline hoặc URL của 1-3 đối thủ.
- Brief, từ khóa chính, mục tiêu thứ hạng.

Nếu thiếu URL danh mục, hỏi đúng một câu để lấy trước khi làm bất cứ việc gì khác. Không đoán sản phẩm từ trí nhớ. Nếu người dùng chỉ đưa outline đối thủ mà không đưa URL đối thủ, vẫn review được nhưng nói rõ là chỉ đánh giá được phần cấu trúc, không kiểm chứng được nội dung bên trong.

## Workflow

Làm tuần tự. Đọc reference đúng bước, không nạp hết cùng lúc.

### Bước 1 - Xác định loại trang

Loại trang quyết định outline chuẩn để so sánh:

| Loại | Dấu hiệu | Skill chuẩn tương ứng |
|---|---|---|
| Type 1 - Ngành hàng | Chủ thể chỉ là ngành hàng: Laptop, Tivi, Máy massage | `tgdd-infobox-nganh-hang` |
| Type 2 - Ngành hàng + Hãng | Có tên thương hiệu: Laptop Asus, Điện thoại Samsung | `tgdd-infobox-nganh-hang-hang` |
| Type 3 - Ngành hàng + Thuộc tính | Có tiêu chí/công dụng/vị trí/công nghệ: Laptop Gaming, Máy massage cổ vai gáy, TV OLED | `tgdd-infobox-nganh-hang-thuoc-tinh` |
| Type 4 - Dòng sản phẩm | Có hãng + dòng: Laptop Asus ROG, iPhone 16 Series | `tgdd-infobox-dong-san-pham` |

Nếu các skill này có mặt trong môi trường, đọc `references/outline.md` và `references/final-checklist.md` của skill tương ứng để lấy chuẩn đối chiếu. Nếu không có, dùng chuẩn rút gọn trong `references/audit-checklist.md` của skill này.

### Bước 2 - Lập danh sách sản phẩm hợp lệ

Mở URL danh mục và ghi lại cho từng sản phẩm: **tên đầy đủ, hãng, giá hiện tại, lượt bán/đánh giá nếu có, nhãn ưu đãi** (trả chậm 0%, chỉ bán online, mới ra mắt...). Ghi thêm danh sách hãng trong bộ lọc.

Bảng này là căn cứ cho gần một nửa số lỗi sẽ tìm được, nên đừng bỏ qua dù outline trông có vẻ ổn. Nếu danh mục dài, vẫn lấy đủ — số lượng sản phẩm cũng là dữ liệu (danh mục 8 sản phẩm và danh mục 60 sản phẩm cần cấu trúc bài khác nhau).

### Bước 3 - Đọc nội dung trang hiện tại, không chỉ outline

Outline chỉ cho thấy khung. Nhiều lỗi nặng nằm trong thân bài: heading giả tạo bằng chữ in đậm, sản phẩm ngoài danh mục nằm trong bảng giá, ảnh minh họa của model đã gỡ, claim y tế không có cơ sở. Nếu người dùng đưa URL, luôn fetch trang để đọc nội dung thật. Nếu chỉ có outline, nói rõ giới hạn này trong báo cáo.

### Bước 4 - Chấm outline của người dùng

Đọc `references/audit-checklist.md` và rà đủ 6 nhóm: cấu trúc heading, phạm vi sản phẩm, độ phủ intent, chất lượng nội dung, CTA, rủi ro bảo trì.

Với mỗi lỗi tìm được, ghi kèm **hệ quả cụ thể**, không chỉ tên lỗi. "Thiếu phần công dụng" là vô nghĩa; "Thiếu phần công dụng — đây là intent lớn nhất của ngành hàng, đối thủ dành 6 mục con cho nó và đang ăn toàn bộ traffic thông tin" mới hành động được.

### Bước 5 - Chấm outline đối thủ

Đọc `references/competitor-analysis.md`. Tìm hai thứ song song: cái đáng học và cái khai thác được. Đừng chỉ liệt kê đối thủ mạnh gì — phần có giá trị nhất thường là lỗ hổng của họ, vì đó là chỗ vượt lên rẻ nhất.

### Bước 6 - Viết báo cáo

Theo đúng template trong `references/output-format.md`.

### Bước 7 - Đề xuất outline mới

Outline thay thế phải: đúng cấp heading CMS (sapo H2, section H3, mục con và câu hỏi FAQ H4, không H1; các ý con trong mục "Tại sao nên mua / sử dụng..." BẮT BUỘC dùng H4 riêng, không dùng nhãn in đậm giả heading để đảm bảo chuẩn heading và luôn được phủ hình AI), chỉ nhắc hãng và sản phẩm có trong danh mục, không xếp hạng thương hiệu, không tạo internal link hay placeholder link, gộp các section trùng ý định.

Kèm chú thích ngắn cho những section mới thêm để người dùng hiểu vì sao thêm. Không cần chú thích cho section giữ nguyên.

## Quy tắc cứng

1. Không kết luận về sản phẩm hay thương hiệu nếu chưa mở URL danh mục.
2. Không đề xuất thêm sản phẩm ngoài danh mục vào bài, kể cả sản phẩm nổi tiếng.
3. Không xếp hạng thương hiệu và không đề xuất heading dạng "hãng nào tốt nhất".
4. Không tạo internal link, URL nội bộ hoặc placeholder chèn link trong outline đề xuất.
5. Không mặc định audit giá/tồn kho theo ngày và khu vực. Chỉ nêu chênh lệch giá khi nó chứng minh một rủi ro bảo trì cụ thể (ví dụ bảng giá trong bài lệch so với giá đang hiển thị).
6. Với ngành hàng sức khỏe, thực phẩm, mẹ và bé: mọi claim hiệu quả phải viết ở mức "hỗ trợ", và phải cảnh báo nếu outline của bất kỳ bên nào hứa điều trị bệnh.
7. Phân biệt rõ "lỗi" và "khác biệt phong cách". Chỉ gọi là lỗi khi có hệ quả với người đọc hoặc với công cụ tìm kiếm.
8. Nếu đề xuất đưa số liệu vào CTA (thời hạn bảo hành, số siêu thị, chính sách 1 đổi 1), đánh dấu rõ cái nào cần người dùng xác minh thay vì tự khẳng định.

## Kết thúc

Đóng báo cáo bằng một câu hỏi mở duy nhất: có triển khai luôn nội dung chi tiết theo outline đề xuất không. Không hỏi nhiều câu, không tóm tắt lại những gì vừa viết.
