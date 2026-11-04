"""Phần dùng chung cho 3 script của skill seo-mo-ta-task-it.

- gws(): gọi Google Workspace CLI đúng profile công ty, trả JSON, fail to tiếng.
- cfg(): đọc harness.config.json (ID sheet tổng hợp task IT, thư mục Drive) — không viết cứng ID.
- load_spec(): đọc spec JSON, gắn đường dẫn gốc để resolve ảnh local.
- parse_md(): markdown tối giản trong ô/đoạn -> danh sách dòng, mỗi dòng là các run.

Markdown tối giản (đủ cho Doc mô tả, cố ý không hỗ trợ hơn):
  **đậm**            [chữ](url)            dòng bắt đầu "- " = bullet, "  - " = cấp 2, "    - " = cấp 3
  {img:key}          {img:key|300}  (ảnh, width pt)      {red}chữ đỏ{/red}
"""
from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in HERE.parents if (p / "harness" / "harness_config.py").is_file())
sys.path.insert(0, str(ROOT / "harness"))
from harness_config import load_harness_config  # noqa: E402

ENV = dict(os.environ, GOOGLE_WORKSPACE_CLI_CONFIG_DIR=os.path.expanduser("<configDir>"))
DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
PERSON_RE = re.compile(r"^[^\d\-]+ - \d{4,7}$")  # "An - 100002"


def gws(*args, body=None, params=None, ok_fail=False, timeout=300):
    cmd = ["gws", *args]
    if params is not None:
        cmd += ["--params", json.dumps(params, ensure_ascii=False)]
    if body is not None:
        cmd += ["--json", json.dumps(body, ensure_ascii=False)]
    # cwd tạm: gws lưu phản hồi rỗng (vd 204 của permissions.delete) thành ./download.html
    p = subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=timeout, cwd=tempfile.gettempdir())
    out = p.stdout
    i = out.find("{")
    if p.returncode or i < 0:
        if ok_fail:
            return None
        sys.exit(f"FAIL gws {' '.join(args[:3])}: {p.stderr[-800:]} {out[-800:]}")
    data = json.loads(out[i:])
    # gws có lúc exit 0 mà thân là {"error": ...} (vd 500 timeout): coi là lỗi, không để dựng Doc dở mà báo xong
    if isinstance(data, dict) and "error" in data and not ok_fail:
        sys.exit(f"FAIL gws {' '.join(args[:3])}: {json.dumps(data['error'], ensure_ascii=False)[:800]}")
    return None if isinstance(data, dict) and "error" in data else data


def cfg(key: str, required: bool = True):
    value = load_harness_config().get(key)
    if required and not value:
        sys.exit(f"Thiếu khoá `{key}` trong harness.config.json (mẫu ở harness.config.example.json).")
    return value


def load_spec(path: str) -> dict:
    p = pathlib.Path(path).resolve()
    spec = json.loads(p.read_text(encoding="utf-8"))
    spec["_dir"] = str(p.parent)
    return spec


def image_path(spec: dict, key: str) -> pathlib.Path:
    rel = spec.get("images", {}).get(key)
    if not rel:
        raise KeyError(f"ảnh `{key}` chưa khai trong spec.images")
    return (pathlib.Path(spec["_dir"]) / rel).resolve()


TOKEN = re.compile(r"\*\*(.+?)\*\*|\[([^\]]+)\]\((https?://[^)\s]+)\)|\{img:([\w.\-]+)(?:\|(\d+))?\}|\{red\}(.+?)\{/red\}")


def parse_inline(text: str) -> list[dict]:
    """Một dòng -> run: {t, bold, link, red} hoặc {img, width}."""
    runs, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            runs.append({"t": text[pos:m.start()]})
        if m.group(1) is not None:
            runs.append({"t": m.group(1), "bold": True})
        elif m.group(2) is not None:
            runs.append({"t": m.group(2), "link": m.group(3)})
        elif m.group(4) is not None:
            runs.append({"img": m.group(4), "width": int(m.group(5)) if m.group(5) else None})
        else:
            runs.append({"t": m.group(6), "red": True})
        pos = m.end()
    if pos < len(text):
        runs.append({"t": text[pos:]})
    return runs


def parse_md(text: str) -> list[dict]:
    """Nhiều dòng -> [{level: 0|1|2|3, runs: [...]}]; level 0 = đoạn thường, 1/2/3 = bullet."""
    lines = []
    for raw in str(text).split("\n"):
        level, body = 0, raw
        if raw.startswith("    - "):
            level, body = 3, raw[6:]
        elif raw.startswith("  - "):
            level, body = 2, raw[4:]
        elif raw.startswith("- "):
            level, body = 1, raw[2:]
        lines.append({"level": level, "runs": parse_inline(body)})
    return lines


def plain(text: str) -> str:
    """Bỏ markup, giữ chữ — dùng cho lint và preview."""
    out = []
    for line in parse_md(text):
        out.append("".join(r.get("t", f"[ảnh {r.get('img')}]") for r in line["runs"]))
    return "\n".join(out)


def walk_blocks(spec: dict):
    """Duyệt body: trả (kind, block). kind: h1|h2|h3|p|bullets|table|img|code."""
    for b in spec.get("body", []):
        kind = next(k for k in ("h1", "h2", "h3", "p", "bullets", "table", "img", "code") if k in b)
        yield kind, b
