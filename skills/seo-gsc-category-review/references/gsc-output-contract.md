# GSC Output Contract

## Required Task Files

Use this layout:

```text
tasks/{task}/
├── README.md
├── data/
│   ├── raw/
│   └── processed/
├── reports/
└── scripts/
```

## Raw Evidence

Recommended names:

- `data/raw/gsc-current-period-query.json`
- `data/raw/gsc-current-period-page.json`
- `data/raw/gsc-current-period-query-page.json`
- `data/raw/gsc-previous-period-query.json`
- `data/raw/gsc-previous-period-page.json`
- `data/raw/gsc-previous-period-query-page.json`

## Processed Outputs

Recommended names:

- `data/processed/gsc-summary-deltas.csv`
- `data/processed/gsc-keyword-movers.csv`
- `data/processed/gsc-page-movers.csv`
- `data/processed/gsc-ctr-opportunities.csv`
- `data/processed/gsc-rank-opportunities.csv`
- `data/processed/gsc-cannibalization-watch.csv`
- `data/processed/{prefix}-business-status-split.csv` — **bắt buộc**, tách SP ngừng kinh doanh
- `data/processed/{prefix}-product-pages-by-status.csv` — **bắt buộc**

Raw thêm `data/raw/{run}/business-status.csv` (trạng thái kinh doanh từng URL sản phẩm,
kèm ngày kiểm).

## Report Sections

Khung và thứ tự mục: `report-plain-language.md` mục "Khung report". Template:
`mwg-seo-analytics/templates/gsc-category-review-report.md`. Tiêu đề mục viết tiếng Việt
(Tóm tắt, Nếu bỏ sản phẩm ngừng kinh doanh, Tin tốt gửi ngành hàng, Số liệu chính...,
Phụ lục kỹ thuật, Câu hỏi còn mở).

## Closeout

- Update task README Results and Outputs.
- If Sheet was written, include target range and readback evidence.
- If live fetch failed, mark partial/blocker plainly.
