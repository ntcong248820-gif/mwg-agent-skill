#!/usr/bin/env python3
"""Smoke tests for audit-task-state.py. No network, no workspace writes.

Run:
    python3 test-audit-smoke.py
"""

import builtins
import re
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def load_module(block_yaml: bool):
    """Import audit-task-state.py, optionally hiding pyyaml to test fallback."""
    real_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if block_yaml and name == "yaml":
            raise ImportError("yaml blocked for fallback test")
        return real_import(name, *args, **kwargs)

    spec = importlib.util.spec_from_file_location(
        f"audit_{'nofm' if block_yaml else 'yaml'}",
        os.path.join(HERE, "audit-task-state.py"),
    )
    module = importlib.util.module_from_spec(spec)
    builtins.__import__ = guarded
    try:
        spec.loader.exec_module(module)
    finally:
        builtins.__import__ = real_import
    return module, guarded, real_import


FRONTMATTER = """title: "Demo Task"
slug: "260809-demo"
status: in-progress
category: "research"
owner: "Thành <Tên - Mã NV>"
created: "2026-08-09"
updated: "2026-08-09"
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
"""


def check(label, condition):
    print(f"{'PASS' if condition else 'FAIL'}  {label}")
    return condition


def test_parser(module, label):
    ok = True
    data = module.parse_frontmatter(FRONTMATTER)
    ok &= check(f"[{label}] flat key parsed", data.get("status") == "in-progress")
    ok &= check(f"[{label}] nested report_targets parsed",
                str(data.get("report_targets", {}).get("file1_cv")).lower() == "true")
    ok &= check(f"[{label}] nested report_sync parsed",
                data.get("report_sync", {}).get("file2_weekly") == "not-needed")
    return ok


def test_sections(module):
    body = "\n## Results\n\nĐã build xong 3 tab.\n\n## Next Steps\n\n- [ ] Còn việc\n- [x] Xong\n"
    ok = check("section_body reads Results",
               "3 tab" in module.section_body(body, "Results"))
    ok &= check("section_body reads Next Steps",
                "[ ]" in module.section_body(body, "Next Steps"))
    ok &= check("section_body missing heading is empty",
                module.section_body(body, "Nope") == "")
    return ok


def test_registry(module):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "_registry.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(
                "| Task Slug | Title | Status |\n| --- | --- | --- |\n"
                "| `260809-demo` | Demo | `done` |\n"
                "| not-a-slug | X | `done` |\n"
            )
        rows = module.registry_rows(path)
    ok = check("registry picks dated slug", rows.get("260809-demo") == "done")
    ok &= check("registry ignores non-slug row", "not-a-slug" not in rows)
    return ok


def test_end_to_end(module):
    """Full audit over a synthetic workspace, verifying read-only behaviour."""
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = os.path.join(tmp, "tasks", "260809-demo")
        os.makedirs(os.path.join(task_dir, "reports"))
        with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as handle:
            handle.write("---\n" + FRONTMATTER + "---\n\n## Next Steps\n\n- [ ] còn việc\n")
        os.makedirs(os.path.join(tmp, "tasks", "_templates"))
        with open(os.path.join(tmp, "tasks", "_registry.md"), "w", encoding="utf-8") as handle:
            handle.write("| Task Slug |\n")
        before = sorted(os.listdir(task_dir))

        registry = module.registry_rows(os.path.join(tmp, "tasks", "_registry.md"))
        found = list(module.discover_tasks(os.path.join(tmp, "tasks")))
        result = module.audit_task(
            tmp, "root", "260809-demo", None,
            os.path.join(task_dir, "README.md"), registry, "",
            module.date(2026, 8, 9),
        )
        untouched = sorted(os.listdir(task_dir)) == before

    ok = check("discovers exactly one task, skips _templates", len(found) == 1)
    ok &= check("flags missing registry row",
                any(f["code"] == "NOT_IN_REGISTRY" for f in result["flags"]))
    ok &= check("fresh in-progress task stays active", result["lifecycle"] == "active")
    ok &= check("detects open next steps", result["open_next_steps"] is True)
    ok &= check("task folder untouched", untouched)
    return ok


def test_registry_severity(module):
    """Task lớn thiếu registry là P1; task lẻ đã done chỉ là P3."""
    def run(frontmatter_overrides):
        fm = FRONTMATTER
        for key, value in frontmatter_overrides.items():
            fm = re.sub(rf"^{key}: .*$", f"{key}: {value}", fm, flags=re.M)
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = os.path.join(tmp, "tasks", "260809-demo")
            os.makedirs(task_dir)
            with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("---\n" + fm + "---\n")
            return module.audit_task(tmp, "root", "260809-demo", None,
                                     os.path.join(task_dir, "README.md"), {}, "",
                                     module.date(2026, 8, 9))

    open_task = run({"status": "in-progress"})
    done_minor = run({"status": "done", "priority": "P3"})
    done_p1 = run({"status": "done", "priority": "P1"})
    initiative = run({"status": "done", "priority": "P3", "task_type": '"initiative"'})

    codes = lambda r: {f["code"] for f in r["flags"]}
    ok = check("task đang mở thiếu registry -> P1", "NOT_IN_REGISTRY" in codes(open_task))
    ok &= check("task lẻ done P3 -> chỉ MINOR",
                "NOT_IN_REGISTRY_MINOR" in codes(done_minor)
                and "NOT_IN_REGISTRY" not in codes(done_minor))
    ok &= check("task done P1 -> P1", "NOT_IN_REGISTRY" in codes(done_p1))
    ok &= check("initiative done -> P1", "NOT_IN_REGISTRY" in codes(initiative))

    # Thiếu task_type không được phép làm task lọt khỏi check registry.
    no_type = run({"status": "in-progress", "task_type": '""'})
    ok &= check("thiếu task_type vẫn bị check registry",
                "NOT_IN_REGISTRY" in codes(no_type))
    return ok


