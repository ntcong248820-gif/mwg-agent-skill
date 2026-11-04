---
name: content-cms-blog
description: "Một cửa tương tác CMS Blog TGDĐ trên NEW CMS (newcms.thegioididong.com) cho 2 hệ bài Hỏi Đáp và Game App: tạo bài mới từ form.json (lint đủ luật, thumb + ảnh bài upload giữ tên vào common/News/{id}/, chuyên mục, dạng bài, tag, trạng thái theo ngày đăng), cập nhật/air thân bài + title/meta/field bất kỳ (backup, diff, đọc lại so byte), upload ảnh, đổi thumb, tick nổi bật, đổi trạng thái, xuất bản hẹn giờ, nghiệm thu trang live, xem lịch sử + rollback, xoá mềm, tra chuyên mục/dạng bài/tag/shortcode/nền tảng. Token Bearer tự lo. Có --old-cms chuyển sang CMS cũ khi NEW CMS lỗi. Thay cms-content-create và content-cms-air-hoidap. Trigger: up bài hỏi đáp, up bài game app, tạo bài mới trên CMS, air bài hỏi đáp, cập nhật bài hỏi đáp, đăng bài lên CMS, xuất bản bài, đổi thumb, tick nổi bật, upload ảnh bài lên CMS, rollback bài, newcms, NEW CMS, token newcms."
---

# CMS Blog (NEW CMS): Hỏi Đáp + Game App

Phạm vi: **chỉ Hỏi Đáp và Game App** (owner chốt 02/11/2026). Tin tức thường (CMS News), trang hãng, bài SP vẫn ở CMS cũ, dùng skill riêng của chúng (`onpage-cms-news-insert`, `content-cms-air-infobox`, `onpage-mdm-khai-bao`).

Chạy bằng Node thuần qua API `webapi.thegioididong.com/gw/bus/cms/api/v1` + Bearer — không bấm UI, không cần giữ tab mở. Token tự seed/refresh từ profile Chrome `cms.chromeProfiles.newcms` (xem `references/api-and-token.md`).

```bash
B=.claude/skills/content-cms-blog/scripts/cms-blog.mjs
node $B            # in danh sách lệnh
```

**Mọi lệnh ghi chỉ ghi khi có `--go`.** Thiếu `--go` = chạy thử: lint, in kế hoạch/diff rồi dừng. Luôn chạy thử trước, đưa user xem, rồi mới `--go`.

## Lệnh

| Việc | Lệnh |
|---|---|
| Đọc bài (tóm tắt + lưu JSON và thân bài) | `node $B read <id> [--out <dir>]` |
| Tạo bài mới | `node $B create --form form.json [--type hoi-dap\|game-app] [--go]` |
| Sửa thân bài và/hoặc field | `node $B update <id> [--html f.html] [--dir <ảnh>] [--set field=giá-trị ...] [--go]` |
| Air = update + nghiệm thu live | `node $B air <id> --html f.html [--dir] [--set ...] [--publish] [--no-live] [--go]` |
| Chỉ upload ảnh local, ra `<f>.cdn.html` | `node $B images <id> --html f.html [--dir] [--go]` |
| Map ảnh local cho `chen_anh.py` (chưa upload) | `node $B image-map <thư mục ảnh> [--out anh-cdn.json]` |
| Đổi trạng thái | `node $B status <id> --to draft\|pending\|approved\|actived [--date dd/mm/yyyy --time HH:MM] [--go]` |
| Xuất bản | `node $B publish <id> [--date dd/mm/yyyy] [--time HH:MM] [--keep-time] [--go]` |
| Đổi thumb | `node $B thumb <id> --file thumb.jpg [--go]` |
| Tick / bỏ nổi bật | `node $B sticky <id...> [--off] [--go]` |
| Lịch sử sửa | `node $B history <id> [--size 20]` |
| Khôi phục thân bài về 1 bản log | `node $B rollback <id> --log <newsLogId> [--go]` (chỉ Hỏi Đáp) |
| Nghiệm thu trang live | `node $B live <id> [--html f.html] [--no-wait]` |
| Xoá mềm | `node $B delete <id> [--go]` |
| Tra cứu | `node $B lookup categories [từ] \| article-types \| form-types \| platforms \| tags <từ> \| shortcodes` |
| Token | `node $B ensure \| status-token \| seed \| install-keepalive \| uninstall-keepalive` |

