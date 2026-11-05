# Nguồn thông tin và cách trích dẫn

## 1. Thứ bậc nguồn

1. **Hãng, bản tiếng Việt:** website và newsroom Việt Nam của hãng (apple.com/vn,
   apple.com/vn/newsroom, trang specs `apple.com/vn/<sản-phẩm>/specs/`, samsung.com/vn,
   sony.com.vn...). Tên tính năng, tên màu, thông số lấy theo bản tiếng Việt của hãng.
2. **Hãng, bản quốc tế:** chỉ dùng khi bản tiếng Việt chưa có thông tin đó.
3. **Trang công nghệ nước ngoài uy tín:** 9to5Mac, MacRumors, AppleInsider, The Verge,
   Cult of Mac, Tom's Guide, TechRadar, CNET, Engadget, PhoneArena, GSMArena, Android
   Authority, SamMobile... Dùng cho số đo thử nghiệm, bài đánh giá, tin lỗi/cập nhật phần
   mềm mà hãng không đăng newsroom.

Báo Việt Nam (VnExpress, Dân trí, VietNamNet, Tinh Tế, Genk...) chỉ đọc để tham khảo ý,
**không dẫn, không nhắc tên** trong bài.

**Giá bán:** mặc định lấy giá đang hiển thị trên web của đúng Site bài viết ngay lúc viết
(mở trang sản phẩm, đúng phiên bản dung lượng/màu), ghi "tại thời điểm viết bài (dd/mm/yyyy)":
- Site TGDĐ: thegioididong.com
- Site TopZone: topzone.vn
- Site ĐMX: dienmayxanh.com
- Ngoại lệ: đề tài bắt buộc nói tới giá hãng (vd hãng công bố giá bán tại Việt Nam, so giá đề
  xuất giữa các đời) thì dùng giá hãng công bố trên website/newsroom Việt Nam của hãng, và ghi
  rõ là "giá đề xuất/giá hãng công bố" để người đọc không nhầm với giá bán thực tế.
- Không lấy giá từ báo, trang tổng hợp hay trí nhớ. Không mở được trang để kiểm thì không
  nêu con số.
- Không viết "hàng sắp về", "giảm đến hết ngày X".

**Hai nguồn mâu thuẫn:** ưu tiên nguồn bậc cao hơn. Hai nguồn cùng bậc mâu thuẫn thì nêu rõ
sự khác biệt trong bài, hoặc hỏi user trước khi viết.

## 2. Link tham khảo trong cột đề tài

- Đọc để nắm search intent (người tìm muốn biết gì), góc bài, cấu trúc.
- Viết lại hoàn toàn bằng lời mình, không sao chép câu chữ, không dịch lại từng đoạn.
- Góc bài bám intent của link tham khảo, không bẻ theo chủ đề của đầu báo (vd báo gia đình
  thì không tự chuyển sang góc gia đình, báo game thì không đưa game lên title/H2). Ý chỉ được
  nhắc thoáng qua trong nguồn không nâng thành title/H2. Chi tiết: mục "Giữ đúng search
  intent" trong SKILL.md.

## 3. Rule riêng cho Apple

- Không viết tin đồn, rò rỉ, dự đoán về sản phẩm Apple **chưa ra mắt chính thức**.
- Không viết bài mổ xẻ, tháo máy (teardown, iFixit, "bên trong iPhone có gì").
- Sản phẩm đã ra mắt nhưng Apple chưa cho phép PR (vd trước ngày mở đặt trước) thì không
  viết đề tài xoay quanh sản phẩm đó; lịch cụ thể ghi trong file dự án.

## 4. Cách trích dẫn trong bài

Nguyên tắc chung: **trích ít, viết thẳng.** Bài dày đặc "Theo X, theo Y" đọc như bài tổng
hợp, khô và mất hấp dẫn. Fact vẫn phải có nguồn để mình kiểm, nhưng phần lớn được viết thành
lời văn tự nhiên, dùng giọng báo PR.

