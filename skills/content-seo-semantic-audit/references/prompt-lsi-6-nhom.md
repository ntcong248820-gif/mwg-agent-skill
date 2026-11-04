# Bước 4: Rà LSI theo nhóm

Nguồn: Bước 4 "Chính tả lần 2 (+ LSI)" tab Thầy (2 prompt). Đầu vào: bài mới nhất,
`brief.json` (`nhom_lsi`), `01-semantic.md`. Đầu ra: `b4-lsi.md`. Không sửa file bài.

## Prompt

> Bạn đóng vai trò là {chuyen_gia}. Hãy quét toàn bộ bài ở phiên bản mới nhất để đưa ra đánh giá sơ bộ về tình hình tối ưu LSI keywords ở các nhóm LSI dưới đây. Đánh giá bao gồm: list những từ khóa LSI bị thiếu và những từ khóa LSI bị lặp lại quá nhiều.
> {nhom_lsi, mỗi nhóm một dòng}
> Làm bảng tổng kết đánh giá mức độ bao phủ của các nhóm.

Sếp chạy prompt thứ hai lần lượt cho từng nhóm yếu ("Nhóm XX"); ở đây làm luôn cho mọi nhóm
dưới mức "Tốt":

> Tiến hành điều chỉnh cho Nhóm XX, để vừa bổ sung LSI keyword bị thiếu, vừa tránh lặp LSI keyword quá mức mà vẫn giữ được tỷ lệ Semantic Coverage như cũ. Lưu ý là khi tiến hành sửa thì hạn chế viết dài thêm cũng như hạn chế rút gọn, hãy cố gắng giữ nguyên độ dài cũ, có sự UX tự nhiên và vẫn giữ cấu trúc câu đã được đa dạng trước đó. Trình bày đầy đủ các đề xuất dưới hình thức show cả đoạn văn cũ và đoạn văn mới đã bổ sung LSI hoặc bỏ bớt LSI để dễ so sánh đối chiếu. Đi kèm đó là các note LSI được thêm - LSI cũ bị thay thế hoặc giảm (nếu có) - LSI cũ lặp (nếu có).

## Định dạng ra

```markdown
## Bảng bao phủ
| Nhóm | Mức (Tốt/Khá/Yếu) | LSI đã có | LSI thiếu | LSI lặp quá nhiều (số lần) |
## Điều chỉnh
### Nhóm <tên>
Đoạn cũ: <nguyên văn>
Đoạn mới: <độ dài ±10% đoạn cũ>
Note: thêm [...] | thay/giảm [...] | lặp [...]
```

"Lặp quá nhiều" là một cụm LSI xuất hiện từ 4 lần trở lên, cùng ngưỡng với từ hạn chế của brief.
