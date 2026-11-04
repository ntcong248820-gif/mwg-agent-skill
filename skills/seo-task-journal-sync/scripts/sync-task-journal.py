#!/usr/bin/env python3
"""Đồng bộ phần cơ học của task journal, và báo phần cần người viết.

Script tự sửa: `updated` trong frontmatter, ô "Cập nhật" trong bảng Metadata, và
dòng registry tương ứng. Script KHÔNG tự viết văn xuôi cho `## Current State`,
`reports/index.md`, hay `resume-brief.md` — các mục đó cần phán đoán nội dung,
script chỉ chỉ ra chỗ đang lệch và format bảng index đang dùng.

Dry-run mặc định. Thêm --apply để ghi thật.

Usage:
    python3 sync-task-journal.py --root . --task 260805-abc
    python3 sync-task-journal.py --root . --task 260805-abc --report 260809-1102-audit-x.md
    python3 sync-task-journal.py --root . --task 260805-abc --status done --apply
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date

VALID_STATUS = {"draft", "in-progress", "done", "blocked", "cancelled"}
# Format canonical của reports/index.md, chốt 09/08/2026.
CANONICAL_INDEX_HEADER = "| Date | Type | File | Nội dung |"


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def find_task(tasks_dir: str, slug: str) -> str | None:
    """Tìm README của task, ở root hoặc trong work-items của bất kỳ initiative nào."""
    direct = os.path.join(tasks_dir, slug, "README.md")
    if os.path.isfile(direct):
        return direct
    for parent in sorted(os.listdir(tasks_dir)):
        nested = os.path.join(tasks_dir, parent, "work-items", slug, "README.md")
        if os.path.isfile(nested):
            return nested
    return None


def frontmatter_value(head: str, key: str) -> str:
    match = re.search(rf'^{key}:\s*"?([^"\n]*)"?\s*$', head, re.M)
    return match.group(1).strip() if match else ""


def newest_report(reports_dir: str) -> str | None:
    if not os.path.isdir(reports_dir):
        return None
    stamped = sorted(f for f in os.listdir(reports_dir)
                     if f.endswith(".md") and re.match(r"^\d{6}-\d{4}-", f))
    return stamped[-1] if stamped else None


def index_format(index_path: str) -> str | None:
    """Trả về dòng header của bảng trong index.md để agent viết dòng khớp."""
    for line in read(index_path).splitlines():
        if line.startswith("|") and "---" not in line:
            return line.strip()
    return None


def section(body: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)", body, re.M | re.S)
    return match.group(1).strip() if match else ""


def sync_registry(registry_path: str, slug: str, fields: dict) -> tuple[str, bool]:
    """Cập nhật dòng registry của slug theo frontmatter. Trả về (nội dung mới, có đổi)."""
    text = read(registry_path)
    if not text:
        return text, False
    out, changed = [], False
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")] if line.startswith("| `") else None
        if cells and cells[0].strip("`") == slug and len(cells) >= 8:
            new = list(cells)
            if fields.get("title"):
                new[1] = fields["title"]
            new[2] = f'`{fields["status"]}`'
            new[3] = f'`{fields["category"].lower()}`'
            new[4] = f'`{fields["workstream"]}`'
            new[6] = fields["created"]
            new[7] = fields["updated"]
            if new != cells:
                changed = True
            out.append("| " + " | ".join(new) + " |")
        else:
            out.append(line)
    return "\n".join(out) + "\n", changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync phần cơ học của task journal.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--task", required=True, help="task slug")
    parser.add_argument("--report", help="tên file report mới, để kiểm tra đã vào index chưa")
    parser.add_argument("--status", help=f"đổi status, một trong {sorted(VALID_STATUS)}")
    parser.add_argument("--today", help="ghi đè ngày hôm nay YYYY-MM-DD (dùng cho test)")
    parser.add_argument("--apply", action="store_true", help="ghi thật thay vì dry-run")
    args = parser.parse_args()

    if args.status and args.status not in VALID_STATUS:
        print(f"error: status không hợp lệ: {args.status}", file=sys.stderr)
        return 2

    root = os.path.abspath(args.root)
    tasks_dir = os.path.join(root, "tasks")
    readme = find_task(tasks_dir, args.task)
    if not readme:
        print(f"error: không tìm thấy task `{args.task}` trong {tasks_dir}", file=sys.stderr)
        return 2

    today = args.today or date.today().isoformat()
    dmy = f"{today[8:10]}/{today[5:7]}/{today[0:4]}"
    task_dir = os.path.dirname(readme)
    original = read(readme)
    head, sep, body = original.partition("\n---\n")
    if not sep:
        print(f"error: {readme} không có YAML frontmatter", file=sys.stderr)
        return 2

    actions, manual = [], []

    # --- Phần script tự sửa ---
    new_head = head
    if frontmatter_value(head, "updated") != today:
        new_head = re.sub(r'^updated:\s*".*"$', f'updated: "{today}"', new_head, flags=re.M)
        actions.append(f'frontmatter `updated` -> {today}')
    if args.status and frontmatter_value(head, "status") != args.status:
        new_head = re.sub(r"^status:\s*.*$", f"status: {args.status}", new_head, flags=re.M)
        actions.append(f'frontmatter `status` -> {args.status}')

    new_body, n = re.subn(r"(\|\s*\*{0,2}Cập nhật\*{0,2}\s*\|\s*)[^|]*(\|)",
                          rf"\g<1>{dmy} \g<2>", body)
    if n and new_body != body:
        actions.append(f'bảng Metadata "Cập nhật" -> {dmy}')
    if args.status:
        new_body, n2 = re.subn(r"(\|\s*\*{0,2}Trạng thái\*{0,2}\s*\|\s*)[^|]*(\|)",
                               rf"\g<1>{args.status} \g<2>", new_body)
        if n2:
            actions.append(f'bảng Metadata "Trạng thái" -> {args.status}')

    result = new_head + sep + new_body

    # --- Registry ---
    registry_path = os.path.join(tasks_dir, "_registry.md")
    fields = {k: frontmatter_value(new_head, k)
              for k in ("title", "status", "category", "workstream", "created", "updated")}
    reg_text, reg_changed = sync_registry(registry_path, args.task, fields)
    if reg_changed:
        actions.append("sync dòng `tasks/_registry.md` theo frontmatter")
    elif f"| `{args.task}`" not in read(registry_path):
        if fields["status"] in {"draft", "in-progress", "blocked"} \
                or frontmatter_value(new_head, "priority").upper() == "P1":
            manual.append("Task lớn nhưng chưa có dòng trong `tasks/_registry.md` — cần thêm tay")

    # --- Phần cần người viết ---
    reports_dir = os.path.join(task_dir, "reports")
    latest = args.report or newest_report(reports_dir)
    if latest:
        current_state = section(new_body, "Current State")
        if current_state and latest not in current_state:
            manual.append(f'`## Current State` chưa trỏ tới report mới nhất `{latest}`')
        index_path = os.path.join(reports_dir, "index.md")
        if os.path.isfile(index_path):
            header = index_format(index_path)
            if header and header != CANONICAL_INDEX_HEADER:
                manual.append(f'`reports/index.md` sai format canonical\n'
                              f'        đang dùng: {header}\n'
                              f'        cần dùng : {CANONICAL_INDEX_HEADER}')
            if latest not in read(index_path):
                manual.append(f'`reports/index.md` thiếu dòng cho `{latest}`\n'
                              f'        format: {CANONICAL_INDEX_HEADER}')
        elif os.path.isdir(reports_dir):
            manual.append("Chưa có `reports/index.md`; tạo nếu task còn chạy dài")

    brief = os.path.join(reports_dir, "resume-brief.md")
    if frontmatter_value(new_head, "task_type") == "initiative" and not os.path.isfile(brief):
        manual.append("Initiative thiếu `reports/resume-brief.md`")

    open_steps = len(re.findall(r"^\s*-\s*\[ \]", section(new_body, "Next Steps"), re.M))
    if args.status == "done" and open_steps:
        manual.append(f"Đóng task nhưng `## Next Steps` còn {open_steps} mục chưa tick")

    for key in ("file1_cv", "file2_weekly"):
        target = re.search(rf"^  {key}: (.*)$", new_head, re.M)
        states = re.findall(rf"^  {key}: (.*)$", new_head, re.M)
        if args.status == "done" and target and len(states) == 2:
            want, state = states[0].strip(), states[1].strip()
            if want.lower() == "true" and state not in {"synced", "not-needed"}:
                manual.append(f"`report_targets.{key}: true` nhưng `report_sync.{key}: {state}` "
                              f"— dùng seo-log-cv / seo-log-weekly-work trước khi đóng")

    # --- Ghi ---
    if args.apply:
        if result != original:
            with open(readme, "w", encoding="utf-8") as fh:
                fh.write(result)
        if reg_changed:
            with open(registry_path, "w", encoding="utf-8") as fh:
                fh.write(reg_text)

    label = "ĐÃ SỬA" if args.apply else "SẼ SỬA"
    print(f"Task: {os.path.relpath(readme, root)}\n")
    print(f"{label} (tự động):")
    print("\n".join(f"  - {a}" for a in actions) if actions else "  - không có gì cần đổi")
    print("\nCẦN NGƯỜI VIẾT (script không tự làm):")
    print("\n".join(f"  ! {m}" for m in manual) if manual else "  - không có")
    if not args.apply:
        print("\n(dry-run — thêm --apply để ghi thật)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
