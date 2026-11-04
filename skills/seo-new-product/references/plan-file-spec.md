# Cấu trúc file phụ (Plan SEO nhóm SP) và file mẫu

Dựng bằng COPY file Plan mẫu (`sheets.nhOrderPlanReference`), không dựng từ đầu: chip màu dropdown không đặt được qua
Sheets API (xem `gws-sheets` quy ước mục 3), bản copy giữ nguyên chip, format, pivot, chart, gridline.

## Tab

| Tab | Nội dung skill điền |
| --- | --- |
| `Hành_Động_SEO` | A Hành động, B Người làm, C Ngày dự kiến, D Trạng thái "Chưa làm", E Ngày xong (trống), F Link kết quả (link bài Renew), G Ghi chú (đường dẫn URL hoặc ghi chú ngắn) |
| `Từ_Khóa` | Từ khoá, URL, Volume/tháng, KW chính (checkbox), Ghi chú SERP |
| `Title_Meta` | URL, Dạng trang, Mode, Title đề xuất, Độ dài Title (công thức LEN), Meta đề xuất, Độ dài Meta, Ghi chú. Chỉ đề xuất, KHÔNG ghi PIM/MDM/CMS |
| `Rank_Theo_Dõi` | MỘT tab duy nhất để dán kết quả đo. Skill chỉ điền cột A (Keyword); B:P để trống cho owner dán kết quả đo và nhập Ngày đo (xem mục "Rank_Theo_Dõi" bên dưới) |
| `Tổng_Hợp` | Công thức + pivot + 2 chart có sẵn từ file mẫu (xem mục "Tổng_Hợp"), skill chỉ đổi tiêu đề A1 |
| `Nhân_sự` | Danh sách từ config `nhOrder.staff` |

## Rank_Theo_Dõi (cấu trúc từ 29/10/2026)

Một tab duy nhất để dán kết quả từ tool **SERP Rank Checker** của owner (extension Chrome, `~/Documents/Personal App/rank-checker-extension`,
xuất CSV/TSV/XLSX/Copy). 16 cột: A:O là 15 cột của tool (mỗi từ khoá MỘT dòng, không có cột Nhóm ranking), P là **Ngày đo** do owner nhập khi dán:

`Keyword | Rank | Domain | URL | AI Overview | Side panel | Citation | Link | AIO total | Top 1 URL | Top 1 Title | Top 2 URL | Top 2 Title | Top 3 URL | Top 3 Title | Ngày đo`

- Mỗi lần đo dán NỐI TIẾP xuống dưới (A:O) rồi điền Ngày đo (cột P) cho các dòng vừa dán. Không xoá lần đo cũ: đó là lịch sử.
- `Rank` là số, hoặc `—` khi không thấy trong độ sâu đã chọn. `Domain`/`URL` là kết quả của domain đứng cao nhất trong số domain đang theo dõi
  (TGDĐ hoặc ĐMX). `AI Overview` nhận `In`, `Not cited`, `No AI Overview`, `Limit`, `Timeout`, `Error`. Ô Side panel/Citation/Link có thể chứa
  nhiều URL (mỗi URL một dòng trong ô). `AIO total` = tổng lượt hiện diện ở 3 loại đó.
- Skill gọi `rank_sheet.check_structure` trước khi copy (file mẫu) và trước khi extend (file đã có): header lệch 16 cột chuẩn thì DỪNG, không dựng.
- Trên BẢN COPY, `rank_sheet.normalize_rank_tab` đưa tab về quy ước gws-sheets (Inter 9, giữa dọc, dòng 28px, header như Từ_Khóa), định dạng ngày
  dd/mm/yyyy cho cột P, xoá các luật tô màu cũ của cột Nhóm ranking, đặt dropdown 6 trạng thái AI Overview (không strict để dán không bị chặn).
  File mẫu/nguồn không bị sửa định dạng.
- File mới: P để trống (chưa đo). Tổng_Hợp coi các dòng chưa có ngày là "lần đo hiện tại" cho tới khi có ngày đầu tiên. Từ khoá thêm sau (extend)
  được nối vào cuối cột A, chưa có ngày, nên chưa vào số liệu cho tới khi được đo và điền ngày.
- Ngày phải là ngày thật (dd/mm/yyyy) chứ không phải chữ; Tổng_Hợp so khớp bằng số.

## Tổng_Hợp (cấu trúc từ 29/10/2026)

Đọc từ Rank_Theo_Dõi A2:P2000 (theo vị trí cột). **Số liệu hiện tại = các dòng có Ngày đo lớn nhất** (ô B26); xu hướng gom theo Ngày đo. Khối 1-2 là pivot cũ (Hành_Động_SEO, Từ_Khóa); từ khối 3 trở xuống:

