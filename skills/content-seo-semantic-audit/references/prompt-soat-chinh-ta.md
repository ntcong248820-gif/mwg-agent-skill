# Soát chính tả, câu dài, câu lặp (Bước 3, 4, 5) + meta description

Nguồn: prompt "Chính tả lần 1/2/3" tab Thầy (cùng một prompt, chạy lại sau mỗi vòng sửa) và
cột ghi chú Bước 3 (meta description). Đầu vào: bài mới nhất, `brief.json`, kết quả lint
(nếu có). Đầu ra: `bN-chinh-ta.md`. Không sửa file bài.

## Prompt

> Đọc toàn bộ bài viết phiên bản mới nhất rồi sau đó:
> 1. Hãy tìm ra những cấu trúc câu bị dài cần phải viết lại kèm đề xuất
> 2. Kiểm tra xem có lỗi chính tả, ngữ pháp và cách diễn đạt không? Liệt kê tất cả lỗi sai và đề xuất cách viết lại để diễn đạt tự nhiên, mạch lạc hơn.
> 3. Hãy chỉ ra cấu trúc câu bị lặp lại trong bài, sau đó đề xuất cấu trúc thay thế mà vẫn formal, tự nhiên, không rút gọn cũng không viết dài thêm.

Chỉ ở Bước 3 (lần soát đầu), thêm:

> Bổ sung meta description dưới {meta_toi_da} ký tự, viết mượt mà, tự nhiên.

Meta chứa `kw_chinh` nguyên cụm, không chứa brand nếu làm quá ký tự.

## Định dạng ra

```markdown
## Câu dài
| # | Câu gốc (nguyên văn) | Viết lại |
## Chính tả - ngữ pháp - diễn đạt
| # | Câu gốc (nguyên văn) | Lỗi | Viết lại |
## Cấu trúc câu lặp
| Mẫu lặp | Số lần | Câu gốc | Viết lại |
## Meta description          # chỉ Bước 3
META: <nội dung> (<n> ký tự)
```

Câu gốc chép nguyên văn để người biên tập tìm-thay được. Không đề xuất câu viết lại làm thêm
từ khoá chính, brand, hay từ trong `brief.tu_han_che` vượt mức lint cho phép. Lint đã liệt kê
câu dài và mở câu lặp: dùng làm điểm xuất phát, không chép lại nguyên danh sách.
