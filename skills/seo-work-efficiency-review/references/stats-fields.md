# `--stats`: từng field và cách đọc đúng

Nguồn: `mwg-task-console/src-tauri/src/stats.rs`. Toàn bộ output là một JSON object.

## Kỳ

| Field | Nghĩa |
| --- | --- |
| `ky.from` / `ky.to` | Kỳ đang xét (YYYY-MM-DD, Asia/Ho_Chi_Minh, bao gồm cả 2 đầu) |
| `ky_truoc.from` / `.to` | Kỳ liền trước, **cùng độ dài**, do CLI tự tính |

Kỳ trước luôn liền kề và cùng độ dài. Không tự chọn kỳ so sánh khác rồi bảo là
`--stats` nói vậy.

## `gio` — giờ đi vào đâu

| Field | Nghĩa |
| --- | --- |
| `gio.tong` | Tổng **giây** trong kỳ |
| `gio.theo_workstream` | Giây theo `workstream` frontmatter |
| `gio.theo_category` | Giây theo `category` frontmatter |
| `gio.theo_kind` | `folder` (task có thư mục) vs `routine` (việc cố định hằng ngày) |
| `gio.top_task[]` | 10 task tốn giờ nhất, giảm dần |
| `gio_ky_truoc` | Tổng giây kỳ trước |
| `gio_thay_doi_phan_tram` | `null` khi kỳ trước = 0 giây |

Đơn vị là **giây**. Chia 3600 rồi làm tròn 1 chữ số thập phân trước khi viết vào report.

**`gio_thay_doi_phan_tram` chỉ dùng được khi `ghi_chu` ở cấp báo cáo rỗng.** Nếu kỳ trước
nằm (một phần) trước `moc_gio_som_nhat`, con số này vẫn được tính và vẫn có vẻ hợp lệ —
một lần chạy thật đã cho ra `+255738%` vì kỳ trước chỉ có 39 giây. Đọc `ghi_chu` trước.
Có nội dung thì bỏ hẳn phần trăm và viết lại `ghi_chu`.

Nhóm `"(không rõ)"` là task có giờ nhưng không tra được frontmatter — giữ nguyên trong
bảng, đừng lọc bỏ, vì bỏ đi thì tổng các dòng không bằng `gio.tong` và bảng nói dối.

`gio.top_task[]` mỗi dòng: `slug`, `label`, `kind`, `workstream`, `category`, `status`,
`seconds`, `so_ngay` (số ngày khác nhau có bấm giờ cho task đó). `so_ngay` cao + `seconds`
thấp = việc bị rải mỏng; `so_ngay` thấp + `seconds` cao = một mạch dài.

## `so_lan_doi_task_moi_ngay`

Mảng `[ngày, số lần]`. Đếm số lần bắt đầu/tiếp tục một task **khác** task đang chạy
trong ngày đó — quay lại task cũ vẫn tính là một lần đổi, vì vẫn phải nạp lại ngữ cảnh.

Con số trần trụi không nói lên gì. Đưa nó về "trung bình bao nhiêu phút một mạch" bằng
cách chia giờ của ngày đó cho số lần đổi.

## `viec_moi` — có loại việc nào mới không

| Field | Nghĩa |
| --- | --- |
| `moc_index` | Ngày app bắt đầu **theo dõi** việc (`first_seen_utc` sớm nhất) |
| `slug_moi` | Task lần đầu được bấm giờ **trong kỳ**. `null` = chưa phân biệt được |
| `workstream_moi` | `workstream` chưa từng thấy ở task cũ hơn kỳ |
| `category_moi` | Tương tự cho `category` |
| `ghi_chu` | Rỗng = ba list trên dùng được |

**"Mới" ở đây nghĩa là mới bắt đầu ăn giờ, không phải mới được tạo.** Hàng `task` trong
`console.db` chỉ sinh ra khi bấm giờ / cộng giờ tay / thêm vào focus. Nên một task tạo
từ tháng trước mà tuần này mới đụng tới vẫn nằm trong `slug_moi` — nhìn slug là thấy
(`260814-…` xuất hiện trong kỳ 19–25/08). Viết là "tuần này mới bắt đầu làm", đừng viết
"tuần này mới phát sinh task".

