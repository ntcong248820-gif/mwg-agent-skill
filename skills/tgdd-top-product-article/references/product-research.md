# Research & verify sản phẩm cho bài top

## Nguyên tắc: script trước, browser sau

Mở trang sản phẩm bằng browser tốn rất nhiều token. Trang TGDĐ đã nhét trạng thái
kinh doanh vào `<script>` datalayer, curl là đủ.

```bash
S=<skill-dir>/scripts/check_product_status.py

# 1. Quét grid ngành hàng, lấy danh sách ứng viên
python3 $S --grid "https://www.thegioididong.com/laptop?g=laptop-gaming" --json

# 2. Check từng SP (URL đầy đủ, path, hoặc slug)
python3 $S https://www.thegioididong.com/laptop/acer-nitro-v-15-anv15-41-r2up 333430

# 3. Check hàng loạt từ file (1 URL/dòng)
python3 $S --file candidates.txt --json
```

Exit code 1 khi có SP `DISCONTINUED` hoặc `ERROR` → dùng được trong shell guard.

## Tín hiệu tĩnh — đã kiểm chứng thực tế

| Tín hiệu | Giá trị | Kết luận |
| --- | --- | --- |
| `pageStatus: 'Không kinh doanh'` | có | DISCONTINUED, chắc chắn |
| `item_web_status: "Ngừng kinh doanh"` | có | DISCONTINUED, chắc chắn |
| `item_web_status: "Còn hàng"` | có | LIVE, chắc chắn |
| `item_web_status: ""` | rỗng | **AMBIGUOUS** — quan sát được ở cả SP live (333430) và SP chết (339687) |

`viewed-product-price` **không dùng được**: chuỗi này chỉ xuất hiện trong CSS của
trang, không phải markup giá.

Tín hiệu **không dùng được**:
- JSON-LD `"availability"`: luôn `https://schema.org/InStock`, kể cả SP đã chết.
- Có mặt trong category grid: grid cache lag (1 SP đã chết vẫn xuất hiện 3 lần),
  và chỉ trả page 1 (~20 SP) → sai cả 2 chiều.

Chỉ escalate bucket AMBIGUOUS lên browser, tìm chuỗi "SẢN PHẨM NGỪNG KINH DOANH".
Với bài 10 SP thường chỉ 1-3 SP phải mở browser.

## Trường khác script trả về

| Field | Nguồn | Dùng để |
| --- | --- | --- |
| `product_id` | `item_id:` trong datalayer | điền `[product ID]`, `listid`, `products` — không cần mở browser |
| `price` | datalayer `price:` | giá bán thật. Nếu datalayer trả `0.0` → fallback JSON-LD = **giá GỐC**, output đánh dấu `~` |
| `price_list` | JSON-LD `"price"` | giá gốc, dùng để hiện "giá niêm yết" |
| `price_sale` (chỉ ở `--grid`) | `a[data-price]` trong grid | **nguồn giá bán đáng tin nhất** — dùng cho bảng tổng hợp và sort |
| `banner_slides` | path chứa `/Slider/` | ảnh marketing cho khối SP; nhiều SP không có |
| `product_images` | `Products/Images/{cate}/{id}/` (bỏ `-thumb-`) | fallback khi SP không có banner |

## Chọn ảnh cho khối sản phẩm

1. Ưu tiên banner marketing `Slider/vi-vn-{slug}-slider-N.jpg`.
2. Slide index 0 nhiều khi là banner brand/bảo hành chung hoặc `-thumbvideo.jpg`
   → **luôn mở ảnh xem trước khi lấy**, đừng chọn theo index 0 mù. File tên có
   `slider-1`, `slider-2`... thường mới đúng là banner SP thật.
