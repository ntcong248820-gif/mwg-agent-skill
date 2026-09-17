# Prompt Archetypes

7 loại ảnh, mỗi loại là 1 cột template trong sheet `Cấu hình ảnh AI`. Chọn đúng
archetype quyết định layout ảnh — chọn sai thì ảnh ra generic "sản phẩm trên nền".

## Bảng nhận diện

| Archetype | Cột sheet | Nhận diện từ section | Reference |
| --- | --- | --- | --- |
| `showcase` | Prompt - Ảnh Sản Phẩm | Heading là **tên 1 sản phẩm cụ thể** (khối H4 trong bài top SP), hoặc giới thiệu 1 danh mục | `required` |
| `comparison` | Prompt - Ảnh So Sánh | "so sánh", "A hay B", "nên chọn ... hay ...", bảng đối chiếu 2 lựa chọn | `preferred` |
| `feature_highlight` | Prompt - Ảnh Tính Năng | Nói về 1 tính năng/công nghệ/lợi ích cụ thể: pin, màn hình, tản nhiệt, chip | `preferred` |
| `instructional` | Prompt - Ảnh Hướng Dẫn | "cách ...", "hướng dẫn", "các bước", quy trình có thứ tự | `not_needed` |
| `lineup_overview` | Prompt - Ảnh Tổng Quan Dòng | Tổng quan 1 dòng/series/hãng, nhiều model cùng họ | `preferred` (2-4 ref) |
| `buying_guide` | Prompt - Ảnh Chọn Mua | "nên mua loại nào", tiêu chí chọn, phân khúc theo nhu cầu/ngân sách | `not_needed` |
| `lifestyle_context` | Prompt - Ảnh Ngữ Cảnh | Bối cảnh sử dụng: sinh viên giảng đường, dân văn phòng, đi công tác | `preferred` |

## Ví dụ định tuyến thật

Bài "TOP 10 laptop pin trâu":

| Section | Archetype | Lý do |
| --- | --- | --- |
| "Tiêu chí chọn laptop pin trâu" | `buying_guide` | Đang nói tiêu chí, chưa nói SP cụ thể |
| "1. MacBook Air 13 M5" | `showcase` | Heading là 1 SKU cụ thể |
| "Bảng so sánh dung lượng pin" | — **SKIP** | Section chứa `<table>` |
| "Pin 99.9Wh nghĩa là gì" | `feature_highlight` | Giải thích 1 thông số |
| "Laptop pin trâu cho dân đi công tác" | `lifestyle_context` | Bối cảnh sử dụng |
| "Chính sách bảo hành" | — **SKIP** | Policy |

## Placeholder trong template

Template dùng 4 placeholder. Thay hết trước khi gửi API — sót placeholder thì
model in nguyên chữ `[TÊN_SẢN_PHẨM]` vào ảnh.

| Placeholder | Điền bằng |
| --- | --- |
| `[TÊN_SẢN_PHẨM]` | Tên đầy đủ SP hoặc chủ đề section |
| `[MÔ_TẢ_TÍNH_NĂNG]` | 2-4 tính năng/lợi ích cụ thể rút từ nội dung section |
| `[MÔ_TẢ_ĐỐI_THỦ]` | Chỉ dùng cho `comparison` — vế đối chiếu còn lại |
| `[STYLE_CHUNG]` | Nội dung cột `Style Hướng Dẫn Chung` của config |

n8n chấp nhận cả biến thể có dấu cách (`[MÔ TẢ TÍNH NĂNG]`). Thay cả 2 dạng cho chắc.

## Ghép prompt cuối

```
{template đã thay placeholder}

{styleGuide}

{promptGuard nếu config có, không thì bỏ qua}
```

Nếu có `--preserve-product`, script `generate_image.py` tự nối thêm ràng buộc
fidelity vào cuối — **không tự viết lại ràng buộc đó trong prompt**, để một nguồn
duy nhất, tránh mâu thuẫn.

## Rule nội dung bắt buộc

Theo `Style Hướng Dẫn Chung` của profile `bright-minimal` (đã sửa 2026-09-17 sau
phản hồi ảnh quá nhiều chữ — xem `SKILL.md` mục "Quy tắc Mật độ Chữ"). **Ảnh
được phép có chữ** — vấn đề không phải "có chữ" mà là dựng thành slide nhiều
lớp. Ngân sách và ví dụ đúng/sai đầy đủ nằm ở `SKILL.md`, tóm tắt ở đây:

- **Ngôn ngữ chữ trong ảnh (BẮT BUỘC): PHẢI LÀ TIẾNG VIỆT.** Được phép dùng các thuật ngữ/từ mượn tiếng Anh thông dụng (như *Arm màn hình, OLED, Gaming, Setup, RAM, SSD, RTX, Type-C...*), nhưng **tuyệt đối KHÔNG để full tiếng Anh** (cấm các câu/tiêu đề thuần tiếng Anh).
- **Ngân sách**: 1 headline ngắn (≤6 từ, phản ánh đúng ý chính section) + tối đa
  1 subhead ngắn (≤10 từ) + tối đa 3-4 nhãn icon ngắn (2-4 từ) **hoặc** tối đa
  3 mini-scene mỗi scene 1 caption ngắn — chọn 1 kiểu, không xếp chồng cả hai.
  Mọi chữ phải suy ra được từ nội dung thật của `[MÔ_TẢ_TÍNH_NĂNG]`, **cấm bịa
  số liệu/phần trăm/benchmark** không có trong bài.
- **CẤM tuyệt đối**: panel đánh số (01/02/03) kèm câu mô tả, lồng 2 lớp chữ
  trong cùng 1 panel (tiêu đề panel + icon-caption con bên trong), banner tóm
  tắt/checklist lặp lại thông điệp ở đáy ảnh, nút CTA dạng chữ ("KHÁM PHÁ NGAY"...).
- Khi section có 2-3 nhánh nội dung tự nhiên (VD: phân khúc giá, dòng sản phẩm,
  3 tình huống mua) thì chia tối đa 3 vùng/mini-scene, mỗi vùng đúng 1 caption
  ngắn, không thêm mô tả nhiều dòng hay icon-caption con bên trong từng vùng.
- Chữ trong ảnh: trắng/off-white là chính, **chỉ đúng 1 từ khoá/số/đơn vị**
  dùng vàng TGDĐ `#FFD400`. Không để toàn bộ chữ màu vàng.
- Mỗi ảnh phải diễn giải tính năng thật thành hình cụ thể, không mood trừu tượng.
- Không logo hãng giả, không giá/khuyến mãi, không microtext dày đặc.
