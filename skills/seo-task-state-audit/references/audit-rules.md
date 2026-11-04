# Audit Rules — seo-task-state-audit

Tài liệu này giải thích từng flag, threshold, và cách quyết định hành động.
Chỉ load khi cần diễn giải kết quả sâu hơn bảng tóm tắt trong `SKILL.md`.

## Threshold

| Tham số | Giá trị | Lý do |
| --- | ---: | --- |
| `STALE_IN_PROGRESS_DAYS` | 14 | Task đang làm mà 2 tuần không đụng thì nhiều khả năng đã rơi |
| `STALE_BLOCKED_DAYS` | 30 | Task blocked thường chờ người khác hoặc điều kiện ngoài, cho thời gian dài hơn |
| `ARCHIVE_CANDIDATE_DAYS` | 60 | Quá 2 tháng không hoạt động thì nên chốt bỏ hay làm tiếp |
| `CLOSE_CANDIDATE_IDLE_DAYS` | 7 | Hết next step mở và im 1 tuần thì gần như đã xong, chỉ thiếu bước đóng |

Chốt ngày 09/08/2026. Đổi threshold thì sửa hằng số đầu file
`scripts/audit-task-state.py` và cập nhật bảng này cùng lúc.

`days_idle` lấy mốc mới nhất giữa field `updated` trong frontmatter và mtime file
mới nhất trong task folder. Không tính `work-items/` con, `node_modules/`,
`__pycache__/`, và `.DS_Store`, để task cha không bị "làm mới" oan bởi con.

## Bảng Flag

### P1 — Sai lệch trạng thái thật, xử lý trước

| Flag | Điều kiện | Ý nghĩa | Hành động |
| --- | --- | --- | --- |
| `NOT_IN_REGISTRY` | Task **lớn** (`initiative`, hoặc status còn mở, hoặc `priority: P1`) không có trong `tasks/_registry.md` | Task vô hình khi resume | Thêm 1 dòng registry |
| `REGISTRY_STATUS_MISMATCH` | Status trong registry khác README | Hai nguồn nói khác nhau, README là nguồn đúng | Sửa registry theo README |
| `MISSING_FRONTMATTER` | README không mở đầu bằng `---` | Task lịch sử trước khi có schema | Chỉ bổ sung khi mở lại task |
| `WORKITEM_NO_PARENT` | `task_type: work_item` nhưng `parent_task` trống | Work item mồ côi | Điền `parent_task` |
| `WORKITEM_PARENT_MISMATCH` | `parent_task` khác tên folder cha thật | Khai sai cha, sai luôn index | Sửa `parent_task` theo folder thật |

### P2 — Thiếu chuẩn, xử lý theo đợt

| Flag | Điều kiện | Hành động |
| --- | --- | --- |
| `MISSING_FIELD` | Thiếu field bắt buộc trong frontmatter | Bổ sung theo `tasks/_templates/task-readme-template.md` |
| `LOG_PENDING` | `status: done` và `report_targets.X: true` nhưng `report_sync.X` không phải `synced`/`not-needed` | Chạy `seo-log-cv` hoặc `seo-log-weekly-work` khi rảnh, hoặc đổi target thành `not-needed` nếu thật sự không cần. **Không** đề xuất mở lại task — task done là done. |
| `MISSING_SYNC_STATE` | `report_targets.X: true` nhưng không có `report_sync.X` | Thêm `pending` hoặc `not-needed` |
| `DONE_WITHOUT_RESULTS` | `status: done` nhưng `## Results` trống hoặc còn placeholder | Điền số liệu thật; không có metric thì ghi status rõ |
| `STALE_IN_PROGRESS` | `in-progress` và idle ≥ 14 ngày | Hỏi user còn làm tiếp không |
| `STALE_BLOCKED` | `blocked` và idle ≥ 30 ngày | Kiểm blocker còn đúng không |
| `WORKITEM_NOT_INDEXED` | Work item chưa xuất hiện trong parent `reports/index.md` lẫn `_workstreams.md` | Thêm dòng vào parent index |
| `INITIATIVE_MISSING_FILE` | Initiative thiếu `roadmap.md`, `reports/resume-brief.md`, hoặc `reports/index.md` | Bổ sung file scaffold |

