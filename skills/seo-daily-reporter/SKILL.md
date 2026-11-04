---
name: seo-daily-reporter
description: "Báo cáo task hằng ngày cho SEO MWG: review File 1 để annotate trạng thái công việc hôm qua (Done/Pending/Đang làm), sau đó đề xuất 3+2 task cho ngày mới dựa theo Sheet Plan, GSC signal, và input user. Output sẵn sàng để copy. Trigger: 'báo task', 'report task ngày', 'điền trạng thái task', 'đề xuất task hôm nay', 'viết report ngày', 'daily report'."
user-invocable: true
when_to_use: "Dùng mỗi sáng khi cần (1) annotate trạng thái task hôm qua dựa File 1, và (2) đề xuất task ngày mới. Trigger: 'báo task', 'report task', 'task hôm nay', 'điền trạng thái', 'đề xuất task'."
category: seo-ops
keywords: [daily-report, task, báo cáo, trạng thái, đề xuất task, file1, gsc, plan]
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
---

# seo-daily-reporter

Tạo tin nhắn báo task 2 phần: annotate trạng thái hôm qua + đề xuất task hôm nay.
Output là một code block sẵn sàng copy, không cần chỉnh sửa thêm.

## KPI của workspace

KPI duy nhất: **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn **31/12/2026**. KPI **đếm keyword** — mọi KW bằng nhau, không
phân biệt KW chính/phụ, không nhân trọng số volume. Traffic **không có KPI riêng**.

`Nhóm NH = Laptop` gồm 5 sub-ngành hàng (`laptop` 839, `máy tính để bàn` 407,
`màn hình máy tính` 320, `máy in` 138, `phần mềm` 24). Lọc `Tên Ngành hàng = laptop`
chỉ phủ 49% phạm vi. Khi user nói "ngành hàng", hỏi rõ hoặc mặc định toàn bộ 1728 KW.

Đọc `docs/kpi-and-owner-context.md` trước khi đo, xếp ưu tiên, hay viết report.

## Tin tốt gửi ngành hàng — bắt buộc

Owner ở tâm thế phục vụ **nhân sự ngành hàng Laptop** — họ quan tâm kinh doanh, không
quan tâm kỹ thuật SEO. Thấy rank hoặc traffic tăng thì phải nêu ngay để owner nhắn cho
họ, không đợi được hỏi.

Mọi report của skill này phải có một mục riêng:

- URL/keyword nào vừa lên, **từ đâu tới đâu**, nhờ action nào.
- Tiếng Việt kinh doanh. **Không** dùng `RANK_CUSTOM`, `Xu hướng Tỷ lệ`, tên band,
  tên tab, tên cột trong mục này. Đủ gọn để forward thẳng.
- Nêu cả phần tụt ở mục "cần lưu ý" — không che.

Có cải tiến quy trình thì ghi **giờ làm trước → sau**. Không có số giờ thì không gọi
là tối ưu. Chi tiết: `docs/kpi-and-owner-context.md` mục 5.

## Scope

Skill này chỉ tổng hợp và format tin nhắn báo task. Không tạo task trong hệ thống,
không ghi File 1, không chạy audit kỹ thuật, không sửa content.

## Constants

```text
# File 1 — CV tuần (chỉ đọc)
FILE1_SPREADSHEET_ID  = "<file1Cv>"
FILE1_SHEET_NAME      = "Nguyễn Thành <Tên - Mã NV>"
FILE1_REPORT_LINK     = "https://docs.google.com/spreadsheets/d/<file1Cv>/edit?gid=867014327#gid=867014327"

# Planning Sheet — đọc action đã plan
PLANNING_SHEET_ID     = "<planOntopLaptop>"
PLANNING_TAB          = "Planning_Grid_V2"

# GSC property (đọc khi cần signal traffic)
GSC_PROPERTY          = "https://www.thegioididong.com/"
```

## Input của user

User cung cấp danh sách task hôm qua (không có trạng thái). Ví dụ:

