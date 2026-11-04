---
name: image-seo-pipeline
description: >
  Tự động tối ưu hình ảnh cho bài viết/infobox TGDĐ: giữ nguyên tên file gốc (kebab-case .jpg),
  nén ImageMagick quality 85, gọi Gemini API sinh alt text & metadata tiếng Việt,
  bắn EXIF metadata (Author, Copyright = Thegioididong.com) vào file ảnh bằng
  exiftool, ghi image-metadata.csv. Chạy trực tiếp từ skill script path.
  Kích hoạt khi user yêu cầu: tối ưu ảnh, process images, viết alt text,
  nén ảnh infobox, sinh metadata ảnh, chạy pipeline hình, xử lý hình.
user-invocable: true
when_to_use: >
  Trigger khi user muốn xử lý/tối ưu hình ảnh cho một content workspace
  mwg-content-editor. Áp dụng cho các topic infobox laptop, màn hình, hoặc
  bất kỳ bài viết TGDĐ nào có images-original/ cần chuẩn hóa SEO.
  KHÔNG dùng cho resize đơn lẻ hay chỉnh sửa ảnh sản phẩm trực tiếp lên CMS.
category: content-ops
keywords: [image-seo, alt-text, exif, metadata, infobox, kebab, ImageMagick, Gemini]
metadata:
  author: mwg-ai-worker
  version: "2.0.0"
  workspace: mwg-ai-worker
---

# image-seo-pipeline

Pipeline tối ưu hình ảnh chuẩn SEO cho bài viết/infobox TGDĐ.

## Scope

Skill này chỉ xử lý ảnh trong `mwg-content-editor/content-workspaces/{topic-slug}/`.
Không xử lý ảnh sản phẩm CMS, không upload ảnh lên CDN, không sửa HTML source.

## Dependencies

Cần cài sẵn trên máy trước khi chạy:
- `exiftool` — ghi EXIF/IPTC vào file ảnh
- `ImageMagick` (lệnh `magick`) — nén ảnh
- Python venv với `google-genai`, `Pillow` — sinh metadata AI

Kiểm tra: `exiftool -ver && magick -version && python3 -c "from google import genai"`

## Script Path

```text
SKILL_DIR = .agents/skills/image-seo-pipeline/
SCRIPT    = .agents/skills/image-seo-pipeline/scripts/process_images.py
```

## Workflow

1. Xác định `workspace_path = mwg-content-editor/content-workspaces/{topic-slug}/`.
2. Kiểm tra `images-original/` tồn tại và không rỗng.
3. Chạy script từ root workspace:
   ```bash
   python3 .agents/skills/image-seo-pipeline/scripts/process_images.py \
     --workspace mwg-content-editor/content-workspaces/{topic-slug}
   ```
4. Script tự động:
   - Đọc `metadata/image-metadata.csv` để skip ảnh đã `status=done`.
   - Giữ nguyên tên file gốc (chuẩn hóa kebab-case, đuôi `.jpg`), KHÔNG đổi tên file bằng AI.
   - Gọi Gemini API sinh alt, title, description tiếng Việt chuẩn SEO.
   - Nén ảnh bằng `magick -quality 85 -strip` → `images-processed/`.
   - Bắn EXIF/IPTC bằng `exiftool`:
     - `Artist`, `By-line`, `Credit`, `Source`, `Copyright` = `Thegioididong.com`
     - `Title` / `ObjectName` = title sinh từ AI
     - `ImageDescription` / `Caption-Abstract` = alt text sinh từ AI
   - Ghi kết quả vào `metadata/image-metadata.csv`.
5. Report kết quả: số ảnh done, watch, skip.

## Output

```
images-processed/
  {original-name-stem}.jpg          ← giữ nguyên tên gốc, đã nén quality 85, có EXIF
metadata/
  image-metadata.csv               ← file-name, alt, title, description, source, status, notes
```

## Rules

- Giữ nguyên ảnh gốc trong `images-original/`, không overwrite.
- Giữ nguyên tên file gốc (kebab-case + `.jpg`), KHÔNG đặt lại tên file bằng AI và KHÔNG thêm chữ `fallback` vào tên file.
- Ảnh `status=done` trong CSV → skip hoàn toàn (incremental).
- Author cố định: `Thegioididong.com` (không nhận param khác).
- **Alt Text Invariant**: Mô tả trực quan hình ảnh. Tuyệt đối KHÔNG chứa các tiền tố "Hình ảnh...", "Ảnh...", "Hình ảnh minh họa...".
- **Description (Caption) Invariant**: Caption hiển thị dưới ảnh bài viết. Tuyệt đối KHÔNG chứa các câu meta như "Bài viết này sẽ...", "Bài viết giới thiệu...", "Hình ảnh giới thiệu...", "Hình ảnh minh họa...". Caption phải giải thích trực tiếp giá trị/tính năng sản phẩm.
- Sau khi chạy xong, agent báo cáo ngắn: tổng ảnh / đã done / cần review.

## Security

Skill chỉ đọc/ghi trong content-workspace được chỉ định.
Không đọc `.env`, không truy cập CDN, không tự động upload.
Không nhận API key qua argument — đọc từ env: `GEMINI_API_KEYS` (nhiều key, phân cách dấu phẩy), rồi `GEMINI_API_KEY`, rồi `GOOGLE_API_KEY`.

### Xoay key khi hết quota

`scripts/gemini_key_pool.py` giữ danh sách cặp (key, model) còn sống. Quota free tính theo
(project, model), và key tạo sau bị chặn `gemini-2.5-flash` / `2.5-flash-lite` ("no longer
available to new users"), nên pool loại theo **cặp**, không loại cả key:

- Hết quota ngày (`...PerDay...`) hoặc 404 model → bỏ cặp đó, sang cặp kế.
- 429 theo phút → nhảy cặp kế ngay; chỉ ngủ 35s khi cả vòng đều nghẽn.
- Key sai (`API key not valid`) → bỏ cả key.
- Chỉ khi **mọi** cặp đều chết mới rơi vào fallback `status=watch` (alt rác, phải chạy lại).

Log in `…xxxx` (4 ký tự cuối), không in key. Thêm key: sửa `GEMINI_API_KEYS` trong `~/.zshrc`.
