# Ví dụ chọn đoạn văn — 14 bài thực tế

Tài liệu này ghi lại 14 ví dụ thực tế từ một đợt xử lý thật.
Dùng làm ground truth để calibrate logic chọn đoạn văn.

## Nhóm 1: Màn hình 24 inch (Dòng 416–421)
**Anchor:** `màn hình 24 inch` → **Link:** `https://www.thegioididong.com/man-hinh-may-tinh-24-inch`

### Dòng 416 — /game-app/huong-dan-chon-man-hinh-may-tinh-choi-game-danh-cho-game-thu-1400788
**Đoạn đã chọn:**
> "Kích thước màn hình phổ biến nhất cho game thủ phải kể đến màn hình 24 inch, đây là kích thước vừa phải đủ để bạn quan sát, không cần xoay đầu nhiều như màn 27 inch."

**Lý do chọn:** `<p>` gần đầu bài nhất (pos nhỏ), chứa cụm `màn hình 24 inch` ở dạng đoạn văn trọn vẹn.

---

### Dòng 417 — /game-app/top-6-man-hinh-may-tinh-co-loa-choi-game-dinh-nhat-hien-nay-1403633
**Đoạn đã chọn:**
> "Màn hình 24 inch là kích thước lý tưởng, vừa đủ để quan sát không cần quay đầu nhiều nhưng vẫn đủ lớn để trải nghiệm chơi game tốt nhất."

---

### Dòng 421 — /hoi-dap/bang-kich-thuoc-man-hinh-may-tinh-24-inch-21-22-1558019
**Đoạn đã chọn:**
> "Màn hình 24 inch là loại màn hình máy tính phổ biến nhất hiện nay với kích thước lý tưởng được nhiều người dùng văn phòng và game thủ ưa chuộng."

---

## Nhóm 2: Laptop văn phòng / sinh viên (Dòng 422–424)
**Anchor:** `laptop văn phòng` / `laptop sinh viên`
**Link:** `https://www.thegioididong.com/laptop?g=hoc-tap-van-phong`

### Dòng 422 — /game-app/laptop-van-phong-co-choi-game-duoc-khong-co-tot-khong-1405433
**Anchor:** `laptop văn phòng`
**Đoạn đã chọn (pos 4):**
> "Laptop văn phòng chỉ sử dụng để xử lý các công việc cơ bản hàng ngày như xem phim, nghe nhạc, lướt web, sử dụng các phần mềm tin học như Word, Excel,...Tất cả các công việc trên đều không yêu cầu cao về mặt cấu hình."

**Lý do chọn:** `<p>` đầu tiên chứa `Laptop văn phòng` (viết hoa đầu câu, case-insensitive match OK).

---

### Dòng 423 — /game-app/top-8-laptop-dung-chip-i5-1235u-danh-cho-sinh-vien-van-phong-1478408
**Anchor:** `laptop sinh viên`
**Đoạn đã chọn (pos 1 — H2/sapo):**
> "Bạn đang tìm kiếm cho mình một chiếc laptop sinh viên - văn phòng với bộ chip xử lý hiệu năng mạnh mẽ để cân nhẹ nhàng mọi tác vụ làm việc, giải trí thì hãy dừng chân ghé lại nơi đây..."

**Lý do chọn:** `<h2>` là sapo (đoạn tóm tắt dài đầu bài) — trong bài này không có `<p>` nào ở đầu chứa anchor. Đây là exception hợp lý.

---

### Dòng 424 — /game-app/top-11-laptop-acer-tot-nhat-va-dang-mua-nhat-2021-1381547
**Anchor:** `laptop sinh viên`
**Đoạn đã chọn (pos 19):**
> "Một trong những laptop sinh viên tốt nhất trong tầm giá, Aspire 3 có thể đáp ứng được hầu hết các tác vụ sinh viên và văn phòng. Ổ cứng SSD 256GB sẽ khiến quá trình khởi động các trình duyệt hay các phần mềm thiết kế đồ họa trở nên nhanh chóng và cực kỳ mượt mà."

---

## Nhóm 3: Màn hình 2K (Dòng 425–427)
**Anchor:** `màn hình 2k` → **Link:** `https://www.thegioididong.com/man-hinh-may-tinh-2k`

