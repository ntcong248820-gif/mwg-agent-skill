---
name: seo-weekly-action-plan
description: "Sinh plan action SEO tuần từ view có sẵn của sheet system: URL_Cần_Xem, KW_Cần_Xem, Planning_Grid_V2, Action_Event, Impact_Timeline, Dashboard_Tổng_Quan. Xuất job list cho crew (skill agent-crew)."
user-invocable: true
when_to_use: "Trigger: plan action tuần, plan SEO tuần, tuần sau làm gì, plan action tháng, lên kế hoạch SEO, sinh job list cho crew, review hiệu suất rồi plan tiếp."
category: seo-ops
keywords: [plan, weekly, action, priority, crew, joblist, rank-gap, kpi]
metadata:
  version: "2.1.0"
  workspace: mwg-ai-worker
---

# seo-weekly-action-plan

Biến kết luận nghiệm thu thành action tuần sau, dưới dạng job list mà `agent-crew`
dispatch được ngay.

Rail này trước đây đứt ở đầu ra: `seo-action-impact-review` nói được action nào hiệu
quả, nhưng không có gì biến kết luận đó thành việc tuần tới. Owner tự làm bước này
bằng tay rồi mới gọi crew.

KPI phải nối về: **số keyword vào Top 1-2** (95%/1728 KW, `Nhóm NH = Laptop`, hạn
31/12/2026 — xem `docs/kpi-and-owner-context.md`). Traffic không có KPI riêng nhưng
vẫn phải nêu trong report. Job nào không viết được `kpi_link` thì không
thuộc plan này.

## Nguyên tắc số 1: đọc view, đừng tính lại

Sheet system đã có sẵn 5 auto-view làm đúng việc skill này cần. Chúng chạy bằng
formula, lấy đúng lô đo mới nhất, tự cập nhật. Tự gom số từ tab thô bằng script là
làm lại một việc đã xong, với kết quả tệ hơn.

Bản 1.0 của skill này tự tính band rank từ `Data Rank` thô và sai theo 3 cách cùng
lúc: đọc cắt range còn 499/13.824 dòng, lấy lô cũ thứ 2 trong 8 lô, và parse volume
`17,000` thành `17.0`. Đọc `KW_Cần_Xem` thì không có lỗi nào trong số đó.

## Required Context

| File | Lấy gì |
| --- | --- |
| `mwg-seo-planning/docs/sheet-write-policy.md` mục `Read Rules` | range phủ hết dòng, tab append-only, đừng tính lại view |
| `mwg-seo-analytics/docs/measurement-windows.md` (S1) | verdict L1–L4 theo GSC, cách chọn end date |
| `mwg-seo-planning/docs/action-ledger.md` (S2) | trạng thái ledger, cảnh báo quy kết credit |
| `references/action-priority-rules.md` | cách xếp P1–P5 |
| `references/crew-joblist-contract.md` | hình dạng job list |
| Bảng skill → worker ở mục `Multi-Agent Crew Policy` của `CLAUDE.md` | gợi ý `worker_hint` |

## Scope

**Phạm vi mặc định là toàn bộ KPI: `Nhóm NH = Laptop`, 1728 KW, 5 sub-ngành hàng**
(`laptop` 839, `máy tính để bàn` 407, `màn hình máy tính` 320, `máy in` 138,
`phần mềm` 24). Chỉ thu hẹp khi user nói rõ.

Lọc `Tên Ngành hàng = laptop` là **sai phạm vi** — phủ 49% và bỏ đúng 2 nhóm hụt nặng
nhất. Xem `docs/kpi-and-owner-context.md`.

Đọc nhiều nguồn, ghi vào task folder. **Không tự ghi `Planning_Grid_V2`** — xuất
paste-table; ghi chỉ khi user yêu cầu rõ, range hẹp, readback hẹp.

Không gọi API tốn phí. Không tự chạy `agent-crew`.

## Nguồn dữ liệu

| Workbook | ID |
| --- | --- |
| `[TGDD] Data Ranking Laptop` | `<dataRankingLaptop>` |
| `[TGDD] Plan Ontop Laptop` | `<planOntopLaptop>` |
| `Data Order TGDD` | `` |

Đọc theo thứ tự này:

| # | Tab | Workbook | Lấy gì |
| ---: | --- | --- | --- |
| 1 | `Dashboard_Tổng_Quan` | Plan | số hiện hành: đã xong, tỷ lệ hoàn thành, % URL đạt KPI, % rank tăng/giảm sau action. **Đọc trước, để số của mình khớp được** |
| 2 | `URL_Cần_Xem` | Ranking | **đầu vào chính** — `Trạng thái KPI` × `Xu hướng Tỷ lệ`, `Tổng Search Volume`, `Tỷ lệ đạt`, `KW chưa đạt Top 1-2` |
| 3 | `KW_Cần_Xem` | Ranking | keyword cụ thể trong URL đó + `Lý do cần xem` |
| 4 | `Planning_Grid_V2` | Plan | cột `AN` `Trạng thái thực thi (Auto)`, cột `AO` `Cảnh báo trùng Infobox` |
| 5 | `Action_Event` | Order | trạng thái ledger theo S2 |
| 6 | `Impact_Timeline` | Ranking | action loại nào đã ra kết quả trên URL đó |
| 7 | GSC qua S1 | — | verdict L1/L2 khi cần kỳ 28 ngày |

`Data Rank` thô chỉ đọc khi cần cột view không mang. Khi đọc: range phủ hết dòng, lọc
lô mới nhất, đọc band từ cột `RANK_CUSTOM`.

### `URL_Cần_Xem` — bảng ưu tiên cấp URL đã dựng sẵn

93 dòng URL, 24 cột (đo 2026-08-20). Hai cột quyết định hạng:

- `Trạng thái KPI`: `Chưa đạt` 69 · `Gần đạt` 14 · `Đạt KPI` 10
- `Xu hướng Tỷ lệ`: `Đang giảm` 18 · `Giữ nguyên` 29 · `Đang tăng` 46

Giao nhau thành ma trận 9 ô — xem `references/action-priority-rules.md`. Ô
`Chưa đạt × Đang giảm` + `Gần đạt × Đang giảm` gồm **17 URL** nhưng gánh **63% tổng
volume**.

Tab này thay cho việc tự gom `KW_Cần_Xem` theo URL. Nó có sẵn `Tổng Search Volume`,
`Tỷ lệ tốt nhất`, `Tỷ lệ trước đó` vs `Tỷ lệ hiện tại`, và phân bố `Top 1`/`Top 2`/
`Top 3`/`Top 4-10`/`>10 hoặc chưa rank`.

### Sheet đang được sửa liên tục — đọc header trước

Ngày 2026-08-20, `Data Order TGDD` có 5 tab BACKUP mốc 19/08 và 20/08;
`[TGDD] Plan Ontop Laptop` có 8 tab BACKUP cùng 2 mốc đó. Schema đổi trong vòng 2 ngày
trước lần đọc này.

Bắt buộc: đọc `A1` của tab rồi tra index cột **theo tên header**, không hardcode chữ
cái. Bỏ mọi tab có `BACKUP` trong tên. Chi tiết ở `sheet-write-policy.md` mục
`Read Rules` mục 6–7.

## Workflow

1. **Chốt scope:** ngành hàng / URL prefix, tuần đích.
2. **Đọc `Dashboard_Tổng_Quan`.** Ghi lại số hiện hành vào report. Nếu số mình tính
   khác, tìm hiểu vì sao trước khi báo cáo.
3. **Đọc `URL_Cần_Xem`** trong scope → xếp URL vào ma trận 9 ô. Lưu raw vào `data/raw/`.
4. **Đọc `KW_Cần_Xem`** để lấy keyword cụ thể cho từng URL đã chọn.
5. **Đọc `Planning_Grid_V2`**: cột `AN` để loại action đang `Đã xong`/`Đang làm`, cột
   `AO` để không tạo order `IB` cho URL đã có Infobox (chuyển sang `AC`).
6. **Đọc `Action_Event`** → trạng thái ledger. `DECLARED_NOT_LIVE` thành dòng P4 riêng.
7. **Đọc `Impact_Timeline`** để biết loại action nào đã ra kết quả trên URL đó.
8. **Lấy verdict L1/L2 theo S1** khi cần kỳ 28 ngày. `Xu hướng Tỷ lệ` của sheet là kỳ
   ~1–2 tuần, **không thay được** L2.
9. **Chấm ưu tiên** theo `references/action-priority-rules.md`.
10. **Xuất 3 file** vào `data/processed/`:
    - `weekly-action-plan-{tuần}.csv` — bảng đầy đủ để dán vào `Planning_Grid_V2`
    - `crew-joblist-{tuần}.yaml` — job list cho `agent-crew`
    - `good-news-brief-{lô}.md` — **bắt buộc**, xem bước 11
11. **Dựng bản tin "tin tốt gửi ngành hàng"** — so 2 lô đo gần nhất, liệt kê từ khoá
    vừa vào Top 1-2, gom theo sub-ngành hàng, xếp theo lượt tìm/tháng. Viết tiếng Việt
    kinh doanh: **không** dùng `RANK_CUSTOM`, `Xu hướng Tỷ lệ`, tên tab, tên cột, band.
    Owner forward thẳng cho nhân sự ngành hàng Laptop. Không đợi user hỏi mới làm.
    Nêu cả nhóm rời Top 1-2 ở mục "cần lưu ý" — không che.
