---
name: content-laptop-product
description: "Viết, tối ưu và làm hình bài Content SP (product_articles) + đặc điểm nổi bật (key_features) cho SP nhóm Laptop của TGDĐ: laptop, máy tính để bàn, màn hình máy tính, máy in, phần mềm. Mode: --full (viết + hình + lint), --write (chỉ viết), --image (chỉ làm hình từ ảnh gallery thật, không AI, nhiều bố cục chống đơn điệu, kiểm điểm ảnh SP y nguyên), --optimize (nâng cấp bài đang có), --audit (chỉ chấm), --variant (bài cho bản anh em từ bài đã duyệt), --publish (ghi PIM khi owner bảo). Thông số lấy từ PIM và trang hãng, lint thông số/link/từ cấm/hedge số hãng. Trigger: viết content SP, viết bài sản phẩm, bài thông tin sản phẩm, product_articles trống, tối ưu bài SP, renew bài SP, chấm bài content SP, nghiệm thu order Content SP, key_features, đặc điểm nổi bật, làm hình content SP, hình bài sản phẩm, ảnh 1020x570, thay nền ảnh laptop, bắn text lên ảnh SP, hình không biến dạng sản phẩm."
user-invocable: true
when_to_use: "Khi owner tự viết/tối ưu/làm hình nội dung bài viết sản phẩm (Thông tin sản phẩm) cho SP Laptop/PC/màn hình/máy in/phần mềm thay vì order Content SP, hoặc chấm bài order về. Không dùng cho infobox ngành hàng/hãng/dòng (tgdd-infobox-*), bài Top N (tgdd-top-product-article), bài Hỏi Đáp (viet-blog), ảnh infobox/blog (image-ai-generate, image-seo-pipeline)."
argument-hint: "--full|--write|--image|--optimize|--audit|--variant|--publish <URL trang SP>"
category: content
keywords: [content-sp, product_articles, key_features, pim, laptop, bai-san-pham, image, 1020x570]
metadata:
  version: "2.1.0"
  workspace: mwg-ai-worker
  chot: "02/11/2026"
---

# Content SP nhóm Laptop: viết, tối ưu, làm hình

Đầu ra mặc định là **bản nháp** trong task folder để owner duyệt. Chỉ mode `--publish` ghi hệ thống thật, và chỉ khi owner nói ghi. Không gọi API tốn tiền, không dùng AI sinh/sửa ảnh SP.

Gộp từ `content-sp-laptop-viet-bai` + `image-sp-content-composer` (02/11/2026).

## Chọn mode

Không ghi mode: SP chưa có bài → `--full`; đã có bài → `--optimize`. Hỏi owner khi không rõ.

| Mode | Làm gì | Bước (mục Quy trình) | Ra |
|---|---|---|---|
| `--full` | Viết bài + key_features, làm 3–5 hình, ráp hình vào nháp, lint | 1→7, 8, 9 | nháp HTML + hình + report |
| `--write` | Chỉ viết bài + key_features, để `<!-- ANH: ... -->` chỗ cần hình | 1→7, 9 | nháp HTML + report |
| `--image` | Làm hình cho bài đã có (nháp đã lint hoặc bài live) | 1, 8, 9 | hình + report verify |
| `--optimize` | Nâng cấp bài đang chạy: giữ ý đúng, sửa lỗi lint, bù phần thiếu (box, FAQ, bảng, mục khuôn), có thể kèm hình | 1→7 theo **Mode optimize**, tuỳ chọn 8 | nháp mới + bảng thay đổi trước/sau |
| `--audit` | Chỉ chấm bài (của mình hoặc order Content SP trả về), không viết lại | 1, 2, 6 + đọc tay theo khuôn | bảng lỗi theo mức |
| `--variant` | Bài cho bản anh em (016VN → 017VN) từ bài đã duyệt, chỉ đổi phần khác trong PIM | theo **Mode variant** | nháp + lint với facts riêng |
| `--publish` | Ghi PIM `product_articles`/`key_features` + upload ảnh, đọc lại so byte | theo **Mode publish** | WRITTEN + backup |

