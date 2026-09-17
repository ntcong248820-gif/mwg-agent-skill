# Workflow bắt buộc

Làm tuần tự. Mỗi bước chỉ mở đúng reference của bước đó để khỏi ngốn context.

## Bước 1 — Nhận brief

Chốt đủ 5 thứ trước khi viết một chữ nào:

| Thứ | Thiếu thì làm gì |
| --- | --- |
| Chủ đề / thông điệp bài PR | Hỏi user |
| Thư mục Google Drive cha | **Hỏi user mỗi bài.** Không có mặc định, không dùng lại thư mục bài trước |
| Link cần chèn + muốn chèn ở đoạn nào | Không có thì bài không có link, không tự bịa |
| Nguồn ảnh bắt buộc | Không có thì mặc định lấy ảnh tự do trên mạng |
| Số chữ và báo đích | Không có thì mặc định 800-1000 chữ |

Gom câu hỏi lại hỏi một lượt. Đừng hỏi nhỏ giọt từng câu.

Nếu user đang nhờ **sửa bài đã có**, đọc bài cũ trước, giữ phần đúng, rồi vào
thẳng bước cần sửa.

## Bước 2 — Research

Đọc `research-rules.md`. Lấy dữ kiện thật trước khi dựng sườn, vì góc bài phụ
thuộc vào chuyện có gì thật để kể.

## Bước 3 — Title và sườn bài

Đọc `title-rules.md`. Ra 3-5 phương án title, chọn 1, rồi dựng sườn:

```text
title  →  sapo  →  [h2 + 2-4 đoạn] × 3-4  →  đoạn chốt
                     ↑ ảnh xen vào giữa các cụm, tối thiểu 2 ảnh
```

Sườn dài 3-4 section H2 là vừa cho 800-1000 chữ. Nhiều hơn thì mỗi phần bị cụt.

## Bước 4 — Viết nội dung

Đọc `writing-rules.md` và `formatting-rules.md`.

Viết thẳng vào `article.json` theo schema ở `drive-delivery.md`. Đừng viết bản
Markdown rồi chuyển đổi sau — bước chuyển đổi là chỗ link và caption hay rơi.

## Bước 5 — Chèn link

Đọc `link-rules.md`. Chỉ chèn link user đã yêu cầu, và chỉ vào block `p`.

## Bước 6 — Chuẩn bị ảnh

Đọc `image-rules.md`. Chọn ảnh, viết caption, điền `source_url` vào các block
`image`. Chưa upload ở bước này.

## Bước 7 — Lint

```bash
python3 scripts/check-article.py /đường/dẫn/article.json
```

Sửa cho hết `ERROR`. `WARN` thì cân nhắc, không bắt buộc sửa.

Lint trước gate verify, vì gate tốn thời gian của worker khác — đừng bắt nó đọc
một bài còn sai độ dài hay lạc chỗ link.

## Bước 8 — Gate verify

Đọc `verify-gate.md`. Bắt buộc. Gate trả `FAIL` thì sửa rồi chạy lại, không
được bỏ qua.

## Bước 9 — Giao hàng lên Drive

Đọc `drive-delivery.md`. Thứ tự cố định:

1. Tạo thư mục con trong thư mục cha user đưa.
2. `prepare-images.py` — resize, upload, mở quyền public.
3. `build-pr-doc.py` — dựng Doc và mở link-share (Doc edit được, thư mục xem được).
4. Đọc lại Doc **và kiểm lại quyền**, không tin output của script.

## Bước 10 — Checklist cuối

Đọc `final-checklist.md`, rà từng mục, tự sửa. Rồi đưa user link thư mục Drive,
link Doc, số chữ thật, và kết quả gate verify.
