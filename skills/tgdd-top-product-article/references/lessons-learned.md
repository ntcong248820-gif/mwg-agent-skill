# Bẫy đã gặp thật — đọc trước khi bỏ qua rule

Nguồn: dự án `hoidap-top-laptop-gaming-duoi-25-trieu` (08/2026), 5 vòng sửa.

## 1. Caption hiện 2 lần trên web

User phát hiện qua screenshot: mỗi ảnh có caption lặp.

Nguyên nhân: CMS **tự render `<img title="...">` thành caption**. Code còn thêm
`<p class="titleOfImages">` → 2 dòng caption.

Source CMS chuẩn của bài khác chỉ có:
```html
<p><img title="Kích thước 42.6mm kết hợp dây silicone" src="..." alt="Kích thước 42.6mm kết hợp dây silicone" width="800" /></p>
```

Rule: **không bao giờ tạo `p.titleOfImages`** trong bài top.

Gốc rễ: `content-html-optimizer/scripts/optimize_content.py` hàm
`format_image_element` (~line 476) tự sinh `p.titleOfImages` **mỗi lần chạy** →
phải xóa lại sau mỗi lần optimize. Validator có check `zero p.titleOfImages`.

## 2. Ảnh đặt sai chỗ trong khối SP

Ảnh nằm ngay sau `[product ID]`, trước `[info]` specs. User yêu cầu theo bài
Garmin Pickleball: **widget → specs → đoạn nội dung đầu → ảnh → đoạn còn lại**.

Validator check: ảnh phải sau `[/info]` VÀ sau ít nhất 1 đoạn nội dung.

## 3. Optimizer gán sai ảnh cho sản phẩm

Khối SP 333430 nhận ảnh của SP 333427 (`class="lazy" title=""`). Chỉ validator
bắt được, đọc mắt không thấy.

Gốc rễ: `optimize_content.py` ~line 617-623 fallback theo index
`img_src = dump_imgs_list[idx]` khi `metadata/image-metadata.csv` không có entry
cho file mới.

Phòng: điền `image-metadata.csv` cho **mọi** ảnh mới trước khi chạy optimizer.
Sau khi chạy, verify từng khối SP có đúng ảnh của nó.

## 4. Sửa ở final-content.html là vô nghĩa

`optimize_content.py` build `final-content.html` **TỪ** `source-content.html` mỗi
lần chạy. Mọi fix ở `final` bị ghi đè lần chạy sau. Sửa `source` trước, rồi
optimize, rồi mới patch cái optimizer làm sai.

Validator có check parity `source ↔ final` (danh sách `[product ID]` + danh sách
ảnh) để bắt trạng thái lệch.

## 5. Optimizer chèn internal link lệch ngữ cảnh

Nó lặp lại 3 lần việc chèn "máy chơi game" → `/may-choi-game-cam-tay` (danh mục
máy chơi game cầm tay) trong bài **laptop** gaming.

Xử lý sau mỗi lần optimize: xóa link sai trong `final-content.html` **và** xóa
entry tương ứng trong `metadata/inserted-links-report.json`.

## 6. Sản phẩm chết giữa dự án

4 SP ngừng kinh doanh trong lúc viết: Asus K3605VC, MSI Katana 15, Asus TUF F16
FX607VJ, Acer Aspire 7 A715-59G-73LB. Category grid vẫn hiện một số cái.

Xử lý: re-check toàn bộ ID bằng script **ngay trước khi publish**, không chỉ lúc
research. Mỗi lần thay phải sync 4 nơi: bảng tổng hợp, khối H4, `listid` đầu bài,
`products` của `[sosanh]`.

Hệ quả phụ đã gặp: sau 5 vòng thay, bài còn 5/10 SP cùng hãng Acer và thứ tự giá
không còn tăng dần. Kiểm lại thứ tự + độ đa dạng hãng sau mỗi lần thay.

## 7. listid / products lệch thứ tự

Shortcode ghi `...,313177,333427,...` nhưng thứ tự body là `...,333427,313177,...`.
Đọc mắt không thấy. Validator so thứ tự chính xác giữa body và cả 2 shortcode.

