# Biên tập: áp đề xuất vào bài (các dòng ">>> Bổ sung điều chỉnh ... theo đề xuất")

Tab Thầy có bước tay sau mỗi vòng soát: đọc đề xuất, sửa bài, dán Word Counter, "Cập nhật
txt". Người biên tập làm việc đó. Đầu vào: bài phiên bản N, các file đề xuất của vòng, kết
quả lint phiên bản N, `brief.json`. Đầu ra: bài phiên bản N+1 và `bN-thay-doi.md`.

## Luật áp

1. Đọc mọi đề xuất trước khi sửa. Hai đề xuất đụng cùng câu thì gộp thành một câu đạt cả hai ý.
2. Áp theo thứ tự ưu tiên: FAIL của lint → lỗi được ≥2 giám khảo nêu → đề xuất LSI/coverage →
   chính tả/câu dài/câu lặp → lỗi 1 giám khảo nêu.
3. Không áp đề xuất làm thêm từ khoá chính nguyên cụm, làm brand lệch số lần, làm từ hạn chế
   vượt trần, hay đưa tiếng Anh vào bài. Bỏ đề xuất đó và ghi lý do.
4. Giữ độ dài: tổng số từ dưới `so_tu.toi_da`; một đoạn sửa không dài/ngắn hơn quá 10% đoạn cũ,
   trừ đề xuất bổ sung đoạn mới của Bước 2.
5. Bỏ in nghiêng của đề xuất (`*...*`) khi chép vào bài; bài giao không có in đậm/in nghiêng.
6. Giữ dòng `META:` nếu đã có; Bước 3 chép meta từ `b3-chinh-ta.md`.
7. Câu nêu số liệu chưa chắc mà giám khảo đưa vào "Cần kiểm chứng": viết lại định tính hoặc
   giữ nguyên và thêm vào `can-kiem-chung.md`, không tự bịa nguồn.

## Kiểm sau khi sửa

Chạy lint trên bản mới. Còn FAIL thì sửa tiếp, tối đa 2 vòng; vẫn còn thì giao kèm danh sách
FAIL chưa gỡ được và lý do (thường là mâu thuẫn trong brief).

## `bN-thay-doi.md`

```markdown
| # | Nguồn đề xuất | Câu cũ | Câu mới | Áp / bỏ (lý do) |
Lint trước: X FAIL, Y WARN, Z từ → sau: ...
```
