# Định dạng HTML infobox trên PIM/MDM (trang Hãng, Filter, Dòng filter)

Đo trên bản live 29/10/2026: `/dtdd-apple-iphone-18-series` (filter_inforbox, 181k ký tự) và `/dtdd-apple-iphone` (brand_cate_article, 120k ký tự).
Editor PIM là **CKEditor 5**: tự chuẩn hoá style (sắp xếp thuộc tính, bỏ xuống dòng), nên xuất HTML compact là đủ, không cần đúng thứ tự thuộc tính.
`scripts/dung_html_pim.py` sinh đúng các khối dưới đây, viết tay chỉ khi sửa lẻ.

## Khác với CMS TinyMCE (bài Hỏi Đáp) và PIM sản phẩm

| Điểm | Hãng / Filter / Dòng filter (PIM) | Bài sản phẩm PIM (product_articles) | CMS Hỏi Đáp |
|---|---|---|---|
| Heading bold | CSS tự đậm (H3 18px, H4 16px), KHÔNG cần `<strong>` | bỏ bold H2/H3, H4 bold | theo CMS |
| Bảng | `figure.table` + `border-color:#cccccc` hiển thị viền OK | phải dùng bg-grid | div + table |
| Bullet | `<ul><li>` hiển thị chấm OK | phải thêm list-style disc | OK |
| Ảnh | `figure.image` + `p.titleOfImages` | | `<p><img class="lazy">` |
| Mục lục | core mới tự sinh từ heading, không viết tay | | |
| Số heading | đánh số trong text: H3 "1.", H4 con "1.1." | | H3 "1." |

=> Không áp mấy mẹo của bài sản phẩm PIM (bg-grid, list-style) cho 3 dạng trang này.

## Khối chuẩn

**Sapo**: đúng 1 `<h2>` đầu bài, là câu định nghĩa/tóm tắt (AIO), không link.
```html
<h2>iPhone là dòng điện thoại thông minh do Apple sản xuất, ... Bài viết dưới đây ...</h2>
```

**Heading**: `<h3>1. iPhone 18 giá bao nhiêu tiền?</h3>`, `<h4>1.1. Bảng giá iPhone 18 Pro mới nhất</h4>`.
- H4 trong mục FAQ và H4 trong mục review/chọn mua theo nhu cầu kiểu câu hỏi KHÔNG đánh số.
- Không bọc heading trong `<strong>`, không gắn style.

**Đoạn**: `<p>...</p>` thường. Nhấn ý bằng `<strong>` vừa đủ. Mỗi `<p>` tối đa 4 dòng desktop (~380 ký tự, `kiem_pim.py` báo LỖI từ 400), đoạn dài tách theo ý thành nhiều `<p>`, mỗi đoạn vẫn có số liệu/tên tính năng cụ thể, không cắt thành câu chung chung.

**List**: `<ul><li><strong>Nhãn</strong>: nội dung.</li></ul>` (nhãn trước dấu ":" in đậm, dấu ":" ngoài thẻ).

**Ảnh** (1200x675 ưu tiên, ảnh dọc 800xH):
```html
<figure class="image"><img style="aspect-ratio:1200/675;display:block;margin-left:auto;margin-right:auto;" src="https://cdnv2.tgdd.vn/mwg-static/common/News/0/<file>.jpg" alt="ALT" width="1200" height="675" title="ALT"></figure><p class="titleOfImages" style="color:#777777;font-size:15px;text-align:center;">ALT. Nguồn: Apple</p>
```
- alt = title = caption (40-60 ký tự, theo đoạn ngay trên), caption thêm ". Nguồn: X" (Apple / Thế Giới Di Động / tên trang công nghệ).
- Ảnh dọc: `aspect-ratio:800/H`, `width="800" height="H"`.

