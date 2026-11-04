# So sánh phương án thay nền + bắn chữ (đo 30/10/2026 trên ảnh MSI N16)

| Phương án | Kết quả thử | Giữ nguyên SP | Chữ | Chọn |
|---|---|---|---|---|
| **Pillow + numpy + scipy**: flood-fill nền trắng từ viền, màu-sang-alpha vành 2 điểm, ghép lên gradient, vẽ chữ | chạy được trên ảnh 2500×2500; viền sạch khi phóng 4× (không viền trắng); 2 demo JPG 1020×570 | chứng minh được từng điểm (lõi alpha=1 giữ nguyên RGB, kiểm độc lập sau khi dựng) | Arial macOS, tiếng Việt đủ dấu, canh dòng thủ công | **Có** |
| HTML/CSS + Chrome headless (cắt nền bằng cách trên, dựng bố cục bằng CSS) | Chrome cài ở `/Applications/Google Chrome.app`, chưa chạy thử | trình duyệt tự co ảnh, không kiểm soát thuật toán, khó chứng minh từng điểm | đẹp hơn, linh hoạt | Không: thêm tiến trình, mất khả năng chứng minh |
| ImageMagick | `magick` có (Homebrew) nhưng **thiếu Freetype và Ghostscript**: `montage`/`annotate` báo "delegate library support not built-in (Freetype)" | được cho co/ghép | **không vẽ được chữ** | Không (chỉ co/ghép) |
| rembg / mô hình tách nền ML | không chạy | mặt nạ do mô hình đoán, có thể cắt mất cổng nhỏ, bút mảnh, lỗ thông gió; không tái lập được | – | Không |
| Ghép bằng multiply không tách nền | lý thuyết | đổi màu SP vì nhân với màu nền | – | Không |
| AI sinh/sửa ảnh (`image-ai-generate`) | không dùng | bịa chi tiết cổng, ổ cắm | – | Cấm cho ảnh SP |

## Số đo demo (016VN, ảnh gallery 2500×2500)

| Ảnh | Nguồn | Ra | SP trong ảnh ra | Kiểm độc lập |
|---|---|---|---|---|
| `016vn-man-hinh-oled-demo.jpg` | gallery-1 (mặt trước) | 1020×570, 58,6 KB | co 0,2252, tỷ lệ khung 1,5843 → 1,5859 | 0,056% điểm lõi lệch quá 2/255, PSNR 39 dB, ĐẠT |
| `016vn-xoay-gap-360-demo.jpg` | gallery-3 (gập phẳng + bút) | 1020×570, 55,4 KB | co 0,2255, tỷ lệ 1,2234 → 1,2239 | 0% lệch quá 2/255, PSNR 40,8 dB, ĐẠT |

Kiểm chứng âm: dán làm mờ một mảng 100×50 điểm lên bản PNG thì verify báo 2,15% điểm lệch, KHÔNG ĐẠT.
