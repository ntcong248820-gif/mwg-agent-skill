# Action Source Map

Nơi đọc action đã done để nghiệm thu. Đọc read-only.

## Đường mặc định: 2 auto-view, không phải 5 tab thô

Đọc `Action_Event` + `Impact_Timeline` trước. Chỉ mở tab thô khi cần cột mà view
không mang.

| View | Sheet | Dòng (đo 2026-08-20) | Mang gì |
| --- | --- | ---: | --- |
| `Action_Event` | `Data Order TGDD` | 213 | 15 cột chuẩn hoá từ cả 5 tab nguồn. **J** URL cần tác động, **M** `Ngày xong`, **N** `Trạng thái` = nguyên giá trị ô bằng chứng |
| `Impact_Timeline` | `[TGDD] Data Ranking Laptop` | 308 | action đã xong × biến động rank. **P** loại action, **Q** ngày xong, **R** trạng thái, **S** kết luận |

`Action_Event!N` mang **nguyên giá trị ô bằng chứng**, nên gate S2 chạy được ở đây:
68 `OK` + 2 `Not Found` + 1 dòng chứa URL của `Onpage_Blog` đều lộ ra. 162/213 dòng
có `Ngày xong`.

**Hai bẫy của `Impact_Timeline`:**

1. Mọi dòng của nó có `Trạng thái action = OK` — view **tự loại**
   `DECLARED_NOT_LIVE`. Tiện, nhưng nó không cho biết bao nhiêu action bị loại. Tỷ lệ
   thành công tính riêng trên view này **không có mẫu số đúng**. Đếm phần bị loại từ
   `Action_Event`.
2. **194/308 dòng (63%) có từ 2 loại action trở lên** trên cùng URL trong cùng kỳ đo
   (`Title/Desc, Infobox` 121 dòng; `Title/Desc, Audit_Content` 49; `Infobox,
   Audit_Content` 24). Rank tăng sau đó **không quy được cho một action nào**. Ghi
   `KHÔNG TÁCH ĐƯỢC CREDIT`, không cộng vào thành tích của một action family.

Chi tiết ở S2 mục 2.2.

## Tab thô: workbook `Data Order TGDD`

Spreadsheet ID: ``

| Tab | Action family | ID prefix | Cột bằng chứng live | Ghi chú |
| --- | --- | --- | --- | --- |
| `Onpage_Blog` | Internal Link | `IL-` | **`F`** — pass = `OK` | Chèn internal link từ blog. Plan date ở `A`/`K`, URL đích ở `G`, note ở `I`. Checker daily, header guard khớp — tin được |
| `Title_Desc` | Metadata | `TD-` | **`I`, `J`** — pass = `OK` | Sửa Title/Description. Checker daily nhưng **không có header guard** |
| `Infobox` | Content | `INFO-` | **`I`** — pass = `TRUE` | Viết/sửa Infobox. Ngày xong ở cột `O`; `P:T` là helper metadata (đang hidden). Checker **chỉ chạy tay** → phần lớn dòng `EVIDENCE_STALE` |
| `Content_Blog` | Content | `CB-` | **`L`** `Nghiệm thu link` | **`NO_CHECKER`** — bản Apps Script đang deploy assert sai header nên throw mỗi ngày, cột L do người điền tay |
| `Audit_Content` | Content | `AC-` | — | **`NO_CHECKER`**. Status mặc định khi tạo order là `Chưa làm` |
| `Content_SP_Optimize` | Content | `CSO-` | `Trạng thái` = `Hoàn thành` + `Product in KPI?` = `TRUE` | Optimize sản phẩm trong danh mục. Rollup theo `CSO Key` ở `Content_SP_Optimize_Rollup` |
| `Backlink_MWG` (qua `Backlink_Target_Map`) | External/Entity | `BM-` | **`Verdict`** trên `Backlink_Target_Map` — pass = `OK` | Backlink nội bộ hệ MWG. `Backlink_MWG!J` chỉ là formula aggregate, đừng đọc trực tiếp cột đó làm bằng chứng. Checker daily 10:00, allowlist 9 host — tin được, cùng hạng `Onpage_Blog` |

