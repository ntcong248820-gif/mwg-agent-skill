# Ahrefs API: units, giá cột, cách gọi tiết kiệm

Nguồn gốc: docs chính thức `docs.ahrefs.com/en/api/docs/limits-consumption`, `.../free-test-queries`,
`.../reference/keywords-explorer/get-matching-terms` (đọc 30/09/2026). Đã rút hết vào đây —
**không cần đọc lại docs mỗi lần chạy**. Chỉ đọc lại khi nghi Ahrefs đổi giá: mở bằng browser pane
(`WebFetch` trả 404 vì trang render bằng JS).

## 1. Công thức chi phí

```
units = max(50, per_row_cost × số_dòng_trả_về)
per_row_cost = tổng giá các cột KHÁC NHAU trong select ∪ where ∪ order_by   (cột lặp chỉ tính 1 lần)
```

- Sàn 50 units/request: request nhỏ vẫn mất đủ 50 → **gom ≥ 5 dòng/request** khi cột là 11 units/dòng.
- Giá cột mặc định **1 unit**. Cột đắt (Keywords Explorer matching-terms): `volume`, `difficulty`,
  `global_volume`, `intents`, `traffic_potential`, `volume_monthly` = **10 units**.
  Cột 1 unit: `keyword`, `cpc`, `cps`, `parent_topic`, `serp_features`, `volume_desktop_pct`,
  `volume_mobile_pct`, `first_seen`, `serp_last_update`.
- Request trả từ **cache không tốn units**. Header mỗi response: `x-api-rows`, `x-api-units-cost-row`,
  `x-api-units-cost-total` (dự kiến), `x-api-units-cost-total-actual` (thực tế), `x-api-cache` (hit|miss|no_cache).
- Free test query: Keywords Explorer miễn phí khi tham số `keywords` CHỈ gồm `ahrefs`/`yep`/`firehose`
  (thêm keyword khác hoặc `keyword_list_id` = tính phí), `limit` bị chặn 100. Dùng để **ước lượng 0 đồng**:
  chạy cùng hình dạng request, đọc `x-api-units-cost-row`. Lệnh: `ahrefs_fetch.py smoke` (tự đối chiếu bảng giá).
  Bẫy đọc header: request nhỏ (tổng < 50) báo `cost_row` = 50 chia số dòng (vd 1 dòng → 50, 3 dòng → 16),
  đó là sàn chứ không phải giá thật. Muốn thấy giá thật phải chọn đủ cột đắt/đủ dòng để vượt 50.
- Hạn mức tháng theo gói: Lite 200.000 · Standard 800.000 · Advanced 2.000.000 · Enterprise tuỳ chỉnh.

## 2. Bảng giá cho nhu cầu phổ biến

Phần lớn việc research chỉ cần `keyword` + `volume`:

| `select` | units/dòng | Ghi chú |
| --- | --- | --- |
| `keyword,volume` | **11** | dùng mặc định |
| `keyword,volume,difficulty,cpc,parent_topic` (bộ cột rộng) | 23 | phí thừa 12/dòng nếu bạn không dùng KD/CPC |
| + `order_by=volume:desc` | không đổi | `volume` đã tính |
| + `volume_monthly` | +10 | không cần; còn không dùng được trong `order_by` |

Ví dụ: 1 URL, `limit=30` → 30×11 = **330 units**. 6 URL Hãng/Filter → ~2.000 .
`limit` mặc định của API là **1000** → nếu quên đặt limit, 1 request = 11.000 units. **Luôn đặt `--limit`.**

## 3. Endpoint dùng

Base `https://api.ahrefs.com/v3/keywords-explorer`, header `Authorization: Bearer <AHREFS_API_KEY>`, mặc định `country=vn` (sửa trong `ahrefs_fetch.py` nếu làm thị trường khác).

