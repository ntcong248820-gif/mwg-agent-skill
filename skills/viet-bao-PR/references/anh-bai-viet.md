# Ảnh bài viết

Làm sau khi bài đã viết xong và chốt H1, trước khi chèn vào Doc. Thao tác upload, chèn Doc,
metadata xem `ky-thuat-docs-drive.md` mục 4.

## 1. Kho ảnh của dự án

- Mỗi dự án có 1 thư mục kho ảnh báo PR do user cung cấp, ghi trong file dự án
  (`references/du-an/<dự-án>.md`). Chưa có thì hỏi user trước khi làm ảnh.
- Ảnh lấy từ kho là nguồn chính. Chỉ lấy ảnh ngoài khi kho chưa có ảnh đáp ứng (mục 5).

## 2. Số lượng

| Lưu ý của báo | Số ảnh trong bài |
|---|---|
| Không ghi gì | 3 ảnh |
| Cho tối đa N ảnh (vd 5) | Chèn đủ N ảnh, mức tối đa báo cho phép |
| Ghi số ảnh cụ thể | Đúng số đó |

Báo có điều kiện riêng về ảnh (cấm logo, cấm nền trắng, kích thước tối thiểu...) thì lọc
ảnh theo điều kiện đó trước khi chọn.

## 3. Chọn ảnh và phân bổ vị trí

1. Lập danh sách các đoạn trong bài và nội dung chính của từng đoạn (thiết kế, camera, pin,
   giá...).
2. Mở kho ảnh, **xem từng ảnh ứng viên** (Read) trước khi chọn, không chọn theo tên file.
3. Ghép mỗi ảnh với đúng đoạn nói về nội dung trong ảnh: ảnh camera đặt sau đoạn nói về
   camera, ảnh màu sắc đặt sau đoạn nói về thiết kế/màu.
4. **Rải đều toàn bài:**
   - Ảnh 1 đặt ở vùng đầu bài (sau đoạn mở bài hoặc đoạn đầu của H2 thứ nhất). Bài có ảnh
     nguồn ngoài thì ảnh 1 là ảnh nguồn ngoài (mục 5).
   - Các ảnh còn lại chia đều cho các H2 phía sau, ưu tiên mỗi H2 có ít nhất 1 ảnh.
   - Không đặt 2 ảnh liền nhau, không dồn nhiều ảnh vào 1 H2 khi H2 khác còn trống.
   - Không đặt ngay dưới heading, không đặt giữa sapo và đoạn mở bài.
5. Tránh ảnh lạc đề (phụ kiện, sản phẩm khác dòng) và, với Báo PR, tránh ảnh khuyến mãi, ảnh
   cửa hàng, ảnh có logo nhà bán lẻ. **Ngoại lệ (chốt 15/10/2026):** bài có đề tài là khuyến
   mãi/CTKM (trả chậm, thu cũ, bảo hành, phiếu mua hàng...) thì user chỉ định lấy banner trong
   file KM của dự án (cột hình ảnh), cắt nút "Xem chi tiết", nới nền cùng màu thành 16:9 rồi
   xuất 2048×1150. Dòng chữ trên banner trái với đoạn thương hiệu (vd "trả trước từ 0đ" trong
   khi đoạn chốt "từ 10%") thì cắt dòng đó đi.
6. **Ảnh sản phẩm ưu tiên góc chính diện (chốt 15/10/2026):** mặt trước hoặc mặt lưng nhìn
   thẳng, thấy rõ cả máy (hoặc dàn máy đứng thẳng). Không dùng ảnh cận cụm camera chụp
   nghiêng, máy xoay chéo nửa chìm trong nền tối, ảnh cắt sát một góc máy: user chê "gớm".
   Chỉ dùng góc nghiêng/cạnh khi đoạn văn thật sự nói về chi tiết đó (cạnh viền, độ mỏng,
   nút bấm, bản lề gập, cụm camera trong bài camera). Ảnh dọc thì nới nền cùng màu thành
   16:9, không crop cắt mất máy.
7. Chọn đa dạng, không lặp ảnh giữa các bài cùng dự án: đọc danh sách ảnh đã dùng
   (`~/viet-bao-pr/tools/used_imgs_<dự-án>.txt`) trước khi chọn, chọn xong append
   `row|tên file hoặc URL`.

## 4. Caption

- Mỗi ảnh có 1 dòng caption ngay bên dưới, theo cấu trúc:
  `<Mô tả ngắn đúng nội dung ảnh, bám đoạn văn liền kề>. Ảnh: <nguồn>`
  (ngoại lệ: ảnh kho chụp thực tế không rõ nguồn thì chỉ ghi mô tả, xem bên dưới).
