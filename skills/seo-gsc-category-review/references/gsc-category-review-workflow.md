# GSC Category Review Workflow

## Trigger Examples

- "Review traffic nganh hang Laptop tren GSC 7 ngay gan nhat voi 7 ngay truoc."
- "Chi ra keyword/nhom keyword dang tang truong tot."
- "Tim co hoi toi uu CTR/rank tu GSC."
- "Traffic nganh hang nay giam o dau?"

## Inputs

Collect or infer:

| Input | Examples |
| --- | --- |
| Site | `https://www.thegioididong.com/`, `https://www.dienmayxanh.com/` |
| Scope | URL prefix `/laptop`, query regex, provided list — **luôn kèm 2 filter loại Apple**, xem mục dưới |
| Period | per contract S1 — default `standard` = L1 (7d vs 7d) + L2 (28d vs 28d) |
| Dimensions | `query`, `page`, `query,page` — nhưng khi filter theo `page` thì **bắt buộc** có `query` trong dimensions, xem mục cuối file |
| Optional | device, country, search type |

## Bộ filter chuẩn cho `Nhóm NH = Laptop`

Ba filter, dùng nguyên cả ba ở **mọi** cửa sổ trong cùng một report. Tool AND chúng lại
(`groupType: "and"`).

```bash
--filter 'page:includingRegex:(?i)^https://www\.thegioididong\.com/(laptop|may-tinh-de-ban|man-hinh-may-tinh|may-in|phan-mem)(-|/|\?|$)' \
--filter 'page:excludingRegex:(?i)(-apple(-|/|$)|/(apple|macbook|imac|mac-mini|mac-studio|mac-pro)-)' \
--filter 'query:excludingRegex:(?i)(apple|macbook|imac|mac ?mini|mac ?studio|mac ?air|mac ?neo|macos|ipad)'
```

Filter 1 neo đầu path nên không kéo `/hoi-dap/laptop-...` và `/may-doi-tra/laptop` vào.
Dùng `page:contains:/laptop` thì bị — đã gặp thật, xem S3 mục 3.

Filter 2 và 3 là rule loại Apple ở `SKILL.md`. **Bỏ một trong hai là lọt Apple**: bỏ
filter 3 thì truy vấn `macbook` vẫn vào bảng keyword mover qua trang `/laptop` chung.

## Execution

1. Create/identify task folder.
2. Find latest complete GSC date **by completeness, not by existence** — S1 mục 2.
   A candidate day needs clicks >= 85% of the median of the 7-14 complete days before
   it. GSC does return today with clicks > 0; on 2026-08-20 that day held 10.8% of a
   normal day, and using it turned a real -5.9% into a reported -16.7%.
3. Query current and previous period with the same filters. Same filters across every
   tier — changing country/device/URL filter between tiers makes the delta meaningless.
4. Store raw responses/exports in task `data/raw/`.
5. Process deltas:
   - clicks delta and percent
   - impressions delta and percent
   - CTR point delta
   - average position delta; lower is better
6. Segment:
   - winners: click growth
   - losses: click decline
   - CTR opportunity: high impressions, low CTR, stable/good position
   - rank opportunity: position 4-15, meaningful impressions
   - cannibalization watch: same query across multiple pages
7. Store processed CSV/JSON in task `data/processed/`.
8. **Tách sản phẩm ngừng kinh doanh** — `business-status-split.md` (2 tool, bước kiểm
   trạng thái dùng lại kho chung, chỉ crawl URL mới/quá hạn; lần đầu ~20 phút thì chạy nền).
9. Write report in task `reports/` theo `report-plain-language.md`.

## Decision Rules

- Impressions up without clicks up is demand/visibility growth, not traffic growth.
- Position value lower means rank improved.
- CTR opportunity needs impressions + weak CTR; do not use CTR alone.
- Cannibalization is a watch item unless SERP/business context confirms conflict.
- If latest GSC date is unknown, say so and avoid final verdict.
- Trang sản phẩm mất clicks thì kiểm trạng thái kinh doanh trước khi gọi là "rớt hạng".
  Máy ngừng bán mất lượt vào là vòng đời sản phẩm, không phải lỗi SEO.
- Kết luận chính dựa trên dòng **bỏ SP ngừng kinh doanh** (so tuần, so 4 tuần) và dòng
  **trang danh mục, hãng, bộ lọc** (so cùng kỳ năm ngoái).

## Nguồn Số Liệu GSC: Dùng Tool API Trực Tiếp, Không Dùng MCP

Mọi phép đo trong skill này lấy qua tool CLI, không gọi MCP `google-search-console`:

```bash
$HOME/.claude/skills/.venv/bin/python3 \
  mwg-seo-analytics/tools/gsc/fetch-search-analytics.py \
  --site https://www.thegioididong.com/ \
  --start YYYY-MM-DD --end YYYY-MM-DD \
  --dimensions query \
  --filter page:equals:{{url}} \
  --out tasks/{{task}}/data/raw/{{ten-file}}.json
```

Lý do: MCP tràn token limit với payload lớn, không vượt được 25.000 dòng, và không
để lại file bằng chứng. Tool ghi thẳng ra `data/raw/`, phân trang tự động, và tính
position bình quân **có trọng số impressions**. Đọc
`mwg-seo-analytics/tools/gsc/README.md` trước khi dùng.

### BẪY: `page` là dimension duy nhất + filter `page` trả 0 dòng

Đây là hành vi của **chính GSC API**, không phải lỗi MCP — nên **tool trực tiếp cũng
bị**. Đã test trên URL có thật 8 clicks / 22 impressions, cùng filter, cùng ngày:

| `--dimensions` | Kết quả |
| --- | --- |
| `page` | **0 dòng — SAI** |
| `date` | **có dòng nhưng Clicks/Impressions = 0 — SAI** |
| `query` | đúng |
| `query,page` | đúng |
| `query,date` | đúng |

`--data-state final` hay `all` đều vậy.

**Quy tắc: hễ filter theo `page` thì `--dimensions` bắt buộc chứa `query`.** Không
chỉ `page` — `date` cũng bị, nên `query,date` mới ra số đúng theo ngày. Cần số
tổng của URL thì lấy `--dimensions query` rồi đọc `summary`. Còn `--dimensions page`
mà **không** filter page (ví dụ `page:contains:/laptop`) thì bình thường — đó là cách
đúng để lấy page movers.

Không kết luận "URL/action không có traffic" từ một lần trả 0 dòng. Đổi dimension thử
lại trước — kết luận âm dựa trên kết quả rỗng là loại sai khó phát hiện nhất, và nó
phủ nhận công việc thực sự đã có hiệu quả.
