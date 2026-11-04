# GSC Period Calculation Guide

## Default Period Logic

Kỳ đo **không** định nghĩa ở đây. Nguồn duy nhất là
`mwg-seo-analytics/docs/measurement-windows.md` (S1). File này chỉ nói skill dùng
tầng nào và định dạng delta ra sao.

Mặc định của `seo-gsc-compare`: chế độ **`quick` = L1**, tức `7d vs 7d liền trước`.

```
E = latest complete date, chọn theo rule độ đầy của S1 mục 2
P1 = [E-6,  E]
P2 = [E-13, E-7]
```

Hai điều tuyệt đối không làm, vì đây là 2 lỗi đã gặp thật:

1. **Không lấy `today - 2 days` làm `E`.** Lag thực tế của property này là 1 ngày,
   nên rule đó bỏ mất một ngày dùng được. Và nó chỉ đúng do may: nới xuống lag 0/1
   là lấy ngay ngày dở.
2. **Không dùng rule "ngày đầu tiên có clicks > 0".** GSC *có* trả về hôm nay với
   clicks dương. Đo 2026-08-20: hôm nay 59.555 clicks = 10,8% một ngày bình thường.
   Lấy nó thì L1 báo `-16,7%` trong khi số thật là `-5,9%` — sai 10,8 điểm phần trăm.

Rule đúng: ứng viên phải có clicks ≥ 85% median 7–14 ngày đủ liền trước. Chi tiết ở
S1 mục 2.

## Custom Periods

User chỉ định kỳ cụ thể thì dùng đúng kỳ đó, nhưng **hai cửa sổ phải cùng độ dài**
(S1 mục 1). So `7d` với `28d` luôn ra số âm giả do độ dài window.

```
"so sánh tháng 6 vs tháng 5"
P1_start = 2026-06-01, P1_end = 2026-06-30
P2_start = 2026-05-01, P2_end = 2026-05-31
```

User yêu cầu `standard` (L1+L2) hoặc `full` (L1–L4) thì lấy công thức ngày từ S1
mục 1 và ghép verdict theo bảng S1 mục 3 — không tự đặt nhãn mới.

## MCP Call Format

```
get_search_by_page_query:
  days: 28        # for P1 (current period)

get_advanced_search_analytics:
  start_date: "YYYY-MM-DD"   # P2_start
  end_date:   "YYYY-MM-DD"   # P2_end
  dimensions: "query,page"
  filters: [
    {dimension: "page",  operator: "equals", expression: "{url}"},
    {dimension: "query", operator: "equals", expression: "{keyword}"}
  ]
```

**Giữ nguyên `dimensions: "query,page"` — không rút gọn thành `"page"`.** Khi filter
theo `page` mà `page` là dimension duy nhất, truy vấn trả rỗng sai dù URL có traffic
thật (đã test: URL 8 clicks / 22 impressions vẫn ra rỗng). Đây là hành vi của chính
GSC API, không phải lỗi MCP — gọi API trực tiếp cũng bị. Tổ hợp `query,page` + filter
page cho kết quả đúng. `date` cũng bị y vậy (trả đủ dòng ngày nhưng
Clicks/Impressions = 0), nên muốn tách theo ngày phải dùng `query,date`.

# Delta Format Guide

## Clicks & Impressions

```
Increase: "+{N} (+{X}%)"   e.g. "+142 (+18%)"
Decrease: "-{N} (-{X}%)"   e.g. "-30 (-5%)"
New URL:  "🆕 Bài mới"      (P2 = 0 data)
No data:  "⚠️ Không có dữ liệu"
```

## Position (Average Rank)

Note: **lower number = better rank**.

```
Improved (lower number): "↑ {old} → {new}"   e.g. "↑ 5.2 → 3.1"
Dropped  (higher number): "↓ {old} → {new}"  e.g. "↓ 1.6 → 2.3"
Same (diff < 0.2):        "→ {pos}"           e.g. "→ 1.6"
```

## Table Output Format

```markdown
| URL | Keyword | P1 Clicks | P1 Impr | P1 Pos | P2 Clicks | P2 Impr | P2 Pos | Δ Clicks | Δ Pos |
|-----|---------|-----------|---------|--------|-----------|---------|--------|----------|-------|
| /laptop-asus | laptop asus | 2,300 | 26,690 | 1.6 | 2,041 | 27,585 | 1.6 | +259 (+12.7%) | → 1.6 |
| /man-hinh-27-inch | màn hình 27 inch | 159 | 2,340 | 1.3 | 142 | 1,688 | 1.7 | +17 (+12%) | ↑ 1.7→1.3 |
| /man-hinh-24-inch | màn hình 24 inch | 3 | 20 | 3.5 | 0 | 0 | — | 🆕 Bài mới | — |
```
