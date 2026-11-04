---
name: seo-action-impact-review
description: Nghiệm thu hiệu quả action SEO đã làm bằng GSC. Đối chiếu action từ Data Order TGDD với clicks/CTR/rank 3 kỳ, phân loại tác động, đề xuất action tiếp.
user-invocable: true
when_to_use: "Use when the user asks whether completed SEO actions worked: nghiệm thu action, đánh giá hiệu quả action, action nào hiệu quả, review hiệu quả Infobox/Title/Internal Link, hoặc báo cáo hiệu quả cho sếp."
category: seo-ops
keywords: [action-impact, nghiem-thu, gsc, data-order, infobox, title-desc, internal-link, effectiveness, before-after]
metadata:
  version: "1.2.0"
  workspace: mwg-ai-worker
---

# seo-action-impact-review

Đo xem các action SEO đã hoàn thành có thật sự làm tăng rank/traffic hay không.
Input là danh sách action đã done (từ `Data Order TGDD` hoặc `Action_Event`),
output là bảng phân loại tác động theo URL + report Vietnamese có evidence.

## KPI của workspace

KPI duy nhất: **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn **31/12/2026**. KPI **đếm keyword** — mọi KW bằng nhau, không
phân biệt KW chính/phụ, không nhân trọng số volume. Traffic **không có KPI riêng**.

`Nhóm NH = Laptop` gồm 5 sub-ngành hàng (`laptop` 839, `máy tính để bàn` 407,
`màn hình máy tính` 320, `máy in` 138, `phần mềm` 24). Lọc `Tên Ngành hàng = laptop`
chỉ phủ 49% phạm vi. Khi user nói "ngành hàng", hỏi rõ hoặc mặc định toàn bộ 1728 KW.

Đọc `docs/kpi-and-owner-context.md` trước khi đo, xếp ưu tiên, hay viết report.

## Tin tốt gửi ngành hàng — bắt buộc

Owner ở tâm thế phục vụ **nhân sự ngành hàng Laptop** — họ quan tâm kinh doanh, không
quan tâm kỹ thuật SEO. Thấy rank hoặc traffic tăng thì phải nêu ngay để owner nhắn cho
họ, không đợi được hỏi.

Mọi report của skill này phải có một mục riêng:

- URL/keyword nào vừa lên, **từ đâu tới đâu**, nhờ action nào.
- Tiếng Việt kinh doanh. **Không** dùng `RANK_CUSTOM`, `Xu hướng Tỷ lệ`, tên band,
  tên tab, tên cột trong mục này. Đủ gọn để forward thẳng.
- Nêu cả phần tụt ở mục "cần lưu ý" — không che.

Có cải tiến quy trình thì ghi **giờ làm trước → sau**. Không có số giờ thì không gọi
là tối ưu. Chi tiết: `docs/kpi-and-owner-context.md` mục 5.

## Scope

Skill này xử lý **nghiệm thu sau khi action đã done**:

- Đối chiếu action đã done với biến động GSC theo URL đích.
- So 3 kỳ: current (P1), previous (P2), baseline trước action (P0).
- Phân loại từng action vào 6 bucket tác động.
- Chỉ ra URL/keyword thắng, URL suy giảm, và action tiếp theo cần làm.
- Tổng hợp verdict cấp ngành hàng để báo cáo.

Skill này **không** xử lý: lên plan action mới (dùng playbook
`url-action-planning`), review traffic ngành hàng thuần không gắn action
(dùng `seo-gsc-category-review`), đo rank keyword ghi vào Sheet
(dùng `seo-gsc-rank-check`), hoặc ghi Plan_Event/order mới.

## Required Context

Trước khi fetch data:

1. Đọc root `README.md` và `CLAUDE.md` nếu chưa đọc trong turn này.
2. Xác định hoặc tạo `tasks/{yymmdd}-{short-task-slug}/` (workstream `analytics`).
3. **Load `mwg-seo-analytics/docs/measurement-windows.md` (S1) trước mọi fetch.**
   Kỳ đo và cách chọn end date nằm ở đó, skill này không tự khai. Kỳ riêng của skill
   này (P0/P2/P1) ghi ở S1 mục 7.