- `<nguồn>` là nơi ảnh thật sự đến từ: tên hãng (Apple, Samsung...) nếu là ảnh của hãng, tên
  trang nếu lấy từ trang công nghệ nước ngoài (MacRumors, Tom's Guide...). Ảnh ghép 2 nguồn
  ghi `Ảnh: A, B`.
- Ảnh trong kho (tên file không cho biết nguồn): nhìn ảnh rồi suy ra nguồn hợp lý nhất.
  - Ảnh render, ảnh press nền trơn, ảnh quảng bá đúng phong cách của hãng: `Ảnh: <Hãng>`.
  - Ảnh có watermark/logo hoặc dấu hiệu rõ của 1 trang/kênh: ghi tên trang/kênh đó.
  - Ảnh chụp thực tế (máy cầm tay, đặt trên bàn, tại cửa hàng) không có dấu hiệu nguồn:
    KHÔNG ghi nguồn, caption chỉ có phần mô tả (không có "Ảnh: ...").
  - Không ghi tên hãng cho ảnh chụp thực tế của bên thứ ba.
  - Ghi caption đoán nguồn vào báo cáo cuối để user kiểm.
- Mô tả 1 câu ngắn, viết tự nhiên, không nhồi keyword, không link, không lặp nguyên câu
  trong đoạn văn.

## 5. Ảnh từ nguồn ngoài

Chỉ dùng khi kho chưa có ảnh đáp ứng. **Tối đa 2 ảnh nguồn ngoài trong 1 bài**, phần còn lại
vẫn lấy từ kho.

**Bài có ảnh nguồn ngoài thì ảnh nguồn ngoài là ảnh 1**, vì báo thường lấy ảnh 1 làm thumb:
- Có 2 ảnh ngoài: ảnh đẹp, rõ sản phẩm hơn làm ảnh 1; ảnh còn lại đặt ở đoạn liên quan phía
  sau như bình thường.
- Chọn ảnh ngoài hợp với nội dung vùng đầu bài để ảnh 1 vẫn đứng đúng ngữ cảnh.
- Ảnh 1 nguồn ngoài resize/crop về 2048×1150 (scale cover rồi crop giữa, jpg quality 90), xem
  lại sau khi crop.

**Thứ tự nguồn:**
1. Bài so sánh (A vs B): ưu tiên ảnh so sánh ghép sẵn của trang công nghệ nước ngoài uy tín
   (ảnh hero bài "A vs B" của PhoneArena, GSMArena, Tom's Guide...) hoặc ảnh chụp 2 máy cạnh
   nhau. Tìm ở nhiều trang vẫn không có thì tự ghép 2 nửa từ ảnh của từng sản phẩm, caption
   `Ảnh: A, B`. Ảnh tự ghép tính là 1 ảnh nguồn ngoài.
2. Các bài khác: ảnh từ website/newsroom của hãng, hoặc trang công nghệ nước ngoài uy tín
   (MacRumors, AppleInsider, The Verge, Tom's Guide, ZDNET, Engadget, CNET, Macworld,
   PhoneArena, GSMArena...). Cách lấy nhanh: `og:image` của bài liên quan
   (`curl -sL -A "Mozilla/5.0" URL | grep og:image`).

**Điều kiện:**
- Không watermark, không logo trang. Phải mở ảnh ra xem trước khi dùng, không chọn hay loại
  trang nào chỉ vì đoán.
- Đúng sản phẩm, đúng đời máy, hợp nội dung đoạn sẽ chèn.
- Lưu lại URL trang và URL ảnh để báo cáo cuối.

**Gắn metadata cho ảnh ngoài (bắt buộc, chốt 15/10/2026):** ảnh tải từ hãng/trang nước ngoài
mang sẵn metadata của nguồn (tác giả, ©, XMP, IPTC). Rule metadata theo Site áp cho MỌI ảnh
trong thư mục Ảnh, kể cả ảnh ngoài, ảnh tự ghép, banner, thumb:
1. Xử lý ảnh bằng PIL (crop/pad 2048×1150, lưu jpg quality 90). Không upload thẳng file gốc
   vừa tải về.
2. Sau khi đã chốt H1 (cột T) và caption trong Doc, chạy `python3 ~/viet-bao-pr/tools/metatag.py <row>`.
   Script ghi EXIF + XMP theo Site và xoá XMP/IPTC cũ của nguồn:
   - Artist/Author = `Thegioididong.com` / `Topzone.vn` / `Dienmayxanh.com` theo cột A Site
   - Copyright = `Copyright © <site>`
   - Title = H1
   - Description = caption (bỏ phần "Ảnh: ...")
3. Kiểm: `python3 ~/viet-bao-pr/tools/metatag.py <row> --check`, mọi ảnh phải `OK`.
4. Đổi H1, đổi caption, thay ảnh (vd `imgswap.py`, `img1swap.py`) thì chạy lại bước 2–3.

Caption vẫn ghi đúng nguồn ảnh (`Ảnh: Apple`, `Ảnh: TechRadar`...). Metadata theo Site là rule
riêng, không đổi caption.

## 6. Ảnh thumb

- Báo có quy định kích thước thumb riêng (ghi trong lưu ý của báo): chọn 1 ảnh đẹp, rõ sản
  phẩm trong số ảnh của bài (ưu tiên ảnh 1), resize về đúng kích thước đó.
- Cách resize: scale cover rồi crop giữa (PIL, jpg quality 90); xem lại ảnh sau khi crop để
  chắc sản phẩm không bị cắt mất.
- Upload vào thư mục Ảnh của bài, đặt tên `<slug>-thumb-thegioididong.<đuôi>`. Không chèn
  thumb vào Doc.
- Báo không quy định thumb thì không cần làm.

## 7. Kiểm trước khi báo xong

- Đủ số ảnh theo mục 2, mỗi ảnh nằm sau đúng đoạn liên quan, rải đều toàn bài.
- Mỗi ảnh có caption; ảnh có nguồn rõ thì ghi `... Ảnh: <nguồn>` đúng nguồn.
- Bài có ảnh nguồn ngoài thì ảnh 1 là ảnh nguồn ngoài, cỡ 2048×1150.
- Không quá 2 ảnh nguồn ngoài.
- File trên Drive đặt tên đúng slug, có quyền `anyone:writer`, đã bắn metadata (kể cả ảnh
  ngoài, banner, thumb): `metatag.py <row> --check` ra OK hết.
- Có file thumb đúng kích thước nếu báo yêu cầu.
- Báo cáo cuối liệt kê: ảnh nào từ kho (tên file), ảnh nào nguồn ngoài (URL), thumb kích
  thước bao nhiêu.
