# Chọn vị trí chèn + viết câu mention tự nhiên (nhánh newContent)

Gộp rule cũ của skill (chấm điểm chủ đề, quota vùng, khuôn câu) với prompt node 9d + hậu kiểm 10d của n8n Onpage Ver 2.

Thứ tự ưu tiên khi các rule đá nhau: **không cắt mạch bài > đúng sự thật > đúng chủ đề > rải vị trí**.

## 1. Chọn vị trí

### 1.1 Đọc toàn bài trước

Dùng `article_marked` của script. Quy ước:
- `## ...` là tiêu đề mục.
- `[DANH SÁCH gạch đầu dòng]` + các dòng `- ...` là một danh sách.
- `[ẢNH minh hoạ]`, `[chú thích ảnh] ...`, `[bảng số liệu]` không phải văn xuôi.
- `⟦n⟧` ở cuối đoạn = được phép chèn **ngay dưới** đoạn đó. Đoạn không có `⟦n⟧` (sapo, caption, promo, đoạn có link ra ngoài,
  infobox) không được chọn, nhưng vẫn phải đọc để hiểu mạch.

### 1.2 Không cắt mạch bài (luật cứng)

Câu mới sẽ nằm giữa đoạn ⟦n⟧ và khối ngay dưới nó (`next_block` trong `candidates`). Bỏ ⟦n⟧ nếu:
- Khối dưới là danh sách/bảng mà đoạn đó dẫn vào — **kể cả khi đoạn kết thúc bằng dấu chấm** chứ không phải dấu hai chấm.
- Khối dưới là ảnh minh hoạ cho chính điều đoạn đó vừa nói.
- Hai khối là một cặp/chuỗi phải đọc liền: so sánh A với B, Bước 1 rồi Bước 2, ưu điểm rồi nhược điểm, câu hỏi rồi trả lời,
  nguyên nhân rồi cách xử lý, "nên chọn X nếu" rồi "nên chọn Y nếu".

Chỗ an toàn nhất: `section_end = true` (đoạn cuối một mục, ngay trên `##` mới). Không chắc → coi như cắt mạch, chọn chỗ khác.

### 1.3 Chấm điểm chủ đề

| Điểm | Loại đoạn |
| ---: | --- |
| 100 | Nói trực tiếp về **khía cạnh** mà trang đích liên quan, có chi tiết cụ thể (thông số, cách hoạt động, so sánh) |
| 70 | Nói về khía cạnh đó nhưng chung chung |
| 40 | Khía cạnh khác nhưng vẫn là thân bài, còn nối được |
| 10 | Kết bài / lời chào (`outro = true`) / câu trả lời FAQ chốt hạ |

Khía cạnh lấy từ chính bài và trang đích: màn hình, pin & sạc, camera, chip & hiệu năng, thiết kế/màu, kết nối, bộ nhớ,
bảo mật, phần mềm, công năng gia dụng (dung tích, ngăn, công suất…), thao tác trong app/game.

### 1.4 Vị trí trong bài và trong batch

- **Không bao giờ** chọn `last_paragraph`. Đoạn `outro` chỉ chọn khi không còn đoạn nào khớp chủ đề.
- Vùng (`zone`) theo vị trí ⟦n⟧ trong danh sách đoạn hợp lệ: đầu 0–35%, giữa 35–70%, cuối 70–100%.
- Quota trên **cả batch**: cuối ≤ 40%, đầu ≥ 20%, giữa ≥ 25%. Sort ứng viên theo điểm, vùng đầy thì lấy ứng viên điểm cao
  kế tiếp ở vùng còn thiếu. Phá quota chỉ khi bài không còn ứng viên an toàn ở vùng thiếu, và ghi rõ trong report.
- K = nguyên văn plain text của đoạn ⟦n⟧ (lấy từ `candidates[].text`).

## 2. Đánh giá độ liên quan sản phẩm ↔ bài (làm trước khi viết)

Hỏi: sản phẩm này có đúng là thứ người đọc **dùng trực tiếp** để làm việc bài đang nói không?

1. **Có và chắc chắn** → viết thẳng về việc dùng sản phẩm cho chính việc đó.
   Bài "Cách nhập code Blox Fruit" + iPhone 16: "Mời bạn tham khảo các mẫu iPhone 16 để chơi Blox Fruit, pin đủ cho những phiên cày dài."
2. **Không, hoặc không chắc** → không khẳng định sản phẩm làm được việc đó. Chuyển sang một nhu cầu khác **có thật** của người đọc bài này.
   Bài "Lỗi TikTok thường gặp" + MacBook Neo.
   SAI: "MacBook Neo giúp khắc phục lỗi TikTok hiệu quả hơn."
   ĐÚNG: "Nếu cần thêm một máy tính để dựng video cơ bản trước khi đăng TikTok, MacBook Neo có mức giá dễ tiếp cận trong các dòng MacBook."
