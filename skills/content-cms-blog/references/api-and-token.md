# NEW CMS: token + module API (tham chiếu)

NEW CMS là SPA React gọi `https://webapi.thegioididong.com/gw/bus/cms/api/v1/...` bằng `Authorization: Bearer`. Token do Keycloak `authkey.dmx.vn/realms/mwg-central`, client `web-new-cms` cấp. Chi tiết API Hỏi Đáp/Game App: `tasks/261102-new-cms-he-tin-review/reports/261102-1410-review-newcms-hoidap-gameapp-api.md`.

## Cơ chế (đo 02/11/2026)

- Access token 12 giờ. Refresh token 7 ngày, **xoay vòng**, mỗi lần refresh hạn trượt về đủ 7 ngày (cùng `sid`).
- Refresh token cũ vẫn dùng được sau khi xoay ⇒ chuỗi token của script tách khỏi tab, refresh ở script **không** làm tab rớt phiên, còn giữ sống luôn phiên của tab.
- Trần cuối: SSO Session Max của realm (chưa đo). Mất phiên khi logout, đổi mật khẩu, IT kill session ⇒ seed lại.
- Không dùng offline token (credential dài hạn) — owner chưa duyệt.

## Lệnh

`$S` = `.claude/skills/content-cms-blog/scripts/newcms-auth.mjs` (CLI chính cũng gọi được: `node cms-blog.mjs ensure | status-token | seed | install-keepalive`)

**Không cần chạy tay.** Skill gọi `newcmsFetch()` / `getAccessToken()` (hoặc `node $S ensure`) là tự lo hết:

| Tình huống | Tự làm gì |
|---|---|
| Chưa có session | Seed từ tab newcms (profile ở session cũ, không có thì `cms.chromeProfiles.newcms`) |
| Access token còn < 15 phút | Refresh |
| Refresh token hỏng/hết hạn (`invalid_grant`) | Seed lại từ tab |
| API trả 401 (`newcmsFetch`) | Ép refresh/seed rồi gọi lại đúng 1 lần |
| Chrome đã đăng xuất newcms | Đưa tab login ra trước + notification, chờ người đăng nhập tối đa 10 phút (`NEWCMS_WAIT_LOGIN_MS`), xong lấy token luôn. Agent **không** tự nhập mật khẩu |
| Nhiều skill cùng thiếu token | Khoá `session.json.seed.lock` — chỉ 1 process mở tab, các process khác chờ rồi dùng chung |

Đã test 02/11: xoá session, làm hỏng refresh token, làm sai access token (401), 3 process cùng lúc → đều tự phục hồi, chỉ seed 1 lần.

| Lệnh | Việc |
|---|---|
| `node $S ensure` | Bảo đảm có token dùng được (tự seed/refresh), in hạn — cho skill viết bằng shell |
| `node $S seed [--profile <key>]` | Không truyền thì lấy `cms.chromeProfiles.newcms` trong `harness.config.json`. Mở tab newcms trong profile, lấy refresh token + cấu hình client, refresh 1 lần, lưu `~/.config/newcms-auth/session.json` (0600), đóng tab |
| `node $S refresh` | Refresh ngay |
| `node $S status` | Hạn còn lại (không in token) |
| `node $S install-keepalive --every-hours 24` | Cài launchd `com.mwg.newcms-auth-keepalive`: refresh định kỳ + chạy lúc login; hỏng thì thử seed lại từ profile đã lưu, vẫn hỏng thì bắn notification. Log `~/Library/Logs/newcms-auth-keepalive.log` |
| `node $S uninstall-keepalive` | Gỡ lịch |

Profile cho trang Hỏi Đáp của CMS cũ (`cms.chromeProfiles.faq`) **chưa đăng nhập** newcms (02/11/2026); profile newcms khai riêng ở `cms.chromeProfiles.newcms`.

## Dùng trong script khác

