# Giao hàng lên Google Drive

Giao hàng là **một thư mục Drive** nằm trong thư mục cha user đưa, chứa:

```text
{thư mục cha user đưa}/
└── {slug-bài}/
    ├── {Title bài}            ← Google Doc rich text
    ├── 01-{ten-anh}.jpg       ← 2048x1150
    └── 02-{ten-anh}.jpg
```

Doc là Doc thật: heading là heading style, link click được, ảnh chèn inline có
caption. Không phải Doc chứa chữ HTML.

## Schema article.json

```json
{
  "title": "Tít bài",
  "slug": "ten-thu-muc-tren-drive",
  "placement": "bao-ngoai",
  "target_words_min": 800,
  "target_words_max": 1000,
  "max_brand_links": 3,
  "blocks": [
    {"type": "title",   "text": "Tít bài"},
    {"type": "sapo",    "text": "2-3 câu dẫn."},
    {"type": "h2",      "text": "Tên section"},
    {"type": "p",       "text": "Đoạn văn.",
                        "links": [{"text": "cụm neo", "url": "https://..."}]},
    {"type": "image",   "source_url": "https://...",
                        "caption": "Caption ảnh",
                        "filename": "01-ten-file"}
  ]
}
```

| `type` | Thành gì trong Doc |
| --- | --- |
| `title` | HEADING_1 |
| `sapo` | Đoạn in đậm |
| `h2` / `h3` | HEADING_2 / HEADING_3 |
| `p` | Đoạn thường, mang link nếu có |
| `image` | Ảnh inline rộng hết khổ + caption in nghiêng căn giữa |

`links` chỉ hợp lệ trên block `p`. Các field `target_words_*`, `max_brand_links`,
`placement` là tuỳ chọn, bỏ trống thì lấy mặc định.

## Ba bước, đúng thứ tự

### 1. Tạo thư mục con

```bash
cd .claude/skills/tgdd-bai-pr-bao-ngoai/scripts
python3 -c "
import sys; sys.path.insert(0,'.')
from gws_helper import create_folder, assert_account
assert_account()
print(create_folder('{slug-bài}', '{ID-thư-mục-cha}'))"
```

`assert_account()` chặn nếu tài khoản không phải `${GWS_EXPECTED_ACCOUNT}`. Sai
tài khoản là bài của khách rơi vào Drive cá nhân.

### 2. Chuẩn bị ảnh

```bash
python3 prepare-images.py {đường dẫn article.json} \
  --folder {ID-thư-mục-con} \
  --keep-local {thư mục giữ bản resize}
```

Script tải ảnh, resize 2048x1150, upload, mở quyền `anyone/reader`, rồi **ghi
ngược** `public_url`, `drive_file_id`, `src_w`, `src_h` vào chính `article.json`.

Mở quyền public là bắt buộc kỹ thuật: Docs API đi tải ảnh theo URL lúc chèn.

### 3. Dựng Doc

```bash
python3 build-pr-doc.py {đường dẫn article.json} --folder {ID-thư-mục-con}
```

Hoặc để script tự tạo thư mục con luôn:

```bash
python3 build-pr-doc.py {article.json} --parent {ID-thư-mục-cha} --folder-name {slug}
```

Script in ra JSON có `folder_url`, `doc_url`, và trạng thái quyền.

### 4. Quyền chia sẻ (script tự làm)

| Thứ | Quyền | Vì sao |
| --- | --- | --- |
| Google Doc | `anyone` → **writer** | Bên báo sửa bài tại chỗ, không gửi bản sửa qua lại |
| Thư mục | `anyone` → reader | Biên tập viên cần lấy file ảnh, không cần sắp xếp lại thư mục |
| File ảnh | `anyone` → reader | Bắt buộc kỹ thuật để Docs API chèn được ảnh |

Đang làm bản nháp chưa giao thì thêm `--no-share`.

Doc mở quyền edit nghĩa là **ai cầm link cũng sửa hoặc xoá được nội dung**. Chỉ
mở cho bài đã qua gate verify, và đừng để trong thư mục giao hàng thứ gì không
thuộc bài.

## Bắt buộc: đọc lại Doc sau khi dựng

Script in ra link **không** chứng minh Doc đúng. Đọc lại rồi mới giao:

```bash
GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws" command gws docs documents get \
  --params '{"documentId":"{DOC_ID}"}' --format json 2>/dev/null \
  | python3 -c '
import sys, json
d = json.load(sys.stdin)
print("inlineObjects:", len(d.get("inlineObjects", {})))
for el in d["body"]["content"]:
    p = el.get("paragraph")
    if not p: continue
    ps = p.get("paragraphStyle", {})
    label = ps.get("namedStyleType", "?") + ("/" + ps.get("alignment", "") if ps.get("alignment") else "")
    txt = ""; imgs = 0; links = []
    for r in p.get("elements", []):
        tr = r.get("textRun")
        if tr:
            txt += tr.get("content", "")
            u = tr.get("textStyle", {}).get("link", {}).get("url")
            if u: links.append((tr["content"], u))
        if r.get("inlineObjectElement"): imgs += 1
    print("[%s] img=%d %s" % (label, imgs, txt.strip()[:60]))
    for a, u in links: print("    LINK %r -> %s" % (a, u))'
```

Kiểm 4 thứ: `inlineObjects` bằng số ảnh, có đúng 1 HEADING_1, link neo đúng cụm
từ, caption ở dòng `NORMAL_TEXT/CENTER` ngay dưới ảnh.

## Vì sao dựng Doc native chứ không upload HTML rồi để Drive convert

Đo ngày 17/09/2026 trên cùng một bài, cùng ảnh:

| | Native `batchUpdate` | Upload HTML để Drive convert |
| --- | --- | --- |
| Cấu trúc heading/link/ảnh | Đúng | Đúng |
| Kích thước Doc | 22.8 KB | 42.9 KB |
| Paragraph dính style thừa | 7 (toàn style cố ý đặt) | 14 — **mọi đoạn** bị nhét `borderBottom`, `borderBetween`, padding |

Đường convert nhét viền và padding vô hình vào từng đoạn. Bên báo mở ra áp style
của họ là đống đó chọi nhau. Nên skill này chỉ dùng native.

## Quirk của gws cần nhớ

- `drive files create --upload` **chỉ nhận file trong thư mục hiện tại**. Helper
  `drive +upload` thì nhận đường dẫn tuyệt đối — `gws_helper.upload_file()` dùng
  helper vì lý do này.
- `gws` in `Using keyring backend: keyring` ra stderr; `gws_helper` đã lọc.
- Luôn dùng dạng `GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$HOME/.config/gws" command gws`,
  không dùng `gws` trần.

## Thư mục cha: hỏi user từng lần

**Không có thư mục cha mặc định.** Mỗi bài user đưa một thư mục. Thiếu thì hỏi,
đừng đoán và đừng dùng lại thư mục của bài trước.

## Không tự làm những việc này

Mở link-share cho Doc và thư mục giao hàng là việc đã được chốt, cứ làm. Ngoài
đó ra thì dừng và hỏi user:

- Gửi Doc cho bên báo, gửi mail, hay đăng bài.
- Thêm email cụ thể vào quyền của file.
- Mở share cho file nguồn, `article.json`, hay evidence file của gate verify.

Skill dừng ở chỗ đưa link cho user.