Mode ghép được: `--optimize --image`, `--variant --publish`...

## Quy trình

1. **Task**: tìm initiative/work item đang có trong `tasks/`; chưa có thì `seo-task-create`. Nháp, hình, evidence nằm trong `tasks/{task}/data/processed/` và `reports/`.
2. **Hiện trạng**: `node .claude/skills/onpage-mdm-khai-bao/scripts/mdm-cli.mjs pim-find --url /<ngành>/<slug>` ra model, lá màu, độ dài bài. Bài đang hiển thị: `scripts/fetch-live-article.py URL --out-dir DIR` (public, không auth; bỏ div bọc khi đối chiếu).
3. **Thông số**: đọc `references/nguon-du-lieu-va-fact-check.md`. Lập `facts-<sp>.json` (`must`, `must_not`, `hedge_numbers`) từ PIM `rawValues` + bảng hãng. PIM, web, hãng mâu thuẫn thì **không viết**, ghi câu hỏi cho owner/IT.
4. **Dàn bài**: khuôn đúng ngành ở `references/khuon-theo-nganh-hang.md`. Mọi bài có **box Đặc điểm nổi bật ở đầu**, **FAQ 2–4 câu có giá trị ở cuối**, **bảng so sánh** khi có bản/model tương đương trong line-up: `references/box-bang-so-sanh-faq.md`.
5. **Viết** theo `references/van-phong-va-quy-tac-html.md` và `references/ke-thua-tu-viet-blog-va-infobox.md`. Điểm bắt đầu: `templates/product-articles-vi-du-msi-016vn.html` (thay hết thông số MSI).
6. **Lint**: `python3 .claude/skills/content-laptop-product/scripts/lint-product-article.py BAI.html --category <ngành> --url /<ngành>/<slug> --facts facts.json`. Sửa hết ERROR, WARN thì đọc rồi quyết.
7. **Link nội bộ**: URL đích trả 200 (`curl -I`); loại KW và anchor theo `chen-link-noi-bo`. Nháp chỉ giữ link tối thiểu đã kiểm.
8. **Hình**: theo `references/lam-hinh.md`: chọn ảnh gallery theo mục, mỗi hình một bố cục (`hero`, `left/right`, `multi`, `zoom`, `strip`), chữ/màu theo bộ hình AI infobox (`--headline`, `--sub`, `--tag`, `*nhấn vàng*`), dựng bằng `scripts/compose-sp-image.py`, kiểm từng hình bằng `scripts/verify-sp-fidelity.py`, kiểm cả bộ bằng `scripts/check-image-set.py`, rồi nhìn bằng mắt. Ráp vào nháp: `<!-- ANH: <file> | <mục> -->` ngay sau đoạn đầu của mục.
9. **Giao**: `{ma}-product-articles-nhap.html`, `{ma}-key-features-nhap.html`, hình + report verify, kết quả lint, danh sách mục chờ owner/IT. Cập nhật `reports/` và `resume-brief` của task.

### Mode optimize

- Bản gốc: lưu bài hiện tại (bước 2) vào `data/raw/{ma}-product-articles-truoc-{yymmdd}.html`, không sửa file này.
- Lint bản gốc trước (bước 6) để có danh sách lỗi. Đối chiếu với khuôn (bước 4): thiếu box, FAQ, bảng so sánh, mục nào.
- Giữ câu đúng và có nguồn; sửa câu sai thông số, từ cấm, giọng báo cáo; bù phần thiếu. Không viết đè mù.
- Ra nháp mới + bảng thay đổi (vị trí, trước, sau, lý do/nguồn). Sửa ít chỗ thì đề xuất ghi bằng `product-ops` (sửa từng chỗ, guard sha256) thay vì thay nguyên bài.

### Mode audit

