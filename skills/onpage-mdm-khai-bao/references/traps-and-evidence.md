# Bẫy đã đo thật và việc chưa đo

Đo bằng ghi thật trên hệ production ngày 05–06/10/2026. Mọi bản ghi test đã khôi phục khớp từng byte.

## Ghi

| Bẫy | Đo được | Skill xử lý |
| --- | --- | --- |
| Khoá phiên bản | Cả 5 kiểu ghi (Danh mục, Hãng, giá trị Filter, model PIM, lá biến thể) gửi rowVersion cũ → `errorReason:"row_version"`, "Phiên bản dữ liệu đã thay đổi [n]", `errorCode:"mvvn4m"`. Đổi nội dung thì +1; lưu không đổi gì thì không tăng | exit 3, không ép |
| MDM ghi đè cả bản ghi | Hãng SingPC: gửi bản thiếu key `seo_keyword` → key **biến mất** | `assertNoDroppedKeys`, payload dựng từ getinfor vừa đọc |
| PIM gộp theo key | `model/update` bỏ key → key cũ **vẫn còn**; `[]`, `null`, `data:null` đều không xoá được key; "xoá" = ghi `""` | không ghi PIM |
| Lưu y nguyên byte | Không trim, không đổi entity (`&amp;` giữ nguyên, khác CMS). Comment HTML, nháy, ký tự có dấu giữ nguyên. UI MDM tự `trim()` khi bấm Lưu, API thì không | so readback tuyệt đối |
| Biến thể SP | Ghi 1 lá Màu **không lan** sang lá khác; người ta đang sửa tay từng lá (cách 19s) hoặc tool ghi cả 4 lá trong 120 ms | SP chỉ đọc |

## Lên web

| Bẫy | Đo được |
| --- | --- |
| Độ trễ MDM → core mới | Filter: node đầu ra bản mới sau ~4 phút, đủ 4/4 mẫu sau ~15 phút, lan dần từng node (cùng lúc node mới, node cũ) |
| `?clearcache=1` | 12 lượt liên tiếp không đổi gì trên core mới → vô tác dụng với dữ liệu MDM |
| Core cũ | Không hiện thay đổi MDM (title core cũ lấy từ CMS) |
| Ép cookie `webmoi_v2=2` | Vẫn có lúc rơi node core cũ (header `x-version: Mwg-*`) → chỉ tính mẫu không có `x-version` |
| Marker vô hình | Comment HTML và ký tự zero-width trong infobox **không bao giờ hiện**: core mới parse lại infobox (chèn mục lục). Muốn đánh dấu để đo: dùng chữ thường/2 dấu cách trong title |
| SP: PIM → web | Title SP sửa trên PIM (cả 4 lá 512GB, 09:42 06/10) → 55+ phút cả 2 core vẫn bản cũ; CMS `MetaTitle` vẫn bản cũ = web. Description CMS = PIM sau lần ghi 120 ms → nghi đồng bộ CMS → PIM |

## Tra cứu

- Mã PIM ≠ ID CMS; ô tìm PIM không khớp ID CMS hay slug (thử searchType 1–5) → lấy `modelCode` từ HTML core mới.
- Chỉ 17/143 danh mục có `seo_title` trong MDM; trang thiếu thì web ra title mẫu tự sinh
  (vd `may-tinh-de-ban-hp`: "Máy tính để bàn Hp chính hãng, giá rẻ - 10/2026").
- Tab ẩn danh: mất khi Chrome khởi động lại → exit 4, nhờ owner đăng nhập lại.
- `list_pages` của chrome-devtools-mcp đôi khi treo 60s → CLI khởi động lại MCP, thử lại 1 lần.

## Upload ảnh

0,8s; CDN 200 ngay; byte giữ nguyên (không nén lại); tên gốc + hậu tố `HHmmss`; không chặn trùng
tên; không có API xoá. Ô bài viết SP trên PIM không nhận `.webp` (MDM nhận).

## Chưa đo — lần đầu làm phải có người đứng xem

1. Ghi `seo_article` / `brand_cate_article` / `filter_inforbox` **dài có ảnh mới** rồi xem web hiển
   thị (mới đo ghi chữ + comment HTML).
2. Độ trễ lên web của **Danh mục** và **Hãng** (mới đo Filter).
3. Bỏ key với `datatobject`/`datarelation` (giả định giống `dataobject`; skill chặn rơi key nên không ảnh hưởng).
4. Token hết hạn sau bao lâu.
5. Trang Hãng+Filter: field `*_brand_filter` dùng chung cho mọi hãng — chưa có cách khai riêng 1 hãng.
6. Chiều đồng bộ CMS ↔ PIM của SP và lịch chạy — hỏi IT trước khi mở ghi SP.
