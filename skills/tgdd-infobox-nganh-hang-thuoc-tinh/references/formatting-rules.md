# Quy tắc cấu trúc và định dạng

## Heading theo CMS Type 3

- Sapo dùng H2.
- Section chính dùng H3.
- Heading con và câu hỏi FAQ dùng H4.
- Không dùng H1.

## Chọn đúng dạng trình bày

- Dùng đoạn văn để giải thích nguyên nhân, tác động và nhận định.
- Dùng checklist khi có nhiều ý độc lập cần quét nhanh.
- Dùng bảng khi các đối tượng cần so sánh theo cùng bộ tiêu chí.
- Không xếp nhiều đoạn ngắn với nhãn in đậm để giả làm danh sách nếu checklist sẽ rõ hơn.

## Section có checklist hoặc bảng

Mỗi section phải đủ ba phần:

1. Dẫn đoạn tối thiểu 2 câu: đặt bối cảnh và giải thích vì sao danh sách ảnh hưởng đến lựa chọn.
2. Checklist hoặc bảng.
3. Kết đoạn 1-2 câu: giúp người đọc hiểu nên ưu tiên gì.

Không kết thúc section ngay sau bullet hoặc hàng cuối của bảng.

## Section “Tại sao nên...”

Section này (ví dụ: "Tại sao nên sử dụng...", "Tại sao nên mua...", "Tại sao nên chọn...") giải thích các lợi ích cốt lõi của ngành hàng hoặc dòng sản phẩm.

1. **Mỗi lợi ích / tiêu chí con BẮT BUỘC PHẢI là một heading con H4 riêng** (`#### [Tên lợi ích]` trong Markdown hoặc `<h4>[Tên lợi ích]</h4>` trong HTML).
2. **TUYỆT ĐỐI KHÔNG** dùng nhãn in đậm (`**...**` hoặc `<p><strong>...</strong></p>`) để giả làm heading. Việc dùng H4 là bắt buộc để:
   - Chuẩn cấu trúc ngữ nghĩa (semantic heading) CMS và mục lục (TOC).
   - Đảm bảo quy tắc phủ hình AI (`image-ai-generate`) tự động quét trúng từng H4 lá và tạo hình ảnh AI riêng biệt cho từng mục con này.
3. Mỗi H4 giải thích tối thiểu khoảng 3 câu:
   - Nêu cơ chế hoặc lý do tính năng tạo ra lợi ích.
   - Nêu tác động thực tế với người dùng.
   - Nêu điều kiện, ví dụ hoặc giới hạn để tránh khẳng định chung chung.

Ví dụ cấu trúc chuẩn:

```markdown
#### Hạn chế sai sót khi tính tiền

Mỗi sản phẩm được ghi nhận trên phần mềm trước khi hóa đơn được in, nên nhân viên không phải chép lại tên hàng, số lượng và giá bán. Dữ liệu được tổng hợp theo cùng một đơn giúp giảm nguy cơ bỏ sót mặt hàng hoặc cộng nhầm tổng tiền. Lợi ích này phát huy tốt khi thông tin sản phẩm và giá trong phần mềm đã được thiết lập chính xác.
```

## Section "Các loại ... phổ biến"

Đây là section phân loại sản phẩm, không phải section thương hiệu.

1. Chọn đúng MỘT tiêu chí phân loại và giữ nhất quán cả section: kiểu thiết
   kế, nền tảng/hệ điều hành, công nghệ, kích thước, hoặc cách sử dụng. Ví dụ
   với màn hình: màn hình phẳng, màn hình cong, màn hình di động. Không trộn
   nhiều tiêu chí trong cùng một danh sách.
2. **Mỗi loại là một heading con (H4) riêng**, không gom thành checklist một
   bullet mỗi loại. Đặt tên H4 đúng bằng tên loại, ví dụ "Máy in laser trắng
   đen", "Máy in phun màu", "Máy in nhiệt".

   Lý do: một bullet chỉ chứa được 2-3 câu nên mọi loại đều bị nén xuống mức
   "đặc điểm + phù hợp với ai", trong khi người đọc đang ở bước chọn công nghệ
   cần biết cả cách hoạt động, chi phí vận hành và giới hạn thật của từng loại.
   H4 riêng cho phép viết đủ chiều sâu và cho mỗi loại một mục trong mục lục.

3. Mỗi H4 loại sản phẩm viết 2-4 đoạn, trả lời đủ bốn câu hỏi theo thứ tự:

   - Loại này hoạt động thế nào, nói bằng ngôn ngữ đời thường.
   - Điểm mạnh thật khi dùng hằng ngày.
   - Giới hạn hoặc chi phí phải chấp nhận.
   - Ai nên chọn, ai nên bỏ qua.

   Không viết H4 chỉ 1-2 câu. Nếu một loại không đủ nội dung cho 2 đoạn thì
   nó không đáng đứng riêng một H4, hãy gộp vào loại gần nhất.