Bẫy 1: nếu `moc_index` **nằm trong kỳ**, thì mọi task app biết đều "mới thấy lần đầu" —
không phải vì chúng mới, mà vì app mới bắt đầu theo dõi. Ca đó CLI trả `null` + `ghi_chu`.
`null` ở đây **không** có nghĩa "không có việc gì mới".

Bẫy 2: `moc_index` nằm ngay **sát trước** kỳ (cách 1–2 ngày) thì CLI không chặn, nhưng
danh sách vẫn gần như vô nghĩa — nó liệt kê hầu hết mọi task đã đụng tới. Tự kiểm khoảng
cách `moc_index` → `ky.from`; dưới một kỳ thì nói rõ "app mới theo dõi từ {ngày}, danh
sách này chưa phân biệt được việc mới với việc cũ mới bấm giờ lần đầu".

## `loai_viec[]` — cùng loại task, nay nhanh hơn chưa

Rỗng khi `tasks/_loai-viec.md` chưa có dòng nào. Đó là trạng thái ngày đầu, không phải lỗi.

| Field | Nghĩa |
| --- | --- |
| `ten` / `pattern` | Tên loại việc và chuỗi con khớp trong slug |
| `so_task` | Số task loại này có giờ trong kỳ |
| `gio_trong_ky` | Tổng giờ trong kỳ |
| `so_task_tron_ky` | Số task có **toàn bộ** giờ nằm trong kỳ |
| `trung_binh_gio` | Trung bình giờ **trọn đời** một task. `null` khi < 3 task trọn kỳ |
| `trung_binh_ky_truoc` | Tương tự cho kỳ trước |
| `thay_doi_phan_tram` | **ÂM = nhanh hơn.** `null` khi thiếu một vế |
| `ghi_chu` | Rỗng = số trên dùng được |

**Dấu ngược so với mọi chỉ số khác ở đây.** Chỗ khác thì tăng là tốt; ở cột này giảm mới
là tốt, vì nó là giờ tiêu cho một task. `-50%` nghĩa là làm nhanh gấp đôi — viết ra thành
câu, đừng để người đọc tự đoán dấu.

**Vì sao `trung_binh_gio` không dùng `gio_trong_ky / so_task`.** Một task 10h trải hai kỳ
(6h kỳ trước, 4h kỳ này) sẽ hiện "4h" ở kỳ này và trông như đã nhanh hơn 33%. Nó không
nhanh hơn, nó bị cắt đôi — và cái sai đó **luôn** lệch về hướng "đang nhanh lên". Nên
trung bình chỉ tính task có cả mốc giờ đầu lẫn cuối nằm trong kỳ, và lấy giờ trọn đời của
nó. `so_task_tron_ky < so_task` là bình thường; nói ra khoảng lệch đó khi nó lớn.

## `de_xuat_loai_viec[]` — cách danh sách dài ra

Token slug lặp ở ≥ 3 task mà chưa loại việc nào phủ. Mỗi dòng có `token`, `so_task`,
`gio`, `vi_du` (tối đa 3 slug).

