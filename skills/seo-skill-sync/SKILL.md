---
name: seo-skill-sync
description: "Đồng bộ skill ra nhiều agent surface (.claude canonical → .codex, .agents, .gemini) và kiểm parity một chiều. Dùng sau mỗi lần sửa skill."
user-invocable: true
when_to_use: "Trigger: sync skill, đồng bộ skill, parity skill, vừa sửa SKILL.md, tạo skill mới, kiểm 4 surface, skill lệch surface."
category: seo-ops
keywords: [skill, sync, surface, parity, claude, codex, agents, gemini]
metadata:
  version: "1.1.0"
---

# seo-skill-sync

Giữ skill local giống nhau ở cả 4 surface. `.claude/skills/` là **canonical**;
3 surface còn lại là bản sao.

Lý do skill này tồn tại: cùng một job có thể được dispatch sang nhiều runtime.
Worker đọc bản sao cũ sẽ trả lời sai mà vẫn tự tin. Sửa tay 4 bản thì lần thứ ba
sẽ quên một bản.

## Scope

Chỉ đọc/ghi trong `.claude/skills/`, `.codex/skills/`, `.agents/skills/`,
`.gemini/skills/` (đổi được bằng `--canonical` / `--targets`). Không sửa
`skills-lock.json`, không sửa MCP config, không tạo global skill.

## Skill nào được sync

Mặc định: **mọi thư mục** trong canonical.

Dùng `--prefixes` để thu hẹp khi surface của bạn còn chứa skill cài từ nguồn
khác (Google Workspace, n8n, gcloud…). Những skill đó có installer riêng, copy
giữa surface sẽ đánh nhau với installer:

```bash
node skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --check --prefixes seo-,tgdd-
```

## Workflow

1. Chạy `--check` trước. Đọc bảng, xác định file nào `DIFF` / `MISSING`.
2. Nếu `DIFF` nằm ở surface phụ → chạy `--apply`.
3. Nếu `DIFF` là do ai đó sửa trực tiếp ở surface phụ và bản đó mới hơn →
   **dừng, báo user**. Script chỉ ghi một chiều; apply sẽ xoá thay đổi đó.
4. Chạy `--check` lại, xác nhận exit `0`.
5. `ORPHAN` (file chỉ có ở surface phụ) thì script chỉ báo, không xoá. Người
   quyết: xoá tay, hoặc chuyển file đó về `.claude` rồi apply.

```bash
node skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --check
node skills/seo-skill-sync/scripts/sync-skill-surfaces.mjs --apply
```

Cờ: `--root <dir>` (mặc định cwd), `--canonical <dir>`, `--targets a,b,c`,
`--prefixes x-,y-`.

## Per-surface override

Một số surface được phép khác canonical ở đúng vài key frontmatter. Hiện tại
allowlist là `model:` — ví dụ canonical ghim `model: haiku` cho một skill mà
3 surface kia không được thừa hưởng.

Cơ chế: những dòng thuộc allowlist bị loại khỏi phép so sánh, và khi ghi thì
script đọc file đích trước để giữ lại dòng override của chính nó.

Thêm key vào allowlist thì sửa `OVERRIDE_KEYS` trong script, không sửa từng file.

## Không làm

- Không có flag sync ngược từ surface phụ về `.claude`. Chiều đó sẽ phá bản canonical.
- Không tự chạy khi agent khởi động. Chỉ chạy khi được gọi.
- Không xoá file. `ORPHAN` chỉ được báo.

## Sau khi sửa skill

Mọi lần sửa hoặc tạo skill local, thứ tự bắt buộc: sửa trong `.claude/skills/` →
`--apply` → `--check` → commit cả 4 surface trong cùng một commit.

## Rollback

```bash
git checkout -- .codex/skills .agents/skills .gemini/skills
```
