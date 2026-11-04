# Viết report để người không làm SEO đọc hiểu

Owner phản ánh 05/10/2026: report của skill đọc khó vì toàn mã (`L1`, `L2`, `E`, `Δ`,
`đ`, `pp`, "ex-Apple", "movers"...). Người nhận forward — trưởng ngành hàng, leader —
không có file S1 để tra. Report này phải đọc được **không cần tra cứu**.

## Rule

1. **Không dùng mã kỳ đo trong thân report.** `L1`–`L4`, `E`, `P0/P1/P2`, "tầng", "tier",
   "mode standard/full" chỉ được nằm ở mục `## Phụ lục kỹ thuật` cuối report. Thân report
   viết tên kỳ + ngày cụ thể. Tên chuẩn lấy từ S1 mục 1, cột "Tên viết trong report".
2. **Câu đầu tiên trả lời "ngành đang tăng hay giảm, thật hay không".** Không mở đầu
   bằng số liệu thô hay phương pháp.
3. **Mỗi con số có đơn vị và chiều.** "lượt nhấp giảm 14,6% (132.118 → 112.890)", không
   "clicks −14,6%" trần. Thứ hạng luôn kèm "tốt hơn/xấu đi" (S1 mục 3.1).
4. **Mỗi bảng có 1 câu "đọc bảng này thế nào"** ngay trên bảng, và 1 câu kết luận ngay dưới.
5. **Không dán slug/URL dài trong văn xuôi.** Gọi bằng tên: "trang Laptop Dell", "máy
   Acer Nitro V15". URL đầy đủ để ở bảng hoặc file CSV.
6. **Nhãn kết luận S1 giữ nguyên chữ in hoa** (`GIẢM THẬT`...) nhưng luôn kèm 1 câu giải
   thích bằng lời thường ngay sau.
7. **Không ghi tên file/tool/worker trong thân report** (`build-tier-tables.py`,
   "Codex", "crew run"). Để ở phụ lục.

## Bảng thay từ

| Đừng viết | Viết |
| --- | --- |
| L1 / L1 · 7d | Tuần này so với tuần trước (23/09–29/09 so với 16/09–22/09) |
| L2 / L2 · 28d | 4 tuần gần nhất so với 4 tuần trước đó |
| L3 / YoY | 4 tuần gần nhất so với cùng kỳ năm ngoái |
| L4 | 3 tháng gần nhất so với cùng kỳ năm ngoái |
| `E` = 2026-09-29 | Số liệu tính tới hết ngày 29/09 (ngày đủ dữ liệu gần nhất) |
| clicks | lượt nhấp (lượt vào từ Google) |
| impressions / impr | lượt hiển thị trên Google |
| CTR | tỷ lệ nhấp (lượt nhấp / lượt hiển thị) |
| position / vị trí TB | thứ hạng trung bình — **số nhỏ hơn là tốt hơn** |
| Δ, delta | thay đổi / chênh lệch |
| +0,21đ, pp | tăng 0,21 điểm phần trăm |
| ex-Apple | đã loại sản phẩm Apple |
| keyword movers / page movers | từ khoá / trang tăng giảm mạnh nhất |
| CTR opportunity | từ khoá có nhiều lượt hiển thị nhưng ít người nhấp |
| rank opportunity | từ khoá đang ở hạng 4–15, đẩy lên được |
| truy vấn thương hiệu | người tìm có gõ tên TGDĐ ("thegioididong laptop") |
| sub-ngành | nhóm hàng (laptop, máy tính để bàn, màn hình, máy in, phần mềm) |
| NKD / ĐKD | ngừng kinh doanh / đang kinh doanh |
| sitelink, cannibalization | giải thích 1 câu, hoặc bỏ nếu không cần cho quyết định |

Thuật ngữ đầu tiên trong report (lượt nhấp, lượt hiển thị, tỷ lệ nhấp, thứ hạng trung
bình) giải thích 1 lần trong ngoặc, các lần sau dùng trơn.

## Khung report

Theo `mwg-seo-analytics/templates/gsc-category-review-report.md`. Thứ tự mục:

1. **Tóm tắt** — 3–5 gạch đầu dòng, câu đầu là kết luận.
2. **Nếu bỏ sản phẩm ngừng kinh doanh** — xem `business-status-split.md`.
3. **Tin tốt gửi ngành hàng** + **Cần lưu ý** — gọn để forward thẳng.
4. **Số liệu chính** — bảng theo từng kỳ so sánh, tên kỳ bằng lời.
5. **Nhóm hàng / nhóm trang** — ai kéo tăng, ai kéo giảm.
6. **Từ khoá / trang tăng giảm mạnh nhất** — có cột trạng thái kinh doanh cho trang sản phẩm.
7. **Cơ hội** — mỗi dòng: từ khoá, vì sao là cơ hội (lời thường), việc cần làm.
8. **Đề xuất** — đánh số, mỗi dòng 1 việc, ai làm nếu biết.
9. **Phụ lục kỹ thuật** — mã kỳ L1–L4 kèm ngày, `E` và cách chọn, filter (gồm filter loại
   Apple), scope file + hash, đường dẫn raw/processed, worker/tool đã chạy.
10. **Câu hỏi còn mở**.

Kiểm trước khi giao: grep thân report (trước `## Phụ lục kỹ thuật`) không còn
`\bL[1-4]\b`, `\bE\b =`, `Δ`, `ex-Apple`, `movers`. Còn thì sửa.

```bash
awk '/^## Phụ lục kỹ thuật/{exit} {print}' report.md | grep -n -E '\bL[1-4]\b|Δ|ex-Apple|movers|\bpp\b'
```
