# Ba khung mô tả task IT

Rút từ 58 Doc trong sheet tổng hợp task IT (09/10/2026): A 38 Doc, B 13, C 4.
Mục 1–2 (Thông tin, Lịch sử) do `build-doc.py` **tự sinh** từ `info` + `history` —
spec chỉ viết từ mục 3 trở đi (khung C: từ mục 3 "Yêu cầu kinh doanh").

## Chọn khung

| Tình huống | Khung |
| --- | --- |
| Sửa lỗi / đổi rule trên hệ trang có sẵn: title/des, heading, canonical, robots, ALT, URL, redirect, hiển thị 1 vùng | **A** (mặc định) |
| Khởi tạo hạng mục mới cần nêu bài toán + phương án: Schema, OG, sitemap, chức năng CMS/PIM mới, vùng nội dung mới | **B** |
| Task lớn nhiều bên, nhiều thuộc tính/API, cần stakeholder ký: GMC feed, đồng bộ API, tích hợp hệ ngoài | **C** |

Không chắc → A. Chọn B/C khi người đọc cần thấy "vì sao chọn giải pháp này" hoặc nhiều bên phải xác nhận.

## Khung A — SEO

```text
TITLE  [Site] Tên task
1. Thông tin yêu cầu task        (tự sinh — bảng 2 cột)
2. Lịch sử cập nhật              (tự sinh — Ngày thay đổi | Name | Mô tả thay đổi)
3. Mô tả chi tiết yêu cầu
  3.1. Mục đích task
       - **Mục đích:** …           ← lợi ích SEO/người dùng
       - **Hiện tại:** …           ← lỗi đang xảy ra + ảnh/URL bằng chứng
       - **Mong muốn:** IT hỗ trợ …
       **=> hệ quả SEO nếu không làm** (đoạn đậm)
  3.2. Phạm vi áp dụng          ← bảng label_col: Site | Hệ trang | Vùng áp dụng | Link ví dụ | Ngoài phạm vi | Dữ liệu
  3.3. Chi tiết task
       bảng  Hiện tại | Mong muốn   (thêm cột đầu "Hình minh họa" hoặc "Hệ trang"/"Vị trí" khi cần)
       nhiều hạng mục → 3.3.1 / 3.3.2 … (hoặc a. b. c.), mỗi mục 1 bảng
       nhiều site → "3.3.1. Site 1 - Thế Giới Di Động", "3.3.2. Site 2 - Điện Máy Xanh"
  3.4. Tiêu chí nghiệm thu      ← BẮT BUỘC, bảng Hạng mục | Kết quả mong muốn
```

Biến thể 3.1 khi bài toán là "mất vùng / thiếu chức năng": nhãn **Vấn đề / Ảnh hưởng / Mục tiêu**
(Doc Giới thiệu hãng 28/09/2026). Lint chỉ cảnh báo, không chặn.

## Khung B — Vấn đề / Giải pháp

```text
TITLE
1. Thông tin yêu cầu task        (tự sinh)
2. Lịch sử cập nhật              (tự sinh — Ngày cập nhật | Người cập nhật | Nội dung cập nhật)
3. Tài liệu liên quan            (tuỳ chọn — STT | Tên tài liệu | Link; có thì đánh lại số các mục sau)
3. Mục đích task                 (1–2 câu)
  3.1. Xác định vấn đề
  3.2. Giải pháp đề xuất         (+ "Lợi ích" nếu cần thuyết phục, có thể dẫn tài liệu Google)
        CHỈ định hướng: làm hệ trang / tính năng gì, giao diện ra sao (1 câu mỗi ý), SEO làm gì,
        IT làm gì, cái gì không đổi, link giao diện. KHÔNG tên màn MDM/PIM, tên trường, giá trị
        dropdown, mã — người đọc chưa vào chi tiết; mấy thứ đó ở mục 4 (owner 03/11/2026)
  3.3. Phạm vi áp dụng           (bảng Hệ trang | URL)
4. Mô tả chi tiết
  4.1 … theo từng hệ trang       bảng theo loại task:
        Schema:  Thẻ Schema | Thuộc tính | Ý nghĩa | Giá trị dữ liệu | Nơi lấy giá trị
        OG:      Thẻ | Gán giá trị | Rule lấy giá trị | Trạng thái thẻ hiện tại
        Sitemap: Thuộc tính | Diễn giải & nơi lấy dữ liệu | Link CMS
        CMS/PIM: Vùng | Hiện tại | Sau khi bổ sung
                 (chỉ liệt kê vùng IT phải đụng; vùng giữ nguyên thì KHÔNG đưa vào bảng,
                  1 câu ở đầu mục 4.x "các vùng khác khai như …" là đủ — owner chốt 03/11/2026.
                  Chỉ dùng Vùng | Mô tả khai báo khi toàn bảng là vùng mới, không có "hiện tại".
                  Không gộp "Hiện tại:" và "Sau khi:" làm 2 bullet trong 1 ô — owner chê 03/11/2026)
        Code mẫu (JSON-LD, robots, dataLayer) → khối `code`
5. Tiêu chí nghiệm thu           ← BẮT BUỘC
```

