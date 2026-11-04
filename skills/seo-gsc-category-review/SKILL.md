---
name: seo-gsc-category-review
description: Review Google Search Console traffic by category, URL group, or keyword cluster — 7d/28d comparisons, keyword growth, page movers, CTR/rank opportunities. Always splits out products that stopped selling (ngừng kinh doanh) to show the real trend, and writes the report in plain Vietnamese without L1/L2 codes.
user-invocable: true
when_to_use: "Use when the user asks broad GSC analytics questions: category traffic, industry review, review ngành hàng, traffic ngành giảm/tăng, keyword growth, page losses, sản phẩm ngừng kinh doanh kéo traffic, traffic thực tế, CTR opportunity, rank opportunity, or 7-day comparison."
category: seo-ops
keywords: [gsc, search-console, category, keyword-growth, traffic-review, ctr, rank, opportunity, ngung-kinh-doanh, business-status]
metadata:
  version: "1.3.0"
  workspace: mwg-ai-worker
---

# seo-gsc-category-review

Analyze Google Search Console performance for a category, URL group, keyword
cluster, or broad SEO traffic question. Produce evidence-backed Vietnamese
reports with raw/processed artifacts in the active task folder.

## KPI của workspace

KPI duy nhất: **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn **31/12/2026**. KPI **đếm keyword** — mọi KW bằng nhau, không
phân biệt KW chính/phụ, không nhân trọng số volume. Traffic **không có KPI riêng**.

`Nhóm NH = Laptop` gồm 5 sub-ngành hàng (`laptop` 839, `máy tính để bàn` 407,
`màn hình máy tính` 320, `máy in` 138, `phần mềm` 24). Lọc `Tên Ngành hàng = laptop`
chỉ phủ 49% phạm vi. Khi user nói "ngành hàng", hỏi rõ hoặc mặc định toàn bộ 1728 KW.

Đọc `docs/kpi-and-owner-context.md` trước khi đo, xếp ưu tiên, hay viết report.

## Loại trừ Apple — bắt buộc, áp trước khi fetch

**Mọi danh sách được cầm ra đối chiếu phải loại hết sản phẩm hãng Apple** — cả URL lẫn
keyword, ở mọi tầng kỳ đo, mọi bảng mover/opportunity, và mục tin tốt gửi ngành hàng.
Apple không thuộc phạm vi owner chịu trách nhiệm, nên số Apple lẫn vào là số của người
khác.

Loại ở **2 chiều, cả hai đều bắt buộc**:

| Chiều | Filter |
| --- | --- |
| `page` | `page:excludingRegex:(?i)(-apple(-\|/\|$)\|/(apple\|macbook\|imac\|mac-mini\|mac-studio\|mac-pro)-)` |
| `query` | `query:excludingRegex:(?i)(apple\|macbook\|imac\|mac ?mini\|mac ?studio\|mac ?air\|mac ?neo\|macos\|ipad)` |

Chỉ loại theo `page` là **chưa đủ**: truy vấn `macbook` vẫn rơi vào trang danh mục
`/laptop` chung, nên nó chui vào bảng keyword mover nếu không loại theo `query`.

Regex `page` phủ 2 dạng URL khác nhau, thiếu một dạng là lọt:

- danh mục: `/laptop-apple-macbook`, `/laptop-apple-m2`, `/may-tinh-de-ban-apple`
- trang sản phẩm: `/laptop/macbook-air-13-inch-m4-...`, `/laptop/apple-macbook-air-2020-...`,
  `/may-tinh-de-ban/mac-mini-m4-...`

Không dùng `mac` trơn trong regex — nó khớp cả slug không phải Apple.

**Report phải ghi rõ một dòng "đã loại Apple"** trong mục Scope, kèm cả 2 filter. Số
ex-Apple và số gồm Apple lệch nhau lớn: đo ngày 03/09/2026 trên `Nhóm NH = Laptop`,
Apple chiếm **14,0% clicks** (25.382/181.638 trong 28 ngày) và giữ 4/10 URL tăng mạnh
nhất — không ghi rõ thì lần sau không ai biết report đang đọc tập nào.

