---
name: seo-attendance-keo-cong
description: "Báo cáo kéo công MWG: review File 1 & lịch sử task, điền bảng công việc minh chứng (File 2 <Tên - Mã NV>), điền file kéo công nội bộ (format chấm công), và soạn tin nhắn xin anh Thanh xác nhận. Trigger: kéo công, quên chấm công, báo cáo công, xin xác nhận công, điền file chấm công, report kéo công."
user-invocable: true
when_to_use: "Dùng khi cần xử lý các ngày quên chấm công: review công việc, điền minh chứng File 2, chuẩn bị file kéo công nội bộ, và soạn tin xin TL xác nhận. Trigger: 'kéo công', 'quên chấm công', 'báo cáo công', 'điền file chấm công', 'report kéo công tháng', 'xin xác nhận công'."
category: seo-ops
keywords: [kéo công, chấm công, báo cáo, quên chấm công, file công, xin xác nhận]
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
---

# seo-attendance-keo-cong

Xử lý trọn vẹn quy trình kéo công MWG: từ review task đến soạn tin nhắn xin xác nhận TL.

## Scope

Skill này chỉ xử lý quy trình kéo công nội bộ MWG. Không ghi File 1 CV (dùng `seo-log-cv`), không sửa dữ liệu rank/traffic, không tạo/đóng task SEO.

> **QUAN TRỌNG**: Không được điền cột I và J trong File 2 (`<Tên - Mã NV>`). Hai cột này là phần xác nhận của quản lý, chỉ TL mới được điền sau khi xem xét.

## Constants

```text
# File 2 — Bảng công việc minh chứng
FILE2_SPREADSHEET_ID = "<attendanceEvidence>"
FILE2_SHEET_NAME     = "<Tên - Mã NV>"

# File kéo công nội bộ (gửi sếp)
INTERNAL_SPREADSHEET_ID = "UtGMHvUKty35L6Z_fNEJgdi9zXrHlZdIgKr1aE"
INTERNAL_SHEET_NAME     = "format chấm công"
INTERNAL_VUNG1_RANGE    = "format chấm công!B9:D40"  # Ngày chấm | Yêu cầu | Lý do
INTERNAL_CHUAN_RANGE    = "format chấm công!F9:G18"  # Bảng chuẩn Yêu cầu / Lý do

# File 1 — CV tuần (chỉ đọc để lấy context)
FILE1_SPREADSHEET_ID = "<file1Cv>"
FILE1_SHEET_NAME     = "Nguyễn Thành <Tên - Mã NV>"

# Người xác nhận
TL_NAME = "Thanh SEO"
TL_ID   = "133641"
```

## Quy trình thực hiện (4 bước)

### Bước 1 — Xác định các ngày quên chấm công

1. Hỏi user nếu chưa có danh sách ngày quên chấm.
2. Với mỗi ngày, xác nhận loại lỗi chấm công:
   - `Quên chấm công giờ ra về - Kéo công`
   - `Quên chấm công cả ngày - Kéo công`
   - `WFH - Kéo công`

### Bước 2 — Review công việc và điền File 2 (`<Tên - Mã NV>`)

Với mỗi ngày quên chấm công:

1. **Đọc File 1** (`FILE1_SPREADSHEET_ID`, tab `FILE1_SHEET_NAME`): lọc các rows có cột
   G/H/I/J/K/L/M khớp ngày làm việc đó để lấy danh sách công việc và thời gian. Đọc luôn
   **cột P (`File chi tiết`)** trong cùng lượt — đó là nguồn link minh chứng, đọc thiếu
   thì phải quay lại lần hai.
   **Bẫy lọc:** cột `Thứ 4` tuần nào cũng có, nên phải lọc **cả `Tuần N` lẫn `Tháng M`**
   rồi mới đọc cột ngày. Lọc thiếu `Tuần` sẽ gom cả 4 tuần và ra tổng giờ vô lý
   (đo thật 31/08: ra 25h cho một ngày).
