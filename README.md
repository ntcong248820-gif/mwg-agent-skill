# mwg-agent-skill

Agent skills dùng lại được cho SEO và content ops, viết cho Claude Code và các
runtime tương thích (Codex, Antigravity, Gemini CLI).

Mỗi skill là một thư mục có `SKILL.md` (chỉ dẫn) và tuỳ chọn `scripts/`,
`references/`. Runtime đọc `SKILL.md` khi mô tả khớp với việc người dùng đang làm.

## Danh mục Skill (54 skills)

### Hệ CMS & MDM/PIM (Tạo bài, Air, Khai báo, Sửa nội dung)

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`content-cms-blog`](skills/content-cms-blog) | Một cửa tương tác NEW CMS (`newcms.thegioididong.com`) cho Hỏi Đáp & Game App: tạo, cập nhật, up ảnh, đổi thumb, hẹn giờ xuất bản | Node 18+, Token Bearer NEW CMS |
| [`onpage-mdm-khai-bao`](skills/onpage-mdm-khai-bao) | Khai báo SEO trên MDM/PIM (thay CMS) cho Danh mục, Hãng, Filter/Dòng filter, Sản phẩm PIM; token Keychain 30 ngày | Node 18+, DevTools MCP, tab MDM |
| [`content-cms-air-infobox`](skills/content-cms-air-infobox) | Đăng bài Infobox lên CMS TGDĐ (trang Filter/Dòng qua News CMS, trang Hãng qua ManufactureEdit) | Node 18+, tab CMS đã đăng nhập |
| [`onpage-cms-product-content`](skills/onpage-cms-product-content) | Can thiệp hàng loạt mục bài viết sản phẩm CMS: insert-link hoặc apply-ops có sha256 protection | Node 18+, tab CMS đã đăng nhập |
| [`onpage-cms-news-insert`](skills/onpage-cms-news-insert) | Chèn câu kèm internal link hoặc biên tập nội dung bài Tin tức/Kinh nghiệm hay/Tekzone trên CMS | Node 18+, tab CMS đã đăng nhập |
| [`onpage-cms-product-link-insert`](skills/onpage-cms-product-link-insert) | Chèn hàng loạt một câu kèm link vào đoạn văn bài sản phẩm trên CMS cũ, verify byte-exact | Node (để chạy test), tab CMS |
| [`cms-content-create`](skills/cms-content-create) | *(Legacy)* Tạo bài Hỏi Đáp / Game App trên CMS cũ (chuyển tiếp sang content-cms-blog) | Node 18+, chrome-profile |
| [`cms-faq-tao-bai`](skills/cms-faq-tao-bai) | *(Legacy)* Tạo bài Hỏi Đáp mới trên CMS TGDĐ cũ | Node 18+, chrome-profile |
| [`cms-topzone-tao-bai`](skills/cms-topzone-tao-bai) | *(Legacy)* Tạo bài CMS V2 TopZone (siteId=16) | Node 18+, chrome-profile |
| [`content-cms-air-hoidap`](skills/content-cms-air-hoidap) | *(Legacy)* Air/cập nhật bài Hỏi Đáp CMS cũ | Node 18+, tab CMS |

