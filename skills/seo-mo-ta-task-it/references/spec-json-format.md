# Định dạng spec JSON

Một spec = một nguồn duy nhất cho cả 3 việc: lint, red-team đọc (qua preview md), dựng Doc,
thêm dòng sheet. Mẫu đầy đủ: `assets/example-spec-khung-a.json`.

Lưu spec ở `tasks/{task}/data/processed/mo-ta-it/spec.json`, ảnh cùng thư mục (`images` là
đường dẫn tương đối so với file spec).

## Khung ngoài

Chú thích `//` dưới đây chỉ để đọc — file thật là JSON thuần, không có comment.

```json
{
  "template": "A",                       // A | B | C — xem khung-mo-ta-a-b-c.md
  "title": "[TGDĐ - ĐMX] …",             // = tên Doc = tên task trên sheet
  "orientation": "auto",                 // auto | portrait | landscape
  "info": {
    "bo_phan_yeu_cau": "SEO/Traffic",
    "ngay_khoi_tao": "dd/mm/yyyy",
    "lead_task": "An - 100002",
    "support_task": "Bình - 100003",       // nhiều người: cách dấu phẩy; trống được
    "designer": "", "link_design": "",
    "site_ap_dung": "1 (Thế Giới Di Động), 2 (Điện Máy Xanh)",
    "extra": {"Nơi khai báo": "PIM - Thương hiệu (dmx_brand)"}   // tuỳ chọn
  },
  "history": [{"ngay": "dd/mm/yyyy", "name": "An - 100002", "mo_ta": "Khởi tạo tài liệu"}],
  "images": {"a1": "a1-cms-hien-tai.png"},
  "body": [ … khối … ],
  "tracker": {
    "tab": "TGDĐ", "uu_tien": "SEO 1", "site": "TGDD", "du_an": "TGDĐ", "pic": "IT",
    "loai_task": "Task mới", "muc_dich": "…", "phu_trach": "An - 100002",
    "timeline_ky_vong": ""                // tuỳ chọn
  }
}
```

Không có khoá nào cho ô xác nhận/duyệt — cố ý. Lint báo lỗi nếu thêm.

## Khối trong `body`

| Khối | Dạng | Ghi chú |
| --- | --- | --- |
| Heading | `{"h1": "3. Mô tả chi tiết yêu cầu"}` / `h2` / `h3` | tự ghi số |
| Đoạn | `{"p": "chữ **đậm** [link](https://…)"}` | nhiều dòng bằng `\n`; dòng `- ` thành bullet |
| Bullet | `{"bullets": ["mục 1", "  mục con", "    mục cháu"]}` | 2 dấu cách đầu = cấp 2, 4 dấu cách = cấp 3 |
| Bảng | `{"table": {"header": [...], "rows": [[...]], "widths": [1,2], "label_col": false, "img_row": "{img:a1}\n**Ảnh 1 - …**"}}` | `header` → nền xanh; `label_col` → cột 1 nền xám đậm; `img_row` → hàng ảnh gộp ngang dưới cùng |
| Ảnh rời | `{"img": "a1", "caption": "Ảnh 1 - …", "width": 400}` | căn giữa, caption đậm |
| Code | `{"code": "User-agent: *\nDisallow: /bin/"}` | bảng 1 ô Courier New |

## Markdown trong chữ (ô bảng, đoạn, bullet)

| Viết | Ra |
| --- | --- |
| `**chữ**` | đậm |
| `[chữ](https://url)` | link (chỉ http/https) |
| `{red}chữ{/red}` | chữ đỏ — chỉ để khoanh lỗi trong chữ, dùng ít |
| `- dòng` / `  - dòng` / `    - dòng` | bullet cấp 1 / cấp 2 / cấp 3 |
| `{img:a1}` / `{img:a1\|300}` | ảnh theo bề rộng ô / width 300pt |

Không có in nghiêng, gạch chân, heading trong ô. Cần thì đổi cách viết, đừng thêm cú pháp.

## File update (`--append-update`)

```json
{
  "update": {"ngay": "dd/mm/yyyy", "name": "An - 100002", "mo_ta": "Bổ sung rule ĐMX"},
  "images": {},
  "body": [ {"h2": "1. Mục đích task"}, …, {"h2": "3. Chi tiết task"}, … ]
}
```

Script thêm dòng vào bảng lịch sử (bảng đầu tiên có ô đầu bắt đầu bằng "Ngày"), rồi nối
H1 `Update mô tả ngày {ngay} - {name}` và các khối ở cuối Doc. Không xoá gì.