## 8. Giới hạn ngầm của [sosanh]

- Quá 7 `properties` → property thứ 8+ **không render**, không báo lỗi.
- `categoryid` rỗng HOẶC `products` rỗng → **mất cả bảng**, không báo lỗi.
- SP ngừng kinh doanh → **âm thầm mất dòng** đó.

## 9. SỰ CỐ: xóa mất cả 10 ảnh

Script BeautifulSoup gọi `img_p.decompose()` trên thẻ `<p>` cha **trước khi**
extract `<img>` con → để lại `<p><></></p>` ở CẢ 2 file. Không có git backup vì
thư mục workspace nội dung bài viết nằm trong `.gitignore`.

Phải dựng lại 10 thẻ `<img>` từ output Read trước đó.

Rule: **workspace nội dung không có git backup.** Trước khi chạy script sửa
hàng loạt, `cp` file ra scratchpad. Khi chuyển thẻ, extract con trước, decompose
cha sau.

## 10. Tín hiệu trạng thái không đáng tin

Đã giả định `item_web_status` là đủ → test cho thấy nó **rỗng ở cả SP live
(333430) và SP chết (339687)**. JSON-LD `availability` luôn `InStock`. Grid có
cache lag.

Nên phân 3 tầng, chỉ escalate AMBIGUOUS lên browser. Đừng cho SP chết đi qua
im lặng.

## 11. Validator tìm ra lỗi trong bài đã báo "xong"

Chạy validator lần đầu trên bài đã báo hoàn thành: **FAIL 4** (ảnh gán sai, thiếu
`title`, listid lệch thứ tự, source↔final lệch). Đọc mắt không bắt được.

Rule: **chưa chạy validator = chưa xong.** FAIL > 0 = chưa xong.

## 12. `--grid` từng hỏng âm thầm vì nháy đơn

Regex grid ban đầu tìm `href="..."` (nháy đôi) → khớp **0 sản phẩm**, chỉ bắt link
nav trong footer, và vẫn in ra "4 SP trong grid" nên trông như chạy được.

HTML grid thật: `<li class=" item __cate_44" data-index="1" data-id="362621"
data-price="29990000.0">` chứa `<a href='/laptop/{slug}?utm_flashsale=1'
data-price="24990000.0" data-name=... data-brand=...>` — **href dùng nháy ĐƠN**.

Bài học: script scrape phải verify bằng số lượng kết quả kỳ vọng (grid trang 1 =
~20 SP). Ra 4 SP là dấu hiệu hỏng, không phải "grid ít hàng".

## 13. Giá: 3 nguồn, 2 nguồn dễ hiểu sai

- `viewed-product-price`: chỉ tồn tại trong **CSS**, không phải markup giá. Vô dụng.
- datalayer `price:` trên trang SP: giá bán thật, **nhưng có SP trả `0.0`**
  (vd Lenovo LOQ 15IRX9) → fallback JSON-LD ra **giá gốc**, lệch ~1.4tr.
- `a[data-price]` trong category grid: nguồn giá bán đáng tin nhất.

Rule: sort/bảng giá lấy từ `--grid`. Giá có dấu `~` trong output là giá gốc,
không được đưa vào bài như giá bán.

## 14. Bài đã "xong" nhưng vẫn bị user chê 5 lỗi khác validator không bắt

Nguồn: dự án `hoidap-top-4-laptop-gaming-duoi-40-trieu` (08/2026), vòng sửa 3.
Bài đã qua `validate_article.py` 22/22 pass nhưng user vẫn phản hồi 5 vấn đề —
validator chỉ bắt lỗi cấu trúc shortcode/ảnh, không bắt văn phong hay lựa chọn
sản phẩm.

- **Giá tĩnh trong bảng tổng hợp trở nên dư/lệch khi có `[sosanh]`**: `[sosanh]`
  đã hiện giá động ngay dưới bảng, giá viết cứng trong bảng dễ lệch theo thời
  gian và gây khó hiểu khi 2 nơi hiện 2 số khác nhau. Bỏ cột Giá khỏi bảng tổng
  hợp (và dòng "Giá tham khảo" trong specs `[info]` mỗi khối H4) khi `[sosanh]`
  xuất hiện ngay sau bảng. Xem `article-structure.md`.
