# File 2 Writing Rules

File 2 / Công việc TGDD là bảng tổng hợp hạng mục. Không ghi chi tiết từng
action nhỏ như File 1.

## Row Shape

| Cột | Cách viết |
| --- | --- |
| Loại công việc | Chọn nhóm dễ hiểu: Technical SEO, Đo lường, Content, Onpage / Internal Link, Dữ liệu, Research, Nghiệm thu, Trao đổi, Công cụ / Quản lý |
| Đầu việc | Tên hạng mục, ngắn và rõ |
| Mô tả công việc | 1-2 câu, nói đã làm gì và phạm vi chính |
| Hiệu quả đạt được | Luôn nối về ranking, traffic, sức khỏe web, crawl/index, hoặc tốc độ xử lý SEO |
| Link File | Link task, Sheet, Drive, report |
| Ghi chú thêm | Chỉ ghi blocker hoặc next step quan trọng |

## Hiệu Quả Đạt Được (Cột D)

Cột D duy trì **1 nội dung tổng hợp lũy kế mới nhất**, không chia dồn hay append theo từng tuần (`Tuần N, tháng M`). Mỗi lần report mới, **cập nhật đè (update)** ô Cột D với số liệu và trạng thái mới nhất theo cấu trúc:

```text
- Tổng số lượng: {Tổng số lượng URL / Keyword / Lỗi / Khối lượng}
- Đã xử lý: {Khối lượng đã hoàn thành / live}
- % Tiến độ: {Tỷ lệ % hoàn thành hoặc % giảm lỗi}
- Hiệu quả thực tế (Số liệu trước ➔ sau):
  + Clicks: {Trước} ➔ {Sau} ({+/- %})
  + Impressions: {Trước} ➔ {Sau} ({+/- %})
  + Position: {Trước} ➔ {Sau} ({bậc})
- Diễn giải thêm (nếu có): {Bối cảnh, nguyên nhân hoặc trao đổi BA/IT}
-> TÁC ĐỘNG KPI: {Câu chốt kết nối tới KPI SEO chung}.
```

*Lưu ý tính linh hoạt:* Với các task không đủ dữ kiện số lượng/xử lý (như Build Tool, Sheet System, Trao đổi), điều chỉnh các dòng Tiến độ / Tiết kiệm thời gian cho phù hợp nhưng **bắt buộc mỗi con số/ý kiến nằm trên 1 dòng riêng**.

### Ví dụ cấu trúc chuẩn Cột D:

#### Task Technical SEO / Audit (Có số lượng & % tiến độ):
```text
- Tổng số lượng lỗi: 8.788 URL (Broken links) & 3.853 URL (404 in sitemap)
- Đã xử lý: 8.467 URL (Broken links) & 2.717 URL (404 in sitemap)
- % Tiến độ: Giảm 96.35% (Broken links) & Giảm 70.52% (404 in sitemap)
- Lỗi Canonical points to redirect (5.580 URL): 100% thuộc 1 mẫu /lich-su-mua-hang/dang-nhap?callbackUrl=... (Báo IT sửa nhanh lại template)
- Lỗi Sitemap (3XX 9.355 URL & Noindex 10.531 URL): Đã báo chị Nguyệt BA, chờ Go-Live Core Web mới (06/08) để tiếp tục review và xử lý tiếp với IT.
-> TÁC ĐỘNG KPI: Tối ưu ngân sách crawl, loại bỏ link hỏng và trang rác, nâng cao sức khỏe toàn trang.
```

#### Task đo lường / GSC / Push Rank:
```text
- Tổng số lượng: 205 keyword trên TGDĐ & DMX
- Đã xử lý: Đo rank 7 ngày & verify 1.015 dòng rank giữa Sheet và GSC
- % Tiến độ: Đạt 97.14% MATCH (986/1.015 dòng)
- Hiệu quả thực tế:
  + Clicks: 12.000 ➔ 14.100 (+17.5%)
  + Impressions: 120.000 ➔ 162.000 (+35.0%)
  + Position: 14.2 ➔ 8.5 (cải thiện +5.7 bậc)
-> TÁC ĐỘNG KPI: Đảm bảo dữ liệu rank chính xác 100% phục vụ planning và push top keyword.
```

#### Task Tool / Sheet System / Automation (linh hoạt):
```text
- Tổng số lượng: 4 module tự động hóa (Rank_Run, Movement, Impact, Summary Sheet)
- Đã xử lý: Build hoàn thiện 4/4 module
- % Tiến độ: 100% hoàn thành
- Tiết kiệm thời gian: ~15h/tuần làm báo cáo thủ công
-> TÁC ĐỘNG KPI: Tăng tốc độ ra quyết định planning, giúp ưu tiên chính xác các URL/Keyword tụt rank.
```