Chỉ đọc. Lint + đọc tay theo khuôn, phép thử FAQ và các luật dưới. Ra bảng `mức (ERROR/WARN/gợi ý) | vị trí | lỗi | sửa thế nào | nguồn`. Bài order Content SP trả về thì chấm như nghiệm thu: thông số sai là lỗi chặn.

### Mode variant

Từ bài **đã duyệt** của bản A ra bài bản B cùng dòng: lấy PIM bản B, lập `facts-B.json` với thông số bản A vào `must_not` (trừ mục so sánh), sửa đúng các chỗ khác nhau (RAM, màn hình...), đổi self-link, tên, mã, câu mở bài và box. Header bảng so sánh giữ tên đầy đủ hai bản. Lint với facts B; số khác biệt phải khớp PIM bản B. Hình dùng chung gallery thì không nói khác biệt bằng hình.

### Mode publish

Chỉ chạy khi owner nói ghi, cho đúng bản nháp owner đã duyệt. Dùng skill `onpage-mdm-khai-bao`:
1. Ảnh: `upload --file IMG --task-dir T` (xem plan) rồi `--live`; thay `<!-- ANH -->` bằng markup chuẩn với URL CDN trả về; lint lại.
2. Bài: `product-write --url /<ngành>/<slug> --task-dir T --set-file product_articles=bai.html --set-file key_features=kf.html` chạy thử, đọc plan, rồi `--live` (backup, ghi, đọc lại so từng byte). SP có biến thể ghi mọi lá màu của trang.
3. Nghiệm thu trang live (bài lên trễ ~15 phút, xem memory PIM) và ghi report.

## Không thương lượng

- Mỗi con số thông số truy được về PIM hoặc trang hãng. Số hiệu năng AI/game/pin hãng công bố ghi "theo hãng/theo NVIDIA/theo thông số công bố", kể cả chữ trên hình.
- Không giá, quà, khuyến mãi trong bài và trên hình. Không "mạnh nhất/số 1/đầu tiên" khi không có nguồn. Không xưng "tôi".
- Số cổng, bộ nhớ, thẻ nhớ mà PIM, web, hãng lệch nhau: viết mô tả không kèm số cho tới khi chốt.
- Không kết luận game x86 chạy tốt trên máy chip Arm khi chưa có nguồn kiểm.
- Bài là nội dung của **một model**; so sánh bản anh em chỉ nêu khác biệt có trong PIM. Header bảng so sánh ghi tên đầy đủ kèm mã máy, không ghi "(bản này)".
- FAQ không hỏi điều đọc được ngay từ thông số, không hỏi chung chung, không trả lời bằng ước tính. Không có chứng cứ chắc chắn thì bỏ câu, ghi vào report.
- Hình: điểm ảnh SP chỉ từ gallery thật, chỉ co đều; mỗi hình phải qua `verify-sp-fidelity.py`; một bài không 2 hình cùng bố cục.

## Đã kiểm chứng

- Khuôn rút từ 52 bài live (report `tasks/261028-plan-seo-msi-prestige-n16-flip-rtx-spark/work-items/261030-skill-content-sp-laptop/reports/261030-1100-mau-chung-content-sp-laptop.md`). Nháp MSI Prestige N16 Flip AI+ 016VN/017VN lint ĐẠT; lint bắt được RAM sai khi cố ý đổi.
- Bộ 5 hình 016VN, 5 bố cục khác nhau, chữ và màu theo bộ hình AI infobox (Avenir Next, vàng #F9C80B, mục đánh số, thanh đáy xanh đậm, không logo), verify ĐẠT cả 5 (02/11/2026, `.../data/processed/hinh-demo-v3/`). Verify bắt được 2 cách làm sai đã thử: xoá vùng trắng kín theo kích thước, tăng `--bg-tol` lên 70/100.
- Chưa thử: máy in, màn hình, PC, phần mềm; SP màu trắng/bạc; mode optimize/audit/variant/publish trên bài thật.