- **"Dưới N triệu" bị hiểu sai thành "bất kỳ giá nào dưới N"**: 10 SP ban đầu
  trải từ 24.99tr đến 37.39tr cho bài "dưới 40 triệu", trong khi nhu cầu thực
  tế nhắm khoảng áp sát 40tr. Xem `product-research.md` mục "Dưới N triệu
  nghĩa là áp sát N".
- **Chọn ảnh chỉ theo tiêu chí "có banner hay không", bỏ qua màu nền**: 4/10 SP
  ban đầu (trước khi bị phát hiện) rơi vào nhóm không có `banner_slides`, và
  ảnh fallback lấy từ `product_images` là ảnh nền trắng thuần — đúng thứ user
  vừa yêu cầu bỏ. Phải tải và xem trực tiếp ảnh trước khi chọn, không suy đoán
  theo tên field. Xem `product-research.md` mục "Chọn ảnh cho khối sản phẩm".
- **Văn phong lộ dấu AI**: dùng em dash "&mdash;"/"—" 4 lần và các từ ít phổ
  biến ("ọp ẹp", "dư địa") — người đọc nhận ra ngay là văn AI. Cấm cả 2 trong
  mọi khối H4. Xem `article-structure.md` mục "Quy tắc nội dung mỗi khối".
- Toàn bộ 4 vấn đề trên biến mất tự nhiên khi làm đúng bước "thay SP giữa dự
  án" (lesson #6) một cách triệt để — tức là khi phải đổi sản phẩm, tận dụng cơ
  hội đó để sửa luôn thứ tự giá, ảnh và văn phong, không chỉ đổi ID.

## 15. "Không nền trắng" bị hiểu hẹp thành "miễn không trắng là được"

Nguồn: dự án `hoidap-top-4-laptop-gaming-duoi-40-trieu` (08/2026), vòng sửa 4,
ngay sau khi lesson #14 vừa thêm rule "cấm ảnh nền trắng".

Khi 3/10 SP không có `banner_slides`, đã chọn ảnh cận cảnh bàn phím/RGB trong
`product_images` làm phương án thay thế — nền tối, đúng rule "không trắng",
nhưng user vẫn chê và tự sửa lại: bài top sản phẩm cần ảnh thấy được **toàn bộ
cái sản phẩm**, không phải ảnh cắt cận một bộ phận (bàn phím) dù nền có tối
hay không.

Rule cũ chỉ kiểm 1 tiêu chí (màu nền) nên vẫn chọn sai. Rule đúng phải kiểm
**2 tiêu chí đồng thời**: không nền trắng VÀ thấy toàn bộ máy. Ảnh cận cảnh
bàn phím/RGB không còn là phương án thay thế hợp lệ, dù trước đây từng dùng
được. Nếu SP không có ảnh nào đạt cả 2, loại SP đó khỏi danh sách. Xem
`product-research.md` mục "Chọn ảnh cho khối sản phẩm".

## 16. Văn phong đúng chuẩn vẫn có thể "yếu" — thiếu tính bán hàng

Nguồn: user đưa ví dụ đối chiếu trực tiếp 1 khối SP (Asus ZenBook 14), không
qua CMS review.

Bài đạt hết rule cứng (không em dash, không slang, có "Phù hợp cho:", nêu hạn
chế) nhưng đoạn văn vẫn đọc như liệt kê spec + nửa câu công dụng, không như
văn bán hàng thật. Câu mở kiểu "X trang bị Y" định vị yếu hơn "X là lựa chọn
hàng đầu cho {nhu cầu} nhờ Y". Chi tiết + ví dụ đối chiếu: `article-structure.md`
mục "Văn phong: bán hàng, không phải liệt kê spec".

