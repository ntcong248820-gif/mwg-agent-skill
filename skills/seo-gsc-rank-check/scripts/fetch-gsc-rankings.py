#!/usr/bin/env python3
"""
Fetch GSC keyword rankings for thegioididong.com and dienmayxanh.com,
select the best-performing URL by impressions, and update a Google Sheet.

Works with ANY sheet layout — just needs a keyword column and output columns.

Usage:
  # Explicit columns
  python3 fetch-gsc-rankings.py \
    --spreadsheet-id <SHEET_ID> --sheet-name "Data Rank" \
    --keyword-col G --rank-col N --url-col O --dry-run

  # Auto-detect columns from headers
  python3 fetch-gsc-rankings.py \
    --spreadsheet-id <SHEET_ID> --sheet-name "Data Rank" \
    --auto-detect --dry-run

  # All rows (no date filter)
  python3 fetch-gsc-rankings.py \
    --spreadsheet-id <SHEET_ID> --sheet-name "Sheet1" \
    --keyword-col B --rank-col C --url-col D --all-rows --dry-run
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Google API imports (optional — graceful fallback if missing)
# ---------------------------------------------------------------------------
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    HAS_GOOGLE_API = True
except ImportError:
    HAS_GOOGLE_API = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
TOKEN_PATH = Path.home() / "Library" / "Application Support" / "mcp-gsc" / "token.json"

TGDD_SITE = "https://www.thegioididong.com/"
DMX_SITE = "https://www.dienmayxanh.com/"

# Header patterns for auto-detection (case-insensitive, partial match)
HEADER_PATTERNS = {
    "keyword": ["keyword", "từ khóa", "tu khoa", "kw", "search term", "query"],
    "date": ["ngày_đo_rank", "ngay_do_rank", "ngày đo", "date", "ngay do rank"],
    "rank": ["rank gsc", "avg position", "position gsc", "thứ hạng gsc",
             "rank_gsc", "ranking gsc"],
    "url": ["url gsc", "url_gsc", "url ranking", "best url"],
}


def col_letter_to_index(letter: str) -> int:
    """Convert column letter (A-Z, AA-AZ, …) to 0-based index."""
    idx = 0
    for ch in letter.upper():
        idx = idx * 26 + (ord(ch) - ord("A") + 1)
    return idx - 1


def index_to_col_letter(idx: int) -> str:
    """Convert 0-based column index to letter (A, B, ..., Z, AA, ...)."""
    result = ""
    idx += 1
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        result = chr(65 + remainder) + result
    return result


def auto_detect_columns(header: list[str]) -> dict[str, str | None]:
    """Scan header row and return detected column letters for each role."""
    detected: dict[str, str | None] = {
        "keyword": None, "date": None, "rank": None, "url": None,
    }
    for col_idx, cell in enumerate(header):
        cell_lower = cell.strip().lower()
        for role, patterns in HEADER_PATTERNS.items():
            if detected[role] is not None:
                continue
            for pat in patterns:
                if pat in cell_lower:
                    detected[role] = index_to_col_letter(col_idx)
                    break
    return detected


def get_credentials():
    if not TOKEN_PATH.exists():
        print(f"Error: GSC token not found at {TOKEN_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(TOKEN_PATH.read_text("utf-8"))
    return Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )


def escape_regex(term: str) -> str:
    """Escape regex metacharacters for GSC includingRegex filter."""
    return re.sub(r"([.\\+*?\[\]^$(){}|])", lambda m: "\\" + m.group(0), term)


def make_regex_chunks(keywords: list[str], max_chars: int = 700) -> list[str]:
    """Split keywords into regex alternation chunks within char limit."""
    chunks: list[list[str]] = []
    cur: list[str] = []
    cur_len = 0
    for kw in keywords:
        esc = escape_regex(kw)
        if cur_len + len(esc) + 1 > max_chars and cur:
            chunks.append(cur)
            cur = [esc]
            cur_len = len(esc)
        else:
            cur.append(esc)
            cur_len += len(esc) + 1
    if cur:
        chunks.append(cur)
    return [f"^({'|'.join(c)})$" for c in chunks]


# ---------------------------------------------------------------------------
# GSC query
# ---------------------------------------------------------------------------
def query_gsc_chunks(service, site_url: str, start: str, end: str,
                     regex_list: list[str]) -> dict:
    """Return {keyword_lower: [{page, impressions, position}, …]}."""
    data: dict[str, list] = {}
    for i, regex in enumerate(regex_list):
        print(f"  GSC {site_url.split('//')[1][:20]} chunk {i+1}/{len(regex_list)}")
        body = {
            "startDate": start,
            "endDate": end,
            "dimensions": ["query", "page"],
            "dimensionFilterGroups": [{
                "filters": [{
                    "dimension": "query",
                    "operator": "includingRegex",
                    "expression": regex,
                }]
            }],
        }
        try:
            resp = service.searchanalytics().query(
                siteUrl=site_url, body=body
            ).execute()
            for r in resp.get("rows", []):
                q = r["keys"][0].strip().lower()
                data.setdefault(q, []).append({
                    "page": r["keys"][1].strip(),
                    "impressions": r.get("impressions", 0),
                    "position": r.get("position", 0.0),
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠ chunk {i+1} error: {e}", file=sys.stderr)
    return data


def best_url(rows: list[dict]) -> dict | None:
    """Pick URL with highest impressions; tie-break by lower position."""
    if not rows:
        return None
    return sorted(rows, key=lambda r: (-r["impressions"], r["position"]))[0]


# ---------------------------------------------------------------------------
# Detect latest GSC final-data date
# ---------------------------------------------------------------------------
def detect_gsc_end_date(service, site_url: str) -> str:
    """Find latest date with final data (usually today-2 or today-3)."""
    today = datetime.date.today()
    for lag in range(2, 6):
        check = (today - datetime.timedelta(days=lag)).strftime("%Y-%m-%d")
        body = {"startDate": check, "endDate": check}
        try:
            resp = service.searchanalytics().query(
                siteUrl=site_url, body=body
            ).execute()
            rows = resp.get("rows", [])
            if rows and rows[0].get("clicks", 0) > 0:
                return check
        except Exception:
            pass
    # Fallback: today - 3
    return (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Sheet read via gws CLI
# ---------------------------------------------------------------------------
def read_sheet(spreadsheet_id: str, range_a1: str) -> dict:
    cmd = f'command gws sheets +read --spreadsheet {spreadsheet_id} --range "{range_a1}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error reading sheet: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    stdout = result.stdout
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        idx = stdout.find("{")
        if idx >= 0:
            return json.loads(stdout[idx:])
        print(f"Cannot parse sheet response:\n{stdout}", file=sys.stderr)
        sys.exit(1)


def write_sheet_batch(spreadsheet_id: str, value_ranges: list[dict],
                      chunk_size: int = 300) -> int:
    """Write values using gws batchUpdate in chunks. Returns total cells."""
    total = 0
    for i in range(0, len(value_ranges), chunk_size):
        chunk = value_ranges[i:i + chunk_size]
        print(f"  Writing chunk {i // chunk_size + 1} "
              f"({len(chunk)} ranges, progress {i}/{len(value_ranges)})")
        payload = {"valueInputOption": "USER_ENTERED", "data": chunk}
        j_payload = shlex.quote(json.dumps(payload, ensure_ascii=False))
        j_params = shlex.quote(json.dumps({"spreadsheetId": spreadsheet_id}))
        cmd = (f"command gws sheets spreadsheets values batchUpdate "
               f"--params {j_params} --json {j_payload}")
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"  ⚠ Write error: {res.stderr}", file=sys.stderr)
        else:
            try:
                total += json.loads(res.stdout).get("totalUpdatedCells", 0)
            except Exception:
                pass
    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Fetch GSC ranks and update Google Sheet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect columns + date filter
  %(prog)s --spreadsheet-id ABC123 --sheet-name "Data Rank" --auto-detect --dry-run

  # All rows, explicit columns, no date filter
  %(prog)s --spreadsheet-id ABC123 --sheet-name "Sheet1" \\
           --keyword-col B --rank-col D --url-col E --all-rows --dry-run

  # Specific date + custom header row
  %(prog)s --spreadsheet-id ABC123 --sheet-name "Ranking" \\
           --target-date 14/07/2026 --header-row 2 --dry-run
        """,
    )
    ap.add_argument("--spreadsheet-id", required=True,
                    help="Google Sheet spreadsheet ID (from URL).")
    ap.add_argument("--sheet-name", required=True,
                    help="Tab/sheet name within the spreadsheet.")

    # Column selection — explicit OR auto-detect
    col_grp = ap.add_argument_group("column selection")
    col_grp.add_argument("--auto-detect", action="store_true",
                         help="Auto-detect columns from header names.")
    col_grp.add_argument("--keyword-col", default=None,
                         help="Column letter for keywords (default: G).")
    col_grp.add_argument("--date-col", default=None,
                         help="Column letter for date filter (default: M). "
                              "Ignored when --all-rows is set.")
    col_grp.add_argument("--rank-col", default=None,
                         help="Column letter for rank output (default: N).")
    col_grp.add_argument("--url-col", default=None,
                         help="Column letter for URL output (default: O).")

    # Row filtering
    row_grp = ap.add_argument_group("row filtering")
    row_grp.add_argument("--all-rows", action="store_true",
                         help="Process ALL rows (skip date filtering). "
                              "Use for sheets without a date column.")
    row_grp.add_argument("--target-date", default=None,
                         help="DD/MM/YYYY. Omit to auto-detect latest date.")
    row_grp.add_argument("--header-row", type=int, default=1,
                         help="Row number of header (1-indexed, default: 1).")
    row_grp.add_argument("--skip-filled", action="store_true",
                         help="Skip rows that already have a rank value.")

    # GSC options
    gsc_grp = ap.add_argument_group("GSC options")
    gsc_grp.add_argument("--days", type=int, default=7,
                         help="GSC lookback window in days (default: 7).")
    gsc_grp.add_argument("--end-date", default=None,
                         help="Specific GSC end date (YYYY-MM-DD). If omitted, auto-detects latest GSC date.")
    gsc_grp.add_argument("--force-fetch", action="store_true",
                         help="Ignore cached GSC responses.")
    gsc_grp.add_argument("--cache-dir", default=None,
                         help="Directory for caching GSC responses.")

    # Output
    ap.add_argument("--dry-run", action="store_true",
                    help="Query GSC but skip sheet write.")
    args = ap.parse_args()

    if not HAS_GOOGLE_API:
        print("Error: google-api-python-client not installed.", file=sys.stderr)
        sys.exit(1)

    # ── 1. Read sheet ────────────────────────────────────────────────────
    print(f"Reading sheet '{args.sheet_name}'...")
    data = read_sheet(args.spreadsheet_id, f"{args.sheet_name}!A:Z")
    rows = data.get("values", [])
    if len(rows) < 2:
        print("Sheet is empty or has no data rows.", file=sys.stderr)
        sys.exit(1)

    header_offset = args.header_row - 1  # 0-based
    header = rows[header_offset]
    n_cols = len(header)

    # ── 2. Resolve columns ───────────────────────────────────────────────
    if args.auto_detect:
        detected = auto_detect_columns(header)
        print(f"Auto-detected columns: {detected}")
        kw_col = args.keyword_col or detected["keyword"] or "G"
        date_col_letter = args.date_col or detected["date"] or "M"
        rank_col_letter = args.rank_col or detected["rank"] or "N"
        url_col_letter = args.url_col or detected["url"] or "O"
    else:
        kw_col = args.keyword_col or "G"
        date_col_letter = args.date_col or "M"
        rank_col_letter = args.rank_col or "N"
        url_col_letter = args.url_col or "O"

    kw_idx = col_letter_to_index(kw_col)
    date_idx = col_letter_to_index(date_col_letter) if not args.all_rows else None
    rank_idx = col_letter_to_index(rank_col_letter)
    rank_col = rank_col_letter.upper()
    url_col = url_col_letter.upper()

    print(f"Columns: keyword={kw_col}, date={date_col_letter if not args.all_rows else '(all rows)'}, "
          f"rank_out={rank_col}, url_out={url_col}")

    # ── 3. Determine target date (if date filtering is active) ───────────
    target_date = None
    if not args.all_rows:
        target_date = args.target_date
        if not target_date:
            dates = set()
            for r in rows[header_offset + 1:]:
                if len(r) > date_idx and r[date_idx].strip():
                    dates.add(r[date_idx].strip())
            if not dates:
                print("No dates found in date column. Use --all-rows to skip date filter.",
                      file=sys.stderr)
                sys.exit(1)
            def parse_date(s):
                try:
                    parts = s.split("/")
                    return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                except Exception:
                    return datetime.date.min
            target_date = max(dates, key=parse_date)
        print(f"Date filter: '{target_date}'")

    # ── 4. Extract target rows ───────────────────────────────────────────
    # row_num is 1-based (matching Sheet row numbers)
    targets: list[tuple[int, str]] = []
    for i, r in enumerate(rows[header_offset + 1:], start=header_offset + 2):
        while len(r) < n_cols:
            r.append("")
        # Date filter
        if not args.all_rows:
            if r[date_idx].strip() != target_date:
                continue
        # Skip filled
        if args.skip_filled and len(r) > rank_idx and r[rank_idx].strip():
            continue
        kw = r[kw_idx].strip() if len(r) > kw_idx else ""
        if kw:
            targets.append((i, kw))

    filter_desc = f"date='{target_date}'" if not args.all_rows else "all rows"
    print(f"Found {len(targets)} rows ({filter_desc})")
    if not targets:
        print("No target rows found. Exiting.")
        sys.exit(0)

    unique_kws = sorted(set(kw.lower() for _, kw in targets))
    print(f"Unique keywords: {len(unique_kws)}")

    # ── 5. Build regex chunks ────────────────────────────────────────────
    chunks = make_regex_chunks(unique_kws)
    print(f"Regex chunks: {len(chunks)}")

    # ── 6. Fetch GSC data ────────────────────────────────────────────────
    creds = get_credentials()
    service = build("webmasters", "v3", credentials=creds)

    if args.end_date:
        end_date = args.end_date
    else:
        end_date = detect_gsc_end_date(service, TGDD_SITE)
    start_dt = (datetime.datetime.strptime(end_date, "%Y-%m-%d")
                - datetime.timedelta(days=args.days - 1))
    start_date = start_dt.strftime("%Y-%m-%d")
    print(f"GSC date range: {start_date} → {end_date} ({args.days} days)")

    cache_path = None
    if args.cache_dir:
        cache_path = Path(args.cache_dir) / "gsc_rank_cache.json"

    if cache_path and cache_path.exists() and not args.force_fetch:
        print(f"Loading cached GSC data from {cache_path}")
        cached = json.loads(cache_path.read_text("utf-8"))
        tgdd = cached.get("tgdd", {})
        dmx = cached.get("dmx", {})
    else:
        print("Fetching TGDD GSC data...")
        tgdd = query_gsc_chunks(service, TGDD_SITE, start_date, end_date, chunks)
        print("Fetching DMX GSC data...")
        dmx = query_gsc_chunks(service, DMX_SITE, start_date, end_date, chunks)
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps({"tgdd": tgdd, "dmx": dmx}, indent=2,
                           ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"Cached GSC data to {cache_path}")

    # ── 7. Match & select best ───────────────────────────────────────────
    updates: list[dict] = []
    stats = {"total": len(targets), "matched": 0, "tgdd": 0, "dmx": 0}

    for row_idx, kw in targets:
        kw_l = kw.lower()
        b_tgdd = best_url(tgdd.get(kw_l, []))
        b_dmx = best_url(dmx.get(kw_l, []))

        winner = None
        site = None
        if b_tgdd and b_dmx:
            if b_tgdd["position"] < b_dmx["position"]:
                winner, site = b_tgdd, "TGDD"
            elif b_dmx["position"] < b_tgdd["position"]:
                winner, site = b_dmx, "DMX"
            elif b_tgdd["impressions"] >= b_dmx["impressions"]:
                winner, site = b_tgdd, "TGDD"
            else:
                winner, site = b_dmx, "DMX"
        elif b_tgdd:
            winner, site = b_tgdd, "TGDD"
        elif b_dmx:
            winner, site = b_dmx, "DMX"


        if winner:
            stats["matched"] += 1
            stats["tgdd" if site == "TGDD" else "dmx"] += 1
            updates.append({
                "range": f"'{args.sheet_name}'!{rank_col}{row_idx}:{url_col}{row_idx}",
                "values": [[str(round(winner["position"], 2)), winner["page"]]],
            })

    # ── 8. Summary ───────────────────────────────────────────────────────
    pct = stats["matched"] / stats["total"] * 100 if stats["total"] else 0
    print(f"\n{'='*50}")
    print(f"SUMMARY")
    print(f"{'='*50}")
    print(f"  Total rows:     {stats['total']}")
    print(f"  Matched (GSC):  {stats['matched']} ({pct:.1f}%)")
    print(f"  → TGDD:         {stats['tgdd']}")
    print(f"  → DMX:          {stats['dmx']}")
    print(f"  No GSC data:    {stats['total'] - stats['matched']}")
    print(f"  GSC range:      {start_date} → {end_date}")

    # ── 9. Write or dry-run ──────────────────────────────────────────────
    if args.dry_run:
        print(f"\n[DRY RUN] Would update {len(updates)} rows. Sample:")
        for u in updates[:5]:
            print(f"  {u['range']} → {u['values']}")
    elif updates:
        print(f"\nWriting {len(updates)} rows to sheet...")
        cells = write_sheet_batch(args.spreadsheet_id, updates)
        print(f"✓ Done. Total cells updated: {cells}")
    else:
        print("\nNo GSC data found — nothing to write.")


if __name__ == "__main__":
    main()
