# Quy tắc chèn link

## Rule cứng

**Link chỉ nằm trong đoạn văn (`type: "p"`).**

Tuyệt đối không chèn link vào:

- title
- sapo
- heading (H2/H3)
- caption ảnh

`scripts/check-article.py` chặn cứng cái này. Lý do nó là rule chứ không phải
lời khuyên: link trong heading làm hỏng mục lục bên báo, và link trong sapo là
dấu hiệu rõ nhất để biên tập viên nhận ra bài quảng cáo.

## Chỉ chèn link user yêu cầu

Không tự thêm link. Không "tiện tay" gắn thêm một link danh mục vì thấy hợp.

User đưa link nào thì chèn đúng link đó. User không đưa link nào thì bài không
có link, và đó là kết quả đúng.

## Số lượng

| Loại bài | Tối đa link về site MWG |
| --- | --- |
| Báo ngoài (mặc định) | **3** |

Vượt ngưỡng là lộ bài quảng cáo và bên báo sẽ cắt bớt — cắt cái nào thì mình
không chọn được. Thà tự chọn 3 link đúng chỗ.

Đổi ngưỡng bằng `max_brand_links` trong `article.json` khi brief cho phép.

**Một URL chỉ chèn một lần.** Cùng một URL xuất hiện hai chỗ là lãng phí và
trông như spam.

## Anchor text

- Anchor là **một cụm từ có nghĩa nằm sẵn trong câu**, không phải chữ chèn thêm.
- Dài **3-8 chữ**.
- Anchor phải nói đúng thứ trang đích có. Anchor "laptop văn phòng" mà trỏ về
  trang laptop gaming là sai, dù cả hai đều là trang laptop.
- Không dùng anchor rỗng: "tại đây", "xem thêm", "nhấn vào đây", "link này".
- **Không in đậm anchor.** Doc đã tô màu và gạch chân link rồi.

Sai — câu được nặn ra chỉ để có chỗ nhét link:

> Bạn có thể tham khảo [danh mục laptop tại Thế Giới Di Động] để biết thêm chi tiết.

Nên — anchor nằm trong câu vốn đã tồn tại:

> Hãy [ra cửa hàng gõ thử vài phút] và nhìn màn hình trong ánh sáng thật, vì đó
> là hai thứ bạn chạm vào mỗi ngày.

## Vị trí trong bài

- Rải đều, **không dồn hết xuống cuối bài**.
- Link đầu tiên không nên nằm ở đoạn đầu tiên. Để người đọc vào mạch đã.
- Một đoạn tối đa một link.

## Cách khai trong article.json

```json
{
  "type": "p",
  "text": "Hãy ra cửa hàng gõ thử vài phút và nhìn màn hình trong ánh sáng thật.",
  "links": [
    {"text": "ra cửa hàng gõ thử vài phút", "url": "https://www.thegioididong.com/laptop"}
  ]
}
```

`text` của link phải **khớp nguyên văn** một đoạn con trong `text` của block.
Lệch một ký tự là script dừng và báo `Anchor not found` — nó dừng có chủ đích,
vì đoán chỗ neo gần đúng sẽ đặt link sai chỗ mà không ai phát hiện.

## URL

- Dùng URL tuyệt đối, bắt đầu bằng `https://`.
- Kiểm URL còn sống trước khi giao. URL chết trong bài PR đã đăng thì sửa rất phiền.
- Không để URL trần trong thân bài. Mọi URL phải được bọc anchor.