2. **Đọc lịch sử task** trong `tasks/`: kiểm tra README, reports/resume-brief.md, báo cáo của ngày đó để bổ sung chi tiết.
3. **Đọc lịch sử chat** nếu user cung cấp conversation ID hoặc gợi ý Antigravity history.
4. **Tổng hợp danh sách công việc** cho ngày đó, rồi **gộp các đầu việc cùng luồng**
   theo `## Gộp Task Cùng Một Luồng` trước khi soạn dòng.
5. **Đọc File 2** để tìm đúng hàng (row) tương ứng với ngày — thường lọc theo cột A (ngày tháng).
6. **Soạn nội dung điền cho các cột A-H** (bỏ qua I và J):
   - Ghi đúng ngày, tên nhân viên, mô tả công việc
   - Cột E: chọn link theo `## Link Minh Chứng — Ưu Tiên Google Workspace`; có link thì
     viết ngắn, không link thì viết đủ ý
   - Ngôn từ theo bảng ở `### Từ hành chính phải đổi`
7. **Preview nội dung** cho user xem và xác nhận trước khi ghi.
8. **Ghi vào File 2** với `USER_ENTERED`, chỉ ghi cột A–H; tuyệt đối bỏ trống I và J.
9. **Readback** range vừa ghi, **so từng ô A-H với payload** (không chỉ đếm số dòng), và
   xác nhận cột I/J vẫn trống. Ghi đè ít dòng hơn lần trước thì phải `values clear` phần dư.
10. **Kiểm tổng giờ mỗi ngày khớp File 1** — lệch là gộp sai hoặc sót đầu việc.
11. Ghi lại số dòng đầu/cuối vừa ghi để dựng `&range=` cho tin nhắn ở Bước 4.

### Bước 3 — Điền file kéo công nội bộ (`format chấm công`)

1. **Đọc bảng chuẩn** `INTERNAL_CHUAN_RANGE` (`F9:G18`) để lấy đúng wording `Yêu cầu` và `Lý do`.
2. **Đọc `INTERNAL_VUNG1_RANGE`** (`B9:D40`) để biết cấu trúc hiện tại và xác định đúng row theo ngày tháng.
3. **Cập nhật toàn bộ lịch tháng** vào cột B nếu chưa điền tháng hiện tại (tính thứ/ngày
   đúng theo lịch, định dạng `Thứ 4, 5 /8`). File chỉ có **một sheet duy nhất** và dùng lại
   mỗi tháng — ghi lịch tháng mới sẽ **xóa dữ liệu tháng cũ**. Xác nhận với user trước khi
   ghi đè. Vùng `B10:D40` đúng 31 dòng: tháng 30 ngày thì xóa dòng cuối, tháng 28-29 ngày
   thì xóa 2-3 dòng cuối.
4. **Điền `Yêu cầu` (cột C) và `Lý do` (cột D)** chỉ cho các ngày quên chấm, dùng wording chuẩn từ bảng F:G:
   - `Quên chấm công giờ ra về - Kéo công` → Lý do: `Em bắt đầu công việc lúc [8:00] và kết thúc công việc lúc [16:30] đã báo trưởng nhóm trong group và có xác nhận trong file`
   - `Quên chấm công cả ngày - Kéo công` → Lý do tương tự
   - `WFH - Kéo công` → Lý do: `đã báo trưởng nhóm trên group và đã xác nhận chi tiết công việc ở link trên`
5. **Readback** `B9:D40` để xác nhận đúng.
6. **Báo cáo kết quả** cho user (các row đã điền).

### Bước 4 — Soạn tin nhắn xin xác nhận TL

Sau khi hoàn thành Bước 2 và 3, soạn sẵn tin nhắn gửi TL để xin xác nhận cột I và J:

```text
Dạ anh @{TL_NAME} {TL_ID} em có điền file report công việc các ngày
{LIST_NGAY_QUEN_CHAM}
Nhờ anh {TL_NAME} hỗ trợ xác nhận các task em làm vào ngày này với ạ, em cám ơn anh {TL_NAME}
{FILE2_URL_KEM_RANGE}
```

