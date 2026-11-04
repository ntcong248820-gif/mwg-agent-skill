---
name: content-seo-semantic-outline
description: "Lên bộ Semantic/LSI/Long-tail keyword và dàn bài SEO Final (AIDA, FAB, phân bổ nhóm LSI theo từng H2/H3) cho một bài viết theo Bước 1 quy trình tab Thầy. Use when cần nghiên cứu semantic hoặc lên dàn bài SEO semantic cho một chủ đề + từ khoá chính + brand. Not for viết cả bài (content-seo-semantic-pipeline) hay dàn bài infobox/Hỏi Đáp TGDĐ (tgdd-infobox-*, viet-blog)."
when_to_use: "Khi người dùng nói: lên dàn bài SEO, outline semantic, bộ semantic keyword, LSI keyword cho bài, semantic chiều dọc chiều ngang, dàn bài AIDA FAB. Được content-seo-semantic-pipeline gọi ở Bước 1."
argument-hint: "<brief.json> --out <thư mục>"
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
  nguon: "Sheet PROMPT CORE, tab Thầy, Bước 1"
---

# Semantic + dàn bài SEO (Bước 1 tab Thầy)

Ra 2 file cho người viết đọc thẳng, không cần copy prompt qua lại: `01-semantic.md` (bộ từ
khoá semantic/LSI/long-tail theo cluster) và `02-dan-bai.md` (dàn bài Final có AIDA, FAB và
từ khoá hoạch định cho từng H2/H3). Chất lượng đạt khi người viết chỉ cần dàn bài là biết mỗi
phần nói gì, chèn cụm nào, câu nào nhắm Featured Snippet/PAA.

## Đầu vào

`brief.json` theo khuôn `../content-seo-semantic-pipeline/assets/brief-mau-tab-thay.json`.
Trường bắt buộc: `chu_de`, `kw_chinh`, `brand`, `nganh`. Thiếu `nhom_lsi` thì làm theo mục
"Khi ngành không phải di trú" trong reference.

## Cách làm

1. Đọc `references/prompt-semantic-va-dan-bai.md`, thay `{...}` bằng giá trị brief.
2. Làm 1a → ghi `01-semantic.md`. Kiến thức nền của model là đủ cho bước này; không cần
   search web, không gọi API tốn tiền.
3. Làm 1b (dàn bài nháp) rồi 1c (dàn bài Final) trên chính kết quả 1b → ghi `02-dan-bai.md`.
   Chỉ file Final được giao; bản nháp 1b không cần lưu.
4. Tự kiểm trước khi giao: số H2/H3 và checklist khớp `brief.cau_truc_h2`; H1 có `kw_chinh`
   và `brand`; đủ các nhóm `nhom_lsi` trong bảng phân bổ; mỗi biến thể `kw_phu` có vị trí.

Khi được pipeline gọi dưới dạng subagent: chỉ ghi file vào thư mục được giao, kết thúc bằng
dòng `Status: DONE | BLOCKED` và 1 câu tóm tắt.

## Resources

- `references/prompt-semantic-va-dan-bai.md`: 3 prompt Bước 1 đã tham số hoá và định dạng file ra.