Đây là **đề xuất**, không phải phân loại. Skill được phép nêu ra ("`infobox` lặp ở 5 task,
11.5h, chưa phân loại") nhưng **không được** tự sửa `tasks/_loai-viec.md` — thêm loại việc
là quyết định của owner, và phân loại sai một lần thì mọi so sánh sau đó nói về hai thứ
khác nhau. Thêm bằng nút trong app, đi qua modal diff.

`loai_viec_canh_bao[]` là dòng hỏng trong file (pattern trùng, thiếu ô). Có nội dung thì
dẫn lại — bảng đang thiếu dòng so với những gì owner tưởng đã thêm.

## `diem_nghen[]`

Tối đa 5 dòng, xếp giảm dần theo `gio`. Hai `kieu`:

| `kieu` | Nghĩa | Ngưỡng |
| --- | --- | --- |
| `task-keo-dai` | Nhiều giờ mà status chưa `done`/`cancelled` | ≥ 4h |
| `vuot-trung-vi-nhom` | Tốn ≥ 2× trung vị các task cùng `workstream` | nhóm phải có ≥ 3 task |

`chi_tiet` đã là câu tiếng Việt đọc được — trích thẳng vào report, đừng diễn giải lại.

Một `slug` xuất hiện hai lần với hai `kieu` khác nhau là bình thường và có ý nghĩa: nó
vừa lâu vừa lệch mặt bằng nhóm.

Không có nhóm nào đủ 3 task thì `vuot-trung-vi-nhom` vắng mặt hoàn toàn. Đó là thiếu
mẫu, không phải "mọi task đều trong chuẩn".

## `velocity` — đóng được nhiều việc hơn không

| Field | Nghĩa |
| --- | --- |
| `co_du_lieu_tu` | Ngày `status_change` bắt đầu có dữ liệu. `null` = chưa có dòng nào |
| `task_done_trong_ky` | Số task chuyển sang `done`. `null` = chưa đo được |
| `task_done_ky_truoc` | Tương tự cho kỳ trước |
| `thay_doi_phan_tram` | `null` khi thiếu một vế, hoặc kỳ trước = 0 |
| `theo_ngay` | `[ngày, số task done]` |
| `ghi_chu` | **Rỗng thì số trên mới dùng được** |

Đếm theo `count(DISTINCT task_id)`: một task bị đóng-mở-đóng trong cùng kỳ vẫn tính 1.

Vì sao có thể `null`: `status_change` chỉ tích luỹ từ lúc app cài migration 004. `updated`
trong frontmatter **không** thay thế được — nó bị ghi đè mỗi lần chạm file, nên một task
cũ sửa lại hôm nay sẽ trông như vừa đóng hôm nay.

### `velocity.uoc_luong` — số suy từ `updated`

`null` là trường hợp thường. Có object nghĩa là workspace đã chạy `--seed-status`, và
đây là ước lượng cho đoạn trước khi app bắt đầu ghi thật.

| Field | Nghĩa |
| --- | --- |
| `task_done_trong_ky` / `task_done_ky_truoc` | Đếm KÈM dòng seed |
| `thay_doi_phan_tram` | Cùng luật `null` như số thật |
| `canh_bao` | **Luôn có nội dung** |

Ba luật bắt buộc:

1. **Không bao giờ trộn số ước lượng vào chỗ của số thật.** `task_done_trong_ky` ở cấp
   `velocity` là số thật; nó `null` thì report ghi "chưa đo được", không được thay bằng
   số trong `uoc_luong`.
2. **Trích `canh_bao` mỗi lần trích số.** Không có ngoại lệ, kể cả khi report dài.
3. **Ước lượng lệch theo hướng muộn hơn thực tế.** `updated` là lần cuối chạm file, nên
   task đóng xong bị sửa lại mang ngày muộn. Đừng đọc nó như mốc đóng.

Giới hạn phủ: seed chỉ chạm được task đã từng bấm giờ (hàng `task` chỉ sinh khi bấm giờ).
Đo thật trên workspace này: 93 task `done` trên đĩa, seed được 18, bỏ qua 75 vì chưa bấm
giờ lần nào. Nên `uoc_luong` là sàn dưới, không phải con số đầy đủ.

## Field ở cấp báo cáo

| Field | Nghĩa |
| --- | --- |
| `khong_ro_metadata[]` | Slug có giờ nhưng không tra được frontmatter |
| `moc_gio_som_nhat` | Ngày sớm nhất `console.db` có giờ |
| `ghi_chu` | Cảnh báo toàn báo cáo, thường là kỳ trước nằm trước lúc app bắt đầu đo |

`khong_ro_metadata` gồm cả `rt-*` (việc cố định, cố ý không có thư mục) — đó không phải
lỗi. Task `folder` nằm trong danh sách này mới là dấu hiệu slug đã bị xoá/đổi tên.

## Lệnh phụ

`--list-hours --from D --to D` — mọi task có giờ trong khoảng, mỗi dòng có `kind`.
Dùng khi cần nhìn từng ngày thay vì tổng kỳ.

`--export-week --week D` — ma trận Thứ 2..CN cho mọi task có giờ trong tuần. Dùng khi
cần bảng theo ngày để điền File 1.

`--export-hours <slug>` — một task. **Không** dùng lệnh này để dò xem tuần này có những
task nào: nó cần biết slug trước, nên nó luôn trả thiếu.
