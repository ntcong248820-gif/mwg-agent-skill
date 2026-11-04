# Contract report hiệu quả công việc

## Artifact

```text
tasks/{task}/
├── data/raw/stats-{from}-{to}.json     # nguyên văn output --stats
└── reports/{yymmdd-hhmm}-efficiency-{kỳ}.md
```

Lưu JSON thô trước khi viết report. Report tham chiếu về nó; không có nó thì không ai
kiểm lại được con số nào.

Task folder: dùng task hiện có nếu review nằm trong một initiative đang chạy. Nếu không,
`workstream: analytics`, `category: reporting`, `task_type: single`.

## Section bắt buộc, đúng thứ tự

### 1. Kỳ và độ tin cậy

Kỳ xét, kỳ so sánh, và **ngay lập tức** mọi `ghi_chu` không rỗng. Đặt ở đầu chứ không
ở cuối: người đọc phải biết chỗ nào chưa đo được trước khi đọc bảng, không phải sau.

```markdown
Kỳ: 19/08–25/08/2026. So với 12/08–18/08/2026.
Velocity: chưa đo được — status_change mới có dữ liệu từ 25/08/2026.
```

### 2. Giờ đi vào đâu

Bảng `workstream` (giờ + % tổng), bảng `kind` (`folder` vs `routine`), và tổng kỳ so
với kỳ trước.

So với kỳ trước **chỉ khi** `ghi_chu` cấp báo cáo rỗng. Không rỗng thì viết
"chưa có mốc so" kèm lý do — `gio_thay_doi_phan_tram` vẫn ra số trong ca đó, và số đó
vô nghĩa (một lần chạy thật ra `+255738%`).

Nêu `routine` thành một dòng riêng có nhận xét. Nếu nó chiếm phần lớn giờ thì đó là
phát hiện chính của report, không phải một dòng trong bảng.

### 3. Top task tốn giờ

Tối đa 10 dòng: slug, label, giờ, `so_ngay`, status. Cột `so_ngay` là cột đáng nói —
"14h trong 1 ngày" và "14h rải 9 ngày" là hai vấn đề khác nhau.

### 4. Chi phí chuyển việc

`so_lan_doi_task_moi_ngay`, viết thành câu có nghĩa: "24/08 đổi việc 20 lần trên 5.5h,
trung bình 16 phút một mạch."

### 5. Việc mới phát sinh

`slug_moi` / `workstream_moi` / `category_moi`. Có `ghi_chu` thì ghi nguyên văn `ghi_chu`
vào chỗ này và không liệt kê gì thêm.

Gọi đúng tên: đây là "việc tuần này mới bắt đầu bấm giờ", không phải "task mới tạo".
Nếu `moc_index` cách `ky.from` dưới một kỳ thì nói ra giới hạn đó ngay tại section.

### 5b. Loại việc

Bỏ qua section này khi `loai_viec` rỗng — nói một câu "chưa dựng danh sách loại việc" là đủ.

Có thì bảng: loại, giờ kỳ này, số task (kèm số trọn kỳ), TB giờ/task, TB kỳ trước, %.

Ba luật:

1. **Âm là tin tốt.** Viết "`Infobox`: 2.3h/task, giảm 18% so kỳ trước" — không để dấu
   trần cho người đọc tự suy.
2. `trung_binh_gio = null` thì **không** suy ra tốc độ bằng cách khác. Dẫn `ghi_chu`.
3. `so_task_tron_ky` lệch nhiều so với `so_task` thì nói ra: phần lớn task loại này còn
   đang làm dở, nên trung bình dựa trên một mẫu nhỏ hơn con số ở cột task.

Có `de_xuat_loai_viec` thì thêm một dòng gợi ý cuối section: token nào lặp nhiều mà chưa
phân loại. **Không tự sửa `tasks/_loai-viec.md`** — đó là quyết định của owner, thêm bằng
nút trong app.

### 6. Điểm nghẽn

Bảng từ `diem_nghen`, dùng nguyên `chi_tiet`. Với mỗi dòng, thêm một câu từ
`## Current State` / `## Next Steps` của task đó — số giờ nói task nghẽn, README nói
nghẽn ở đâu.

### 7. Velocity

`task_done_trong_ky` vs `task_done_ky_truoc` và `theo_ngay`. `ghi_chu` không rỗng thì
section này chỉ có một câu dẫn lại `ghi_chu`, không có bảng, không có phần trăm.

Có `velocity.uoc_luong` thì thêm một đoạn **tách riêng, dưới đoạn số thật**, mở đầu bằng
"Ước lượng (không phải mốc đóng thật):" và kèm `canh_bao`. Không gộp vào cùng câu với số
thật, không dùng nó để lấp chỗ `null` ở trên.

### 8. Đề xuất — đúng một điểm

```markdown
## Đề xuất tuần tới

**Nghẽn:** {mô tả, kèm giờ}
**Làm:** {một hành động, gói trong một buổi}
**Đo bằng:** {field nào trong --stats sẽ đổi, theo hướng nào}
```

Không có gì đạt cả ba thì viết "kỳ này không có điểm nghẽn đáng đề xuất" và nói tại sao.

### 9. Unresolved Questions

Cuối file. Chỗ ghi những gì số liệu chưa trả lời được.

## Quy tắc số

| Tình huống | Viết | Không viết |
| --- | --- | --- |
| Có giờ | `5.5h` | `5.53h`, `19908s` |
| Chưa đo được | `chưa đo` + lý do | `0h`, `0%`, `—` |
| Tăng | `+18%` | `18%` |
| Giảm | `−12%` | `12%`, `(12%)` |
| Kỳ trước = 0 | `chưa có mốc so` | `+100%` |

## Không được làm

- Không đổi status task nào. Report này chỉ đọc.
- Không ghi vào `report_sync`. Đó là việc của `seo-log-cv` / `seo-log-weekly-work`.
- Không đề xuất mở lại task đã đóng để "làm cho gọn số liệu".
- Không suy giờ từ ngày sửa file, từ số commit, hay từ độ dài report.
- Không sửa `tasks/_loai-viec.md`. Đề xuất được, ghi thì không.
- Không gộp hai kỳ độ dài khác nhau rồi so phần trăm.
