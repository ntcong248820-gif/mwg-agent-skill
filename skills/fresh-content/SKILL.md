---
name: fresh-content
description: >
  Làm mới (fresh) bài content HTML đang chạy trên TGDĐ/ĐMX/TopZone, ví dụ bài category
  dòng máy hoặc bài infobox sản phẩm vừa ra mắt. Skill check giá và khuyến mãi sống trên
  site, sửa lỗi chính tả và factual, kéo từ khoá GSC chưa có trong bài rồi rải vào theo
  nguyên tắc CHỈ THÊM, KHÔNG SỬA KW CŨ. Skill cũng bổ sung FAQ từ nguồn nước ngoài uy tín
  hoặc bài tin mới trên site, và thêm bài mới vào box "Bài viết liên quan" nếu bài có box.
user-invocable: true
when_to_use: >
  Trigger khi user đưa file/bài HTML và nói "coi bài này hôm nay cần update gì không",
  "fresh bài này", "check giá TGDĐ", "check GSC xem còn kw nào chưa rải", "thêm FAQ",
  "rà bài viết liên quan còn thiếu bài nào mới", hoặc "tương tự check bài này" sau khi
  đã fresh một bài khác. Không dùng cho bài sản phẩm đã cũ cần viết lại sapo/cấu trúc
  (dùng toi-uu-content-sp-outdate), và không dùng để chỉ fact-check (dùng
  check-content-iphone-18).
category: content-ops
keywords: [fresh-content, update-bai, gia-tgdd, khuyen-mai, gsc, tu-khoa, faq, bai-viet-lien-quan, tgdd, dmx, topzone]
metadata:
  author: content02@thegioididong.com
  version: "1.0.0"
---

# Fresh Content (fresh-content)

Skill này đóng gói quy trình đã dùng để fresh 2 bài iPhone 18 Pro (bài category series và bài 256GB) ngày 01/10/2026. Mục đích là giữ bài luôn đúng giá, đúng khuyến mãi và phủ thêm kw GSC mà không phá dụng ý SEO của người viết.

## Nguyên tắc bắt buộc (input của user)

1. **Chỉ thêm, không sửa kw hiện tại.** User viết có dụng ý hết. Kw mới phải chèn bằng câu hoặc đoạn mới, hoặc nối vào cuối đoạn có sẵn. Không được đổi, cắt hay paraphrase cụm từ đang có trong bài.
   - Ngoại lệ được sửa: giá, ngày, khuyến mãi đã sai, lỗi chính tả rõ ràng (ví dụ "Phone 16" thành "iPhone 16", "Bênh" thành "Bên") và lỗi factual có nguồn xác nhận. Các chỗ này phải liệt kê rõ trong báo cáo.
2. **Rải kw phải hỏi user trước, không tự rải.** Skill chỉ được ĐỀ XUẤT (bảng: kw, impression, vị trí định chèn, câu nháp) rồi dừng chờ user duyệt từng kw hoặc cả nhóm. Chưa được duyệt thì không chèn kw nào vào bài. Làm xong các phần khác (giá, khuyến mãi, lỗi chính tả, FAQ) trước, phần kw để cuối.
3. **Không nhồi kw.** Mỗi kw mới tối đa 1 lần, câu phải đọc tự nhiên như người viết. Mỗi đoạn mới chèn tối đa 2 kw mới. Không dựng đoạn văn chỉ để chứa kw (kiểu liệt kê "Nếu bạn đang tìm... hay... hay..."). Bỏ qua biến thể gần nghĩa, sai chính tả, viết tắt (ip, prm, 18pm) và kw địa phương, chỉ đề xuất kw thật sự khác ý định tìm kiếm.
4. **Luôn làm trên file mới nhất trên đĩa.** User hay dán lại HTML giữa chừng. Trước mỗi lượt sửa phải đọc lại file, không dùng bản đã cache trong đầu.
5. **Box "Bài viết liên quan":** bài nào có box thì rà site để thêm bài mới còn thiếu. Bài nào không có box thì bỏ qua, không tự tạo box.
6. **Giá lấy từ site đang viết bài** (TGDĐ/ĐMX/TopZone), không lấy giá Apple.com. Câu ngày cập nhật giá phải in nghiêng theo dạng "Giá … được cập nhật vào ngày dd/mm/yyyy…".
7. **Không đưa tin đồn hay rò rỉ**, kể cả khi ghi rõ là tin đồn, vì TGDĐ là partner Apple. Nếu FAQ hỏi về model chưa có (Plus/Air/18e…), chỉ trả lời theo những gì hãng đã công bố.
8. **Brand và hotline:**
   - TGDĐ: 1900 232 460
   - Điện máy XANH: 1900 232 461 (viết đúng "Điện máy XANH")
   - TopZone: 1900 9696 42, không tô màu bảng/chữ
