# Checklist trước khi giao bài

Rà từng mục và **tự sửa**, không chỉ liệt kê lỗi ra rồi giao.

## Chạy máy trước

```bash
python3 scripts/check-article.py {article.json}
```

Hết `ERROR` mới đi tiếp. Những mục dưới đây là thứ script **không** bắt được.

## Độ dài và cấu trúc

- [ ] Thân bài trong khoảng 800-1000 chữ (hoặc đúng số brief yêu cầu).
- [ ] Có đúng 1 title, 1 sapo.
- [ ] Có 3-4 section H2, mỗi section 2-4 đoạn.
- [ ] Không đoạn nào quá 4 câu hoặc quá 90 chữ.
- [ ] Không dùng bullet, không dùng bảng.

## Title và sapo

- [ ] Tít hứa điều gì thì thân bài trả đúng điều đó.
- [ ] Tít có ít nhất một danh từ cụ thể, không phải tít cảm xúc rỗng.
- [ ] Tít không chứa tên thương hiệu.
- [ ] Sapo 2-3 câu, không lặp lại tít bằng từ khác.
- [ ] Không có link trong title và sapo.

## Giọng văn

- [ ] Tuyệt đối KHÔNG xưng "tôi" trong title, sapo hay thân bài; không biến bài viết thành nhật ký review cá nhân.
- [ ] Trọng tâm bài viết xoay quanh sản phẩm, tính năng, hiệu năng và giá trị thực tế cho người dùng.
- [ ] Giọng reviewer am hiểu công nghệ, tâm sự thân mật, tinh tế và khách quan.
- [ ] Có chi tiết trải nghiệm thực tế (cảm giác cầm nắm, nhiệt độ, độ sáng ngoài nắng, pin cả ngày).
- [ ] Có ít nhất một điểm đánh đổi hoặc chi tiết cần lưu ý để tạo độ tin cậy.
- [ ] Có một câu chốt rút ra được cho người mua.
- [ ] Không câu nào đọc như thông cáo báo chí khô khan.
- [ ] Không dùng "tốt nhất", "số 1", "hoàn hảo", "vượt trội" thiếu căn cứ.
- [ ] Không câu nào nhắc nơi lấy tin ("theo trang chủ hãng", "theo một số nguồn").
- [ ] Thuật ngữ khó chỉ giải thích một lần.
- [ ] Mỗi đoạn văn xuôi tối đa một dấu `:`.

## Thương hiệu

- [ ] "Thế Giới Di Động" xuất hiện tối đa 3-4 lần.
- [ ] Không xuất hiện trong title, sapo và caption.
- [ ] Lần nhắc đầu rơi vào nửa sau bài.
- [ ] Bài không kết bằng lời kêu gọi mua hàng.

## Link

- [ ] Chỉ chèn đúng những link user yêu cầu, không tự thêm.
- [ ] Mọi link nằm trong đoạn văn; không có link ở title, sapo, heading, caption.
- [ ] Tối đa 3 link về site MWG.
- [ ] Một URL chỉ chèn một lần.
- [ ] Anchor 3-8 chữ, nằm sẵn trong câu, không phải câu nặn ra để nhét link.
- [ ] Anchor nói đúng thứ trang đích có.
- [ ] Đã mở thử từng URL, còn sống.

## Ảnh

- [ ] Tối thiểu 2 ảnh, mỗi ảnh đúng 2048x1150.
- [ ] Nếu user chỉ định nguồn ảnh, **mọi** ảnh đều lấy từ đúng nguồn đó.
- [ ] Ảnh gốc đủ nét, không bị phóng lên vỡ.
- [ ] Không ảnh nào có watermark của bên khác.
- [ ] Mỗi ảnh có caption 8-20 chữ, nói ý nghĩa chứ không mô tả lại ảnh.
- [ ] Caption không lặp câu trong đoạn ngay trên nó.
- [ ] Ảnh đặt giữa bài, không nằm ngay dưới title, không nằm cuối bài.
- [ ] Hai ảnh cách nhau ít nhất 2 đoạn.

## Gate verify

- [ ] Gate đã chạy **sau** phiên bản cuối cùng của bài.
- [ ] Đã mở evidence file ra đọc, không chỉ nhìn exit code.
- [ ] Không còn claim nào `SAI`.
- [ ] Mọi claim `KHÔNG TRA ĐƯỢC` đã bị **bỏ khỏi bài**, không viết mờ đi.
- [ ] Bài có sửa sau gate thì đã chạy lại gate.

## Giao hàng

- [ ] Thư mục con nằm đúng trong thư mục cha user đưa.
- [ ] Thư mục chứa đủ Doc và toàn bộ file ảnh.
- [ ] Đã **đọc lại Doc** bằng `docs.documents.get`, không chỉ tin output script.
- [ ] `inlineObjects` bằng đúng số ảnh trong bài.
- [ ] Có đúng 1 HEADING_1; các section là HEADING_2.
- [ ] Link trong Doc neo đúng cụm từ và trỏ đúng URL.
- [ ] Caption nằm ngay dưới ảnh, `NORMAL_TEXT/CENTER`.
- [ ] Doc đã mở quyền `anyone` → **writer**; thư mục `anyone` → reader. Kiểm bằng
      `gws drive permissions list`, không tin output script.
- [ ] Trong thư mục giao hàng không có file nào ngoài Doc và ảnh của bài.

## Bàn giao cho user

Đưa đủ:

- [ ] Link thư mục Drive.
- [ ] Link Google Doc.
- [ ] Số chữ thật của thân bài.
- [ ] Kết quả gate verify và đường dẫn evidence file.
- [ ] Những chỗ đã bỏ vì không verify được, nếu có.
- [ ] Câu hỏi còn treo, nếu có.
