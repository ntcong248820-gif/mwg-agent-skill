#!/usr/bin/env python3
"""
crawl_and_fill.py — Crawl TGDD/DMX articles & fill Sheet WF đi link.

Reads spreadsheet IDs from environment variables (no ID hardcoded):
  SHEET_GAME_APP_ID          — Game App / Hỏi Đáp (thegioididong.com)
  SHEET_KINH_NGHIEM_HAY_ID   — Kinh Nghiệm Hay / Vào Bếp (dienmayxanh.com)

Usage:
  # TGDD Game App / Hỏi Đáp (default)
  python3 scripts/crawl_and_fill.py --rows 416:429
  python3 scripts/crawl_and_fill.py --rows 430:435 --dry-run

  # DMX Kinh Nghiệm Hay / Vào Bếp
  python3 scripts/crawl_and_fill.py --sheet kinh-nghiem-hay --rows 1220:1229
  python3 scripts/crawl_and_fill.py --spreadsheet-id <ID> --rows 1220:1229

Dependencies: bs4, lxml (pip install beautifulsoup4 lxml)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

TARGET_SHEETS = {
    "game-app": os.environ.get("SHEET_GAME_APP_ID", ""),
    "kinh-nghiem-hay": os.environ.get("SHEET_KINH_NGHIEM_HAY_ID", ""),
}
DEFAULT_TARGET = "game-app"
SHEET_NAME = "WF đi link"
CURL_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
J_VALUE = "Chèn link vào text có sẵn"

GWS_ENV = dict(os.environ)
GWS_ENV["GOOGLE_WORKSPACE_CLI_CONFIG_DIR"] = os.path.expanduser("~/.config/gws")


def fetch_html(url: str) -> str:
    res = subprocess.run(
        ["curl", "-sL", "--max-time", "40", "-A", CURL_UA, url],
        capture_output=True, text=True
    )
    return res.stdout


def pick_best_paragraph(html: str, anchor: str) -> str | None:
    """Return plain text of best <p> containing anchor (case-insensitive, earliest pos)."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[ERROR] bs4 not installed. Run: pip install beautifulsoup4", file=sys.stderr)
        sys.exit(1)

    # Try lxml first for malformed HTML, fallback to html.parser
    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    detail = (
        soup.find("div", class_="contentnews") or
        soup.find("div", class_="divContent") or
        soup.find("div", class_="detail-content") or
        soup.find("div", class_="contentpost") or
        soup.find("div", class_="content-article") or
        soup.find("article") or soup
    )

    candidates = []
    for i, el in enumerate(detail.find_all(["p", "h2", "h3", "h4", "li"])):
        classes = el.get("class") or []
        if "titleOfImages" in classes or "captionnews" in classes:
            continue
        text = " ".join(el.get_text().split())
        if el.name == "p" and re.search(re.escape(anchor), text, re.IGNORECASE):
            candidates.append((i, text))

    if not candidates:
        # Fallback: any tag that's not li/caption
        for i, el in enumerate(detail.find_all(["h2", "h3", "h4"])):
            text = " ".join(el.get_text().split())
            if re.search(re.escape(anchor), text, re.IGNORECASE):
                candidates.append((i, text))

    return min(candidates, key=lambda x: x[0])[1] if candidates else None


def read_sheet_rows(spreadsheet_id: str, start: int, end: int) -> list[list[str]]:
    range_str = f"'{SHEET_NAME}'!A{start}:P{end}"
    cmd = [
        "command", "gws", "sheets", "+read",
        "--spreadsheet", spreadsheet_id,
        "--range", range_str
    ]
    res = subprocess.run(
        " ".join(cmd), shell=True, env=GWS_ENV,
        capture_output=True, text=True
    )
    if res.returncode != 0:
        print(f"[ERROR] gws sheets +read failed: {res.stderr}", file=sys.stderr)
        return []
    try:
        data = json.loads(res.stdout)
        return data.get("values", [])
    except json.JSONDecodeError:
        print(f"[ERROR] Failed to parse gws response: {res.stdout}", file=sys.stderr)
        return []