### Viết bài & Tối ưu Content

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`blog-hoi-dap-tron-goi`](skills/blog-hoi-dap-tron-goi) | Quy trình trọn gói 1 bài blog Hỏi Đáp: viết bài, làm hình (thumb + bài), up NEW CMS, hẹn giờ 02:00, ghi sheet | Node 18+, Python, Google Workspace CLI, NEW CMS token |
| [`viet-blog`](skills/viet-blog) | Viết blog Hỏi Đáp TGDĐ bằng AI agent: research SERP, outline 13 dạng, viết, QC số liệu, shortcode, dựng HTML | Python 3.9+, Google Workspace CLI, HOI_DAP_SHEET_ID |
| [`viet-infobox-apple`](skills/viet-infobox-apple) | Chuẩn viết/biên tập infobox Apple theo format TGDD và quy trình trọn gói infobox Hãng/Filter trên PIM/MDM | Node 18+, Python 3.9+, onpage-mdm-khai-bao |
| [`content-laptop-product`](skills/content-laptop-product) | Viết, tối ưu và làm hình bài Content SP + đặc điểm nổi bật cho nhóm Laptop TGDĐ | Python 3.9+, Google Workspace CLI, Pillow |
| [`tgdd-top-product-article`](skills/tgdd-top-product-article) | Viết mới hoặc renew bài Top N sản phẩm TGDĐ/ĐMX: verify còn kinh doanh, HTML CMS, 21 validate checks | Python 3.9+, BeautifulSoup |
| [`tgdd-seo-title-description`](skills/tgdd-seo-title-description) | Viết, chỉnh sửa, kiểm tra và điền SEO Title/Meta Description cho TGDD/ĐMX (Evergreen và CTA mạnh) | Python 3.9+, Google Workspace CLI |
| [`content-seo-semantic-pipeline`](skills/content-seo-semantic-pipeline) | Viết trọn bài SEO semantic theo quy trình 5 bước tab Thầy (brief -> semantic/outline -> viết -> tối ưu -> soát 7 checklist) | AI agent |
| [`content-seo-semantic-outline`](skills/content-seo-semantic-outline) | Lên bộ Semantic/LSI keyword và dàn bài SEO Final (AIDA, FAB, phân bổ LSI theo H2/H3) | AI agent |
| [`content-seo-semantic-audit`](skills/content-seo-semantic-audit) | Soát và chấm bài SEO semantic: lint đếm từ/từ khoá/brand, coverage, rà LSI, 7 checklist bởi 3 giám khảo | AI agent |
| [`tgdd-bai-pr-bao-ngoai`](skills/tgdd-bai-pr-bao-ngoai) | Viết bài báo PR (booking PR) đăng báo ngoài (VnExpress, Kenh14...) giọng reviewer, Google Doc rich text inline | Python, ImageMagick, Google Workspace CLI |

### Bộ Rule Infobox TGDD

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`tgdd-infobox-nganh-hang`](skills/tgdd-infobox-nganh-hang) | Viết/audit Infobox cho trang NGÀNH HÀNG tổng (Laptop, Điện thoại, Máy in...) | — |
| [`tgdd-infobox-nganh-hang-hang`](skills/tgdd-infobox-nganh-hang-hang) | Viết/audit Infobox cho trang NGÀNH HÀNG + HÃNG (Laptop Asus, Điện thoại Samsung...) | — |
| [`tgdd-infobox-nganh-hang-thuoc-tinh`](skills/tgdd-infobox-nganh-hang-thuoc-tinh) | Viết/audit Infobox cho trang NGÀNH HÀNG + THUỘC TÍNH (Laptop Gaming, Điện thoại 5G...) | — |
| [`tgdd-infobox-dong-san-pham`](skills/tgdd-infobox-dong-san-pham) | Viết/audit Infobox cho trang NGÀNH HÀNG + DÒNG SẢN PHẨM (MacBook Pro, Galaxy S...) | — |
| [`tgdd-review-outline-infobox`](skills/tgdd-review-outline-infobox) | Review, audit và so sánh outline Infobox với đối thủ để tìm cách lên Top | — |

### Tối ưu HTML, Ảnh & Liên kết nội bộ

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`content-html-optimizer`](skills/content-html-optimizer) | Tối ưu HTML bài viết/infobox: xếp ảnh theo section, điền alt/title, chèn internal link chống trùng/cắt chữ, chuẩn hóa table/heading | Python 3.9+, Google Workspace CLI |
| [`image-seo-pipeline`](skills/image-seo-pipeline) | Nén ImageMagick quality 85, gọi Gemini API sinh alt text, bắn EXIF (Copyright TGDD), xoay vòng key pool | Python, ImageMagick, exiftool, GEMINI_API_KEY |
| [`image-ai-generate`](skills/image-ai-generate) | Tạo ảnh minh họa AI cho bài viết bằng OpenAI Image API, giữ thiết kế SP thật, resize 1200x675 hoặc 800x450, đóng logo TGDD | Python, OPENAI_API_KEY |
| [`chen-link-noi-bo`](skills/chen-link-noi-bo) | Rule + quy trình chèn internal link bài content tĩnh TGDD/DMX/TopZone theo 5 loại KW, nguồn tra All KW | Python 3.9+, Google Workspace CLI, SHEET_ALL_KW_ID |
| [`onpage-internal-link`](skills/onpage-internal-link) | Đề xuất chèn internal link bài Hỏi đáp/Game App/Kinh nghiệm hay: crawl live, chọn đúng đoạn liên quan, viết mention | Python (bs4), Google Workspace CLI |

