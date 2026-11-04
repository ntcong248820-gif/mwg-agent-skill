# README Template — seo-task-create

Use this template for `tasks/{folder}/README.md`.

```markdown
---
title: "{Task Title}"
slug: "{yymmdd-short-task-slug}"
status: in-progress
category: "{seo-audit | content | technical | research | reporting}"
owner: "Thành <Tên - Mã NV>"
created: "{YYYY-MM-DD}"
updated: "{YYYY-MM-DD}"
priority: P2
workstream: "{sheet-system | analytics | seo-task | content | technical | research | other}"
task_type: "{initiative | work_item | single}"
parent_task: "{parent slug or empty}"
report_targets:
  file1_cv: true
  file2_weekly: true
report_sync:
  file1_cv: pending
  file2_weekly: pending
---

# {Task Title}

## Metadata

| Field | Value |
| --- | --- |
| Ngày tạo | {DD/MM/YYYY} |
| Cập nhật | {DD/MM/YYYY} |
| Trạng thái | 🟡 In Progress |
| Phụ trách | Thành <Tên - Mã NV> |
| Danh mục | {category} |
| Priority | P2 |
| Workstream | {workstream} |
| Task type | {task_type} |
| Parent task | {parent or —} |

## Current State

| Field | Value |
| --- | --- |
| Đã làm | Chưa bắt đầu |
| Đang kẹt | Không có |
| Next action | ... |
| Plan hiện tại | — |
| Report mới nhất | — |

## Goal

{1-2 câu mô tả mục tiêu và output mong muốn.}

## Inputs

- `data/raw/` — dữ liệu gốc.
- Link Google Sheet / Drive / tài liệu nếu có.

## Method

1. Thu thập dữ liệu.
2. Phân tích hoặc triển khai.
3. Lưu output và bằng chứng.

## Results

| Metric | Trước | Sau | So sánh |
| --- | --- | --- | --- |
| — | — | — | — |

**Trạng thái xử lý:** Đang xử lý.

**Tóm tắt kết quả:** Chưa có.

## Outputs

- `data/processed/`
- `reports/`

## Report Sync

| Report target | Status | Ghi chú |
| --- | --- | --- |
| File 1 / CV tuần | pending | Dùng `seo-log-cv` nếu cần log giờ làm |
| File 2 / Công việc TGDD | pending | Dùng `seo-log-weekly-work` để tổng hợp hạng mục |

## External Links

| Loại | Link |
| --- | --- |
| Google Sheet / Drive | — |
| File 2 - Work Report | https://docs.google.com/spreadsheets/d/bifHI63Td1zKmyKD5_9qBtOtjgOC0DP4l4TGO0 |

## Scripts

- Task scripts: `scripts/`
- Scratch scripts: `/tmp`

## Next Steps

- [ ] ...

## Unresolved Questions

- None.
```

For initiative tasks, also create `roadmap.md`, `reports/resume-brief.md`, and
`reports/index.md`.
