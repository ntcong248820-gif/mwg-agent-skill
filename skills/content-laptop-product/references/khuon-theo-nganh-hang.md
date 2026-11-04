# Khuôn bài theo ngành hàng

Rút từ 52 bài live (30/10/2026). Mọi bài dùng `<h3>` cho mục; **không `<h2>`** (h2 là của tab trang). Mở bài là một đoạn nằm trong `<h3>` đầu tiên, chứa self-link (anchor = tên đầy đủ + mã, `target="_blank" rel="noopener" title="<Tên> tại thegioididong.com"`).

## Laptop (700–1.600 từ, 6–9 h3; mẫu live trung vị ~980 từ, chưa tính box/bảng/FAQ)

| # | Mục (h3) | Nội dung bắt buộc | Nguồn PIM (`rawValues`) |
|---|---|---|---|
| – | Box Đặc điểm nổi bật (div, trước h3 đầu) | 4–5 điểm khác biệt có số, trùng `key_features` | như các mục dưới |
| 0 | Mở bài (h3 chứa đoạn) | tên máy, kiểu máy, đối tượng, 1 điểm khác dòng | `product_name`, `product_type_filter_master` |
| 1 | Hiệu năng | CPU (nhân, xung), GPU, NPU nếu có, RAM (loại, bus, tối đa), SSD | `cpu_*`, `graphics_card_*`, `ram_*`, `hard_drive_*`, `npu_*` |
| 2 | Màn hình | kích thước, độ phân giải, tấm nền, tần số quét, độ phủ màu, cảm ứng | `screen_size_*`, `resolution_*`, `panel_*`, `scanning_frequency_*`, `color_coverage_*` |
| 3 | Âm thanh, webcam | công nghệ âm thanh, webcam, bàn phím | `audio_technology_*`, `webcam_*`, `keyboard_backlight_*` |
| 4 | Thiết kế, độ bền | vật liệu, trọng lượng, kích thước, tản nhiệt, bảo mật | `material_*`, `machine_weight_*`, `long/wide/thick_*`, `heat_sink_*` |
| 5 | Kết nối, pin | cổng (theo bảng đã chốt), không dây, pin, sạc, hệ điều hành | `communication_port_*`, `connect_*`, `battery_information_*`, `operating_system_*` |
| 6 | Chọn bản nào / So sánh (có điều kiện) | bảng so sánh với bản/model tương đương trong line-up | PIM các model |
| – | Đoạn chốt `<p>` | tên máy, đối tượng, link dòng/hãng/ngành | – |
| 7 | Câu hỏi thường gặp về {SP} (h3 cuối, câu hỏi h4) | 2–4 câu qua phép thử giá trị | nguồn đã kiểm |

Máy AI/gaming/OLED: thêm ý NPU/TOPS, GPU rời, tấm nền OLED vào mục 1–2, vẫn giữ 5 mục. Box, bảng so sánh và FAQ áp cho mọi ngành phần cứng (máy tính để bàn, màn hình, máy in) theo cùng quy tắc.

## Máy tính để bàn (550–1.000 từ, 4–7 h3)
All-in-one: hiệu năng → màn hình → âm thanh/webcam → thiết kế, kết nối. PC mini/tower: hiệu năng → lưu trữ/nâng cấp → thiết kế → kết nối. Luôn chia mục (mẫu có 2/8 bài không chia, đừng bắt chước).

## Màn hình máy tính (550–900 từ, 4–6 h3)
Thiết kế → hiển thị (kích thước, độ phân giải, tấm nền) → màu sắc (độ phủ, HDR) → chuyển động (tần số quét, thời gian phản hồi) → kết nối, tính năng bảo vệ mắt. Link phụ được: bàn phím/chuột/giá treo cùng hãng.

## Máy in (600–1.300 từ, 5–10 h3)
Kiểu dáng → hiệu suất (tốc độ, độ phân giải in) → công suất/hộp mực → giấy (khổ, khay, in 2 mặt) → kết nối (USB, Wi-Fi, ứng dụng). Link mực in cùng model, bài hướng dẫn cài driver nếu có. Bài cũ giọng "mình" của reviewer là di sản, bài mới viết ngôi thứ ba.

## Phần mềm (900–1.500 từ, 6–9 h3, có h2 theo bài gốc)
Khuôn khác phần cứng: giới thiệu gói → ứng dụng trong gói → quyền lợi/thời hạn/số thiết bị → so sánh các gói → **Thông tin sử dụng và lưu ý khi mua** → **Câu hỏi thường gặp** → mua tại Thế Giới Di Động. Đọc bài đang chạy của chính gói đó trước khi viết, vì điều kiện bản quyền khác nhau từng gói.

## Mục bổ sung (đề xuất, cần nguồn)
Nâng cấp và lưu ý trước khi mua, Hiệu năng AI/game theo hãng, Bảo hành và mua tại TGDĐ (chỉ khi owner xác nhận chính sách). Box, bảng so sánh, FAQ đã thành chuẩn (`box-bang-so-sanh-faq.md`). Chi tiết lý do ở report mẫu chung mục 5.