9. **Văn phong:** áp dụng `~/.claude/skills/_shared/tranh-van-phong-ai.md`. Viết tiếng Việt tự nhiên, không sáo rỗng, không dùng dấu gạch dài.
10. **Giữ nguyên link ngoài do user cố ý đặt** (ví dụ link Wikipedia ở câu kết bài để tăng độ uy tín). Không flag, không gỡ, không hỏi lại.
11. **Backup trước khi sửa** vào scratchpad (`backup-<ten-bai>-<ddmm>.html`).

## Quy trình

### Bước 1. Đọc bài và chụp hiện trạng
- Đọc toàn bộ file. Ghi lại:
  - mọi con số giá, ngày cập nhật, dòng khuyến mãi, hotline
  - link sản phẩm (/dtdd/...)
  - các FAQ hiện có
  - có box "Bài viết liên quan" hay không
- Lưu ý encoding:
  - Có file dùng HTML entity (`B&agrave;i viết li&ecirc;n quan`), có file dùng UTF-8 thô.
  - File copy từ CMS thường chứa NBSP (`\xa0`), nên exact match sẽ fail. Dùng `scripts/rep.py`:
    ```bash
    PYTHONPATH=~/.claude/skills/fresh-content/scripts python3 - <<'E'
    from rep import make
    p='<file>'; st,R=make(open(p).read())
    R('chuỗi cũ', 'chuỗi mới')      # assert đúng 1 match, chịu được NBSP
    open(p,'w').write(st['t'])
    E
    ```

### Bước 2. Check giá và khuyến mãi sống
- `curl -s -A 'Mozilla/5.0' <link sản phẩm>` cho từng phiên bản dung lượng hoặc model có trong bài. Lấy giá ở `class="box-price-present"` hoặc `"price":` trong JSON.
- Đọc block "Khuyến mãi" trên trang sản phẩm để lấy:
  - thời gian áp dụng
  - PMH và điều kiện
  - ưu đãi thanh toán online (ngân hàng, mức giảm, số suất)
  - mở thẻ, trả góp
  - dòng "dự kiến giao hàng"
- So với bài và cập nhật lại các chỗ sau:
  - giá ở sapo, bảng giá, bullet
  - các câu so sánh chênh giá (ví dụ "rẻ hơn 17 Pro X triệu")
  - "thấp hơn giá niêm yết Apple VN X đồng"
  - ngày cập nhật (mọi chỗ)
- Gỡ ưu đãi không còn trên site.
- Sau khi sửa, grep lại để chắc **0 chuỗi giá/ngày cũ còn sót**.

### Bước 3. Rà lỗi chính tả và factual
- Lỗi tag dính chữ (`k</span>hung`), tên model thiếu chữ, tên chip/tập lệnh viết sai, thông số sạc không khớp.
- Factual đối chiếu với Apple Newsroom VN, apple.com/vn và trang sản phẩm TGDĐ. Với dòng iPhone 18, dùng thêm quy ước trong `check-content-iphone-18`.