4. Không nêu tên thương hiệu, model hay giá trong section này. Thương hiệu
   thuộc section "Các thương hiệu ... phổ biến"; model và giá thuộc section
   sản phẩm nổi bật.
5. Giữ 2 câu dẫn trước loạt H4 và 1-2 câu kết sau loạt H4. Câu kết nên chỉ ra
   quyết định thực tế mà phần lớn người mua phải chọn giữa hai loại phổ biến
   nhất, thay vì tóm lại toàn bộ danh sách.

## Section "Nên chọn ... theo nhu cầu?"

Không viết section này thành một đoạn văn dài gộp mọi nhu cầu.

1. Mỗi nhu cầu là một heading con (H4) riêng, đặt tên theo nhu cầu thật:
   "{Ngành hàng} cho văn phòng và học tập", "... cho chơi game", "... cho
   giải trí", "... cho thiết kế đồ họa".
2. Chọn 4-6 nhu cầu phổ biến nhất, đúng với ngành hàng đang viết.
3. Mỗi H4 viết 2-4 câu: đặc điểm/cấu hình sản phẩm phù hợp với nhu cầu đó,
   tác động thực tế, và giới hạn khi có.
4. Nói đặc điểm sản phẩm phù hợp, không nói model cụ thể.

## Section "Các thương hiệu ... phổ biến"

Section này **chỉ có 3 khối: dẫn đoạn, bảng, kết đoạn**. Không tách heading con
cho từng hãng.

1. Dẫn đoạn 2-3 câu: bối cảnh thị trường và vì sao định vị của hãng ảnh hưởng
   tới lựa chọn, cộng 1 câu dẫn trước bảng theo mục "Simple lead-in before
   tables".
2. Một bảng tổng hợp, mỗi hãng (hoặc nhóm hãng cùng định vị) một dòng, ví dụ
   cột: Thương hiệu, Đặc điểm nổi bật, Phù hợp với.
3. Kết đoạn 2-4 câu: nêu điểm khác biệt lớn nhất giữa các nhóm hãng và cách
   người đọc chọn theo nhu cầu. Đây là chỗ duy nhất diễn giải thêm bằng văn
   xuôi, và cùng với dẫn đoạn là nơi chèn internal link brand/dòng máy — xem
   "Internal link cho tên hãng / dòng máy trong section này" ngay bên dưới.

**Không viết mỗi thương hiệu thành một H4 riêng.** Bảng đã nêu đủ đặc điểm và
nhóm người dùng phù hợp của từng hãng; thêm 4-7 H4 mỗi cái một đoạn chỉ diễn
đạt lại đúng nội dung bảng bằng văn xuôi, làm section dài ra mà không thêm
thông tin, và đẩy các section quyết định mua hàng xuống dưới.

Các rule còn giữ nguyên:

- Liệt kê đủ các hãng thật sự đáng kể của ngành hàng, không dừng ở 2-3 hãng
  đầu tiên nghĩ ra và không dừng ở các hãng có trong danh mục. Rà lại theo các
  nhóm sau trước khi chốt danh sách: hãng máy tính/thiết bị lâu năm, hãng linh
  kiện, hãng chuyên làm riêng phân khúc đó, hãng nội địa Việt Nam, và hãng sở
  hữu nền tảng riêng.
- Khi ngành hàng có nhiều hãng, gộp các hãng cùng định vị thành **một dòng
  bảng** theo nhóm (ví dụ "MSI, GIGABYTE, ASRock và ZOTAC") thay vì bỏ bớt
  hãng. Giữ khoảng 4-7 dòng để bảng không bị loãng.
- Không nêu model hay giá cụ thể ở section này. Tên dòng sản phẩm quen thuộc
  của hãng thì được, vì nó giúp người đọc nhận ra hãng.
- Không xếp hạng hãng.

Bảng luôn đứng giữa dẫn đoạn và kết đoạn, không đặt ở cuối section.

### Internal link cho tên hãng / dòng máy trong section này

Bài audit `260916-infobox-laptop-do-hoa-ky-thuat` từng giao section này mà
**không có link nào** cho hãng/dòng máy — chờ bước `content-html-optimizer`
sau đó không xử lý category link kiểu này (nó chỉ chèn theo Sheet "All KW" và
"BÀI TIN", không tự tìm URL danh mục con của từng hãng). Vì vậy section này có
ngoại lệ riêng, khác với internal link SEO chèn ở bước optimizer:

- Được chèn link tay ngay khi viết draft — đây là ngoại lệ thứ hai của quy tắc
  "không chèn link bằng tay khi đang viết draft" (ngoại lệ thứ nhất là cột tên
  sản phẩm ở bảng "Các sản phẩm ... nổi bật").
- **Bắt buộc verify URL thật trước khi chèn**, không suy đoán và không lấy từ
  trí nhớ:
  ```bash
  curl -s -o /dev/null -w "%{http_code} %{redirect_url}\n" -m 15 -A "Mozilla/5.0" \
    "https://www.thegioididong.com/{slug}"
  ```
  Chỉ dùng URL trả về `200`. URL trả `302` về một trang khác (ví dụ về
  `/laptop` chung hoặc về danh mục hãng cha) nghĩa là slug không tồn tại —
  dùng URL hãng chung (`/laptop-{brand}`) thay thế, không tự suy
  `/laptop-{brand}-{dòng}` rồi chèn mà không kiểm tra trước.
- Đặt link ở dẫn đoạn hoặc kết đoạn (văn xuôi), **không đặt trong ô bảng** —
  bảng của section này không nằm trong ngoại lệ chèn-link-trong-`<table>`
  (ngoại lệ đó chỉ áp cho cột tên sản phẩm ở bảng sản phẩm nổi bật).
- Mỗi URL chỉ chèn 1 lần trong toàn bài. Nếu một hãng đã có link ở dẫn đoạn
  (URL cấp hãng), không chèn lại đúng URL đó ở kết đoạn — kết đoạn nên link
  sang dòng máy cụ thể của hãng đó (URL khác, cấp con) thay vì lặp URL cấp
  hãng.
- Không bắt buộc chèn đủ link cho mọi hãng nếu bảng liệt kê 7-8+ hãng; ưu tiên
  chèn cho các hãng/dòng máy được nhắc tên rõ nhất trong câu văn.

## Section "Các sản phẩm ... nổi bật tại Thế Giới Di Động"

1. Chọn khoảng 5 sản phẩm có số bán cao nhất trong URL danh mục. Dùng số đã
   bán hiển thị trên trang danh mục làm căn cứ, không tự suy đoán.
2. Khi nhiều sản phẩm bán chạy chỉ là các phiên bản gần trùng nhau của cùng
   một dòng, giữ 1-2 phiên bản tiêu biểu và thay phần còn lại bằng sản phẩm
   bán chạy nhất của nhóm hoặc nền tảng khác, để bảng phủ được các lựa chọn
   chính của ngành hàng thay vì lặp lại một dòng.
3. Trình bày bằng bảng, tối thiểu 3 cột: tên sản phẩm, thông số chính, giá
   bán. Sắp xếp theo giá tăng dần để người đọc quét nhanh theo ngân sách.
4. Chỉ điền thông số và giá đọc được từ danh mục hoặc trang chi tiết sản
   phẩm. Không bịa, không làm tròn khác con số thật.
5. Giữ 1 câu dẫn trước bảng và 1-2 câu kết sau bảng.
6. Đây là chỗ duy nhất nêu phạm vi thương hiệu TGDĐ đang kinh doanh, viết
   gọn trong 1 câu.

## Section “Những sai lầm thường gặp”

Viết 2 câu dẫn, sau đó dùng checklist theo mẫu:

```markdown
- **[Sai lầm]:** [Hậu quả]. [Cách tránh hoặc cách kiểm tra].
```

Không tách từng sai lầm thành heading có một đoạn ngắn. Kết section bằng 1-2 câu nêu thứ tự ưu tiên khi kiểm tra.

## Đoạn văn

- Mỗi đoạn nên có 2-4 câu vừa phải.
- Một heading không dùng checklist hoặc bảng cần chiều sâu tương đương khoảng 4 câu, có thể chia thành 1-2 đoạn.
- Không kéo dài bằng câu lặp hoặc câu quảng cáo chung chung.

## FAQ

- Mỗi câu hỏi là heading con theo cấp được quy định trong `outline.md`.
- Câu trả lời là đoạn văn ngay bên dưới, không dùng bullet con.
- Trả lời trực tiếp trước, sau đó giải thích điều kiện hoặc ví dụ.
- Ưu tiên câu hỏi ảnh hưởng đến quyết định mua, khả năng tương thích, cách chọn và chính sách.

## Simple lead-in before tables - latest rule

This rule overrides the earlier requirement for a minimum two-sentence lead before a table.

