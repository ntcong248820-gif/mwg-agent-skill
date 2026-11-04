#!/usr/bin/env python3
"""Read-only audit of task state in the mwg-ai-worker workspace.

Scans every task README (root tasks and work items), parses YAML frontmatter,
cross-checks the registry / workstream index / parent report index, then emits
flags and a lifecycle label per task.

The script never writes into tasks/ and never changes frontmatter. It only
prints JSON or Markdown to stdout, or writes to an explicit --out path.

Usage:
    python3 audit-task-state.py --root . --format md
    python3 audit-task-state.py --root . --format json --out /tmp/audit.json
    python3 audit-task-state.py --root . --status in-progress --format md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime

# Thresholds in days. Decided 2026-08-09, see references/audit-rules.md.
STALE_IN_PROGRESS_DAYS = 14
STALE_BLOCKED_DAYS = 30
ARCHIVE_CANDIDATE_DAYS = 60
CLOSE_CANDIDATE_IDLE_DAYS = 7

REQUIRED_FIELDS = [
    "title", "slug", "status", "category", "owner",
    "created", "updated", "priority", "workstream", "task_type",
]
OPEN_STATUSES = {"draft", "in-progress", "blocked"}
SKIP_DIR_PARTS = {"node_modules", ".git", "__pycache__", "_templates"}
# Chỉ bắt câu placeholder thật sự. KHÔNG bắt `—` hay `n/a`: dấu gạch ở cột
# "Trước" là hợp lệ với task không có số liệu nền, bắt nó gây false positive.
PLACEHOLDER_RE = re.compile(
    r"(chưa hoàn thành|chưa có kết quả|chưa cập nhật|điền sau|cập nhật sau|"
    r"bổ sung sau|to ?be ?determined|\btbd\b)", re.I)


# --------------------------------------------------------------------------
# Frontmatter parsing (pyyaml when available, minimal fallback otherwise)
# --------------------------------------------------------------------------

def split_frontmatter(text: str):
    """Return (frontmatter_string_or_None, body)."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    return text[3:end].strip("\n"), text[end + 4:]


def parse_frontmatter(raw: str) -> dict:
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        pass
    # Fallback: flat keys plus one nested level, enough for the task schema.
    data: dict = {}
    current_parent = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ":" not in line:
            continue
        key, _, value = line.strip().partition(":")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if indent == 0:
            if value == "":
                current_parent = key
                data[key] = {}
            else:
                current_parent = None
                data[key] = value
        elif current_parent and isinstance(data.get(current_parent), dict):
            data[current_parent][key] = value
    return data


# --------------------------------------------------------------------------
# Filesystem helpers
# --------------------------------------------------------------------------

def is_skipped(path: str) -> bool:
    return any(part in SKIP_DIR_PARTS for part in path.split(os.sep))


def discover_tasks(tasks_dir: str):
    """Yield (task_type_guess, folder_name, parent_slug_or_None, readme_path)."""
    if not os.path.isdir(tasks_dir):
        return
    for entry in sorted(os.listdir(tasks_dir)):
        task_dir = os.path.join(tasks_dir, entry)
        if entry.startswith("_") or entry.startswith(".") or not os.path.isdir(task_dir):
            continue
        readme = os.path.join(task_dir, "README.md")
        if os.path.isfile(readme):
            yield ("root", entry, None, readme)
        work_items = os.path.join(task_dir, "work-items")
        if os.path.isdir(work_items):
            for child in sorted(os.listdir(work_items)):
                child_dir = os.path.join(work_items, child)
                child_readme = os.path.join(child_dir, "README.md")
                if os.path.isdir(child_dir) and os.path.isfile(child_readme):
                    yield ("work-item", child, entry, child_readme)


def last_touch_date(task_dir: str) -> date | None:
    """Newest mtime under the task folder, ignoring vendor and cache dirs."""
    newest = None
    for dirpath, dirnames, filenames in os.walk(task_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS and d != "work-items"]
        for name in filenames:
            if name == ".DS_Store":
                continue
            try:
                mtime = os.path.getmtime(os.path.join(dirpath, name))
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    return date.fromtimestamp(newest) if newest else None


def parse_iso_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def newest_report_name(task_dir: str) -> str | None:
    reports_dir = os.path.join(task_dir, "reports")
    if not os.path.isdir(reports_dir):
        return None
    stamped = sorted(
        f for f in os.listdir(reports_dir)
        if f.endswith(".md") and re.match(r"^\d{6}-\d{4}-", f)
    )
    return stamped[-1] if stamped else None


def section_body(body: str, heading: str) -> str:
    match = re.search(rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
                      body, re.M | re.S)
    return match.group(1).strip() if match else ""


