# Template brief — Anti review anchor/link sau optimizer

Dùng cho **mọi** lần chạy `optimize_content.py` có chèn/sửa link hoặc chuẩn hoá
bảng, bất kể bài dạng nào (top SP, infobox, hỏi đáp) và bất kể bài có mấy link.
Đây là **bản duy nhất** — `tgdd-top-product-article` trỏ về đây, không giữ bản
riêng, để hai bên không lệch nhau.

Điền `{...}` rồi lưu thành `{run_dir}/brief-antigravity-{seq}.md`. Trần 2048 B —
`readPrompt` từ chối brief lớn hơn.

Bản này **sát trần**: điền path thật (slug dài + evidence trong `crew-{ts}/`) ra
~2040 B. Thêm chữ là phải đo lại `wc -c` trên bản đã điền, đừng đo trên template.
Luật đầy đủ nằm trong `SKILL.md` — worker đọc skill, brief chỉ nói phần nó không
tự suy ra được.

```markdown
# Job {run_id}#{job_seq} — antigravity

## Tình hình
Bài vừa chạy `optimize_content.py`. Script chèn link theo khớp chữ — khớp chữ
không bảo đảm đúng vật.

## Cần gì
`final-content.html` chỉ còn link đúng ngữ cảnh, anchor trọn nghĩa, href trả 200
không redirect. Kèm bảng "trước → sau" mỗi link đã đụng (anchor | URL cũ → mới
hoặc gỡ | lý do).

## Bối cảnh & file
- `WS={ws}`; đọc `$WS/source/final-content.html`

## Skill
`content-html-optimizer` — đọc SKILL.md rồi làm, kỹ mục "Xử lý redirect".

## Lưu ý
- Mỗi link trả 3 câu, sai 1 câu là gỡ: anchor nằm trong tên SP/tên công nghệ/dòng
  thông số? câu nói đúng vật đó? đích đúng vật đó?
- Anchor trọn cụm: "laptop HP" — không để "laptop [HP]". "dòng [Acer Aspire]" đã
  trọn, giữ nguyên.
- Redirect sang URL mới cùng nội dung → thay bằng URL cuối.
- 404, hoặc redirect về trang chủ/trang rộng hơn → tìm bài tương đương (cùng chủ
  đề, cùng loại đích, kiểm 200 sạch) thay vào; không có thì gỡ `<a>` giữ chữ.
  **Cấm để nguyên.**

## Được ghi
- {evidence_path}
- `$WS/source/final-content.html`

KHÔNG ghi file khác. Chỉ đụng **thẻ `<a>`**, không đổi chữ nào của thân bài.

## Acceptance
- [ ] `check_internal_links.py --workspace $WS` → 0 FAIL, **hoặc** mỗi FAIL còn lại
      có 1 dòng nói vì sao giữ (link đúng thì giữ, đừng gỡ cho sạch bảng)
- [ ] `validate_article.py --workspace $WS` → FAIL 0
- [ ] Bảng trước → sau đủ link đã đụng

## Ranh giới
- Không air CMS, không ghi Sheet. API tốn tiền → `BLOCKED / COST_GATE`.

## Kết thúc
3 dòng cuối evidence: `Summary:`, `Concerns/Blockers:`, `Status:` (một giá trị).
```

## Sau khi Anti xong — Claude review lại (bắt buộc)

Đọc bảng trước → sau và chính `final-content.html`:

- kiểm đúng 3 câu hỏi trên cho từng dòng Anti đã sửa;
- đếm link biến mất mà không dòng nào giải thích;
- chạy lại `check_internal_links.py` + `validate_article.py`: **còn href redirect
  hoặc chết thì không nhận evidence**, trả job về cho Anti.

Anti tự khai "đã kiểm" không tính — xem
`tgdd-top-product-article/references/lessons-learned.md` lesson #28.