Tiền lệ: report `tasks/260728-gsc-tech-gadgets-28d-review/` đã loại Apple từ 28/07/2026
nhưng rule không được ghi vào skill, nên vòng đo 03/09/2026 để Apple lọt lại vào đúng
mục tin tốt gửi ngành hàng. Đó là lý do rule này nằm ở đây thay vì trong đầu người chạy.

## Tách sản phẩm ngừng kinh doanh — bắt buộc

Trang của sản phẩm đã ngừng bán vẫn xếp hạng thêm một thời gian rồi rơi dần. Lượt vào
mất ở đó là vòng đời sản phẩm, không phải sức khoẻ SEO. Gộp chung thì ngành trông tệ
hơn thực tế. Đo vòng 02/10/2026: trang sản phẩm ~34% clicks ngành Laptop; 8/12 URL sản
phẩm mất clicks nhiều nhất đã ngừng kinh doanh.

Mọi report phải trả lời 3 câu cho mỗi kỳ so sánh:

1. Sản phẩm ngừng kinh doanh chiếm bao nhiêu % lượt nhấp?
2. Gánh bao nhiêu % phần tăng/giảm của ngành?
3. Bỏ nhóm đó ra thì ngành thực sự tăng hay giảm?

Hai tool, chạy sau khi fetch xong file `page`:
`classify-product-business-status.py` (kiểm trạng thái từng URL sản phẩm, chạy nền) →
`build-business-status-split.py` (tách số). Lệnh, cách đọc, bẫy:
`references/business-status-split.md`.

Hai điểm không được sai:

- **So cùng kỳ năm ngoái** không dùng dòng "bỏ SP ngừng KD" — sản phẩm năm ngoái gần như
  đã ngừng hết, bỏ ra là đẹp giả. Dùng dòng **trang danh mục, hãng, bộ lọc**.
- Sản phẩm ngừng bán **không** đưa vào "rớt hạng" ở mục cần lưu ý, không đề xuất tối ưu.

## Report đọc được không cần tra cứu — bắt buộc

Người nhận forward (ngành hàng, leader) không có file S1. Thân report **không** dùng mã
`L1`–`L4`, `E`, `Δ`, `pp`, `ex-Apple`, `movers`, tên tool/worker. Viết tên kỳ bằng lời
kèm ngày ("4 tuần gần nhất so với 4 tuần trước đó, 02/09–29/09 so với 05/08–01/09").
Câu đầu tiên là kết luận. Mã và đường dẫn kỹ thuật dồn vào mục `## Phụ lục kỹ thuật`
cuối report. Bảng thay từ + khung report + lệnh grep kiểm trước khi giao:
`references/report-plain-language.md`.

## Tin tốt gửi ngành hàng — bắt buộc

Owner ở tâm thế phục vụ **nhân sự ngành hàng Laptop** — họ quan tâm kinh doanh, không
quan tâm kỹ thuật SEO. Thấy rank hoặc traffic tăng thì phải nêu ngay để owner nhắn cho
họ, không đợi được hỏi.

Mọi report của skill này phải có một mục riêng:

- URL/keyword nào vừa lên, **từ đâu tới đâu**, nhờ action nào.
- Phần "cần lưu ý" chỉ nêu cái tụt thật — sản phẩm đã ngừng bán thì ghi "đã ngừng bán",
  không ghi "rớt hạng".
- Tiếng Việt kinh doanh. **Không** dùng `RANK_CUSTOM`, `Xu hướng Tỷ lệ`, tên band,
  tên tab, tên cột trong mục này. Đủ gọn để forward thẳng.
- Nêu cả phần tụt ở mục "cần lưu ý" — không che.

Có cải tiến quy trình thì ghi **giờ làm trước → sau**. Không có số giờ thì không gọi
là tối ưu. Chi tiết: `docs/kpi-and-owner-context.md` mục 5.

## Scope

This skill handles read-oriented GSC analysis:

- Multi-tier period comparison per contract S1 (default `standard` = L1+L2), or any user-specified period.
- Category/industry review from URL prefix, keyword seed, or supplied list.
- Keyword/page movers, losses, CTR opportunities, rank opportunities.
- Optional Google Sheet read/write only when user explicitly requests it.

