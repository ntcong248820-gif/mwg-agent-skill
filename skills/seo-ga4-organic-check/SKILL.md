---
name: seo-ga4-organic-check
description: "Đối chiếu GA4 Organic Search sessions với GSC clicks cho một nhóm landing page. Chỉ channel Organic Search, read-only, không thay GSC làm nguồn chính."
user-invocable: true
when_to_use: "Trigger: GA4 organic, đối chiếu GA4 với GSC, session organic, traffic organic GA4, clicks vs sessions, kiểm chéo traffic, GA4 landing page."
category: analytics
keywords: [ga4, organic-search, sessions, gsc, clicks, corroboration, landing-page]
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
---

# seo-ga4-organic-check

Một việc: nhận danh sách landing page + kỳ đo → trả sessions Organic Search, tỷ lệ
so GSC clicks, và cờ lệch hướng.

GSC vẫn là nguồn chính. Skill này **không** thay GSC, **không** dựng attribution,
**không** suy tỷ lệ chuyển đổi.

## KPI của workspace

KPI duy nhất: **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn **31/12/2026**. KPI **đếm keyword** — mọi KW bằng nhau, không
phân biệt KW chính/phụ, không nhân trọng số volume. Traffic **không có KPI riêng**.

`Nhóm NH = Laptop` gồm 5 sub-ngành hàng (`laptop` 839, `máy tính để bàn` 407,
`màn hình máy tính` 320, `máy in` 138, `phần mềm` 24). Lọc `Tên Ngành hàng = laptop`
chỉ phủ 49% phạm vi. Khi user nói "ngành hàng", hỏi rõ hoặc mặc định toàn bộ 1728 KW.

Đọc `docs/kpi-and-owner-context.md` trước khi đo, xếp ưu tiên, hay viết report.

## Required Context

Đọc trước khi fetch, không được bỏ:

| File | Lấy gì từ đó |
| --- | --- |
| `mwg-seo-analytics/docs/traffic-corroboration.md` (S3) | property ID, rule join, rule timezone, rule sampling, ngưỡng cảnh báo |
| `mwg-seo-analytics/docs/measurement-windows.md` (S1) | kỳ đo và cách chọn end date |

Không tự khai property ID, không tự khai kỳ đo, không tự đặt ngưỡng. Ba thứ đó
nằm trong contract.

## Scope

Read-only. Không ghi Google Sheets, không ghi GA4, không sửa MCP config.

MCP dùng: `analytics-mcp` → `run_report`. GSC lấy qua `google-search-console`.

## Workflow

1. **Xác định kỳ đo.** Skill gọi nó đưa tầng nào thì dùng tầng đó (S1). Gọi trực
   tiếp mà không nói tầng thì mặc định L1. End date lấy theo rule độ đầy của S1
   mục 2, tính trên GSC — **không** để GA4 tự dò ngày.
2. **Xác định scope.** Chọn theo **prefix của path**, và áp đúng prefix đó ở cả 2
   nguồn (S3 mục 3). Đây là lỗi hay gặp nhất: GSC `contains` không phải
   `begins with`, nên phải lọc lại phía client sau khi normalize.
3. **Fetch GA4:**
   - `property_id` đọc từ S3 — `properties/276784199` cho TGDĐ. **Không tra theo
     tên lúc chạy**: account có 3 property tên `[ko dung]`.
   - dimension `landingPage`, metric `sessions`
   - `dimension_filter`: `sessionDefaultChannelGroup EXACT "Organic Search"` AND
     scope prefix
4. **Kiểm cờ trước khi dùng số** (S3 mục 6):
   - `data_loss_from_other_row` phải là `false`. `true` → thu hẹp query, chạy lại,
     không ghi số đó vào processed.
   - `sampling_metadatas` **sẽ không rỗng** ở quy mô TGDĐ — đó là bình thường, không
     phải lỗi. Tính `sampled_n = sessions × samples_read_count / sampling_space_size`.
     Path nào có `sampled_n < 30` thì không trích số per-URL.
5. **Fetch GSC** cùng `start`/`end`, dimension `page`, cùng scope.
6. **Join** theo rule normalize của S3 mục 3. Ghi 3 số: khớp / chỉ GSC / chỉ GA4.
7. **Đọc kết quả:**
   - tỷ lệ `sessions/clicks` cho từng path và cho tổng nhóm
   - **cờ lệch hướng**: một nguồn tăng, nguồn kia giảm → bắt buộc nêu trong report
   - lệch độ lớn thì chỉ ghi tỷ lệ, chưa cảnh báo (S3 mục 7 — ngưỡng chưa chốt)
8. **Lưu evidence** trong task folder:
   - `data/raw/ga4-organic-{scope}-{tầng}.json` — response GA4 kèm `metadata`
   - `data/raw/gsc-pages-{scope}-{tầng}.json`
   - `data/processed/gsc-ga4-corroboration.csv`
9. **Report** phải có dòng disclaimer timezone nguyên văn từ S3 mục 4, và tỷ lệ
   sampling.

## Đọc số thế nào cho đúng

Tỷ lệ `sessions/clicks` **lớn hơn 1** là chuyện thường, không phải lỗi. Đo thật
2026-08-20 trên 18 path Laptop: 1,334 (khoảng per-URL 0,74 → 1,86). Lý do: GSC chỉ
đếm click từ Google, GA4 `Organic Search` gộp cả Bing, Cốc Cốc, Yahoo.

Thứ đáng theo dõi là **độ ổn định của tỷ lệ theo thời gian** trên cùng nhóm URL,
không phải giá trị tuyệt đối. Tỷ lệ nhảy từ 1,3 xuống 0,6 giữa 2 kỳ là tín hiệu tag
lỗi, dù cả hai số đều "hợp lý" khi xét riêng.

## Không làm

- Không cộng clicks với sessions.
- Không dùng GA4 để sửa số GSC, và ngược lại.
- Không so **ngày lẻ** giữa 2 nguồn — lệch timezone làm phép so đó vô nghĩa.
- Không "sửa" lệch timezone bằng cách dịch ngày GA4 đi 1 hôm.
- Không dùng channel `Organic Social`, `Organic Shopping`, `Organic Video`, hay
  `sessionMedium == organic` thay cho `Organic Search`.
- Không gọi property có tên `[ko dung]` / `[ko dùng]` / `Staging`.
- Không ghi số có `data_loss_from_other_row: true` vào `data/processed/`.

## Ai gọi skill này

`seo-gsc-category-review` và `seo-action-impact-review` gọi khi user yêu cầu đối
chiếu, hoặc khi đã thấy cờ lệch hướng. Gọi trực tiếp cũng được.

Hiện chỉ hỗ trợ TGDĐ. DMX (`properties/245308182`) có ID trong S3 nhưng chưa có
case đo — thêm khi có yêu cầu thật.

## Liên quan

- S1 `mwg-seo-analytics/docs/measurement-windows.md`
- S3 `mwg-seo-analytics/docs/traffic-corroboration.md`
- `seo-gsc-category-review`, `seo-action-impact-review`
