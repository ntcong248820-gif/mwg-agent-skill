# Action Priority Rules

Xếp ưu tiên theo **khoảng cách tới KPI**, và dùng đúng từ vựng của sheet system chứ
không tự đặt bộ nhãn thứ hai.

KPI là **95% của 1728 keyword trong `[KPI] All KW` đạt Top 1-2**, phạm vi
`Nhóm NH = Laptop`, hạn 31/12/2026. Không có KPI cho Traffic.

Định nghĩa đầy đủ, bẫy phạm vi, và cách owner được đánh giá: `docs/kpi-and-owner-context.md`.

Hai điều bắt buộc rút ra từ đó:

1. **KPI đếm keyword, mọi KW bằng nhau.** Volume dùng để xếp thứ tự trong cùng nhóm
   khoảng cách và để kể chuyện với sếp — không bao giờ nhân vào con số KPI.
2. **Lọc `Nhóm NH = Laptop`, không lọc `Tên Ngành hàng = laptop`.** Cái thứ hai chỉ phủ
   839/1728 = 49% phạm vi, và bỏ đúng 2 sub-ngành hàng đang hụt nặng nhất
   (`máy tính để bàn` 37.6%, `màn hình máy tính` 31.6%).

## Nguyên tắc: sheet đã phân loại rồi

Sheet system đã có 3 thứ mà skill này từng tự dựng lại:

| Cần gì | Sheet đã có | Ở đâu |
| --- | --- | --- |
| URL nào đang ở đâu so với KPI | `Trạng thái KPI` + `Xu hướng Tỷ lệ` | `URL_Cần_Xem` cột `Trạng thái KPI`, `Xu hướng Tỷ lệ` |
| Keyword nào cần xem và vì sao | `Lý do cần xem` | `KW_Cần_Xem` |
| Band rank | `RANK_CUSTOM` — 6 mức | `Data Rank`, và `Rank custom` ở các view |

Đừng đặt bộ nhãn cạnh tranh. Người đọc report phải khớp được số của skill với
`Dashboard_Tổng_Quan`.

## Xếp ưu tiên: đếm KW theo khoảng cách band

KPI đếm keyword → **đơn vị ưu tiên là số KW có thể đưa vào Top 1-2**, không phải volume
và không phải nhãn xu hướng.

Chia KW chưa đạt của mỗi URL thành 2 nhóm:

| Nhóm | Band `RANK_CUSTOM` | Ý nghĩa |
| --- | --- | --- |
| **gần** | `2.1-3.0`, `3.1-4.0` | nhích 1–2 bậc là đạt KPI |
| **xa** | `4.1-10.0`, `>10.0`, `No Rank` | phải leo nhiều bậc hoặc làm lại |

Xếp URL theo: **số KW gần** giảm dần → **volume của nhóm gần** giảm dần → **số KW xa**.
Cắt nhóm theo nhịp KW/tuần cần thiết để về đích 95% đúng hạn:

| Nhãn | Nghĩa |
| --- | --- |
| `P1` | lấp đủ nhịp 1 tuần |
| `P2` | tuần kế tiếp |
| `P3` | còn KW gần, xếp hàng |
| `backlog-xa` | KW gần = 0, chỉ còn KW xa — không làm tuần này |

Đo trên lô `15/08/2026`, `Nhóm NH = Laptop`, nhịp 41 KW/tuần:

| Nhãn | URL | KW gần | KW xa | Volume gần |
| --- | ---: | ---: | ---: | ---: |
| `P1` | 2 | 60 | 83 | 1.334.330 |
| `P2` | 1 | 22 | 14 | 13.175 |
| `P3` | 66 | 269 | 312 | 357.035 |
| `backlog-xa` | 14 | 0 | 115 | 0 |

Tổng 351 KW gần → làm hết đưa tỷ lệ từ 49,4% lên 69,7%. Chưa đủ 95%, nên band
`4.1-10.0` (177 KW) phải chạy song song, không dồn cuối năm.

### Vì sao bỏ ma trận `Trạng thái KPI` × `Xu hướng Tỷ lệ`

Bản trước của file này xếp hạng bằng ma trận 3×3 và cho `Đang tăng` vào hạng chót với
lý do "đang tự lên, đừng đổ action". Ba lỗi đo được:

1. **`Xu hướng Tỷ lệ` chỉ nói hướng, không nói mức.** `/laptop-acer` (94% đạt) và
   `/laptop-lenovo-thinkpad` (17% đạt) cùng nhãn `Đang tăng`. Ngưỡng trong công thức là
   `0,0005` — chốt chống lỗi làm tròn, không phải ngưỡng ý nghĩa.
2. **Mẫu số nhỏ phóng đại %.** 15/29 URL `Đang tăng` ở ngành `laptop` chỉ vì **đúng 1
   keyword** đổi. `/laptop-dell-15` hiện `50% → 100%` trên tổng 2 KW.
3. **Ma trận loại mất nhóm lớn nhất.** Ô `Đang tăng` gánh 490.800 volume ở ngành
   `laptop`, gần 4 lần `P1+P2` gộp lại, mà bị đẩy khỏi plan.

Hai cột đó vẫn dùng — nhưng để **đọc ngữ cảnh và viết report**, không để xếp hạng.
`Đang giảm` là tín hiệu cần nêu trong report và cần chẩn đoán nguyên nhân; nó không tự
động làm URL đó đáng làm hơn một URL có nhiều KW gần hơn.

### Volume dùng vào đâu

| Dùng | Không dùng |
| --- | --- |
| Xếp thứ tự giữa các URL **cùng số KW gần** | Nhân vào con số KPI |
| Chọn keyword nào làm trước **trong** một URL | Tuyên bố KPI đạt |
| Kể chuyện với sếp: "KW lớn đã cover bao nhiêu" | Thay cho việc đếm keyword |

Số thật lô `15/08/2026`: volume đã ontop **20,8%**; 50 KW volume lớn nhất chiếm
**85,6%** tổng volume nhưng chỉ **20/50** đã ontop. Đòn bẩy đơn lẻ lớn nhất là keyword
`máy tính` — volume 1.300.000, band `3.1-4.0`, thuộc `/may-tinh-de-ban`.

## Band rank: dùng `RANK_CUSTOM` của sheet

6 mức, đo trên lô `15/08/2026`, 1.728 keyword:

| `RANK_CUSTOM` | Số KW | Ý nghĩa |
| --- | ---: | --- |
| `1.0-2.0` | 853 | đã đạt Ontop 1-2 |
| `2.1-3.0` | 235 | sát đích, đẩy là lên |
| `3.1-4.0` | 116 | gần |
| `4.1-10.0` | 177 | còn xa |
| `>10.0` | 320 | rất xa |
| `No Rank` | 27 | **không rank được** |

Band này là **trục ưu tiên chính**, không phải tiêu chí phụ. Không tự định nghĩa khoảng số.

`No Rank` là nhãn riêng của sheet, không phải rank 0. Tự parse `Ranking Tổng` sẽ thấy
`0.00` và band "r <= 2" sẽ hút 27 keyword này vào nhóm "đã top 1-2" — ngược hoàn toàn.
Đọc cột `RANK_CUSTOM` thì không gặp lỗi này.

## Thứ tự áp rule

1. **Đọc đúng lô, đúng cột.** `Data Rank` append-only → lọc lô mới nhất. Tra cột bằng
   tên header. Xem `sheet-write-policy.md` mục `Read Rules`.
2. **Đọc `Dashboard_Tổng_Quan`** để biết số hiện hành. Số của skill phải khớp hoặc giải
   thích được chênh lệch.
3. **Xếp ưu tiên** theo số KW gần → volume gần → KW xa, cắt theo nhịp KW/tuần.
4. **Loại action đã có trong `Planning_Grid_V2`** — xem mục dưới.
5. **Ledger gate (S2)** trên `Action_Event`: action `DECLARED_NOT_LIVE` nổi thành
   **dòng nhãn `VẬN HÀNH`**, **không** hạ hạng SEO của URL.

   Nhãn `VẬN HÀNH` tách riêng khỏi `P1`–`P3` vì nó không phải một mức ưu tiên SEO — nó
   là việc của người thực thi. Gộp vào một hạng ưu tiên làm hạng đó mang 2 nghĩa không
   thay thế được cho nhau, nên phải hai nhãn.
6. **Cùng số KW gần thì xếp theo volume nhóm gần**, rồi theo số KW xa.

### Vì sao ledger không được hạ hạng URL

Đo 2026-08-20 trên 43 URL Laptop: cách gộp hạ **16/43 URL** xuống hạng chót, trong đó có
`/laptop-samsung` (15 KW cần xem, 9 KW giảm, đạt 17%) — tức URL đang mất nhiều nhất bị
đẩy khỏi plan SEO vì một order chưa live. Tách ra thì dòng `VẬN HÀNH` còn đúng số
action chưa live, và hạng SEO của URL không bị nhiễu.

