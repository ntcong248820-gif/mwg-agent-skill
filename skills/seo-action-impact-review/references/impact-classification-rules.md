# Impact Classification Rules

Chấm từng action thành đúng 1 bucket. **Thứ tự dưới đây là thứ tự chấm** — bucket
nào match trước thì chốt, không xét tiếp.

## Ký hiệu

| Ký hiệu | Nghĩa |
| --- | --- |
| `P0` | Baseline: 7 ngày liền trước ngày xong sớm nhất của cụm action |
| `P2` | Previous: 7 ngày liền trước `P1` |
| `P1` | Current: 7 ngày complete gần nhất trên GSC |
| `L2` | 28 ngày vs 28 ngày liền trước — kiểm chéo xu hướng tháng |

Định nghĩa 4 kỳ này là bản sao đọc nhanh. **Nguồn duy nhất** là
`mwg-seo-analytics/docs/measurement-windows.md` (S1) mục 7. Lệch nhau thì S1 đúng.
| `ΔC` | `clicks(P1) - clicks(P0)` |
| `ΔC%` | `ΔC / clicks(P0)`, bỏ qua khi `clicks(P0) = 0` |
| `ΔPos` | `position(P0) - position(P1)`; dương = rank tốt lên |

## Thứ tự chấm

### 0. KHÔNG XÁC MINH ĐƯỢC

Match khi trạng thái ledger theo `mwg-seo-planning/docs/action-ledger.md` (S2)
**không phải** `VERIFIED`.

Chạy bước này **trước mọi bucket khác**. Không chấm bucket, không vào tử số lẫn mẫu
số của tỷ lệ thành công.

Báo riêng theo 3 nhóm, vì hành động tiếp theo của mỗi nhóm khác nhau:

| Nhóm | Nghĩa | Việc phải làm |
| --- | --- | --- |
| `DECLARED_NOT_LIVE` | order khai done nhưng bằng chứng nói chưa live | đi hỏi người thực thi |
| `EVIDENCE_STALE` | bằng chứng trống hoặc không rõ chạy lúc nào | chạy lại checker rồi nghiệm thu lại |
| `NO_CHECKER` | tab không có bằng chứng máy đọc được | chốt cách nghiệm thu thủ công |

`DECLARED_NOT_LIVE` **không** được xếp cùng mục với bucket 5 `CHƯA ĐẠT / SUY GIẢM`.
Một cái là lỗi vận hành, một cái là kết luận về SEO. Gộp lại là cách một lỗi vận hành
bị đọc thành thất bại chiến lược.

### 0b. KHÔNG TÁCH ĐƯỢC CREDIT

Match khi URL nhận **từ 2 loại action trở lên** trong cùng kỳ đo.

Chạy ngay sau bucket 0. URL vẫn được chấm bucket hiệu quả ở cấp **URL**, nhưng kết quả
**không** được cộng vào thành tích của một action family nào.

Đo 2026-08-20 trên `Impact_Timeline`: **194/308 dòng (63%)** thuộc nhóm này —
`Title/Desc, Infobox` 121 dòng, `Title/Desc, Audit_Content` 49, `Infobox,
Audit_Content` 24. Chỉ 114 dòng có đúng 1 loại action.

Hệ quả phải nêu trong report: câu "action Title/Desc hiệu quả X%" chỉ tính được trên
114 dòng đơn-action. Tính trên cả 308 dòng là gán công của 3 loại action cho 1 loại.

### 1. CHỜ DỮ LIỆU (MỚI XONG)

Match khi `ngày xong action > ngày bắt đầu P1`.

Action chưa nằm trọn trong cửa sổ đo. **Không** chấm điểm, không tính vào tỷ lệ
thành công. Ghi ngày xong + ngày đủ dữ liệu dự kiến (`ngày xong + 7`).

### 2. CHƯA CÓ TRAFFIC GSC TRỰC TIẾP

Match khi URL đích **không có row nào** trong GSC ở cả `P0` và `P1`.

Thường là bài blog/tin hoặc infobox làm nhiệm vụ truyền internal link về landing
page. Đây **không phải** thất bại. Nếu action là internal link, ghi thêm URL đích
mà nó trỏ về và bucket của URL đó.