Loại bài tự nhận từ bản ghi (Game App = `isGameApp=1` hoặc chuyên mục 2002), lệnh theo id không cần `--type`.

`--set` nhận tên field như `newsselect` hoặc tên tắt: `title`, `url`, `meta_title`→`metaTitle`, `meta_desc`→`metaDescription`, `tags`→`metaKeyword` (Hỏi Đáp, ghi cả `tags`), `article_type`, `products`→`productIdList`, `child_category`/`parent_category`, `thumb`, `schema`, `isSticked`; Game App thêm `form_game_app`, `isGame`, `platforms`→`platformIdList`, `isFeature`, `isPin`. Field không truyền giữ nguyên.

## Tạo bài (`create`)

`form.json` cùng khuôn với skill cũ `cms-content-create` (đường dẫn tương đối tính theo thư mục form):

```json
{
  "type": "hoi-dap",
  "keyword": "macbook màu bạc",
  "title": "Top 8 mẫu MacBook màu bạc đẹp, sang",
  "url": "",
  "thumb": "macbook-mau-bac-thumb.jpg",
  "child_category": "1703", "parent_category": "1656",
  "article_type": "Top sản phẩm",
  "product_related": "293655,293766",
  "meta_title": "", "meta_desc": "…",
  "tags": ["macbook màu bạc", "macbook air"],
  "content_file": "final-content.html",
  "images_dir": "",
  "publish_date": "05/11/2026", "publish_time": "02:00",
  "status": ""
}
```

- `url` trống → tự sinh từ title (≤50, cắt ở ranh giới cụm). `meta_title` trống → lấy title.
- `images_dir` trống → thư mục của `content_file`. Ảnh trong HTML để src tương đối (tên file), CLI upload rồi thay src.
- Trạng thái: `publish_date` có ngày → **Xuất bản hẹn `publish_time` (mặc định 02:00)** ngày đó; trống → **Chờ duyệt**. Ghi đè bằng `status` (`draft|pending|approved|actived`).
- Game App: `"type": "game-app"`, thêm `form_game_app` (bắt buộc, xem `lookup form-types`), `platforms` (`lookup platforms`), `is_game` (1 game / 0 app). Bỏ `child_category`, `article_type`; Game App không có ô tag. Trạng thái Xuất bản của Game App là `approved`.

Luồng: lint → sổ chống trùng (`~/.local/state/cms-blog/created.json`, khoá theo `loại:url`) → tạo nháp → upload thumb + ảnh vào `cdnv2.tgdd.vn/webmwg/common/News/{id}/` giữ tên → ghi bản cuối (thân bài đã thay src, thumb, trạng thái, ngày đăng, **luôn tick Bài viết nổi bật**) → đọc lại so từng field, thân bài so byte. Lỗi giữa chừng sau khi có id: CLI in id, sửa xong chạy `update <id>`, **đừng tạo lại**.

Luật lint chính (lỗi = không ghi): title ≤70 (Game App ≤130); url a-z0-9-, ≤84 Hỏi Đáp / ≤92 Game App; meta title ≤70; meta desc bắt buộc ≤170; Hỏi Đáp tags 2–5 phải chứa keyword, cặp chuyên mục con/cha phải khớp, dạng bài phải có trong CMS; ngày đăng không được ở quá khứ; thân bài không có `<html>/<body>`, ngày "cập nhật" phải là hôm nay, ảnh URL ngoài phải trả 200, ảnh local phải có trong thư mục. Cảnh báo: thumb khác 560x292 hoặc >300KB, chữ "thiết bị", bullet "-" trong `<p>`, từ đặt trước/tin đồn/rò rỉ, ảnh thiếu alt.