### Dòng 425 — /hoi-dap/man-hinh-qhd-la-gi-955079
**Đoạn đã chọn (pos 5):**
> "Độ phân giải QHD (hay còn gọi là Quad HD nghĩa là gấp 4 của độ phân giải HD hoàn chỉnh (full HD) được đo ở 2560 x 1440 pixel. Từ đó hình thành tên màn hình 2K có độ phân giải lớn hơn 2000 pixel. Một số dòng điện thoại của Samsung, Xiaomi hay LG cũng đang sở hữu màn hình QHD."

**Lý do chọn:** Đây là bài định nghĩa QHD — đoạn pos 5 là đoạn định nghĩa trực tiếp, gần đầu bài nhất chứa `màn hình 2K`.

---

### Dòng 426 — /hoi-dap/cach-chon-laptop-mong-nhe-va-thoi-trang-1022639
**Đoạn đã chọn (pos 12 — duy nhất):**
> "Ngoài ra nếu tài chính cho phép, bạn cũng có thể cân nhắc các màn hình 2K, 4K để cho ra hình ảnh siêu mịn. Tuy nhiên độ phân giải cao sẽ máy tốn pin nhiều hơn đấy."

**Lưu ý:** Chỉ có 1 candidate. Đoạn văn ngắn nhưng chứa anchor rõ ràng và có ngữ nghĩa phù hợp.

---

### Dòng 427 — /game-app/tu-van-mua-laptop-choi-game-tu-a-z-...-1402055
**Đoạn đã chọn (pos 113):**
> "Ngoài ra, với nhu cầu chơi game cao, max setting thì bạn cũng nên cân nhắc các laptop có màn hình 2K (Quad HD) hoặc thậm chí là 4K (Ultra HD) cùng với đó là tần số quét màn hình cao lên đến 360Hz để có những trải nghiệm tuyệt vời nhất bạn nhé!"

**Lý do chọn pos 113 thay vì pos 102:** Pos 102 chứa `màn hình có độ phân giải lên đến 2K` — viết hoa `2K` không match anchor `màn hình 2k` theo regex? Không — `re.IGNORECASE` match. Nhưng pos 113 có cụm `màn hình 2K` rõ ràng hơn và trọn vẹn hơn.

---

## Nhóm 4: Màn hình 4K (Dòng 428–429)
**Anchor:** `màn hình 4k` → **Link:** `https://www.thegioididong.com/man-hinh-may-tinh-4k`

### Dòng 428 — /hoi-dap/card-do-hoa-intel-arc-hieu-nang-ngang-card-rtx-co-mat-1396576
**Đoạn đã chọn (pos 30 — duy nhất):**
> "Một số tiện ích nổi bật có thể kể đến như: Hỗ trợ 2 màn hình 8K 60Hz hoặc 4 màn hình 4K 120Hz, tính năng Smooth Sync..."

**Lưu ý:** Anchor `màn hình 4k` match trong cụm `4 màn hình 4K 120Hz`. HTML tự sinh bọc đúng `màn hình 4K` — công thức Cột O tìm first occurrence.

---

### Dòng 429 — /hoi-dap/chip-snapdragon-8cx-la-gi-nhung-diem-khac-biet-cua-1230932
**Đoạn đã chọn (pos 21 — duy nhất):**
> "Cuối cùng, GPU này mang đến nhiều cải tiến cho hình ảnh, chẳng hạn như bộ mã hóa video chất lượng cao, hỗ trợ codec video H.265 mới nhất được sử dụng trên web, hỗ trợ HDR thế hệ 2 để chỉnh màu thời gian thực và hỗ trợ trình chiếu giữa hai màn hình 4K HDR được kết nối."

---

## Pattern Summary

| Rule | Trường hợp |
| --- | --- |
| Ưu tiên `<p>` pos nhỏ nhất | 11/14 dòng |
| Chấp nhận `<h2>` khi không có `<p>` phù hợp ở đầu | 1/14 (dòng 423) |
| Đoạn văn chứa anchor nhưng anchor là phần của cụm từ dài hơn | OK — regex match vẫn tìm được |
| Anchor viết thường, bài viết viết hoa (2K vs 2k) | `re.IGNORECASE` xử lý đúng |
