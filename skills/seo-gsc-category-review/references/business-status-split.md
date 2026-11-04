# Tách sản phẩm ngừng kinh doanh khỏi traffic ngành

Trả lời 3 câu cho mỗi kỳ so sánh:

1. Trang sản phẩm **ngừng kinh doanh** chiếm bao nhiêu % clicks của ngành?
2. Phần giảm (hoặc tăng) của ngành có bao nhiêu % nằm ở nhóm đó?
3. Bỏ nhóm đó ra thì ngành **thực sự** tăng hay giảm?

## Vì sao bắt buộc

Sản phẩm ngừng bán thì trang của nó vẫn xếp hạng thêm một thời gian rồi rơi dần. Số
clicks mất ở đó là vòng đời sản phẩm, không phải sức khoẻ SEO. Gộp chung thì ngành
trông tệ hơn thực tế, và action bị đẩy vào chỗ không cứu được.

Đo thật vòng 02/10/2026 (4 tuần, ngành Laptop ex-Apple): trang sản phẩm chiếm ~34%
clicks; trong 12 URL sản phẩm mất clicks nhiều nhất, **8 URL đã ngừng kinh doanh**
(Acer Nitro V15 `anv15-41-r1jy`, Lenovo LOQ 15ARP9, IdeaPad Slim 3/5...). Report vòng đó
ghi "Acer Nitro V15 rớt hạng" vào mục cần lưu ý — thật ra là máy đã ngừng bán.

Chạy đủ trên vòng đó (kiểm 05/10, 2.425 URL sản phẩm: 1.973 ngừng KD, 450 đang KD):

| Kỳ so sánh | Toàn ngành | Bỏ SP ngừng KD | SP ngừng KD gánh | Riêng trang danh mục |
| --- | ---: | ---: | ---: | ---: |
| Tuần này so với tuần trước | −9,1% | −6,9% | 38,7% phần giảm | −8,4% |
| 4 tuần so với 4 tuần trước | −14,6% | −10,0% | 47,4% phần giảm | −11,9% |
| 4 tuần so với cùng kỳ năm ngoái | −33,7% | (−21,8%, đẹp giả) | — | −32,4% |

Bài học: sản phẩm ngừng KD giải thích gần **một nửa** phần giảm tháng, nhưng trang danh
mục **vẫn giảm thật** −11,9%. Tách nhóm này ra là để thấy đúng cỡ của vấn đề, không phải
để xoá vấn đề.

## Cách chạy — 2 bước, sau khi fetch xong và trước khi viết report

```bash
SCOPE=mwg-seo-analytics/scopes/nh-laptop-ex-apple.json
RAW=$TASK/data/raw/$RUN

# 1. Kiểm trạng thái từng URL sản phẩm có clicks (HTTP tĩnh, ~1 giây/URL, 8 luồng)
python3 mwg-seo-analytics/tools/gsc/classify-product-business-status.py \
  --scope $SCOPE --raw-dir $RAW --workers 8
#    -> $RAW/business-status.csv

# 2. Tách số theo trạng thái (không gọi mạng)
python3 mwg-seo-analytics/tools/gsc/build-business-status-split.py \
  --scope $SCOPE --raw-dir $RAW --out-dir $TASK/data/processed --prefix $PREFIX
#    -> {prefix}-business-status-split.csv, {prefix}-product-pages-by-status.csv
```

### Kho trạng thái — không crawl lại cái đã biết

Mọi lần kiểm đều gộp vào **một kho dùng chung**: `mwg-seo-analytics/cache/product-business-status.csv`.
Lần sau tool chỉ crawl URL **chưa có trong kho** hoặc **quá hạn dùng**:

| Trạng thái trong kho | Dùng lại trong | Lý do |
| --- | --- | --- |
| Đang KD | 7 ngày | máy đang bán có thể ngừng bất cứ lúc nào — đúng nhóm làm rơi traffic, phải bắt kịp |
| Ngừng KD | 90 ngày | hiếm khi bán lại |
| Đổi URL | 30 ngày | |
| Chưa rõ | luôn kiểm lại | |

