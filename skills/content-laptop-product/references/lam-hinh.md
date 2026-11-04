# Làm hình Content SP (ảnh thật, xử lý xác định)

Quy tắc cứng: **không AI sinh/sửa ảnh SP** (không GPT Image, Gemini, Flux, inpainting). Mọi điểm ảnh của SP lấy từ ảnh gallery thật; chỉ được co đều (không phóng to), cắt khung và ghép lên nền. Nền, bóng, chữ, thẻ vẽ ngoài vùng SP. Phương án đã so và lý do chọn: `phuong-an-xu-ly-anh.md`.

## Chuẩn ảnh trong bài SP (đo 89 ảnh trên 52 bài live, 30/10/2026)

| Mục | Chuẩn dùng | Bằng chứng |
|---|---|---|
| Kích thước | **1020×570** (16:9) | ảnh bài mới của MacBook Neo/Air M5, HP Smart Tank, HP LaserJet đều đúng 1020×570; chuẩn đời cũ 780×433 |
| Định dạng | JPG (WebP có ở 1 SP Asus, không dùng) | 85/89 ảnh JPG |
| Dung lượng | 20–250 KB, mục tiêu ≤ 150 KB | dải đo 19–245 KB |
| Tên file | ASCII kebab-case `<slug-sp>-bai-viet-<n>.jpg` (CDN gắn thêm dãy số khi upload) | `macbook-neo-13-inch-a18-pro-8gb-256gb-bai-viet-8-<ticks>.jpg` |
| alt = title | một câu mô tả có tên model, hoặc "Tên SP (mã) - Mục" | bài MacBook Neo; bài máy in/màn hình |
| Markup | `<p><a><img loading="lazy" alt title src data-original/></a></p>`, ảnh ở CDN `cdnv2.tgdd.vn` | bài MacBook Neo |
| Số ảnh | 3–5 ảnh/bài, mỗi mục chính 1 ảnh | report mẫu chung mục 4 |

Số đo chi tiết: `tasks/261028-plan-seo-msi-prestige-n16-flip-rtx-spark/work-items/261030-skill-content-sp-laptop/data/processed/sample-images-measured.json`.

## Chữ và màu: theo bộ hình AI infobox TGDĐ (owner góp ý 02/11/2026: chữ bản đầu "giống đánh chữ lên")

Rút từ hình AI đã làm ở `mwg-content-editor/content-workspaces/infobox-laptop-mong-nhe-thoi-trang`, `infobox-laptop-acer-predator`, `infobox-laptop-do-hoa-ky-thuat` (đo màu bằng pixel). Code ở `scripts/sp_image_typography.py`.

| Thành phần | Bộ AI làm gì | Skill làm |
|---|---|---|
| Font | sans hình học nét đậm | Avenir Next (có sẵn trong macOS): Bold cho tiêu đề và số, Demi Bold cho tiêu đề mục, Medium/Regular cho chữ thường. Bản Heavy **thiếu dấu tiếng Việt** (kiểm bằng fontTools), không dùng. Script báo VẤN ĐỀ khi chuỗi có ký tự font không có |
| Tiêu đề | VIẾT HOA, 1–2 dòng, từ khoá vàng | `--headline "Màn hình *Tandem OLED*\n16 inch"`: `*...*` là chữ vàng, `\n` là xuống dòng. Tự giảm cỡ để tối đa 2 dòng, không ngắt giữa cụm vàng |
| Màu nhấn | vàng TGDĐ, đo được #F9C80B (median 249,200,11 ở cả bộ sáng và tối) | `#F9C80B`. Chữ nhỏ trên nền sáng dùng vàng đậm `#CE9600` nét đậm để đọc được |
| Gạch dưới tiêu đề | nền sáng là vạch xám mảnh, nền tối là vạch vàng mờ dần | như bộ AI |
| Phụ đề | Medium, xám, từ khoá vàng đậm | `--sub "..."` |
| Mục đánh số | ô bo góc "01/02/03" + tiêu đề VIẾT HOA + mô tả xám | mỗi `--callout "Tiêu đề|Mô tả"` thành 1 mục. Ô số: nền sáng xanh đậm chữ trắng, nền tối vàng chữ xanh đậm |
| Con số lớn | số vàng rất to, đơn vị nhỏ ("16,9 mm") | layout `hero`: callout đầu "1000 TOPS" |
| Thanh đáy | viên thuốc xanh đậm #031023, cột ngăn vạch mảnh | layout `strip`; nền tối dùng thanh trắng mờ có viền |
| Nhãn | viên thuốc vàng chữ xanh đậm ("Ổ cứng SSD tốc độ cao") | `--tag "..."` |
| Logo | logo TGDĐ vàng góc phải trên | **không đóng logo** (owner chốt 02/11/2026: hình Content SP không cần logo) |
| Nền | bộ sáng trắng xám (mỏng nhẹ), bộ tối đen xanh (Predator, đồ hoạ) | `--palette studio` (sáng) và `--palette night` (tối, mặc định) |

