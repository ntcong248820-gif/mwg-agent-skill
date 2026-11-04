# Bước 2: Tối ưu Semantic Coverage

Nguồn: Bước 2 tab Thầy (2 prompt). Đầu vào: bài mới nhất, `01-semantic.md`, `brief.json`.
Đầu ra: `b2-coverage.md`. Không sửa file bài; người biên tập áp đề xuất.

## Prompt

> Bạn đóng vai trò là {chuyen_gia}. Hãy đánh giá tỷ lệ đạt Semantic Coverage của cả bài khi xét theo trục Semantic chiều dọc và chiều ngang. Sau đó đưa ra giải pháp để tăng tỉ lệ đạt ở 2 trục thành 100%. Chỉ ra được từng giải pháp đó sẽ bổ sung những từ khóa semantic nào, thuộc nhóm nào. Không viết tiếng Anh xen lẫn tiếng Việt, chỉ viết tiếng Việt.

> Triển khai theo đề xuất. Nếu là bổ sung đoạn văn mới thì chỉ ra vị trí bổ sung trong bài, có bổ sung H2 hoặc H3 hay không, hay chỉ là đoạn văn. Nếu là bổ sung từ khóa semantic vào đoạn văn cũ thì hãy trình bày đoạn cũ và đoạn mới đồng thời italic từ khóa semantic trong đoạn mới đề xuất để dễ nhận biết.
>
> Lưu ý đề xuất ngắn gọn nhất có thể, không viết quá dài. Mỗi đoạn đề xuất chỉ từ 50-100 từ. Các đoạn đề xuất không xuất hiện thêm từ khóa chính. Không viết tiếng Anh xen lẫn tiếng Việt, chỉ viết tiếng Việt.

## Định dạng ra

```markdown
## Đánh giá
| Trục | Tỷ lệ đạt | Cluster đã phủ | Cluster còn thiếu |
## Đề xuất
### ĐX1 — <vị trí: sau đoạn ... của H2/H3 ...> — <đoạn mới | sửa đoạn cũ | thêm H3>
Nhóm: <cluster/nhóm LSI> | Cụm bổ sung: a, b, c
Đoạn cũ: <nguyên văn, để người biên tập tìm đúng chỗ>
Đoạn mới: <50-100 từ, cụm semantic in nghiêng bằng *...*>
```

Không thêm H2 khi `brief.cau_truc_h2` đã cố định số H2; ưu tiên chèn vào đoạn cũ. Tổng số từ
sau khi áp mọi đề xuất phải dưới `brief.so_tu.toi_da`; ghi ước lượng số từ tăng thêm ở cuối file.