## Cập nhật / air

- Backup bản ghi + thân bài trước mỗi lần ghi vào `~/.local/state/cms-blog/<id>/`.
- Ảnh local trong `--html` tự upload vào `News/{id}`: tên đã có trên CDN cùng byte → dùng lại; khác byte → dừng (CDN không ghi đè được, đổi tên file). Upload xong so từng byte.
- Ghi xong đọc lại, so byte thân bài và từng field `--set`. Hỏi Đáp ghi thêm 1 bản lịch sử (`history`).
- `air` nghiệm thu live khi bài đã xuất bản: đợi ~60s, `?clearcache=1`, so heading, tên ảnh, đoạn đầu/cuối thân bài. Shortcode được bỏ qua khi so.

## Xuất bản

Chỉ xuất bản (`publish`, `status --to actived`, `air --publish`) khi user bảo xuất bản. Mặc định ngày đăng = lúc chạy; `--keep-time` giữ ngày đang khai; `--date/--time` hẹn giờ. Hẹn giờ tương lai trên NEW CMS chưa kiểm chứng trên trang live — sau giờ hẹn chạy `live <id>`.

## CMS cũ dự phòng (`--old-cms`)

Khi NEW CMS lỗi, thêm `--old-cms`: `create` → `tao_bai.mjs`, `update` → `cap_nhat_noi_dung.mjs`, `publish` → `xuat_ban.mjs`, `thumb` → `doi_thumb.mjs`, `status` → `doi_trang_thai.mjs` (không có chạy thử), `sticky` → `tick_noi_bat.mjs`, `air` → `run-air-hoidap-cli.mjs`. Các script đó lái tab CMS cũ qua chrome-profile, cần skill `cms-content-create` / `content-cms-air-hoidap` có trên máy. CMS cũ vẫn nhận ghi (owner xác nhận 02/11/2026).

## Bẫy đã đo (02/11/2026)

- Hỏi Đáp: thân bài ở `description` (`content` = "Câu hỏi"). Game App: thân bài ở `content`. CLI tự chọn.
- Ảnh giữ tên ra bucket `webmwg`, không phải `mwg-static` như CMS cũ. Cùng file theo đường `mwg-static` trả 404.
- Game App: server từ chối tạo khi thiếu thumb → CLI tạo bằng thumb tạm (PostImage, tên hash) rồi đổi sang bản giữ tên. Server lưu url kèm `-{id}`; gửi lại thì bỏ `-{id}`.
- Lịch sử Game App không giữ HTML → không rollback được, chỉ còn backup local.
- Dạng bài Game App ở htmlinfo 3620 (3648 là của Vào bếp).
- `delete` là xoá mềm: bài vào mục đã xoá trên CMS, `read` không đọc được nữa.

## File

- `scripts/cms-blog.mjs` — CLI. `cms-blog-core.mjs` — loại bài, trạng thái, payload, upload, backup. `cms-blog-lint.mjs` — luật form/nội dung.
- `scripts/newcms-api.mjs`, `newcms-auth.mjs` — API + token (`references/api-and-token.md`).
- `scripts/cms-cli-air.mjs`, `cms-cli-mcp.mjs` — **bản copy y hệt** module chung của các skill CMS; sửa thì copy sang mọi bản, chạy `node .claude/skills/onpage-cms-news-insert/scripts/test-cms-cli-shared-drift.mjs`.
- `references/cms-options.json` — chuyên mục con/cha, dạng bài (mã giống CMS cũ).
- Test offline: `node .claude/skills/content-cms-blog/scripts/test-cms-blog-offline.mjs`.

## Luật

- Không in token/secret. Không lưu session vào repo.
- Bài test đặt title `[TEST AGENT] …`, để Nháp, xoá mềm ngay sau test.
- Ghi xong báo user: newsId, link sửa trên CMS, link xem trước/live, trạng thái, số ảnh đã upload.
