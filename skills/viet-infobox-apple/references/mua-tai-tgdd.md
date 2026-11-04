# Mua Tại TGDĐ

## Mục tiêu

Viết một block HTML hoàn chỉnh cho phần H3 về nơi mua sản phẩm Apple chính hãng, uy tín, giá tốt tại Thế Giới Di Động. Dựa trên mẫu gốc của người dùng, nhưng tinh chỉnh tự nhiên theo đúng sản phẩm, dòng sản phẩm, thương hiệu và ngữ cảnh bài viết Apple.

## Khi sử dụng

Đọc reference này khi người dùng yêu cầu viết hoặc chỉnh H3 dạng:

- `Mua ... ở đâu chính hãng, uy tín, giá tốt?`
- `Mua ... chính hãng, uy tín, giá tốt tại TGDĐ`
- Các biến thể tương tự có ý định hỏi nơi mua sản phẩm Apple tại Thế Giới Di Động.

## Cách xử lý

1. Xác định sản phẩm/dòng sản phẩm từ H3 hoặc ngữ cảnh gần nhất, ví dụ: iPhone 17 Series, iPad Air, MacBook Air M4, Apple Watch, AirPods.
2. Với sản phẩm Apple, có thể dùng cụm `đại lý ủy quyền của Apple tại Việt Nam` nếu ngữ cảnh đang nói về mua sản phẩm Apple chính hãng.
3. Không rút gọn block này quá mức. Đây là phần CTA mua hàng quan trọng, cần viết đủ chi tiết theo mẫu tham khảo của người dùng: 3 đoạn mở đầu, 1 box lý do mua gồm 6-8 bullet và 1 đoạn kênh đặt mua kèm danh sách kênh.
4. Nếu ngữ cảnh đã xác định được dòng sản phẩm cụ thể như `iPhone 17 Series`, phải gọi đúng tên dòng sản phẩm trong các đoạn chính, tiêu đề box, CTA và link. Không đổi thành tên quá chung như `iPhone` nếu người dùng đang nói về một series cụ thể.
5. Với dòng sản phẩm/series đang bán tại TGDĐ, ưu tiên nêu cụ thể các phiên bản TGDĐ đang có trong đoạn 2 và bullet lựa chọn sản phẩm. Ví dụ với iPhone 16 Series: `iPhone 16, iPhone 16 Plus, iPhone 16 Pro, iPhone 16 Pro Max và iPhone 16e`; với iPhone 17 Series: `iPhone 17e, iPhone 17, iPhone 17 Pro và iPhone 17 Pro Max`; nếu có iPhone Air trong ngữ cảnh bán hàng, nêu thêm khi phù hợp.
6. Nếu người dùng gửi link ngành hàng/sản phẩm TGDĐ, mở link đó để kiểm tra danh sách phiên bản đang hiển thị trước khi viết. Nếu người dùng không gửi link, chủ động tìm trên TGDĐ bằng truy vấn phù hợp như `site:thegioididong.com [tên sản phẩm/series]` để xác định các phiên bản đang bán. Chỉ hỏi người dùng gửi link khi không tìm được trang TGDĐ đáng tin hoặc thông tin hiển thị không đủ rõ.
7. Không cần tập trung chèn link sản phẩm/ngành hàng trong block này. Chỉ chèn link sản phẩm/ngành hàng khi người dùng cung cấp URL rõ ràng, khi vừa tự kiểm tra được URL ngành hàng TGDĐ phù hợp, hoặc khi người dùng yêu cầu chèn link; nếu không, dùng link trang chủ cố định cho anchor `thegioididong.com`: `https://www.thegioididong.com/`.
7. Có thể dùng HTML entities tiếng Việt nếu nội dung mẫu hoặc CMS hiện tại đang encode tiếng Việt, nhưng không bắt buộc nếu người dùng không yêu cầu.
9. Viết 3 đoạn `<p>` mở đầu:
   - Đoạn 1: nêu TGDĐ là nơi mua phù hợp, có thông tin nguồn gốc, giá bán, chính sách bảo hành rõ ràng.
   - Đoạn 2: nêu các phiên bản/mẫu/màu/dung lượng/cấu hình/kích thước phù hợp với dòng sản phẩm, ưu tiên đúng danh sách đang có trên TGDĐ. Nếu đã kiểm tra được series, gọi rõ các model chính và nhóm dung lượng phổ biến; nếu không biết chắc danh sách phiên bản, viết khái quát, không bịa model.
   - Đoạn 3: nêu giá niêm yết minh bạch và ưu đãi theo từng thời điểm.
