# Ưu Đãi Tại TGDĐ

## Mục tiêu

Viết block HTML cho H3 dạng `Ưu đãi khi mua [sản phẩm/ngành hàng] tại Thế Giới Di Động`, dùng cho bài SEO Apple/TGDD. Mục này tập trung nêu các chương trình khuyến mãi nổi bật theo ngành hàng đang nói đến, không viết riêng cho một sản phẩm nếu heading đang nói chung.

## Khi sử dụng

Đọc reference này khi người dùng yêu cầu viết hoặc chỉnh H3 dạng:

- `Ưu đãi khi mua iPhone tại Thế Giới Di Động`
- `Ưu đãi khi mua [sản phẩm Apple] tại TGDĐ`
- Các biến thể tương tự về ưu đãi, khuyến mãi, giảm giá khi mua sản phẩm Apple tại Thế Giới Di Động.

## Cách xử lý

1. Xác định ngành hàng/sản phẩm chính từ heading hoặc ngữ cảnh gần nhất, ví dụ: iPhone, iPhone 17 Series, iPhone Air, iPad, MacBook, Apple Watch, AirPods.
2. Nếu người dùng gửi link một sản phẩm có ưu đãi cao để tham khảo, chỉ dùng link đó để lấy mức ưu đãi hấp dẫn đưa vào bài chung; không biến toàn bộ mục thành nội dung riêng cho sản phẩm đó, trừ khi heading yêu cầu riêng.
3. Viết câu dẫn phù hợp với ngành hàng đang nói đến. Ví dụ với iPhone: `Khi mua iPhone tại thegioididong.com...`.
4. Anchor `thegioididong.com` luôn trỏ về `https://www.thegioididong.com/`, mở tab mới bằng `target="_blank"` và `rel="noopener"`.
5. Danh sách ưu đãi dùng `<ul>` và `<li>` sạch. Mỗi bullet nêu một ưu đãi rõ ràng, có `<strong>` ở cụm chính.
6. Với mức giảm/ưu đãi, luôn dùng cách diễn đạt an toàn: `giảm đến ...`, `ưu đãi đến ...`, `trị giá đến ...`, `tùy phiên bản`, `tùy chương trình`, `theo điều kiện áp dụng`.
7. Không tự bịa giá, mã giảm, mức voucher, ngày cập nhật hoặc điều kiện chương trình. Chỉ dùng con số người dùng cung cấp hoặc vừa kiểm tra từ trang sản phẩm.
8. Nếu CMS/TinyMCE đang tự thêm `<p>&nbsp;</p>`, xuất HTML minified một dòng, không xuống dòng giữa các block.
9. Nếu người dùng đang dùng HTML entities trong mẫu, có thể encode tiếng Việt thành entities để đồng bộ; nếu không, dùng tiếng Việt có dấu trực tiếp vẫn được.
10. Đoạn cuối luôn là ghi chú in nghiêng về thời điểm cập nhật và khả năng thay đổi ưu đãi.

## Mẫu Chuẩn Theo Người Dùng

Khi viết cho iPhone, giữ cấu trúc này và chỉ thay câu dẫn + các khuyến mãi cho phù hợp với ngành hàng/sản phẩm đang nói đến:

```html
<p style="margin: 0 0 8px 0!important; padding: 0!important; line-height: 1.5!important;">Khi mua iPhone tại <a href="https://www.thegioididong.com/" target="_blank" rel="noopener">thegioididong.com</a>, bạn có thể nhận nhiều ưu đãi hấp dẫn theo từng phiên bản và thời điểm mua hàng. Các chương trình thường gặp gồm <strong>giảm giá trực tiếp, trả góp 0% lãi suất, thu cũ đổi mới</strong> và hỗ trợ bảo hành chính hãng.</p>
<ul>
<li><strong>Ưu đãi giá trị đến 9,5 triệu đồng</strong>: một số phiên bản iPhone có thể được giảm sâu tùy dung lượng, màu sắc và chương trình áp dụng tại từng thời điểm.</li>
<li><strong>Giảm trực tiếp đến 5,5 triệu đồng</strong> cho một số phiên bản iPhone tùy chương trình khuyến mãi, khu vực và tình trạng hàng.</li>
<li><strong>Trả góp 0% lãi suất</strong>: hỗ trợ mua iPhone với hình thức trả góp hoặc trả chậm, giúp giảm áp lực thanh toán ban đầu theo điều kiện áp dụng.</li>
<li><strong>Thu cũ đổi mới giảm đến 2 triệu đồng</strong> tùy chương trình, tình trạng máy cũ và model iPhone người dùng chọn mua.</li>
<li><strong>Hư gì đổi nấy đến 12 tháng</strong>: hỗ trợ đổi sản phẩm theo chính sách áp dụng, trong đó tháng đầu có thể được hỗ trợ miễn phí theo điều kiện của chương trình.</li>
<li><strong>Bảo hành chính hãng điện thoại 1 năm</strong> tại các trung tâm bảo hành hãng, giúp người mua yên tâm hơn trong quá trình sử dụng.</li>
<li><strong>Giao hàng tận nơi hoặc nhận tại siêu thị</strong>: người mua có thể kiểm tra tình trạng hàng theo khu vực và chọn hình thức nhận máy phù hợp.</li>
</ul>
<p style="margin: 0 0 8px 0!important; padding: 0!important; line-height: 1.5!important;"><em>(Ưu đãi được cập nhật ngày [NGÀY_CẬP_NHẬT]. Mức ưu đãi cụ thể có thể thay đổi tùy phiên bản iPhone, thời điểm mua hàng, khu vực và điều kiện của từng chương trình.)</em></p>
```

## Lưu ý theo ngành hàng

- Với iPhone: có thể nhắc giảm giá trực tiếp, trả góp 0%, thu cũ đổi mới, hư gì đổi nấy đến 12 tháng, bảo hành chính hãng điện thoại 1 năm, giao hàng/nhận tại siêu thị.
- Với iPad/MacBook: điều chỉnh `bảo hành chính hãng` theo sản phẩm, không ghi `điện thoại 1 năm` nếu không phải điện thoại.
- Với Apple Watch/AirPods/phụ kiện: không dùng `thu cũ đổi mới` hoặc `hư gì đổi nấy 12 tháng` nếu không có thông tin áp dụng rõ.