4. **Load `mwg-seo-planning/docs/action-ledger.md` (S2) trước khi lọc action.**
   Cột bằng chứng live của từng tab và 4 trạng thái ledger nằm ở đó. Mục 2.2 nói
   cách đọc `Action_Event` thay cho 5 tab thô, và 2 bẫy của `Impact_Timeline`.
4b. **Load `mwg-seo-planning/docs/sheet-write-policy.md` mục `Read Rules`** trước khi
   đọc bất kỳ sheet nào: range phủ hết dòng, tab append-only lọc lô mới nhất.
5. Load `references/action-source-map.md` để biết đọc action ở đâu, tab nào, ID prefix nào.
6. Load `references/impact-classification-rules.md` trước khi chấm bucket. Không tự bịa threshold.
7. Load `references/impact-report-contract.md` khi ghi artifact và report.
8. Chỉ đọc `mwg-seo-planning/docs/measurement-logic.md` khi user muốn đổi rule đo.
9. Load `mwg-seo-analytics/docs/traffic-corroboration.md` (S3) và gọi
   `seo-ga4-organic-check` khi user yêu cầu đối chiếu GA4, hoặc khi clicks và
   sessions lệch hướng.

## Workflow

1. **Chốt scope:** site property, ngành hàng / URL prefix / danh sách URL, và
   khoảng action cần nghiệm thu (ví dụ "cụm action tháng 7").
2. **Đọc action đã done rồi dựng ledger:** đọc **`Action_Event`** (workbook
   `Data Order TGDD`, 15 cột) — không mở 5 tab thô trừ khi cần cột view không mang.
   Range phủ hết dòng theo `sheet-write-policy.md` mục `Read Rules`. Chỉ nhận status
   done (`OK`, `Hoàn thành`, `Đã làm`); loại `Chưa làm`.

   Đọc thêm **`Impact_Timeline`** (sheet `[TGDD] Data Ranking Laptop`) để lấy phần
   nối action × biến động rank mà sheet system đã dựng sẵn. Hai lưu ý bắt buộc:
   view này chỉ chứa dòng `OK` nên **không dùng nó làm mẫu số**; và 63% dòng của nó
   có ≥2 loại action trên cùng URL nên phải ghi `KHÔNG TÁCH ĐƯỢC CREDIT`.

   Rồi **join với cột bằng chứng live** theo `mwg-seo-planning/docs/action-ledger.md`
   (S2) và gán 1 trong 4 trạng thái: `VERIFIED`, `DECLARED_NOT_LIVE`,
   `EVIDENCE_STALE`, `NO_CHECKER`. Chỉ `VERIFIED` được đi tiếp sang bước chấm bucket.

   So **chính xác** với giá trị pass, không dùng "ô không rỗng" — checker ghi lý do
   hoặc URL đang live khi lệch, nên ô đầy nội dung có thể là báo lỗi.

   Lưu `data/raw/action-ledger-{scope}.json` kèm ô bằng chứng nguyên văn.
3. **Suy ra 3 kỳ từ ngày xong action**, định nghĩa ở S1 mục 7, không tự chọn ngày:
   - P1 = 7 ngày complete gần nhất trên GSC.
   - P2 = 7 ngày liền trước P1.
   - P0 = 7 ngày liền trước ngày xong **sớm nhất** của cụm action.
   - `E` (ngày cuối của P1) chọn bằng **rule độ đầy** của S1 mục 2, không phải rule
     "có clicks > 0". GSC trả về cả hôm nay với clicks dương; đo 2026-08-20 ngày đó
     chỉ bằng 10,8% một ngày bình thường, lấy nó là biến `-5,9%` thành `-16,7%`.
   - Thêm **L2 (28d vs 28d)** cạnh 3 kỳ trên. Nó tồn tại để bắt trường hợp URL tăng
     vì mùa chứ không vì action: P1 dương mà L2 âm thì verdict là
     `HỒI NGẮN HẠN, THÁNG VẪN GIẢM` (S1 mục 3), không phải action thành công.
   - Ghi rõ mọi khoảng ngày trong report. Không verify được `E` thì nói rõ đó là
     assumption.
