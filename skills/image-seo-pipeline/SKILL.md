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
  Trigger khi user muốn xử lý/tối ưu hình ảnh cho một content workspace.
  Áp dụng cho bất kỳ thư mục bài viết nào có images-original/ cần chuẩn hóa SEO.
  KHÔNG dùng cho resize đơn lẻ hay chỉnh sửa ảnh sản phẩm trực tiếp lên CMS.
category: content-ops
keywords: [image-seo, alt-text, exif, metadata, infobox, kebab, ImageMagick, Gemini]
metadata:
  author: mwg-agent-skill
  version: "2.0.0"
---

# image-seo-pipeline

Pipeline tối ưu hình ảnh chuẩn SEO cho bài viết/infobox TGDĐ.

## Scope

Skill này chỉ xử lý ảnh trong một content workspace `{workspace_path}/` có sẵn
thư mục `images-original/`.
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

1. Xác định `workspace_path` — thư mục chứa `images-original/` của bài.
2. Kiểm tra `images-original/` tồn tại và không rỗng.
3. Chạy script từ root workspace:
   ```bash
   python3 skills/image-seo-pipeline/scripts/process_images.py \
     --workspace {workspace_path}
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
Không nhận API key qua argument — dùng `GEMINI_API_KEY` env hoặc ADC.