```
Em báo task 03/08
1. Air bài Infobox PC Gaming lên website
2. Audit Content Infobox Laptop Gaming
3. Build Google Sheet tổng hợp số lượng Internal Link
4. Khai báo Title/Desc Laptop HP và Laptop AI lên CMS
5. Follow sức khỏe SEO & Traffic
```

User có thể bổ sung thêm danh sách task dự định cho ngày mới:

```
Hôm nay tao muốn làm:
- Viết bài PC Gaming
- Đo Rank
```

## Quy trình thực hiện

### Phase I — Annotate trạng thái task hôm qua

1. Xác định ngày hôm qua từ input user (ví dụ: `03/08/2026`).
2. Tính cột thứ của ngày đó bằng code:
   ```python
   from datetime import date
   d = date(YYYY, M, D)
   col_map = {0:"G",1:"H",2:"I",3:"J",4:"K",5:"L",6:"M"}
   col = col_map[d.weekday()]  # 4=Thứ 6→K, 5=Thứ 7→L ...
   ```
3. Đọc File 1 tab `FILE1_SHEET_NAME!A:P`, lọc các rows có cùng tháng/tuần và
   có giá trị tại cột thứ tương ứng (hoặc bất kỳ cột G–M nào chứa ngày đó trong note O).
4. Với mỗi task trong danh sách user, khớp với rows File 1 theo keyword:
   - Match keyword từ tên task với cột D (`CV chi tiết`) hoặc nội dung cột O (`Note`).
   - Ưu tiên match exact; fallback match từ khóa chính (ví dụ "Infobox PC Gaming" → row viết content).
5. Xác định trạng thái:
   - Cột thứ tương ứng **có giờ** → `Done`
   - Cột thứ tương ứng **trống** nhưng row tồn tại và có giờ ngày khác → `Đang làm`
   - Cột thứ tương ứng **trống** hoặc không tìm thấy row khớp → `Chưa làm`
   - Có note hoãn/dời cụ thể từ File 1 hoặc User → `Pending`
6. Soạn annotation `(Done - ...)` / `(Đang làm - ...)` / `(Pending - ...)` / `(Chưa làm)`:
   - Done: tóm tắt từ cột O (số lượng, hành động đã làm, link nếu có)
   - Đang làm: ghi % hoặc hành động đang tiến hành
   - Pending: chỉ dùng khi có ghi chú lý do thực tế từ File 1 hoặc user
   - Chưa làm: ghi đơn giản `(Chưa làm)`, KHÔNG tự suy diễn hay bịa lý do nếu File 1 / User không ghi chú
7. **Bổ sung công việc phát sinh từ File 1 (Ad-hoc Tasks)**:
   - Rà soát toàn bộ các rows trong File 1 có ghi nhận giờ (>0) vào ngày hôm qua.
   - Nếu row nào CHƯA được match với bất kỳ task nào trong danh sách user nhập, xếp vào mục `Phát sinh / Bổ sung:` dưới dạng các gạch đầu dòng `- ...` nằm ngay bên dưới danh sách task chính.

### Phase II — Đề xuất task ngày mới

Đọc 3 nguồn theo thứ tự ưu tiên:

**Nguồn 1 — Sheet Plan** (ưu tiên cao nhất):
- Đọc `PLANNING_SHEET_ID`, tab `PLANNING_TAB` (`Planning_Grid_V2`, `gid=1227786912`).
- Đọc chính xác các cột trạng thái thực thi của từng action theo URL & tuần hiện tại:
  + Cột T (`TD - Status`): Title & Description
  + Cột W (`IB - Status`): Infobox
  + Cột Z (`IMG - Status`): Hình ảnh Onpage
  + Cột AC (`AC - Status`): Audit Content
  + Cột AF (`IL - Status`): Internal Link
