# Từ Điển Quy Cách & Giá Trị Dropdown Chuẩn

Tài liệu này định nghĩa chính xác cấu trúc cột và toàn bộ giá trị dropdown hợp lệ của 2 Google Sheet sử dụng trong quy trình CSO. **Bắt buộc nhập chính xác 100% từng ký tự, không được tự ý viết hoa/thường hoặc điền giá trị ngoài danh mục.**

---

## 1. Sheet "Order Content SP" (File Quản Lý Order Content)
- **Spreadsheet ID**: `<orderContent>`
- **Tab Gid**: `1094471385`
- **Tên Tab**: `Order Content SP`

### Bảng Định Nghĩa 47 Cột

| Index | Cột | Tên Cột | Kiểu Dữ Liệu / Dropdown | Quy Tắc & Giá Trị Bắt Buộc |
| :---: | :---: | :--- | :--- | :--- |
| 0 | A | ID Web | Text / Số | ID sản phẩm trên site TGDĐ (vd: `322533`). Lấy từ mã `productId` HTML. |
| 1 | B | Trạng thái onweb | Dropdown (List) | `Đã onweb`, `Chưa onweb`, `Không onweb`. (Mặc định: `Đã onweb`). |
| 2 | C | Ngày onweb | Date | Để trống nếu không có yêu cầu cụ thể. |
| 3 | D | Check ngày tạo ID | Date | Để trống nếu không có yêu cầu cụ thể. |
| 4 | E | Tên Sản Phẩm | Text | Tên sản phẩm đầy đủ chuẩn site TGDĐ. |
| 5 | F | Site chính (URL gốc) | Dropdown (List) | `TGDĐ`, `ĐMX`, `TopZone`. (Mặc định: `TGDĐ`). |
| 6 | G | Site kinh doanh | Dropdown (Range `=Data!$A$2:$A$9`) | `TGDĐ, ĐMX`, `TGDĐ, ĐMX, TopZone`, `TGDĐ`, `ĐMX`, `TopZone`. (Mặc định màn hình/laptop: `TGDĐ, ĐMX`). |
| 7 | H | Nhóm hàng | Text (tự động) | `Laptop` (theo scope Nhóm NH = Laptop). |
| 8 | I | Ngành hàng | Text | `màn hình máy tính` (hoặc `laptop`, `máy tính để bàn`, `máy in`, `phần mềm`). |
| 9 | J | Hãng | Text | Tên hãng (vd: `Samsung`, `Asus`, `MSI`, `Dell`, `HP`). |
| 10 | K | Trạng thái KD | Dropdown (List) | `Đang kinh doanh`, `Hàng sắp về`, `Tạm hết hàng`, `NKD`. (Mặc định: `Đang kinh doanh`). |
| 11 | L | Nhân sự Order | Dropdown (Range `=Data!$B$2:$B$25`) | `<Tên - Mã NV>`. |
| 12 | M | Team Order | Dropdown (List) | `SEO`, `NH/Khai báo`. (Mặc định: `SEO`). |
| 13 | N | Ngày Order | Date | Định dạng `DD/MM/YYYY` (vd: `16/09/2026`). |
| 14 | O | Tháng Order | **CÔNG THỨC MẢNG (KHÔNG GHI)** | **BẮT BUỘC ĐỂ TRỐNG**. Row 4 có `=ARRAYFORMULA(IF(ISBLANK(N4:N);"";MID(N4:N;4;7)))` tự sinh ra `MM/YYYY`. Ghi đè sẽ làm hỏng toàn bộ cột! |
| 15 | P | Deadline mong muốn | Date | Định dạng `DD/MM/YYYY` (mặc định sau ngày order 10 ngày). |
| 16 | Q | Hành động | Dropdown (Range `=Data!$E$2:$E$9`) | `Viết mới`, `Renew`, `Tối ưu`.<br>• `Viết mới`: Nếu trang chưa có bài viết.<br>• `Tối ưu`: Nếu đã có bài viết (cần tối ưu hình ảnh, internal link, outline). |
| 17 | R | Loại content | Dropdown (List) | `BVĐG`, `ĐĐNB`, `Không cần`. (Mặc định: `BVĐG`). |
| 18 | S | Nhân sự Content TGDĐ | Dropdown (Range `=Data!$C$2:$C$10`) | Để trống (team Content tự phân chia). |
| 19 | T | Trạng thái Content TGDĐ | Dropdown (List) | `Chưa làm`, `Đang làm`, `Hoàn thành`, `Không làm`. Để trống ban đầu hoặc đặt `Chưa làm`. |
| 20 | U | Ngày hoàn thành TGDĐ | Date | Để trống (điền khi nghiệm thu). |
| 21 | V | Tháng done Content TGDĐ| Date | Để trống. |
| 22 | W | Order TGDĐ? | Dropdown (List) | `Có`, `Không`. (Mặc định: `Có`). |
| 23 | X | Trạng thái BVĐG - TGDĐ | Dropdown (List) | `Đã có`, `Chưa có`.<br>• `Chưa có`: Nếu Hành động là `Viết mới`.<br>• `Đã có`: Nếu Hành động là `Tối ưu`. |
| 24 | Y | Trạng thái ĐĐNB - TGDĐ | Dropdown (List) | Để trống. |
| 25 | Z | URL Web TGDĐ | URL | URL sản phẩm đầy đủ trên thegioididong.com. |
| 26-41 | AA-AP | (Các cột ĐMX & TopZone) | - | Để trống cho các sản phẩm TGDĐ. |
| 42 | AQ | Outline / Nội dung Bổ sung | Long Text | • Nếu bài viết chưa có hoặc chỉ là bullet: Outline chi tiết phân cấp H2, H3, H4, Specs, FAQ.<br>• Nếu bài đã có heading: Ghi chú giữ nguyên khung heading hiện tại. |
| 43 | AR | Loại bài viết | Dropdown (Range `=Data!$K$2:$K$6`) | `Bài viết AI`, `Bài viết AI + bổ sung`, `Bài viết research riêng`.<br>• `Bài viết AI`: Dùng cho bài `Viết mới`.<br>• `Bài viết AI + bổ sung`: Dùng cho bài `Tối ưu`. |
| 44 | AS | Keyword | Text | **Quy tắc lấy Keyword chính xác:**<br>1. Tra cứu URL sản phẩm tại **Cột O** trong sheet `All KW` (File ``). Lấy từ khóa tại **Cột L** có Volume search (**Cột M**) cao nhất.<br>2. *Fallback*: Nếu không có URL trong `All KW`, chuẩn hóa theo tên model sản phẩm (Hãng + Dòng máy + Model code) chính xác tuyệt đối, không ghi chung chung. |
| 45 | AT | Ghi chú | Text | Chỉ dẫn rõ việc cần làm: viết mới/viết lại theo outline, bổ sung hình ảnh minh họa, chèn link URL danh mục đích. |
| 46 | AU | Note chia phụ trách | Text | Để trống. |

