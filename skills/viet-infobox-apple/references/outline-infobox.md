# Outline infobox Hãng / Filter / Dòng filter (PIM)

User chốt 29/10/2026: outline = **3 nguồn**, Claude dựng, ghi rõ nguồn từng heading trong `outline.md`.
1. **CellphoneS** cùng trang (cột URL CellphoneS, trống thì tự tìm trang dòng/hãng tương ứng trên cellphones.com.vn): lấy các H2/H3/H4 bằng `nghien_cuu.py`.
2. **Infobox TGDĐ của dòng liền trước** (làm iPhone 19 thì xem `/dtdd-apple-iphone-18-series`, làm hãng thì xem trang hãng cùng ngành đã chuẩn): giữ khung mục, thứ tự, các mục đặc thù (thu cũ, review video, so sánh đời cũ).
3. **Keyword khách quan tâm**: kw GSC của URL (28 ngày, query có impression), kw phụ ở sheet, Google gợi ý/PAA (`goi_y.py`). Heading đặt theo đúng cụm kw tự nhiên, không ghép 2 kw cùng ý thành 2 heading.

Template là khung gợi ý (giống [outline linh hoạt]): heading theo SERP/GSC, cố định các mục **giá (đầu bài), Mua TGDĐ, Ưu đãi, FAQ**.

Trong `outline.md` mỗi heading kèm chú thích nguồn: `<!-- CPS | TGDĐ cũ | GSC "iphone 18 giá" 12.400 imp | PAA -->`.

## Khung Dòng filter / Filter (vd /dtdd-apple-iphone-18-series)

```
## Sapo (H2) 2 câu: định nghĩa dòng (ra mắt khi nào, gồm phiên bản nào) + bài tổng hợp gì
### 1. <Dòng> giá bao nhiêu tiền?            ← giá TGDĐ từng phiên bản, bảng, câu ngày cập nhật
#### 1.1. Bảng giá <model 1> mới nhất
#### 1.2. Bảng giá <model 2> mới nhất
#### 1.x. So sánh giá <dòng> với <dòng trước / dòng anh em>
#### 1.x. Bảng giá thu cũ lên đời <dòng>     ← chỉ khi TGDĐ đang có chương trình
### 2. Thông số cấu hình <dòng>              ← bảng thông số so model
### 3. <Dòng> ra mắt khi nào?                 ← chỉ khi kw có impression
### 4. <Dòng> có gì mới?                      ← H4 ĐẶC ĐIỂM NỔI BẬT (rule bên dưới), mỗi H4 1-2 đoạn + ảnh
### 5. <Dòng> có mấy dòng/phiên bản?          ← H4 từng model
### 6. <Dòng> có mấy màu?                      ← tên màu "Tiếng Việt (English)"
### 7. So sánh <model A> và <model B>          ← trong dòng
### 8+. So sánh <dòng> với <dòng trước/đời cũ> ← theo kw GSC/CPS có, mỗi cặp 1 H3, bảng + đoạn kết luận
### n. Mua <dòng> ở đâu chính hãng, uy tín, giá tốt?   ← 1-3 đoạn + box vàng Lý do nên mua
### n+1. Ưu đãi khi mua <dòng> tại Thế Giới Di Động     ← ul ưu đãi live, references/uu-dai-tgdd.md
### n+2. Review <dòng> chi tiết (có video)     ← chỉ khi có bài/video review TGDĐ (video review của TGDĐ, khác video Apple đầu bài)
### n+3. Câu hỏi thường gặp về <dòng>          ← 10-25 H4 câu hỏi KHÔNG đánh số, theo PAA/GSC
*Kết bài in nghiêng + hotline*
[Box Bài viết liên quan đến <dòng>]
```

## Khung Hãng (vd /dtdd-apple-iphone)

```
## Sapo (H2): câu định nghĩa thương hiệu/dòng sản phẩm (AIO) + bài giúp gì
### 1. <Hãng> giá bao nhiêu?                  ← bảng giá các dòng đang bán (giá thấp nhất mỗi dòng), câu ngày cập nhật
### 2. <Hãng> là gì? Lịch sử hình thành
### 3. Tại sao nhiều người thích dùng <hãng>?  ← H4 ĐẶC ĐIỂM NỔI BẬT (rule bên dưới)
### 4. Tổng hợp các dòng <hãng> từ trước đến nay   ← H4 từng dòng
### 5. So sánh <hãng> với <đối thủ / hệ điều hành khác>
### 6. Hướng dẫn chọn mua <hãng> phù hợp nhu cầu và ngân sách   ← H4 theo nhu cầu
### 7. Mua <hãng> ở đâu chính hãng, uy tín, giá tốt?   ← box vàng
### 8. Ưu đãi khi mua <hãng> tại Thế Giới Di Động
### 9. Cách kiểm tra <hãng> chính hãng trước khi mua     ← H4 không số
### 10. Một số câu hỏi thường gặp khi mua <hãng>         ← H4 không số
*Kết bài* + [Box Bài viết liên quan]
```