3. **Không bịa khả năng** sản phẩm không chắc có. Hai thứ không liên quan công dụng (tra điểm thi + tủ lạnh) thì nối bằng bối cảnh người đọc, không bằng công dụng.
4. Sản phẩm không phải thiết bị thực hiện việc trong bài → **cấm** viết nó giúp việc đó dễ/nhanh/hiệu quả hơn
   ("Laptop giúp nhập code game mobile nhanh hơn", "Tai nghe giúp quay màn hình tiện hơn" đều sai).
5. Lợi ích phải **kiểm chứng được**: pin 5.000 mAh, màn 6,7 inch, 256GB, nặng 1,2 kg, ngăn mát 250 lít, sạc 45W.
   Không được: cấu hình ổn định, đáp ứng tốt nhu cầu, trải nghiệm tối ưu. Không chắc con số → mô tả cụ thể không số
   ("màn hình lớn hơn điện thoại", "cầm nhẹ tay", "giá mềm hơn các dòng còn lại").

## 3. Cách nối theo dạng bài (minh hoạ, không phải danh sách đủ)

| Dạng bài | Cách nối | Ví dụ |
| --- | --- | --- |
| Hướng dẫn / thủ thuật | Nối vào chính thao tác đang hướng dẫn | "Nếu hay quay màn hình để lưu thao tác, iPhone 16 256GB đủ chỗ cho những video dài." |
| Tư vấn chọn mua | Đặt sản phẩm vào đúng tiêu chí/tầm giá bài đang bàn | "Ở tầm giá thấp hơn, MacBook Neo vẫn đáp ứng các tiêu chí vừa nêu nếu bạn dựng video ở mức cơ bản." |
| Top / tổng hợp | Thêm như một cái tên đáng cân nhắc bên cạnh danh sách | "Ngoài các máy kể trên, iPhone 15 Plus cũng đáng cân nhắc nhờ viên pin lớn nhất dòng iPhone 15." |
| Giải thích khái niệm / hỏi đáp | Từ khái niệm vừa giải thích sang sản phẩm có đúng đặc điểm đó | "Nếu muốn một máy đạt chuẩn này, Samsung Galaxy S25 có kháng nước IP68." |
| Game / code / app | Sản phẩm dùng được → nối vào việc chơi; khác nền tảng → việc phụ trợ (xem video hướng dẫn, tra cứu, giải trí) | "Bên cạnh việc nhập code trên điện thoại, bạn có thể tham khảo MacBook Neo để xem video hướng dẫn đội hình trên màn hình lớn." |
| Cùng ngành, đời máy (bài iPhone cũ → máy mới) | Khuôn kế thừa ở mục 4 | "Cả hai chuẩn sạc này vẫn được giữ trên iPhone 18, nên củ sạc đang dùng không phải thay." |

Phép thử chung: bê nguyên câu sang bài khác mà vẫn dùng được → còn chung chung, viết lại cho bám bài này.

## 4. Khuôn câu

Câu chèn là **câu tiếp theo của đoạn neo**, đọc liền phải trôi.

| Quan hệ | Khuôn |
| --- | --- |
| Còn giữ | `… vẫn được giữ trên {anchor}` |
| Nâng cấp | `Sang {anchor}, {khía cạnh} được nâng lên …` |
| Thông số đổi | `Ở {anchor}, con số này là …` |
| Thao tác giống | `Thao tác tương tự cũng áp dụng cho {anchor}.` |
| So thế hệ | `So với đời này, {anchor} khác ở chỗ …` |
| Mở bằng chủ đề đoạn neo | `{nhận xét thật về việc trong đoạn}, {anchor} …` |
| Sản phẩm làm chủ ngữ | `{anchor} {đặc điểm thật}, phù hợp khi …` |
| Tình huống người đọc | `Khi {tình huống trong bài}, {anchor} …` |
| Nối tiếp việc bài đang làm | `Bên cạnh việc {việc trong bài}, …` |
| Mục đích cụ thể | `Để {mục đích}, bạn có thể chọn {anchor} với …` |
| Mời tham khảo gắn nhu cầu | `Mời bạn tham khảo {anchor} để {nhu cầu cụ thể trong bài}.` |

Ràng buộc batch:
- Một khuôn **≤ 30%** số dòng.
- Câu mở bằng `Nếu` / `Nếu bạn` **≤ 25%**; hạn chế mở bằng `Ngoài ra`, `Để có trải nghiệm`.
- Câu có `tham khảo` (kể cả "Mời bạn tham khảo", "bạn có thể tham khảo") **≤ 30%**, và chỉ dùng khi câu
  gắn với một nhu cầu/chi tiết cụ thể trong đoạn neo. "Bạn có thể tham khảo thêm {anchor}." trơ trọi là hỏng.

## 5. Yêu cầu câu chữ