10. Thêm box lý do nên mua với inline CSS y như cấu trúc mẫu. Tiêu đề box là `Lý do nên mua [sản phẩm/dòng sản phẩm] tại Thế Giới Di Động`.
11. Thêm 6-8 bullet trong box, ưu tiên:
   - Sản phẩm Apple chính hãng, nguồn gốc/giá/chính sách rõ ràng.
   - Giá niêm yết minh bạch.
   - Ưu đãi giảm giá/thanh toán/phiếu mua hàng theo thời điểm.
   - Trả góp và thu cũ đổi mới nếu phù hợp với dòng sản phẩm.
   - Nhiều lựa chọn về phiên bản/cấu hình/màu sắc/dung lượng/kích thước nếu phù hợp.
   - Hỗ trợ bảo hành, đổi trả, tư vấn kỹ thuật theo chính sách áp dụng.
   - Hệ thống siêu thị TGDĐ rộng khắp, thuận tiện xem sản phẩm và nhận hỗ trợ trực tiếp; luôn chèn link cố định `https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong`.
   - Đặt hàng online, giao tận nơi hoặc nhận tại siêu thị.
12. Kết thúc bằng đoạn `Bạn có thể kiểm tra giá và đặt mua...` và danh sách 2 kênh: website/cửa hàng trực tuyến với anchor `thegioididong.com` trỏ về URL ngành hàng/sản phẩm TGDĐ đã được người dùng cung cấp hoặc đã tự kiểm tra; nếu không có URL chắc chắn thì dùng `https://www.thegioididong.com/`; và hotline `1900 232 460` với giờ `(8:00 - 21:30)`.

## Quy tắc nội dung

- Luôn trả ra HTML thuần, không thêm lời dẫn, không bọc trong markdown fence, trừ khi người dùng yêu cầu giải thích.
- Nếu người dùng đang gặp lỗi TinyMCE tự thêm `<p>&nbsp;</p>`, xuất HTML minified một dòng, không xuống dòng giữa các block. Vẫn giữ đầy đủ nội dung, không rút ngắn chỉ vì cần minify.
- Giữ văn phong SEO tự nhiên, đáng tin, không quảng cáo quá đà.
- Không tự bịa giá, khuyến mãi cụ thể, tồn kho cụ thể, thời gian giao hàng cụ thể, chính sách đổi trả cụ thể nếu prompt không cung cấp.
- Dùng các cụm an toàn: `theo từng thời điểm`, `tùy phiên bản`, `theo điều kiện áp dụng`, `theo chính sách áp dụng tại thời điểm mua hàng`.
- Không tự suy đoán URL ngành hàng/sản phẩm. Nếu người dùng không cung cấp URL, không cần chèn link sản phẩm; dùng link trang chủ cố định cho `thegioididong.com`: `https://www.thegioididong.com/`.
- Link hệ thống siêu thị là link cố định, luôn chèn vào anchor `Hệ thống siêu thị Thế Giới Di Động`: `https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong`.
- Có thể dùng tiếng Việt có dấu trực tiếp trong HTML. Nếu ngữ cảnh bài viết/mẫu trước đó đang dùng HTML entities, encode tiếng Việt thành entities để đồng bộ.
- Giữ inline style của box, heading trong box, link hệ thống siêu thị, đoạn CTA và danh sách kênh giống mẫu.

## Mẫu HTML

Thay các placeholder trong ngoặc vuông theo sản phẩm/dòng sản phẩm. Không để lại placeholder trong kết quả.