#### Task Trao đổi / Phối hợp:
```text
- Tiến độ: Đã chốt workflow phối hợp với team Dev & Content cho 3 task Technical & Infobox lớn.
- Kết quả: Thống nhất tiêu chí nghiệm thu SEO, gỡ bỏ toàn bộ blocker vận hành, đảm bảo task triển khai không gây ảnh hưởng tiêu cực đến cấu trúc URL hiện tại.
-> TÁC ĐỘNG KPI: Đảm bảo các task ảnh hưởng trực tiếp đến website được triển khai đúng tiến độ và chuẩn SEO, gián tiếp thúc đẩy mục tiêu ranking và KPI chung.
```

## Examples

### Sheet System

| Cột | Nội dung |
| --- | --- |
| Loại công việc | Công cụ / Quản lý |
| Đầu việc | Build hệ thống Google Sheet quản lý SEO Planning & Rank Tracking |
| Mô tả công việc | Chuẩn hóa dữ liệu rank, action đã làm và timeline biến động để phục vụ planning. Build các sheet Rank_Run, Rank_Movement, Action_Event, Impact_Timeline và KPI summary. |
| Hiệu quả đạt được | Giúp theo dõi keyword chưa đạt top 1-2 rõ hơn, ưu tiên đúng URL cần xử lý để cải thiện ranking và traffic. |
| Link File | Link task hoặc Sheet |
| Ghi chú thêm | Tiếp tục dọn Planning Sheet và luồng order |

### Trao Đổi Công Việc

| Cột | Nội dung |
| --- | --- |
| Loại công việc | Trao đổi |
| Đầu việc | Trao đổi lỗi Technical SEO cần xử lý |
| Mô tả công việc | Phối hợp với team liên quan để làm rõ lỗi đang ảnh hưởng tới SEO và hướng xử lý tiếp theo. |
| Hiệu quả đạt được | Giúp xử lý task ảnh hưởng SEO nhanh hơn, cải thiện sức khỏe website và hạn chế ảnh hưởng tới ranking/traffic. |
| Link File | Link task hoặc Sheet |
| Ghi chú thêm | Nếu còn blocker, ghi ngắn owner hoặc next step |

## Giọng Văn & Định Dạng Trình Bày

Người đọc là **người làm SEO** — họ hiểu thuật ngữ chuyên ngành, không cần giải thích lại khái niệm cơ bản.

### Quy tắc định dạng & sử dụng từ ngữ:

1. **MỖI Ý MỘT DÒNG (Rất quan trọng):**
   - Mỗi kết quả, mỗi tiến độ hoặc số liệu tách biệt thành **1 dòng riêng** (`- ...`).
   - Tuyệt đối KHÔNG gom nhiều ý, nhiều hành động hoặc số liệu vào cùng một câu dài gây khó đọc.
2. **Dùng từ ngữ bình thường, tự nhiên, chuyên nghiệp:**
   - Dùng: *"cải thiện"*, *"tăng"*, *"nâng cao"*, *"hỗ trợ"*, *"tối ưu"*, *"cải thiện thứ hạng"*, *"tăng trưởng traffic"*, *"đảm bảo tiến độ"*, *"từ khóa mục tiêu"*.
3. **Tuyệt đối KHÔNG dùng từ ngữ cường điệu, hoa mỹ hoặc làm quá:**
   - Tránh hoàn toàn: *"bứt phá"*, *"trọng điểm"*, *"thần tốc"*, *"khẩn cấp cứu rank"*, *"ngoạn mục"*, *"vượt trội"*, *"siêu việt"*, *"bứt phá đỉnh cao"*.
4. **Gọi đúng tên ngành hàng:**
   - Dùng "Ngành hàng Laptop" cho Laptop/Màn hình/Máy in/PC/Gaming. Không dùng từ lóng tiếng Anh ("IT/Tech Gadgets").
