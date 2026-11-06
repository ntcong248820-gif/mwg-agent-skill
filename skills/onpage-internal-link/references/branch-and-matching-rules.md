# Phân nhánh + khớp keyword (port từ node 6, 8c, 9b, 9c của n8n Onpage Ver 2)

`scripts/analyze_article.py` đã cài các rule máy ở mục 1–4. Mục 5–6 là phần Claude phán.
Khi phân tích tay (không chạy được script) thì làm đúng các rule này.

## 1. Bóc thân bài

Container, lấy cái đầu tiên có > 200 ký tự (cắt theo `<div>` cân bằng, không regex non-greedy):

| Site | Thứ tự |
| --- | --- |
| TGDĐ, TopZone | `detail-content` → `warpper-content` → `article-content` → `contentnews` → `divContent` → `contentpost` → `content-article` |
| ĐMX | `contentnews` → `divContent` → rồi như trên |

**Không fallback về `<article>` hay cả trang** — `article.pagedetail` bao cả khối bài liên quan cuối trang.
Trượt hết → `extract_ok = false`, báo fail.

Sau khi lấy container:

1. **Cắt đầu từ `<h1>`** (bỏ breadcrumb). Không có H1 thì xoá `ul.breadcrumb`.
2. **Cắt đuôi** từ khối widget sớm nhất: `boxRatingNew`, `boxreviewcontentv2`, `reviewcontentV2`, `kwLst`
   (danh sách thẻ Từ khoá), `askrelate`, `cookie-found`, `likeshare`, `articleview`, `rowcount`.
3. **Xoá tại chỗ** hộp `div.infobox` có nội dung bắt đầu bằng `Xem thêm:` (hộp này nằm được giữa bài; cắt từ đó trở đi là mất nửa bài).
4. Xoá tiêu đề listing `<b class="tlt">` đứng ngay trước `boxpromote`.
5. Xoá khối: `boxpromote`, `banner-detail`, `set_table`, `box-relative`, `rowuser`, `promo`, `listproduct`, `shortcodeGA`/`shorcodeGA`.

Bóc thẻ HTML ra text: regex phải nhảy qua giá trị trong nháy (`title="Vào AppStore > Đăng ký"`),
nếu không nửa sau thẻ `<img>` rơi ra thành chữ và `<p>` chỉ có ảnh bị tưởng là đoạn văn.

## 2. Hai vùng khác nhau — đừng dùng lẫn

| Vùng | Giữ | Bỏ | Dùng cho |
| --- | --- | --- | --- |
| **Nhận diện** | sapo, heading, infobox | bảng, `<p>` căn giữa có ảnh/link | dò link có sẵn, dò keyword có sẵn |
| **Chọn đoạn mốc** | thân bài từ heading đầu tiên trở đi | sapo, heading, caption (`text-align:center`, `color:#777`, trùng alt ảnh), bảng, infobox | chọn chỗ chèn câu mới |

Sapo TGDĐ bọc trong `<h2>`: xoá heading ở vùng nhận diện là mất link trong sapo → báo nhầm "chưa có link" → chèn trùng.

## 3. Dò link đã có

- Bỏ: link có class (`postarticle`, nút, box), shortcode `[product ...]`, `pro-1sp/2sp/moresp/container`,
  `<a>` chỉ bọc ảnh, `tel:`/`mailto:`/`#`, link có `itm_medium|itm_source|itm_campaign`.
- So URL đích: bằng nhau sau khi bỏ `/` cuối và lowercase, hoặc bắt đầu bằng `{đích}/` hay `{đích}?`,
  **hoặc cùng host + cùng tập token path** (bắt bản redirect: `/laptop-apple-macbook-macbook-neo` ≡ `/laptop-apple-macbook-neo`).
- Có link → anchor đúng khi chứa keyword **đứng độc lập** (mục 4, bản `standalone`). "HONOR 600" không khớp anchor "HONOR 600 Lite".
- Anchor rộng hơn kiểu "iPhone 16 thường" trỏ đúng URL vẫn tính **đạt**, không bắt sửa.

## 4. Keyword "đứng độc lập"

**standalone** (dùng so anchor có sẵn):
- Trước keyword không phải chữ/số.
- Sau keyword **không** là một từ ASCII trọn vẹn: `Pro`, `Max`, `Plus`, `Lite`, `Ultra`, `256GB`… (đó là model khác).
  Kiểm "trọn vẹn" để không chặn oan "gi" trong "giá", "kh" trong "không".

