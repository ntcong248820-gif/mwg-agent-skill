# Cấu trúc bài top sản phẩm TGDĐ

## Skeleton đầy đủ

```html
<p>[Product_Promotion listid="ID1,ID2,...,IDN" categoryid="" manufactureid="" propertyid="" title="ĐỪNG BỎ LỠ danh sách TOP {ngành hàng} {điều kiện} đáng mua trong bài:" ]</p>

<h2>{Mở bài 2-3 câu: vấn đề người đọc + bài này giải quyết gì}</h2>

<p>[info]</p>
<p>Bài viết được cập nhật ngày {dd/mm/yyyy}. Giá và tình trạng kinh doanh có thể thay đổi.</p>
<p>[/info]</p>

<h3><strong>1. Tiêu chí chọn {ngành hàng} {điều kiện}</strong></h3>
<p>{dẫn nhập}</p>
<table>...2 cột: Tiêu chí | Giải thích...</table>

<p>[info]</p>
<p><strong>Xem thêm</strong>: {2-3 link bài liên quan}</p>
<p>[/info]</p>

<h3><strong>2. Bảng tổng hợp TOP N {ngành hàng} {điều kiện} nổi bật</strong></h3>
<table>...N dòng: Tên SP | Điểm mạnh...</table>
<p>[sosanh products="ID1,...,IDN" properties="P1,...,P7" categoryid="{cat}"]</p>

<h3><strong>3. Đánh giá TOP N {ngành hàng} {điều kiện}</strong></h3>
{N khối H4 — xem dưới}

<h3><strong>4. Chính sách bảo hành và ưu đãi khi mua tại Thế Giới Di Động</strong></h3>

<h3><strong>5. Câu hỏi liên quan</strong></h3>
{3-5 cặp H4 câu hỏi + đoạn trả lời, hoặc p+strong}

<p>[Product_Promotion listid="{ID ngành hàng giảm sốc, KHÔNG trùng bài}" categoryid="" manufactureid="" propertyid="" title="ĐỪNG BỎ LỠ các mẫu {ngành hàng} GIẢM SỐC:" ]</p>

<p>[info]</p>
<p><strong>Xem thêm</strong>: {1-2 link bài liên quan thật, không tự suy/bịa URL}</p>
<p>[/info]</p>

<p><em>{đoạn kết + CTA}</em></p>
```