### P3 — Nhiễu nhẹ, gom lại làm sau

| Flag | Điều kiện | Hành động |
| --- | --- | --- |
| `CURRENT_STATE_STALE` | `## Current State` không nhắc tên report timestamp mới nhất | Cập nhật dòng "Report mới nhất" |
| `NOT_IN_REGISTRY_MINOR` | Task lẻ đã `done`/`cancelled`, priority P2/P3, chưa index registry | Không cần làm gì. Chỉ thêm khi task hoá ra quan trọng hơn dự kiến |

### Policy Registry (chốt 09/08/2026)

`tasks/_registry.md` **cố ý không index hết** mọi task. Nó chỉ giữ task lớn:

- mọi `initiative`;
- mọi task còn mở (`draft`, `in-progress`, `blocked`) — vì đây là thứ cần tra khi resume;
- mọi task `priority: P1`.

Task lẻ đã xong như check rank GSC, viết infobox, convert một bộ data thì không
thêm vào, để bảng không loãng. Chúng vẫn nằm trong `tasks/` và vẫn được skill
này quét đầy đủ, chỉ hạ xuống `NOT_IN_REGISTRY_MINOR` mức P3.

Hệ quả: một task `done` P2 không có trong registry là **bình thường**. Nhưng khi
task đó được mở lại (`status` về `in-progress`), flag sẽ tự nâng lên P1.

## Thứ Tự Phân Loại Lifecycle

Script gán đúng một label, xét theo thứ tự sau, dừng ở điều kiện khớp đầu tiên:

1. Không có frontmatter → `legacy-no-frontmatter`.
2. Status thuộc `draft`/`in-progress`/`blocked`:
   - idle ≥ 60 → `archive-candidate`;
   - không còn `- [ ]` trong `## Next Steps` và idle ≥ 7 → `close-candidate`;
   - vượt threshold stale theo status → `stale-watch`;
   - còn lại → `active`.
3. Còn lại → `active`.

Không còn label `sync-pending`. Trước đây status `done` mà còn nợ log bị ghi đè
lifecycle thành `sync-pending`, tức "task này trông như xong nhưng chưa xong".
Bỏ đi vì nó sai: task xong là xong, còn nợ log là một cờ (`LOG_PENDING`) đi kèm,
không phải một pha khác của task. Ghi đè làm mất chính thông tin cần để trả lời
"tuần này đóng được mấy việc".

Report cũ có thể còn chứa `sync-pending`; script vẫn xếp nó đúng thứ tự khi đọc
lại, chỉ không sinh ra label đó nữa.

## Nguyên Tắc Khi Đề Xuất

- Không gộp nhiều loại hành động vào một đề xuất. Tách rõ: sửa registry, log
  báo cáo, đóng task, bổ sung metadata.
- Không đề xuất đóng hàng loạt task cùng lúc. Hỏi user chọn nhóm ưu tiên.
- Không đề xuất xóa. Task hết giá trị thì `cancelled`, kèm lý do trong README.
- Không tự đổi `report_targets` thành `false` để né flag. Chỉ đổi khi user xác
  nhận task đó thật sự không cần báo cáo.
- Initiative không đóng chỉ vì work item con đã xong.

## Giới Hạn Đã Biết

- `days_idle` dựa vào mtime, nên copy/move file có thể làm task trông mới hơn
  thực tế. Khi con số bất thường, mở README kiểm tra `updated` trước khi kết luận.
- Script không đọc live File 1/File 2. `report_sync` phản ánh những gì đã ghi
  trong README, không phải trạng thái thật trên Google Sheet.
- Script không phát hiện task trùng mục tiêu. Việc đó cần đọc `## Goal`.