**anchorable** (dùng khi chọn chỗ gắn link, khắt khe hơn) = standalone + chặn hậu tố biến thể có dấu:
`thường`, `tiêu chuẩn`, `bản thường`, `bản tiêu chuẩn`. Ngoại lệ: `thường xuyên|được|bị|thấy|gặp|dùng|sử dụng|xảy|phải|hay` là trạng từ, vẫn hợp lệ.
Gặp hậu tố biến thể mới thì bổ sung vào `VARIANT_SUFFIX` trong script.

Không gắn link vào chữ **đang nằm trong `<a>`** (link lồng link làm hỏng CMS). Script dùng bản text đã che chữ trong `<a>` bằng `·` để so theo vị trí.

## 5. Câu gắn link được (nhánh insertText)

Script đã lọc:
- Câu < 25 ký tự; câu promo (`tham khảo các/ngay/thêm`, `xem thêm`, `mời bạn`, `đừng bỏ lỡ`, `mua ngay`, `trả góp`…);
  câu dẫn kết thúc bằng `:` (dẫn vào list/listing).
- Câu có biến thể dài hơn (`has_longer_variant`) bị xếp xuống cuối, tối đa 8 câu.

Claude làm tiếp (thay node 8c + 9c):
1. Đọc từng câu, loại câu mà keyword là **một phần của tên gọi dài hơn**. Phán bằng ngữ nghĩa, không chắc thì loại.
   - "iPhone 16 thường đã ra mắt" (kw iPhone 16) → loại.
   - "iPhone 17 Pro Max có camera mới" (kw iPhone 17 Pro) → loại.
   - "MacBook Neo dùng chip A18 Pro" (kw MacBook) → loại.
   - "iPhone 16 có giá tốt hơn bản tiền nhiệm" → giữ.
2. Bỏ câu `in_infobox`.
3. Chọn 1 câu: thân bài, ngữ cảnh liên quan sản phẩm; tránh tiêu đề, chú thích ảnh, lời kêu gọi mua.
   Batch nhiều dòng thì cân vị trí theo quota ở `natural-mention-and-placement.md`.
4. **Không bịa câu, không sửa chữ nào** — H phải trùng nguyên văn bài (plain text, giữ case gốc).
5. Không còn câu → chuyển `newContent`.

## 6. Sửa anchor (nhánh fixAnchor, thay node 9b + 10b)

Input: `existing_anchor_text`, `anchor_sentence` (câu chứa link; rỗng nếu link nằm trong khối danh sách link điều hướng —
≥ 12 link, hoặc 3+ link chiếm > 70% chữ).

Anchor mới hợp lệ khi:
- Chứa keyword đứng độc lập, đúng chữ và thứ tự từ (hoa/thường được sửa theo quy ước hãng).
- Cụm danh từ ngắn; không `và/hoặc/cùng/hay`; không `, ; . : ! ?`; keyword chỉ xuất hiện 1 lần; dài ≤ keyword + 24 ký tự.
- Không lặp với từ đứng ngay trước (câu "…điện thoại [điện thoại iPhone 17]" là lặp).
- Không hợp lệ → anchor mới = keyword.

Output:
- Thay anchor cũ trong câu bằng anchor mới, gỡ cụm lặp liền kề, chuẩn dấu câu.
- Keyword đã có ở chỗ khác trong câu (ngoài anchor cũ) **hoặc** `anchor_sentence` rỗng → H = anchor cũ, I = anchor mới.
- Ngược lại H = câu cũ, I = câu mới (viết hoa đầu câu chỉ khi câu gốc vốn viết hoa đầu).
- C = `Infobox` nếu link nằm trong infobox, còn lại `Đoạn văn`. J = `Thay đoạn cũ`.

## 7. Nhiều keyword trong 1 dòng plan

- Ô A/B tách theo dòng, ghép cặp theo thứ tự (lấy min số dòng của 2 ô).
- Mỗi cặp phân nhánh riêng. Cặp `ok` không sinh dòng WF. Cặp cùng nhánh gộp 1 dòng WF: E = các `keyword_display` ngăn `\n`, F = các URL ngăn `\n`.
- Nhánh newContent nhiều keyword: nhắc **đủ tất cả trong cùng một câu**.
  Quan hệ cha–con (một keyword là tiền tố của các keyword còn lại): viết "các dòng MacBook như MacBook Neo hoặc MacBook Air",
  không viết "MacBook và MacBook Neo" như hai sản phẩm ngang hàng.
- Ghi plan: tất cả cặp `ok` → `Đã đúng guideline`; còn lại → `Done`.