```js
import { newcmsFetch, getAccessToken } from '<đường dẫn>/newcms-auth.mjs';
const r = await newcmsFetch('/api/v1/News/newsselect?newsid=1467850');   // Bearer + 401 tự xử lý
const token = await getAccessToken();   // khi cần token thô (vd upload multipart tự dựng)
```

Lịch `install-keepalive` không bắt buộc nữa; nó chỉ giữ phiên Chrome không chết khi cả tuần không chạy skill nào (chết thì lần sau phải đăng nhập lại newcms).

Đã kiểm: Node thuần (không qua trình duyệt) gọi `newsselect` trả 200.

## API đọc/ghi (`newcms-api.mjs`, đã test ghi thật 02/11/2026)

| Hàm | Việc | Ghi chú đã kiểm |
|---|---|---|
| `newsSelect(id)` | Đọc bài | Hỏi Đáp: thân bài ở `description`. Game App: ở `content` |
| `faqUpdate(id, changes)` | Sửa bài Hỏi Đáp, chỉ đổi field truyền vào | Đọc gốc → allowlist → `News/newsupdate` → `Cms/news/updatecategory` 1226 → ghi log. Field khác giữ nguyên, entity `&amp; &lt;` lưu đúng byte |
| `faqAdd({status, ...})` | Tạo bài Hỏi Đáp | `status`: draft / pending / approved / actived (Xuất bản). Trả newsId |
| `gameAppSave(payload)` | Tạo (không newsId) / sửa Game App | Tạo mới: server tự gắn `-{newsId}` vào url. Sửa: gửi url không kèm id; `platformIdList`/`productIdList` không gửi = giữ nguyên |
| `newsDelete(id)` | Xoá mềm | Bài sang mục "đã xoá" (`isDeleted=1`), `newsSelect` không đọc được nữa |
| `uploadFilesCms(file, {pathFolder:'News/<id>'})` | Upload **giữ tên file** | Ra `cdnv2.tgdd.vn/webmwg/common/News/<id>/<tên>` — bucket `webmwg`, không phải `mwg-static` như CMS cũ |
| `postImage(file)` | Upload kiểu nút ảnh TinyMCE | Đổi tên thành hash: `mwg-static/tgdd/Common/xx/yy/<hash>.jpg` — không dùng cho ảnh cần tên SEO |
| `newsLog(id)` | Lịch sử sửa | Hỏi Đáp: mỗi bản giữ nguyên HTML `description` → rollback phía server. Game App: log KHÔNG giữ HTML |
| `shortcodeList()`, `tagSearch(kw)`, `faqArticleTypes()`, `gameAppFormTypes()`, `gameAppPlatforms()` | Danh mục shortcode (19), tag có sẵn, Dạng bài Hỏi Đáp (htmlinfo 3724), Dạng bài Game App (htmlinfo 3620 — 3648 là Vào bếp), nền tảng | |
| `previewUrl.faq(url,id)` | Link xem trước bài chưa xuất bản | `staging.thegioididong.com/hoi-dap/xem-truoc/...` |

Bundle app đổi tên biến mỗi lần deploy (02/11 đã đổi 1 lần) — đừng bám tên biến minify; endpoint thì giữ nguyên.

## Luật

- Không in access/refresh token hay client secret ra terminal, report, chat. Chỉ in hạn.
- Tên file script không được chứa chữ `token` — `.gitignore` có rule `**/*token*` nuốt file im lặng.
- Không lưu session vào repo. File nằm ở `~/.config/newcms-auth/`.
- Exit 3 = phải seed lại (refresh token hỏng/hết hạn hoặc tab chưa đăng nhập).
- `cms-cli-mcp.mjs` là bản copy module chung; sửa ở đây thì copy sang các skill CMS khác (test drift `onpage-cms-news-insert/scripts/test-cms-cli-shared-drift.mjs`).

- Game App tạo mới thiếu `thumbnailImage` → HTTP 400 "Vui lòng upload hình thumb" (Hỏi Đáp thì cho tạo thumb rỗng). Đo 02/11/2026.