# --------------------------------------------------------------------------
# Index parsing
# --------------------------------------------------------------------------

def read_text(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return ""


def registry_rows(path: str) -> dict:
    """Map slug -> status from tasks/_registry.md."""
    rows = {}
    for line in read_text(path).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        slug = cells[0].strip("`").strip()
        status = cells[2].strip("`").strip()
        if re.match(r"^\d{6}-", slug):
            rows[slug] = status
    return rows


# --------------------------------------------------------------------------
# Audit core
# --------------------------------------------------------------------------

def audit_task(root, scope, folder, parent_folder, readme, registry, workstreams, today):
    task_dir = os.path.dirname(readme)
    rel_readme = os.path.relpath(readme, root)
    text = read_text(readme)
    raw_fm, body = split_frontmatter(text)
    flags = []

    if raw_fm is None:
        touched = last_touch_date(task_dir)
        return {
            "slug": folder,
            "path": rel_readme,
            "scope": scope,
            "parent": parent_folder,
            "status": "unknown",
            "task_type": "unknown",
            "days_idle": (today - touched).days if touched else None,
            "lifecycle": "legacy-no-frontmatter",
            "flags": [{"code": "MISSING_FRONTMATTER", "severity": "P1",
                       "detail": "README chưa có YAML frontmatter (task lịch sử)"}],
        }

    fm = parse_frontmatter(raw_fm)
    status = str(fm.get("status", "")).strip() or "unknown"
    task_type = str(fm.get("task_type", "")).strip() or "unknown"
    targets = fm.get("report_targets") or {}
    syncs = fm.get("report_sync") or {}

    for field in REQUIRED_FIELDS:
        if not str(fm.get(field, "")).strip():
            flags.append({"code": "MISSING_FIELD", "severity": "P2",
                          "detail": f"thiếu frontmatter `{field}`"})

    # Idle computation: newest of the `updated` field and real file activity.
    touched = last_touch_date(task_dir)
    updated = parse_iso_date(fm.get("updated"))
    marks = [d for d in (touched, updated) if d]
    last_activity = max(marks) if marks else None
    days_idle = (today - last_activity).days if last_activity else None

    # Nợ log File 1 / File 2.
    #
    # P2 chứ không phải P1, và tên là LOG_PENDING chứ không phải DONE_BUT_SYNC_PENDING:
    # đóng task khi chưa log KHÔNG còn là vi phạm rule. Rule cũ bắt `status: done` đợi
    # log, nhưng hai việc đó không cùng nhịp — task xong là sự thật về công việc, log
    # File 1/File 2 là việc hành chính chạy theo tuần. Bắt cái trước đợi cái sau làm
    # `status` trong repo luôn tụt sau thực tế.
    #
    # Cờ vẫn giữ vì log File 1/File 2 là bằng chứng KPI (giờ làm trước/sau) theo
    # `docs/kpi-and-owner-context.md`. Bỏ chặn không phải bỏ đếm — nó vẫn là món nợ,
    # chỉ không còn là lỗi.
    for key in ("file1_cv", "file2_weekly"):
        wanted = str(targets.get(key, "")).strip().lower() in {"true", "yes"}
        state = str(syncs.get(key, "")).strip().lower()
        if wanted and status == "done" and state not in {"synced", "not-needed"}:
            flags.append({"code": "LOG_PENDING", "severity": "P2",
                          "detail": f"`status: done` nhưng `report_sync.{key}: {state or 'thiếu'}` — còn nợ log"})
        if wanted and state == "":
            flags.append({"code": "MISSING_SYNC_STATE", "severity": "P2",
                          "detail": f"`report_targets.{key}: true` nhưng thiếu `report_sync.{key}`"})

    # Results quality on closed tasks.
    if status == "done":
        results = section_body(body, "Results")
        # Bỏ khung bảng markdown và dấu gạch để xem còn nội dung thật không.
        stripped = re.sub(r"[|>\-—\s]", "", results)
        if not stripped:
            flags.append({"code": "DONE_WITHOUT_RESULTS", "severity": "P2",
                          "detail": "`status: done` nhưng `## Results` trống"})
        elif PLACEHOLDER_RE.search(results):
            flags.append({"code": "DONE_WITHOUT_RESULTS", "severity": "P2",
                          "detail": "`status: done` nhưng `## Results` còn câu placeholder"})
        elif not re.search(r"\d", stripped) and len(stripped) < 120:
            # Không số liệu VÀ quá ngắn thì gần như chắc chắn là khung rỗng.
            # Task dạng restructure/docs có kết quả định tính dài là hợp lệ.
            flags.append({"code": "DONE_WITHOUT_RESULTS", "severity": "P2",
                          "detail": "`status: done` nhưng `## Results` chỉ là khung rỗng"})

    # Staleness.
    if days_idle is not None:
        if status == "in-progress" and days_idle >= STALE_IN_PROGRESS_DAYS:
            flags.append({"code": "STALE_IN_PROGRESS", "severity": "P2",
                          "detail": f"in-progress nhưng {days_idle} ngày không có hoạt động"})
        if status == "blocked" and days_idle >= STALE_BLOCKED_DAYS:
            flags.append({"code": "STALE_BLOCKED", "severity": "P2",
                          "detail": f"blocked nhưng {days_idle} ngày không có hoạt động"})

    # Registry parity. Registry chỉ index task lớn, nên task lẻ đã xong không bị
    # coi là lỗi P1 — xem references/audit-rules.md.
    # Task root thiếu `task_type` vẫn phải bị kiểm: nếu gate theo task_type đã
    # khai, một task chỉ cần quên field là lọt khỏi toàn bộ check registry.
    if scope == "root" and task_type in {"initiative", "single", "unknown"}:
        major = (task_type == "initiative"
                 or status in OPEN_STATUSES
                 or str(fm.get("priority", "")).strip().upper() == "P1")
        if folder not in registry:
            if major:
                flags.append({"code": "NOT_IN_REGISTRY", "severity": "P1",
                              "detail": "task lớn nhưng thiếu dòng trong `tasks/_registry.md`"})
            else:
                flags.append({"code": "NOT_IN_REGISTRY_MINOR", "severity": "P3",
                              "detail": "task lẻ đã đóng, chưa index trong registry (chấp nhận được)"})
        elif registry[folder] and status not in {"unknown"} and registry[folder] != status:
            flags.append({"code": "REGISTRY_STATUS_MISMATCH", "severity": "P1",
                          "detail": f"registry ghi `{registry[folder]}` nhưng README ghi `{status}`"})

    if task_type == "work_item":
        declared_parent = str(fm.get("parent_task", "")).strip()
        if not declared_parent:
            flags.append({"code": "WORKITEM_NO_PARENT", "severity": "P1",
                          "detail": "`task_type: work_item` nhưng `parent_task` trống"})
        elif parent_folder and declared_parent != parent_folder:
            flags.append({"code": "WORKITEM_PARENT_MISMATCH", "severity": "P1",
                          "detail": f"`parent_task: {declared_parent}` khác folder cha `{parent_folder}`"})
        if parent_folder:
            index_text = read_text(os.path.join(root, "tasks", parent_folder, "reports", "index.md"))
            if folder not in index_text and folder not in workstreams:
                flags.append({"code": "WORKITEM_NOT_INDEXED", "severity": "P2",
                              "detail": "chưa xuất hiện trong parent `reports/index.md` hoặc `_workstreams.md`"})

    if task_type == "initiative":
        for required in ("roadmap.md", "reports/resume-brief.md", "reports/index.md"):
            if not os.path.isfile(os.path.join(task_dir, required)):
                flags.append({"code": "INITIATIVE_MISSING_FILE", "severity": "P2",
                              "detail": f"initiative thiếu `{required}`"})

    # Current State freshness vs newest timestamped report.
    newest = newest_report_name(task_dir)
    if newest:
        current_state = section_body(body, "Current State")
        if current_state and newest not in current_state:
            flags.append({"code": "CURRENT_STATE_STALE", "severity": "P3",
                          "detail": f"`## Current State` chưa trỏ tới report mới nhất `{newest}`"})

    has_open_next = bool(re.search(r"^\s*-\s*\[ \]", section_body(body, "Next Steps"), re.M))

    # Lifecycle label, most severe first.
    lifecycle = "active"
    if status in OPEN_STATUSES and days_idle is not None:
        if days_idle >= ARCHIVE_CANDIDATE_DAYS:
            lifecycle = "archive-candidate"
        elif not has_open_next and days_idle >= CLOSE_CANDIDATE_IDLE_DAYS:
            lifecycle = "close-candidate"
        elif (status == "in-progress" and days_idle >= STALE_IN_PROGRESS_DAYS) or \
             (status == "blocked" and days_idle >= STALE_BLOCKED_DAYS):
            lifecycle = "stale-watch"
    # Cố ý KHÔNG ghi đè `lifecycle` thành `sync-pending` nữa. Task `done` mà còn nợ log
    # thì lifecycle của nó là `done` — nợ log là một cờ, không phải một pha của task.
    # Ghi đè làm mất chính thông tin cần cho câu hỏi "hôm nay xong mấy việc".

    return {
        "slug": folder,
        "path": rel_readme,
        "scope": scope,
        "parent": parent_folder,
        "status": status,
        "task_type": task_type,
        "workstream": str(fm.get("workstream", "")).strip(),
        "updated": str(fm.get("updated", "")).strip(),
        "days_idle": days_idle,
        "open_next_steps": has_open_next,
        "lifecycle": lifecycle,
        "flags": flags,
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Task State Audit",
        "",
        f"- Ngày chạy: {result['generated']}",
        f"- Tổng task quét: {result['summary']['total']}",
        f"- Task có flag: {result['summary']['with_flags']}",
        "",
        "## Lifecycle",
        "",
        "| Lifecycle | Số task |",
        "| --- | ---: |",
    ]
    for key, count in sorted(result["summary"]["lifecycle"].items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{key}` | {count} |")

    lines += ["", "## Flag Theo Mã", "", "| Flag | Severity | Số task |", "| --- | --- | ---: |"]
    for code, info in sorted(result["summary"]["flags"].items(), key=lambda kv: -kv[1]["count"]):
        lines.append(f"| `{code}` | {info['severity']} | {info['count']} |")

    flagged = [t for t in result["tasks"] if t["flags"]]
    lines += ["", "## Task Cần Xử Lý", "",
              "| Task | Type | Status | Idle | Lifecycle | Flags |",
              "| --- | --- | --- | ---: | --- | --- |"]
    # `sync-pending` không còn là một lifecycle nào script gán ra, nhưng giữ trong map
    # để report cũ đọc lại vẫn xếp đúng chỗ thay vì rơi xuống nhóm 9.
    order = {"legacy-no-frontmatter": 0, "sync-pending": 1, "archive-candidate": 2,
             "close-candidate": 3, "stale-watch": 4, "active": 5}
    for task in sorted(flagged, key=lambda t: (order.get(t["lifecycle"], 9), -(t["days_idle"] or 0))):
        idle = "—" if task["days_idle"] is None else str(task["days_idle"])
        codes = ", ".join(f"`{c}`" for c in dict.fromkeys(f["code"] for f in task["flags"]))
        lines.append(
            f"| [{task['slug']}]({task['path']}) | {task['task_type']} | "
            f"{task['status']} | {idle} | `{task['lifecycle']}` | {codes} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only task state audit.")
    parser.add_argument("--root", default=".", help="workspace root (default: cwd)")
    parser.add_argument("--format", choices=["json", "md"], default="md")
    parser.add_argument("--status", help="only report tasks with this status")
    parser.add_argument("--lifecycle", help="only report tasks with this lifecycle label")
    parser.add_argument("--out", help="write output to this path instead of stdout")
    parser.add_argument("--today", help="override today's date as YYYY-MM-DD (testing)")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    tasks_dir = os.path.join(root, "tasks")
    if not os.path.isdir(tasks_dir):
        print(f"error: {tasks_dir} not found", file=sys.stderr)
        return 2

    today = parse_iso_date(args.today) or date.today()
    registry = registry_rows(os.path.join(tasks_dir, "_registry.md"))
    workstreams = read_text(os.path.join(tasks_dir, "_workstreams.md"))

    tasks = []
    for scope, folder, parent, readme in discover_tasks(tasks_dir):
        if is_skipped(readme):
            continue
        tasks.append(audit_task(root, scope, folder, parent, readme,
                                registry, workstreams, today))

    if args.status:
        tasks = [t for t in tasks if t["status"] == args.status]
    if args.lifecycle:
        tasks = [t for t in tasks if t["lifecycle"] == args.lifecycle]

    lifecycle_counts: dict = {}
    flag_counts: dict = {}
    for task in tasks:
        lifecycle_counts[task["lifecycle"]] = lifecycle_counts.get(task["lifecycle"], 0) + 1
        # Count affected tasks, not raw occurrences: one task can trip the same
        # code twice (file1 and file2 sync, several missing fields).
        for code in dict.fromkeys(f["code"] for f in task["flags"]):
            severity = next(f["severity"] for f in task["flags"] if f["code"] == code)
            entry = flag_counts.setdefault(code, {"severity": severity, "count": 0})
            entry["count"] += 1

    result = {
        "generated": today.isoformat(),
        "root": root,
        "summary": {
            "total": len(tasks),
            "with_flags": sum(1 for t in tasks if t["flags"]),
            "lifecycle": lifecycle_counts,
            "flags": flag_counts,
        },
        "tasks": tasks,
    }

    output = json.dumps(result, ensure_ascii=False, indent=2) if args.format == "json" \
        else render_markdown(result)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
        print(f"wrote {args.out}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