5. **Thuật ngữ — theo phép thử người ngoài, KHÔNG dịch máy móc:**
   - **Giữ nguyên** thuật ngữ SEO (`crawl`, `index`, `canonical`, `sitemap`, `anchor text`, `E-E-A-T`, `Impressions`, `Clicks`, `Position`, `CTR`, `backlink`, `landing page`...) và thuật ngữ agent (`skill`, `agent`, `prompt`, `token`, `Claude`, `Codex`, `Antigravity`). Đây là ngôn ngữ nghề, quản lý đọc được. **Đừng dễ hiểu quá** — dịch hết ra tiếng Việt dân dã làm báo cáo mất chuyên môn.
   - **Phải bỏ** tên hệ thống/sheet/tab/cột của riêng mình: `Plan Ontop`, `Data Rank`, `Data Order`, `WF đi link`, `Action_Event`, `Master Lookup`, `Cột O`... Người ngoài không biết đó là gì. Viết tác dụng thay cho tên.
   - **Đổi hoặc giải thích ngắn** thuật ngữ kỹ thuật hẹp: `mixed content`, `crawl trap`, `facet`, `errorCount`, `SKU`, `PO/BA`, `cannibalize`, `staging`.
   - Chi tiết đầy đủ: `SKILL.md` mục `## Ngôn Ngữ: Phép Thử Người Ngoài`.

5b. **Con số phải là con số hiệu quả:**
   - **Luôn ghi:** traffic, thứ hạng, số từ khóa Top 1-2, lượt hiển thị, giờ làm trước ➔ sau.
   - **Được ghi:** số bài đã viết, số việc đã xử lý, số trang, số dòng dữ liệu, số link đã lên.
   - **Bỏ:** số quy trình nội bộ — "vá 6 lỗi", "112 file mã nguồn", "29.600 dòng code", "400 bài kiểm tự động", "10/11 phần việc". Người đọc không có mốc nào để biết 6 lỗi là nhiều hay ít. Thay bằng: giờ làm được gì mà trước đây không làm được.
6. **SO SÁNH SỐ LIỆU GSC TRƯỚC VS SAU KHI HÀNH ĐỘNG (BẮT BUỘC):**
   - Mọi công việc có thể liên hệ số liệu (Content/Infobox, Internal Link, Onpage, Technical) **BẮT BUỘC phải kiểm tra và trình bày dưới dạng SO SÁNH TRƯỚC VS SAU (P1 vs P2)**.
   - **Tự hỏi để so sánh:**
     - *Chèn Internal Link*: Bài tin đã chèn link trỏ về URL nào? Clicks, Impressions, Position của các URL nhận link **trước vs sau khi chèn** thay đổi thế nào?
     - *Viết Infobox / Content*: Viết Infobox xong thì Clicks, Impressions, Position của trang đó **trước vs sau khi live bài** cải thiện ra sao?
     - *Technical / Audit*: **Trước vs sau khi fix**, lỗi giảm bao nhiêu URL, Googlebot cào/index biến động như thế nào, Clicks/Impressions tổng cate thay đổi ra sao?

### Ví dụ bad → good

| ❌ Bad (Làm quá / Tiếng Anh trang trí) | ✅ Good (Tự nhiên, chuyên nghiệp) |
| --- | --- |
| Bứt phá ranking Top 1-2 và tăng trưởng bứt phá Organic Traffic cho nhóm keyword trọng điểm | Cải thiện thứ hạng Top 1-2 và hỗ trợ tăng trưởng Organic Traffic cho nhóm keyword mục tiêu |
| Nâng cao chỉ số Rich Media trên trang sản phẩm để tăng thời gian on-site (Dwell Time), nâng cao tín hiệu E-E-A-T và hỗ trợ trực tiếp cải thiện tỷ lệ chuyển đổi đơn hàng (CR) | Tạo thêm video trên trang cho số lượng lớn sản phẩm để tăng thời gian on-site, nâng cao tín hiệu E-E-A-T và hỗ trợ cải thiện tỷ lệ chuyển đổi đơn hàng |
| Xây dựng hệ thống dữ liệu multi-source phục vụ attribution model | Build Sheet tổng hợp rank, action, biến động để phục vụ planning |

### Tóm tắt

> Viết cho đồng nghiệp SEO đọc nhanh, hiểu ngay. Tự nhiên, bình thường, chuyên nghiệp nhưng không làm quá hay dùng từ cường điệu.

## Avoid

- **Không dùng từ ngữ cường điệu:** bứt phá, trọng điểm, thần tốc, khẩn cấp cứu rank...
- Không viết quá technical hoặc dùng tiếng Anh trang trí.
- Không ghi log từng giờ làm.
- Không ghi "đã hỗ trợ tốt hơn" mà không nối với SEO KPI.
- Không claim ranking/traffic đã tăng nếu chưa có dữ liệu đo.
- Không ghi quá dài; mỗi ô nên đọc nhanh được.
- Không giải thích thuật ngữ SEO cơ bản cho người đọc.