3. SP không có `banner_slides` → lấy ảnh trong `product_images`, nhưng ảnh
   phải đáp ứng **cả 2 tiêu chí**, không chỉ 1:
   - **Không nền trắng thuần** (ảnh catalog trước/sau máy, kiểu chụp sản phẩm
     trên nền studio trắng). User đã phản hồi trực tiếp về việc này ("không
     lấy hình nền trắng nữa").
   - **Hiển thị toàn bộ sản phẩm** (nguyên chiếc laptop mở nắp, nhìn thấy cả
     màn hình + thân máy), không phải ảnh cắt cận một bộ phận. User đã phản
     hồi trực tiếp lần 2 về việc này: bài top sản phẩm cần ảnh thấy được toàn
     bộ máy để người đọc nhận diện, ảnh cận cảnh bàn phím/RGB dù không nền
     trắng vẫn **không đạt** — đây là lỗi đã lặp lại sau khi lesson #14 mới chỉ
     xử lý phần "nền trắng", chưa xử lý phần "toàn bộ sản phẩm". Xem lesson #15.
   - Tải và xem trực tiếp bằng Read tool nhiều index khác nhau trước khi chốt
     — không suy đoán ảnh nào đạt/không đạt chỉ từ tên file, và không dùng ảnh
     cận cảnh bàn phím/RGB làm phương án thay thế nữa.
   - Nếu **không có ảnh nào** của SP đó vừa không nền trắng vừa thấy toàn bộ
     máy, loại SP đó khỏi danh sách, không đưa vào bài dù cấu hình/giá phù hợp.
4. Resize `magick <in> -resize 800x -quality 85 -strip <out>`, đặt tên kebab-case
   theo model + mã SP.
5. Ảnh mới chưa upload CMS thì src 404 trên web → luôn báo tên file cho user upload.

## "Dưới N triệu" nghĩa là áp sát N, không phải bất kỳ giá nào dưới N

User đã phản hồi trực tiếp: bài "dưới 40 triệu" mà chọn SP rải từ 24-37 triệu là
sai nhu cầu thực tế — người tìm "laptop gaming dưới 40 triệu" thường đang nhắm
mức **gần 40 triệu** (vd trong khoảng 32-40tr), không phải "càng rẻ càng tốt".
Rule: khi ngành hàng có đủ SP LIVE, ưu tiên chọn dải giá áp sát ngưỡng trên của
title (khoảng 75-100% của N), thay vì trải đều từ giá thấp nhất có thể. Nếu
không đủ SP trong dải đó mới nới xuống thấp hơn theo thứ tự ở mục dưới.

Cách lấy đúng dải giá: URL 2 phía (`p=35-40-trieu`) **không** kết hợp đúng với
`g=` category filter, dễ trả nhầm sản phẩm ngoài ngành hàng. Dùng bucket 1 phía
`g={category}&p=tren-{floor}-trieu` (floor lấy từ các bucket filter thật scrape
được trong grid HTML, không đoán) để lấy superset, rồi tự lọc theo ngưỡng trên.

## Khi số SP đủ điều kiện < N trong title

**Tự nới điều kiện cho đủ số** (quyết định của user). Không đổi số trong title,
không giao bài thiếu SP. Thứ tự nới:

1. **Nới ngưỡng giá ~5-10%** trong biên vẫn đúng title (bài "dưới 25 triệu" thì
   lấy tới sát 25tr, kể cả SP 24.99tr; không vượt 25tr).
2. **Nới cấu hình/tính năng phụ** — hạ 1 bậc thành phần không phải trọng tâm
   (vd bài gaming: chấp nhận RAM 8GB nếu GPU vẫn đạt).
3. **Mở rộng thương hiệu** — bỏ ràng buộc "mỗi hãng tối đa 2 SP". Chấp nhận
   trùng hãng, nhưng ưu tiên đa dạng khi còn lựa chọn.
4. **Mở rộng biến thể cấu hình** cùng dòng (khác RAM/SSD, mã SP khác).
5. **Nới sang dòng cận kề** cùng nhu cầu (vd laptop gaming → laptop có GPU rời).

Bắt buộc: ghi rõ trong report đã nới điều kiện nào và SP nào là kết quả của việc
nới đó. Không nới im lặng.

Nếu nới hết 5 bậc vẫn không đủ N → báo user, đề xuất hạ N trong title. Đây là
trường hợp duy nhất được đổi title.

## Danh sách "giảm sốc" cho Product_Promotion cuối bài

- Lấy SP cùng ngành hàng đang giảm mạnh, **không trùng bất kỳ ID nào trong bài**
  (validator check overlap = 0).
- 6-10 ID. Verify LIVE bằng script như SP trong bài — SP chết bị bỏ dòng.
- Không cần cùng điều kiện top của bài (bài "dưới 25 triệu" vẫn được list SP 30tr
  giảm sốc).

## Renew: check lại toàn bộ trước khi sửa

Bài top sống 6-12 tháng thì gần như luôn có SP chết. Trong 1 dự án laptop 10 SP,
**4 SP ngừng kinh doanh giữa quá trình viết**. Vì vậy:

- Re-check toàn bộ ID ngay trước khi publish, không chỉ lúc research.
- Mỗi lần thay SP: cập nhật đồng thời bảng tổng hợp, khối H4, `listid` đầu bài,
  `products` của `[sosanh]`, và kiểm lại thứ tự giá.
