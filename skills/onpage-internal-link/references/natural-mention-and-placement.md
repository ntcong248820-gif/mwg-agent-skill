# Chọn đoạn neo theo chủ đề + viết câu mention tự nhiên

Tài liệu này chốt cách chọn **vị trí chèn** và cách viết **câu chèn** cho Mode B
(`Thêm vào dưới đoạn văn`).

## Vấn đề đang sửa

Cách làm cũ mặc định lấy đoạn kết bài (`Hy vọng…`, `Trên đây…`, `Cảm ơn bạn…`), nên:

- 100% link rơi xuống cuối bài — Google thấy một pattern lặp, người đọc thấy một
  cục quảng cáo dán ở đáy.
- Câu chèn buộc phải viết kiểu chào mời (`bạn có thể tham khảo…`) vì đoạn kết bài
  không còn chủ đề gì để nối tiếp.

Chuẩn mới: **đoạn neo phải là đoạn đang nói về đúng khía cạnh mà trang đích có liên hệ**,
và **vị trí phải rải đều** trong batch.

## 1. Chấm điểm đoạn neo

Sau khi lọc `<p>` hợp lệ (bỏ caption, bỏ đoạn dưới 80 ký tự, bỏ dòng mồi), chấm điểm:

| Điểm | Loại đoạn |
| ---: | --- |
| 100 | Đoạn nói trực tiếp về **khía cạnh** mà máy mới có liên hệ, và có nêu chi tiết cụ thể (thông số, cách hoạt động, so sánh) |
| 70 | Đoạn nói về khía cạnh đó nhưng chung chung |
| 40 | Đoạn nói về khía cạnh khác nhưng vẫn thuộc thân bài, còn nối được |
| 10 | Đoạn kết bài / lời chào / câu trả lời FAQ chốt hạ |

**Khía cạnh** lấy từ chính bài và từ trang đích: màn hình & kích thước, pin & sạc,
camera, chip & hiệu năng, thiết kế & chất liệu & màu, kết nối (5G/Wi-Fi/cổng sạc),
bộ nhớ, bảo mật (Face ID / Touch ID), hệ điều hành & tính năng phần mềm.

Nhận diện đoạn kết bài bằng mở đầu: `Hy vọng`, `Hi vọng`, `Trên đây`, `Như vậy`,
`Tóm lại`, `Vừa rồi`, `Bài viết trên`, `Cảm ơn`, `Chúc bạn`.

## 2. Quota vùng vị trí

Chia danh sách `<p>` hợp lệ của mỗi bài thành 3 vùng theo chỉ số:

| Vùng | Khoảng vị trí |
| --- | --- |
| Đầu | 0 – 35% |
| Giữa | 35 – 70% |
| Cuối | 70 – 100% |

Ràng buộc trên **cả batch**, không phải từng bài:

- Vùng cuối **≤ 40%** số dòng.
- Vùng đầu **≥ 20%** số dòng.
- Vùng giữa **≥ 25%** số dòng.

Thuật toán: sort ứng viên theo điểm giảm dần, duyệt và gán; nếu vùng của ứng viên
đã đầy quota thì lấy ứng viên điểm cao nhất kế tiếp thuộc vùng còn thiếu. Chỉ khi
một bài không còn ứng viên nào ở vùng thiếu mới được phá quota — và phải ghi rõ
trong report.

## 3. Khuôn câu tự nhiên

Câu chèn là **câu tiếp theo của đoạn neo**. Đọc liền mạch thì phải thấy trôi.

| Quan hệ | Khuôn | Ví dụ |
| --- | --- | --- |
| Còn giữ | `… vẫn được giữ trên {anchor}` | "Cổng USB-C này vẫn được giữ trên iPhone 18, nên bộ cáp cũ dùng tiếp được." |
| Nâng cấp | `Sang {anchor}, {khía cạnh} được nâng lên …` | "Sang iPhone 18, tấm nền này được nâng lên chuẩn ProMotion 120Hz có Always-On." |
| Thông số đổi | `Ở {anchor}, con số này là …` | "Ở iPhone Duo, con số này thay đổi vì máy dùng hai tấm nền gập lại." |
| Thao tác giống | `Thao tác tương tự cũng áp dụng cho {anchor}.` | "Thao tác chụp màn hình tương tự cũng áp dụng cho iPhone 18." |
| So thế hệ | `So với đời này, {anchor} khác ở chỗ …` | "So với đời này, iPhone Duo khác ở chỗ mở ra là một màn hình liền." |
| Kế thừa thiết kế | `{anchor} đi theo hướng …` | "iPhone Duo đi theo hướng khác: gập lại gọn, mở ra là màn lớn." |

Một khuôn **không dùng quá 30%** số dòng trong batch.

## 4. Cấm

Các mẫu này rời ngữ cảnh, đọc ra ngay là chèn máy móc:

- `Nếu bạn muốn mua…`, `Nếu đang tìm máy mới…`
- `bạn có thể tham khảo thêm…`, `bạn có thể xem thêm…`
- `là lựa chọn đáng cân nhắc`, `là hướng đáng xem`
- `ghé ngay Thế Giới Di Động`, `đừng quên theo dõi`
- Câu mở đầu bằng `Nếu` chiếm quá 25% batch.

Cũng cấm: giá cụ thể, ngày bán, thông số chưa xác minh từ trang hãng.

## 5. Ví dụ đạt / không đạt

### Không đạt

> **Đoạn neo:** "Hy vọng bài viết đã gửi đến bạn những hình nền iPhone 15 đẹp chất lượng và làm bạn hài lòng. Hẹn gặp lại ở bài viết tiếp theo nhé!"
> **Câu chèn:** "Nếu muốn ngắm hình nền 4K trên khung hình rộng hơn, iPhone Duo mở ra là có ngay không gian hiển thị lớn."

Hỏng ở hai chỗ: neo vào lời chào cuối bài (điểm 10), và câu chèn là lời mời mua.

### Đạt

> **Đoạn neo (giữa bài, nói về độ phân giải):** "Hình nền 4K có độ phân giải 3840 x 2160, khi đặt lên màn hình OLED của iPhone 15 Pro Max sẽ giữ được chi tiết ở vùng tối mà không bị vỡ hạt."
> **Câu chèn:** "Cùng tấm hình đó, iPhone Duo trải trên màn gập cỡ lớn nên vùng hiển thị rộng hơn đáng kể."

Neo vào đoạn đang nói đúng chuyện độ phân giải – màn hình, câu chèn nối tiếp ý đó.

### Đạt

> **Đoạn neo (đầu bài, nói về chuẩn sạc):** "iPhone 16 Pro Max hỗ trợ sạc nhanh qua USB-C lên đến 30W và MagSafe 25W. Việc sạc nhanh hơn giúp giảm thời gian máy ở trạng thái nhiệt độ cao."
> **Câu chèn:** "Cả hai chuẩn sạc này vẫn được giữ trên iPhone 18, nên củ sạc và đế MagSafe đang dùng không phải thay."

## 6. Checklist trước khi ghi sheet

- [ ] Mỗi đoạn neo khớp đúng 1 thẻ `<p>` trong thân bài.
- [ ] Điểm chủ đề trung bình ≥ 60.
- [ ] Vùng cuối ≤ 40%, vùng đầu ≥ 20%, vùng giữa ≥ 25%.
- [ ] Không khuôn câu nào vượt 30%.
- [ ] Không câu nào chứa mẫu cấm ở mục 4.
- [ ] Anchor đúng 1 lần/câu, không câu trùng, dài 45–140 ký tự.
