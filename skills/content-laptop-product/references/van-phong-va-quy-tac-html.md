# Văn phong và quy tắc HTML

## Văn phong
Rule chi tiết đã chốt của team (dấu câu, thuật ngữ, từ cấm) nằm ở `ke-thua-tu-viet-blog-va-infobox.md`. Dưới đây là phần riêng của bài SP.
- Ngôi thứ ba, giọng tư vấn rõ ràng, câu 15–30 từ. Không xưng "tôi", hạn chế "mình".
- Mỗi mục mở bằng thông số then chốt, rồi nói nó có ích gì cho người dùng nào. Không tính từ rỗng ("tuyệt vời", "đỉnh cao") khi không đi kèm số.
- Không lặp một câu mở bài giữa các SP ("lý tưởng cho học sinh, sinh viên..." đang ở 16/25 bài laptop): nêu một điểm khác dòng của đúng model.
- Hedge số hãng công bố. Giới hạn nền tảng (phần mềm Arm, xung đột phần mềm) nói thẳng, ngắn.

## HTML (khớp mẫu đang chạy)
- PIM lưu bài **không có** thẻ bọc: web tự bọc `<div id="description-text-detail">`. Nháp bắt đầu thẳng bằng `<h3>` (đã kiểm bài Samsung Odyssey trong `pim-plan-product-194337-...-before.html`). `fetch-live-article.py` trả bản có div bọc, bỏ div khi đối chiếu.
- Mục: `<h3>`. Đoạn: `<p>`. Số liệu: `<strong>`. Không `<h1>/<h2>`.
- Link nội bộ: `<a href="https://www.thegioididong.com/..." rel="noopener" target="_blank" title="...">`; https; mỗi URL 1 lần/bài; không link tìm kiếm/tag/ldp; không `thegioidong.com` (thiếu i); không `http://`.
- Danh sách `<ul>`: phải có `style="list-style: disc; padding-left: 25px;"` (CSS web tắt bullet).
- Bảng: `<table>` có border/padding style trực tiếp.
- Ảnh: `<p><a><img loading="lazy" alt="..." title="..." src="CDN" data-original="CDN" /></a></p>`; `alt` = `title` = một câu mô tả có tên model (hoặc "Tên SP (mã) - Mục"); ảnh 1020×570 JPG đã upload CDN (chưa upload: để `<!-- ANH: ... -->`).
- Byte-exact khi ghi: HTML luôn qua `--set-file`, không gõ inline.

## key_features (đặc điểm nổi bật)
4 gạch đầu dòng ngắn, mỗi dòng 1 thông số then chốt (chip, bộ nhớ, màn hình, thiết kế/pin). `<ul>` có style bullet như trên. Cùng quy tắc nguồn và hedge với bài.