---

## 2. Sheet "Content_SP_Optimize" (File Data Order TGDD)
- **Spreadsheet ID**: ``
- **Tab Gid**: `1678314717`
- **Tên Tab**: `Content_SP_Optimize`

### Quy Tắc Cột:
- **Cột A (Ngày audit)**: Định dạng `MM/DD/YYYY` (vd: `09/16/2026`).
- **Cột B (URL danh mục)**: Link danh mục cần push SEO (vd: `https://www.thegioididong.com/man-hinh-may-tinh-man-hinh-cong`).
- **Cột C (URL sản phẩm)**: Link chi tiết sản phẩm.
- **Cột D (Trạng thái)**:
  - Ban đầu khi vừa audit: `Chưa làm`.
  - Sau khi đẩy order qua sheet `Order Content SP`: `Đang làm`.
  - Sau khi nghiệm thu đạt yêu cầu: `Hoàn thành`.
- **Cột E đến T (BẢO TOÀN TUYỆT ĐỐI CÔNG THỨC MẢNG)**:
  - Cột E: `Product in KPI?` (MAP formula `=MAP(C2:C, ...)`).
  - Cột F: `Tính AC?` (MAP formula).
  - Cột G: `CSO Key` (Date|Category URL).
  - Cột H: `AC Key`.
  - Cột I-M: Metadata danh mục tự sinh.
  - Cột N-R: Metadata sản phẩm tự sinh.
  - Cột S: `Status chuẩn hóa`.
  - Cột T: `Row check` (phải ra `OK`).
  - **TUYỆT ĐỐI KHÔNG GHI ĐÈ TỪ CỘT E TRỞ ĐI.** Chỉ ghi dữ liệu thủ công vào dải **A:D**. Ghi đè cột E sẽ làm vỡ công thức mảng của toàn sheet và báo `#REF!`.
