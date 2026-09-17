# Quy tắc trình bày

Mục tiêu của mọi rule dưới đây: **người đọc lướt trên điện thoại không gặp bức
tường chữ nào.** Bài PR bị bỏ giữa chừng gần như luôn vì đoạn văn quá dài, không
phải vì nội dung dở.

## Cấu trúc bài

```text
title (H1)
sapo (in đậm, 2-3 câu)
H2 — section 1
  2-4 đoạn
  [ảnh + caption]
H2 — section 2
  2-4 đoạn
  [ảnh + caption]
H2 — section 3
  2-4 đoạn
đoạn chốt
```

- **3-4 section H2** cho bài 800-1000 chữ. Nhiều hơn thì mỗi phần bị cụt.
- **Không dùng H3** trừ khi một section thật sự có nhánh con. Bài PR hiếm khi cần.
- Mỗi section **2-4 đoạn**. Section chỉ có 1 đoạn thì gộp vào section bên cạnh.

## Đoạn văn — rule cứng

| Ràng buộc | Số |
| --- | --- |
| Số câu mỗi đoạn | **tối đa 4** |
| Số chữ mỗi đoạn | **tối đa 90** |
| Số câu lý tưởng | 2-3 |

`scripts/check-article.py` chặn cứng hai ngưỡng trên. Đoạn vượt ngưỡng thì tách,
đừng rút gọn bằng cách bỏ chi tiết — chi tiết là thứ làm bài đáng đọc.

Kỹ thuật tách: một đoạn = một ý. Thấy chữ "và", "nhưng", "tuy nhiên" nối hai ý
khác nhau thì đó là chỗ xuống dòng.

## Heading

- Heading là **câu có thông tin**, không phải nhãn.
  - Nhạt: "Về màn hình", "Ưu điểm", "Kết luận"
  - Được: "Thứ không nhạt đi là màn hình", "Một khoản tôi tiêu hơi phí"
- Dài 5-12 chữ.
- **Không chèn link vào heading.** Không ngoại lệ.
- Heading tiếp nối mạch kể, đọc riêng dãy heading phải ra được cốt truyện.

## Không dùng bullet và bảng

Bài PR báo ngoài là **bài kể chuyện**, không phải bài tư vấn mua hàng.

- Không dùng checklist gạch đầu dòng.
- Không dùng bảng so sánh.
- Không dùng nhãn in đậm đầu đoạn để giả làm danh sách.

Có nhiều ý song song thì viết thành các đoạn liền mạch có từ nối ("Thứ hai là...",
"Ngược lại...", "Còn một thứ nữa..."). Đó là cách các bài trên VnExpress và Thanh
Niên làm, và là lý do bài đọc như bài báo chứ không như slide.

## Vị trí ảnh

- Ảnh đặt **giữa các cụm nội dung**, sau đoạn mà nó minh hoạ.
- **Không đặt ảnh ngay dưới title** và không đặt ảnh ở cuối bài.
- Hai ảnh không nằm sát nhau; giữa chúng phải có ít nhất 2 đoạn.
- Mỗi ảnh có caption riêng. Chi tiết ở `image-rules.md`.

## Đoạn chốt

1-2 đoạn cuối, không có heading riêng.

- Quay lại câu chuyện mở đầu để khép vòng.
- Nêu điều rút ra, viết như lời khuyên thật của người kể.
- **Không kết bằng lời kêu gọi mua hàng.** Bài báo ngoài không kết bằng CTA;
  thông tin mua hàng nếu có thì nằm tự nhiên trong đoạn áp chót.

Sai:

> Hãy đến ngay Thế Giới Di Động để sở hữu chiếc laptop ưng ý với giá tốt nhất!

Nên:

> Tổng kết lại sau ba tuần, tôi tiếc duy nhất một điều là đã chần chừ quá lâu.
