# Rule lọc keyword theo dạng trang

Cài đặt trong `scripts/kw_rules.py`; chạy `python3 scripts/tests/test_kw_rules.py` sau khi sửa.
Verdict: **keep** (dùng được) · **review** (mơ hồ, người xem) · **drop** (loại, có kèm lý do).

Rule viết cho thị trường Việt Nam (keyword tiếng Việt). Danh sách hãng, ngành hàng, nhà bán lẻ trong
`kw_rules.py` là điểm khởi đầu — sửa cho khớp lĩnh vực của bạn.

## 0. Quy ước chung

- Chuẩn hoá: chữ thường, gộp khoảng trắng, cắt dấu `: , - _ + .` ở cuối. Không trùng keyword trong cùng một trang.
- **Volume:** Ahrefs nhóm 0–10 (trả `0`/null) → ghi **5**. Volume còn lại giữ nguyên.
- Tiếng Việt **thiếu dấu** (`man hinh`, `sim so dep`): **vẫn giữ** (đi qua rule như keyword thường) nhưng `main=False`, không tick KW chính. Nhận diện: keyword toàn không dấu + chứa cụm trong `NO_DIACRITIC_VI` hoặc âm tiết trong `NEED_DIACRITIC` (`kw_rules.missing_diacritics`). Từ vốn không dấu (`laptop`, `tai nghe`, `mua`) không bị tính là thiếu dấu. Intent blog viết không dấu (`cach`, `huong dan`...) vẫn drop.
- Không lấy tên nhà bán lẻ (`fptshop`, `cellphones`, `shopee`...) làm keyword.
- Loại ở MỌI dạng trang (intent blog/hỗ trợ): `review`, `đánh giá`, `quy trình`, `thủ tục`, `nào` (câu hỏi/hệ tin), `so sánh`, `vs`, `specs`, `thông số`, `hướng dẫn`, `cách`,
  `là gì`, `có tốt không`, `driver`, `tải`, `cài đặt`, `lỗi`, `sửa chữa`, `reset`, `firmware`, `ngày ra mắt`...
- **Intent blog tầng 1 — hỏi/tư vấn/sự cố (drop, mọi dạng trang):** `nên mua`, `nên chọn`, `đáng mua`, `có nên`, `loại nào`,
  `nào tốt/ngon/bền`, `ưu nhược`, `kinh nghiệm`, `mẹo`, `tư vấn`, `xuất xứ`, `bảo hành bao lâu`, `có bền`, `bền không`, `ổn không`,
  `được không`, `có tốt`, `bị nóng/đơ/treo/lag`, `hay bị`, `không lên`, `nâng cấp`. `cách` không bắt `cách âm/nhiệt/điện`.
- **Tầng 2 — mơ hồ (review):** `top`, `best`, `mới nhất`, `ra mắt`, `tốt nhất`, `tốt`, `phù hợp`, trừ khi chính trang đã có từ đó
  và trừ `giá tốt` (intent mua). Áp ở mọi dạng trang.
- **Mẫu kiểm hai chiều:** `scripts/known_intent_keywords.json` (blog phải khác keep, intent mua phải là keep), test `IntentBlogLot`
  đọc file này. Thấy keyword blog lọt thì thêm vào file đó.
- Giữ: biến thể giá/mua (`giá`, `giá rẻ`, `mua`, `bao nhiêu`, `chính hãng`).
- **Đọc trang đích trước khi duyệt** (bước nên làm): mở URL, xem sản phẩm đang bán và khoảng giá để xác định intent thật.
  Keyword `giá rẻ` trên trang chỉ bán máy cao cấp là sai intent dù đúng chính tả.
- Cờ `main` (KW chính, tick TRUE) khi **đủ cả 2**: (1) volume search **≥ 10** (`volume_sheet`; nhóm 0–10 ghi 5 hoặc không có số liệu → FALSE) và (2) tiếng Việt **đúng chính tả/có dấu** (không bị `missing_diacritics`). Thiếu 1 trong 2 → vẫn giữ keyword nhưng `main=False`, lý do ghi ở `reason`. Đổi ở `filter_keywords.assign_main` / `MAIN_MIN_VOLUME`.

## 1. Sản phẩm (`sp`) — tiêu chí là ĐỊNH DANH, không phải volume

Keyword hợp lệ khi tìm nó ra đúng trang sản phẩm đó; chỉ có mã model vẫn được. Nhiều sản phẩm chỉ có keyword volume 0
nhưng vẫn là keyword đúng, nên volume không phải bộ lọc.