4. **Fetch GSC 3 kỳ cùng filter** bằng tool `fetch-search-analytics.py`
   (xem `## Nguồn Số Liệu GSC`), **không gọi MCP**. Dùng `--dimensions query,page`
   cho URL-level và `--dimensions query` cho keyword movers; không dùng `page` làm
   dimension duy nhất khi đã filter theo `page`. Mỗi kỳ ghi 1 file
   `data/raw/gsc-{kỳ}-{scope}.json` để trace số về nguồn.
5. **Join action → URL đích → GSC delta.** Một URL có thể nhận nhiều action từ
   nhiều tab; giữ nguyên list tab nguồn thay vì chọn một.
5b. **Lấy giờ đã bỏ ra cho từng action** từ MWG Task Console (xem
   `## Giờ Bỏ Ra: Đọc Từ MWG Task Console`). Không có giờ thì ghi `null`, **không
   ước lượng** — một cột giờ đoán bừa sẽ làm mọi tỷ số hiệu quả/giờ sai theo hướng
   không ai kiểm được.
6. **Chấm bucket** theo `references/impact-classification-rules.md`, đúng thứ tự
   ưu tiên trong file đó. Xuất bảng đối chiếu ra `data/processed/`.
   Xếp bảng cuối theo **hiệu quả trên mỗi giờ**, không chỉ hiệu quả tuyệt đối — xem
   `## Xếp Theo Hiệu Quả/Giờ`.
7. **Viết report** trong `reports/{yymmdd-hhmm}-impact-{slug}.md` theo section
   trong `references/impact-report-contract.md`.
8. **Cập nhật task README** `## Results` với số action theo bucket + delta tổng.
   Nếu `report_targets` bật, xử lý File 1/File 2 trước khi đóng task.

## Output Rules

- Evidence trước, nhận định sau, câu hỏi chưa rõ cuối.
- Mọi con số phải trace được về raw file trong `data/raw/`. Không điền số ước lượng.
- Nếu một action không có row GSC, **trước khi ghi `CHƯA CÓ TRAFFIC GSC TRỰC TIẾP`
  phải verify lại bằng `--dimensions query` + `--filter page:equals:`** (xem
  `## Nguồn Số Liệu GSC`). Rỗng vì gọi sai tổ hợp dimension là chuyện đã xảy ra thật. Verify xong vẫn
  rỗng thì ghi nhãn đó, và **không** suy ra action thất bại.
- Nếu action mới xong chưa đủ 7 ngày trong P1, ghi `CHỜ DỮ LIỆU`, không chấm điểm.
- Verdict cấp ngành hàng phải nêu cả impressions và CTR, không chỉ clicks —
  clicks tăng khi impressions giảm là tín hiệu CTR, cần nói rõ.
- Tiếng Việt ngắn gọn. Với `## Recommendations`, mỗi item phải gắn URL cụ thể.

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

## Giờ Bỏ Ra: Đọc Từ MWG Task Console

Câu hỏi skill này thật sự trả lời là **"action nào đáng làm tiếp"**, và câu đó không
trả lời được nếu chỉ biết action nào hiệu quả — một action tăng 30% clicks mà tốn 6
giờ có thể tệ hơn một action tăng 12% mà tốn 40 phút.

Giờ nằm trong `console.db` của MWG Task Console. Đọc qua CLI headless (chỉ đọc, chạy
song song được với app đang mở):

```bash
"/Applications/MWG Task Console.app/Contents/MacOS/mwg-task-console" \
  --list-hours --from 2026-07-01 --to 2026-07-31
```

