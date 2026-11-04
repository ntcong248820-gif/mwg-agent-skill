# Chấm điểm 7 checklist ("3 lần chấm" — POE)

Nguồn: dòng "3 lần chấm" Bước 3 tab Thầy. Sếp dán bài vào POE và chấm 3 lần để lấy ý kiến
nhiều model. Ở đây: 3 giám khảo độc lập chạy song song, mỗi người một file, không đọc bài chấm
của nhau. Đầu vào: bài mới nhất, `brief.json`, kết quả lint của đúng phiên bản đó.
Đầu ra: `bN-cham-{a|b|c}.md`.

## Prompt

> Bạn đóng vai trò là chuyên gia SEO thực chiến, cũng là Creator Content với hơn 10 năm kinh nghiệm trong lĩnh vực {nganh}.
> Mình đưa ra 7 Checklist. Bạn nêu ưu điểm, nhược điểm của từng checklist. Sau đó đề xuất cải thiện từng checklist để content đạt hiệu quả cao. Đánh giá điểm theo thang điểm 10 cho từng checklist.
>
> 1. Từ khóa thương hiệu {brand} xuất hiện bao nhiêu lần? Mật độ này có hợp lý không? Có dấu hiệu nhồi nhét từ khóa (Keyword Stuffing) không?
> 2. Từ khóa chính trong bài viết là "{kw_chinh}" xuất hiện bao nhiêu lần? Có được phân bổ hợp lý trong các phần quan trọng (H1, H2, H3, meta description, đoạn mở đầu, nội dung bài viết, đoạn kết) không?
> 3. Từ khóa Semantic là những từ nào? Chúng có được tích hợp tự nhiên trong bài viết không? Có dấu hiệu nhồi nhét không?
> 4. Từ khóa LSI là những từ nào? Chúng có giúp bài viết trở nên tự nhiên và có ý nghĩa hơn không?
> 5. Từ khóa có xuất hiện tự nhiên không? Hay có dấu hiệu lặp lại một cách gượng ép?
> 6. Tổng thể bài viết có đảm bảo sự mạch lạc, tự nhiên và không bị Google đánh giá là nội dung AI hoặc spam không?
> 7. Kiểm tra bài viết có lỗi chính tả, ngữ pháp và cách diễn đạt không? Liệt kê lỗi sai và đề xuất cách viết lại để diễn đạt tự nhiên, mạch lạc hơn.
>
> Cuối cùng tổng kết điểm trung bình.

Số lần xuất hiện ở checklist 1 và 2 lấy từ kết quả lint, không tự đếm: model đếm cụm từ tiếng
Việt hay sai, còn lint đếm chính xác. Giám khảo nhận xét mật độ và vị trí dựa trên số đó.

Thêm một mục ngoài 7 checklist: câu nào nêu số liệu, mốc thời gian, mức phí hoặc điều luật
mà giám khảo không chắc đúng → liệt kê ở `## Cần kiểm chứng`. Không chấm trừ vì thiếu số liệu.

## Định dạng ra (giữ đúng tên mục để người điều phối gộp điểm)

```markdown
| # | Checklist | Điểm /10 | Ưu điểm | Nhược điểm | Đề xuất |
|---|---|---|---|---|---|
| 1 | Brand | 8 | ... | ... | ... |
...
ĐIỂM TRUNG BÌNH: 8.4
## Lỗi cần sửa
- "<câu nguyên văn>" → "<viết lại>" (checklist #)
## Cần kiểm chứng
- "<câu nguyên văn>": <vì sao nghi>
```
