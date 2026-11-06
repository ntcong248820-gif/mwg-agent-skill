# Column map — tab plan `onpage` + tab `WF đi link` (22 cột A–V)

## Spreadsheets

| Vai trò | Tên | ID mặc định (env ghi đè) |
| --- | --- | --- |
| Plan order | Plan SEO - Auto, tab `onpage` | `$SHEET_PLAN_ONPAGE_ID` |
| WF Hỏi đáp / Game App / TekZone | PHỐI HỢP SEO - CONTENT GAME APP Chạy AI, tab `WF đi link`, tab `HDSD WF đi link` | `$SHEET_GAME_APP_ID` |
| WF Kinh nghiệm hay / Vào bếp ĐMX | tab `WF đi link` | không có mặc định (`SHEET_KINH_NGHIEM_HAY_ID`) |

## Tab plan `onpage` (A–G)

| Col | Tên | Ai ghi | Giá trị |
| --- | --- | --- | --- |
| A | Keyword cần chèn | SEO | 1 hoặc nhiều keyword, mỗi cái 1 dòng trong ô. **Khoá** cùng C |
| B | URL cần chèn | SEO | URL đích, ghép cặp theo thứ tự dòng với A |
| C | URL bài tin | SEO | URL bài live. **Khoá** cùng A |
| D | Phân loại | Skill | `Có URL` / `Chưa có URL` |
| E | Nội dung chèn | Skill | Nội dung mới (I) hoặc câu gốc (H) của dòng WF đã ghi |
| F | Status | SEO → Skill | `Run` → `Doing` → `Done` / `Đã đúng guideline`; lỗi crawl trả về `Run` |
| G | Ngày order | Skill | Ngày xử lý, theo định dạng các dòng trên |

Khoá dòng = (A nguyên văn, C). Không dùng số dòng vì xoá/sort giữa chừng sẽ ghi nhầm dòng.

## Tab WF đi link — A–G: thông tin dòng

| Col | Tên header | Giá trị | Ghi chú |
| --- | --- | --- | --- |
| A | Ngày add | date serial | Không ghi chuỗi `dd/mm/yyyy` |
| B | Nhân sự SEO | `Tên - Mã NV` | Theo chuỗi user đang dùng; không rõ thì để trống |
| C | Loại hành động | `Đoạn văn` / `Infobox` | **Dữ liệu**, không phải công thức. Quyết định nhánh của cột O |
| D | URL bài tin | URL live | |
| E | Anchor text cần chèn | 1 hoặc nhiều anchor, ngăn `\n` | Viết hoa đúng quy ước hãng |
| F | Link cần chèn | 1 hoặc nhiều URL, ngăn `\n`, cùng thứ tự E | |
| G | Link cần xóa | thường trống | |

## H–K: nội dung (skill điền theo nhánh)

| Nhánh | H Nội dung cũ | I Nội dung mới | J Hành động chèn | K Chèn sau text này |
| --- | --- | --- | --- | --- |
| fixAnchor | câu chứa link cũ (hoặc anchor cũ) | câu đã thay anchor (hoặc anchor mới) | `Thay đoạn cũ` | trống |
| insertText | câu gốc nguyên văn (plain text) | trống | `Chèn link vào text có sẵn` | trống |
| newContent | trống | câu mới | `Thêm vào dưới đoạn văn` | đoạn neo nguyên văn |

Plain text, không encode HTML, không giữ markup.

## L–M: Content

| Col | Tên | Ghi chú |
| --- | --- | --- |
| L | Deadline kì vọng | Content điền |
| M | Trạng thái | Content điền |

## N–O: công thức neo ở hàng 2 (dạng `MAP`) — không ghi

Đọc `valueRenderOption=FORMULA` tại ô data trả rỗng là bình thường.

**N — CMS:**
- `thegioididong.com/hoi-dap/…{id}` → `https://cms.thegioididong.com/v2/Faq/NewsEdit?newsId={id}`
- `thegioididong.com/game-app/…{id}` → `https://cms.thegioididong.com/v2/GameApp/EditNews?newID={id}`
- Còn lại (TekZone, ĐMX) → `Không hỗ trợ URL này` (bình thường, ghi chú trong report).

**O — HTML** (`IFS` theo C và J):

| Điều kiện | Kết quả |
| --- | --- |
| C = `Đoạn văn` và J = `Chèn link vào text có sẵn` | `GENERATE_FINAL_HTML_LINKS(E; F; G; …; H)` — bọc anchor vào **H** |
| C = `Đoạn văn` (J khác) | `GENERATE_FINAL_HTML_LINKS(E; F; G; …; I)` — bọc anchor vào **I** |
| C = `Infobox` | `GENERATE_BOX_HTML(E; F; I)` — dựng box mới từ **I** |
| C trống | trống |

Hệ quả:
- insertText phải C = `Đoạn văn` (C = `Infobox` sẽ dựng box từ I đang trống).
- fixAnchor/newContent: anchor phải xuất hiện trong I, nếu không O không có `<a>`.
- Bọc anchor không phân biệt hoa thường, lấy lần xuất hiện đầu.

## P: trigger n8n

| Col | Tên | Giá trị |
| --- | --- | --- |
| P | Content cho bắt đầu | Skill ghi `Hold` khi nạp. Chỉ đổi `Ready` khi user duyệt — `Ready` kích webhook n8n chèn CMS |

## Q–V: n8n tự điền — không ghi

Q Content vào check · R QC Status · S QC Note · T Backup Doc Link · U Final Verify · V Article Context.
