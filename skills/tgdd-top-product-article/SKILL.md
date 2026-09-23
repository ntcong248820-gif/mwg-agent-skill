---
name: tgdd-top-product-article
description: >
  Viết mới hoặc renew bài "Top N sản phẩm" TGDĐ/ĐMX: research SP còn kinh doanh,
  dựng source HTML chuẩn CMS, chèn shortcode, đặt ảnh, validate bằng script.
user-invocable: true
when_to_use: >
  Trigger khi user muốn viết bài dạng top/danh sách sản phẩm ("top 10 laptop gaming
  dưới 25 triệu", "top điện thoại pin khỏe", "top đồng hồ Garmin..."), hoặc renew /
  cập nhật một bài top cũ (đổi sản phẩm ngừng kinh doanh, cập nhật giá, bổ sung
  shortcode, sửa trình bày ảnh).
category: content-ops
keywords: [top-list, hoi-dap, shortcode, product-promotion, sosanh, product-id, item_web_status, ngung-kinh-doanh, renew, laptop, dien-thoai, cms, tgdd]
metadata:
  version: "1.0.0"
---

# tgdd-top-product-article

Pipeline viết/renew bài top sản phẩm TGDĐ. Rule trong skill này rút ra từ một bài
top thực tế (5 vòng sửa, 4 sản phẩm ngừng kinh doanh giữa dự án, 2 lỗi trình bày
do CMS render). Đọc `references/lessons-learned.md` trước khi bỏ qua bất kỳ rule
nào.

Dùng chung với skill `content-html-optimizer` (build ảnh/link vào `final-content.html`).

## Scope

- Có làm: research sản phẩm, dựng `source-content.html`, chèn shortcode, đặt ảnh +
  alt/title, chèn internal link, validate, viết report task.
- Không làm: upload ảnh lên CMS, publish bài, ghi vào Google Sheet. Chỉ đọc Sheet.
- Sheet/CMS là **read-only** trừ khi user xin write rõ ràng.
- Không gọi API tốn tiền (Ahrefs, DataForSEO, Gemini API). Cần thì trả
  `BLOCKED / COST_GATE`.

## 2 Mode

| Mode | Khi nào | Bước |
| --- | --- | --- |
| **Viết mới** | Chưa có bài | 1 → 8 |
| **Renew** | Đã có bài trên CMS / có workspace | 0 → 8 (bỏ bước viết nội dung mới cho SP giữ lại) |

## Bước 0 — Renew: chốt hiện trạng trước

1. Xác định workspace nội dung của bài (thư mục lưu `source/source-content.html`
   riêng cho bài này). Nếu chưa có, tạo và paste source từ CMS vào đó.
2. Trích toàn bộ `[product ID="..."]` trong bài.
3. Check trạng thái kinh doanh của **tất cả** ID (bước 2). Bài top cũ luôn có
   SP đã chết.
4. Chạy `validate_article.py` để biết bài thiếu shortcode/ảnh/format gì.
5. Chỉ thay phần cần thay. Không viết lại bài đang chuẩn.

## Bước 1 — Chốt điều kiện top

Rút từ title: **số lượng N**, **ngành hàng**, **điều kiện** (giá `<25 triệu`,
tính năng `pin khỏe`, công nghệ `RTX`, đối tượng `sinh viên`...).

Chốt luôn:
- URL category grid nguồn (vd `https://www.thegioididong.com/laptop?g=laptop-gaming`)
- `categoryid` + `properties` cho `[sosanh]` → lấy từ Google Sheet của riêng bạn
  (ID qua biến môi trường `SHEET_SHORTCODE_MAU_ID`), sheet "Shortcode mẫu (copy
  dùng luôn)", chọn dòng có cột B khớp ngành hàng.

## Bước 2 — Research + verify sản phẩm bằng SCRIPT (không mở browser)

Mở trang bằng browser rất tốn token. Trang sản phẩm TGDĐ đã có tín hiệu tĩnh
trong `<script>`: `item_web_status` và `pageStatus`.