| Endpoint | Dùng khi | Tham số chính |
| --- | --- | --- |
| `matching-terms` | tìm keyword mới quanh một seed (Hãng, NH Filter, Dòng Filter) | `keywords=<seed>`, `limit`, `order_by=volume:desc`, `match_mode=terms|phrase`, `terms=all|questions`, `where` |
| `overview` | đo volume của danh sách keyword đã biết (SP: mã, hãng+mã...) | `keywords=a,b,c`, `select` |

- `match_mode=terms`: chứa các từ theo thứ tự bất kỳ (rộng). `phrase`: đúng thứ tự (hẹp, ít dòng hơn → rẻ hơn).
- `where` lọc phía server → giảm số dòng trả về → giảm units. Cột dùng trong `where` cũng tính giá (volume đã có sẵn nên 0 phí thêm).
- Key: tên biến lấy từ `AHREFS_KEY_VAR` (env), mặc định `AHREFS_API_KEY`; giá trị đọc từ môi trường hoặc file `.env` (đổi đường dẫn bằng `AHREFS_ENV_FILE`). **Không in key.**
- HTTP 429 = quá tần suất: đợi ~20 giây rồi thử lại 1 lần (script đã làm). HTTP 403 = hết units.

## 4. Quy tắc tiết kiệm (áp dụng theo thứ tự)

1. `select=keyword,volume` — không thêm cột.
2. Luôn `--limit` nhỏ: Hãng/Filter 20–30; thêm khi URL ít keyword mới.
3. SP: **không** chạy `matching-terms` cho từng SP. Sinh sẵn ứng viên theo khuôn (xem `keyword-rules.md` mục SP),
   đo một lượt bằng `overview` theo lô; chỉ SP nào có keyword volume cao mới mở rộng bằng `matching-terms`.
4. Lô `overview`: ≥ 5 keyword/request (sàn 50 units). Giữ lô ≤ 50 keyword vì giới hạn keyword/request **chưa xác minh**.
5. Không gọi lại request y hệt (cache miễn phí, nhưng đổi tham số là mất cache).
6. Trước mỗi lần chạy thật: `ahrefs_fetch.py ... ` không có `--approve` để in ước lượng → người chịu chi phí xác nhận → chạy lại với `--approve <units>`.
7. Mọi response ghi `*.ledger.jsonl` (units thực tế, cache hit/miss). Báo tổng units đã tốn vào report.

## 5. Quy ước volume khi lưu kết quả

Ahrefs nhóm "0–10" (API trả `0` hoặc `null`) → **ghi 5** (quy ước của skill; đổi ở `sheet_volume` nếu bạn muốn khác). Volume khác giữ nguyên
(10, 20, 50...). Không ghi 0 cho keyword đã đo bằng Ahrefs.

## 6. Đã kiểm bằng request miễn phí (30/09/2026, key qua `AHREFS_KEY_VAR`)

| Request (free) | Units/dòng thật | Kết luận |
| --- | --- | --- |
| matching-terms `keyword` ×100 dòng | 1 | khớp |
| matching-terms `keyword,volume` ×100 dòng | 11 (tổng 1.100) | khớp |
| matching-terms `keyword,volume,difficulty,cpc,parent_topic` ×100 | 23 (tổng 2.300) | khớp (select skill cũ) |
| overview 3 keyword `keyword,volume,difficulty` | 21 | khớp → **overview tính giá y như matching-terms** |
| overview 3 keyword + global_volume, traffic_potential, intents | 51 | khớp |
| overview 3 keyword `keyword,volume,volume_monthly` | 21 | khớp |

Gọi bằng khoá Ahrefs hợp lệ, `actual = 0` cho cả 7 request. Bảng giá `FIELD_COST` trong `ahrefs_fetch.py` đúng với Ahrefs.

## 7. Chưa xác minh (đừng khẳng định trong report)

- Giới hạn số keyword mỗi request `overview` (free chỉ thử được 3 keyword); giữ lô ≤ 50.
- Rate limit/phút, cách xem units còn lại, có tính phí khi trả 0 dòng hay không.
- Gói Ahrefs hiện tại và units còn trong tháng: hỏi người quản lý tài khoản Ahrefs, ghi vào report.
