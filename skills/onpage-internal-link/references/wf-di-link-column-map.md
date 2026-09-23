# WF đi link — Column Map chi tiết 22 cột A–V

## Spreadsheets được hỗ trợ

Cấp ID qua biến môi trường (không hardcode ID nào trong skill này):

1. **Game App / Hỏi Đáp (thegioididong.com):**
   - **ID:** `$SHEET_GAME_APP_ID`
   - **Tab chính:** `WF đi link`
   - **Tab hướng dẫn:** `HDSD WF đi link`

2. **Kinh Nghiệm Hay / Vào Bếp (dienmayxanh.com):**
   - **ID:** `$SHEET_KINH_NGHIEM_HAY_ID`
   - **Tab chính:** `WF đi link`

## Cột A–G: SEO nhập

| Col | Tên | Giá trị mẫu | Ghi chú |
| --- | --- | --- | --- |
| A | Ngày add | `19/08/2026` | Ngày SEO thêm dòng |
| B | Nhân sự SEO | `Tên - Mã NV` | Tên và mã nhân viên |
| C | Loại hành động | `Đoạn văn` | **FORMULA** — tự tính từ Cột J |
| D | URL bài tin | `https://www.thegioididong.com/game-app/...` | URL live bài viết |
| E | Anchor text | `màn hình 24 inch` | Từ/cụm cần bao trong thẻ `<a>` |
| F | Link cần chèn | `https://www.thegioididong.com/man-hinh-may-tinh-24-inch` | href đích |
| G | Link cần xóa | _(rỗng)_ | Link cần xóa (nếu có) |

## Cột H–K: Nội dung (SKILL điền H+J)

| Col | Tên | Giá trị | Ghi chú |
| --- | --- | --- | --- |
| **H** | **Nội dung cũ** | `Plain text đoạn văn gốc trên web` | **SKILL điền** — không encode HTML |
| I | Nội dung mới | _(rỗng)_ | Content điền khi mode "Thêm đoạn văn mới" |
| **J** | **Hành động chèn** | `Chèn link vào text có sẵn` | **SKILL điền** — giá trị cố định |
| K | Chèn sau text | _(rỗng)_ | Anchor vị trí sau đoạn văn nào |

## Cột L–M: Workflow Content

| Col | Tên | Giá trị | Ghi chú |
| --- | --- | --- | --- |
| L | Deadline | `25/08/2026` | Content điền |
| M | Trạng thái | `Pending` / `Done` | Content điền |

## Cột N–O: Formula tự sinh

| Col | Tên | Formula logic | Ghi chú |
| --- | --- | --- | --- |
| N | CMS | `=MAP(D2:D; INDEX(ROW(D2:D)); LAMBDA(...))` | Link CMS từ URL bài tin |
| **O** | **HTML** | `=MAP(C2:C; E2:E; F2:F; G2:G; H2:H; I2:I; J2:J; INDEX("H"&ROW(...)); LAMBDA(...))` | **Tự sinh HTML `<p><a>...</a></p>`** |

### Công thức Cột O output khi J = "Chèn link vào text có sẵn":

```html
<p>...text trước...<a title="{E}" href="{F}" target="_blank" rel="noopener">{anchor_match}</a>...text sau...</p>
```

- Formula tìm first occurrence của anchor text (Cột E) trong plain text (Cột H) và bọc `<a>`.
- Match case-insensitive: `màn hình 2k` trong H nhưng bài viết viết `2K` → Formula bọc đúng `màn hình 2K`.

## Cột P: Trigger n8n

| Col | Tên | Giá trị | Ghi chú |
| --- | --- | --- | --- |
| P | Content cho bắt đầu | `Ready` | Khi = "Ready", webhook n8n trigger tự động chèn vào CMS |

**KHÔNG ghi Cột P trong skill này** — Content team quyết định khi nào Ready.

## Cột Q–V: n8n Automated

| Col | Tên | Ghi chú |
| --- | --- | --- |
| Q | Content check | n8n điền |
| R | QC Status | n8n điền |
| S | QC Note | n8n điền |
| T | Backup Doc Link | n8n điền |
| U | Final Verify | n8n điền |
| V | Article Context | n8n điền |