```bash
python3 scripts/check_product_status.py \
  --grid "https://www.thegioididong.com/laptop?g=laptop-gaming" --json
```

```bash
python3 scripts/check_product_status.py \
  https://www.thegioididong.com/laptop/acer-aspire-5-a515-58gm-i5-nxkw1sv002 334998
```

Script trả 3 trạng thái:

| Status | Nghĩa | Xử lý |
| --- | --- | --- |
| `LIVE` | `item_web_status: "Còn hàng"` | Dùng được |
| `DISCONTINUED` | `pageStatus: 'Không kinh doanh'` hoặc `item_web_status: "Ngừng kinh doanh"` | Loại, tìm SP thay |
| `AMBIGUOUS` | `item_web_status` rỗng | **Phải** mở browser 1 lần, tìm chữ "SẢN PHẨM NGỪNG KINH DOANH" |

Không tin: JSON-LD `availability` (luôn `InStock` kể cả SP chết), sự hiện diện
trong category grid (grid có cache lag, chỉ trả page 1 ~20 SP).

Script cũng trả `product_id` (từ `item_id`, không cần mở browser), `name`, `brand`,
`banner_slides` + `product_images` để lấy ảnh, và giá:
`price` = datalayer `price:` (giá bán thật) — nếu datalayer trả `0.0` thì fallback
JSON-LD (**giá GỐC**, output đánh dấu `~`). Giá bán chuẩn nhất lấy từ `--grid`
(`price_sale`). `viewed-product-price` chỉ là CSS, không phải markup — đừng dùng.

**Thiếu SP so với N trong title → tự nới điều kiện cho đủ số**, theo thứ tự ưu
tiên ở `references/product-research.md`. Không bao giờ giao bài "Top 10" mà chỉ
có 8 SP, cũng không đổi số trong title.

Chi tiết grid parsing, chọn ảnh banner, thứ tự nới điều kiện:
`references/product-research.md`.

## Bước 3 — Dựng cấu trúc bài

Đúng thứ tự này, không đảo:

```
[Product_Promotion] (đầu bài, listid = đúng SP trong bài, đúng thứ tự)
<h2> mở bài
[info] ngày cập nhật [/info]
<h3>1. Tiêu chí chọn ...</h3>  + bảng 2 cột
[info] Xem thêm [/info]
<h3>2. Bảng tổng hợp TOP N ...</h3> + bảng so sánh
[sosanh products="..." properties="..." categoryid="..."]   <- NGAY dưới </table>
<h3>3. Đánh giá TOP N ...</h3>
   N khối <h4> sản phẩm
<h3>4. Chính sách bảo hành ...</h3>
<h3>5. Câu hỏi liên quan</h3>
[Product_Promotion] (cuối bài, listid = SP ngành hàng giảm sốc, KHÔNG trùng bài)
[info] Xem thêm [/info]
đoạn kết (bọc <em>)
```

Thứ tự cuối bài là **shortcode → box info → câu kết**, không phải ngược lại —
xem lesson #17 ở `references/lessons-learned.md`.

Mỗi khối sản phẩm — thứ tự bắt buộc: widget → specs → nội dung, ảnh chen giữa:

```html
<h4><strong>Tên SP đầy đủ (mã)</strong></h4>
<p>[product ID="334998" Description="none" Display="block"]</p>
<p>[info]</p>
<p><strong>Thông số kỹ thuật</strong>:</p>
<ul>...</ul>
<p>[/info]</p>
<p><a href="..." rel="noopener" target="_blank"><strong>Tên SP</strong></a> là ...</p>
<p><img alt="Tên SP" src="https://cdnv2.tgdd.vn/..." title="Tên SP + mệnh đề liên quan đoạn văn quanh ảnh" width="800" /></p>
<p>Đoạn nội dung tiếp ...</p>
<p>Phù hợp cho: ...</p>
```

Template đầy đủ + rule shortcode chi tiết: `references/article-structure.md`.

## Bước 4 — Rule shortcode (vi phạm là bài hỏng)