**Bảng**:
```html
<div style="-webkit-overflow-scrolling:touch;box-sizing:border-box;margin:16px 0;max-width:100%;overflow-x:auto;width:100%;"><figure class="table" style="max-width:100%;min-width:620px;width:100%;"><table style="border-collapse:collapse;color:#333333;font-size:14px;line-height:1.5;margin:0;table-layout:fixed;"><thead><tr><th style="background-color:#000000;border-color:#cccccc;box-sizing:border-box;color:#ffe14c;overflow-wrap:anywhere;padding:8px 10px;text-align:center;vertical-align:middle;white-space:normal;width:40%;word-break:break-word;"><strong>Phiên bản</strong></th>...</tr></thead><tbody><tr><td style="border-color:#cccccc;box-sizing:border-box;overflow-wrap:anywhere;padding:8px 10px;text-align:left;vertical-align:middle;white-space:normal;word-break:break-word;">...</td><td style="...white-space:nowrap;text-align:center;">38.990.000đ</td></tr></tbody></table></figure></div>
```
- Header nền đen `#000000`, chữ vàng `#ffe14c`, `<strong>`. Cột giá `white-space:nowrap` căn giữa.
- Có `<thead>`/`<tbody>` (CKEditor giữ được, khác TinyMCE).
- Giữa 2 bảng luôn có đoạn văn, không ảnh và không video sát trên/dưới bảng (kiem_pim chặn). Video đầu bài đặt giữa 2 đoạn văn, bảng giá sau đoạn thứ 2.

**Ghi chú ngày cập nhật giá** (ngay sau đoạn/bảng có giá, MỖI LẦN SỬA đổi về hôm nay):
```html
<p><i>Giá iPhone 18 cập nhật ngày 29/10/2026, có thể thay đổi theo thời gian, chi tiết truy cập thegioididong.com hoặc liên hệ hotline </i><a href="tel:1900232460" title="1900 232 460"><i>1900 232 460</i></a><i> để biết thông tin chính xác nhất.</i></p>
```

**Khối Mua (box vàng "Lý do nên mua ... tại Thế Giới Di Động")** đặt trong H3 "Mua ... ở đâu chính hãng, uy tín, giá tốt?", sau 1-3 đoạn văn:
```html
<div style="width:100%;max-width:100%;margin:14px 0;padding:14px 16px;background-color:#fff9e6;border:1px solid #f2c94c;border-left:5px solid #f5b700;border-radius:8px;box-sizing:border-box;color:#222222;font-size:15px;line-height:1.6;"><p style="margin:0 0 10px 0;padding:0 0 8px 0;border-bottom:1.5px solid #ebd27b;font-size:18px;line-height:1.4;font-weight:bold;color:#111111;">Lý do nên mua iPhone tại Thế Giới Di Động</p><ul><li>...</li><li><a title="Hệ thống siêu thị Thế Giới Di Động" href="https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong" target="_blank" rel="noopener">Hệ thống siêu thị Thế Giới Di Động</a> rộng khắp, ...</li></ul></div>
```
Nội dung chuẩn ở `references/mua-tai-tgdd.md` (6-8 dòng, có dòng hệ thống siêu thị). Không viết "giá niêm yết", dùng "giá bán minh bạch".

**Video YouTube** (video Apple ở đầu bài, thêm video review TGDĐ nếu có):
```html
<figure class="media"><div data-oembed-url="https://youtu.be/ID"><div style="position:relative;height:0;padding-bottom:56.2493%;"><iframe src="https://www.youtube.com/embed/ID" style="position:absolute;width:100%;height:100%;top:0;left:0;" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen=""></iframe></div></div></figure>
```

**Kết bài** (sau FAQ, in nghiêng, CTA TGDĐ + hotline):
```html
<p><i>... tham khảo tại <strong>Thế Giới Di Động</strong> hoặc gọi hotline </i><a style="color:#d9381e;text-decoration:none;white-space:nowrap;" href="tel:1900232460"><i><strong>1900 232 460</strong></i></a><i> để được tư vấn ...</i></p>
```