- **Ý nghĩa từng action (đừng suy diễn khác)**:
  + `IB` = lên bài Infobox **mới toanh** cho trang chưa có content.
  + `IMG` = làm hình ảnh onpage cho bài đó.
  + `AC` = sửa/audit lại content của một trang **đã có content từ trước** — không phải bước QA bắt buộc sau khi viết mới.
  + Khi một trang có `IB` + `IMG` đều `Done`, trang đó đã được viết mới và tối ưu đầy đủ ngay từ đầu. `AC` để trống trong trường hợp này là bình thường — KHÔNG suy diễn thành "còn thiếu QA" hay đề xuất làm `AC` tiếp theo cho trang đó.
  + Chỉ đề xuất `AC` cho trang đã có content cũ đang cần sửa/audit, không phải cho trang vừa `IB`+`IMG` xong.
- **QUY TẮC BẮT BUỘC**: Tuyệt đối KHÔNG đề xuất lại action đã có trạng thái `Done` trong Grid. Bắt buộc đối soát chi tiết từng cột trạng thái trước khi đề xuất; chỉ chọn các action đang `Planned`, `Đang làm`, hoặc `Blocked` cần xử lý.

**Nguồn 2 — Input user & Cam kết Order / Lịch họp**:
- Nếu user đã cung cấp danh sách task muốn làm, đưa vào làm task ưu tiên.
- Không loại bỏ bất kỳ task nào user đã nêu.
- Tích hợp các cam kết phối hợp với PO/IT/Ngành hàng (ví dụ: viết mô tả SEO H1, vùng Content trang mới/demo) và các lịch họp quan trọng (như Họp Go-Live Core Web).

**Nguồn 3 — GSC signal** (optional, khi cần data-driven):
- Khi filter theo `page`, phải có `query` trong `dimensions` (`query` hoặc
  `query,page`). Dùng `page` làm dimension duy nhất kèm filter page thì truy vấn trả
  rỗng sai dù URL có traffic — hành vi của chính GSC API, gọi trực tiếp cũng bị.
  `date` cũng bị (ra đủ dòng ngày nhưng metric = 0), phải dùng `query,date`.
  Đừng kết luận "URL không có traffic" từ 1 lần gọi rỗng.
- Chỉ đọc GSC khi user yêu cầu hoặc khi Nguồn 1+2 chưa đủ 5 task.
- Dùng MCP google-search-console để lấy top movers 7 ngày gần nhất.
- Ưu tiên URL có rank giảm mạnh hoặc CTR thấp bất thường.

**Tổng hợp**:
- Chọn **3 task ưu tiên** (core, phải làm) và **2 task optional** (nếu có thời gian).
- Mỗi task ghi thêm lý do chọn vào phần note bên dưới output (không nằm trong code block).

### Phase III — Format output

Output gồm 2 phần trong 1 code block duy nhất, ngăn cách bằng `===================`:

```
Em báo task {ngày hôm qua, format DD/MM}
1. Task A ({Trạng thái} - {Diễn giải siêu ngắn})
2. Task B (Chưa làm)
3. Task C ({Trạng thái} - {Diễn giải siêu ngắn})
Phát sinh / Bổ sung:
- {Tên CV phát sinh 1} ({Diễn giải siêu ngắn})
- {Tên CV phát sinh 2} ({Diễn giải siêu ngắn})
File Report CV: {FILE1_REPORT_LINK}
===================
Em báo task {ngày hôm nay, format DD/MM}
1. {Task ưu tiên 1 ngắn gọn: Động từ + Tên Hạng mục}
2. {Task ưu tiên 2 ngắn gọn: Động từ + Tên Hạng mục}
3. {Task ưu tiên 3 ngắn gọn: Động từ + Tên Hạng mục}
4. {Task optional 1 ngắn gọn}
5. {Task optional 2 ngắn gọn}
```

Sau code block, ghi thêm phần **Lý do chọn task hôm nay** (ngoài code block):
- Giải thích ngắn gọn tại sao chọn từng task (từ nguồn Plan, GSC, input user).

## Quy tắc viết annotation, chọn từ ngữ & 5 Bộ lọc tự kiểm duyệt