**Link phải kèm `&range=` trỏ đúng khối dòng vừa ghi** (owner chốt 31/08/2026). File có
gần 200 dòng trải nhiều tháng; đưa link trần bắt sếp tự cuộn đi tìm.

```text
https://docs.google.com/spreadsheets/d/{FILE2_SPREADSHEET_ID}/edit?gid={GID}#gid={GID}&range={DONG_DAU}:{DONG_CUOI}
```

Ví dụ đã dùng: `...#gid=808822567&range=174:189` cho khối 16 dòng ghi ngày 31/08.
`{DONG_DAU}:{DONG_CUOI}` là số dòng thật vừa ghi, lấy từ bước readback — không đoán.

Trong đó `{LIST_NGAY_QUEN_CHAM}` là danh sách các ngày theo format:
```
{DD}/{MM}: {Loại lỗi chấm công}
```

Ví dụ output hoàn chỉnh:
```
Dạ anh @Thanh SEO 133641 em có điền file report công việc các ngày
03/07: Quên chấm công
09/07: Quên chấm công
29/07: Quên chấm công
Nhờ anh Thanh hỗ trợ xác nhận các task em làm vào ngày này với ạ, em cám ơn anh Thanh
https://docs.google.com/spreadsheets/d/<attendanceEvidence>/edit?gid=808822567#gid=808822567
```

Hiển thị tin nhắn này dạng code block cho user dễ copy.

## Gộp Task Cùng Một Luồng — Làm TRƯỚC khi ghi

Owner chốt 31/08/2026: các đầu việc **nối nhau trong cùng một luồng** thì gộp thành
**một dòng**, cộng thời gian lại. File này để sếp xác nhận người đó có đi làm hôm đó,
không phải bảng kê chi tiết — 13 dòng vụn khó đọc hơn 10 dòng gọn.

Nhận diện luồng: các đầu việc cùng phục vụ **một sản phẩm đầu ra** hoặc là **các bước
kế tiếp của một quy trình**.

| Gộp được | Thành |
| --- | --- |
| Làm hình ➔ Tối ưu Onpage ➔ On-Air (cùng một bài) | 1 dòng, cộng giờ |
| Tối ưu Title/Desc ➔ Khai báo Title/Desc lên CMS | 1 dòng, cộng giờ |
| Nhiều lần trao đổi ngắn, cùng loại, đều không có link | 1 dòng, liệt kê từng ý |

Không gộp khi:

- Hai việc **khác sản phẩm đầu ra** (làm hình bài A và viết bài B).
- Mỗi việc có **file bằng chứng riêng quan trọng** mà gộp vào sẽ chôn mất link — trừ khi
  dòng gộp giữ được đủ cả 2 link.
- Hai việc **khác ngày**. Đây là ngoại lệ cứng: file này ghi công theo ngày, tổng giờ mỗi
  ngày phải khớp cột ngày tương ứng trong File 1. Gộp chéo ngày làm một ngày dư giờ và
  một ngày thiếu giờ — sai lệch trên chính hồ sơ chấm công. Luồng chéo ngày thì để 2 dòng
  nhưng **đặt chung một tên cột C** (ví dụ `Title/Desc`) để sếp nhìn ra là một mạch việc.

**Kiểm sau khi gộp:** tổng giờ mỗi ngày phải bằng đúng tổng cột ngày đó ở File 1. Lệch
là gộp sai.

## Link Minh Chứng — Ưu Tiên Google Workspace

Thứ tự ưu tiên khi chọn link cho cột E:

1. **Google Docs / Sheets / Drive** — ưu tiên cao nhất, sếp mở được ngay, thấy đủ quá trình làm.
2. URL trang đã lên web — dùng khi cần chứng minh bài đã publish.
3. Link nội bộ khác (CMS, trang bản thử) — chỉ dùng khi không có nguồn nào ở trên.
4. **KHÔNG dùng `file://`** — đường dẫn máy cá nhân, người khác mở không được.

