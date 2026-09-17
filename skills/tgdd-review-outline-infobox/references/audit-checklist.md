# Checklist audit outline Infobox

Rà đủ 6 nhóm. Với mỗi lỗi tìm được, ghi lại: lỗi là gì, bằng chứng cụ thể (tên heading, tên sản phẩm, câu văn), và hệ quả.

## Nhóm A - Cấu trúc và heading

- [ ] **Heading giả**: một cụm nội dung lớn hoặc các lợi ích/tiêu chí con (ví dụ trong mục "Tại sao nên mua / sử dụng...") được đánh dấu bằng chữ in đậm (`**...**` / `<p><strong>...</strong></p>`) thay vì thẻ heading H4 (`<h4>...</h4>`). Hệ quả nặng: các mục con của nó bị TOC gán nhầm vào section phía trên, làm mất cụm semantic và khiến công cụ tạo ảnh AI (`image-ai-generate`) bỏ qua không tạo ảnh riêng cho từng mục con. BẮT BUỘC phải chuyển thành H4.
- [ ] **Sai cấp**: sapo phải H2, section chính H3, mục con và câu hỏi FAQ H4, không dùng H1.
- [ ] **Nhảy cấp**: H3 xuống thẳng H5, hoặc mục con đứng ngang hàng section cha.
- [ ] **Mục con lạc chỗ**: đọc TOC như người dùng và hỏi "mục này có thật sự thuộc section cha không". Ví dụ các tiêu chí chọn mua bị nằm dưới bảng giá.
- [ ] **Hai section liền nhau trùng ý định**: phần giới thiệu hãng và bảng sản phẩm/giá đặt cạnh nhau là trường hợp phổ biến nhất — nên gộp thành một.
- [ ] **Section một mục con**: một H3 chỉ có duy nhất một H4 thì không cần tách cấp.
- [ ] **Heading không chứa hoặc chứa quá dày từ khóa**: heading nên đọc như câu hỏi người dùng thật sự gõ.

## Nhóm B - Phạm vi sản phẩm

Đối chiếu với danh sách sản phẩm hợp lệ đã lập ở Bước 2.

- [ ] **Sản phẩm ngoài danh mục** xuất hiện trong bảng giá, ví dụ, ảnh minh họa hoặc FAQ. Gồm cả model đã bị gỡ khỏi danh mục sau khi bài được đăng.
- [ ] **Hãng có bán nhưng không được nhắc**. Ưu tiên cảnh báo nếu hãng bị bỏ sót lại đang có sản phẩm bán chạy nhất danh mục.
- [ ] **Hãng được nhắc nhưng không có sản phẩm nào trong danh mục**. Lỗi này rất hay gặp ở đối thủ, và cũng là lỗ hổng dễ khai thác nhất.
- [ ] **Sản phẩm có trong bảng nhưng không có mô tả ở phần hãng**, hoặc ngược lại.
- [ ] **Bảng giá lệch** so với giá đang hiển thị ở danh mục. Không sa đà vào audit giá — chỉ nêu như một rủi ro bảo trì và gợi ý cách giảm rủi ro (bỏ cột giá, hoặc ghi khoảng giá thay vì con số chính xác).

## Nhóm C - Độ phủ intent

Đối chiếu với outline chuẩn của loại trang tương ứng. Với Type 3 (ngành hàng + thuộc tính) và Type 1, các cụm dưới đây gần như luôn cần có; thiếu cụm nào thì ghi rõ cụm đó đang thuộc về đối thủ:

- [ ] Định nghĩa "… là gì" — nền tảng thực thể và cơ hội featured snippet.
- [ ] Phân loại các biến thể — ăn được các truy vấn dài.
- [ ] Công dụng / lợi ích / Tại sao nên mua / sử dụng — thường là intent lớn nhất của ngành hàng ("có tốt không", "có tác dụng gì"). Cần 8-12 ý, mỗi ý theo mạch cơ chế → tác động → điều kiện. **BẮT BUỘC mỗi ý con phải là H4 riêng (`<h4>...</h4>`)**, không dùng nhãn in đậm giả heading (vừa vi phạm lỗi heading giả, vừa làm mất ảnh AI minh họa).
- [ ] Đặc điểm / thông số nổi bật — phải là các trục ra quyết định thật, không phải liệt kê tính năng cho đủ.
- [ ] Chọn theo nhu cầu hoặc theo nhóm người dùng — dạng bảng thì tốt.
- [ ] Tiêu chí chọn mua — 4-8 tiêu chí, có ngưỡng hoặc cách kiểm tra khi có cơ sở.
- [ ] Đặc điểm nổi bật của các hãng trong danh mục.
- [ ] Sai lầm thường gặp — dạng checklist, không tách mỗi lỗi thành một heading ngắn.
- [ ] Lưu ý sử dụng / an toàn / ai không nên dùng — bắt buộc với ngành hàng sức khỏe, và thường là chỗ khác biệt lớn nhất vì đối thủ hay bỏ.
- [ ] CTA mua tại TGDĐ/ĐMX.
- [ ] FAQ 5-10 câu — kiểm tra cả hai bên; nếu cả hai cùng thiếu thì đây là khoảng trống chiếm được rẻ nhất.

## Nhóm D - Chất lượng nội dung

- [ ] **Section mỏng**: một section chỉ có 2-3 câu hoặc 3 mục con sơ sài trong khi đối thủ khai thác sâu.
- [ ] **Claim tuyệt đối** cho thứ chỉ đúng với vài model. Sửa bằng "thường", "nhiều mẫu", "tùy model".
- [ ] **Claim y tế / hiệu quả không có cơ sở**. Với ngành hàng sức khỏe, mọi thứ vượt quá mức "hỗ trợ" đều là rủi ro. Nếu đối thủ mắc lỗi này, ghi vào phần khai thác được.
- [ ] **Suy rộng thông số** của một sản phẩm thành đặc điểm của cả hãng hoặc cả danh mục.
- [ ] **Văn sáo, lặp ý**, câu chuyển vô nghĩa.
- [ ] **Lạc chủ đề**: nhét sản phẩm thuộc ngành hàng khác vào để tăng độ dài.
- [ ] **Kể lại quá trình research** hoặc mô tả cách website hiển thị dữ liệu thay vì viết cho người mua.

## Nhóm E - CTA

- [ ] Có đúng một section heading, lead ngắn, checklist bullet, không tách heading nhỏ cho từng lợi ích.
- [ ] Có nhắc: hàng chính hãng và bảo hành, hỗ trợ trả chậm 0%, thanh toán linh hoạt, giao nhanh toàn quốc, hệ thống gần 3.000 siêu thị.
- [ ] Ưu đãi riêng của một số sản phẩm (1 đổi 1, quà tặng kèm) phải ghi đúng phạm vi, ví dụ "một số sản phẩm".
- [ ] Thời hạn bảo hành khác nhau giữa các nhóm sản phẩm thì không gộp thành một con số.
- [ ] Giọng kêu gọi mua hàng, không phải lời cảnh báo hay hướng dẫn kiểm tra website.
- [ ] Không có đoạn dài về ngày, khu vực, tồn kho hay việc khuyến mãi có thể thay đổi.

## Nhóm F - Rủi ro bảo trì

- [ ] Bảng giá con số chính xác trong ngành hàng đổi giá liên tục.
- [ ] Nhắc số lượng sản phẩm, số model cụ thể — sẽ sai sau vài tháng.
- [ ] Ảnh minh họa gắn với model dễ bị gỡ.
- [ ] Nội dung gắn với chương trình khuyến mãi có thời hạn.

## Mức đánh giá

Chấm mỗi nhóm theo ba mức, dùng trong bảng tổng ở đầu báo cáo:

- **Đạt** — không có vấn đề đáng sửa.
- **Cần sửa** — có nội dung nhưng sai cấu trúc, thiếu chiều sâu hoặc sai phạm vi.
- **Thiếu** — không có gì cả.