Đo 05/10/2026: lần đầu 2.589 URL mất ~19 phút; chạy lại cùng dữ liệu **0,16 giây, 0 URL
crawl**. Vòng review hằng tuần chỉ phải kiểm lại ~450 URL đang KD + URL mới (vài phút).
Lần đầu hoặc sau `--refresh` thì vẫn chạy nền (`run_in_background`).

- Lỗi mạng khi kiểm lại **không** đè trạng thái đã biết — tool dùng kết quả cũ và ghi rõ
  ngày đó ở `ly_do`.
- Kho ghi `trang_thai_truoc` + `doi_luc` khi trạng thái đổi; tool in ra số máy vừa đổi
  (ví dụ `DANG_KD→NGUNG_KD 12`).
- Kho là cache, **không commit** (gitignore): mất thì crawl lại ~20 phút. Khác `snapshots/`,
  nơi tháng GSC mất là mất hẳn.
- File `{raw}/business-status.csv` của mỗi lượt vẫn được ghi — đó là bằng chứng lượt đó
  đã dùng trạng thái nào, kèm `kiem_luc` từng dòng.
- `--refresh` kiểm lại tất cả; `--no-store` chạy tách biệt, không đọc/ghi kho; đổi hạn
  dùng bằng `--max-age-dang-kd` / `--max-age-ngung-kd` / `--max-age-chuyen-huong`.

Scope phải có khoá `product_url_pattern` (path `/{ngành}/{slug}` = trang sản phẩm). Khoá
này không nằm trong `filters` nên không đổi `filters_hash` của snapshot.

## Nhóm trang

| Nhóm | Nghĩa |
| --- | --- |
| Trang danh mục, hãng, bộ lọc | không phải trang sản phẩm (`/laptop-dell`, `/laptop?g=...`) |
| SP đang kinh doanh | `pageStatus 'Kinh doanh'` hoặc `item_web_status 'Còn hàng'` |
| SP ngừng kinh doanh | `pageStatus 'Không kinh doanh'`, `item_web_status 'Ngừng/Không kinh doanh'`, hoặc HTTP 404/410 |
| SP đã đổi URL | HTTP 3xx — **không** tính là ngừng KD: traffic thường chuyển sang URL mới, URL mới vẫn nằm trong data |
| SP chưa rõ trạng thái | lỗi mạng hoặc không có tín hiệu — báo ra, không đoán |

Trạng thái đo **vào ngày chạy**, áp cho cả 2 kỳ của một phép so. Đúng chủ đích: sản
phẩm vừa ngừng bán trong tháng chính là trang có clicks rơi.

## Đọc kết quả — 3 lăng kính

| Dòng trong `-business-status-split.csv` | Dùng cho |
| --- | --- |
| `TOÀN NGÀNH` | số như cũ, để đối chiếu với các vòng trước |
| `TOÀN NGÀNH, BỎ SP NGỪNG KINH DOANH` | **traffic thực tế** cho phép so tuần và 4 tuần |
| `Trang danh mục, hãng, bộ lọc` | sức khoẻ trang đích KPI; **lăng kính duy nhất cho phép so cùng kỳ năm ngoái** |

**Bẫy so cùng kỳ năm ngoái:** sản phẩm thay đời trong vòng một năm, nên phần lớn sản
phẩm năm ngoái hôm nay đã ngừng KD. Bỏ chúng ra thì gần như xoá sạch traffic sản phẩm
của năm ngoái, kết quả đẹp giả. Tool ghi chú cảnh báo ở các dòng đó. Phép so năm ngoái
đọc dòng **trang danh mục, hãng, bộ lọc**.

Nhãn kết luận (TĂNG THẬT / GIẢM THẬT / HỒI NGẮN HẠN...) theo S1 mục 3 — ghép **2 lần**:
một lần trên toàn ngành, một lần trên dòng bỏ SP ngừng KD. Hai nhãn khác nhau là phát
hiện chính của report, phải nằm ở câu đầu tiên.