- 1–2 câu, độ dài 45–220 ký tự (1 câu ≤ 140). Thà ngắn mà cụ thể còn hơn dài mà rỗng.
- Gắn với chi tiết **có thật** trong đoạn neo (tên sự vật, thao tác, tình huống).
- Có 1–2 tính từ mô tả **đặc điểm thật** của sản phẩm (mỏng nhẹ, pin lâu, màn hình lớn, dung lượng cao, giá dễ tiếp cận, ngăn đá rộng).
  Không xâu 3–4 tính từ liền nhau. Không lặp một tính từ 2 lần trong câu.
- Vế sau suy ra được từ vế trước; không ghép hai ý rời bằng dấu phẩy.
- Không "chúng"/"nó" chỉ sản phẩm. Không ngoặc vuông/kép, dấu sao, URL, "Xem thêm tại đây", "Link".
- Tên site chỉ nhắc khi tự nhiên, và chỉ nhắc đúng brand của URL đích (TopZone / Thế Giới Di Động / Điện máy XANH).
- Không giá cụ thể, ngày bán, thông số chưa xác minh từ trang hãng/trang sản phẩm.

## 6. Cụm cấm

Viết ra là hỏng câu:

đáp ứng tốt nhu cầu, nhu cầu đa dạng, nhu cầu cơ bản, nhu cầu hằng ngày, trải nghiệm hiệu quả, nâng cao trải nghiệm,
trải nghiệm tốt hơn, trải nghiệm tối ưu, thiết kế tinh tế, lựa chọn lý tưởng, là lựa chọn đáng cân nhắc, là hướng đáng xem,
phục vụ tốt, màn hình lớn rõ nét, mượt mà, mạnh mẽ, vượt trội, hoàn hảo, tuyệt vời, tuyệt đỉnh, đỉnh cao, tốt nhất, hàng đầu,
cỗ máy, chiến mọi game, cân mọi game, cấu hình tối ưu, cấu hình ổn định, tối ưu cho, trơn tru, hiệu quả hơn,
ghé ngay Thế Giới Di Động, đừng quên theo dõi, được phân phối bởi/tại …, được bán tại ….

## 7. Ví dụ đạt / không đạt

**Không đạt** — neo vào lời chào cuối bài, câu là lời mời mua:
> Đoạn neo: "Hy vọng bài viết đã gửi đến bạn những hình nền iPhone 15 đẹp… Hẹn gặp lại ở bài viết tiếp theo nhé!"
> Câu chèn: "Nếu muốn ngắm hình nền 4K trên khung hình rộng hơn, iPhone Duo mở ra là có ngay không gian hiển thị lớn."

**Không đạt** — cắt mạch: đoạn neo dẫn vào danh sách bước bên dưới.
> Đoạn neo: "Để nhập code, bạn làm theo các bước sau đây." → ngay dưới là `[DANH SÁCH]`.

**Không đạt** — khẳng định sai công dụng:
> "Ngoài việc chơi game, MacBook Neo là lựa chọn lý tưởng, màn hình lớn rõ nét, đáp ứng tốt nhu cầu đa dạng."

**Đạt** — giữa bài, đúng chủ đề độ phân giải:
> Đoạn neo: "Hình nền 4K có độ phân giải 3840 x 2160, đặt lên màn OLED của iPhone 15 Pro Max vẫn giữ chi tiết vùng tối."
> Câu chèn: "Cùng tấm hình đó, iPhone Duo trải trên màn gập cỡ lớn nên vùng hiển thị rộng hơn đáng kể."

**Đạt** — đầu bài, chuẩn sạc:
> Đoạn neo: "iPhone 16 Pro Max hỗ trợ sạc nhanh qua USB-C lên đến 30W và MagSafe 25W…"
> Câu chèn: "Cả hai chuẩn sạc này vẫn được giữ trên iPhone 18, nên củ sạc và đế MagSafe đang dùng không phải thay."

**Đạt** — khác nền tảng, chuyển sang nhu cầu phụ trợ, đoạn cuối một mục:
> "Bên cạnh việc nhập code trên điện thoại, bạn có thể tham khảo MacBook Neo để xem video hướng dẫn đội hình trên màn hình lớn."

## 8. Checklist trước khi ghi sheet

- [ ] Mỗi K khớp đúng 1 ⟦n⟧ trong `candidates`, không phải `last_paragraph`.
- [ ] Không ⟦n⟧ nào cắt mạch (đã đọc `next_block` + khối dưới trong `article_marked`).
- [ ] Đã qua bước đánh giá liên quan (mục 2), không câu nào khẳng định sai công dụng.
- [ ] Điểm chủ đề trung bình ≥ 60; quota vùng đạt hoặc đã ghi lý do.
- [ ] Không khuôn > 30%, `Nếu` ≤ 25%, `tham khảo` ≤ 30%.
- [ ] Không cụm cấm, không 2 câu trùng, mỗi keyword đúng 1 lần, viết hoa đúng quy ước.