| Khối | Vị trí | Nội dung |
| --- | --- | --- |
| 3 | A14:F26 | Số từ khoá theo nhóm ranking (COUNTIFS từ cột Rank) + cột Trong AIO, TGDĐ, ĐMX; dòng Top 1-2 (mục tiêu KPI), Top 1-3, Rank trung bình, Ngày đo mới nhất (B26) |
| 4 | J14:L22 | Số từ khoá theo trạng thái AI Overview, tỉ lệ được trích, tổng lượt AIO |
| chart | A27, J27 | "Số từ khóa theo nhóm ranking" (nguồn A16:B21), "Số từ khóa theo trạng thái AI Overview" (nguồn J16:K19) |
| 5 | A37:H48 | Xu hướng: mỗi dòng một Ngày đo (10 mốc gần nhất, cũ → mới), số từ khoá từng nhóm ranking và rank trung bình (công thức MAP) |
| chart | A50, J50 | Cột chồng "nhóm ranking qua các ngày đo", đường "Rank trung bình qua các ngày đo" (nguồn bảng khối 5) |
| 6 | A60:E71 | Domain đứng Top 1/2/3 của Google ở lần đo mới nhất (tối đa 10 domain) |
| 7 | A74:H | Chi tiết từng từ khoá ở lần đo mới nhất: Rank, Nhóm ranking (tô màu), Domain giữ hạng, AI Overview, domain Top 1-3. Khối dài ra, nằm dưới cùng |

Pivot thật của tab là khối 1 và 2 (Hành_Động_SEO, Từ_Khóa). Rank_Theo_Dõi không pivot được vì có nhiều lần đo cho cùng từ khoá và không có cột nhóm ranking.
Nguồn của 4 chart là chính các bảng hiển thị ở khối 3, 4, 5 nên không có bảng "dữ liệu nguồn" riêng. Công thức dùng `;` (vi_VN), tên biến LET không được
trùng địa chỉ ô (d1, c1, r, c...); thống kê theo ngày dùng `MAP` + hàm vô hướng vì `COUNTIFS`/`SUMIFS` với mảng tiêu chí và 2 cặp điều kiện trả sai. `plan_writer.readback` quét cả tab Tổng_Hợp tìm #REF!/#N/A/#VALUE!/#ERROR! sau mỗi lần dựng.
Mã nguồn dựng khối này: `tasks/260721-sheet-system-build/work-items/261029-rank-theo-doi-cau-truc-serp-moi/scripts/build-tong-hop-rank-serp.py`.

## Timeline (ngày làm việc kể từ ngày dựng plan, `action_plan.py`)

Title/Meta +1 · Nội dung +4 · Renew và Lên bài mới +5 (dàn thêm tối đa +3) · Chèn link Promote +8 (dàn thêm tối đa +3).
Mỗi URL một dòng cho Title/Meta, Nội dung, Promote (owner chốt 29/10). "Lên bài viết mới Tin tức" gán người phụ trách Tin tức, không có ngày
(`--no-news` để bỏ dòng này).

## Quy tắc sheet (gws-sheets mục "Quy ước khi tạo hoặc sửa Google Sheet")

Font Inter 9, căn giữa dọc, dòng 28px, CLIP, tab Tổng_Hợp tắt gridline: kế thừa từ file mẫu; tab `Title_Meta` do
`plan_writer.ensure_title_meta_tab` áp cùng format. Công thức locale vi_VN dùng dấu `;`.

## Không có file mẫu riêng

Owner chốt 29/10: không giữ file mẫu riêng. Nguồn copy là file Plan tham chiếu (`sheets.nhOrderPlanReference`, chỉ đọc, không bao giờ sửa);
bản copy bị xoá dữ liệu mẫu (`reset_values`: giữ format, dropdown, công thức Nhóm ranking, pivot, chart), thêm tab `Title_Meta`
(`ensure_title_meta_tab`), rồi mới điền. Dropdown "Hành động" và "Người làm" lấy theo file tham chiếu; thêm lựa chọn mới thì sửa ở
file tham chiếu (kèm chip màu bằng UI), các file copy sau tự có.

## Nhóm đã có file Plan (extend)

Nhóm có dòng đã có link ở cột G và dòng mới chưa có: `plan --apply` KHÔNG tạo file mới mà nối thêm dòng vào cuối từng tab của file đó
(bỏ qua cặp từ khoá+URL đã có, không xoá gì), rồi ghi cùng link vào cột G của các dòng mới. Nhóm có nhiều link khác nhau thì dừng.

## Cột G của file chính

Chỉ ghi ô G của đúng dòng URL thuộc nhóm, bằng `--apply --write-main-link`: đọc lại file chính ngay trước khi ghi, dừng nếu
dòng đã đổi, không ghi đè ô G đã có link, ghi RAW rồi đọc lại và kiểm các cột khác không đổi. `--test` bị chặn ghi cột G.
