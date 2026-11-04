# Box Đặc điểm nổi bật, bảng so sánh, FAQ (owner chốt 30/10/2026)

Ba thành phần owner yêu cầu cho bài SP mới. Mẫu live hiếm có (0/23 bài laptop có box hay bảng so sánh bản anh em, FAQ chỉ ở bài Apple và phần mềm), nên skill này đặt chuẩn riêng. Lint kiểm cấu trúc, còn chất lượng câu hỏi FAQ phải đọc tay theo phép thử bên dưới.

## 1. Box Đặc điểm nổi bật: bắt buộc, phần tử đầu tiên của bài

- Đứng **trước** đoạn mở bài (`<h3>` đầu tiên). Không dùng heading cho tiêu đề box (để mục lục không có thêm dòng), dùng `<p><strong>`.
- 4–5 gạch đầu dòng, mỗi dòng 1 điểm khác biệt của **đúng model** (chip, bộ nhớ, màn hình, thiết kế/pin...), có số. Không giá, không quà, không "nhất".
- Dùng chung nội dung với `key_features` (soạn 1 lần, dán 2 chỗ). Nếu trang web cũng hiển thị `key_features` ở khối riêng thì người đọc sẽ thấy 2 lần: kiểm trang live sau khi ghi và báo owner.
- Số hiệu năng hãng công bố trong box vẫn phải ghi là của hãng ("theo NVIDIA", "theo thông số công bố").

```html
<div style="border: 1px solid #d1d5db; border-radius: 8px; background: #f8fafc; padding: 12px 16px; margin-bottom: 16px;">
<p><strong>Đặc điểm nổi bật của {Tên SP ngắn}</strong></p>
<ul style="list-style: disc; padding-left: 25px;">
<li>...</li>
</ul>
</div>
```

## 2. Bảng so sánh: có điều kiện

**Khi nào làm:** SP thuộc một line-up có bản/model **tương đương** mà người mua dễ phân vân: cùng dòng khác cấu hình (016VN và 017VN), hoặc 2 model cùng thế hệ cùng phân khúc trong một dòng (vd Prestige N16 và một bản N17 nếu có). Không so với model khác chip/khác phân khúc/khác hãng (Prestige 14 Flip chip Intel không tương đương Prestige N16 RTX Spark).

**Điều kiện dữ liệu:** mọi ô có nguồn PIM hoặc trang hãng VN. Model so sánh nên đang bán ở TGDĐ để link được; không bán thì chỉ so khi owner đồng ý và không link.

**Cách làm:**
- Đặt trong mục `<h3>` riêng ("Chọn bản ... hay ...?" hoặc "So sánh ... và ..."), đoạn dẫn 1–2 câu trước bảng, đoạn gợi ý chọn theo nhu cầu sau bảng.
- Cột 1 là tiêu chí, cột 2 là SP của bài, các cột sau là model so sánh (tối đa 3). Tên model so sánh ở dòng đầu là link tới trang SP.
- Header mỗi cột SP ghi **tên đầy đủ** như trên trang SP, kể cả mã máy (vd `MSI Prestige N16 Flip AI+ C1XMT 016VN`). Không ghi "016VN (bản này)", "máy này" hay chỉ mã máy: người đọc lướt bảng phải biết ngay cột nào là máy nào. Lint báo ERROR khi header có "bản/máy/sản phẩm/mẫu này" hoặc ngắn dưới 3 từ.
- 5–10 dòng: các dòng **khác nhau** trước, rồi vài dòng giống nhau để người đọc thấy phần dùng chung. Không dòng giá.
- Style trực tiếp như mẫu live (bảng giá MacBook Air M5):

```html
<table style="border-collapse: collapse; font-family: arial,sans-serif; font-size: 15px; line-height: 1.4; width: 100%;">
<tbody>
<tr><th style="border: 1px solid #000; background: #efefef; padding: 6px 8px;">Tiêu chí</th><th style="...">{SP bài}</th><th style="...">{SP so sánh}</th></tr>
<tr><td style="border: 1px solid #000; padding: 6px 8px; font-weight: 600;">RAM</td><td style="border: 1px solid #000; padding: 6px 8px;">...</td>...</tr>
</tbody>
</table>
```

Thông số của model so sánh đưa vào `must_not` của facts kèm `allow_must_not_in` = tên heading mục so sánh, để lint vẫn bắt chép nhầm ở các mục khác.

## 3. FAQ cuối bài: bắt buộc, 2–4 câu có giá trị