### Phân tích SEO, GSC, GA4 & Báo cáo

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`seo-gsc-category-review`](skills/seo-gsc-category-review) | Review Google Search Console theo ngành hàng, nhóm URL, keyword cluster 7d/28d, tách riêng SP ngừng kinh doanh | Python 3.9+, GSC MCP |
| [`seo-gsc-compare`](skills/seo-gsc-compare) | So sánh GSC 2 kỳ cho URL bất kỳ: top keyword, clicks, impressions, position | Python 3.9+, GSC MCP |
| [`seo-gsc-rank-check`](skills/seo-gsc-rank-check) | Đo thứ hạng keyword từ GSC cho thegioididong.com và dienmayxanh.com, ghi ngược Google Sheet | Python 3.9+, Google Workspace CLI, GSC MCP |
| [`seo-ga4-organic-check`](skills/seo-ga4-organic-check) | Đối chiếu GA4 Organic Search sessions với GSC clicks cho nhóm landing page | Python 3.9+, GA4 MCP |
| [`seo-keyword-research`](skills/seo-keyword-research) | Research keyword Ahrefs API tiết kiệm units, lọc keep/review/drop theo intent từng dạng trang | Python 3.9+, AHREFS_API_KEY |
| [`seo-datastudio-dashboard`](skills/seo-datastudio-dashboard) | Đọc, dựng và sửa dashboard Data Studio / Looker Studio bằng RPC nội bộ tab Chrome: chart, filter, calculated field | Node 18+, chrome-profile, DevTools MCP |
| [`seo-action-impact-review`](skills/seo-action-impact-review) | Nghiệm thu hiệu quả action SEO đã làm bằng GSC (clicks/CTR/rank 3 kỳ) | Python 3.9+, Google Workspace CLI, GSC MCP |
| [`seo-cso-optimize`](skills/seo-cso-optimize) | Tối ưu Content Sản Phẩm đẩy SEO danh mục: audit 5 tiêu chí bài viết SP, log Data Order | Python 3.9+, Google Workspace CLI |

### Vận hành Task & Workflow Agent

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`seo-task-create`](skills/seo-task-create) | Tạo task SEO local (initiative, work_item, single); scaffold README, registry, workstream | Python 3.9+ |
| [`seo-task-done`](skills/seo-task-done) | Đóng task SEO local, cập nhật status, Results, registry, report sync | Python 3.9+ |
| [`seo-task-journal-sync`](skills/seo-task-journal-sync) | Cập nhật journal task SEO sau khi làm việc (Current State, Next Steps, reports index) | Python 3.9+ |
| [`seo-task-state-audit`](skills/seo-task-state-audit) | Audit trạng thái toàn bộ task SEO local: frontmatter, report sync, registry parity | Python 3.9+ |
| [`seo-weekly-action-plan`](skills/seo-weekly-action-plan) | Sinh plan action SEO tuần từ view sheet system, xuất job list cho multi-agent crew | Python 3.9+, Google Workspace CLI |
| [`seo-daily-reporter`](skills/seo-daily-reporter) | Báo cáo task hàng ngày SEO MWG: annotate trạng thái hôm qua, đề xuất 3+2 task hôm nay | Python 3.9+, Google Workspace CLI |
| [`seo-log-cv`](skills/seo-log-cv) | Ghi File 1 / CV tuần chi tiết: giờ làm, số lượng, note, link nghiệm thu | Python 3.9+, Google Workspace CLI |
| [`seo-log-weekly-work`](skills/seo-log-weekly-work) | Ghi File 2 / Công việc TGDD: tổng hợp tuần/tháng theo hạng mục, hiệu quả nối về ranking/traffic | Python 3.9+, Google Workspace CLI |
| [`seo-attendance-keo-cong`](skills/seo-attendance-keo-cong) | Báo cáo kéo công MWG: review File 1, điền bảng minh chứng, soạn tin nhắn xác nhận | Python 3.9+, Google Workspace CLI |
| [`seo-work-efficiency-review`](skills/seo-work-efficiency-review) | Review hiệu quả làm việc theo kỳ từ giờ bấm công việc, phân tích thời gian và điểm nghẽn | Python 3.9+ |
| [`seo-skill-sync`](skills/seo-skill-sync) | Đồng bộ skill một chiều từ surface canonical (.claude) ra các surface khác và kiểm parity | Node 18+ |
| [`seo-new-product`](skills/seo-new-product) | Dựng file Plan SEO cho nhóm sản phẩm mới từ danh sách order, copy file mẫu, điền keyword | Python 3.9+, Google Workspace CLI |
| [`seo-mo-ta-task-it`](skills/seo-mo-ta-task-it) | Soạn mô tả task gửi IT đúng format SEO MWG: khung A/B/C, tiêu chí nghiệm thu, dựng Google Doc | Python 3.9+, Google Workspace CLI |

