# Rule lọc keyword theo dạng trang

Cài đặt trong `scripts/kw_rules.py`; chạy `python3 scripts/tests/test_kw_rules.py` sau khi sửa.
Verdict: **keep** (dùng được) · **review** (mơ hồ, người xem) · **drop** (loại, có kèm lý do).

Rule viết cho thị trường Việt Nam (keyword tiếng Việt). Danh sách hãng, ngành hàng, nhà bán lẻ trong
`kw_rules.py` là điểm khởi đầu — sửa cho khớp lĩnh vực của bạn.

## 0. Quy ước chung

- Chuẩn hoá: chữ thường, gộp khoảng trắng, cắt dấu `: , - _ + .` ở cuối. Không trùng keyword trong cùng một trang.
- **Volume:** Ahrefs nhóm 0–10 (trả `0`/null) → ghi **5**. Volume còn lại giữ nguyên.
- Tiếng Việt **có dấu**: cụm Việt viết thiếu dấu (`man hinh`, `may choi game`) bị drop. Từ vốn không dấu (`laptop`, `tai nghe`) không bị loại.
- Không lấy tên nhà bán lẻ (`fptshop`, `cellphones`, `shopee`...) làm keyword.
- Loại ở MỌI dạng trang (intent blog/hỗ trợ): `review`, `đánh giá`, `so sánh`, `vs`, `specs`, `thông số`, `hướng dẫn`, `cách`,
  `là gì`, `có tốt không`, `driver`, `tải`, `cài đặt`, `lỗi`, `sửa chữa`, `reset`, `firmware`, `ngày ra mắt`...
- Giữ: biến thể giá/mua (`giá`, `giá rẻ`, `mua`, `bao nhiêu`, `chính hãng`).
- **Đọc trang đích trước khi duyệt** (bước nên làm): mở URL, xem sản phẩm đang bán và khoảng giá để xác định intent thật.
  Keyword `giá rẻ` trên trang chỉ bán máy cao cấp là sai intent dù đúng chính tả.
- Cờ `main` (KW chính): mặc định mọi keyword `keep` đều `True`. Đổi ở `filter_keywords.assign_main`.

## 1. Sản phẩm (`sp`) — tiêu chí là ĐỊNH DANH, không phải volume

Keyword hợp lệ khi tìm nó ra đúng trang sản phẩm đó; chỉ có mã model vẫn được. Nhiều sản phẩm chỉ có keyword volume 0
nhưng vẫn là keyword đúng, nên volume không phải bộ lọc.

**Giữ:** chứa mã của chính sản phẩm, hoặc ≥ 2 thành phần tên dòng khớp tên sản phẩm (tách chữ/số: `fold8` ↔ `fold 8`).
**Khuôn sinh ứng viên** (đo volume bằng `overview`): `[mã]` · `[hãng] [mã]` · `[loại] [hãng] [mã]` · `[hãng] [dòng ngắn]` ·
`[loại] [hãng] [dòng ngắn]`.
**Loại:** chứa mã SKU khác sản phẩm (biến thể màu/cấu hình khác) · câu > 6 từ kèm ≥ 2 thông số · intent blog · không liên quan ·
tên hãng khác (khi tên sản phẩm có ghi hãng).
**review:** chỉ trùng 1 thành phần tên, hoặc chỉ có mã lạ. Năm (`2025`) được giữ ở sản phẩm.

## 2. Hãng (`hang`) — bộ lọc intent nghiêm ngặt

Loại: dòng con (`flip`, `aero`, `go`, `pro`, `360`), thông số chi tiết (inch, OLED/IPS/4K, CPU, RAM/SSD), mã model, năm,
hãng khác, intent blog. Giữ: `[ngành] [hãng]`, `[hãng] giá`, `mua [ngành] [hãng]`, `[hãng] [ngành] giá rẻ`.
Keyword không chứa tên hãng → review.

## 3. Filter ngành hàng / dòng (`nh`, `dong`) — thuộc tính của filter là từ BẮT BUỘC

1. Thuộc tính trong *tên filter* và *URL* được giữ nguyên, không bao giờ coi là thông số cần loại (filter OLED → `oled` là từ phải có).
2. Keyword phải chứa ít nhất một thuộc tính của filter; không chứa → **review** (người dùng hay viết biến thể).
3. Thông số **khác** filter (filter OLED mà keyword có `ips`, `27 inch`) → **review** (thường thuộc URL hẹp hơn).
4. **drop:** mã model cụ thể (thuộc trang sản phẩm), intent blog, hãng khác khi trang đã gắn một hãng.
5. Hãng xuất hiện ở filter thuộc tính không gắn hãng → drop (thuộc trang hãng).
6. Năm được giữ (filter dòng máy hay có hậu tố năm).
7. Bốn nhóm lỗi hay gặp ở filter:
   1. **Trỏ riêng một hãng/dòng/nền tảng** → thuộc trang hãng/dòng. Kể cả keyword mở đầu bằng ngành hàng khác.
   2. **Keyword blog/danh sách/công cụ:** `các loại`, `các ...` (mở đầu), `video`, `test`, `độ phân giải ...` (mở đầu).
   3. **Phân khúc chi tiết hơn filter:** giá cụ thể (`giá rẻ 50k`), series (`5000 series`).
   4. **Tiếng Anh:** `screen`, `refresh`, `rate`.
8. Dạng ít gặp (`cũ`, địa danh, `best`, `top`, tiếng Anh) → review để người xem.

## 4. Seed cho `matching-terms`

- Filter ngành hàng: `[ngành hàng] [tên filter]`. Nếu < 5 dòng mới có nghĩa: thử `--mode phrase` thay vì `terms`.
- Filter dòng: `[tên dòng]` và `[hãng] [tên dòng]`.
- Hãng: `[ngành] [hãng]` và `[hãng]`.
- Một seed/trang, `--limit` 20–30. Keyword lõi Ahrefs bỏ sót thì bổ sung thủ công rồi đo lại bằng `overview`.

## 5. Khi nào sửa rule

Có ca keyword bị phân loại sai → thêm ca đó vào `scripts/tests/test_kw_rules.py`, rồi sửa `kw_rules.py`.
Đừng nới rule chỉ vì một ca; nới khi thấy loại oan hàng loạt.
