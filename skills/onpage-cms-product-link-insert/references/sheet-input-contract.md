# Hợp đồng input từ sheet plan

Skill nhận một danh sách dòng. Sheet chỉ là nguồn phổ biến nhất của danh sách đó,
không phải một cấu trúc cố định.

## Trường bắt buộc mỗi dòng

| Trường runner | Nguồn điển hình | Ghi chú |
| --- | --- | --- |
| `row` | số dòng sheet | Để tick lại cột Tình trạng |
| `pid` | cột Product ID | Lấy từ URL CMS nếu sheet không có |
| `site` | cột `Site` | `1` TGDĐ, `2` ĐMX. Tab không có cột này thì mặc định `1` |
| `oldText` | cột **Nội dung cũ** | Phải là **nguyên văn đoạn trên bài đang sống** |
| `sentence` | cột **Nội dung mới** | Plain text, đã chứa anchor |
| `links[]` | cột **Từ khóa chèn** + **Link chèn** | Ghép cặp anchor ↔ href |

## Column map lệch giữa các tab của cùng một file

Đây là bẫy thật, đã trả giá. Tab nào không có cột `Site` thì mọi cột sau đó
**lệch -1**:

| Trường | Tab có cột Site | Tab không có cột Site |
| --- | --- | --- |
| Nội dung cũ | H | **G** |
| Nội dung mới | I | **H** |
| Từ khóa chèn | J | **I** |
| Link chèn | K | **J** |
| Tình trạng | L | **K** |

**Đọc header của từng tab, đừng bê map của tab trước sang.**

## Lọc scope

Chỉ lấy dòng có cột Tình trạng = `FALSE` (chưa làm). Dòng `TRUE` đã xong ở đợt
trước hoặc do người khác làm tay.

Kể cả vậy vẫn sẽ gặp dòng `FALSE` mà bài **đã có link** — người khác vừa làm tay
chưa tick. Runner tự bỏ qua an toàn (khớp bằng đúng → 0 match), nhưng sau đó
**phải verify riêng nhóm này**: đủ anchor và độ dài text khớp cột Nội dung mới.

## Cột "Nội dung cũ" là điểm chết của chất lượng dữ liệu

Đoạn phải được **lấy từ bài đang sống**, không phải soạn lại hay lấy từ bản nháp.
Đã gặp 8 dòng mà đoạn ở cột này không tồn tại trong bài (similarity 0,10-0,21) —
runner từ chối ghi, và đó là hành vi đúng.

Khi bàn giao sheet cho bên soạn, nói rõ ràng buộc này.

## Lỗi dữ liệu đã gặp, nên quét trước khi chạy

Có ai đó find/replace `Ultra` → `Duo` khi sinh cột Nội dung mới:

- `Fusion Ultra Wide` → `Fusion Duo Wide` (2 dòng)
- `Apple Watch Ultra 2` → `Apple Watch Duo 2` (1 dòng)

Vì skill chỉ **append** nên lỗi này không vào CMS. Nhưng sheet vẫn sai. Quét cả
cột Nội dung mới cho các cặp từ dễ bị replace nhầm trước khi chạy, và báo lại
bên soạn sheet.

## Rule map anchor → link đích

Skill **không tự quyết** anchor nào trỏ đi đâu. Map phải do user chốt và nằm sẵn
trong sheet, vì map này không suy ra được từ tên gọi.

Ví dụ từ đợt iPhone 18, hai anchor bất đối xứng rất dễ làm ngược:

| Anchor | Đích | Bẫy |
| --- | --- | --- |
| `iPhone 18` | trang **series** | nghe như tên máy |
| `iPhone Duo` | trang **sản phẩm** | nghe như tên dòng, và trang filter cùng tên có thật |

Trước khi chạy, kiểm lại: mỗi câu chèn chứa anchor **đúng 1 lần**, và anchor ngắn
không nằm trong anchor dài hơn.
