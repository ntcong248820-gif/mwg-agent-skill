---
name: content-seo-semantic-audit
description: "Soát và chấm bài SEO semantic theo Bước 2-5 quy trình tab Thầy: lint đếm từ/từ khoá/brand/từ hạn chế/cấu trúc, đánh giá Semantic Coverage, rà LSI theo nhóm, soát chính tả-câu dài-câu lặp, chấm 7 checklist bởi 3 giám khảo. Use when cần kiểm, chấm điểm hoặc ra đề xuất sửa cho một bài SEO đã viết. Not for viết bài từ đầu (content-seo-semantic-pipeline) hay chấm bài Content SP/infobox TGDĐ (content-laptop-product, tgdd-infobox-*)."
when_to_use: "Khi người dùng nói: chấm bài SEO, soát chính tả bài, check tần suất từ khoá/brand, word counter, semantic coverage, rà LSI 6 nhóm, 3 lần chấm, chấm 7 checklist. Được content-seo-semantic-pipeline gọi ở Bước 2-5."
argument-hint: "<bai.md> <brief.json> [--lint|--coverage|--lsi|--chinh-ta|--cham]"
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
  nguon: "Sheet PROMPT CORE, tab Thầy, Bước 2-5"
---

# Soát + chấm bài SEO semantic (Bước 2-5 tab Thầy)

Mỗi việc soát ra một file đề xuất, **không sửa bài**: người biên tập (hoặc pipeline) áp đề
xuất sau. Đếm số luôn bằng script, không để model tự đếm, vì model đếm cụm tiếng Việt sai
thường xuyên. Đề xuất phải chép câu gốc nguyên văn để tìm-thay được.

## Đầu vào

- Bài dạng Markdown: dòng `META: ...` (nếu có) trước H1, `#` H1, `##` H2, `###` H3, danh
  sách `-` hoặc `1.`. Bài ở định dạng khác thì chuyển về dạng này trước.
- `brief.json` theo `../content-seo-semantic-pipeline/assets/brief-mau-tab-thay.json`.

## Chọn việc

| Việc | Đọc / chạy | Ra |
|---|---|---|
| `--lint` (luôn chạy trước các việc khác) | `scripts/seo-semantic-lint.py` | `bN-lint.txt` |
| `--coverage` (Bước 2) | `references/prompt-semantic-coverage.md` | `b2-coverage.md` |
| `--chinh-ta` (Bước 3, 4, 5) | `references/prompt-soat-chinh-ta.md` | `bN-chinh-ta.md` |
| `--lsi` (Bước 4) | `references/prompt-lsi-6-nhom.md` | `b4-lsi.md` |
| `--cham` (sau Bước 3, 4, 5) | `references/prompt-cham-7-checklist.md`, 3 giám khảo | `bN-cham-{a,b,c}.md` |

Không ghi việc: chạy `--lint` rồi `--cham`. Các việc ngoài lint độc lập nhau trên cùng một
phiên bản bài, nên khi runtime có subagent thì giao mỗi việc một subagent chạy song song;
không có thì làm tuần tự trong phiên.

## Lint

```bash
python3 .claude/skills/content-seo-semantic-audit/scripts/seo-semantic-lint.py BAI.md --brief brief.json --stage draft|final --json bN-lint.json > bN-lint.txt
```

- Kiểm: số từ, H1/H2/H3 + checklist theo `cau_truc_h2`, từ khoá chính nguyên cụm đứng riêng
  (không tính khi nằm trong biến thể dài hơn) + tổng, đủ biến thể `kw_phu`, trần `tan_suat_toi_da`,
  số lần brand + brand ở H1/H2/sapo/đoạn kết, brand + cách gọi thay thế, từ hạn chế, câu CTA
  nguyên văn, meta, in đậm/emoji/code, tiếng Anh xen, câu dài, mở câu lặp.
- Exit 1 khi có FAIL. `--stage draft` hạ lỗi thiếu META xuống WARN (meta có từ Bước 3).
- WARN tiếng Anh và câu dài là gợi ý: đọc rồi quyết, không sửa máy móc.

## 3 giám khảo

Chạy 3 subagent độc lập trên cùng bài + cùng lint. Nếu runtime cho chọn model thì giao 3 model
khác nhau (thay cho việc sếp chấm trên POE nhiều model); không thì 3 subagent cùng model vẫn
có giá trị vì đọc độc lập. Gộp: điểm trung bình từng checklist và cả bài, lỗi được ≥2 giám khảo
nêu thì xếp đầu danh sách sửa.

## Resources

- `scripts/seo-semantic-lint.py`: lint đếm từ/từ khoá/brand/cấu trúc; test ở `scripts/tests/`.
- `references/prompt-semantic-coverage.md`: Bước 2, coverage 2 trục + đề xuất 50-100 từ.
- `references/prompt-soat-chinh-ta.md`: soát câu dài, chính tả, câu lặp; meta ở Bước 3.
- `references/prompt-lsi-6-nhom.md`: Bước 4, bảng bao phủ nhóm LSI + đoạn cũ/mới.
- `references/prompt-cham-7-checklist.md`: 7 checklist, thang 10, định dạng để gộp điểm.
