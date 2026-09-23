---
name: seo-gsc-rank-check
description: >-
  Check keyword rankings from Google Search Console for thegioididong.com and
  dienmayxanh.com, select best performing URL by impressions, and update a
  Google Sheet. Trigger on: 'check rank GSC', 'đo rank', 'lấy rank từ khóa',
  'update ranking', 'cập nhật thứ hạng', 'rank GSC 7 ngày', 'check thứ hạng',
  'ghi rank vào sheet', 'đo thứ hạng từ khóa'.
metadata:
  version: 1.1.0
  category: seo
  requires:
    bins:
      - gws
      - python3
    mcpServers:
      - google-search-console
---

# SEO GSC Rank Check

Check keyword rankings from Google Search Console (GSC) for 2 MWG sites
(`thegioididong.com` + `dienmayxanh.com`), select best-performing URL,
and write results back to a Google Sheet.

Works with **any sheet layout** — only needs a keyword column and 2 output
columns (rank + URL). Date filtering is optional.

**Scope:** GSC keyword rank lookup + Sheet writing.
Does NOT handle: third-party rank tools (Ahrefs, SEMRush), GA4 data,
Google Ads keyword planner.

## Measurement window

Mặc định `--days 7`. Nếu cột đích trên sheet của bạn được đặt tên theo một cửa sổ
cụ thể (ví dụ `Rank GSC (7 ngày)`) thì con số đó **là định nghĩa của cột** — đổi
`--days` là đổi nghĩa của dữ liệu đã ghi trước đó. Đổi cửa sổ thì đổi tên cột luôn.

Chọn ngày kết thúc theo **độ đầy dữ liệu**, không theo rule "có clicks > 0". `fetch-gsc-rankings.py` (`detect_gsc_end_date`) hiện dò từ
lag 2 và lấy ngày đầu tiên có clicks > 0. Kết quả đúng, nhưng đúng **nhờ bắt đầu ở
lag 2**: nó bỏ mất 1 ngày dùng được, và sẽ lấy ngay ngày dở nếu ai nới lag xuống 0/1.
Ai chỉnh tham số lag phải chuyển sang rule độ đầy trước.

Muốn xem xu hướng nhiều tầng cho cùng bộ keyword thì dùng `seo-gsc-compare` hoặc
`seo-gsc-category-review`, không mở rộng skill này.

## Prerequisites

- `gws` CLI authenticated (`gws auth login`).
- GSC MCP server with access to both `thegioididong.com` and `dienmayxanh.com`.
- Python 3 with `google-api-python-client` and `google-auth`.
- GSC token at `~/Library/Application Support/mcp-gsc/token.json`.

## When to Use

Activate when the user asks to:
- Check / measure / update keyword rankings from GSC
- Fill rank data into a Google Sheet
- Compare ranking between TGDD and DMX
- Đo thứ hạng, cập nhật rank GSC, ghi rank vào sheet

## Workflow

### Step 1 — Gather Parameters

Collect from user (ask if not provided):

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| Spreadsheet ID | ✓ | — | Extract from Google Sheet URL |
| Sheet Name | ✓ | — | Tab name (e.g. `Data Rank`) |
| Target Date | ○ | Auto-detect | `DD/MM/YYYY` — or use `--all-rows` |
| Keyword Column | ○ | Auto-detect or `G` | Column with keywords |
| Rank Output Column | ○ | Auto-detect or `N` | Column for avg position |
| URL Output Column | ○ | Auto-detect or `O` | Column for best URL |

### Step 2 — Read Sheet Headers

```bash
command gws sheets +read --spreadsheet <ID> --range "<SheetName>!A1:Z3"
```

Verify columns. If standard headers exist, use `--auto-detect`.

### Step 3 — Run Script (Dry Run First)

Script location: `{this_skill_dir}/scripts/fetch-gsc-rankings.py`

**Scenario A — Standard MWG ranking sheet (has date column):**
```bash
python3 <skill-dir>/scripts/fetch-gsc-rankings.py \
  --spreadsheet-id <ID> --sheet-name "<Tab>" \
  --auto-detect --dry-run
```

**Scenario B — Simple sheet (keyword list, no date column):**
```bash
python3 <skill-dir>/scripts/fetch-gsc-rankings.py \
  --spreadsheet-id <ID> --sheet-name "<Tab>" \
  --keyword-col B --rank-col C --url-col D \
  --all-rows --dry-run
```

**Scenario C — Custom columns + specific date:**
```bash
python3 <skill-dir>/scripts/fetch-gsc-rankings.py \
  --spreadsheet-id <ID> --sheet-name "<Tab>" \
  --keyword-col G --date-col M --rank-col N --url-col O \
  --target-date "14/07/2026" --dry-run
```

### Step 4 — Review & Confirm Write

Present dry-run summary: total rows, match rate, TGDD/DMX split, sample.
After user confirms, re-run without `--dry-run`.

### Step 5 — Verify

