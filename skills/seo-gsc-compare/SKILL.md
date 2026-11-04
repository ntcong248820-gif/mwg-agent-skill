---
name: seo-gsc-compare
description: "So sánh Google Search Console 2 kỳ cho URL bất kỳ: top keyword, clicks, impressions, position. Trigger: 'check GSC', 'so sánh GSC', 'performance URL', 'xem rank', 'check keyword'."
user-invocable: true
when_to_use: "Dùng khi cần đánh giá hiệu quả SEO của một URL qua 2 kỳ thời gian. Trigger: 'check GSC', 'so sánh GSC', 'performance', 'kiểm tra rank', 'xem clicks URL'."
category: seo-ops
keywords: [gsc, search-console, performance, rank, clicks, impressions, compare]
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
---

# seo-gsc-compare

So sánh hiệu quả SEO của URL trên Google Search Console giữa 2 kỳ thời gian.

## KPI của workspace

KPI duy nhất: **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn **31/12/2026**. KPI **đếm keyword** — mọi KW bằng nhau, không
phân biệt KW chính/phụ, không nhân trọng số volume. Traffic **không có KPI riêng**.

`Nhóm NH = Laptop` gồm 5 sub-ngành hàng (`laptop` 839, `máy tính để bàn` 407,
`màn hình máy tính` 320, `máy in` 138, `phần mềm` 24). Lọc `Tên Ngành hàng = laptop`
chỉ phủ 49% phạm vi. Khi user nói "ngành hàng", hỏi rõ hoặc mặc định toàn bộ 1728 KW.

Đọc `docs/kpi-and-owner-context.md` trước khi đo, xếp ưu tiên, hay viết report.

## Scope

Skill này chỉ đọc dữ liệu GSC. Không ghi file, không append sheet, không thay đổi dữ liệu.
Site mặc định: `https://www.thegioididong.com/`

## Required Context

Đọc `mwg-seo-analytics/docs/measurement-windows.md` (S1) **trước khi fetch**. Kỳ đo,
cách chọn end date, và verdict rule nằm ở đó — skill này không tự khai.

Mặc định của skill này là chế độ **`quick` = chỉ L1 (7d vs 7d liền trước)**. Lý do:
đây là công cụ check nhanh 1 URL, chạy 4 tầng mỗi lần làm nó mất tác dụng. User
muốn thấy xu hướng tháng thì yêu cầu `standard` (L1+L2) hoặc `full` (L1–L4), lúc đó
ghép verdict theo bảng của S1.

## Constants

```
SITE_URL    = "https://www.thegioididong.com/"
TOP_N       = top 1 keyword by clicks (for single-URL comparison)
```

Kỳ đo **không** khai ở đây. Đọc S1.

## Workflow

### Step 1 — Gather inputs

Ask user:

> 1. URL cần check (hoặc nhiều URL, mỗi dòng 1 URL)
> 2. Kỳ so sánh (mặc định: chế độ `quick` — L1, 7 ngày vs 7 ngày liền trước)

Nếu user không chỉ định kỳ → dùng `quick` theo S1. End date phải chọn bằng rule độ
đầy của S1 mục 2, **không** lấy `today`: GSC có trả về hôm nay với clicks > 0 nhưng
đó là ngày dở (đo 2026-08-20: 10,8% một ngày bình thường), lấy nó là báo giảm ảo.

### Step 2 — Fetch top keyword per URL (Period 1)

For each URL, call:

```
MCP: google-search-console / get_search_by_page_query
  site_url: "{SITE_URL}"
  page_url:  "{url}"
  days:      28
```

Extract top keyword = row with highest clicks.

### Step 3 — Fetch Period 2 for same keyword

For each URL + top keyword pair:

```
MCP: google-search-console / get_advanced_search_analytics
  site_url:   "{SITE_URL}"
  dimensions: "query,page"
  start_date: "{P2_start}"
  end_date:   "{P2_end}"
  filters:    [page == url, query == top_keyword]
```

### Step 4 — Build comparison table

For each URL output:

```
| URL | Keyword | P1 Clicks | P1 Impr | P1 Pos | P2 Clicks | P2 Impr | P2 Pos | Δ Clicks | Δ Impr | Δ Pos |
```

Delta format:
- Clicks/Impr: `+N (X%)` or `-N (X%)`
- Position: `↑` (rank improved = lower number) / `↓` (rank dropped)
- New URL (P2 = 0): label as `🆕 Bài mới`

### Step 5 — Output

Present table with brief commentary:
- Best performer, notable changes, new URLs ranking
- Keep it concise — numbers first, interpretation second

For multiple URLs (>5): process in parallel batches of 4.

## Error Handling

- URL not found in GSC → mark as `⚠️ Không có dữ liệu`
- P2 has no data for keyword → treat as 0 (may be new content)
- GSC MCP timeout → retry once, then report partial results

## Security

- Read-only: only calls GSC MCP read tools
- Never writes to any file or sheet
- Never exposes raw API responses — only summarized table output
- Scope: `thegioididong.com` only by default; ask user before querying other sites

## References

- `references/gsc-period-and-delta-guide.md` — how to calculate P1/P2 date ranges, and formatting rules for comparison deltas