### 1. Tư duy cốt lõi (Mental Model)
Báo task gửi Quản lý / Ngành hàng là **bảng điểm sản phẩm bàn giao (Deliverables & Next Actions)**, KHÔNG PHẢI nhật ký chấm công (Timesheet) và KHÔNG PHẢI bản tường trình sự cố.
Người đọc cần nắm tiến độ dứt khoát, gọn gàng trong 5 giây; họ không muốn đọc thủ tục hành chính, không muốn nghe kể công và không muốn bị làm hoang mang bởi các con số sự cố.

Trước khi xuất bất kỳ tin nhắn báo task nào, AI **BẮT BUỘC** phải tự đối soát qua 5 bộ lọc sau:

---

### 2. 5 Bộ Lọc Tự Kiểm Duyệt (Self-Check Heuristics)

#### Bộ lọc 1: Bệnh Hành chính hóa / Thủ tục hóa (Bureaucratic Bloat)
- **Dấu hiệu nhận biết:** Các từ ngữ chỉ quy trình trung gian, thủ tục văn phòng, hoặc vị trí lưu trữ tài liệu thay vì bản thân công việc.
  - Ví dụ từ rác: *"nghiệp vụ"*, *"thủ tục"*, *"khai báo bổ sung Sheet..."*, *"phối hợp IT..."*, *"triển khai công tác..."*, *"quy trình..."*.
- **Câu hỏi tự kiểm:** *Nếu bỏ từ/cụm từ này đi, người đọc có mất thông tin cốt lõi nào về việc cần làm không?*
- **Quy tắc sửa:** Cắt bỏ hoàn toàn. Đi thẳng vào hành động và đối tượng:
  - ❌ *"Soạn mô tả nghiệp vụ Quicklink..."* → ✅ `Soạn mô tả Quicklink...`
  - ❌ *"Khai báo bổ sung Sheet mô tả nghiệp vụ Quicklink..."* → ✅ `Mô tả khởi tạo Quicklink...`
  - ❌ *"Phối hợp IT xử lý lỗi..."* → ✅ `Follow các lỗi...`

#### Bộ lọc 2: Bệnh Kịch tính hóa quy mô & Tự trói việc (Drama / Over-scoping)
- **Dấu hiệu nhận biết:** Nhồi số lượng lỗi chi tiết, con số to tát, hoặc từ ngữ giật gân vào **Plan ngày mới**.
  - Ví dụ từ gây hoang mang: *"Xử lý 371 URL lỗi sitemap"*, *"Khắc phục triệt để sự cố"*, *"Cứu rank khẩn cấp"*, *"Rà soát biến động sụt giảm"*.
- **Hệ quả tiêu cực:** 
  1. Gây cảm giác hệ thống đang gặp sự cố nghiêm trọng.
  2. Tự trói cam kết là hôm nay phải xử lý xong toàn bộ con số đó (trong khi vai trò của SEO thường là theo dõi/phối hợp).
- **Quy tắc sửa:**
  - **Plan ngày mới:** Tuyệt đối KHÔNG đưa số lượng lỗi/URL vào tên task. Chỉ dùng động từ điều hướng nhẹ nhàng, khái quát:
    - ❌ *"Phối hợp IT xử lý 371 URL lỗi sitemap sau nghiệm thu"* → ✅ `Follow các lỗi Nghiệm thu Core Web mới`.
  - **Báo cáo hôm qua:** Con số chi tiết CHỈ ĐƯỢC xuất hiện ở phần kết quả trong ngoặc đơn `(Done - ...)` để làm minh chứng.