### Bước 4. GSC: tìm kw chưa rải (CHỈ ĐỀ XUẤT, chờ user duyệt)
- Lấy query của đúng URL bài, 28–30 ngày gần nhất, bằng `mcp__gscServer__get_advanced_search_analytics`. Tham số: site_url `https://www.thegioididong.com/` (hoặc site tương ứng), dimensions `query`, filter `page` equals URL bài, sort theo impressions.
- Nếu bài chưa có URL hoặc data ít, lấy query theo cụm chủ đề (filter query contains tên model) ở cấp site.
- Lọc ra những query có impression đáng kể mà cụm từ chưa xuất hiện nguyên văn trong bài (so cả bản entity-decoded, bỏ NBSP). Loại biến thể gần nghĩa, sai chính tả, viết tắt, kw địa phương, kw đã lỗi thời (đặt trước, giá dự kiến).
- Gom theo nhóm intent: ra mắt, giá, màu, thông số, mua ở đâu/TGDĐ, sẵn hàng, bản Mỹ, model khác.
- **Dừng lại và hỏi user.** Trình bày bảng ngắn: kw | impression | chỗ định chèn | câu nháp. Ưu tiên ít kw, chỉ những kw đáng giá. Chỉ rải sau khi user trả lời duyệt (toàn bộ, một phần, hoặc sửa câu).
- Sau khi rải, chạy n-gram check so với bản backup để chắc không mất kw cũ (mọi 4-gram của bản backup phải còn, trừ giá/ngày/lỗi đã chủ động sửa).

### Bước 5. FAQ từ nguồn uy tín và bài tin mới
- Tìm thông tin mới về sản phẩm:
  - Apple Support/Newsroom, release notes iOS
  - 9to5Mac, MacRumors (chỉ phần đã xác nhận), The Verge
  - bài tin mới trên chính site
- Ví dụ FAQ đã thêm:
  - bản cập nhật iOS x.0.1 sửa lỗi gì, có nên cập nhật không (kèm lời khuyên Wi-Fi, pin trên 50%, backup iCloud)
  - lỗi Face ID đã sửa chưa
  - có màu X không
  - có nên mua bản Mỹ không
- Không thêm thông tin rò rỉ hay chưa được hãng xác nhận.

### Bước 6. Box "Bài viết liên quan" (chỉ khi bài có box)
- Trích các href đang có trong box.
- Tìm bài mới trên site cùng chủ đề:
  - GSC dimension `page`, filter page contains slug chủ đề (ví dụ `iphone-18`), bỏ `/dtdd`
  - có thể xem thêm trang tin/hỏi đáp của site
- Với mỗi URL chưa có trong box, `curl` để chắc trả về 200 và lấy H1 làm title/anchor.
- Bỏ bài đã lỗi thời, ví dụ "Đặt trước…" khi đã qua giai đoạn đặt trước.
- Append `<li>` vào cuối `<ul>` của box, copy đúng style đang có:
  ```html
  <li><a style="color: #0066cc; text-decoration: none; font-weight: 500;"
      title="<H1>" href="<url>" target="_blank" rel="noopener"><H1></a></li>
  ```
  Escape ký tự `"`, `&`. Ưu tiên bài sát intent bài chính lên trước (trên tay, so sánh, đánh giá thực tế).

### Bước 7. Báo cáo cho user (tiếng Việt)
Báo cáo theo từng bài, chia các nhóm:
- Giá và khuyến mãi (số cũ → số mới)
- Sửa lỗi
- Kw GSC: danh sách đã đề xuất, kw nào user duyệt và đã rải
- FAQ thêm mới
- Bài viết liên quan đã thêm, hoặc "bài không có box, bỏ qua"

Cuối báo cáo xác nhận "chỉ thêm, không sửa kw cũ" và ghi đường dẫn backup. Nếu user muốn copy, gửi lại HTML hoặc text khi được yêu cầu.

## Ghi chú kỹ thuật
- macOS: `ls -laT` (không có `--time-style`), `cat -v` (không có `-A`).
- Grep text tiếng Việt trong file entity-encoded thì phải grep cả dạng entity.
- Với nhiều bài liên tiếp ("tương tự check bài này"), lặp lại đủ bước 1–7 cho từng bài.