- `[Product_Promotion]` **đúng 2 cái**. Đầu bài: `listid` = danh sách ID trong
  bài, **cùng thứ tự** body, title chứa "ĐỪNG BỎ LỠ danh sách TOP ... đáng mua
  trong bài:". Cuối bài: `listid` = SP ngành hàng giảm sốc, **không trùng 1 ID
  nào** với trong bài, title "ĐỪNG BỎ LỠ các mẫu ... GIẢM SỐC:".
- `[sosanh]`: tối đa **7** `properties` (cái thứ 8 không render);
  `categoryid` rỗng **hoặc** `products` rỗng → mất cả bảng; SP ngừng kinh doanh
  bị âm thầm bỏ dòng → verify lại sau khi đổi SP.
- `[product ID]`: 1 cái / 1 khối `<h4>`.

## Bước 5 — Ảnh

- **Không tạo `<p class="titleOfImages">`.** CMS render `<img title>` thành
  caption → thêm paragraph caption là hiện caption **2 lần** trên web.
- Mỗi `<img>` bắt buộc: `alt` + `title` + `width="800"`, tiếng Việt có dấu, không
  mở đầu bằng "Hình ảnh...", "Minh họa...".
- **`alt` và `title` không được giống nhau.** CMS render `title` thành caption
  hiển thị dưới ảnh; `alt` không hiển thị. Hai trường có công thức riêng:
  - `alt` = **đúng tên sản phẩm**, không thêm gì. Ví dụ:
    `alt="Máy in Phun màu đa năng Canon G3010 Wifi"`.
  - `title` = **tên sản phẩm + mệnh đề liên quan tới nội dung bao quanh ảnh**.
    Mở đầu bằng chính tên sản phẩm đó, rồi nối sang điểm mạnh / con số / đối
    tượng dùng đang được nói ở đoạn ngay trên hoặc dưới ảnh. Ví dụ:
    `title="Máy in Phun màu đa năng Canon G3010 Wifi có tốc độ in nhanh và tiết
    kiệm chi phí, phù hợp với văn phòng nhỏ"`.
  Cấm `title` là mệnh đề trống chủ ngữ ("Bình mực kéo chi phí xuống thấp") —
  người đọc phải biết caption đang nói về máy nào.
  Cấm tả bố cục/tư thế chụp: "nhìn thẳng", "nhìn nghiêng", "đặt trên bàn",
  "cạnh chồng giấy", "kiểu dáng...". Người đọc nhìn thấy ảnh rồi — caption tả
  lại ảnh là dòng chữ thừa.
- **Không đặt link trong `<table>`.** Bảng so sánh và bảng tiêu chí chỉ chứa
  chữ; link sản phẩm/danh mục nằm ở đoạn văn chi tiết bên dưới. Để link ở cả
  hai chỗ là đi link 2 lần cùng một URL trong một bài.
- Ảnh đặt **sau `[/info]` và sau đoạn nội dung đầu tiên**, không đặt ngay sau
  `[product ID]`.
- Resize: `magick <in> -resize 800x -quality 85 -strip <out>`.
- Ảnh mới chưa upload CMS thì không render → **liệt kê tên file cho user upload**.

## Bước 5b — Điền 2 box "Xem thêm"

Bài top có 2 box `[info]` Xem thêm (sau mục 1, và sau `[Product_Promotion]` cuối
bài). Cả hai phải có 2-3 link bài thật. Tra bằng script của `content-html-optimizer`,
không bịa URL:

```bash
python3 <path-to>/content-html-optimizer/scripts/suggest_related_articles.py \
  --workspace <workspace-của-bài-này> \
  --terms "{3-5 cụm chủ đề, cách nhau bằng dấu phẩy}" --he-bai "Top sản phẩm"
```