- `<h3>Câu hỏi thường gặp về {Tên SP ngắn}</h3>` là `<h3>` cuối bài. Mỗi câu hỏi là `<h4>` kết thúc bằng "?", trả lời 2–4 câu trong `<p>`. `<h4>` chỉ dùng ở đây. Đoạn chốt có link (ngành hàng, hãng, dòng) đặt **trước** FAQ.
- Nguồn câu hỏi: Google gợi ý/PAA khi có (Google gợi ý miễn phí: `suggestqueries.google.com/complete/search?client=firefox&hl=vi&q=...`), cộng với các băn khoăn mua hàng theo loại máy. Không cần chờ có PAA mới viết FAQ.
- Nguồn câu trả lời, tra theo thứ tự (owner chốt 30/10/2026: đa số câu trả lời được từ thông số):
  1. **Bảng thông số trên trang SP TGDĐ** (JSON-LD `additionalProperty` của trang, hoặc tskt PIM). Nhiều câu "nâng cấp được không" trả lời ngay ở đây: dòng "Hỗ trợ RAM tối đa" bằng đúng RAM có sẵn nghĩa là không nâng được RAM.
  2. **Trang hãng VN**: tab Thông số (số khe M.2, bảo hành, sạc khuyến nghị, cổng), tab Tổng quan (phụ kiện, tính năng), mục FAQ của hãng. Trang hãng hay chặn bot (MSI chặn curl và trình duyệt headless): đọc bằng `ak-chrome-profile` mở tab rồi lấy `textContent` qua CDP, lấy cả nội dung đang thu gọn.
  3. Tài liệu chính hãng của bên thứ ba (Microsoft, NVIDIA) cho câu về nền tảng.
  - Chỉ ghi câu vào "câu hỏi chờ xác nhận" sau khi đã tra cả 1 và 2 mà không có.
  - **Không có chứng cứ chắc chắn thì bỏ câu hỏi** (owner chốt 30/10/2026). "Chắc chắn" nghĩa là có nguồn ghi thẳng câu trả lời. Gồm các trường hợp:
    - các nguồn lệch nhau;
    - phải suy luận mới ra;
    - phải đẩy người đọc đi "hỏi nhân viên" hoặc "liên hệ cửa hàng".
  - Câu bị bỏ ghi vào "câu hỏi chờ xác nhận" trong report kèm nguồn đã tra, không đưa vào bài, kể cả khi câu hỏi rất hay. Ví dụ bút MSI Nano Pen có kèm không: tab Thông số ghi "hỗ trợ", tab Tổng quan ghi "Tuỳ chọn", FAQ của MSI ghi "đi kèm", nên bỏ.
  - Câu được giữ thì từng câu trong phần trả lời cũng phải có nguồn. Cắt vế tự suy dù nghe hợp lý. Ví dụ:
    - "vì RAM gắn cố định" khi nguồn không ghi;
    - "sạc công suất thấp hơn thì chỉ lâu hơn" khi hãng không nói.
  - FAQ còn 2 câu chắc chắn vẫn tốt hơn 4 câu có 1 câu đoán. Còn dưới 2 câu thì báo owner, không độn câu hiển nhiên cho đủ số.
  - Lint báo ERROR khi phần FAQ có "hỏi nhân viên", "liên hệ cửa hàng", "chưa rõ", "chưa xác nhận"…
  - Câu trả lời dùng thông số đã nêu ở thân bài phải nói thêm điều thân bài chưa nói (vd khe M.2 duy nhất đã lắp SSD nên muốn tăng dung lượng phải thay ổ), không chép lại thông số.

**Phép thử giá trị (câu nào trượt 1 ý thì bỏ):**
1. Câu trả lời **không** đọc được ngay từ bảng thông số hay tiêu đề trang. Trượt: "Máy có màn hình bao nhiêu inch?", "Máy nặng bao nhiêu?", "Có mấy màu?".
2. Câu hỏi gắn với quyết định mua hoặc cách dùng thật: tương thích phần mềm/thiết bị, nâng cấp, sạc và phụ kiện, xuất màn hình ngoài, dùng cho công việc cụ thể, khác gì đời trước/bản anh em, bảo hành (khi chính sách đã xác nhận). Trượt: "Có nên mua không?", "Máy có tốt không?".
3. Có câu trả lời **chắc chắn, có nguồn ghi thẳng** (thông số trang SP TGDĐ/PIM, trang hãng VN, tài liệu chính hãng như Microsoft/NVIDIA). Nguồn lệch nhau hoặc phải suy luận thì trượt. Câu hỏi hay mà chưa có nguồn thì không đưa vào bài, ghi vào danh sách "câu hỏi chờ xác nhận" trong report cho owner/PIM.
4. Không trùng ý một heading thân bài (mục "Chọn bản nào" đã trả lời thì FAQ không hỏi lại).
5. Trả lời thẳng câu đầu (có/không/con số), rồi điều kiện hoặc lời khuyên. Không "theo ước tính", không con số tự suy.

Ví dụ trượt có thật trên bài live (MacBook Air M5): "có mấy tùy chọn màu sắc và kích thước màn hình?" (đọc được từ trang), "mạnh hơn M4 bao nhiêu phần trăm?" trả lời bằng "theo ước tính" (không nguồn).