**Giữ:** chứa mã của chính sản phẩm, hoặc ≥ 2 thành phần tên dòng khớp tên sản phẩm (tách chữ/số: `fold8` ↔ `fold 8`).
**Khuôn sinh ứng viên** (đo volume bằng `overview`): `[mã]` · `[hãng] [mã]` · `[loại] [hãng] [mã]` · `[hãng] [dòng ngắn]` ·
`[loại] [hãng] [dòng ngắn]`.
**Loại:** chứa mã SKU khác sản phẩm (biến thể màu/cấu hình khác) · câu > 6 từ kèm ≥ 2 thông số · intent blog · không liên quan ·
tên hãng khác (khi tên sản phẩm có ghi hãng).
**review:** chỉ trùng 1 thành phần tên, hoặc chỉ có mã lạ. Năm (`2025`) được giữ ở sản phẩm.

## 1.1. Quy tắc dòng con, bản tiêu chuẩn (Standard Variant) và sản phẩm mới

Áp dụng khi research từ khóa cho các SKU sản phẩm thuộc một hệ sản phẩm có nhiều biến thể cấu hình (CPU/GPU, RAM, ROM/SSD, màn hình, công nghệ kết nối...):

1. **Không máy móc lược bỏ từ khóa định danh:**
   - Không tự ý lược bỏ các từ như `wifi`, `inch`, `24`, `14` theo cảm tính. Quyết định giữ hay bỏ dựa trên dữ liệu tìm kiếm thực tế của người dùng trên Google.

2. **Tham chiếu Google Search Console (GSC) của thế hệ tiền nhiệm:**
   - Khi nghiên cứu sản phẩm mới (chưa ra mắt hoặc mới ra mắt nên Ahrefs chưa kịp ghi nhận volume/trả về 0 hoặc null):
     - Truy vấn GSC của dòng máy/sản phẩm kề trước nhất (ví dụ: lấy dữ liệu của iMac M4 khi làm iMac M6; iPad M4 khi làm iPad M5) để xem người dùng thực tế tìm kiếm bằng những cụm từ nào, cấu trúc ra sao và từ nào có Impression cao nhất.
     - Giữ lại các cụm từ có Impression cao và khớp intent với sản phẩm mới.
     - Quy ước gán Search Volume (VLS) là **5** cho các từ khóa này (để phân biệt với từ khóa bị loại hoàn toàn).

3. **Gom nhóm dòng con và xác định "Bản tiêu chuẩn" (Standard Variant):**
   - Gom các sản phẩm có chung một đặc tính bất kỳ vào một nhóm con (sub-group):
     - Ví dụ nhóm GPU: 10-core GPU vs 12-core GPU.
     - Ví dụ nhóm RAM: 16GB vs 24GB.
     - Ví dụ nhóm Màn hình: Màn hình Nano-texture vs Màn hình tiêu chuẩn.
   - **Bản tiêu chuẩn của nhóm:** Là SKU có **dung lượng/cấu hình thấp nhất (base model)** trong nhóm đó (thường là bản RAM thấp nhất hoặc SSD thấp nhất).
   - **Gán từ khóa đại diện:** Bản tiêu chuẩn được quyền "sở hữu" các từ khóa đại diện bao quát của cả nhóm (ví dụ: `imac m6 16gb`, `imac m6 10 core gpu`, `imac m6 nano`) vì search intent của người dùng khi tìm kiếm nhóm này là muốn xem **giá khởi điểm / thấp nhất** của cấu hình đó.
   - Các bản nâng cấp (Upgrade SKU - dung lượng cao hơn như 512GB, 1TB) sẽ sở hữu các từ khóa chi tiết theo đúng dung lượng cấu hình cao của chúng.

4. **Quy tắc gán cờ `main` (Tick TRUE - Keyword chính):**
   - **Mỗi sản phẩm phải có ít nhất 1 keyword được tick TRUE.**
   - Điều kiện tick TRUE:
     - Viết đúng chính tả tiếng Việt / có dấu, hoặc đúng tên gọi/cách viết thông dụng của người dùng (ví dụ: `iphone 18 promax` viết liền, `iphone gập`).
     - Đúng thứ tự/quy ước đặt tên thương hiệu (không đảo ngữ lung tung).
     - Search Volume $\ge 10$.
     - Đối với sản phẩm mới chưa có Volume Ahrefs: Chọn 1 keyword đại diện có Impression cao nhất từ GSC của thế hệ trước và thật sự phù hợp nhất với sản phẩm/intent.

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