Cột bằng chứng và 4 trạng thái ledger định nghĩa ở
`mwg-seo-planning/docs/action-ledger.md` (S2). Bảng trên là bản đọc nhanh; lệch nhau
thì S2 đúng.

Lưu ý khi đọc: workbook lớn, luôn query full range dạng `Infobox!A1:T` thay vì
range ngắn để tránh sót dòng.

## `Action_Event` nằm ở đâu

Trong workbook **`Data Order TGDD`**, không phải Planning workbook. Nó là auto-view,
formula ở `Action_Event!A1`, gom từ `Title_Desc`, `Onpage_Blog`, `Infobox`,
`Audit_Content`, `Blog_Target_Map` (cho `Content_Blog`), `Content_SP_Optimize`,
và `Backlink_Target_Map` (cho `Backlink_MWG`).

Không dùng `Plan_Event` cho skill này — đó là planned-action source, chưa done.
`Planning_Grid_V2` cũng không phải nguồn trạng thái: nó trả lời **khi nào** làm
action. Xem `mwg-seo-planning/docs/planning-workflow.md`.

## Rule đọc sheet

Theo `mwg-seo-planning/docs/sheet-write-policy.md` mục `Read Rules`:

- Range phải phủ hết dòng. Biên cứng kiểu `A1:T500` trên tab lớn trả về ít dòng hơn
  và **không báo lỗi**.
- `Data Rank` là append-only snapshot: lọc `M = max(M)` trước mọi phép tính. Dòng đầu
  tab là lô **cũ nhất**.
- Đừng tự tính lại thứ auto-view đã tính.

## Lọc status rồi join bằng chứng live

Hai bước, không được bỏ bước hai.

**Bước 1 — status khai báo.** Chỉ nhận:

- `OK`
- `Hoàn thành`
- `Đã làm`

Loại bỏ: `Chưa làm`, trống, `Planned`, `Blocked`, `Skipped`.

**Bước 2 — join với cột bằng chứng live theo S2.** Status khai báo một mình **không
đủ** để đưa action vào phân tích. Đây chính là chỗ sinh ra lỗi "URL chưa làm action A
nhưng bị phân tích như đã làm".

So **chính xác** với giá trị pass ở bảng trên. **"Ô không rỗng" không phải tín hiệu
tốt** — checker ghi lý do hoặc nguyên văn nội dung đang live khi lệch. Đo thật trên
`Onpage_Blog!F` ngày 2026-08-20: rule "không rỗng" cho 71 dòng đã live, gate S2 cho
68 `VERIFIED` + 3 `DECLARED_NOT_LIVE`, trong đó 1 dòng chứa URL đầy đủ mà vẫn là lỗi.

Nếu row done nhưng **thiếu ngày xong**, không suy ra ngày. Đưa vào nhóm
`Thiếu ngày xong` và báo count trong report — không chấm bucket. Lần nghiệm thu
Laptop 10/08/2026 có 25 dòng `OK` thiếu date dạng này.

## Lọc scope URL

Ưu tiên theo thứ tự user cung cấp:

1. Danh sách URL cụ thể user đưa.
2. URL prefix ngành hàng (ví dụ `/laptop`, `/man-hinh-may-tinh`).
3. Toàn bộ action trong khoảng ngày user nêu.

Với action internal link, URL trong tab là **URL bài blog nguồn**; URL cần đo là
**URL đích được trỏ tới** (cột `G` của `Onpage_Blog`). Đo sai cột này sẽ ra kết
luận ngược.

## Raw evidence bắt buộc lưu

- `data/raw/action-ledger-{scope}.json` — bảng ledger: mỗi action kèm status khai báo,
  ô bằng chứng nguyên văn, và trạng thái S2 đã suy ra.
- `data/raw/data-order-{scope}-actions.json` — action rows thô đã lọc status.
- `data/raw/gsc-{scope}-p0.json`, `-p2.json`, `-p1.json` — 3 kỳ GSC.

## Cấm

- Không ghi vào `Data Order TGDD` trong skill này.
- Không tạo order mới, không đổi status action.
- Không in Sheet ID kèm token/credential vào report.
- Không sửa Apps Script, không thêm trigger từ skill này.
- Không coi `NO_CHECKER` là đã verify.