## Khung C — BRD

```text
TITLE
1. Lịch sử thay đổi              (tự sinh — Ngày | Phiên bản | Nội dung thay đổi | Người yêu cầu | Người xác nhận | Note)
2. Các bên yêu cầu và xác nhận   (tự sinh — No. | Các bên yêu cầu | Bộ phận | Xác nhận | Ngày | Note)
3. Yêu cầu kinh doanh            (bối cảnh + mục tiêu đo được)
4. Phạm vi task                  (site, hệ thống bị ảnh hưởng, ngoài phạm vi)
5. Tài liệu tham khảo            (Nội dung | Link)
6. Business Rules / Rule …       (bảng ID | Rule, hoặc Thuộc tính | Nguồn lấy | Rule | Ví dụ)
7. Functions / API               (tuỳ chọn — Function | Rules, Response | Mô tả)
8. Ví dụ                         (ID | UI/UX | Associated BRs, hoặc link)
9. Tiêu chí nghiệm thu           ← BẮT BUỘC (thay Definition of Done)
```

## Mục 1 — bảng Thông tin (khung A/B, tự sinh)

| Trái | Phải |
| --- | --- |
| Bộ phận yêu cầu: `info.bo_phan_yeu_cau` | Ngày khởi tạo mô tả: `info.ngay_khoi_tao` |
| Lead task: `info.lead_task` | Support task: `info.support_task` |
| Designer: | Link design: |
| Ngày bắt đầu Live task: | Ngày kết thúc Live task: |
| Site áp dụng: `info.site_ap_dung` | cặp đầu của `info.extra` (vd Nơi khai báo) |
| Xác nhận trưởng bộ phận / trưởng nhóm: | |
| Trưởng nhóm: | Ngày xác nhận: |
| Trưởng BP: | Ngày xác nhận: |

- `bo_phan_yeu_cau` mặc định `SEO/Traffic`. Tên người luôn `Tên - MãNV`.
- Ô xác nhận / trưởng nhóm / trưởng BP **luôn để trống** — sếp tự điền khi duyệt. Agent
  không ghi "Đồng ý", không ghi tên người duyệt thay.
- Site áp dụng ghi số site + tên: `1 (Thế Giới Di Động), 2 (Điện Máy Xanh)`, `16 (TopZone)`,
  `10 (Nhà thuốc An Khang)`, `17 (AVAKids)`, `19 (Erablue)`.

## Mục Tiêu chí nghiệm thu (mọi khung)

Bảng `Hạng mục | Kết quả mong muốn`, ≥3 dòng. Mỗi dòng kiểm được bằng mắt hoặc bằng
view-source/GSC, không viết "hoạt động tốt". Luôn nghĩ tới:

- case chính (có dữ liệu) và case trống dữ liệu / ô khai báo để trống;
- trang không bị ảnh hưởng phải **giữ nguyên** (chống IT làm lan);
- từng site, desktop + mobile, core cũ / core mới nếu đang chạy song song;
- thứ SEO sẽ đo khi nghiệm thu: thẻ trong source, mã HTTP, canonical, robots, schema test.

## Update mô tả (mọi khung)

Không sửa đè nội dung cũ — IT có thể đang làm theo bản cũ. Mỗi đợt update:

1. Thêm 1 dòng vào bảng lịch sử (`build-doc.py --append-update` tự làm).
2. Nối khối `Update mô tả ngày dd/mm/yyyy - Tên MãNV` ở cuối Doc, bên trong lặp lại
   `1. Mục đích task / 2. Phạm vi áp dụng / 3. Chi tiết task (+ Tiêu chí nghiệm thu nếu đổi)`.
3. Chỉ ghi phần **thay đổi**, không chép lại toàn bộ mô tả.

Ví dụ thật: Doc Robots.txt ĐMX có 3 khối Update (15/01/2025, 22/05/2025, 05/12/2025).