### Công cụ Hỗ trợ & Khác

| Skill | Làm gì | Cần gì |
| --- | --- | --- |
| [`batch-llm-skill`](skills/batch-llm-skill) | Đẩy CSV/JSONL qua batch API của OpenAI / Gemini để phân loại, trích xuất, tóm tắt kèm pool xoay vòng key | Python, OPENAI_API_KEY hoặc GEMINI_API_KEY |
| [`chrome-profile`](skills/chrome-profile) | Mở URL trên đúng profile Google Chrome thật qua CLI chrome-profile + token DevTools MCP | Python 3.9+, Google Chrome |
| [`fable-thinking`](skills/fable-thinking) | Quy trình suy luận đa giả định (Floor check, Constraint Loop, evidence-based) | — |

## Biến môi trường

Các skill đọc cấu hình từ biến môi trường, không hardcode ID hay token:

| Biến | Ý nghĩa |
| --- | --- |
| `OPENAI_API_KEY`, `GEMINI_API_KEY` | Key gọi LLM API / Image API |
| `AHREFS_API_KEY` | Key gọi Ahrefs keyword API |
| `SHEET_ALL_KW_ID`, `SHEET_BAI_TIN_ID` | Sheet kho từ khóa All KW và kho link bài tin |
| `HOI_DAP_SHEET_ID`, `SHORTCODE_SHEET_ID` | Sheet quản lý bài Hỏi Đáp và kho shortcode |
| `MDM_CONFIG`, `MDM_TOKEN_CACHE` | Cấu hình endpoint PIM/MDM (`mdm.config.json`) và cờ cache token Keychain |
| `CMS_CHROME_PROFILE` | Tên profile Chrome đã đăng nhập CMS |
| `DATASTUDIO_CHROME_PROFILE` | Tên profile Chrome có quyền sửa Looker Studio |

## Cài đặt

Chép thư mục skill bạn cần vào surface của runtime:

```bash
git clone https://github.com/ntcong248820-gif/mwg-agent-skill.git
cp -R mwg-agent-skill/skills/<ten-skill> ~/.claude/skills/
```

### Đồng bộ nhiều surface cùng lúc

Dùng `seo-skill-sync` để fan-out từ `.claude/skills` ra `.codex/skills`, `.agents/skills`, `.gemini/skills`:

```bash
node .claude/skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --apply
node .claude/skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --check
```

## Bảo mật & An toàn dữ liệu

Các skill can thiệp hệ thống CMS/PIM production (`content-cms-blog`, `onpage-mdm-khai-bao`, `onpage-cms-product-content`, `content-cms-air-infobox`) đều có cổng bảo vệ:
- Chạy `dryRun` mặc định trước khi ghi thật (`--live`).
- Backup bản ghi trước khi thay đổi.
- Khóa `rowVersion` và guard `sha256` chống ghi đè khi có người đang sửa tay.
- Đọc lại verify byte-exact sau khi submit.

## License

MIT — xem [LICENSE](LICENSE).
