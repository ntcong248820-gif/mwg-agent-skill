---
name: seo-cso-optimize
description: Tối ưu Content Sản Phẩm (CSO - Content Sản Phẩm Optimize) đẩy SEO cho trang danh mục. Audit 5 tiêu chí bài viết sản phẩm, log Data Order TGDD, order Content SP với dropdown chuẩn 100%, và nghiệm thu tự động.
user-invocable: true
when_to_use: "Use when user wants to audit/optimize product descriptions for category SEO (CSO action), log product content audits to Data Order TGDD, generate orders in Order Content SP, or verify/nghiệm thu completed content orders."
category: seo-ops
keywords: [cso, content-san-pham, order-content, audit-san-pham, thong-tin-san-pham, internal-link-danh-muc, nghiem-thu-cso]
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
---

# seo-cso-optimize

Kỹ năng tự động hóa quy trình **CSO (Content Sản Phẩm Optimize)** nhằm tăng độ dày nội dung và link nội bộ đẩy SEO cho trang danh mục mục tiêu (thuộc scope `Nhóm NH = Laptop`).

## Hai Chế Độ Hoạt Động (Modes)

1. **Mode `execute`**: Nhận URL danh mục -> Audit toàn bộ sản phẩm -> Ghi Sheet `Content_SP_Optimize` (`Data Order TGDD`) -> Tạo đơn ở Sheet `Order Content SP` (`Quản lý Order Content`) chuẩn 100% dropdown -> Chuyển trạng thái `Content_SP_Optimize` sang `Đang làm`.
2. **Mode `nghiem-thu`**: Nhận dải row order (vd: `8342:8359`) -> Kiểm tra trực tiếp trang sản phẩm live trên site -> Cập nhật trạng thái `Content_SP_Optimize` sang `Hoàn thành` cho các SP đạt chuẩn.

---

## 1. Mode Execute (Audit & Tạo Đơn Order)

### Bước 1: Crawl & Audit 5 Tiêu Chí Sản Phẩm
Chạy script audit chuyên dụng:
```bash
python3 .claude/skills/seo-cso-optimize/scripts/audit_cso_category.py \
  --category-url "https://www.thegioididong.com/man-hinh-may-tinh-man-hinh-cong" \
  --keyword "màn hình cong"
```
*Ghi chú: Nếu có sẵn danh sách URL sản phẩm cụ thể, truyền thêm `--urls URL1 URL2 ...`.*

**5 Tiêu chí Audit:**
1. **Nội dung:** Đã có bài viết "Thông tin sản phẩm" chưa (`len(text) > 100`)?
2. **Cấu trúc Outline:** Là bài viết chia Heading rõ ràng (`H2`, `H3`, `H4`) hay chỉ là bullet checklist (`•`, `li`)?
3. **Hình ảnh:** Đã có ảnh minh họa thực tế bên trong bài viết chưa?
4. **Link danh mục:** Đã có internal link trỏ về URL danh mục mục tiêu chưa?
5. **Keyword mention:** Bài viết đã nhắc đến từ khóa/chủ đề của danh mục cần SEO chưa?

### Bước 2: Ghi vào Sheet 1 (`Content_SP_Optimize` - Data Order TGDD)
- **Spreadsheet ID:** ``
- **Tab Gid:** `1678314717` (`Content_SP_Optimize`)
- **Phạm vi ghi:** Chỉ ghi dữ liệu vào **Cột A đến D** (`Ngày audit`, `URL danh mục`, `URL SP`, `Trạng thái: Chưa làm`).
- **QUY TẮC SỐNG CÒN:** **BẢO TOÀN TUYỆT ĐỐI TỪ CỘT E TRỞ ĐI (E:T)**. Đây là công thức mảng tự động (`Product in KPI?`, `Tính AC?`, `Row check`). Tuyệt đối không ghi đè cột E vì sẽ làm vỡ công thức mảng toàn sheet (`#REF!`).

### Bước 3: Tạo Đơn Order vào Sheet 2 (`Order Content SP` - Quản lý Order Content)
- **Spreadsheet ID:** `<orderContent>`
- **Tab Gid:** `1094471385` (`Order Content SP`)
- Tìm dòng trống tiếp theo ở cuối bảng (đọc cột A để xác định `last_row + 1`).
- Điền đầy đủ 47 cột theo chuẩn quy cách trong `references/dropdown-dictionary.md`.