- Dùng `--list-hours --from D --to D` khi cụm action trải nhiều tuần.
- Dùng `--export-week` khi cụm nằm gọn trong một tuần.
- Mỗi hàng có `slug`, `kind`, `label`, `seconds`, `so_ngay`. `kind: "routine"` là việc
  cố định hằng ngày (follow traffic, log báo cáo) — **loại chúng khỏi cột giờ của
  action**, chúng không thuộc về một action cụ thể nào.
- Map task → action bằng slug task trong `tasks/`, hoặc bằng ngày làm khi task gom
  nhiều action cùng loại.

Ba ca phải ghi `null` thay vì một con số:

1. Action làm trước khi cài app → không có giờ. `--list-hours` trả `moc` sớm nhất qua
   `--stats`; action trước mốc đó là chưa đo, không phải 0 giờ.
2. Một task gom nhiều action mà không tách được → ghi giờ ở mức **cụm**, để trống
   ở mức action, và nói rõ trong report là không tách được credit.
3. CLI báo `schema version` không khớp → mở app một lần rồi chạy lại. Không đoán giờ
   để lấp chỗ trống.

## Xếp Theo Hiệu Quả/Giờ

Sau khi có cột giờ, thêm `hieu_qua_moi_gio = delta_clicks / gio_bo_ra` vào bảng và xếp
giảm dần theo cột đó. Ba rule bắt buộc:

- `gio_bo_ra` là `null` → dòng đó **không có** hiệu quả/giờ và xếp thành một nhóm
  riêng ở cuối, không xếp chung như thể bằng 0.
- `gio_bo_ra` dưới 0.25 giờ → không tính tỷ số (mẫu số quá nhỏ làm tỷ số nổ), ghi
  `giờ quá nhỏ để chia` và giữ delta tuyệt đối.
- `delta_clicks` âm thì tỷ số cũng âm — giữ nguyên dấu. Một action tốn nhiều giờ mà
  làm giảm traffic là kết luận quan trọng nhất của cả bảng, không được ẩn đi.

Trong `## Recommendations`, ưu tiên theo hiệu quả/giờ chứ không theo delta tuyệt đối,
và nói rõ khi hai cách xếp cho thứ tự khác nhau — đó chính là chỗ đáng đọc nhất.

Cột giờ này cũng là nguồn cho yếu tố đánh giá owner "giảm giờ làm, có số giờ
trước/sau" trong `docs/kpi-and-owner-context.md`.

## Security

- Không đọc `.env`, OAuth token, client secret, credential file.
- Không in API key, credential ID, hoặc full auth header vào report/chat.
- Skill này là **read-only trên live Sheet**. Chỉ ghi Sheet khi user yêu cầu rõ,
  ghi range hẹp, và verify bằng readback hẹp.
- Không copy nguyên payload GSC vào chat; summarize rồi lưu file trong task.

## Existing Related Skills

- `seo-gsc-category-review`: review traffic ngành hàng khi không gắn action.
- `seo-gsc-compare`: check nhanh 1 URL/keyword qua 2 kỳ.
- `seo-log-cv` / `seo-log-weekly-work`: log File 1/File 2 sau khi nghiệm thu.
- `gws-sheets-read`: đọc `Data Order TGDD` khi không dùng MCP.
- `seo-work-efficiency-review`: nhìn từ phía ngược lại — giờ đi vào đâu và nghẽn ở
  đâu, không cần action có kết quả GSC. Hai skill dùng chung cột giờ từ CLI.

## References

- `references/action-source-map.md` — source action, tab, ID prefix, cột status/ngày xong.
- `references/impact-classification-rules.md` — 6 bucket + threshold + thứ tự chấm.
- `references/impact-report-contract.md` — artifact naming và section report.

## Unresolved Questions

- Review window mặc định đang là 7 ngày sau ngày xong action
  (`measurement-logic.md` ghi window này chưa finalized). Action loại content
  nặng có thể cần 14-28 ngày — chờ user chốt.
- Threshold `HIỆU QUẢ CAO` đang là `+20%` clicks so P0, lấy từ lần nghiệm thu
  ngành Laptop 10/08/2026. Chưa được approve thành chuẩn chính thức.