## H4 ĐẶC ĐIỂM NỔI BẬT (mục "có gì mới" / "tại sao nên dùng")

Viết đúng rule user chốt (feedback dac-diem-noi-bat-format):
- Mỗi H4 là **heading SEO rõ ý**, đọc là hiểu điểm mạnh, 8-15 từ.
- Xếp theo **độ nổi bật**: điểm mới/khác biệt lớn nhất lên đầu (thiết kế mới, chip, màn hình, camera, pin, kết nối, dung lượng...).
- **Gộp ý cùng loại** vào 1 heading (A19 và A19 Pro chung 1 dòng, camera trước và sau chung 1 dòng).
- **Không** "dấu hai chấm rồi giải thích", không câu dài kiểu đoạn văn.
- Tính từ tạo sức hút vừa phải, **không phóng đại** ("mạnh mẽ", "bền bỉ", "sáng, mượt" OK; "đỉnh cao", "vô đối", "hoàn hảo" không).
- Có thông số/tên công nghệ cụ thể khi có (Ceramic Shield 2, ProMotion 120Hz, Wi-Fi 7).
- Đánh số "4.1.", "4.2." theo H3 cha.

Ví dụ đạt:
```
#### 4.1. Thiết kế mới bền bỉ với Ceramic Shield 2
#### 4.2. Chip A19 và A19 Pro cho hiệu năng mạnh mẽ, tản nhiệt ổn định hơn
#### 4.3. Màn hình Super Retina XDR sáng, mượt với ProMotion 120Hz
#### 4.4. Camera trước và sau được nâng cấp toàn diện
#### 4.5. Kết nối thế hệ mới với Wi-Fi 7, Bluetooth 6 và chip N1
```
Ví dụ sai: `#### Chip: A19 Pro mạnh hơn 30%...`, `#### Hiệu năng` (danh từ trơn), `#### Màn hình đẹp nhất từ trước đến nay`.

**Khác bài sản phẩm**: trong infobox PIM, dưới mỗi H4 đặc điểm VẪN có 1-2 đoạn giải thích + ảnh (mẫu live iPhone 18 series). Chỉ khi user nói "viết Đặc điểm nổi bật" dạng list (key_features) mới bỏ đoạn.

## Quy tắc chung outline
- Có `outline_user.md` (user dán outline ở cột Ghi chú) → đó là khung chính, giữ heading/thứ tự; 3 nguồn ở trên chỉ để bổ sung và ghi nguồn.
- Bài TopZone: mục Mua viết "Mua <dòng> tại TopZone", ưu đãi "tại TopZone".
- Mục giá luôn H3 số 1 (sau sapo). Tất cả bảng giá gom về mục giá, các mục khác không lặp giá.
- FAQ: câu hỏi thật người dùng tìm (PAA, GSC query dạng câu hỏi), H4 không số, trả lời câu đầu trực tiếp, 2-4 câu. Có ít nhất 1 câu "mua ở đâu / trả góp / thu cũ" (rule nhắc brand AIO).
- KW phụ đồng nghĩa: kw phụ đầu tiên vào Meta, còn lại rải kết bài/FAQ, không heading riêng, không câu nhét gượng.
- Không đưa tin đồn/rò rỉ, kể cả ghi rõ là tin đồn. Ý chưa có nguồn thì bỏ, không viết "chưa công bố" (trừ kw dạng "có X không" → "không có X" + cách thay thế).
- Sản phẩm/màu/dung lượng chỉ bản bán ở Việt Nam (đối chiếu apple.com/vn).
- Gọi sản phẩm là "máy"/"sản phẩm", không "thiết bị".

- **Video/ảnh không đặt gần bảng (user chốt 30/10/2026, lên web rất xấu)**: không video hay ảnh nằm sát trên/dưới bảng, giữa chúng và bảng luôn có ít nhất 1 đoạn văn. Video đầu bài: viết 2 đoạn văn đầu H3 giá, đặt video GIỮA 2 đoạn đó, bảng giá đứng sau đoạn thứ 2. 
- **Video YouTube của Apple** (user chốt 29/10/2026): chèn 1 video chính thức của Apple (ưu tiên kênh Apple Vietnam, không có mới lấy Apple global, chốt 29/10/2026) liên quan sản phẩm ở ĐẦU BÀI, ngay sau đoạn đầu của heading đầu tiên. Tìm URL: trang apple.com/vn thường KHÔNG nhúng YouTube, nên mở trình duyệt vào youtube.com/@AppleVietnam/search?query=<tên sp> trước, không có mới sang youtube.com/@Apple/search?query=<tên sp>, đọc href video + ngày đăng (meta datePublished), ghi vào research.json.du_kien kèm nguồn; không có thì bỏ, không bịa ID. Viết `[VIDEO https://youtu.be/<id>]` trong bai.md.
