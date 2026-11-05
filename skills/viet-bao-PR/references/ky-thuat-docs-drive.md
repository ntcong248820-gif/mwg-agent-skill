# Kỹ thuật: Drive, Google Docs, ảnh, sheet

Dùng `gws` theo account trong CLAUDE.md (dự án MWG dùng account mặc định). Script dùng lại
được lưu ở `~/viet-bao-pr/tools/` (`dump.py`, `review.py`, `rep.py`, `metatag.py`,
`retitle.py`, `sety.py`...). `review.py` dùng chung mọi dự án; các script khác có thể còn
hard-code sheet của dự án iPhone 18, đọc code trước khi dùng cho dự án khác.

## 1. Cú pháp gws hay nhầm

Field của request body (`name`, `mimeType`, `parents`, permission `type`/`role`) phải nằm
trong `--json`. Để nhầm vào `--params` thì gws tạo file "Untitled" với mimeType
`application/octet-stream` mà không báo lỗi. `--params` chỉ dùng cho query parameter thật
(`fileId`, `documentId`, `spreadsheetId`, `range`...).

## 2. Tạo cấu trúc Drive (làm sớm)

Trong thư mục "Báo PR" của dự án:
1. Tạo thư mục bài, đặt tên theo đề tài (không ghi tên báo). Cuối quy trình sẽ đổi theo H1.
2. Trong đó tạo 1 Google Doc (cùng tên) và 1 thư mục `Ảnh`.
3. Set quyền cho Doc và thư mục Ảnh:
   `gws drive permissions create --params '{"fileId":"<id>"}' --json '{"type":"anyone","role":"writer"}'`
4. Ghi link Doc và link thư mục Ảnh vào cột URL Doc / URL Hình của đúng dòng.

## 3. Chèn nội dung vào Doc

**Doc trống:**
1. Viết toàn bộ text ra file tạm (tên có số dòng), mỗi đoạn/heading 1 dòng.
2. Dùng Python tính offset: `insertText` bắt đầu tại index 1, cộng dồn `len(line) + 1`.
3. Tính offset bắt đầu/kết thúc của từng anchor, chọn đúng 1 vị trí, cẩn thận chuỗi con.
4. Một `batchUpdate` gồm: `insertText` tại `{"location":{"index":1}}`;
   `updateParagraphStyle` cho title (`HEADING_1`) và H2 (`HEADING_2`), H3 nếu có;
   `updateTextStyle` `{"link":{"url":"..."}}`, `fields: "link"` cho từng anchor.

**Doc đã có nội dung (viết lại, enrich, đổi đề tài):**
1. `gws docs documents get` lấy nội dung và `endIndex` của đoạn cuối.
2. Trong cùng 1 `batchUpdate`: `deleteContentRange` từ 1 đến `endIndex - 1`, `insertText`
   tại 1, rồi các request style/link.

**Sửa nhỏ giữa bài:** dùng `replaceAllText` (khớp theo nội dung), hoặc fetch lại Doc rồi mới
tính index. Không dùng index cũ sau khi Doc đã đổi độ dài. Sửa nhiều chỗ thì làm tuần tự:
sửa 1 chỗ → fetch lại → tính index chỗ tiếp theo.

## 4. Ảnh: upload, chèn Doc, metadata

Cách chọn ảnh, số lượng, vị trí, caption, thumb, ảnh nguồn ngoài: xem `anh-bai-viet.md`.
Phần dưới chỉ là thao tác kỹ thuật.

**Upload và đặt tên:**
- `gws drive +upload <file> --parent <AnhFolderId>`, set quyền
  `gws drive permissions create --params '{"fileId":"<id>"}' --json '{"type":"anyone","role":"writer"}'`.
- Đổi tên bằng `gws drive files update --params '{"fileId":"<id>"}' --json '{"name":"..."}'`:
  - Ảnh trong bài: `<slug>-<stt>-thegioididong.<đuôi thật>` (stt theo thứ tự xuất hiện trong bài).
  - Ảnh thumb: `<slug>-thumb-thegioididong.<đuôi thật>`.
  - `<slug>` = title H1 bỏ dấu, chữ thường, nối bằng `-`. Đổi title thì đổi tên ảnh theo.