Cạm bẫy đi kèm: khi viết lại cho "hay hơn", dễ vô tình xóa luôn câu hạn chế
(rule #14 "nêu ít nhất 1 hạn chế") vì hạn chế nghe không "sang". Phải giữ hạn
chế, chỉ đổi giọng — không xóa.

## 17. Thứ tự cuối bài bị hiểu ngược: câu kết trước, shortcode chốt bài

Nguồn: CMS review trực tiếp bởi reviewer nội bộ, trên 2 bài renew cùng lúc
(`hoidap-top-laptop-pin-trau`, `hoidap-top-laptop-van-phong-gia-re`) — cả 2 đều
sai giống nhau, và bài thứ 3 (`hoidap-top-laptop-sinh-vien`) thiếu hẳn box
info "Xem thêm" ở cuối.

`article-structure.md` (bản cũ) và `SKILL.md` Bước 3 (bản cũ) đều ghi thứ tự
`đoạn kết → [Product_Promotion]` — tức shortcode nằm SAU câu kết, vì trực giác
"shortcode nằm cuối cùng trong khối markup nhìn hình thức = kết bài". Reviewer
yêu cầu ngược lại: `[Product_Promotion] → [info] Xem thêm [/info] → câu kết`.

Rule đúng: shortcode luôn đặt trước, box info "Xem thêm" ngay sau shortcode,
câu kết (bọc `<em>`) là dòng cuối cùng thật sự của bài. Áp dụng cho **mọi**
mục có heading kết thúc bằng câu tổng kết (không chỉ mục 5 "Câu hỏi liên
quan") — không chỉ được thiếu box "Xem thêm" dù bài có vẻ đã đủ ý.

Không tự bịa URL cho box "Xem thêm" khi chưa có link thật — hỏi user hoặc để
trống chờ xác nhận, đừng chèn `href="#"` hay link đoán chừng vào bài sắp
publish.

## 18. Link hãng/dòng SP không tự động đủ, phải verify sau optimize

Nguồn: user yêu cầu thêm rule sau khi soát lại 3 bài renew.

Optimizer (`content-html-optimizer/optimize_content.py`) đã có cơ chế chèn
link hãng/dòng qua `CUSTOM_LINK_OVERRIDES`, nhưng danh sách này build dần theo
từng dự án nên **không phủ hết** — 3 bài pin-trau/van-phong-gia-re/sinh-vien
đang dùng các dòng SP (Acer Aspire, Acer Swift, HP OmniBook 5/X, MSI Prestige,
MacBook Air) mà danh sách cũ hoàn toàn thiếu, và `hp victus` từng trỏ sai URL
(`laptop-hp-victus` thay vì `laptop-hp-compaq-victus`, xác nhận qua đối chiếu
URL taxonomy đã build sẵn trong workspace). Đã bổ sung + sửa trực tiếp trong
`optimize_content.py`.

Rule mới: mỗi hãng/dòng SP trong bài phải có đúng 1 link, verify bằng cách
đếm hãng/dòng trong `[product ID]` đối chiếu `inserted-links-report.json` sau
mỗi lần optimize — không tin optimizer tự đủ. Chi tiết:
`article-structure.md` mục "Link hãng + dòng sản phẩm".

## 19. Box "Xem thêm" bỏ trống vì không có cách tra bài liên quan

Nguồn: soát lại sau CMS review — nối tiếp lesson #17.

Lesson #17 chốt rule "không bịa URL cho box Xem thêm", nhưng lúc đó chưa có
đường nào lấy URL thật nhanh, nên rule đúng lại dẫn tới kết quả sai: bài
`hoidap-top-laptop-sinh-vien` bỏ trống hẳn box đó. Cấm bịa mà không cấp nguồn
tra thì người viết chọn bỏ trống — vẫn là lỗi CMS review bắt.

Nguồn thật đã nằm sẵn trong pipeline mà không ai dùng đúng chỗ: sheet **BÀI TIN**
(cột B/C/D/E = Link air / Hệ bài / Title / KW mục tiêu) được `optimize_content.py`
fetch mỗi lần chạy, nhưng chỉ dùng cặp `(keyword, url)` để chèn link inline —
`Title` và `Hệ bài` bị bỏ, đúng 2 cột cần cho box Xem thêm.

Đã thêm `content-html-optimizer/scripts/suggest_related_articles.py`: chấm điểm
theo term trên `KW mục tiêu` (×3) + `Title` (×2), cộng điểm nếu trùng hệ bài, tự
loại URL đã có trong bài và loại chính bài đang viết qua ID cuối slug. In bảng
xếp hạng + HTML sẵn, **không** tự chèn — chọn bài liên quan vẫn là quyết định
biên tập.

Bẫy khi viết script: tên sheet `BÀI TIN` có dấu, `json.dumps` mặc định escape
thành `BÀI TIN` và `gws` trả **exit 5** không nói lý do. Phải
`ensure_ascii=False`.

## 20. Link hãng neo vào tên công nghệ, không phải vào hãng

Nguồn: user soát một bài sau round 2.

Optimizer chèn `Acer` → `/laptop-acer` đúng vào chữ "Acer" trong cụm **"công
nghệ Acer ComfyView"**. Chuỗi khớp hoàn hảo, `CONTEXT_EXCLUSIONS` không có case
này nên không chặn. Nhưng ở đó "Acer" là một phần tên công nghệ màn hình độc
quyền — người đọc đang đọc tên công nghệ, click vào lại bị đẩy sang danh mục
laptop Acer.

Đây là biến thể mới của lesson #5: lệch ngữ cảnh mà **không** lệch ngành hàng,
nên mọi rule cũ (đúng ngành hàng, đúng chuỗi) đều pass.

Rule: tên hãng trần chỉ được neo ở chỗ câu đang nói về **hãng hoặc máy của
hãng** — "laptop Acer", "máy Acer", "hãng Acer", "của Acer". Cấm neo vào "Acer
ComfyView", "Acer Purified Voice", "Asus Lumina OLED", "AMD FreeSync", và cấm
neo vào tên dòng máy ("HP Victus" → dùng link dòng riêng).

Đã sửa trong `content-html-optimizer/scripts/optimize_content.py`: bỏ match khi
tên hãng đứng ngay trước một từ viết hoa (không có dấu câu chen giữa) — bắt được
cả tên công nghệ chưa từng gặp, không cần hardcode từng cái; và quét 2 lượt,
lượt 1 chỉ nhận chỗ có `laptop/máy/hãng/của/dòng/mẫu/thương hiệu` đứng trước.

Hệ quả phải chấp nhận: hãng chỉ xuất hiện dưới dạng tên công nghệ/tên dòng thì
**mất link hãng**. Cách sửa là viết thêm câu nhắc hãng tự nhiên trong
`source-content.html` rồi optimize lại (thêm "đặc trưng thiết kế đơn sắc bàn
phím trắng của HP" để neo `/laptop-hp`), không phải nới guard.

## 21. Anchor box "Xem thêm" bị cắt còn 1 cụm giữa tiêu đề

Nguồn: user soát bài — nối tiếp lesson #19.

Lesson #19 giải quyết "box Xem thêm bỏ trống". Lỗi tiếp theo là box **có** link
nhưng anchor chỉ bọc 1 cụm giữa tiêu đề, phần còn lại là text trơ:

```html
<li>Bật mí top <a href="...">8 laptop tốt nhất</a>, bền nhất trên thị trường hiện nay</li>
```

Anchor kiểu đó vừa mất tín hiệu anchor text (không nói được bài đích viết gì),
vừa cho vùng click bé xíu. Bài paste từ CMS gần như luôn ở dạng này, và
optimizer trước đây còn góp thêm: nó coi `<li>` box Xem thêm là container chèn
link bình thường nên cắt tiêu đề bằng link keyword.

Rule: mỗi dòng box "Xem thêm" là **1 bài liên quan**, anchor = **full tiêu đề**,
kèm `title` đúng bằng tiêu đề đó.

Đã sửa trong `optimize_content.py`: `normalize_related_article_links()` nới
anchor từng `<li>` ra hết tiêu đề + gán `title` (log `[XEM THÊM] ... → full tiêu
đề`), và `insert_internal_links()` loại `<li>` box này + `<p>` mở đầu "Xem thêm"
khỏi vùng chèn. Dạng inline nhiều link trong cùng `<p>` script không tự sửa được
(không biết ranh giới tiêu đề) → chỉ `[WARN]`, sửa tay.