Hình AI có ảnh ngữ cảnh (người dùng, bàn làm việc) và icon; skill không làm vì chỉ dùng ảnh thật của SP.

## Chống đơn điệu (owner góp ý 02/11/2026: bộ demo đầu chỉ 1 kiểu, hình na ná nhau)

Trong **một bài**, mỗi hình một bố cục (`check-image-set.py` báo ERROR khi trùng). Giữ 1–2 bảng màu cho đồng bộ (vd `night` + `studio`), đổi kiểu nền giữa các hình. Chọn bố cục theo nội dung mục:

| Mục bài | Bố cục gợi ý | Vì sao |
|---|---|---|
| Chip, hiệu năng, pin | `hero`: con số lớn (1000 TOPS, 99.9 Wh) | người lướt thấy ngay con số khác biệt |
| Màn hình | `left`/`right` + tiêu đề + mục đánh số | ảnh mặt trước, chữ cột bên |
| Xoay gập, nhiều chế độ, nhiều màu | `multi` 2–3 ảnh gallery khác góc + `--tag` | một hình kể được cả dải chế độ |
| Bàn phím, cổng, bản lề, chất liệu | `zoom` với vùng cắt chi tiết | thẻ phóng cắt nguyên trạng từ ảnh gốc, không tách nền |
| Cấu hình, kết nối | `strip` thanh 3–4 cột thông số | thay cho bảng chữ dài |
| Ảnh đầu bài (ít dùng) | `center` | |

Nền (`--bg`): `gradient`, `shapes` (vòng tròn, dải chéo mờ), `split` (2 mảng), `spotlight` (sáng ở SP), `light` (nền sáng chữ tối). Bảng màu (`--palette`): `night`, `studio`, `navy`, `teal`, `charcoal`, `purple`, `emerald`, `warm`, `light`, `auto` (lấy sắc của SP; SP xám/đen ra charcoal).

## Quy trình