- Use one direct, reader-facing sentence before a comparison table.
- Preferred pattern: "De hieu ro hon ve su khac nhau giua ..., cac ban co the tham khao bang duoi day:"
- Adapt the subject naturally to the category and write the final sentence in Vietnamese with diacritics.
- Do not describe editorial decisions such as "the table focuses on...", "price is not used as a criterion", or "the data below represents...".
- After the table, add 1-2 concise sentences that help the reader choose or identify the main difference.

## Do not repeat headings for the same product group

The brand section and the highlighted-products section are allowed to sit next
to each other because they answer different questions: the first is about brand
positioning in the market, the second is about which specific products are on
sale. Keep them distinct rather than merging them.

- Before writing, compare the intent of all planned headings. Merge only headings that answer the same purchase question.
- Do not describe the same product group twice with the same intent. If a section only restates what an earlier section already said, delete it.
- Do not put brand names in the classification section, and do not put model names or prices in the brand section — mixing them is what makes the article read as repetitive.
- If product differences were already covered sufficiently in a needs-based section, do not repeat the same explanations in a later section; refer to the criterion briefly instead.

## CTA checklist format

- Use only the main CTA section heading.
- Inside the CTA, use a short lead plus checklist bullets with bold labels; do not use smaller headings for each benefit.
- The general table/checklist lead rules do not force a long lead for this CTA. Keep it compact.

## Bảng sản phẩm tại TGDĐ: tên sản phẩm phải là link về trang sản phẩm

Trong section `Các sản phẩm ... tại Thế Giới Di Động`, mọi ô ở **cột tên sản
phẩm** phải được bọc link trỏ về **đúng trang chi tiết của chính sản phẩm đó**.
Người đọc bảng để so, rồi click để mua — bảng không có link là cắt đúng bước đó.

Đây là **ngoại lệ** của quy tắc "không chèn link trong `<table>`". Ngoại lệ chỉ
áp cho cột tên sản phẩm của bảng liệt kê sản phẩm, không mở cho cột nào khác và
không mở cho bảng khác (bảng thông số, bảng so sánh dòng con...).

### Lấy URL ở đâu

**Không** lấy từ Sheet keyword. Trang chi tiết sản phẩm (SKU) không nằm trong
Sheet đó — Sheet chỉ có URL danh mục và URL bài viết. Lấy trực tiếp từ **trang
danh mục** đang viết:

```bash
curl -s -m 30 -A "Mozilla/5.0" "https://www.thegioididong.com/{category-slug}" -o /tmp/cat.html
```

Trong HTML danh mục, mỗi sản phẩm là một khối có `data-name` (tên đầy đủ kèm mã
SKU) và thẻ `<a href='/laptop/...'>` — **href dùng dấu nháy đơn**, nên regex viết
theo `"` sẽ trượt hết. Ghép SKU trong `data-name` với `href` để ra URL.

Mã SKU theo hãng có độ dài khác nhau — đếm lại trước khi viết regex, đừng đoán:

| Dạng | Ví dụ | Regex |
| --- | --- | --- |
| Lenovo | `83M0002YVN` | `83[A-Z0-9]{6}VN` |
| Acer | `NH.QVYSV.001` | `NH\.[A-Z0-9]{5}\.\d{3}` |

Đếm sai một ký tự thì regex trả 0 kết quả và trông y như "danh mục không có sản
phẩm nào" — đã xảy ra thật với cả hai dạng trên.

### Ràng buộc

- Link phải là URL thật đọc được từ trang danh mục. **Không suy URL từ mã SKU.**
- Mỗi sản phẩm link về đúng trang của nó; không dồn nhiều sản phẩm về một URL.
- Anchor là **toàn bộ tên sản phẩm trong ô**, kèm mã SKU nếu ô có mã. Không cắt lẻ.
- Dùng `rel="noopener noreferrer" target="_blank"` như mọi link khác trong bài.
- Rule "1 URL 1 link" của internal link **không** áp cho các link này: đây là link
  sản phẩm, mỗi dòng một URL riêng nên không có chuyện trùng.
- Bước này `content-html-optimizer` **không tự làm** — script vẫn chặn link trong
  `<table>`. Phải làm thủ công, xem mục "product listing table" của skill đó.

### Lấy URL thì lấy luôn giá

Trang danh mục có sẵn giá hiển thị, nên đọc luôn trong cùng lượt curl và đối
chiếu với cột giá trong bảng. Giá hiển thị nằm ở `class="price"`; khi sản phẩm
đang giảm thì có 2 giá, **giá đầu là giá bán, giá sau là giá gạch** — lấy giá
đầu. Không dùng `data-price`: đó là giá gốc chưa giảm, lệch tới hàng chục triệu.
Giá lệch thì sửa số **và** sửa luôn mốc ngày cập nhật trong bài.
