---
name: content-seo-semantic-pipeline
description: "Viết trọn một bài SEO semantic theo quy trình 5 bước tab Thầy (sheet PROMPT CORE): brief → semantic + dàn bài → viết → tối ưu semantic → soát chính tả 3 lần + rà LSI → 3 giám khảo chấm 7 checklist, mỗi đầu việc giao một subagent, lint đếm từ khoá/brand thay Word Counter. Use when cần viết bài SEO cho chủ đề + từ khoá chính + brand thay cho chuỗi prompt copy tay qua ChatGPT/Claude/POE. Not for bài Hỏi Đáp, infobox, Content SP, bài Top của TGDĐ (viet-blog, tgdd-infobox-*, content-laptop-product, tgdd-top-product-article)."
when_to_use: "Khi người dùng nói: viết bài SEO semantic, viết bài theo quy trình tab Thầy, chạy prompt core, viết bài brand/dịch vụ có từ khoá chính + biến thể + brand, viết bài di trú/đèn LED/lốp/BĐS theo quy trình sếp, demo quy trình viết bài bằng agent."
argument-hint: "<brief.json | chủ đề + từ khoá chính + brand> [--nhanh] [--out <thư mục>]"
metadata:
  version: "1.0.0"
  workspace: mwg-ai-worker
  nguon: "Sheet PROMPT CORE, tab Thầy (gid 518143844), đọc 02/11/2026"
---

# Pipeline viết bài SEO semantic (tab Thầy)

Thay chuỗi ~15 prompt sếp copy qua ChatGPT, Claude, POE và Word Counter bằng một lần chạy:
người điều phối (phiên chính) giữ brief và thứ tự, mỗi đầu việc giao một subagent đọc đúng
prompt của bước đó, mọi phiên bản bài và đề xuất nằm thành file để soát lại được. Bài giao
đạt khi lint 0 FAIL, điểm trung bình 3 giám khảo vòng cuối ≥ 8/10, và mọi câu có số liệu chưa
chắc đã nằm trong `can-kiem-chung.md`.

## Bước 0: brief

1. Lấy từ người dùng: chủ đề, từ khoá chính, biến thể từ khoá phụ, brand (+ 1 câu mô tả),
   ngành, câu CTA kết bài. Thiếu chủ đề, từ khoá chính hoặc brand thì hỏi một lần; các trường
   còn lại lấy mặc định từ `assets/brief-mau-tab-thay.json` (cấu trúc 3 H2, tần suất, từ hạn
   chế, meta < 140 ký tự) và nói rõ đã dùng mặc định.
2. Ghi `brief.json` vào thư mục ra. Trong workspace này thư mục ra mặc định là
   `tasks/{task}/data/processed/{slug-bai}/`; tạo task bằng `seo-task-create` nếu chưa có.
3. Ngành khác di trú mà brief chưa có `nhom_lsi`: subagent Bước 1a đề xuất, điều phối cập nhật
   brief trước khi sang 1b.

## Sơ đồ subagent

Mỗi ô là một subagent mới; mũi tên là phụ thuộc file. Ô cùng hàng chạy song song.

| Bước | Subagent (đọc) | Ghi ra | Cần có trước |
|---|---|---|---|
| 1a | Nghiên cứu semantic (`content-seo-semantic-outline`, mục 1a) | `01-semantic.md` | brief |
| 1b | Dàn bài (`content-seo-semantic-outline`, mục 1b + 1c) | `02-dan-bai.md` | 01 |
| 1c | Người viết (`references/prompt-viet-bai.md`) | `bai-v1.md`, `can-kiem-chung.md` | 02 |
| 2 | Coverage (`audit --coverage`) → Biên tập | `b2-coverage.md` → `bai-v2.md` | v1 |
| 3 | Soát chính tả + meta (`audit --chinh-ta`) ‖ lint → Biên tập → 3 giám khảo ‖ | `b3-*` → `bai-v3.md` → `b3-cham-{a,b,c}.md` | v2 |
| 4 | Rà LSI (`audit --lsi`) ‖ Soát chính tả → Biên tập (+ lỗi giám khảo B3) → 3 giám khảo ‖ | `b4-*` → `bai-v4.md` → `b4-cham-*` | v3 + b3-cham |
| 5 | Biên tập (lỗi giám khảo B4) → Soát chính tả → Biên tập → lint final → 3 giám khảo ‖ | `bai-v5.md` → `bai-final.md` → `b5-cham-*` | v4 + b4-cham |

