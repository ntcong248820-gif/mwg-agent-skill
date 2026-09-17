# Quy tắc hình ảnh

## Số lượng và kích thước

- **Tối thiểu 2 ảnh.** Bài 800-1000 chữ thường vừa với 2-3 ảnh.
- **Kích thước chuẩn 2048x1150** (tỷ lệ 16:9). `prepare-images.py` tự scale to
  cover rồi crop giữa, nên ảnh gốc tỷ lệ khác vẫn ra đúng khung.
- Ảnh gốc nên **rộng tối thiểu 1600px**. Ảnh nhỏ hơn bị phóng lên sẽ vỡ, và khi
  đó phải đổi ảnh chứ đừng giao ảnh mờ.

## Nguồn ảnh

**Mặc định:** lấy ảnh tự do trên mạng, miễn hợp chủ đề và đủ độ phân giải.

**Khi user chỉ định nguồn:** chỉ được lấy từ đúng nguồn đó.

> Ví dụ: bài iPhone 18, user nói chỉ lấy ảnh trên trang Apple → mọi ảnh phải có
> `source_url` thuộc `apple.com`. Không lấy ảnh từ chỗ khác rồi báo là đã lấy
> đúng nguồn.

Ràng buộc này là ràng buộc bản quyền và ràng buộc với bên báo, không phải sở
thích. Không tìm được ảnh đạt yêu cầu trong nguồn đã chỉ định thì **báo user**,
đừng tự nới nguồn.

Không lấy ảnh có watermark của trang khác, không lấy ảnh chụp màn hình bài viết
của đối thủ, không lấy ảnh có logo cửa hàng khác.

## Caption

**Mọi ảnh bắt buộc có caption.** Script chặn nếu thiếu.

Caption tốt nói **ý nghĩa của thứ trong ảnh với người đọc**, không mô tả lại
thứ ai cũng nhìn thấy.

| Đừng | Nên |
| --- | --- |
| "Hình ảnh chiếc laptop" | "Màn hình lớn giúp giảm thao tác chuyển cửa sổ khi làm việc" |
| "Bàn phím của máy" | "Bàn phím hành trình sâu tạo khác biệt rõ khi gõ nhiều" |
| "Sản phẩm tại cửa hàng" | "Gõ thử vài phút tại cửa hàng cho biết nhiều hơn đọc thông số" |

Ràng buộc:

- Dài **8-20 chữ**, một câu, không có dấu chấm cuối.
- **Không chèn link vào caption.**
- Không nhồi tên thương hiệu vào caption.
- Caption không lặp lại nguyên văn câu trong đoạn văn ngay trên nó.

## Đặt tên file

`prepare-images.py` tự sinh tên kebab-case từ caption nếu không khai. Muốn tự
đặt thì dùng `filename` (không kèm đuôi):

```json
{
  "type": "image",
  "source_url": "https://.../anh-goc.jpg",
  "caption": "Màn hình lớn giúp giảm thao tác chuyển cửa sổ khi làm việc",
  "filename": "01-man-hinh-lon"
}
```

Đặt tiền tố số thứ tự để file trong Drive xếp đúng thứ tự xuất hiện trong bài.

## Quyền truy cập

`prepare-images.py` mở quyền `anyone/reader` cho từng ảnh. Đây là **bắt buộc kỹ
thuật**, không phải lựa chọn: Docs API đi tải ảnh theo URL lúc chèn, nên ảnh
chưa public thì Doc dựng ra sẽ thiếu ảnh.

URL công khai dùng dạng `https://drive.google.com/uc?export=view&id=<ID>`.
Không dùng `lh3.googleusercontent.com/d/<ID>` — host đó trả bản đã bị thu nhỏ
(đo được 208 KB so với 429 KB của cùng một file).

Ảnh public nghĩa là ai có link đều xem được. Đừng đưa vào bài PR ảnh chứa thông
tin nội bộ, ảnh màn hình có dữ liệu khách hàng, hay ảnh chưa được phép công bố.

## Ảnh có sẵn ở máy

Dùng `source_path` thay cho `source_url`:

```json
{"type": "image", "source_path": "/đường/dẫn/anh.jpg", "caption": "..."}
```