def write_h_j(spreadsheet_id: str, rows_data: list[tuple[int, str]]):
    """rows_data: list of (row_number, h_text)"""
    if not rows_data:
        return
    first_row = rows_data[0][0]
    last_row = rows_data[-1][0]
    range_str = f"'{SHEET_NAME}'!H{first_row}:J{last_row}"

    values = [[text, "", J_VALUE] for _, text in rows_data]

    params_json = json.dumps({"spreadsheetId": spreadsheet_id, "range": range_str, "valueInputOption": "USER_ENTERED"})
    body_json = json.dumps({"range": range_str, "majorDimension": "ROWS", "values": values})
    cmd = (
        f'GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws" command gws sheets spreadsheets values update '
        f"--params '{params_json}' --json '{body_json}'"
    )
    res = subprocess.run(cmd, shell=True, env=GWS_ENV, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERROR] write_h_j failed: {res.stderr}\n{res.stdout}", file=sys.stderr)
        return
    try:
        data = json.loads(res.stdout)
        print(f"[WRITE] Updated {data.get('updatedRows')} rows, {data.get('updatedCells')} cells.")
    except Exception:
        print(f"[WRITE] Done writing to {range_str}.")


def resolve_spreadsheet_id(args) -> str:
    if args.spreadsheet_id:
        return args.spreadsheet_id
    sheet_id = TARGET_SHEETS.get(args.sheet) or TARGET_SHEETS[DEFAULT_TARGET]
    if not sheet_id:
        env_name = "SHEET_GAME_APP_ID" if args.sheet == "game-app" else "SHEET_KINH_NGHIEM_HAY_ID"
        print(f"[ERROR] Missing spreadsheet ID. Set {env_name} or pass --spreadsheet-id.", file=sys.stderr)
        sys.exit(1)
    return sheet_id


def main():
    parser = argparse.ArgumentParser(description="Fill WF đi link columns H+J from live TGDD/DMX articles.")
    parser.add_argument("--sheet", choices=list(TARGET_SHEETS.keys()), default=DEFAULT_TARGET,
                        help="Target sheet preset (default: game-app)")
    parser.add_argument("--spreadsheet-id", help="Explicit Google Spreadsheet ID (overrides --sheet)")
    parser.add_argument("--rows", required=True, help="Row range, e.g. 416:429")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write to sheet")
    args = parser.parse_args()

    spreadsheet_id = resolve_spreadsheet_id(args)
    start, end = map(int, args.rows.split(":"))
    print(f"[TARGET] Spreadsheet ID: {spreadsheet_id} ({args.sheet})")
    sheet_rows = read_sheet_rows(spreadsheet_id, start, end)

    to_write = []
    for offset, row in enumerate(sheet_rows):
        row_num = start + offset
        url = row[3] if len(row) > 3 else ""
        anchor = row[4] if len(row) > 4 else ""
        h_current = row[7] if len(row) > 7 else ""

        if not url or not anchor:
            print(f"[SKIP] Row {row_num}: No URL or anchor")
            continue
        if h_current.strip():
            print(f"[SKIP] Row {row_num}: Col H already filled")
            continue

        print(f"[CRAWL] Row {row_num}: {url} | anchor={anchor}")
        html = fetch_html(url)
        text = pick_best_paragraph(html, anchor)

        if not text:
            print(f"[WARN] Row {row_num}: No <p> found with anchor '{anchor}'")
            continue

        print(f"[FOUND] Row {row_num}: {text[:120]}...")
        to_write.append((row_num, text))

    if args.dry_run:
        print(f"\n[DRY-RUN] Would write {len(to_write)} rows. No changes made.")
        return

    write_h_j(spreadsheet_id, to_write)
    print(f"\n[DONE] {len(to_write)} rows processed.")


if __name__ == "__main__":
    main()
