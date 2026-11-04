# Impact Report Contract

## Artifact layout

```text
tasks/{task}/
├── data/raw/
│   ├── data-order-{scope}-actions.json
│   ├── gsc-{scope}-p0.json
│   ├── gsc-{scope}-p2.json
│   └── gsc-{scope}-p1.json
├── data/processed/
│   ├── action-impact-matrix.csv
│   ├── action-impact-summary.csv
│   ├── url-movers.csv
│   └── keyword-movers.csv
└── reports/{yymmdd-hhmm}-impact-{scope}.md
```

## `action-impact-matrix.csv` — cột bắt buộc

`action_id`, `source_tab`, `action_family`, `target_url`, `ngay_xong`,
`clicks_p0`, `clicks_p2`, `clicks_p1`, `delta_clicks`, `delta_clicks_pct`,
`imp_p1`, `ctr_p0`, `ctr_p1`, `pos_p0`, `pos_p1`, `delta_pos`,
`gio_bo_ra`, `hieu_qua_moi_gio`, `bucket`, `note`

Một dòng một action. URL nhiều action thì lặp URL, giữ nguyên `action_id` khác nhau.

`gio_bo_ra` để TRỐNG khi chưa đo được (action làm trước khi cài app, hoặc task gom
nhiều action không tách được). Trống ≠ 0: ghi `0` là khẳng định action đó tốn 0 giờ,
và mọi tỷ số hiệu quả/giờ tính từ đó đều sai. `hieu_qua_moi_gio` cũng để trống theo,
và dòng đó xếp riêng ở cuối bảng.

## `action-impact-summary.csv`

`bucket`, `so_luong`, `ty_le_pct` — cộng đủ 100%, có dòng `TỔNG CỘNG`.

## Section report

1. `## Summary` — verdict 1 câu, tỷ lệ action thành công + công thức, 3 khoảng ngày, scope.
2. `## Evidence - Hiệu Quả Tổng Thể` — bảng clicks/impressions/CTR/avg position cho
   P0, P2, P1 + 2 cột delta (P1 vs P2, P1 vs P0). Kèm 1 đoạn nhận định chính.
3. `## Phân Loại Tác Động` — bảng 6 bucket: số lượng, tỷ lệ, mô tả tín hiệu GSC.
4. `## Breakdown Theo Tab Action` — mỗi tab một mục, nêu action tiêu biểu kèm số liệu.
5. `## URL Movers` — URL đã làm action, sort theo delta clicks desc, gồm cả URL giảm.
6. `## Keyword Movers` — winners và losers tách 2 bảng nhỏ.
6b. `## Hiệu Quả Trên Mỗi Giờ` — bảng xếp theo `hieu_qua_moi_gio` giảm dần, cột
   `gio_bo_ra` bên cạnh delta tuyệt đối. Nhóm chưa đo được giờ xếp riêng ở cuối, có
   nhãn rõ. Nêu ra khi thứ tự này khác thứ tự theo delta tuyệt đối.
7. `## Recommendations & Next Actions` — mỗi item gắn URL cụ thể + action đề xuất,
   ưu tiên theo hiệu quả/giờ.
8. `## Outputs` — link tới raw + processed file.
9. `## Unresolved Questions`.

## Rule ghi số

- Clicks/impressions: số nguyên, có dấu phân cách nghìn.
- CTR: 2 chữ số thập phân + `%`; delta CTR ghi `%p` (điểm phần trăm), không ghi `%`.
- Position: 2 chữ số thập phân; delta ghi `+x.xx rank` khi tốt lên.
- Giờ: 1 chữ số thập phân, đơn vị giờ (`2.5h`). Chưa đo được thì ghi `chưa đo`, không
  ghi `0h` và không ghi `—` (dấu gạch dễ đọc nhầm thành "không tốn giờ").
- Không bold số nếu chưa trace được về raw file.

## Closeout

- Cập nhật task `README.md`: `## Results` gồm delta tổng ngành + count theo bucket.
- Nếu `report_targets.file1_cv` hoặc `file2_weekly` là `true` mà chưa log, task vẫn
  đóng được — ghi việc log còn nợ vào `## Next Steps`. `report_sync` là sổ nợ log,
  không phải cổng (root `CLAUDE.md`, mục Work Report Policy).
- Với File 2, `Hiệu quả đạt được` nối về ranking/traffic, viết ngắn, ít technical.
- Nếu fetch GSC hoặc đọc Sheet fail, ghi partial/blocker thẳng, không suy số.
