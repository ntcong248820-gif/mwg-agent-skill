#!/usr/bin/env python3
"""Smoke tests cho sync-task-journal.py. Không mạng, không đụng workspace thật.

Run:
    python3 test-journal-sync-smoke.py
"""

import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

spec = importlib.util.spec_from_file_location("journal_sync",
                                              os.path.join(HERE, "sync-task-journal.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

FRONTMATTER = """---
title: "Demo"
slug: "260809-demo"
status: in-progress
category: "Research"
owner: "Thành <Tên - Mã NV>"
created: "2026-08-01"
updated: "2026-08-01"
priority: P2
workstream: "other"
task_type: "single"
parent_task: ""
report_targets:
  file1_cv: true
  file2_weekly: false
report_sync:
  file1_cv: pending
  file2_weekly: not-needed
---

## Metadata

| Field | Value |
| --- | --- |
| **Cập nhật** | 01/08/2026 |
| **Trạng thái** | In Progress |

## Current State

| Field | Value |
| --- | --- |
| Report mới nhất | `reports/260801-0900-old-report.md` |

## Next Steps

- [ ] còn việc
"""

REGISTRY = ("| Task Slug | Title | Status | Category | Workstream | Owner | Created | Updated |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| `260809-demo` | Old Title | `draft` | `other` | `other` | X | 2026-08-01 | 2026-07-01 |\n")


def build(tmp, *, nested=False, with_index=True, reports=("260801-0900-old-report.md",)):
    parts = ["tasks"] + (["260721-parent", "work-items"] if nested else []) + ["260809-demo"]
    task_dir = os.path.join(tmp, *parts)
    os.makedirs(os.path.join(task_dir, "reports"))
    with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as fh:
        fh.write(FRONTMATTER)
    for name in reports:
        with open(os.path.join(task_dir, "reports", name), "w", encoding="utf-8") as fh:
            fh.write("# report\n")
    if with_index:
        with open(os.path.join(task_dir, "reports", "index.md"), "w", encoding="utf-8") as fh:
            fh.write("# Index\n\n| Date | Type | File | Nội dung |\n| --- | --- | --- | --- |\n")
    with open(os.path.join(tmp, "tasks", "_registry.md"), "w", encoding="utf-8") as fh:
        fh.write(REGISTRY)
    return task_dir


def run(tmp, extra=()):
    argv = sys.argv
    sys.argv = ["x", "--root", tmp, "--task", "260809-demo", "--today", "2026-08-09", *extra]
    from io import StringIO
    buf, real = StringIO(), sys.stdout
    sys.stdout = buf
    try:
        code = mod.main()
    finally:
        sys.stdout, sys.argv = real, argv
    return code, buf.getvalue()


def check(label, cond):
    print(f"{'PASS' if cond else 'FAIL'}  {label}")
    return cond


def main():
    ok = True

    # 1. Dry-run không ghi gì
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = build(tmp)
        before = open(os.path.join(task_dir, "README.md"), encoding="utf-8").read()
        code, out = run(tmp)
        after = open(os.path.join(task_dir, "README.md"), encoding="utf-8").read()
        ok &= check("dry-run trả về 0", code == 0)
        ok &= check("dry-run không sửa README", before == after)
        ok &= check("dry-run báo sẽ đổi updated", "updated` -> 2026-08-09" in out)

    # 2. --apply sửa đúng frontmatter + metadata + registry
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = build(tmp)
        run(tmp, ["--apply"])
        text = open(os.path.join(task_dir, "README.md"), encoding="utf-8").read()
        reg = open(os.path.join(tmp, "tasks", "_registry.md"), encoding="utf-8").read()
        ok &= check("apply cập nhật frontmatter updated", 'updated: "2026-08-09"' in text)
        ok &= check("apply cập nhật bảng Metadata", "| **Cập nhật** | 09/08/2026 |" in text)
        ok &= check("apply sync registry title", "| Demo |" in reg and "Old Title" not in reg)
        ok &= check("apply sync registry status", "`in-progress`" in reg)
        ok &= check("apply sync registry updated", "2026-08-09 |" in reg)
        ok &= check("apply hạ category về chữ thường", "`research`" in reg)

    # 3. Đổi status
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = build(tmp)
        _, out = run(tmp, ["--status", "done", "--apply"])
        text = open(os.path.join(task_dir, "README.md"), encoding="utf-8").read()
        ok &= check("status -> done", "status: done" in text)
        ok &= check("apply cập nhật bảng Metadata Trạng thái", "| **Trạng thái** | done |" in text)
        ok &= check("cảnh báo next step chưa tick", "chưa tick" in out)
        ok &= check("cảnh báo report_sync pending", "report_sync.file1_cv: pending" in out)
        ok &= check("không cảnh báo file2 (not-needed)", "report_sync.file2_weekly" not in out)

    # 4. Phát hiện report mới chưa vào index và Current State
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp, reports=("260801-0900-old-report.md", "260809-1200-new-report.md"))
        _, out = run(tmp)
        ok &= check("phát hiện Current State lệch report mới", "Current State` chưa trỏ" in out)
        ok &= check("phát hiện index thiếu dòng", "index.md` thiếu dòng" in out)
        ok &= check("in ra format canonical", "| Date | Type | File | Nội dung |" in out)

    # 4b. Phát hiện index sai format canonical
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = build(tmp)
        with open(os.path.join(task_dir, "reports", "index.md"), "w", encoding="utf-8") as fh:
            fh.write("# Index\n\n| Ngày | Loại | File | Trạng thái |\n| --- | --- | --- | --- |\n")
        _, out = run(tmp)
        ok &= check("phát hiện index sai format canonical", "sai format canonical" in out)

    with tempfile.TemporaryDirectory() as tmp:
        build(tmp)  # index.md dựng sẵn đúng canonical
        _, out = run(tmp)
        ok &= check("index đúng canonical -> không báo sai format",
                    "sai format canonical" not in out)

    # 5. Work item lồng trong initiative
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp, nested=True)
        code, out = run(tmp)
        ok &= check("tìm được task lồng trong work-items", code == 0 and "work-items" in out)

    # 6. Thiếu index.md
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp, with_index=False)
        _, out = run(tmp)
        ok &= check("báo thiếu reports/index.md", "Chưa có `reports/index.md`" in out)

    # 7. Lỗi đầu vào
    with tempfile.TemporaryDirectory() as tmp:
        build(tmp)
        sys.argv = ["x", "--root", tmp, "--task", "khong-co", "--today", "2026-08-09"]
        ok &= check("task không tồn tại -> exit 2", mod.main() == 2)

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