Cột `gop_vao_chenh_lech_pct` = phần chênh của nhóm / phần chênh của toàn ngành. Ngành
giảm 1.000 clicks mà nhóm ngừng KD giảm 700 thì nhóm đó gánh 70% phần giảm. Có thể >100%
khi các nhóm khác tăng bù.

## Viết vào report

Mục riêng **"Nếu bỏ sản phẩm ngừng kinh doanh"**, đặt ngay sau tóm tắt:

```markdown
| | 4 tuần trước (05/08–01/09) | 4 tuần gần nhất (02/09–29/09) | Thay đổi |
| --- | ---: | ---: | ---: |
| Toàn ngành | 132.118 | 112.890 | −14,6% |
| Sản phẩm ngừng kinh doanh (tỷ trọng) | 31.279 (23,7%) | 22.165 (19,6%) | −9.114 lượt |
| **Bỏ sản phẩm ngừng kinh doanh** | 100.839 | 90.725 | **−10,0%** |
| Riêng trang danh mục, hãng, bộ lọc | 84.661 | 74.602 | −11,9% |
```

(Số thật vòng 02/10/2026, ngành Laptop đã loại Apple.) Kèm 1–2 câu: nhóm ngừng KD gánh
bao nhiêu % phần giảm, và 3–5 sản phẩm ngừng KD mất clicks nhiều nhất (tên máy, không
dán slug) lấy từ `-product-pages-by-status.csv`.

Hệ quả cho các mục khác:

- **Tin tốt / cần lưu ý gửi ngành hàng:** không nêu sản phẩm ngừng KD như "rớt hạng". Nếu
  cần nhắc thì ghi "đã ngừng bán, mất lượt vào là bình thường".
- **Đề xuất:** không đề xuất tối ưu trang sản phẩm ngừng KD. Nếu nó còn nhiều lượt hiển
  thị thì đề xuất trỏ người đọc sang máy thay thế (internal link/redirect) — hỏi ngành
  hàng trước.
- **Bảng URL tăng giảm mạnh:** thêm cột trạng thái kinh doanh cho dòng trang sản phẩm.
- **Máy vừa ngừng bán từ lần kiểm trước** (dòng có `trang_thai_truoc = DANG_KD`,
  `trang_thai = NGUNG_KD` trong file của lượt): nêu tên ở mục "cần lưu ý" — ngành hàng
  thường muốn biết máy nào vừa rút để đẩy máy thay thế. `doi_luc` là ngày **phát hiện**,
  không phải ngày ngừng bán thật.

## Bẫy đã gặp

| Bẫy | Hệ quả | Cách tool xử lý |
| --- | --- | --- |
| Không gửi cookie → web trả ngẫu nhiên core mới, HTML core mới **không có** `pageStatus`/`item_web_status` | 2/3 lượt ra "mơ hồ" (đo 05/10/2026, cùng 1 URL) | mặc định `--cookie webmoi_v2=1` (core cũ), thử lại khi thiếu tín hiệu |
| JSON-LD `availability` luôn `InStock` kể cả máy đã ngừng bán | đếm sai thành đang KD | không đọc JSON-LD |
| `item_web_status` rỗng nhưng `pageStatus 'Kinh doanh'` (ví dụ Gigabyte A16 05/10) | dễ bị xếp "chưa rõ" | `pageStatus` quyết định |
| Trang so sánh `/laptop/{máy-a}-vs-{máy-b}` khớp dạng `/{ngành}/{slug}` nhưng không có tín hiệu trạng thái | 160/2.589 URL ra "chưa rõ" (vòng 02/10), chỉ 0,02% clicks | `product_url_pattern` loại `-vs-`, trang so sánh rơi vào nhóm không phải sản phẩm |
| URL redirect bị đọc theo trang đích (urllib tự theo redirect) | trang sản phẩm cũ đọc thành trang danh mục | tắt tự theo redirect, 3xx → SP đã đổi URL |

`SP chưa rõ trạng thái` > 2% clicks → tool cảnh báo. Chạy lại bước 1 trước khi kết luận.