### 3. HIỆU QUẢ CAO

Match khi thỏa **một trong hai**:

- `ΔC% >= +20%` và `ΔC >= +50` clicks; hoặc
- `ΔPos >= +0.5` và `ΔC > 0`.

Điều kiện `ΔC >= +50` để URL nhỏ tăng từ 3 lên 4 clicks không bị gắn nhãn cao.

### 4. HIỆU QUẢ / DUY TRÌ TOP

Match khi thỏa **một trong hai**:

- `position(P1) <= 3.0` và `ΔC >= 0` (đang giữ top, không tụt); hoặc
- `+5% <= ΔC% < +20%`.

### 5. CHƯA ĐẠT / SUY GIẢM

Match khi thỏa **một trong hai**:

- `ΔC% <= -5%`; hoặc
- `ΔPos <= -0.5` (rank xấu đi từ nửa bậc).

Bucket này bắt buộc có dòng recommendation riêng trong report.

### 6. DUY TRÌ / ÍT BIẾN ĐỘNG

Bucket còn lại: `-5% < ΔC% < +5%` và `|ΔPos| < 0.5`.

## Rule bắt buộc kèm theo

1. **Một URL nhiều action:** chấm ở cấp URL, rồi gán bucket đó cho mọi action
   trỏ vào URL đó, và liệt kê đủ tab nguồn (ví dụ `Infobox, Title_Desc`).
   Không chia credit cho từng action — GSC không tách được. Đánh dấu bucket `0b` và
   **loại khỏi mọi con số theo action family**. Đây là 63% dòng, không phải ngoại lệ
   nhỏ.
2. **Không suy nhân quả một chiều:** nếu impressions toàn ngành giảm mà clicks
   tăng, nói rõ phần tăng đến từ CTR/rank, không từ demand.
3. **Mùa vụ:** nếu kỳ đo trùng cao điểm (tựu trường, sale lớn), ghi cảnh báo vào
   `## Unresolved Questions` — bucket vẫn giữ, nhưng verdict phải nêu.
4. **Tỷ lệ thành công** = `(bucket 3 + bucket 4) / (tổng action - bucket 0 - bucket 1)`.
   Loại cả `KHÔNG XÁC MINH ĐƯỢC` và `CHỜ DỮ LIỆU` khỏi mẫu số. Ghi rõ công thức trong
   report.

   Tỷ lệ **theo action family** có mẫu số khác: `(tổng action - bucket 0 - bucket 0b
   - bucket 1)`. Chỉ action đơn-loại mới quy được credit cho một family.

   Con số này sẽ **thấp hơn** các lần nghiệm thu trước khi có bucket 0. Đó là kết quả
   mong đợi: trước đây action chưa live được tính vào thành tích. Ghi rõ đã đổi cách
   đếm kèm số cũ để đối chiếu; **không** nới gate để giữ con số cũ.
5. **`clicks(P0) = 0` nhưng `clicks(P1) > 0`:** chấm `HIỆU QUẢ CAO` khi
   `clicks(P1) >= 50`, ngược lại `HIỆU QUẢ / DUY TRÌ TOP`.

## Ví dụ đối chiếu (ngành Laptop, 10/08/2026)

| URL | clicks P0 | clicks P1 | ΔC% | Pos P0 | Pos P1 | Bucket |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `/laptop` | 5,317 | 7,155 | +34.6% | 2.6 | 2.2 | HIỆU QUẢ CAO |
| `/laptop-dell` | 1,722 | 2,300 | +33.6% | 3.1 | 2.8 | HIỆU QUẢ CAO |
| `/laptop-hp-compaq-victus` | — | — | ~0 | 2.1 | 2.1 | HIỆU QUẢ / DUY TRÌ TOP |
| `/laptop-dell-inspiron` | 543 | 472 | -13.1% | 4.6 | 4.2 | CHƯA ĐẠT / SUY GIẢM |

Dòng cuối là ca đáng chú ý: rank tốt lên nhưng clicks giảm — vẫn xếp
`CHƯA ĐẠT / SUY GIẢM` vì rule 5 xét `ΔC%` trước `ΔPos`, và phải nêu nghịch lý
này trong report.