Script tra sheet BÀI TIN (`SHEET_BAI_TIN_ID`, ~6.800 bài đang air), tự loại URL đã
có trong bài và loại chính bài đang viết, in ra bảng xếp hạng + HTML sẵn. **Chỉ
giữ 2-3 dòng thật sự liên quan** — điểm cao chỉ là khớp nhiều chữ, không phải
đáng đọc tiếp. Chi tiết cách chọn: `references/article-structure.md` mục "Box
Xem thêm".

## Bước 6 — Optimize + chèn link

```bash
python3 <path-to>/content-html-optimizer/scripts/optimize_content.py \
  --workspace <workspace-của-bài-này> --fetch-links
```

Optimizer build `final-content.html` **TỪ** `source-content.html` mỗi lần chạy →
sửa ở `final` sẽ bị ghi đè. Sửa ở `source` trước.

Sau mỗi lần chạy, kiểm 5 thứ nó hay làm sai:
1. Tự thêm lại `<p class="titleOfImages">` → xóa.
2. Gán sai ảnh cho SP khi `metadata/image-metadata.csv` thiếu entry → điền CSV
   cho mọi ảnh mới, rồi verify từng khối.
3. Chèn link lệch ngữ cảnh (vd "máy chơi game" → `/may-choi-game-cam-tay` trong
   bài laptop) → xóa link và xóa entry trong `metadata/inserted-links-report.json`.
4. **Thiếu link hãng/dòng SP cho 1+ sản phẩm trong bài** — optimizer chỉ chèn
   link khi từ khóa khớp đúng trong `CUSTOM_LINK_OVERRIDES`
   (`content-html-optimizer/scripts/optimize_content.py`), danh sách này không
   phủ hết mọi dòng SP. Verify thủ công theo `references/article-structure.md`
   mục "Link hãng + dòng sản phẩm" — mỗi hãng/dòng xuất hiện trong bài phải có
   đúng 1 link, không tự bịa URL khi chưa xác nhận được.
5. **Link hãng neo sai chỗ + anchor box "Xem thêm" bị cắt** (lesson #20, #21):
   - Đọc `inserted-links-report.json`, xem từng anchor hãng nằm ở câu nào. Link
     hãng phải neo ở chỗ nói về hãng ("laptop Acer", "của HP"), **không** neo
     vào tên công nghệ ("công nghệ Acer ComfyView", "Acer Purified Voice").
     Script đã chặn tự động, nhưng vẫn đọc lại vì đây là lỗi chuỗi-khớp-nhưng-
     sai-vật, validator không bắt được.
   - Hãng mất link vì trong bài chỉ có tên công nghệ/tên dòng → viết thêm một
     câu nhắc hãng tự nhiên trong `source-content.html` rồi optimize lại, đừng
     chèn tay vào cụm tên công nghệ.
   - Box "Xem thêm": mỗi `<li>` phải có anchor = **full tiêu đề** bài đích +
     `title` bằng tiêu đề đó. Script tự nới (log `[XEM THÊM]`); đọc log xem có
     `[WARN]` dạng inline cần sửa tay không.

## Bước 7 — Validate (bắt buộc, trước khi báo xong)

```bash
python3 scripts/validate_article.py --workspace <workspace-của-bài-này>
```

Thêm `--check-cdn` để HEAD từng ảnh, phát hiện ảnh chưa có trên CDN.

21 check: shortcode, thứ tự listid, overlap listid, `[sosanh]` properties/vị trí,
số ảnh = số SP, caption lặp, alt/title/width, vị trí ảnh trong khối, heading
H2 không bold / H3-H6 bọc `<strong>`, link `target="_blank"` + `noopener`, parity
source ↔ final.

**FAIL > 0 → chưa xong.** Không báo hoàn thành khi còn FAIL.

## Bước 8 — Task + report

Ghi report vào task/workspace tracking của bạn: SP dùng + ID, SP đã loại và lý
do, ảnh cần upload CMS, output validator, unresolved questions cuối.

## Bẫy đã gặp

Đọc `references/lessons-learned.md` — caption lặp, ảnh sai chỗ, SP chết giữa dự
án, workspace nội dung bị gitignore (không có git backup), sự cố `decompose()`
xóa mất 10 ảnh.