**Box Bài viết liên quan** (cuối cùng, sau kết bài):
```html
<div style="width:100%;max-width:100%;box-sizing:border-box;background-color:#fff9e6;border:1px solid #f2c94c;border-left:5px solid #f5b700;padding:14px 16px;margin:20px 0;border-radius:6px;font-size:14px;line-height:1.6;color:#333333;"><div style="margin:0 0 10px 0;padding-bottom:6px;border-bottom:1.5px solid #ebd27b;font-size:16px;font-weight:bold;color:#111111;display:flex;align-items:center;">📖 Bài viết liên quan đến iPhone 18 Series</div><div style="max-height:260px;overflow-y:auto;-webkit-overflow-scrolling:touch;padding-right:6px;"><ul><li><a style="color:#0066cc;font-weight:500;text-decoration:none;" href="URL" title="TITLE BÀI" target="_blank" rel="noopener">ANCHOR</a></li></ul></div></div>
```
- 6-12 bài Hỏi Đáp/Tin tức TGDĐ cùng chủ đề, mới trước, đều HTTP 200 (lấy bằng `tim_link.py tim`).

## Link
- Link nội bộ: `<a href="https://www.thegioididong.com/..." title="ANCHOR" target="_blank" rel="noopener">ANCHOR</a>`. Rule anchor/vị trí theo `viet-blog/references/chen-link.md` + skill `chen-link-noi-bo` (dạng bài hãng / dòng filter).
- Hotline luôn `tel:1900232460`.

## Field theo màn MDM
| Dạng trang | Screen mdm-cli | Field bài | Title / Meta / KW |
|---|---|---|---|
| Hãng (`/dtdd-apple`, `/dtdd-apple-iphone`) | brand | `brand_cate_article` | `seo_title`, `seo_description`, `seo_keyword` |
| Filter / Dòng filter (giá trị filter) | filter-value | `filter_inforbox` | `title`, `description`, `main_keyword` |
| Hãng + Filter (variant brand-filter) | filter-value | `filter_inforbox` | `title_brand_filter`, `description_brand_filter` (DÙNG CHUNG mọi hãng của giá trị đó, cẩn thận) |


## TopZone (CMS, chưa qua PIM): bài News infobox, format TinyMCE (đo trên 1598413, 29/10/2026)
- H2 sapo `<h2 style="margin: 0 0 10px 0; line-height: 1.6;">`, H3 `style="margin: 20px 0 10px 0;"`, H4 `style="margin: 16px 0 8px 0;"` bọc `<strong>`.
- Đoạn `<p style="margin: 0 0 10px 0; line-height: 1.6;">`, list `<ul style="margin: 0 0 10px 0; padding-left: 18px; line-height: 1.6;">`.
- Ảnh `<p><img style="display: block; margin-left: auto; margin-right: auto;" title alt src width height /></p>` + `<p class="titleOfImages"
  style="font-size: 15px; color: #777777; text-align: center;">… Nguồn: X</p>`.
- Bảng: div cuộn ngang + `<table>` viền `1px solid #cccccc`, `th` in đậm KHÔNG tô nền/màu chữ.
- Video: div `padding-bottom: 56.25%` + iframe YouTube.
- Mua: H3 "Mua <dòng> tại TopZone" + đoạn văn + `<ul>` "Cửa hàng trực tuyến: topzone.vn" (trang chủ) / "Hotline tư vấn và hỗ trợ khách hàng:
  1900.9696.42 (8:00 - 21:30)". Không box vàng "Lý do nên mua".
- Ghi chú giá + kết bài: `<p ...><em>…</em></p>`, hotline `<a style="font-weight: bold; text-decoration: none; white-space: nowrap;" href="tel:1900969642">`.
- Cuối bài: box viền xám "Xem thêm các bài viết liên quan" (link topzone.vn/tekzone).
- Dựng bằng `dung_html_pim.py` (tự nhận site TopZone từ bai.json), lint `kiem_pim.py` (chặn màu, link site khác, chữ Thế Giới Di Động).
