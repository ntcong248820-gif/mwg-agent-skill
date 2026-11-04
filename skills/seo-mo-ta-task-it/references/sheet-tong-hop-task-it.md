# Sheet tổng hợp task IT

ID: khoá `sheets.itTaskTracker` (harness.config.json). Không viết cứng ID vào file của skill.

## Tab

Mỗi site 1 tab cùng cấu trúc: `TGDĐ`, `ĐMX`, `TopZone`, `AN KHANG`, `AVAKids`, `ERA BLUE`
(+ `AI PLATFORM SEO & BLOG SEO` ẩn). Tab `TỔNG HỢP` là view gom, **không ghi vào**.
Tab `Data System` chứa danh sách dropdown. Task nhiều site → ghi vào tab của site chính
(task `[TGDĐ/ĐMX/TZ]` đang nằm ở tab TGDĐ).

## Cột (dòng 1, map theo tên — tab ĐMX/ERA BLUE có xuống dòng trong header)

| Cột | Ai điền | Skill ghi |
| --- | --- | --- |
| Thứ tự ưu tiên | SEO | `tracker.uu_tien` — dropdown `SEO 1`…`SEO 13`, `Hỏi Đáp 01`…, `KNH 01`…; owner quyết |
| Site | SEO | `tracker.site` — `TGDD`, `DMX`, `TopZone`, `Avakids`, `AnKhang`, `EraBlue`, `All Site` |
| Dự án | SEO | `tracker.du_an` — `TGDĐ`, `Điện Máy Xanh`, `All hệ`, `Hỏi Đáp + Game App`… |
| PIC | SEO | `tracker.pic` — `IT`, `PM`, `Content`, `PIM`, `CMS`, `IT + PM` |
| Trạng thái duyệt task | **Sếp** | **không ghi** — để trống chờ duyệt |
| Tên task | SEO | = title của Doc |
| Loại task | SEO | `tracker.loai_task` — `Bug` (đang sai) / `Task mới` (chưa có) |
| Mục đích task giải quyết vấn đề gì? | SEO | `tracker.muc_dich` — 2–4 câu |
| Link mô tả | SEO | URL Doc |
| Trạng thái task | SEO → IT | `New` lúc thêm; sau đó Kick-off / Doing / PO nghiệm thu / IT Fixing / Closed / Pending / Reject |
| Phụ trách Task | SEO | `tracker.phu_trach` — dropdown `Tên - MãNV` |
| Timeline hoàn thành kỳ vọng | SEO | `tracker.timeline_ky_vong` nếu đã chốt, không thì trống |
| Timeline thực tế, Ghi chú SEO, cột note IT | người khác | **không ghi** |

Nghĩa trạng thái (tab Data System): New = task mới từ SEO; Add X Task = được chọn làm trong
tháng; Kick-off = SEO kick-off với IT; Doing = IT nhận và xử lý; PO nghiệm thu = IT code xong,
SEO nghiệm thu; IT Fixing = IT fix theo checklist nghiệm thu; Closed = nghiệm thu xong.

## Ghi

`add-tracker-row.py` mặc định dry-run. Chỉ `--write` sau khi owner đồng ý trong lượt chat.
Script tự: kiểm dropdown, tìm dòng ngay sau dòng cuối có Tên task, chặn nếu dòng đó không
trống, xác nhận tài khoản gws, ghi `USER_ENTERED`, đọc lại so từng ô.
