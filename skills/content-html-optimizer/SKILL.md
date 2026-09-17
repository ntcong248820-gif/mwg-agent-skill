---
name: content-html-optimizer
description: >
  Tối ưu HTML source content bài viết/infobox TGDĐ: di chuyển ảnh vào đúng
  section theo image-placement.json, dựng sẵn URL CDN theo tên file để xếp ảnh
  ngay sau khi gen mà KHÔNG phải chờ upload CMS, điền alt/title/caption từ image-metadata.csv,
  tự động fetch keyword & URL từ 2 Google Sheets MWG ('All KW' & 'BÀI TIN'),
  chèn Internal Link phủ rộng tối đa (1 link / 1 URL, target="_blank" rel="noopener noreferrer"),
  HỔ TRỢ chèn link ở <h2> và <p>, CẤM chèn link ở <h3>, <h4>, <h5>, <h6>, <table>, <img>,
  chống cắt chữ (không cắt lẻ thương hiệu như 'HP' trong 'HP Victus'), tên hãng trần chỉ link
  ở chỗ đang nói về hãng ('laptop Acer') chứ không link khi hãng là phần tên công nghệ
  ('Acer ComfyView'), box 'Xem thêm' anchor là TOÀN BỘ tiêu đề bài liên quan chứ không phải
  1 cụm cắt trong tiêu đề, chuẩn hóa khoảng trắng
  anchor text (không để dư khoảng trắng trong thẻ <a>), chuẩn hóa table HTML theo MWG standard
  mới (header đen #000000/chữ vàng #ffe14c, table-layout fixed, width % tự tính theo cột,
  cột giá tự nhận diện qua ₫/đ, cột giá ưu đãi bôi đỏ #d9381e), chuẩn hóa heading TGDD
  (H2 KHÔNG bold, H3/H4/H5/H6 BẮT BUỘC bọc <strong>), 2 ngoại lệ link trong table
  (brand comparison table + product listing table: link từng SKU về đúng trang
  sản phẩm lấy từ category listing/site search thegioididong.com, không dùng Sheet).
  Output vào source/final-content.html.
user-invocable: true
when_to_use: >
  Trigger khi user muốn xử lý/tối ưu toàn bộ HTML source content của một bài
  viết/infobox TGDĐ, bao gồm tự động đặt ảnh, chèn link nội bộ chuẩn ngữ cảnh
  (H2 & Paragraph), chống cắt chữ, gỡ space dư trong link và chuẩn hóa HTML.
category: content-ops
keywords: [html, infobox, table, heading, h2, h3, strong, alt, caption, image-placement, cdn-urls, du-doan-url-cdn, verify-cdn, internal-link, anchor-text, brand-link, xem-them, related-articles, final-content, gws]
metadata:
  author: mwg-ai-worker
  version: "3.3.0"
---

# content-html-optimizer

Pipeline tối ưu HTML source content chuẩn MWG/TGDĐ (layout ảnh, chuẩn hóa HTML, Heading TGDD & Internal Link phủ rộng).

## Scope

Chỉ xử lý file trong `content-workspaces/{topic-slug}/source/`.
Không upload CMS, không xử lý file ảnh vật lý (dùng `image-seo-pipeline`).

## Dữ liệu cấp workspace (KHÔNG nhét vào script)

Script dùng chung cho mọi bài. Mọi thứ chỉ đúng với **một bài** phải nằm trong
folder workspace của bài đó:

| File | Nội dung |
| --- | --- |
| `image-placement.json` | Ảnh nào đặt sau heading nào, block thứ mấy |
| `metadata/image-metadata.csv` | alt / title / caption từng ảnh |
| `cdn-urls.json` | URL CDN của từng ảnh — có thể **dựng trước khi upload**, xem mục dưới |

`cdn-urls.json` là object phẳng `{"ten-file.jpg": "https://cdnv2.tgdd.vn/..."}`:

```json
{
  "laptop-asus-choi-game.jpg": "https://cdnv2.tgdd.vn/mwg-static/tgdd/Common/09/61/0961beed7fad8d55d8a60be49c55dfbd.jpg"
}
```

Thứ tự script chọn `src` cho mỗi ảnh trong `image-placement.json`:

1. Key `cdn_url` ngay trong rule của `image-placement.json` (nếu có).
2. `cdn-urls.json` tra theo tên file.
3. `src` của chính ảnh đó trong `source-content.html`.
4. Ảnh thứ `idx` trong `source-content.html` (theo thứ tự xuất hiện).
5. URL dựng theo tên file + tiền tố CDN của workspace — **đường chính khi chưa
   upload**, không còn là chốt chặn cuối. Xem mục kế tiếp.

**Không thêm map URL vào `scripts/optimize_content.py`.** Khoá tra là tên file
ảnh, mà tên file ảnh trùng nhau giữa các bài là chuyện bình thường
(`laptop-asus-choi-game.jpg` có thể có ở nhiều bài Asus). Map nằm trong script
dùng chung thì bài B âm thầm nhận URL ảnh của bài A — ảnh vẫn hiện, không có
lỗi nào bắn ra, chỉ sai ảnh. Cùng lý do đó, đừng gán URL theo tên workspace
bằng `if/elif` trong script.

`cdn-urls.json` không bắt buộc: thiếu file thì script chỉ log `[WARN]` và dùng
`src` sẵn có trong `source-content.html`.

## Dựng URL CDN trước khi upload

Trước đây quy trình là: gen ảnh → upload CMS → chờ lấy URL → mới xếp ảnh vào bài.
Không cần chờ nữa. **Tên file thì CMS giữ nguyên**, nên URL suy được từ trước, và
bài xếp xong một lần là xong.

Hình dạng URL:

```
{tiền tố CDN của workspace}{tên-file}.jpg
https://cdnv2.tgdd.vn/mwg-static/common/News/0/may-in-phun-mau-kho-giay-ho-tro.jpg
```

### Phần tên file: đoán được

Kiểm chứng vòng tròn ngày 08/09/2026 trên bài `infobox-may-in-phun-mau`: ghi sẵn 24
URL vào bài **trước** khi upload, sau khi user upload thì cả 24 trả 200 với đúng file
của mình (EXIF `Thegioididong.com`, đúng `1200x675`). Không cái nào phải sửa.

**Bẫy `-845x475`:** hậu tố kích thước có thật, nhưng nó nằm ở **alt/title** mà CMS tự
điền, **không** nằm trong tên file. Biến thể `...-845x475.jpg` trả 404. Đừng "sửa" URL
bằng cách thêm hậu tố — làm vậy là giết cả bộ ảnh.

### Phần thư mục: phải chốt bằng phép đo, không đoán

`/News/{id}/` khác nhau theo bài, không suy được từ loại bài: đếm trên 30 workspace có
ảnh CDN thì 21 dùng `/News/0/`, 7 dùng id thật, 2 trộn cả hai. Cả bài infobox lẫn bài
hỏi đáp đều có mặt ở cả hai nhóm.

Thứ tự lấy tiền tố:

1. **Ảnh đã có sẵn trong `source-content.html` / `final-content.html` của chính
   workspace đó** — căn cứ tốt nhất, vì cùng một bài thì CMS bỏ ảnh vào cùng thư mục.
2. Bài hoàn toàn mới, chưa ảnh nào: dùng `/News/0/` rồi **bắt buộc** xác minh sau khi
   upload. Đây là mặc định theo số đông, không phải điều chắc chắn.

### Script kiểm

```bash
# TRƯỚC khi upload — mọi URL phải 404
python3 .claude/skills/content-html-optimizer/scripts/verify_cdn_urls.py \
  --workspace content-workspaces/{topic-slug} --expect free

# SAU khi upload — mọi URL phải 200, kèm ghi cdn-urls.json
python3 .claude/skills/content-html-optimizer/scripts/verify_cdn_urls.py \
  --workspace content-workspaces/{topic-slug} --expect live --write-json
```

Script tự suy tiền tố từ source của workspace; ép tay bằng `--base`.

**Lượt `--expect free` không phải thủ tục thừa.** `/News/0/` là thư mục dùng chung cho
mọi bài, nên tên file trùng là up đè lên ảnh của bài khác — ảnh vẫn hiện, không có lỗi
nào bắn ra, chỉ là bài kia âm thầm đổi ảnh. Vì vậy tên file nên mang tiền tố từ khoá
của bài (`may-in-phun-mau-kho-giay-ho-tro.jpg`) chứ đừng đặt tên chung chung
(`kho-giay-ho-tro.jpg`).

**Lượt `--expect live` cũng không bỏ được.** Nó là chỗ duy nhất phát hiện CMS đổi hành
vi. Gặp 404 thì mở 1 ảnh trong CMS lấy URL thật rồi chạy lại với `--base` cho đúng —
sửa một chỗ, cả bộ theo.

## Internal Linking Rules (Phủ Rộng & Chuẩn Ngữ Cảnh)

1. **Containers Được Phép Chèn Link:**
   - **Thẻ `<p>`** (trừ `p.titleOfImages` và `<p>` nằm trong `<table>`).
   - **Thẻ `<li>`** (bullet list, ví dụ danh sách ưu đãi/điều kiện) — cùng rule như `<p>`.
   - **Thẻ `<h2>`** (được phép chèn link trong H2 nếu từ khóa match URL phù hợp).
   - **CẤM chèn link trong:** `<h3>`, `<h4>`, `<h5>`, `<h6>`, `<table>`, `<img>`, `<figcaption>`, `p.titleOfImages`.
1b. **CẤM chèn link cho nội dung NGOÀI DANH MỤC (`--no-link-anchor`):**
   - Bài infobox được phép viết phần kiến thức về loại/dòng sản phẩm mà TGDĐ
     **không kinh doanh** (owner chốt 09/09/2026: nội dung phải đầy đủ về chủ đề).
     Phần đó chỉ mang tính giải thích, **không được dẫn về trang bán**.
   - Chèn link cho anchor như vậy tạo ra link tới **trang filter rỗng sản phẩm** —
     hại UX và hại SEO. Ca thật: bài Máy in, anchor `Máy in kim` bị chèn về
     `/may-in?g=may-in-kim` trong khi TGDĐ không kinh doanh máy in kim.
   - Truyền danh sách anchor loại trừ qua `--no-link-anchor` (lặp được nhiều lần)
     hoặc file `metadata/no-link-anchors.txt` trong content workspace, mỗi dòng
     một anchor. Script phải bỏ qua các anchor này khi match, **không** chèn link.
   - So khớp: không phân biệt hoa/thường, có/không dấu. Anchor loại trừ chặn cả
     biến thể chứa nó (`máy in kim`, `Máy in kim`, `máy in kim 24 kim`).
   - Khi bỏ qua một anchor vì rule này, log ra dòng
     `skip-link: <anchor> (no-link-anchor)` để verify được.

2. **Quy Tắc Match & Chống Cắt Chữ:**
   - **1 URL / 1 link:** Mỗi URL đích chỉ xuất hiện tối đa 1 lần duy nhất trong bài.
   - **Chống cắt lẻ thương hiệu:** Không cắt lẻ từ thương hiệu/tên ngắn (ví dụ "HP") nếu từ ngay sau nó là tên dòng/model (ví dụ "HP Victus", "HP Omen", "HP Pavilion").
   - **Chuẩn hóa Anchor Text:** Xóa bỏ khoảng trắng thừa đầu/cuối bên trong thẻ `<a>` (ví dụ `<a>sạc</a>` thay vì `<a> sạc </a>`).
   - Tất cả thẻ link chèn đều có `target="_blank" rel="noopener noreferrer"`.
3. **Phủ Rộng Tối Đa:**
   - Không giới hạn số lượng link cứng trên mỗi đoạn `<p>`, miễn là khớp ngữ cảnh và không trùng URL.
4. **Giới hạn đã biết của `fetch_links_from_sheets()` (KHÔNG tự "sửa" bằng cách bỏ dedup):**
   - Script chỉ giữ **1 keyword đại diện / 1 URL** khi đọc Sheet (dòng đầu tiên
     gặp cho mỗi URL, các biến thể keyword khác cho cùng URL bị bỏ qua) →
     nhiều từ khóa hợp lệ trong bài không match được dù URL đã có trong Sheet,
     chỉ vì cách diễn đạt khác với dòng đại diện.
   - **KHÔNG fix bằng cách bỏ dedup-theo-URL rồi feed toàn bộ biến thị vào
     `insert_internal_links()`** — đã thử và gây lỗi nghiêm trọng: tên
     thương hiệu (Samsung, Lenovo, Acer, Dell, Asus, MSI...) tồn tại nhiều
     URL khác NGÀNH HÀNG trong Sheet (điện thoại, laptop, màn hình...), script
     sẽ chọn URL sai ngành hàng cho bài đang viết (ví dụ bài Màn hình lại bị
     chèn "Samsung" trỏ về trang điện thoại Samsung `dtdd-samsung`).
     `CONTEXT_EXCLUSIONS` trong script chỉ chặn được 6 case đã hardcode, không
     bao quát hết kiểu nhầm-ngành-hàng-theo-brand này.
   - Nếu nghi ngờ có từ khóa bị bỏ sót: tra thủ công từng cụm từ trong Sheet
     (đọc trực tiếp, không chạy lại script với candidate list mở rộng), xác
     nhận URL đúng NGÀNH HÀNG của bài đang xử lý trước khi chèn tay.
5. **Anchor được phép là biến thể gần nghĩa của keyword Sheet — nhưng trang
   đích phải đúng là thứ anchor đang chỉ:**

   Rule cũ bắt anchor trùng verbatim keyword Sheet. **User đã nới ngày
   24/08/2026**: biến thể gần nghĩa (rút gọn, đồng nghĩa, cách gọi khác) được
   chấp nhận, miễn đúng ngữ nghĩa. Cái phải giữ nguyên là chốt chống link sai
   thứ — không phải chuyện so chuỗi.

   **Test bắt buộc, phải đạt CẢ HAI:**

   a. **Ngữ nghĩa:** đọc nguyên câu chứa anchor, hỏi "người đọc click vào chữ
      này có ra đúng thứ họ đang đọc không?". Anchor và trang đích phải chỉ
      **cùng một vật**.
   b. **Ngành hàng:** trang đích cùng ngành hàng với nghĩa của anchor trong
      câu đó.

   **Biến thể ĐƯỢC chèn** (đã duyệt qua thực tế, bài Infobox Mini PC):

   | Anchor trong bài | Keyword Sheet ghi | Vì sao được |
   | --- | --- | --- |
   | màn hình | màn hình máy tính | cùng vật, bài đang nói màn hình PC |
   | bàn phím | bàn phím máy tính | cùng vật |
   | ổ cứng ngoài | ổ cứng di động | cùng vật, chỉ khác cách gọi |
   | máy tính để bàn | máy tính | anchor còn hẹp và chính xác hơn Sheet |

   **Vẫn CẤM — đây mới là thứ rule này sinh ra để chặn:**
   - **Cụm thông số trần → danh mục đã lọc theo thông số đó.** Lỗi thật ở bài
     Infobox Laptop Zenbook: chèn "14 inch"→`laptop-khoang-14-inch`,
     "120Hz"→`laptop-120-hz`, "RAM 32 GB"→`laptop-32-gb`,
     "SSD 1 TB"→`laptop-ssd-1-tb`. Trượt test (a): trong câu, "14 inch" đang
     tả **chiếc máy bài đang nói**, không phải chỉ **tập hợp mọi laptop 14
     inch**. Anchor và trang đích không cùng một vật → cấm, dù cùng ngành hàng.
   - **Brand trần → URL sai ngành hàng.** "Samsung" trong bài màn hình mà trỏ
     `dtdd-samsung`. Trượt test (b).
   - **Tự bịa URL không có trong Sheet.** Biến thể được nới là ở *anchor*,
     không phải ở *URL*. URL luôn phải tra ra trong Sheet.

   Khi phân vân: hỏi test (a) trước, đừng đi so chuỗi. Chuỗi khớp mà sai vật
   thì vẫn cấm; chuỗi lệch mà đúng vật thì được.

6. **Tên hãng trần chỉ được link ở chỗ câu đang nói về HÃNG:**

   Lỗi thật (bài Top laptop gaming 770589, 03/09/2026): optimizer chèn
   `Acer` → `/laptop-acer` vào cụm **"công nghệ Acer ComfyView"**. Ở đó "Acer"
   là một phần **tên công nghệ màn hình độc quyền**, không phải nhắc tới hãng
   — người đọc click vào chỉ thấy mình bị đưa sang danh mục laptop Acer.

   | Chỗ được link | Chỗ CẤM link |
   | --- | --- |
   | "laptop **Acer**", "máy **Acer**", "hãng **Acer**" | "**Acer** ComfyView", "**Acer** Purified Voice", "**Acer** Nitro Sense" |
   | "của **Asus**", "thương hiệu **MSI**" | "**Asus** Lumina OLED", "**AMD** FreeSync", "**HP** Victus" (dòng máy → dùng link dòng riêng) |

   Script đã tự chặn 2 lớp trong `insert_internal_links()`:
   - Tên hãng đứng ngay trước **một từ viết hoa** (không có dấu câu chen giữa)
     → bỏ match. Bắt được cả tên công nghệ mới chưa từng gặp, không cần
     hardcode từng cái như `CONTEXT_EXCLUSIONS`.
   - Quét 2 lượt: lượt 1 chỉ nhận chỗ có từ chỉ hãng/ngành hàng đứng trước
     (`laptop`, `máy`, `hãng`, `của`, `dòng`, `mẫu`, `thương hiệu`...); hết chỗ
     đó mới hạ xuống lượt 2 nhận chỗ trung tính.

   **Hệ quả phải chấp nhận:** hãng nào trong bài chỉ xuất hiện dưới dạng tên
   công nghệ/tên dòng thì **mất link hãng** — đúng như vậy. Cách sửa là viết
   thêm một câu nhắc hãng tự nhiên trong `source-content.html` rồi optimize
   lại (ví dụ đã làm: bài 770589 thêm "đặc trưng thiết kế... của HP" để có chỗ
   neo link `/laptop-hp`), **không phải** nới lỏng guard này.

## Box "Xem thêm" — anchor phải là TOÀN BỘ tiêu đề bài liên quan

Box `[info]` "Xem thêm" cuối bài/cuối mục là danh sách bài liên quan, không
phải chỗ chèn link keyword. Mỗi dòng: **anchor = full tiêu đề bài đích**,
kèm `title` đúng bằng tiêu đề đó.

```html
<p>[info]</p>
<p><strong>Xem thêm</strong>:</p>
<ul>
<li><a title="TOP 10 laptop thiết kế đồ họa 3D tốt, đáng mua nhất tại TGDĐ" href="https://www.thegioididong.com/hoi-dap/top-5-mau-laptop-chuyen-do-hoa-3d-tu-hang-dell-asus-hp-1378290" target="_blank" rel="noopener">TOP 10 laptop thiết kế đồ họa 3D tốt, đáng mua nhất tại TGDĐ</a></li>
</ul>
<p>[/info]</p>
```

**SAI** (lỗi thật, bài 770589 — bài paste từ CMS hay ở dạng này): chỉ bọc 1
cụm trong tiêu đề, phần còn lại là text trơ.

```html
<li>Bật mí top <a href="...">8 laptop tốt nhất</a>, bền nhất trên thị trường hiện nay</li>
```

Anchor cắt kiểu đó vừa không nói được bài đích viết gì (mất tín hiệu anchor
text cho SEO), vừa cho vùng click bé xíu.

Script tự xử lý:

- `normalize_related_article_links()` nhận diện box qua marker
  `<p><strong>Xem thêm</strong>:</p>` đứng ngay trước `<ul>`/`<ol>`, rồi nới
  anchor của từng `<li>` ra hết tiêu đề + gán `title`. In log
  `[XEM THÊM] ... → full tiêu đề` mỗi dòng đã sửa.
- `insert_internal_links()` **loại** mọi `<li>` trong box này và mọi `<p>` mở
  đầu bằng "Xem thêm" khỏi vùng chèn link — nếu không, link keyword lại cắt
  ngang tiêu đề đúng như lỗi trên.
- Dòng có **nhiều link** trong cùng `<li>`: giữ URL của link đầu, các URL còn
  lại in `[WARN] bỏ link phụ trong cùng dòng` — đọc log, đừng để rơi âm thầm.
- Dạng inline (`<p>Xem thêm: <a>...</a>, <a>...</a></p>`) script **không tự
  sửa** được vì không biết ranh giới từng tiêu đề, chỉ in `[WARN]` khi anchor
  ngắn bất thường (<25 ký tự) → sửa tay, hoặc chuyển sang dạng `<ul>`.

`suggest_related_articles.py` in ra HTML đã đúng format này sẵn (full title +
`title` attr) — dán nguyên dòng, đừng cắt lại anchor.

## Ngoại Lệ: Bảng So Sánh Theo Hãng (Brand Table) — dễ bỏ sót

Rule "CẤM chèn link trong `<table>`" ở trên áp dụng cho bảng specs/cấu
hình/giá. Bảng **so sánh thương hiệu** (cột đầu tiêu đề `Thương hiệu`/`Hãng`,
mỗi dòng 1 hãng, ví dụ "Màn hình Asus", "Màn hình Xiaomi"...) là **ngoại lệ
bắt buộc phải xử lý thủ công** — script `optimize_content.py` KHÔNG tự làm
bước này (vẫn chặn link table như bình thường):

1. Liệt kê toàn bộ tên hãng ở cột đầu bảng.
2. Với mỗi hãng, tra URL trong Sheet 'All KW' (`SHEET_ALL_KW_ID`, cột O) theo
   pattern `https://www.thegioididong.com/{category-slug}-{brand-slug}` (ví
   dụ ngành hàng màn hình: `man-hinh-may-tinh-xiaomi`,
   `man-hinh-may-tinh-gigabyte`, `man-hinh-may-tinh-acer`...).
3. Hãng có URL → thay `<strong>Màn hình {Hãng}</strong>` bằng
   `<a href="{url}" rel="noopener noreferrer" target="_blank">Màn hình
   {Hãng}</a>` (bỏ `<strong>`, theo đúng pattern đã có sẵn trong bài).
4. Hãng KHÔNG có URL trong Sheet (ví dụ thương hiệu nhỏ/không phân phối chính
   hãng) → giữ nguyên `<strong>`, **không tự bịa URL**.
5. Vẫn giữ **1 URL / 1 link toàn bài**: nếu hãng đã được link ở đoạn văn khác
   trong bài, KHÔNG link lại trong bảng (và ngược lại).
6. QA cuối: đếm số hãng trong bảng có URL khả dụng trong Sheet, đối chiếu số
   hãng đã link trong bảng — phải khớp 100%, không được bỏ sót hãng nào có URL
   thật (lỗi thực tế đã gặp: 5/13 hãng có link, 8 hãng còn lại tuy có URL sẵn
   trong Sheet nhưng bị bỏ sót).

## Ngoại Lệ 2: Bảng Danh Sách Sản Phẩm (Product Table) — bắt buộc link từng sản phẩm

Ngoại lệ chèn link trong `<table>` thứ hai, song song với "Ngoại Lệ: Bảng So
Sánh Theo Hãng" ở trên. Áp dụng khi bảng liệt kê **từng sản phẩm cụ thể của
chính chủ đề bài viết** (mỗi dòng 1 SKU/model, ví dụ bảng "Các sản phẩm
laptop Asus Zenbook tại Thế Giới Di Động" trong bài Infobox Laptop Zenbook) —
khác brand table (mỗi dòng 1 hãng). Script `optimize_content.py` KHÔNG tự làm
bước này, xử lý thủ công:

1. **KHÔNG dùng Sheet 'All KW'** cho case này — trang chi tiết sản phẩm (SKU)
   không nằm trong Sheet keyword đó, chỉ có category/keyword URL. Phải lấy
   URL trực tiếp từ trang danh mục thật trên thegioididong.com.
2. Xác định trang danh mục (category listing) đúng chủ đề bài viết — thường
   suy ra được từ brand + ngành hàng của bài (pattern
   `https://www.thegioididong.com/{category-slug}-{brand-slug}`, ví dụ bài
   Zenbook → `https://www.thegioididong.com/laptop-asus-zenbook`), hoặc trang
   dòng sản phẩm hẹp hơn nếu bài chỉ viết về 1 dòng cụ thể.
3. Mở trang danh mục bằng `mcp__Claude_Browser__*`, dùng
   `mcp__Claude_Browser__javascript_tool` (chỉ để đọc DOM, không dùng để sửa
   UI) chạy
   `document.querySelectorAll('a[href*="/{category-root}/"]')` (ví dụ
   `a[href^="/laptop/"]`) để lấy toàn bộ cặp tên sản phẩm ↔ href. **Không chỉ
   dựa vào 1 lần `read_page`/accessibility-tree snapshot** — trang danh mục
   có thể lazy-render/virtualize sản phẩm, 1 lần đọc có thể chỉ bắt được một
   phần sản phẩm đang hiển thị trên viewport (thực tế đã gặp: lần đầu chỉ bắt
   được 9/15, phải chạy lại DOM query mới ra đủ).
4. Khớp từng dòng bảng theo tên sản phẩm/mã SKU (phần trong ngoặc, ví dụ
   "(PZ204WS)") với danh sách vừa lấy.
5. Sản phẩm KHÔNG có trong trang danh mục hiện tại (ví dụ model cũ đã hết
   hàng/ẩn khỏi listing) → fallback dùng công cụ tìm kiếm chính chủ site:
   `https://www.thegioididong.com/tim-kiem?key={SKU}`, lấy đúng 1 link sản
   phẩm khớp bằng cùng cách DOM query ở bước 3.
6. Sản phẩm vẫn không tìm được qua cả 2 cách trên (SKU sai/không tồn tại) →
   để nguyên không link, ghi rõ trong evidence/report — **không tự bịa URL**.
7. Format thay thế: chỉ đổi phần text tên sản phẩm trong `<span>` của `<td>`
   thành `<a href="{URL đầy đủ https://}" target="_blank"
   rel="noopener noreferrer">{đúng nguyên văn tên sản phẩm}</a>`, giữ nguyên
   toàn bộ style/cấu trúc còn lại của `<td>`/`<tr>`.
8. **Không xung đột với rule "1 URL / 1 link toàn bài"** ở trên: URL trang
   chi tiết sản phẩm (theo SKU) là một không gian URL hoàn toàn khác URL
   category/keyword dùng ở phần văn bản khác trong bài, nên không tính trùng.
9. QA cuối: đếm số dòng sản phẩm trong bảng vs số cell tên sản phẩm đã bọc
   `<a>` — phải khớp 100%, chỉ được lệch đúng bằng số sản phẩm đã ghi rõ
   "không tìm được" ở bước 6.

## Image Caption Rules (BẮT BUỘC — dễ nhầm)

Mỗi `<img>` bài Infobox **PHẢI** đi kèm 1 caption ngay sau, đúng cấu trúc:

```html
<p><img alt="..." title="..." src="..." width="845" height="475" /></p><p class="titleOfImages" style="font-size: 15px; color: #777777; text-align: center;">{caption}</p>
```

- `{caption}` lấy từ cột `caption` (ưu tiên) hoặc `description` trong
  `metadata/image-metadata.csv` — câu mô tả 1-2 câu **khác nội dung** với
  `alt`/`title`, không phải lặp lại `title`.

### Caption viết gì: giải thích liên quan, KHÔNG mô tả ảnh

Đây là lỗi hay gặp nhất và không bị bất kỳ gate đếm số nào bắt được, vì caption
sai nội dung vẫn đủ số lượng.

`alt` mô tả **ảnh có gì** (cho máy và cho người không xem được ảnh). Caption trả
lời **vì sao ảnh này đứng ở đoạn này** — nó là một câu nội dung của bài, đọc rời
khỏi ảnh vẫn có nghĩa và vẫn giúp người đọc quyết định được điều gì.

Test 1 câu: **che ảnh đi, caption còn nói được điều gì mới cho người đọc không?**
Nếu che ảnh đi mà caption thành vô nghĩa thì đó là mô tả ảnh, phải viết lại.

**CẤM** trong caption:

- Từ ngữ về bố cục/góc chụp/hậu cảnh: `góc 3/4`, `nền tối`, `cận cảnh`,
  `toàn cảnh`, `nhìn từ trên`, `xếp cạnh nhau`, `trong ảnh`, `phát sáng`.
- Mở đầu bằng `Cận cảnh...`, `Toàn cảnh...`, `Hình ảnh...`, `Bộ đôi...`,
  `Cỗ máy...`, `Đối chiếu...` — mở như vậy thì gần như chắc chắn đang tả ảnh.
- Liệt kê lại đúng chuỗi thông số đã có trong `alt`/`title` hoặc trong câu ngay
  trước ảnh. Trùng lặp thì caption không thêm giá trị gì.

Ví dụ (bài dòng laptop gaming, đoạn nói về tản nhiệt):

| | Caption |
| --- | --- |
| SAI (tả ảnh) | Cận cảnh khe thoát khí tổ ong và cụm quạt kép tản nhiệt ColdFront làm mát tối ưu. |
| ĐÚNG (giải thích) | Tản nhiệt quyết định máy giữ được tốc độ sau vài chục phút chơi hay tụt khung hình dần, nên đáng để ý ngang với cấu hình. |

Cột `description` trong `metadata/image-metadata.csv` **là nguồn caption** khi
không có cột `caption` (xem `format_image_element()`). Nên sửa caption trong HTML
mà bỏ quên CSV thì lần re-run optimizer sau sẽ ghi caption sai trở lại. Sửa
caption phải sửa đủ 4 nơi: `source-content.html`, `final-content.html`,
`image-placement.json`, `metadata/image-metadata.csv`.
- Đây đúng là hành vi mặc định của `format_image_element()` trong
  `scripts/optimize_content.py` — script luôn sinh cặp `<img>` + caption cùng
  lúc khi tự đặt ảnh theo `image-placement.json`.
- Nếu ảnh được chèn tay vào `source-content.html`/`final-content.html` (không
  qua `image-placement.json`, ví dụ paste trực tiếp từ CMS hoặc thao tác thủ
  công khác), **PHẢI tự thêm caption theo đúng mẫu trên** — không được bỏ qua
  chỉ vì ảnh không đi qua auto-placement.
- Rà nhanh trước khi báo xong: đếm số `<img>` phải bằng đúng số
  `p.titleOfImages` trong `final-content.html` (`grep -c` cả hai, phải khớp).

**KHÔNG nhầm với skill khác:** `tgdd-top-product-article` (bài Top-N sản phẩm)
có rule ngược lại — **CẤM tạo `p.titleOfImages`** vì CMS bài Top tự render
`<img title>` thành caption, thêm paragraph sẽ hiện caption 2 lần. Hai loại
bài (Infobox vs Top sản phẩm) render khác nhau trên CMS — áp nhầm rule của bài
này sang bài kia là sai.

## TGDD Heading Formatting Rules

- **`<h2>`**: KHÔNG dùng `<strong>`/`<b>`. Xóa bỏ hoàn toàn `style="font-weight: 400"` hoặc thẻ `<span>` thừa. *(Ví dụ: `<h2>Tiêu đề H2</h2>`)*
- **`<h3>`, `<h4>`, `<h5>`, `<h6>`**: BẮT BUỘC có thẻ `<strong>` bao bọc. Gỡ sạch `style="font-weight: 400"` trên `<span>` bên trong để hiển thị chữ ĐẬM. *(Ví dụ: `<h3><strong>Tiêu đề H3</strong></h3>`)*

## Table Formatting Rules (MWG Standard Mới)

Áp dụng cho mọi `<table>` trong source content — bảng thông số/cấu hình/so sánh giá.

- **`<table>`**: `width: 100%; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5; color: #333333;`. Xóa attribute `border`/`cellspacing`/`cellpadding`/`align` cũ (nếu có). Luôn bọc toàn bộ `<tr>` trong 1 `<tbody>` (không dùng attribute style/color riêng cho `<tr>`).
- **`<th>` (dòng đầu = header)**: nền đen `background: #000000`, chữ vàng `color: #ffe14c`, `font-weight: bold`, `text-align: center`, `vertical-align: middle`, `border: 1px solid #cccccc`, `padding: 8px 10px`, `box-sizing: border-box`.
- **`<td>` (các dòng sau)**: `border: 1px solid #cccccc`, `padding: 8px 10px`, `vertical-align: middle`, `box-sizing: border-box`. Bỏ thẻ `<p>` lồng trong `<td>`/`<th>` (unwrap).
- **Tự nhận diện cột giá:** cột mà ≥60% cell dữ liệu chứa số + ký hiệu `₫`/`đ` (ví dụ `19.490.000₫`) được xử lý là cột giá: `text-align: center`, `white-space: nowrap`, `width: 100px` cố định (**px chứ không phải %** — 15% của 355px chỉ còn 53px, không đủ chỗ cho `1.090.000₫` với `nowrap` (~79px) nên giá bị cắt trên mobile).
- **Cột text (tên sản phẩm, mô tả, nhu cầu sử dụng...)**: `text-align: left`, `white-space: normal; overflow-wrap: anywhere; word-break: break-word;` (chống tràn layout khi nội dung dài). Width % của các cột text chia theo tỉ lệ độ dài nội dung trung bình trên phần % còn lại sau khi trừ ngân sách 15%/cột giá (làm tròn về mốc 5%). Lưu ý: 15% chỉ là ngân sách chia layout, width xuất ra CSS cho cột giá vẫn là `100px`.
- **Cột "giá ưu đãi" nổi bật:** nếu header cột giá chứa từ khóa `ưu đãi`, `khuyến mãi`, `giá sốc`, `giá sale`, `giá online`, `giá giảm`, `giảm giá`, `còn lại`, `sau khi giảm` → tô `font-weight: bold; color: #d9381e;`. Nếu không match keyword nhưng bảng có ≥2 cột giá, mặc định cột giá cuối cùng (bên phải nhất) được coi là giá ưu đãi và tô đỏ.
- **Bảng có `colspan`/`rowspan` lệch cột:** fallback về style border/padding/wrap chuẩn, KHÔNG set `width` % và KHÔNG nhận diện cột giá (giữ layout gộp ô nguyên vẹn).
- **Link sẵn có trong `<td>`** (ví dụ tên sản phẩm có `<a href>`) giữ nguyên `href`/`target`/`rel`, không bị đụng tới — vì Internal Linking Rules ở trên CẤM chèn link MỚI vào `<table>`.

*Ví dụ output chuẩn (4 cột: 2 cột text + 2 cột giá, cột "Giá ưu đãi" tô đỏ):*

```html
<table style="width: 100%; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5; color: #333333;">
<tbody>
<tr>
<th style="width: 25%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #ffe14c; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">Phiên bản cấu hình</th>
<th style="width: 45%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #ffe14c; font-weight: bold; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">Nhu cầu sử dụng thực tế</th>
<th style="width: 100px; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #ffe14c; font-weight: bold; white-space: nowrap;">Giá gốc</th>
<th style="width: 100px; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; background: #000000; color: #ffe14c; font-weight: bold; white-space: nowrap;">Giá ưu đãi</th>
</tr>
<tr>
<td style="width: 25%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">MacBook Neo 256GB (Không có Touch ID)</td>
<td style="width: 45%; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: left; vertical-align: middle; white-space: normal; overflow-wrap: anywhere; word-break: break-word;">Phù hợp lưu trữ cơ bản tài liệu Word, Excel, file PDF và tiểu luận.</td>
<td style="width: 100px; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; white-space: nowrap;">19.490.000₫</td>
<td style="width: 100px; box-sizing: border-box; border: 1px solid #cccccc; padding: 8px 10px; text-align: center; vertical-align: middle; white-space: nowrap; font-weight: bold; color: #d9381e;">18.990.000₫</td>
</tr>
</tbody>
</table>
```

## Invocation

```bash
python3 .agents/skills/content-html-optimizer/scripts/optimize_content.py \
  --workspace content-workspaces/{topic-slug} \
  --fetch-links
```

## Gate QC internal link — chạy sau mỗi lần optimize

`optimize_content.py` chèn link theo keyword khớp chuỗi, nên **đúng chuỗi vẫn có
thể sai ngữ cảnh**. Đo 12 bài ngày 07/09/2026: 322 link, **47 link (14%) sai ngữ
cảnh**. Vì vậy sau khi build xong, bắt buộc chạy:

```bash
python3 .agents/skills/content-html-optimizer/scripts/check_internal_links.py \
  --workspace content-workspaces/{topic-slug} \
  --json {task}/data/processed/linkqc-{topic-slug}.json
```

Nguyên tắc chấm: **link đúng khi trang đích nói về đúng thực thể mà anchor đang
chỉ trong câu đó** — không phải thứ chứa nó (dòng/hãng/ngành hàng), thứ gần nó
(phụ kiện cùng tên), hay thứ trùng tên khác nghĩa.

| Case | Bắt cái gì |
| --- | --- |
| A1 | Anchor là tiền tố, mã đời nằm ngay sau: `[Acer Aspire]7` → `/laptop-acer-aspire` |
| B4 | Đích lệch ngành hàng bài, hoặc bộ phận có sẵn → category phụ kiện rời |
| C1 | Link trong khối `[info]` thông số trỏ về trang mua hàng |
| D1/D2/D3 | Tự link về chính bài / trùng URL / trùng đích với box "Xem thêm" |

Bảng phân loại đầy đủ 20 trường hợp (kể cả các ca **ĐÚNG** không được gỡ nhầm,
như `[tần số quét]144Hz` → bài "tần số quét là gì"):
`references/internal-link-qc-cases.md`.

**Mặc định script chỉ đề xuất, không sửa file.** Đọc từng finding kèm câu chứa
link rồi mới quyết. Duyệt xong thì gỡ bằng:

```bash
python3 .agents/skills/content-html-optimizer/scripts/check_internal_links.py \
  --workspace content-workspaces/{topic-slug} --fix
```

`--fix` gỡ thẻ `<a>` nhưng **giữ nguyên chữ**, và backup `final-content.html.prelinkfix`.
Optimizer chèn link lại ở MỖI lần build, nên **`--fix` phải chạy lại sau mỗi lần
optimize** — không phải sửa một lần là xong.

Đích lệch ngành nhưng là lời mời mua thật (không bao giờ là bộ phận có sẵn của
máy) khai trong `phu_kien_hop_le` của `references/link-category-map.json`, không
gắn cờ. Hiện có: `tui-chong-soc-balo-laptop`, `phan-mem-*` cho bài laptop.

**Luật không bắt được** 3 loại, phải đọc câu mới biết — chuyển cho lớp review
bằng model (xem `references/internal-link-qc-cases.md`, cột "Ai bắt"):

- A2/A3: anchor là dòng — câu đang nói về cả dòng hay về một SKU cụ thể?
- B3: trùng tên khác nghĩa khi đích là bài hỏi đáp (`cổng USB` → `usb-charge-la-gi`).
- E1: anchor từ chung chung, câu không mang ý định mua.

## QA sau khi chạy — bắt buộc đếm link theo NGUỒN

Script kéo link từ **2 Sheet**: `All KW` (danh mục/sản phẩm) và `BÀI TIN`
(bài hỏi đáp, hệ blog). Lỗi đã gặp thật (bài Infobox Mini PC, 24/08/2026):
worker chạy script ra 15 link (11 `All KW` + 4 `BÀI TIN`), rồi giao ra bản chỉ
còn 11 link — **0 link blog**. 2 link bị gỡ có ghi lý do, 2 link còn lại
(`cổng HDMI`, `DisplayPort`) bị bỏ âm thầm, không báo cáo.

Vì vậy sau mỗi lần chạy:

1. Đếm link theo nguồn, ghi rõ vào report: `{n} link All KW + {m} link BÀI TIN`.
2. `m = 0` **không mặc nhiên là đúng**. Phải kiểm lại: chạy
   `load_internal_links_from_sheets()` rồi đối chiếu keyword `BÀI TIN` với text
   bài — nếu có match thật mà không link, phải giải thích từng cái.
3. Gỡ bất kỳ link nào script đã chèn → **bắt buộc ghi vào report: anchor, URL,
   lý do**. Gỡ mà không ghi là báo cáo sai, không phải tối ưu.
4. Không tự tay thêm link ngoài output của script mà không nói rõ. Thêm tay thì
   URL vẫn phải tra ra trong Sheet (xem rule 5).

Câu lệnh đếm nhanh trên file đã xong:

```bash
grep -o '<a href="[^"]*"' final-content.html | sort -u | grep -c '/hoi-dap/'
```
