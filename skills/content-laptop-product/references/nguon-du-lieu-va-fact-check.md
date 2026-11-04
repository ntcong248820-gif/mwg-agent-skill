# Nguồn dữ liệu và fact-check

Chỉ đọc. Ưu tiên theo thứ tự: PIM → bảng thông số hãng (PDF/trang hãng VN) → fact sheet của task → báo công nghệ (chỉ làm bối cảnh, không làm số liệu bán hàng).

| Cần | Lấy ở đâu | Cách |
|---|---|---|
| Model, lá màu, độ dài bài hiện có | PIM | `mdm-cli.mjs pim-find --url /<ngành>/<slug>` (skill `onpage-mdm-khai-bao`) |
| Thông số chuẩn hoá | PIM `rawValues` của model | `mdm-cli.mjs pim-find` ra mã model; `product-write` không `--live` in plan; trong task MSI đã có `data/raw/title-meta/pim-model-*.json` làm mẫu |
| Thông số hãng | PDF/trang hãng VN | `pdftotext -layout`; ghi ngày PDF ("2026-10-08") vào báo cáo |
| Bài/thông số đang hiển thị | trang live | `scripts/fetch-live-article.py`, `curl` JSON-LD |
| Chip/công nghệ mới | fact sheet trong task (`XN`/`CCB`/`MT`) | chỉ viết dòng `XN` |
| Ảnh | PIM `gallery`, `image` (URL CDN `cdnv2.tgdd.vn/pim/...`) | xem `lam-hinh.md` |

## Quy tắc đối chiếu

1. Mỗi thông số đưa vào bài có ít nhất 1 nguồn trong `facts-<sp>.json` (`must`).
2. PIM ≠ trang web ≠ bảng hãng: **mâu thuẫn (MT)**. Không chọn giùm. Viết câu không có con số đó và ghi MT vào danh sách câu hỏi cho IT/PIM. Ví dụ đã gặp (MSI N16, 30/10/2026): web ghi 1 USB-C, PIM 016VN ghi 2 USB-C, bảng MSI VN ghi 2 USB-C; PIM ghi thẻ Micro SD, MSI VN ghi SD (XC/HC).
3. Thông số của bản anh em nằm trong `must_not` (trừ mục so sánh `allow_must_not_in`), để lint bắt chép nhầm.
4. Số do hãng công bố (TOPS, fps, giờ pin, độ sáng, tốc độ in): đưa vào `hedge_numbers`; câu chứa số phải có "theo hãng/theo NVIDIA/theo thông số công bố".
5. Không có nguồn thì để `CCB`, không viết. Không suy từ SP khác cùng hãng.
6. Giá, quà, trả góp, bảo hành TGDĐ: ngoài phạm vi bài, trừ khi owner đã chốt chính sách.
