# Journal Sections — Cách Viết

Chi tiết cách viết từng phần journal. Chỉ load khi cần ví dụ cụ thể.

## `## Current State`

Đây là phần AI đọc đầu tiên khi resume task. Phải trả lời được 4 câu trong 10 giây.

```markdown
## Current State

| Field | Value |
| --- | --- |
| Đã làm | Build xong 3 tab rank, verify readback 120 dòng |
| Đang kẹt | Chờ user chốt trọng số band cho công thức xếp ưu tiên |
| Next action | Áp trọng số band vào script plan sau khi có quyết định |
| Plan hiện tại | — |
| Report mới nhất | `reports/260809-1102-build-rank-summary.md` |
```

Quy tắc:

- **Đã làm**: kết quả cụ thể, có số. Không viết "đã xử lý một số việc".
- **Đang kẹt**: blocker thật. Không có thì ghi `—`, đừng bịa.
- **Next action**: một hành động khởi động được ngay, không phải mục tiêu chung.
  Viết "Áp trọng số band vào script plan", không viết "hoàn thiện hệ thống".
- **Report mới nhất**: đúng tên file timestamped mới nhất. Đây là dòng
  `seo-task-state-audit` kiểm để bắt `CURRENT_STATE_STALE`.

Sai thường gặp: viết Current State theo kế hoạch thay vì theo thực tế. Nếu report
mới nhất nói khác README, **tin report**.

## `## Next Steps`

Dùng checkbox để `seo-task-state-audit` phân biệt task còn việc hay không.

```markdown
## Next Steps

- [x] Build tab `Rank_Run`
- [x] Verify readback 120 dòng
- [ ] Áp trọng số band vào script plan
- [ ] Bàn giao cho team content
```

Quy tắc:

- Tick `[x]` mục vừa xong thay vì xóa, để giữ dấu vết.
- Task hết mục `[ ]` và im trên 7 ngày sẽ bị gắn nhãn `close-candidate`.
- Mỗi mục là một hành động, không phải một chủ đề.

## `reports/index.md`

Format canonical, chốt 09/08/2026, dùng cho **mọi** task:

```markdown
| Date | Type | File | Nội dung |
| --- | --- | --- | --- |
| 2026-08-09 11:02 | build | [rank summary](260809-1102-build-rank-summary.md) | Build `Rank_Summary`, trọng số band chờ chốt |
```

Quy tắc từng cột:

| Cột | Format | Ghi chú |
| --- | --- | --- |
| Date | `YYYY-MM-DD HH:MM` | Bỏ `HH:MM` khi file không có timestamp, ví dụ `resume-brief.md` |
| Type | một từ, chữ thường | Lấy từ vocabulary bên dưới |
| File | `[nhãn ngắn](tên-file.md)` | Nhãn suy từ tên file, bỏ prefix ngày và từ type |
| Nội dung | một câu | Kết quả cụ thể, ưu tiên có số |

Vocabulary `Type` đang dùng trong workspace:

```text
audit  build  research  decision  cleanup  report  handoff  resume
validation  repair  fix  rework  reference  polish  format  pack  backfill
```

Cần type mới thì thêm một từ, chữ thường, và dùng lại cho các lần sau. Không
dùng cụm dài kiểu `Auth retest + package` hay `Sheet kế hoạch WHAT-only` — chi
tiết đó thuộc về cột `Nội dung`.

Thêm dòng mới ở cuối bảng, theo thứ tự thời gian tăng dần.

Nếu task chưa có `index.md` và task còn chạy dài, tạo mới:

```markdown
# Reports Index — {Tên Task}

Timeline report trong task này.

## Reports

| Date | Type | File | Nội dung |
| --- | --- | --- | --- |
```

Phần khác ngoài bảng, ví dụ `## Planned Reports` hay `## Unresolved Questions`,
đặt sau bảng và giữ nguyên khi thêm dòng.

## `reports/resume-brief.md`

Bắt buộc với `initiative`. Đây là bộ nhớ dài hạn, không phải nhật ký.

Cấu trúc:

```markdown
# Resume Brief — {Tên Task}

## Bối Cảnh
{2-4 câu: task này giải quyết gì, phạm vi tới đâu}

## Đã Chốt
- {quyết định đã chốt, mỗi dòng một ý, giữ nguyên qua nhiều phiên}

## Đang Làm
{phase hiện tại + trạng thái}

## Chưa Chốt
- {câu hỏi còn treo}
```

Quy tắc:

- **Đã Chốt** chỉ thêm, gần như không sửa. Đây là thứ giữ cho các phiên sau khỏi
  quyết định lại từ đầu.
- Không copy nguyên report vào đây. Resume brief là bản cô đọng.
- Khi một mục "Chưa Chốt" được quyết, chuyển nó lên "Đã Chốt" kèm ngày.

## Report Mới

Đặt tên: `reports/{yymmdd-hhmm}-{type}-{slug}.md`

Cấu trúc tối thiểu:

```markdown
# {Tiêu đề}

## Scope
{làm gì, phạm vi, lệnh/nguồn dữ liệu}

## Kết Quả
{bảng số liệu trước/sau nếu có}

## Đã Làm
{từng việc, có bằng chứng}

## Còn Lại
{việc chưa xong và lý do}

## Unresolved Questions
{câu hỏi cần user chốt}
```

Nguyên tắc: số liệu trước, nhận định sau, câu hỏi chưa rõ cuối. Tiếng Việt ngắn.

## Khi Nào Không Dùng Skill Này

| Tình huống | Skill đúng |
| --- | --- |
| Task đã xong hẳn, cần đóng | `seo-task-done` |
| Cần tạo task mới | `seo-task-create` |
| Cần ghi File 1 / CV tuần | `seo-log-cv` |
| Cần ghi File 2 / Công việc TGDD | `seo-log-weekly-work` |
| Cần quét toàn bộ task xem cái nào lệch | `seo-task-state-audit` |