This skill does not handle GA4-first analysis, paid traffic attribution, content
writing, technical crawl audit, or MCP/auth setup. Use GA4 only as secondary
corroboration when the user asks or GSC/traffic mismatch matters.

## Required Context

Before fetching data:

1. Read root `README.md`, `CLAUDE.md`, and `AGENTS.md` if not already read this turn.
2. Identify or create `tasks/{yymmdd}-{short-task-slug}/`.
3. Read `mwg-seo-analytics/README.md`.
4. Load `mwg-seo-analytics/docs/analytics-workflow.md` for the full workflow.
4b. **Load `mwg-seo-analytics/docs/measurement-windows.md` (S1) before any fetch.**
    Periods, end-date selection, and the verdict labels live there — this skill does
    not declare its own. Default mode for a category review is `standard` = L1 (7d vs
    7d) **plus** L2 (28d vs 28d), because a category that rose this week while the
    month is still falling must not be reported as growth.
4c. Load `mwg-seo-analytics/docs/traffic-corroboration.md` (S3) and call
    `seo-ga4-organic-check` only when the user asks for GA4 corroboration, or when
    L1/L2 disagree in direction and a second source would settle whether the move is
    real.
5. Load `mwg-seo-analytics/docs/query-recipes.md` only when mapping vague user asks to query filters.

## Workflow

1. Clarify or infer scope:
   - site URL: TGDD/DMX/other property
   - category URL prefix, keyword seed, or provided URL/keyword list
   - current period and previous period
   - country, device, search type if specified
2. Determine latest complete GSC date. If not verified, state the date assumption.
3. Fetch current and previous periods with identical filters, using
   `mwg-seo-analytics/tools/gsc/fetch-search-analytics.py` (direct Google API,
   not the MCP). See the GSC source section in
   `references/gsc-category-review-workflow.md` — including the trap where `page`
   as the only dimension plus a page filter returns 0 rows.
4. Save raw GSC evidence in task `data/raw/`.
5. Generate processed tables in task `data/processed/`:
   - keyword movers
   - page movers
   - CTR opportunities
   - rank opportunities
   - cannibalization watch, only when evidence supports it
   - **business-status split** — khởi động `classify-product-business-status.py` nền
     ngay khi có file `page`, rồi `build-business-status-split.py`
6. Write report in task `reports/` using
   `mwg-seo-analytics/templates/gsc-category-review-report.md` and
   `references/report-plain-language.md`. Chạy lệnh grep kiểm mã trước khi giao.
7. If writing Google Sheet, write only requested ranges and verify with narrow readback.
8. Update task `README.md` Results/Outputs. Update registry only if status changes.

## Output Rules

- Kết luận trước, bằng lời thường; số liệu ngay sau (lượt nhấp, lượt hiển thị, tỷ lệ
  nhấp, thứ hạng trung bình, kỳ so sánh kèm ngày).
- Recommendations second: specific page/query actions.
- **Position là chỉ số ngược** — mỗi lần nhắc phải kèm `tốt hơn`/`xấu đi`, cấm viết
  "position tăng/giảm" trần. Bảng do/don't ở S1 mục 3.1.
- Keep Vietnamese concise. Sacrifice grammar for concision.
- End reports with `## Unresolved Questions`.
- Never imply live success if fetch, write, or readback was not done.

## Security

- Never read `.env`, OAuth tokens, client secrets, or credential files unless the task explicitly requires auth debugging and user approval is present.
- Do not expose raw API payloads in chat if they contain sensitive URLs or private workspace data; summarize and save to task files.
- Keep MCP config out of task folders.
- Treat Sheet writes as high-impact: confirm target range, write narrowly, read back narrowly.

## Existing Related Skills

- Use `seo-gsc-compare` for quick URL/keyword two-period checks.
- Use `seo-task-create` when only task scaffolding is requested.
- Use `gws-sheets-read` or `gws-sheets` only for explicit Google Sheet read/write needs.

## References

- `references/gsc-category-review-workflow.md` - compact execution checklist.
- `references/gsc-output-contract.md` - artifact and report contract.
- `references/business-status-split.md` - tách SP ngừng kinh doanh: lệnh, cách đọc, bẫy.
- `references/report-plain-language.md` - bảng thay từ, khung report, grep kiểm mã.