12. **Viết report** `reports/{yymmdd-hhmm}-weekly-plan-{scope}.md`: evidence trước,
    danh sách action sau, câu chưa rõ cuối. Nếu có cải tiến quy trình, ghi **giờ làm
    trước → sau**; không có số giờ thì không gọi là tối ưu.
13. **Preview cho user.** Ghi `Planning_Grid_V2` chỉ khi user yêu cầu rõ.
14. **Gợi ý bước tiếp:** `agent-crew` với job list vừa xuất, hoặc `seo-log-cv` để log giờ
    plan (`CV chi tiết` = `Plan Action SEO tuần`).

## Vị trí trong system loop

```text
Bàn_Cờ_URL -> Planning_Grid_V2 -> Plan_Event -> Hàng_đợi_Order
           -> Data Order TGDD -> Action_Event -> Impact_Timeline
```

`Planning_Grid_V2` trả lời **khi nào** làm action, không phải **đã làm chưa**. Nguồn
"đã làm" là các tab action trong `Data Order TGDD`, chuẩn hoá qua `Action_Event`.
Skill này sinh **đầu vào** cho `Planning_Grid_V2`; nó không phải nguồn trạng thái.

Chi tiết: `mwg-seo-planning/docs/planning-workflow.md`,
`mwg-seo-planning/sheet-system/rank-tracking/README.md`.

## Chia lô theo ngưỡng crew

`agent-crew` có `MAX_JOBS = 6`, `MAX_PARALLEL = 3`. Plan ra 20 action thì:

- cắt thành nhiều run, ưu tiên P1 → P5;
- ghi rõ run sau gồm gì ở khoá `next_run`;
- **không sinh file joblist cho run sau**. Không có file thì crew không có gì để đọc.

## Không làm

- **Không tự tính lại thứ auto-view đã tính.** Kiểm `URL_Cần_Xem`, `KW_Cần_Xem`,
  `Tổng_Hợp_Biến_Động`, `Impact_Timeline`, `Dashboard_Tổng_Quan` trước khi viết script.
- **Không đặt bộ nhãn cạnh tranh với sheet.** Band rank dùng `RANK_CUSTOM` 6 mức;
  trạng thái URL dùng `Trạng thái KPI` × `Xu hướng Tỷ lệ`.
- **Không hardcode chữ cái cột.** Tra theo tên header ở `A1`. Sheet đang được sửa.
- **Không đọc tab `BACKUP`.**
- **Không tạo order `IB` cho URL có cảnh báo ở `Planning_Grid_V2!AO`** — chuyển `AC`.
- Không đặt biên range cứng. `A1:T500` trên tab 13.824 dòng trả về 499 dòng và
  không báo lỗi.
- Không đọc `Data Rank` mà bỏ bước lọc `M = max(M)`. Dòng đầu tab là lô **cũ nhất**.
- Không coi `Ranking Tổng = 0` là hạng tốt. Sheet gọi nó là `No Rank`.
- **Không so ngày bằng `max()` trên chuỗi.** `Ngày_Đo_Rank` là `dd/mm/yyyy`, so chuỗi
  cho `28/07/2026 > 15/08/2026`. Phải parse ngày trước khi lấy lô mới nhất.
- **Không nhân volume vào con số KPI.** KPI đếm keyword, mọi KW bằng nhau. Volume chỉ
  xếp thứ tự trong cùng nhóm khoảng cách và để trình bày với sếp.
- **Không nộp plan mà thiếu mục "tin tốt gửi ngành hàng".**
- Không đề xuất action cho URL có action `EVIDENCE_STALE` — chưa biết action cũ đã
  live chưa, chồng thêm thì sau không tách được credit.
- Không đề xuất lại action đã có trong `Action_Event` với trạng thái `VERIFIED` trong
  kỳ đo hiện tại.
- Không đề xuất action mới cho URL verdict `TĂNG THẬT`.
- Không gán kết quả rank cho một action khi URL có nhiều loại action cùng kỳ
  (63% dòng `Impact_Timeline` thuộc nhóm này).
- Không tự ghi `Planning_Grid_V2`, không tự chạy `agent-crew`.
- Không tạo job thiếu `kpi_link`.

## Liên quan

- `references/action-priority-rules.md`, `references/crew-joblist-contract.md`
- S1 `mwg-seo-analytics/docs/measurement-windows.md`
- S2 `mwg-seo-planning/docs/action-ledger.md`
- `mwg-seo-planning/docs/sheet-write-policy.md` mục `Read Rules`
- `seo-action-impact-review` (đầu vào), `agent-crew` (đầu ra), `seo-gsc-rank-check`
  (người chạy khi cần lô đo rank mới)
