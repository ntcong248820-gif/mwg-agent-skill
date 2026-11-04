# Report Template — seo-task-state-audit

Ghi report vào:

```text
tasks/260805-skill-context-management-direction/reports/{yymmdd-hhmm}-audit-task-state.md
```

Sau khi ghi, thêm 1 dòng vào `reports/index.md` của task đó nếu file index tồn tại.

Viết tiếng Việt ngắn. Số liệu trước, đề xuất sau, câu hỏi chưa rõ cuối.

---

## Cấu Trúc

```markdown
# Task State Audit {DD/MM/YYYY}

## Scope

- Ngày chạy: {YYYY-MM-DD}
- Lệnh: `python3 <skill_dir>/scripts/audit-task-state.py --root . --format md`
- Phạm vi: {N} task ({X} root, {Y} work item)
- Threshold: in-progress 14d, blocked 30d, archive 60d

## Tổng Quan

| Lifecycle | Số task | Ghi chú |
| --- | ---: | --- |
| `active` | | |
| `sync-pending` | | |
| `close-candidate` | | |
| `stale-watch` | | |
| `archive-candidate` | | |
| `legacy-no-frontmatter` | | |

| Flag | Severity | Số task |
| --- | --- | ---: |
| | | |

## P1 — Cần Xử Lý Trước

Liệt kê theo nhóm flag, không liệt kê từng task rời rạc nếu cùng nguyên nhân.

### {FLAG_CODE} — {số task}

Nguyên nhân: {1-2 câu}

| Task | Status | Idle | Chi tiết |
| --- | --- | ---: | --- |
| | | | |

Đề xuất: {hành động cụ thể, skill nào chạy tiếp}

## P2 — Xử Lý Đợt Sau

{cùng cấu trúc, gọn hơn}

## P3 — Nhiễu Nhẹ

{gộp thành 1 đoạn, không cần bảng dài}

## Đề Xuất Thứ Tự Xử Lý

1. {đợt 1 — phạm vi, số task, skill dùng}
2. {đợt 2}
3. {đợt 3}

## Không Đề Xuất Làm

- {task/nhóm cố ý bỏ qua và lý do, ví dụ legacy task chưa mở lại}

## Unresolved Questions

- {câu hỏi cần user chốt}
```

---

## Quy Tắc Viết

- Gom task theo nguyên nhân, không dump nguyên bảng script vào report.
- Mỗi nhóm P1 phải có đề xuất hành động cụ thể kèm tên skill sẽ chạy tiếp.
- Ghi rõ task nào cố ý không đụng và vì sao. Im lặng bỏ qua sẽ gây hiểu nhầm ở
  lần audit sau.
- Không kết luận task "vô dụng" chỉ vì idle cao. Idle là tín hiệu, không phải
  phán quyết.
- Nếu audit chạy lại nhiều lần, so với report gần nhất và ghi phần "Đã xử lý từ
  lần trước" ngay dưới `## Tổng Quan`.
