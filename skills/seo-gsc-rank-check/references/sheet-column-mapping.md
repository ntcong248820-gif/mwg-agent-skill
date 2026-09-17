# Sheet Column Mapping Reference

## Sheet Structure

Works with any sheet layout. The skill only needs a keyword column plus two
output columns (rank + URL); every column letter is a CLI argument.

### Example Column Map

The script has **no built-in column defaults** — pass `--auto-detect`, or name the
columns with `--keyword-col` / `--rank-col` / `--url-col`. The layout below is one
worked example; substitute your own headers.

| Column | Letter | Header | Type | Direction |
|--------|--------|--------|------|-----------|
| Nhóm NH | A | Product category group | text | read |
| Loại KW | B | Keyword type classification | text | read |
| Tên Ngành hàng | C | Category name | text | read |
| Tên hãng | D | Brand name | text | read |
| Tên Filter | E | Filter name | text | read |
| Tên Sản phẩm | F | Product name | text | read |
| **Keyword** | **G** | Search term to rank for | text | **read** |
| Volume Search | H | Monthly search volume | number | read |
| URL TGDD | I | Planned TGDD URL | url | read |
| URL DMX | J | Planned DMX URL | url | read |
| Trạng Thái | K | SEO status | text | read |
| KW Chính | L | Main keyword flag | boolean | read |
| **Ngày_Đo_Rank** | **M** | Date of measurement (DD/MM/YYYY) | date | **read** |
| **Rank GSC (7 ngày)** | **N** | GSC avg position (7d) | number | **write** |
| **URL GSC** | **O** | Best performing URL from GSC | url | **write** |
| Rank RC | P | RankChecker position | number | read |
| URL RC | Q | RankChecker URL | url | read |
| Ranking Tổng | R | Final composite rank | number | read |
| URL Tổng | S | Final composite URL | url | read |
| RANK_CUSTOM | T | Custom rank bucket | text | read |

### Key Columns (Script Parameters)

- `--keyword-col` (default `G`): Column containing the search keyword.
- `--date-col` (default `M`): Column containing `Ngày_Đo_Rank` value.
- `--rank-col` (default `N`): Column where GSC avg position is written.
- `--url-col` (default `O`): Column where the best-performing URL is written.

### Target Spreadsheet

Pass the sheet on the command line — nothing is hardcoded:

```bash
--spreadsheet-id <your-spreadsheet-id> --sheet-name '<your tab name>'
```

### Ranking Selection Logic

Selection runs in **two stages with different criteria**. Mixing them up picks the
wrong URL, so keep the stages separate.

```
FOR each keyword:
  # Stage 1 — best URL WITHIN each site: impressions first
  1. Query GSC for TGDD site → best_tgdd = max impressions
                                (tie → lower avg position wins)
  2. Query GSC for DMX site  → best_dmx  = max impressions
                                (tie → lower avg position wins)

  # Stage 2 — winner ACROSS the two sites: position first
  3. Compare best_tgdd vs best_dmx:
     - Lower avg position → selected
     - Equal position     → higher impressions → selected
  4. Write selected (position, URL) to rank + URL columns
```

| Stage | Compares | Primary criterion | Tie-break |
| --- | --- | --- | --- |
| 1 | URLs inside one site | Higher impressions | Lower avg position |
| 2 | TGDD winner vs DMX winner | Lower avg position | Higher impressions |

Stage 1 uses impressions because within one site the highest-impression URL is the
one Google actually surfaces for that keyword. Stage 2 uses position because the
question there is which site ranks better, and impressions are not comparable
across two different properties.

Implemented in `scripts/fetch-gsc-rankings.py`: `best_url()` for stage 1, the
`b_tgdd["position"] < b_dmx["position"]` comparison in `main()` for stage 2.