def test_workitem_inherits_reporting(module):
    """Target tắt thì không có nợ log, và lifecycle không bị ghi đè."""
    fm = FRONTMATTER
    fm = re.sub(r"^status: .*$", "status: done", fm, flags=re.M)
    fm = re.sub(r"^  file1_cv: true$", "  file1_cv: false", fm, flags=re.M)
    fm = re.sub(r"^  file1_cv: pending$", "  file1_cv: not-needed", fm, flags=re.M)
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = os.path.join(tmp, "tasks", "260809-demo")
        os.makedirs(task_dir)
        with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("---\n" + fm + "---\n\n## Results\n\nXong 3 tab.\n")
        result = module.audit_task(tmp, "root", "260809-demo", None,
                                   os.path.join(task_dir, "README.md"),
                                   {"260809-demo": "done"}, "", module.date(2026, 8, 9))
    return check("report_targets false -> không nợ log, lifecycle không bị ghi đè",
                 result["lifecycle"] != "sync-pending"
                 and not any(f["code"] == "LOG_PENDING" for f in result["flags"]))


def test_results_detection(module):
    """`—` ở cột Trước là hợp lệ, không được coi là placeholder."""
    def run(results_body):
        fm = re.sub(r"^status: .*$", "status: done", FRONTMATTER, flags=re.M)
        fm = re.sub(r"^  file1_cv: true$", "  file1_cv: false", fm, flags=re.M)
        fm = re.sub(r"^  file1_cv: pending$", "  file1_cv: not-needed", fm, flags=re.M)
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = os.path.join(tmp, "tasks", "260809-demo")
            os.makedirs(task_dir)
            with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as fh:
                fh.write("---\n" + fm + "---\n\n## Results\n\n" + results_body + "\n")
            r = module.audit_task(tmp, "root", "260809-demo", None,
                                  os.path.join(task_dir, "README.md"),
                                  {"260809-demo": "done"}, "", module.date(2026, 8, 9))
        return any(f["code"] == "DONE_WITHOUT_RESULTS" for f in r["flags"])

    real = ("| Metric | Trước | Sau |\n| --- | --- | --- |\n"
            "| Dòng check | — | 1,015 |\n| Khớp | — | 986 (97.14%) |")
    ok = check("bảng có số liệu, cột Trước là `—` -> KHÔNG flag", run(real) is False)
    ok &= check("Results trống -> flag", run("") is True)
    ok &= check("bảng rỗng toàn `—` -> flag",
                run("| M | Trước | Sau |\n| --- | --- | --- |\n| — | — | — |") is True)
    ok &= check("còn câu 'Điền sau' -> flag",
                run("> Điền sau khi chốt hướng schema.\n\n| M |\n| --- |\n| 1 |") is True)
    ok &= check("văn xuôi có số -> KHÔNG flag",
                run("Đã xử lý 217 keyword, 179 có dữ liệu GSC.") is False)
    return ok


def test_log_pending(module):
    """Còn nợ log thì cờ `LOG_PENDING` P2, và lifecycle KHÔNG bị ghi đè.

    Test này gác cả hai nửa của việc bỏ gate: nợ log vẫn phải được đếm (nó là bằng
    chứng KPI), và task `done` vẫn phải trông như đã done — nếu lifecycle bị ghi đè
    thì câu hỏi "tuần này đóng mấy việc" mất câu trả lời.
    """
    fm = re.sub(r"^status: .*$", "status: done", FRONTMATTER, flags=re.M)
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = os.path.join(tmp, "tasks", "260809-demo")
        os.makedirs(task_dir)
        with open(os.path.join(task_dir, "README.md"), "w", encoding="utf-8") as fh:
            fh.write("---\n" + fm + "---\n\n## Results\n\nXong 3 tab.\n")
        r = module.audit_task(tmp, "root", "260809-demo", None,
                             os.path.join(task_dir, "README.md"),
                             {"260809-demo": "done"}, "", module.date(2026, 8, 9))
    no = [f for f in r["flags"] if f["code"] == "LOG_PENDING"]
    ok = check("sync pending -> cờ LOG_PENDING", len(no) > 0)
    ok &= check("LOG_PENDING là P2, không phải P1",
                all(f["severity"] == "P2" for f in no))
    ok &= check("lifecycle không bị ghi đè thành sync-pending",
                r["lifecycle"] != "sync-pending")
    ok &= check("không còn cờ DONE_BUT_SYNC_PENDING",
                not any(f["code"] == "DONE_BUT_SYNC_PENDING" for f in r["flags"]))
    return ok


def main():
    ok = True
    with_yaml, _, _ = load_module(block_yaml=False)
    ok &= test_results_detection(with_yaml)
    ok &= test_parser(with_yaml, "pyyaml")
    ok &= test_sections(with_yaml)
    ok &= test_registry(with_yaml)
    ok &= test_end_to_end(with_yaml)
    ok &= test_registry_severity(with_yaml)
    ok &= test_workitem_inherits_reporting(with_yaml)
    ok &= test_log_pending(with_yaml)

    without_yaml, _, _ = load_module(block_yaml=True)
    ok &= test_parser(without_yaml, "fallback")

    print("\nRESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