**Thứ tự cuối bài bắt buộc: shortcode → box info Xem thêm → câu kết.** Không phải
"đoạn kết trước, shortcode chốt bài" — đó là hiểu sai phổ biến vì shortcode nằm
ở cuối markup nhìn hình thức. Một lần review CMS từng bắt lỗi này trên 2/3 bài
renew cùng lúc (lesson #17).

## Khối sản phẩm (H4)

Thứ tự bất di bất dịch: **widget → specs → nội dung có ảnh chen giữa**.

```html
<h4><strong>{Tên SP đầy đủ} ({mã SP})</strong></h4>
<p>[product ID="{id}" Description="none" Display="block"]</p>
<p>[info]</p>
<p><strong>Thông số kỹ thuật</strong>:</p>
<ul>
<li>CPU: ...</li>
<li>RAM: ...</li>
<li>...</li>
</ul>
<p>[/info]</p>
<p><a href="{url SP}" rel="noopener" target="_blank"><strong>{Tên SP ngắn}</strong></a> là {câu định vị: vì sao SP này vào top, gắn với điều kiện của bài}.</p>
<p><img alt="{mô tả có dấu}" src="{cdn url}" title="{mô tả có dấu, giống alt}" width="800" /></p>
<p>Trang bị <strong>{spec nổi bật}</strong> {diễn giải lợi ích thực tế}.</p>
<p>{đoạn về màn hình / pin / thiết kế / hạn chế}</p>
<p>Phù hợp cho: {đối tượng cụ thể}.</p>
```

Quy tắc nội dung mỗi khối:
- 3-5 đoạn `<p>`, mỗi đoạn 2-4 câu. Không viết 1 khối dài 10 đoạn.
- Đoạn đầu phải trả lời "vì sao SP này trong top", không mô tả chung chung.
- Nêu ít nhất 1 hạn chế → tăng độ tin.
- Kết bằng "Phù hợp cho:" để người đọc tự loại.
- Link SP chỉ 1 lần / khối, ở đoạn đầu.
- **Không dùng dấu em dash "—" (kể cả `&mdash;`)** — đây là dấu đặc trưng của
  văn AI, user nhìn phát biết ngay. Thay bằng câu tách riêng hoặc dấu phẩy.
- **Không dùng từ ngữ ít phổ biến/thiếu chuyên nghiệp** (vd "ọp ẹp", "dư địa").
  Ưu tiên từ ngữ báo chí/CMS quen dùng: "chắc chắn", "linh hoạt hơn", "cải
  thiện", "tối ưu hơn" thay cho slang.

### Văn phong: bán hàng, không phải liệt kê spec

Mỗi đoạn phải **dịch spec thành lợi ích người đọc cảm nhận được**, không chỉ nêu
thông số rồi thêm nửa câu công dụng. Câu mở đoạn nên định vị sản phẩm ("là lựa
chọn hàng đầu cho...") thay vì liệt kê linh kiện ("trang bị..."). Xưng "bạn" để
kéo người đọc vào, gộp các spec liên quan (thiết kế + màn hình + RAM) thành 1
đoạn liền mạch thay vì tách mỗi spec 1 đoạn riêng biệt, cụt lủn.

Yếu vs tối ưu, cùng 1 sản phẩm (Asus ZenBook 14):

```
Yếu:
Asus ZenBook 14 trang bị pin 75Wh, đủ dùng nhiều giờ liên tục cho công việc
di chuyển thường xuyên.

Vỏ nhôm nguyên khối màu xanh navy mang lại vẻ ngoài sang trọng, trọng lượng
nhẹ, dễ mang theo trong balo laptop hằng ngày.

Dòng Asus Zenbook nổi bật với màn hình OLED, đối với sản phẩm này, màn hình
đạt 3K OLED 120Hz hiển thị sắc nét, nhưng bù lại máy chỉ có RAM 16GB hàn chết,
không nâng cấp được về sau.

Phù hợp cho: người dùng văn phòng, sinh viên cần máy mỏng nhẹ, pin bền và
màn hình đẹp để làm việc lẫn giải trí.

Tối ưu:
Asus ZenBook 14 là lựa chọn hàng đầu cho nhu cầu làm việc linh hoạt nhờ viên
pin 75Wh vượt trội, cho phép bạn thoải mái xử lý công việc cả ngày dài mà
không cần mang theo củ sạc vướng víu.

Máy sở hữu thiết kế vỏ nhôm xanh Navy sang trọng, siêu mỏng nhẹ để bạn dễ
dàng mang theo mỗi ngày. Trải nghiệm thị giác được nâng tầm với màn hình 3K
OLED 120Hz tuyệt đẹp, kết hợp cùng 16GB RAM chạy đa nhiệm mượt mà.

Phù hợp: Dân văn phòng và sinh viên năng động.
```

Khác biệt cụ thể:
- Câu mở: "X trang bị Y" → "X là lựa chọn hàng đầu cho {nhu cầu} nhờ Y". Định vị
  trước, thông số sau.
- Lợi ích cụ thể hóa thành trải nghiệm: "đủ dùng nhiều giờ" → "cả ngày dài mà
  không cần mang theo củ sạc vướng víu". Nêu cái người đọc **không phải làm**,
  không chỉ nêu cái máy **làm được**.
- Xưng "bạn" ở câu có hành động của người đọc (mang theo, xử lý công việc).
- Gộp đoạn: 2 đoạn tách riêng (vỏ máy / màn hình+RAM) → 1 đoạn liền mạch, câu
  sau nối ý câu trước bằng dấu phẩy thay vì chấm câu cụt.
- "Phù hợp cho:" rút gọn thành cụm ngắn ("Dân văn phòng và sinh viên năng
  động") thay vì liệt kê 3 nhu cầu cách nhau bằng dấu phẩy.

**Cảnh báo — đừng đánh đổi rule "nêu hạn chế" lấy văn phong hay.** Ví dụ trên
đánh đổi: bản gốc có "RAM 16GB hàn chết, không nâng cấp được" (hạn chế thật),
bản tối ưu bỏ hẳn, chỉ còn "16GB RAM chạy đa nhiệm mượt mà" (thuần lợi ích).
Rule "nêu ít nhất 1 hạn chế → tăng độ tin" ở trên vẫn đứng — khi viết tối ưu,
**giữ câu hạn chế nhưng đổi giọng cho đỡ khô** (vd "RAM 16GB hàn sẵn, đủ dùng
cho đa nhiệm hiện tại nhưng không nâng cấp được về sau nếu nhu cầu tăng"),
không xóa hẳn để đoạn văn nghe mượt hơn.

## Link hãng + dòng sản phẩm

Mỗi **hãng** và mỗi **dòng sản phẩm** xuất hiện trong bài (suy từ tên SP ở mỗi
`<h4>`) phải có **đúng 1 link** trong toàn bài trỏ về trang danh mục hãng/dòng
đó trên thegioididong.com, không chỉ link tới trang chi tiết SP (`[product ID]`
đã làm việc đó rồi). Ví dụ bài có SP "Acer Aspire Go 15 AG15-72P-500W":

- Nhắc tới hãng **Acer** ở đâu đó trong bài (đoạn mở, đoạn so sánh, hoặc ngay
  trong khối SP đó) → chèn 1 link tới `https://www.thegioididong.com/laptop-acer`.
- Nhắc tới dòng **Acer Aspire** → chèn 1 link tới
  `https://www.thegioididong.com/laptop-acer-aspire`.

**Link hãng phải neo vào chỗ đang nói về HÃNG.** Không được neo vào chỗ tên hãng
là một phần **tên công nghệ độc quyền**: "công nghệ **Acer** ComfyView", "**Acer**
Purified Voice", "**Asus** Lumina OLED", "**AMD** FreeSync". Lỗi thật từng gặp:
optimizer chèn `/laptop-acer` đúng vào chữ "Acer" trong "công nghệ Acer
ComfyView" — click vào ra danh mục laptop Acer trong khi người đọc đang đọc tên
một công nghệ màn hình. Chỗ neo hợp lệ: "laptop Acer", "máy Acer", "hãng Acer",
"của Acer", "mẫu Acer".

Optimizer đã tự chặn (bỏ match khi tên hãng đứng ngay trước một từ viết hoa, và
ưu tiên chỗ có `laptop/máy/hãng/của/dòng/mẫu` đứng trước). Hệ quả: hãng nào
trong bài **chỉ** xuất hiện dưới dạng tên công nghệ/tên dòng thì mất link hãng.
Cách sửa là viết thêm một câu nhắc hãng tự nhiên trong `source-content.html` rồi
optimize lại — ví dụ thêm "đặc trưng thiết kế đơn sắc bàn phím trắng của HP" để
có chỗ neo `/laptop-hp` — **không** phải bỏ guard đó đi.

2 SP cùng hãng (vd Acer Aspire Go 15 + Acer Swift AI SF14) → 1 link hãng Acer
(không lặp), + 1 link dòng Aspire + 1 link dòng Swift (khác dòng, khác URL nên
không tính là trùng theo rule 1-link/1-URL).

**Nguồn URL — không tự suy/bịa theo mẫu tên**: dùng
`CUSTOM_LINK_OVERRIDES` trong `content-html-optimizer/scripts/optimize_content.py`
(khớp theo hãng/dòng, laptop workspace) làm nguồn chính — optimizer tự chèn khi
từ "hãng"/"hãng dòng" xuất hiện verbatim trong body. Danh sách này **không phủ
hết mọi dòng SP** — sẽ có thể thiếu dòng gặp trong dự án của bạn. Dòng SP không
có trong danh sách → tra URL thật bằng cách mở category grid tương ứng trên
thegioididong.com (không đoán slug), rồi **tự thêm entry vào
`CUSTOM_LINK_OVERRIDES`** cho lần chạy sau, đừng chỉ vá tay 1 bài rồi bỏ. Không
tìm được URL thật → để trống, báo user, không chèn URL đoán chừng.

Verify sau khi optimize: đọc `metadata/inserted-links-report.json`, đếm theo
hãng/dòng xuất hiện trong `[product ID]` của bài — thiếu cái nào thì tự chèn
tay link đó vào `source-content.html` (đoạn văn tự nhiên, không nhét link trơ
vào cuối câu), rồi optimize lại.

## Box "Xem thêm" — lấy bài liên quan ở đâu

Bài top có **2 box `[info]` Xem thêm**: một sau mục 1 (tiêu chí chọn), một sau
`[Product_Promotion]` cuối bài. Cả hai đều cần **2-3 link bài thật**, không được
để trống và không được bịa URL.

Nguồn duy nhất: Google Sheet **BÀI TIN** (ID qua biến môi trường `SHEET_BAI_TIN_ID`,
cùng biến mà skill `content-html-optimizer` dùng), cột B = `Link air`, C = `Hệ bài`,
D = `Title`, E = `KW mục tiêu`. Đây là danh sách bài hỏi đáp thật đang air (có thể
hàng nghìn dòng tùy quy mô website của bạn). Không tra Google, không suy URL từ
tên bài.

Chạy script để thu hẹp danh sách:

```bash
python3 <path-to>/content-html-optimizer/scripts/suggest_related_articles.py \
  --workspace <workspace-của-bài-này> \
  --terms "laptop sinh viên,laptop học tập,laptop dưới 20 triệu" \
  --he-bai "Top sản phẩm" --top 8
```

- `--terms`: 3-5 cụm chủ đề của bài, cách nhau bằng dấu phẩy. Khớp không dấu cũng
  ăn. Không truyền thì script suy từ tên workspace — kém chính xác, chỉ dùng khi bí.
- `--he-bai`: cộng điểm chứ không lọc cứng. Bài top nên ưu tiên `Top sản phẩm`,
  nhưng vẫn để lọt `Tư vấn chọn mua` vì hai hệ này bổ trợ nhau.
- Script **tự loại** mọi URL đã xuất hiện trong `source-content.html` /
  `final-content.html`, gồm cả chính bài đang viết (nhận diện qua ID cuối slug).

### Anchor phải là TOÀN BỘ tiêu đề

Mỗi dòng trong box là một bài liên quan, nên anchor = **full tiêu đề bài đích**,
kèm `title` đúng bằng tiêu đề đó:

```html
<li><a title="TOP 10 laptop thiết kế đồ họa 3D tốt, đáng mua nhất tại TGDĐ" href="https://www.thegioididong.com/hoi-dap/top-5-mau-laptop-chuyen-do-hoa-3d-tu-hang-dell-asus-hp-1378290" target="_blank" rel="noopener">TOP 10 laptop thiết kế đồ họa 3D tốt, đáng mua nhất tại TGDĐ</a></li>
```

**SAI** — chỉ bọc 1 cụm giữa tiêu đề, phần còn lại text trơ (dạng bài paste từ
CMS hay bị, lỗi thật từng gặp):

```html
<li>Bật mí top <a href="...">8 laptop tốt nhất</a>, bền nhất trên thị trường hiện nay</li>
```

`optimize_content.py` tự nới anchor các `<li>` trong box này ra hết tiêu đề
(log `[XEM THÊM] ... → full tiêu đề`) và không chèn link keyword vào đó nữa.
Dạng inline nhiều link trong 1 thẻ `<p>` thì script chỉ `[WARN]`, phải sửa tay.

Script in ra bảng xếp hạng + khối HTML sẵn (đã đúng format anchor full tiêu đề).
**Không dán cả khối.** Đọc lại tiêu đề, giữ 2-3 dòng thật sự liên quan với bài. Điểm cao chỉ nghĩa là khớp nhiều
chữ, không nghĩa là đáng đọc tiếp — vd bài "laptop cho sinh viên ngành xây dựng"
khớp điểm cao với mọi bài laptop sinh viên nhưng quá hẹp để làm link cuối bài
của một bài top tổng quát.

Vì sao phải có script thay vì tự nhớ: sheet có thể hàng nghìn dòng, tra tay thì
hoặc bỏ sót bài hợp hơn, hoặc lười rồi bịa URL. Một bài top laptop sinh viên
từng bị review bắt lỗi thiếu hẳn box này (lesson #17) đúng vì lúc đó chưa có
cách tra nhanh.

## Thứ tự sản phẩm

Sắp theo điều kiện của bài:
- Bài theo giá → tăng dần theo giá bán thật (`viewed-product-price`).
- Bài theo tính năng/công nghệ → mạnh nhất trước.
- Bài theo đối tượng → phổ thông trước, cao cấp sau.

Sau khi thay SP giữa dự án, **kiểm lại thứ tự** — SP mới thường phá mạch giá.
Thứ tự trong bảng tổng hợp, thứ tự khối H4, `listid` đầu bài, `products` của
`[sosanh]` phải **giống hệt nhau**.

## Shortcode reference

| Shortcode | Cú pháp | Lưu ý |
| --- | --- | --- |
| `[info]` | `[info]` ... `[/info]` mỗi cái 1 thẻ `<p>` riêng | Dùng cho specs, ngày cập nhật, "Xem thêm" |
| `[product]` | `[product ID="334998" Description="none" Display="block"]` | 1 / khối H4 |
| `[Product_Promotion]` | `listid` `categoryid` `manufactureid` `propertyid` `title` | Đúng 2 cái/bài; `categoryid`/`manufactureid`/`propertyid` để rỗng khi đã có `listid` |
| `[sosanh]` | `products` `properties` `categoryid` | ≤7 properties; `categoryid` rỗng hoặc `products` rỗng → mất bảng |

`[sosanh]` hiện giá **động** (real-time) ngay dưới bảng tổng hợp. Vì vậy bảng
tổng hợp ở mục 2 **không cần cột Giá** — giá tĩnh viết cứng trong HTML sẽ lệch
với giá hiển thị qua `[sosanh]` mỗi khi CMS đổi giá, gây khó hiểu cho người đọc.
Bảng tổng hợp chỉ còn 2 cột: Sản phẩm | Điểm mạnh nổi bật (đổi width thành
40%/60%). Áp dụng cả cho dòng "Giá tham khảo" trong specs list `[info]` mỗi
khối H4 — bỏ luôn, vì cùng lý do.

`properties` + `categoryid` theo ngành hàng: lấy runtime từ Google Sheet của
riêng bạn (ID qua biến môi trường `SHEET_SHORTCODE_MAU_ID`), sheet "Shortcode
mẫu (copy dùng luôn)" — tìm dòng có cột B khớp tên ngành hàng (vd "Laptop chơi
game" → dòng 9). Không hardcode.

## Format HTML (theo content-html-optimizer)

- `<h2>`: KHÔNG `<strong>`/`<b>`.
- `<h3>`–`<h6>`: BẮT BUỘC bọc `<strong>`.
- Mọi `<a>`: `target="_blank"` + `rel` chứa `noopener`.
- Table: theo MWG standard (header đen `#000000` / chữ vàng `#ffe14c`,
  `table-layout: fixed`, KHÔNG `min-width`, cột giá `nowrap` `width: 100px`
  (px chứ không phải %), cột giá ưu đãi
  `#d9381e` bold). Optimizer tự chuẩn hóa, không tự viết style tay.
