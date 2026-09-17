# mwg-agent-skill

Agent skills dùng lại được cho SEO và content ops, viết cho Claude Code và các
runtime tương thích (Codex, Antigravity, Gemini CLI).

Mỗi skill là một thư mục có `SKILL.md` (chỉ dẫn) và tuỳ chọn `scripts/`,
`references/`. Runtime đọc `SKILL.md` khi mô tả khớp với việc người dùng đang làm.

## Skill trong repo

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`onpage-cms-product-link-insert`](skills/onpage-cms-product-link-insert) | Chèn hàng loạt một câu kèm internal link vào đoạn văn có sẵn của bài sản phẩm trên CMS, splice trên string thô và verify byte-exact | Node (để chạy test), một tab CMS đã đăng nhập |
| [`batch-llm-skill`](skills/batch-llm-skill) | Đẩy CSV/JSONL qua batch API của OpenAI / Gemini để phân loại, trích xuất, tóm tắt — có ước tính chi phí và cổng xác nhận trước khi submit | Python, `OPENAI_API_KEY` hoặc `GEMINI_API_KEY` |
| [`image-seo-pipeline`](skills/image-seo-pipeline) | Nén ảnh, sinh alt text/metadata bằng Gemini, bắn EXIF, ghi CSV metadata | Python, ImageMagick (`magick`), `exiftool`, `GEMINI_API_KEY` |
| [`seo-keyword-research`](skills/seo-keyword-research) | Research keyword bằng Ahrefs API với bộ lọc intent nghiêm ngặt (tách general/product intent khỏi blog/specs/SKU) | `AHREFS_API_KEY` |
| [`seo-skill-sync`](skills/seo-skill-sync) | Đồng bộ skill một chiều từ surface canonical ra các surface khác và kiểm parity | Node |
| [`tgdd-bai-pr-bao-ngoai`](skills/tgdd-bai-pr-bao-ngoai) | Viết bài PR đăng báo (booking PR) giọng kể chuyện 800-1000 chữ, rồi giao ra một thư mục Drive có Google Doc rich text (ảnh inline, link click được) — kèm linter và một gate fact-check bắt buộc | Python, ImageMagick, `gws` CLI |
| [`seo-gsc-rank-check`](skills/seo-gsc-rank-check) | Lấy thứ hạng keyword từ Google Search Console, chọn URL tốt nhất theo impressions, ghi ngược vào Google Sheet bất kỳ (mọi cột là tham số CLI) | Python, `gws` CLI, MCP `google-search-console` |
| [`content-html-optimizer`](skills/content-html-optimizer) | Tối ưu HTML bài viết: xếp ảnh vào đúng section, điền alt/title/caption, chèn internal link từ Google Sheet với chống trùng và chống cắt chữ | Python, `gws` CLI |
| [`image-ai-generate`](skills/image-ai-generate) | Sinh ảnh minh hoạ cho bài bằng OpenAI image API, dùng ảnh sản phẩm làm reference, resize và đóng logo | Python, `OPENAI_API_KEY` |
| [`tgdd-infobox-nganh-hang`](skills/tgdd-infobox-nganh-hang) | Viết/audit Infobox cho trang ngành hàng tổng | — |
| [`tgdd-infobox-nganh-hang-hang`](skills/tgdd-infobox-nganh-hang-hang) | Viết/audit Infobox cho trang ngành hàng + hãng | — |
| [`tgdd-infobox-nganh-hang-thuoc-tinh`](skills/tgdd-infobox-nganh-hang-thuoc-tinh) | Viết/audit Infobox cho trang ngành hàng + thuộc tính | — |
| [`tgdd-infobox-dong-san-pham`](skills/tgdd-infobox-dong-san-pham) | Viết/audit Infobox cho trang ngành hàng + dòng sản phẩm | — |
| [`tgdd-review-outline-infobox`](skills/tgdd-review-outline-infobox) | Chấm outline Infobox và so với outline đối thủ để tìm chỗ còn thiếu | — |


4 skill `tgdd-infobox-*` và `tgdd-review-outline-infobox` là **bộ rule biên tập**,
không có script — chúng viết cho ngành hàng và văn phong thương mại điện tử Việt
Nam, dùng được nhất khi bạn sửa lại cho site của mình.

### Biến môi trường

Vài skill đọc Google Sheet của riêng bạn. Không có ID nào hardcode; script dừng
kèm thông báo nếu thiếu biến:

| Biến | Skill dùng |
| --- | --- |
| `SHEET_ALL_KW_ID`, `SHEET_BAI_TIN_ID` | `content-html-optimizer` |
| `SPREADSHEET_ID` | `image-ai-generate` |
| `GWS_EXPECTED_ACCOUNT` | `tgdd-bai-pr-bao-ngoai` (chốt chặn ghi nhầm tài khoản; bỏ trống thì bỏ qua kiểm) |

## Cài

Chép thư mục skill bạn cần vào surface của runtime:

```bash
git clone https://github.com/<owner>/mwg-agent-skill.git
cp -R mwg-agent-skill/skills/onpage-cms-product-link-insert ~/.claude/skills/
```

Hoặc cài vào scope dự án: `<repo>/.claude/skills/`.

### Dùng cho nhiều surface cùng lúc

`seo-skill-sync` fan-out từ một bản canonical ra các surface còn lại, nên bạn chỉ
sửa một chỗ:

```bash
cp -R mwg-agent-skill/skills/* .claude/skills/
node .claude/skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --apply
node .claude/skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --check
```

Mặc định ghi ra `.codex/skills`, `.agents/skills`, `.gemini/skills`. Đổi bằng
`--canonical`, `--targets`, `--prefixes`, `--root`. Script **chỉ ghi một chiều** —
không có đường sync ngược về canonical, và không bao giờ xoá file (`ORPHAN` chỉ
được báo).

## Trước khi chạy skill ghi dữ liệu

`onpage-cms-product-link-insert` **sửa nội dung production**. Nó được viết với
giả định là hệ CMS không rollback được, nên có sẵn các cổng chặn: backup từng bài
trước khi ghi, 6 bất biến phải xanh hết mới POST, đọc lại sát trước khi ghi để
không đè người đang sửa tay, và verify byte-exact sau khi ghi.

Đừng bỏ các cổng đó để chạy nhanh hơn. Chạy `dryRun: true` một lô nhỏ trước.

Skill này mô tả hợp đồng endpoint của một CMS nội bộ. Nó **không** chứa
credential và không tự đăng nhập — phải có sẵn một phiên đăng nhập hợp lệ do bạn
tự mở.

## Cấu hình

Không skill nào chứa key. Tất cả đọc từ biến môi trường:

| Biến | Dùng bởi |
| --- | --- |
| `OPENAI_API_KEY` | `batch-llm-skill` |
| `GEMINI_API_KEY` | `batch-llm-skill`, `image-seo-pipeline` |
| `AHREFS_API_KEY` | `seo-keyword-research` |

## Test

```bash
node skills/onpage-cms-product-link-insert/scripts/test-runner-logic.mjs
```

19 assert cho phần logic thuần: định vị đoạn qua markup lồng và HTML entity, bọc
anchor chồng tiền tố, 6 bất biến, và 3 nhánh chẩn đoán khi không chèn được.
Không cần mạng, không đụng CMS.

## Ghi chú về ngôn ngữ

Phần lớn `SKILL.md` viết bằng tiếng Việt vì đó là ngôn ngữ làm việc của nhóm tạo
ra chúng. Script và tên biến bằng tiếng Anh.

## License

MIT — xem [LICENSE](LICENSE).