#### Bộ lọc 3: Bệnh Đao to búa lớn / Trịnh trọng thái quá (Heavy / Pompous Phrasing)
- **Dấu hiệu nhận biết:** Dùng các cụm động từ ghép 3-4 chữ kiểu văn bản hành chính nhà nước, hoặc viết nguyên văn tên nền tảng dài dòng.
- **Câu hỏi tự kiểm:** *Dân kỹ thuật / SEO thực chiến ngoài đời có nói chuyện như thế này không?*
- **Bảng quy đổi sang văn phong thực chiến:**
  | Văn phong AI hành chính (CẤM) | Văn phong thực chiến SEO (BẮT BUỘC) |
  | :--- | :--- |
  | *Chạy hoàn tất* | **Khai báo** / **Chạy** |
  | *Rà soát biến động* | **Follow** / **Theo dõi** |
  | *Hoàn thiện luồng tự động hóa* | **Build tự động hóa** |
  | *Tiến hành triển khai* | **Làm** / **Viết** / **Build** |
  | *Google Business Profile* | **GMB** |
  | *Xây dựng tài liệu* | **Soạn mô tả** / **Viết tài liệu** |

#### Bộ lọc 4: Bệnh Kể lể việc hiển nhiên / Việc thở hàng ngày (Routine Hygiene Pollution)
- **Dấu hiệu nhận biết:** Đưa các hoạt động giao tiếp thường nhật (vốn là công cụ làm việc đương nhiên của mọi nhân sự) vào danh sách task chính hoặc mục "Phát sinh / Bổ sung".
  - Ví dụ: *"Trao đổi công việc qua LINE"*, *"Họp sync tiến độ"*, *"Check mail / tin nhắn"*, *"Cập nhật tiến độ hàng ngày"*, *"Daily review"*.
- **Câu hỏi tự kiểm:** *Hoạt động này có tạo ra một sản phẩm bàn giao (Deliverable) độc lập không, hay chỉ là phương tiện trao đổi để làm các việc khác?*
- **Quy tắc sửa:** **CẤM TUYỆT ĐỐI** đưa các việc mang tính "thở" (hygiene) này vào tin nhắn báo task. Báo task chỉ chứa các đầu việc tạo ra giá trị hoặc sản phẩm cụ thể.

#### Bộ lọc 5: Bệnh Động từ chung chung, mơ hồ (Vague Actions)
- **Dấu hiệu nhận biết:** Dùng động từ rỗng, không thể hiện được mục tiêu hoặc đầu ra của công việc.
  - Ví dụ: *"Rà soát dữ liệu tên sản phẩm..."*, *"Xử lý thông tin..."*.
- **Quy tắc sửa:** Động từ phải gắn liền với mục đích/đầu ra rõ ràng:
  - ❌ *"Rà soát dữ liệu tên sản phẩm Laptop phục vụ bổ sung size"* → ✅ `Review chốt cấu trúc tên sản phẩm Laptop phục vụ bổ sung size màn hình`.

---

### 3. Quy chuẩn từ vựng và thuật ngữ chuẩn

- **Cấm tiếng Anh rườm rà**: Tuyệt đối không dùng các cụm từ tiếng Anh rườm rà ("general-intent keywords", "intent-based", "IT/Tech Gadgets", "dispatch"...). Thay bằng tiếng Việt tự nhiên: "từ khóa tìm kiếm chung", "bộ từ khóa danh mục", "Ngành hàng Laptop".
- **Thuật ngữ chuẩn được phép dùng**: `onpage`, `internal link`, `rank`, `GSC`, `GA4`, `infobox`, `title`, `desc`, `canonical`, `index`, `sitemap`, `Ahrefs`, `AI Overview`, `SERP`, `GMB`, `Core Web`.
- **Độ dài diễn giải kết quả hôm qua `(Done - ...)`**: Tối đa 5-10 từ, tập trung vào số lượng hoàn thành hoặc kết quả bàn giao cụ thể.
- **Pending & Chưa làm**:
  - `Pending`: chỉ ghi kèm lý do ngắn gọn nếu có ghi chú rõ ràng từ người dùng hoặc hệ thống.
  - `Chưa làm`: ghi duy nhất `(Chưa làm)`, tuyệt đối không suy đoán lý do.

## Security

- Chỉ đọc File 1, Planning Sheet, GSC — không ghi bất kỳ file nào.
- Không đọc credentials, `.env`, token, OAuth.
- Không tự thêm/bớt task không có trong input user hoặc nguồn data.
