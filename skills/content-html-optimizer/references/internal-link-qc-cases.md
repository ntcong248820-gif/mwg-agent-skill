# QC Internal Link — bảng phân loại trường hợp

Dùng cho `scripts/check_internal_links.py` (lớp luật) và làm rubric cho lớp
review bằng model.

## Nguyên tắc gốc

> Link đúng khi trang đích nói về **đúng thực thể mà cụm anchor đang chỉ trong
> câu đó**. Sai khi đích chỉ là thứ **chứa** nó (dòng/hãng/ngành hàng), thứ
> **gần** nó (phụ kiện cùng tên), hoặc thứ **trùng tên khác nghĩa**.

Phép thử một câu: *"Trang đích này nói về đúng cái mà cụm từ đang chỉ, hay chỉ
nói về một cái chứa nó / gần nó?"* — nếu là vế sau thì gỡ.

Quyết định nằm ở **loại đích**, không ở hình dạng anchor. Cùng một anchor có số
theo sau: `[tần số quét]144Hz` → bài "tần số quét là gì" là ĐÚNG, còn
`[Acer Aspire]7` → category `/laptop-acer-aspire` là SAI.

## Nhóm A — anchor không trỏ đúng thực thể

| Case | Mô tả | Ví dụ | Kết luận | Ai bắt |
| --- | --- | --- | --- | --- |
| A1 | Anchor là tiền tố, mã đời nằm ngay sau, đích là trang hãng/dòng | `[Acer Aspire]7 ở trên` → `/laptop-acer-aspire` | SAI | luật |
| A2 | Mã đời cách anchor vài từ hoặc đứng trước | `So với [Lenovo LOQ] 15IAX9E...` | SAI | model |
| A3 | Anchor là dòng, câu nói về **cả dòng** | `Dòng [Acer Nitro] theo đuổi thiết kế...` | ĐÚNG | model |
| A4 | Anchor cắt ngang tên SP đang nêu nguyên vẹn | `[MSI Modern]15 F1MG-1264VN dùng RAM rời` | SAI | luật (A1) |
| A5 | Anchor là tên SP, đích là PDP đúng SP đó | — | ĐÚNG | — |

Ranh giới A2 ↔ A3 là chỗ luật chịu thua: cùng anchor `Lenovo IdeaPad`, câu
"Dòng Lenovo IdeaPad là..." thì đúng, "So với Lenovo IdeaPad Slim 5 thì..." thì sai.

## Nhóm B — đích sai loại so với ý định câu

| Case | Mô tả | Ví dụ | Kết luận | Ai bắt |
| --- | --- | --- | --- | --- |
| B1 | Bộ phận có sẵn của máy → category phụ kiện rời | `[pin]70Wh` → `/pin`; `Jack [tai nghe]3.5mm` → `/tai-nghe`; `[Màn hình]` của laptop → `/man-hinh-may-tinh` | SAI | luật (B4) |
| B2 | Cổng/thông số → category mua hàng | `[USB 3.2]` → `/usb?g=usb-32` | SAI | luật (B4) |
| B3 | Trùng tên khác nghĩa | `[cổng USB]` → `usb-charge-la-gi`; `công tắc khoá [camera]` → `/camera-giam-sat` | SAI | model (khi đích là hỏi đáp) |
| B4 | Lệch ngành hàng bài | bài máy in → `/laptop`; bài laptop → `/may-choi-game-cam-tay` | SAI | luật |
| B5 | Khái niệm → bài giải thích **chính khái niệm đó** | `[tần số quét]144Hz` → `tan-so-quet-la-gi` | ĐÚNG | — |
| B6 | Anchor ngành hàng, câu là ý định mua | `Sắm ngay một chiếc [máy in] giá rẻ` → `/may-in` | ĐÚNG | — |

B5 là lý do **không được** lấy "có số ngay sau anchor" làm dấu hiệu chặn: trong
12 bài đo 07/09/2026 có 22 link dính dấu hiệu đó, 13 trong số đó đúng.

## Nhóm C — vị trí chèn

| Case | Mô tả | Kết luận | Ai bắt |
| --- | --- | --- | --- |
| C1 | Trong khối `[info]` thông số, đích là **category mua hàng** | SAI | luật |
| C2 | Trong khối `[info]` thông số, đích là **bài giải thích thông số** | ĐÚNG | — |
| C3 | Trong `<table>` | SAI | optimizer đã chặn |
| C4 | Trong `<h3>`-`<h6>` | SAI | optimizer đã chặn |
| C5 | Trong `alt`/`title` ảnh | SAI | optimizer đã chặn |
| C6 | Trong box "Xem thêm" | SAI | optimizer đã chặn |

Trang chính sách (`chinh-sach-*`, `khuyen-mai`, `tra-gop`) tính là trung tính,
không phải category mua hàng — không gắn cờ C1.

## Nhóm D — quan hệ bài ↔ đích

| Case | Mô tả | Kết luận | Ai bắt |
| --- | --- | --- | --- |
| D1 | Tự link về chính bài | SAI | luật + `--self-url` |
| D2 | Hai link cùng một URL | SAI | luật |
| D3 | Đích đã nằm trong box "Xem thêm" | SAI | luật |
| D4 | Link về SP đã có `[product ID]` / `[sosanh]` trong bài | Cần xét | model |

Ngoại lệ D2: **2 nút CTA giống hệt nhau** đặt đầu và cuối bài (cùng URL tracking)
là thiết kế cố ý, giữ nguyên.

## Nhóm E — anchor vô giá trị

| Case | Mô tả | Ví dụ | Kết luận | Ai bắt |
| --- | --- | --- | --- | --- |
| E1 | Anchor từ chung chung, câu không nói về việc mua | `Chia sẻ bộ nhớ với [máy tính]` → `/may-tinh-de-ban` | SAI | model |
| E2 | Anchor là hãng đứng trơ | `phiên bản kế nhiệm của [HP]107w` | SAI | luật (A1) |

## Vì sao cần cả 2 lớp

`optimize_content.py` đã có `CONTEXT_EXCLUSIONS` — blocklist từ cấm theo cặp
(keyword, url). Đo 07/09/2026: bảng đó **đã có dòng riêng cho `pin` và
`camera`** mà cả hai vẫn lọt, vì ngữ cảnh thật ("công tắc khoá camera", "máy
mỏng nhẹ, pin...") không nằm trong danh sách từ. Tập ngữ cảnh sai là tập mở,
không đóng được bằng danh sách từ.

Lớp luật đóng phần **có dấu hiệu cấu trúc** (vị trí, ngành hàng đích, token mã
đời liền sau, trùng URL). Lớp model đóng phần **phải đọc câu mới biết** (A2/A3,
B3, D4, E1).

## Đo lần đầu (07/09/2026, 12 bài, 322 link)

| Case | Số link gắn cờ |
| --- | --- |
| A1 | 9 |
| B4 | 35 |
| C1 | 9 |
| D2 | 1 |
| **Tổng link bị gắn cờ** | **47 (14%)** |

Đối chiếu với danh sách rà tay: A1 bắt đủ 9/9, C1 đủ 9/9. Dương tính giả đếm
được 3 (`balo laptop` → `/tui-chong-soc-balo-laptop`, `phần mềm Windows` →
`/phan-mem-windows`, 1 ca `máy tính bảng`) — đều là link phụ kiện/phần mềm hợp
lệ cho bài laptop.

Luật **không** bắt được: B3 khi đích là bài hỏi đáp (`cổng USB` →
`usb-charge-la-gi` lọt vì đích là `/hoi-dap/`), A2/A3, E1.