- Đuôi file phải đúng định dạng thật (kiểm bằng PIL, không tin đuôi tên file gốc).

**Chèn vào Doc (`insertInlineImage`):**
- URI `https://drive.google.com/uc?export=view&id=<fileId>`, width **460 PT**, không set height.
- Đặt ngay sau đoạn văn liên quan, dòng tiếp theo là caption. Không đặt ngay dưới heading.
- Nhiều ảnh: xử lý theo index giảm dần trong cùng 1 `batchUpdate`; mỗi ảnh gồm
  `insertInlineImage` rồi `insertText` `"\n"` + caption ngay sau.
- Caption không chứa link. Ảnh thumb không chèn vào Doc, chỉ để trong thư mục Ảnh.

**Metadata ảnh:** sau khi đã có H1 và caption, bắn metadata cho mọi ảnh trong thư mục Ảnh
(cả thumb) theo Site: Artist/Author, Copyright = "Copyright © <site>", Title = H1,
Description = caption. TGDĐ: Thegioididong.com; TopZone: Topzone.vn; ĐMX: Dienmayxanh.com.
Dùng `python3 ~/viet-bao-pr/tools/metatag.py <row>` (máy không có exiftool), kết quả phải
OK hết. Script ghi cả EXIF lẫn XMP và xoá XMP/IPTC cũ (metadata gốc của ảnh nguồn ngoài hoặc
của kho). Kiểm lại bằng `metatag.py <row> --check`. Áp cho cả ảnh nguồn ngoài (xem
`anh-bai-viet.md` mục 5). Thay ảnh, đổi H1 hoặc caption thì chạy lại.

## 5. Verify độc lập sau khi chèn

Fetch lại Doc (`gws docs documents get`) rồi kiểm:
- Số từ: join toàn bộ `textRun.content` rồi `.split()`, so với giới hạn của báo.
- Title là `HEADING_1`, ≤ 80 ký tự. Sapo 2 câu, ≤ 150 ký tự, không link.
- Từng anchor: đúng 1 lần, đúng URL, đúng cụm chữ, link đầu ở đoạn thân bài 1–3 (hoặc đúng
  yêu cầu riêng của báo), rải theo đoạn liên quan.
- Không link ở heading, caption.
- Dòng cuối bài là `Nguồn: <Site>` đúng Site (TGDĐ: Thế Giới Di Động; TopZone: TopZone; ĐMX:
  Điện Máy Xanh), chỉ 1 dòng.
- Đoạn thương hiệu đúng bản user đã xác nhận cho Site và giai đoạn.
- Ảnh: đủ số lượng, width 460, sau đoạn văn liên quan, rải đều, caption có "Ảnh: <nguồn>", tối đa 2 ảnh nguồn ngoài; có file thumb nếu báo yêu cầu.
- Không còn dấu hiệu văn phong AI.

Chạy `python3 ~/viet-bao-pr/tools/review.py <row> [--tab <tab>] [--sheet <id>]` để kiểm tự động
(dùng chung mọi dự án, map cột theo tên header), rồi làm các mục CHECK TAY nó in ra.

## 6. Cập nhật sheet và Drive khi xong

1. Cột Tên đề tài = title H1 mới, xoá dòng "Link tham khảo" trong ô.
2. Đổi tên Doc và thư mục bài theo H1 (thư mục bài = `parents[0]` của Doc):
   `gws drive files get --params '{"fileId":"<docId>","fields":"parents"}'`, rồi
   `gws drive files update --params '{"fileId":"<id>"}' --json '{"name":"<H1>"}'`.
3. Bắn metadata ảnh.
4. Cột Trạng thái = `Chờ duyệt` (trừ khi user dặn không set). Trước khi sửa 1 dòng mà user
   có thể đang duyệt song song, đọc lại ô trạng thái; đã là `Xong` thì không đụng vào.