#### Bảng Giá Trị Dropdown Bắt Buộc:
| Cột | Tên Cột | Giá Trị Hợp Lệ Bắt Buộc | Ghi Chú |
| :--- | :--- | :--- | :--- |
| **B (Col 1)** | Trạng thái onweb | `Đã onweb` | Dropdown cố định |
| **F (Col 5)** | Site chính (URL gốc) | `TGDĐ` | Dropdown cố định |
| **G (Col 6)** | Site kinh doanh | `TGDĐ, ĐMX` | Range `=Data!$A$2:$A$9` |
| **K (Col 10)** | Trạng thái KD | `Đang kinh doanh` | Dropdown cố định |
| **L (Col 11)** | Nhân sự Order | `<Tên - Mã NV>` | Range `=Data!$B$2:$B$25` |
| **M (Col 12)** | Team Order | `SEO` | Dropdown cố định |
| **N (Col 13)** | Ngày Order | `DD/MM/YYYY` (vd: `16/09/2026`) | Định dạng ngày |
| **O (Col 14)** | Tháng Order | **BẮT BUỘC ĐỂ TRỐNG** | Row 4 có `ARRAYFORMULA` tự tính |
| **P (Col 15)** | Deadline mong muốn | `DD/MM/YYYY` (mặc định sau 10 ngày) | Định dạng ngày |
| **Q (Col 16)** | Hành động | `Viết mới` hoặc `Tối ưu` | Range `=Data!$E$2:$E$9` |
| **R (Col 17)** | Loại content | `BVĐG` | Dropdown cố định |
| **W (Col 22)** | Order TGDĐ? | `Có` | Dropdown cố định |
| **X (Col 23)** | Trạng thái BVĐG - TGDĐ | `Chưa có` (nếu Viết mới) / `Đã có` (nếu Tối ưu) | Dropdown cố định |
| **AQ (Col 42)**| Outline / Nội dung Bổ sung | Dựng outline phân cấp H2, H3, H4 chi tiết | Nếu bài chỉ toàn bullet, phải dựng outline mới hoàn chỉnh |
| **AR (Col 43)**| Loại bài viết | `Bài viết AI` (Viết mới) / `Bài viết AI + bổ sung` (Tối ưu) | **TUYỆT ĐỐI KHÔNG DÙNG "Bài viết mới"** |
| **AS (Col 44)**| Keyword | Lấy KW có Volume cao nhất từ `All KW` | Tra cứu URL tại Col O `All KW` (``), lấy Col L có Col M (Volume) cao nhất. Nếu không có: Chuẩn hóa theo model SP rõ ràng, không chung chung. |
| **AT (Col 45)**| Ghi chú | Ghi rõ: Thêm ảnh, chèn internal link danh mục, mention từ khóa | Hướng dẫn rõ ràng cho team content |

### Bước 4: Cập Nhật Trạng Thái Sheet 1
Sau khi đã append thành công vào Sheet `Order Content SP`, quay lại Sheet `Content_SP_Optimize` cập nhật Cột D từ `Chưa làm` thành `Đang làm`.

---

## 2. Mode Nghiệm Thu (Verify & Update Done)

Khi team Content báo đã hoàn thành hoặc tới kỳ kiểm tra định kỳ:

### Bước 1: Kiểm Tra Trực Tiếp Site Live
Chạy script nghiệm thu đối chiếu với dải row order:
```bash
python3 .claude/skills/seo-cso-optimize/scripts/verify_cso_order.py --range 8342:8359
```

Script sẽ crawl từng URL sản phẩm và kiểm tra:
1. Đã có nội dung "Thông tin sản phẩm" thực tế trên web chưa?
2. Đã có hình ảnh minh họa trong bài viết chưa?
3. Đã chèn link trỏ về URL danh mục mục tiêu chưa?
4. Đã phân cấp Heading rõ ràng hay chưa?

### Bước 2: Áp Dụng Trạng Thái "Hoàn thành"
Nếu kết quả đạt yêu cầu, chạy lệnh với flag `--apply`:
```bash
python3 .claude/skills/seo-cso-optimize/scripts/verify_cso_order.py --range 8342:8359 --apply
```
Script sẽ tự động:
- Cập nhật Cột D của các URL tương ứng trong `Content_SP_Optimize` thành `Hoàn thành`.
- Báo cáo rõ ràng số lượng URL PASS / FAIL và các lỗi còn tồn đọng nếu có.

---

## 3. Quy Định An Toàn Antigravity & GWS

- Luôn dùng cờ cấu hình profile công ty cho GWS:
  ```bash
  GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws" command gws ...
  ```
- Không bao giờ ghi inline chuỗi có dấu nháy phức tạp trong Antigravity shell; ưu tiên chạy thông qua file script `.py` hoặc heredoc.
- Khi cập nhật Sheet có công thức mảng, luôn kiểm tra lại cột `Row check` (cột U trong `Content_SP_Optimize`) xem có giữ nguyên giá trị `OK` hay không.