1. **Ảnh gốc**: gallery của đúng model (PIM `rawValues.gallery`/`image`, URL `cdnv2.tgdd.vn/pim/...`). Lưu vào `tasks/{task}/data/raw/gallery/`, ghi size thật vào report. Không tải ảnh đối thủ, ảnh báo chí. Ảnh dùng chung nhiều biến thể thì không nói khác biệt giữa các biến thể bằng ảnh.
2. **Chọn ảnh theo mục**: SP nằm trọn trong khung (script báo khi bị cắt ở mép), nền trắng thuần, góc chụp khớp ý mục. Gallery thường chỉ 4–6 góc nên dùng lại một ảnh là chấp nhận được (WARN), miễn bố cục khác.
3. **Dựng** từng hình (`--article` bắt buộc khi chữ có số: số trên ảnh phải có trong bài đã lint; số hiệu năng hãng công bố vẫn ghi "theo thông số công bố"):
```bash
PY=$HOME/.claude/skills/.venv/bin/python3; S=.claude/skills/content-laptop-product/scripts
$PY $S/compose-sp-image.py --layout hero --src gallery-0.jpg --bg shapes --palette night --headline "Chip *NVIDIA RTX Spark*" \
  --callout "1000 TOPS|Sức mạnh AI *theo thông số công bố*" --callout "20 nhân CPU|GPU Blackwell RTX 6144 nhân" \
  --article DIR/bai-nhap.html --out DIR/<slug>-bai-viet-1.jpg --report DIR/<slug>-bai-viet-1.json
$PY $S/compose-sp-image.py --layout right --src gallery-1.jpg --bg light --palette studio --headline 'Màn hình *Tandem OLED*\n16 inch' \
  --sub "*4K UHD+* (3840 x 2400), 100% DCI-P3" --callout "Tần số quét 30-120 Hz|Tự đổi theo nội dung, tối đa 120 Hz" ...
$PY $S/compose-sp-image.py --layout zoom --src gallery-0.jpg --zoom 450,1540,1450,1930 --headline "Bàn phím *RGB 4 vùng*" ...
$PY $S/compose-sp-image.py --layout multi --src g1.jpg --src g4.jpg --src g3.jpg --headline "Laptop 2 trong 1 *linh hoạt*" --tag "Bản lề xoay gập 360 độ" --callout "Laptop|..." ...
$PY $S/compose-sp-image.py --layout strip --src g4.jpg --bg light --palette studio --headline 'Mỏng nhẹ vẫn\n*đủ kết nối*' --callout "USB4 Type-C|DisplayPort, PD 3.1" ...
```
   `--zoom` là toạ độ điểm ảnh trên ảnh gốc: cắt thử, nhìn rồi chỉnh. Tiêu đề ≤ 7 từ, callout ngắn (tiêu đề ≤ 5 từ), không giá, không "nhất". `strip` nhận tối đa 4 callout, các kiểu khác 3. JPG lưu 4:4:4 (không gộp màu, chữ vàng không nhoè), tự chọn chất lượng thấp nhất đạt PSNR ≥ 34 dB, ra ~80–95 KB.
4. **Kiểm độc lập** từng hình (bắt buộc, lưu kết quả cạnh ảnh): `$PY $S/verify-sp-fidelity.py --out X.jpg --report X.json`. Đạt khi mọi mảnh SP (kể cả thẻ zoom, từng ảnh trong multi) khớp ảnh gốc đã co (≤ 0,1% điểm lõi lệch quá 2/255), sha256 ảnh gốc khớp, tỷ lệ khung lệch < 0,5%, PSNR JPG so với PNG ≥ 33 dB.
5. **Kiểm cả bộ**: `$PY $S/check-image-set.py DIR/<slug>-bai-viet-*.json`. Sửa hết ERROR.
6. **Nhìn bằng mắt**: viền, cổng, logo, màn hình, chữ có đè SP không. Việc nhìn không thay được bước 4 và ngược lại.
7. **Chèn vào bài**: `alt`/`title` theo bảng chuẩn; `src` là URL CDN **sau khi upload** (mode `--publish`). Chưa upload thì giữ `<!-- ANH: <file> | <mục> -->` trong nháp.

## Giới hạn đã kiểm (02/11/2026)

- **Vùng trắng bị bao kín** (script liệt kê kèm `seed`): đa số là chỗ sáng trên màn hình, logo, viền kim loại, tức là chi tiết thật, nên giữ. Chỉ xoá khe nền thật (giữa chân đế, giữa bút và máy) bằng `--clear-at I:X,Y` lấy seed từ report, sau khi đã vẽ khung các vùng ra xem. Xoá theo kích thước đã thử và làm mất mảng sáng màn hình (verify KHÔNG ĐẠT 2,4% điểm), nên script không có tuỳ chọn đó.
- **Bóng phản chiếu sàn** dính liền SP (gallery-4 MSI N16): đừng tăng `--bg-tol`. Đã thử 70 và 100: bóng mất nhưng viền thật của máy bị đổi màu, verify KHÔNG ĐẠT. Dùng nền `light` để bóng hoà vào nền, hoặc chọn ảnh khác.
- Chỉ nhận ảnh nền trắng thuần. SP màu trắng/bạc sáng chưa thử: viền gần trắng dễ bị coi là nền, phải kiểm kỹ.
- Ảnh gốc nhỏ (vd `image-0` 600×600) không được phóng to, nên SP sẽ nhỏ hơn các ảnh 2500×2500 trong `multi`.
- Font Avenir Next chỉ có trên macOS. Máy khác script tự lùi về Arial (nếu có) và hình sẽ kém hơn; kiểm thiếu ký tự vẫn chạy.