Lệch so với tab Thầy, có chủ đích: ở Bước 4 sếp rà LSI xong mới soát chính tả; ở đây hai việc
chạy song song trên v3 và người biên tập gộp, vì cả hai đều chỉ ra đề xuất chứ không sửa bài.

`--nhanh` (khi cần bài nhanh, ít token): 1a → 1b → 1c → [coverage ‖ chính tả + meta ‖ LSI] trên
v1 → biên tập → 3 giám khảo → biên tập → lint final. Ghi rõ trong báo cáo là chạy chế độ nhanh.

## Giao việc cho subagent

Mỗi lời giao gồm: vai trò, đường dẫn tuyệt đối của brief + file đầu vào + reference phải đọc,
đúng tên file được ghi, câu "không sửa file nào khác", và yêu cầu dòng cuối
`Status: DONE | DONE_WITH_CONCERNS | BLOCKED` + 1 câu tóm tắt. Không dán lịch sử hội thoại;
subagent chỉ cần file. Giám khảo nhận kèm file lint của đúng phiên bản bài đó.

Sau mỗi subagent, điều phối kiểm file ra có thật và không rỗng trước khi chạy bước sau;
subagent tự báo DONE chưa phải bằng chứng. Thiếu file thì chạy lại subagent đó một lần với lời
giao rõ hơn, vẫn thiếu thì dừng và báo.

Runtime không có subagent: làm tuần tự trong phiên chính theo cùng bảng và cùng tên file;
3 giám khảo khi đó là 3 lượt chấm riêng, không đọc lượt trước.

Model: nếu runtime cho chọn, người viết và biên tập dùng model mạnh nhất có sẵn; soát chính tả
dùng model rẻ hơn được; 3 giám khảo nên là 3 model khác nhau (thay cho POE).

## Lint

```bash
python3 .claude/skills/content-seo-semantic-audit/scripts/seo-semantic-lint.py BAI.md --brief brief.json --stage draft
```

Chạy sau v1 và sau mỗi lần biên tập; `--stage final` cho `bai-final.md`. Lưu đầu ra cạnh bài
(`bN-lint.txt`). Lint là trọng tài cho mọi con số; giám khảo và biên tập dùng số của lint.

## Giao bài

Trong thư mục ra:
- `bai-final.md`: bài cuối, có dòng `META:`.
- `bao-cao.md`: bảng điểm 3 giám khảo × 3 vòng (B3, B4, B5), lint final, số từ từng phiên bản,
  thay đổi chính mỗi vòng, đề xuất bị bỏ và lý do, các mâu thuẫn trong brief nếu gặp.
- `can-kiem-chung.md`: câu có số liệu/điều luật cần người duyệt kiểm.

Điểm vòng cuối < 8 hoặc lint còn FAIL: vẫn giao, nhưng ghi rõ chưa đạt và lỗi còn lại ở đầu
`bao-cao.md`. Không đăng bài, không ghi Sheet/Doc/CMS nếu người dùng không bảo.

## Resources

- `assets/brief-mau-tab-thay.json`: brief đúng đề bài mẫu tab Thầy, cũng là giá trị mặc định.
- `references/prompt-viet-bai.md`: prompt người viết (Bước 1 prompt 4-6) + định dạng bài.
- `references/prompt-bien-tap.md`: luật người biên tập áp đề xuất, thứ tự ưu tiên, kiểm sau sửa.
- Skill `content-seo-semantic-outline`: Bước 1a-1b (semantic + dàn bài).
- Skill `content-seo-semantic-audit`: lint, coverage, chính tả, LSI, 3 giám khảo.