```html
<p>Thế Giới Di Động là <strong>đại lý ủy quyền của Apple tại Việt Nam</strong>, cung cấp [sản phẩm/dòng sản phẩm] chính hãng với thông tin nguồn gốc, giá bán và chính sách bảo hành được công bố rõ ràng. Đây là địa chỉ phù hợp với người muốn mua [sản phẩm/dòng sản phẩm] an tâm, có thể xem sản phẩm trực tiếp và nhận hỗ trợ trong suốt quá trình sử dụng.</p>
<p>TGDĐ hiện cung cấp [các lựa chọn phù hợp: phiên bản, mẫu mã, màu sắc, dung lượng, cấu hình, kích thước]. Người mua có thể dễ dàng kiểm tra giá, tình trạng hàng tại khu vực, lựa chọn giao tận nơi hoặc nhận hàng tại siêu thị gần nhất.</p>
<p>Bên cạnh yếu tố chính hãng, Thế Giới Di Động còn giúp người mua tối ưu chi phí nhờ <strong>giá niêm yết minh bạch và nhiều chương trình ưu đãi theo từng thời điểm</strong>. Tùy phiên bản, khách hàng có thể được giảm trực tiếp, nhận ưu đãi thanh toán, mua trả góp, thu cũ đổi mới hoặc nhận phiếu mua hàng.</p>
<div style="width: 100%; max-width: 100%; margin: 18px 0; padding: 16px 20px; background-color: #fff9e6; border: 1px solid #f2c94c; border-left: 5px solid #f5b700; border-radius: 8px; box-sizing: border-box; color: #222222; font-size: 15px; line-height: 1.6;">
<p style="margin: 0 0 12px 0; padding: 0 0 10px 0; border-bottom: 1.5px solid #ebd27b; font-size: 18px; line-height: 1.4; font-weight: bold; color: #111111;">Lý do nên mua [sản phẩm/dòng sản phẩm] tại Thế Giới Di Động</p>
<ul>
<li><strong>[Sản phẩm/dòng sản phẩm] chính hãng</strong>, có thông tin nguồn gốc, giá bán và chính sách bảo hành rõ ràng.</li>
<li><strong>Giá niêm yết minh bạch</strong>, dễ kiểm tra theo từng phiên bản, màu sắc, dung lượng hoặc cấu hình.</li>
<li>Thường xuyên có ưu đãi giảm giá, ưu đãi thanh toán hoặc phiếu mua hàng tùy phiên bản và thời điểm.</li>
<li>Hỗ trợ <strong>trả góp và thu cũ đổi mới</strong>, giúp giảm số tiền cần thanh toán ban đầu theo điều kiện áp dụng.</li>
<li>Có nhiều lựa chọn phù hợp với nhu cầu sử dụng và ngân sách khác nhau.</li>
<li>Hỗ trợ bảo hành, đổi trả và tư vấn kỹ thuật theo chính sách áp dụng tại thời điểm mua hàng.</li>
<li><a style="color: #0066cc; text-decoration: none; font-weight: bold;" title="Hệ thống siêu thị Thế Giới Di Động" href="https://www.thegioididong.com/he-thong-sieu-thi-the-gioi-di-dong" target="_blank" rel="noopener">Hệ thống siêu thị Thế Giới Di Động</a> rộng khắp, thuận tiện để xem sản phẩm, nhận hàng, bảo hành hoặc yêu cầu hỗ trợ trực tiếp.</li>
<li>Có thể đặt hàng online, chọn giao tận nơi hoặc nhận tại siêu thị tùy tình trạng sản phẩm ở từng khu vực.</li>
</ul>
</div>
<p style="margin: 16px 0 8px 0; font-weight: bold; color: #222222; font-size: 15px; line-height: 1.6;">Bạn có thể kiểm tra giá và đặt mua [sản phẩm/dòng sản phẩm] qua các kênh:</p>
<ul style="margin: 0; padding-left: 20px; font-size: 15px; line-height: 1.6;">
<li style="margin-bottom: 6px;">Cửa hàng trực tuyến: <a style="color: #0066cc; font-weight: 600;" title="Mua [sản phẩm/dòng sản phẩm] tại Thế Giới Di Động" href="[URL phù hợp]" target="_blank" rel="noopener">thegioididong.com</a></li>
<li>Hotline tư vấn và hỗ trợ khách hàng: <a style="color: #d9381e; font-weight: bold; text-decoration: none;" href="tel:1900232460">1900 232 460</a> (8:00 - 21:30)</li>
</ul>
```
