# Results Section Examples — seo-task-done

Reference examples for filling `## Results` section when closing tasks.

## Template

```markdown
## Results

| Metric | Trước | Sau | So sánh |
| ------ | ----- | --- | -------- |
| {metric} | {before} | {after} | {delta} |

**Trạng thái xử lý:** {status}

**Tóm tắt:** {1–2 sentences}
```

---

## Example 1 — Nghiệm thu technical (no metrics)

```markdown
## Results

| Metric | Trước | Sau | So sánh |
| ------ | ----- | --- | -------- |
| Breadcrumb đạt | 45/49 dòng | 47/49 dòng | +2 dòng |
| Lỗi còn tồn đọng | — | 2 dòng | Min-Max filter (hash fragment) |

**Trạng thái xử lý:** Đã xử lý xong — 47/49 dòng PASS. 2 dòng còn chờ IT xác nhận hướng xử lý hash fragment.

**Tóm tắt:** Nghiệm thu breadcrumb 49 URL trên Core Web mới. 47 dòng đạt chuẩn sau vòng 2, 2 dòng tồn đọng liên quan client-side hash filter cần làm rõ với IT.
```

---

## Example 2 — GSC performance có số liệu

```markdown
## Results

| Metric | Kỳ 1 (20/6–17/7) | Kỳ 2 (23/5–19/6) | So sánh |
| ------ | ----------------- | ----------------- | ------- |
| Clicks (laptop asus) | 2,300 | 2,041 | +12.7% |
| Impressions (laptop asus) | 26,690 | 27,585 | -3.2% |
| Clicks (màn hình 27 inch) | 159 | 142 | +12% |
| Rank (màn hình 27 inch) | 1.3 | 1.7 | ↑ cải thiện |

**Trạng thái xử lý:** Hoàn thành — đã điền vào File 2 sheet <name>.

**Tóm tắt:** Kiểm tra GSC 4 URL danh mục laptop/màn hình. Laptop Asus giữ rank tốt, màn hình 27 inch cải thiện vị trí từ 1.7 lên 1.3.
```

---

## Example 3 — Research keyword (số lượng)

```markdown
## Results

| Metric | Giá trị |
| ------ | ------- |
| Tổng keyword research | 112 keyword |
| Nhóm sản phẩm cover | Laptop gaming, Màn hình, Phụ kiện |
| File output | Google Sheet — tab Research KW |

**Trạng thái xử lý:** Đã xử lý xong — file đã gửi team.

**Tóm tắt:** Research 112 keyword cho 3 nhóm sản phẩm mới nhập về. Ưu tiên triển khai theo volume search và độ khó.
```

---

## Example 4 — Xử lý lỗi kỹ thuật (done bởi IT)

```markdown
## Results

| Lỗi | Trạng thái |
| --- | ---------- |
| Metadata sau filter thừa kế từ trang trước | ✅ IT đã sửa |
| Metadata nằm ngoài thẻ head | ✅ IT đã sửa |
| Pre-render thiếu nội dung tĩnh | ✅ IT đã sửa |

**Trạng thái xử lý:** Đã xử lý xong — tất cả lỗi đã được IT khắc phục và nghiệm thu lại.

**Tóm tắt:** 3 lỗi kỹ thuật SEO phát sinh trong giai đoạn go-live Core Web mới đã được xử lý hoàn toàn.
```

---

## Status Badge Values

| Tình huống | Status text |
|---|---|
| Xong hết | `Đã xử lý xong` |
| Còn tồn đọng | `Còn tồn đọng X vấn đề — [mô tả]` |
| Chờ IT | `Đã bàn giao IT, đang chờ xử lý` |
| Chuyển giao | `Đã chuyển giao team [tên], hoàn thành phần của mình` |
| Hủy | `Cancelled — [lý do]` |