Read back sample rows to confirm write:
```bash
command gws sheets +read --spreadsheet <ID> --range "<Tab>!N<row>:O<row>"
```

## Script CLI Reference

| Arg | Default | Description |
|-----|---------|-------------|
| `--spreadsheet-id` | *(required)* | Google Sheet ID |
| `--sheet-name` | *(required)* | Sheet tab name |
| `--auto-detect` | off | Auto-detect columns from header names |
| `--keyword-col` | `G` | Keyword column letter |
| `--date-col` | `M` | Date column letter |
| `--rank-col` | `N` | Rank output column |
| `--url-col` | `O` | URL output column |
| `--all-rows` | off | Process all rows (no date filter) |
| `--target-date` | auto-detect | `DD/MM/YYYY` date filter |
| `--header-row` | `1` | Header row number (1-indexed) |
| `--skip-filled` | off | Skip rows that already have rank |
| `--days` | `7` | GSC lookback days |
| `--dry-run` | off | Preview without writing |
| `--cache-dir` | none | Cache GSC responses directory |
| `--force-fetch` | off | Ignore cached data |

## Auto-Detect Header Patterns

The script recognizes these header names (case-insensitive, partial match):

| Role | Matches |
|------|---------|
| keyword | `keyword`, `từ khóa`, `kw`, `search term`, `query` |
| date | `ngày_đo_rank`, `ngày đo`, `date` |
| rank | `rank gsc`, `avg position`, `position gsc`, `thứ hạng gsc` |
| url | `url gsc`, `url_gsc`, `url ranking`, `best url` |

Explicit `--*-col` args always override auto-detect.

## Ranking Selection Logic

For each keyword:
1. Query GSC for TGDD → find URL with max impressions (best URL of TGDD)
2. Query GSC for DMX → find URL with max impressions (best URL of DMX)
3. Compare winners: lower `avg_position` (better rank) wins; tie → higher impressions wins
4. Write `(avg_position, URL)` to rank + URL columns
5. No GSC data → row left blank


## Appending a New Date Batch

When the user asks to "sinh hàng mới cho ngày X" or "thêm đợt đo mới":

### Step A — Check existing batch structure

```bash
# Count rows and identify date batches
command gws sheets +read --spreadsheet <ID> --range "Data Rank!M1:M20000" \
  | python3 -c "..."
```

Each batch has the same number of rows as the keyword list (one row per keyword).
Find the latest batch's row range, then set `FIRST_NEW_ROW = last_row + 1`.

### Step B — Expand sheet if needed

Sheet `rowCount` equals current data rows. Expand before writing:

```bash
command gws sheets spreadsheets batchUpdate \
  --params '{"spreadsheetId": "<ID>"}' \
  --json '{"requests":[{"updateSheetProperties":{"properties":{"sheetId":0,"gridProperties":{"rowCount":<new_count>}},"fields":"gridProperties.rowCount"}}]}'
```

### Step C — Copy keyword rows, write with new date

Copy the non-date columns from the latest batch. For the date column **NEVER write
text** like `"19/09/2026"` — a Google Sheet stores dates as **serial numbers**.
Writing text causes red validation errors.

**Calculate serial number:**
```python
from datetime import date
serial = (date(YYYY, MM, DD) - date(1899, 12, 30)).days
# e.g. 19/09/2026 → 46284
```

**Write with `valueInputOption: RAW`** so the number is stored as-is (not parsed):
```bash
--params '{"...", "valueInputOption": "RAW"}'
```

### Step D — Apply date number format to the date column

After writing serial numbers, apply date cell format so they display as `dd/mm/yyyy`:

```bash
command gws sheets spreadsheets batchUpdate \
  --params '{"spreadsheetId": "<ID>"}' \
  --json '{
    "requests": [{
      "repeatCell": {
        "range": {"sheetId": 0, "startRowIndex": <first-1>, "endRowIndex": <last>,
                  "startColumnIndex": <col-index>, "endColumnIndex": <col-index+1>},
        "cell": {"userEnteredFormat": {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}}},
        "fields": "userEnteredFormat.numberFormat"
      }
    }]
  }'
```

> **Pitfall:** Writing a date as text via `USER_ENTERED` valueInputOption looks fine
> in dry-run but shows as red cells in the sheet because the column expects a
> numeric DATE, not a string. Always use serial + RAW + explicit numberFormat.

### Step E — Run rank check for the new date

After rows are created, run the rank script normally:

```bash
python3 <skill-dir>/scripts/fetch-gsc-rankings.py \
  --spreadsheet-id <ID> --sheet-name "Data Rank" \
  --keyword-col G --date-col M --rank-col N --url-col O \
  --target-date "DD/MM/YYYY" --dry-run
```

Confirm dry-run results, then re-run without `--dry-run`.

---

## Security Policy

- Never expose GSC API tokens in output.
- Always `--dry-run` first before writing.
- Only write to rank + URL output columns, nothing else.
- Confirm with user before executing writes.