Một action chưa live là việc **vận hành**; hạng SEO của URL là việc **nội dung**. Hai
việc, hai dòng.

## Trạng thái thực thi: đọc `Planning_Grid_V2` cột Auto

`Planning_Grid_V2` có **8 nhóm action** (xác nhận live 2026-09-23, đọc trực
tiếp `Planning_Grid_V2!R1:AP1` — đừng tin số nhóm ghi trong tài liệu cũ),
mỗi nhóm 3 cột `Ngày / Status / Note`:

| Action | Ngày | Status | Note |
| --- | --- | --- | --- |
| TD Sửa Title/Desc | `S` | `T` | `U` |
| IB Viết Infobox | `V` | `W` | `X` |
| IMG Làm hình Infobox | `Y` | `Z` | `AA` |
| AC Audit Content | `AB` | `AC` | `AD` |
| IL Chèn internal link | `AE` | `AF` | `AG` |
| BL Đặt bài blog hỗ trợ | `AH` | `AI` | `AJ` |
| **CSO Optimize sản phẩm trong danh mục** | `AK` | `AL` | `AM` |
| **BM Backlink MWG** | `AN` | `AO` | `AP` |

`BL` thêm 2026-08-16, `CSO`/`BM` thêm sau đó (`BM` xác nhận 2026-09-22, plan
`260915-0756-backlink-mwg-action-bm` Phase 5). Tài liệu cũ (bản trước bản
này) chỉ liệt kê 6 nhóm và ghi nhầm cột Auto là `AN` — `AN` giờ là cột
`BM - Ngày`, không phải cột tổng hợp. Cột tổng hợp thật đã dịch sang `AT`.

Đọc **cột `AT` `Trạng thái thực thi (Auto)`** (không phải `AN` — xem trên) thay vì
đọc 8 cột status rời: nó đã gom sẵn dạng `TD: Đã xong | IB: Đã xong | IMG: Đã xong`.
Phân bố status nhập tay đo 2026-08-20 (trước khi thêm CSO/BM, số liệu cho 6 nhóm
đầu, chưa đo lại cho CSO/BM): TD 26 `Done`; AC 9 `Done` + 13 `Đang làm`; IMG 7
`Done` + 3 `Blocked` + 2 `Planned`; IB 4 `Done` + 1 `Planned`; BL 1 `Done` + 7
`Đang làm`; IL 2 `Blocked` + 1 `Planned`.

**Cột `AO` `Cảnh báo trùng Infobox`** là rule routing, không phải ghi chú: giá trị
`⚠️ Đã có Infobox — dùng Audit_Content để sửa` (4 dòng ngày 2026-08-20) nghĩa là
**không tạo order IB mới cho URL đó**, phải chuyển sang `AC`. Đọc cột này trước khi
sinh job `IB`.

## Điều kiện có mặt trong plan

| Field | Yêu cầu |
| --- | --- |
| `why` | dẫn được về ít nhất 1 dòng trong `data/raw/` |
| `acceptance` | kiểm được bằng mắt hoặc bằng lệnh |
| `kpi_link` | nói rõ **số KW dự kiến vào Top 1-2** và band hiện tại của chúng |

Không viết được `kpi_link` thì chuyển sang backlog.

## Unresolved

- Nhịp KW/tuần dùng để cắt `P1`/`P2` là suy ra từ deadline 31/12/2026
  (789 KW ÷ ~19 tuần ≈ 41 KW/tuần), **chưa phải cam kết của owner**.
- Dao động giữa 2 lô liền kề lên tới ±222 KW, gấp 5 lần nhịp cần thiết. Chưa tách được
  phần biến động thật và phần do đổi nguồn đo (GSC 7 ngày ↔ Rank RC). Chưa nên dùng
  biến động 1 lô làm căn cứ nghiệm thu.
- `Xu hướng Tỷ lệ` so 2 lô liền nhau (`Tỷ lệ trước đó` vs `Tỷ lệ hiện tại`), tức chu kỳ
  ~1–2 tuần. Nó không thay được verdict L2 (28 ngày) của S1; hai thước đo khác kỳ.
- 27 keyword `No Rank`: chưa rõ là chưa có URL đích hay có URL nhưng Google không xếp.