Nguồn lấy link: **cột P (`File chi tiết`) của File 1**, đúng dòng đầu việc đó. Đọc cột P
cùng lúc với cột G-M khi lọc giờ, đừng đọc thiếu rồi phải quay lại.

**Không tự gán link.** Dòng nào cột P của File 1 để trống thì ô E **không có link** — viết
mô tả chi tiết thay thế. Gán một Sheet "trông có vẻ liên quan" vào việc không sinh ra nó
là tạo bằng chứng giả trên hồ sơ chấm công. Lỗi này đã mắc ngày 31/08 ở 2 dòng
`Follow sức khỏe SEO` (gán nhầm sheet đo thứ hạng) và phải gỡ ra.

### Có link thì viết ngắn, không link thì viết đủ

| Tình huống | Cách viết ô E |
| --- | --- |
| **Có link** | `Hoàn thành` + 1 câu tóm tắt kết quả + link. Đừng liệt kê dài — link đã nói hết. |
| **Không có link** | `Hoàn thành` + danh sách đánh số, mỗi ý một việc cụ thể đã làm. Đây là bằng chứng duy nhất nên phải đủ để đọc là hình dung ra được đã làm gì. |

## Quy tắc ghi nội dung (File 2)

- Ngôn ngữ: tiếng Việt **phổ thông, nói sao viết vậy**. Đây là file gửi sếp đọc lướt,
  không phải văn bản hành chính.

### Từ hành chính phải đổi (owner chốt 31/08/2026)

Viết chữ nghiêm trang không làm việc trông giá trị hơn, chỉ làm câu khó đọc hơn.

| Đừng viết | Viết |
| --- | --- |
| rà soát, đối soát | kiểm tra, xem lại, so lại |
| dứt điểm | xong, xong hết |
| ghi nhận | thấy, đã cập nhật |
| biến động | thay đổi |
| chốt định hướng | thống nhất hướng làm |
| chuẩn hóa | chỉnh lại cho đúng chuẩn |
| bằng chứng công việc | file kết quả |
| scope | nhóm, phạm vi |
| sinh alt/title | tự động viết alt/title |
| khởi tạo | tạo, làm mới |
| triển khai | làm, thực hiện |

Quét cột D và E tìm các từ trên trước khi ghi. Giữ nguyên `nghiệm thu` — đây là từ MWG
dùng hằng ngày, đổi đi còn khó hiểu hơn.
- Không dùng tiếng Anh jargon; chỉ dùng: `onpage`, `internal link`, `rank`, `GSC`, `infobox`, `title`, `desc`, `canonical`, `index`, `sitemap`.
- Dùng "Ngành hàng Laptop" thay cho "IT/Tech Gadgets" hay "Laptop/Màn hình".
- Công việc done: `(Done - Đã ...)` với mô tả kết quả ngắn gọn.
- Khi không có link Drive/doc: viết dạng:
  ```
  Hoàn thành
  1. Thực hiện A
  2. Xử lý B
  ```

## Cột I và J — Phần quản lý xác nhận

**TUYỆT ĐỐI KHÔNG GHI** vào cột I (`Xác nhận quản lý`) và cột J (`Trạng thái duyệt`) trong File 2.
Hai cột này chỉ dành cho TL/quản lý điền sau khi xem xét.
Nếu user yêu cầu điền I/J, nhắc nhở user và từ chối.

## Security

- Chỉ đọc File 1 để lấy context, không ghi.
- Chỉ ghi File 2 sau khi user xác nhận preview.
- Chỉ ghi File kéo công nội bộ sau khi xác nhận.
- Không đọc credentials, `.env`, token, OAuth files.
- Không ghi bất kỳ sheet nào ngoài `FILE2_SPREADSHEET_ID` và `INTERNAL_SPREADSHEET_ID`.