| Loại thông tin | Cách viết | Tần suất |
|---|---|---|
| Thông tin chính thức của hãng | "Theo Apple...", "Apple cho biết...", "theo thông số Apple công bố..." | Chỉ ở chỗ cần xác lập độ tin cậy (con số chính, tính năng mới). Tối đa khoảng 2 lần/bài, còn lại viết thẳng |
| Số đo thử nghiệm của bên thứ ba | "Trong thử nghiệm pin của Tom's Guide...", "Trong bài đánh giá của The Verge..." | Chỉ khi dùng số đo cụ thể cần ghi công. Tối đa 1–2 lần/bài |
| Tin/fact chung từ trang nước ngoài | Viết thẳng, không ghi "Theo MacRumors" | |
| Thông tin của nhà bán lẻ | Mặc định KHÔNG viết "Theo Thế Giới Di Động", "Theo ghi nhận từ Thế Giới Di Động". Nhà bán lẻ chỉ xuất hiện trong đoạn thương hiệu ("Tại Thế Giới Di Động..."). Ngoại lệ bài đề tài KM/chương trình của nhà bán lẻ: tên Site ở title ("tại <Site>") và đoạn giới thiệu chương trình vùng đầu (van-phong-bao-pr.md mục 9), vẫn không dùng "Theo..." | Chỉ viết dạng "Theo (ghi nhận từ) Thế Giới Di Động" khi lưu ý của báo yêu cầu (vd VnExpress), và chỉ với thông tin chính chủ đã công bố (giá, CTKM, số liệu user cung cấp), không tự nghĩ ra nhận định |
| Báo Việt Nam | Không nhắc tên | |

Không nhắc quá nhiều nguồn trong cùng 1 đoạn hay cùng 1 bài:
- Mỗi đoạn tối đa 1 nguồn được gọi tên.
- Cả bài: "Theo Apple/hãng" khoảng 2 lần, tên trang bên thứ ba 1–2 lần. Vượt mức thì chuyển
  bớt thành câu viết thẳng.

Không dùng "theo X" để né trách nhiệm cho con số mình không chắc: không chắc thì bỏ.

## 5. Giữ đúng mức độ chắc chắn

- Không biến "có thể", "ước tính", "theo thử nghiệm", "dự kiến" thành "chắc chắn", "Apple
  xác nhận", "đã được chứng minh".
- Tin chưa chính thức (bài viết của bên thứ ba về lỗi chưa được hãng thừa nhận...) phải giữ
  cách nói "một số người dùng gặp tình trạng...", "Apple chưa đưa ra phản hồi chính thức".
- Thông số hãng ghi "lên đến" thì giữ "lên đến".

## 6. Ý kiến người dùng thật

- Chỉ dùng ý kiến có thật đã đọc được, không suy diễn.
- Paraphrase, trích nguyên văn không quá 15 từ.
- Không nêu tên người dùng thường, không ghi tên diễn đàn hay báo Việt Nam. Tên KOL, chuyên
  gia có phát biểu công khai thì được nêu.
- Ý kiến trái chiều vẫn được nêu (không tô hồng), nhưng đặt sau phần tích cực và viết bằng
  giọng trung tính.

## 7. Số liệu về chính công ty

Không đưa số liệu gán riêng cho TGDĐ/TopZone/ĐMX (lượt đặt cọc, doanh số, tỷ lệ chọn mẫu...)
nếu số đó chỉ do báo chí hay bên thứ ba ước tính, không phải công ty tự công bố. Số liệu của
nhà bán lẻ khác do báo chí đưa thì có thể dùng, viết thẳng không nhắc tên báo.

## 8. Không bịa

Không bịa số liệu, ý kiến, nhận định, tên tính năng. Không tìm được nguồn cho một khía cạnh
thì bỏ khía cạnh đó, không tự suy đoán để lấp chỗ trống.
