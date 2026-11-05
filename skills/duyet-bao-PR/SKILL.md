---
name: duyet-bao-PR
description: >
  Duyệt 1 hoặc nhiều bài PR báo điện tử/GuestPost (Google Doc) cho mọi dự án sản phẩm thuộc
  TGDĐ, TopZone, ĐMX, đồng bộ rule với skill viet-bao-PR: đối chiếu sheet plan và sheet KW
  (anchor, URL, lưu ý báo), chạy lại toàn bộ checklist viết (title, sapo, độ dài, H2, anchor
  và vị trí link, văn phong, nguồn và trích dẫn, fact, giá live theo Site, CTKM có còn đúng
  thời điểm không, ảnh/caption/tên ảnh/thumb, dòng Nguồn, đồng bộ H1 với sheet và Drive), tự
  sửa lỗi rõ ràng, liệt kê phần cần user quyết, báo cáo từng bài.
user-invocable: true
when_to_use: >
  Trigger khi user gửi 1 hoặc nhiều link Google Doc bài PR báo điện tử/GuestPost (bất kỳ dự
  án, bất kỳ báo) và nói "duyệt bài này/các bài này", "check bài PR", "rà lại bài đăng báo",
  hoặc gửi 1 khoảng dòng sheet plan cần duyệt. Không dùng để VIẾT/viết lại bài (dùng
  `viet-bao-PR`), không dùng cho bài content trên site TGDĐ/ĐMX/TopZone.
---

# Duyệt bài PR báo điện tử

Skill này chạy SAU `viet-bao-PR`. Mục tiêu: kiểm lại bài theo đúng bộ rule đã dùng khi viết,
sửa ngay những lỗi rõ ràng, và đưa cho user những chỗ cần quyết.

**Bộ rule dùng chung với skill viết** (đọc trước khi duyệt, không chép lại rule ở đây để 2
skill không lệch nhau):

| File | Dùng để kiểm |
|---|---|
| `~/.claude/skills/viet-bao-PR/SKILL.md` | Bảng rule cứng + checklist tự kiểm |
| `~/.claude/skills/viet-bao-PR/references/van-phong-bao-pr.md` | Văn phong, title, sapo, H2, anchor, đoạn thương hiệu |
| `~/.claude/skills/viet-bao-PR/references/nguon-va-trich-dan.md` | Nguồn, giá, trích dẫn, rule Apple |
| `~/.claude/skills/viet-bao-PR/references/anh-bai-viet.md` | Ảnh, caption, ảnh ngoài, thumb |
| `~/.claude/skills/viet-bao-PR/references/ky-thuat-docs-drive.md` | Thao tác Docs/Drive/sheet |
| `~/.claude/skills/viet-bao-PR/references/du-an/<dự-án>.md` | Sheet, kho ảnh, đoạn thương hiệu, quy ước riêng dự án |

Rule trong các file trên thay đổi thì skill duyệt tự theo, không cần sửa file này.

## Bước 1. Xác định bài và đọc sheet

- Tìm đúng dòng trong sheet plan theo cột URL Doc khớp chính xác link Doc (không đoán theo
  tên báo). Đọc header thật (dòng 1) rồi map cột theo tên.
- Lấy: Site, Loại domain, Tên báo, Lưu ý của báo, AnchorText, URL đích, Tên đề tài, URL Doc,
  URL Hình, Trạng thái.
- User đang duyệt song song: đọc lại ô Trạng thái ngay trước khi sửa. Đã là `Xong` thì
  không sửa gì, ghi vào báo cáo.

## Bước 2. Đọc Doc

Chạy trước `python3 ~/viet-bao-pr/tools/review.py <row> [--tab <tab>] [--sheet <id>]`
(mặc định sheet plan iPhone 18, tab `Đề_Tài_Báo`). Script chỉ đọc, map cột theo tên header,
và kiểm tự động phần lớn checklist Bước 3: title/sapo/số từ/H2/FAQ, anchor và vị trí link,
dòng Nguồn, cụm cấm, tên báo VN, số lần trích nguồn, số ảnh, vị trí ảnh, kích thước ảnh
(Doc + file), caption, tên file ảnh theo slug, thumb, đồng bộ H1 với sheet/Doc/thư mục. Nó
đọc lưu ý của báo để lấy giới hạn chữ, số ảnh, cỡ thumb, rule link từ đoạn 3.

Output gồm `ISSUES` (lỗi theo rule) và `CHECK TAY` (giá, CTKM, fact, văn phong, nhìn ảnh).
Script không thay được việc đọc bài: vẫn đọc Doc (`gws docs documents get`) và làm đủ các mục
CHECK TAY. Rule đổi thì sửa script cho khớp.

## Bước 3. Chạy lại checklist viết

Đi lần lượt từng nhóm, ghi lại lỗi và mức độ.

**3.1 Cấu trúc và độ dài**
- Title (H1) ≤ 80 ký tự, có keyword sản phẩm, gợi tò mò mà vẫn đúng chất báo chí, không chép
  y đề tài, không từ tuyệt đối.
- Sapo 2 câu, ≤ 150 ký tự, có keyword chính, không link. Có đoạn mở bài ngắn dưới sapo.
- 2–3 H2 nội dung, H2 8–15 từ, có thông tin. GuestPost có FAQ ≥ 2 câu.
- **GuestPost (chốt 15/10/2026):** title/sapo/H2 ở trên KHÔNG áp, duyệt theo
  `~/.claude/skills/viet-bao-PR/references/guestpost-blog.md`: bài là blog evergreen (không mở
  bằng tin tức, không từ chỉ thời điểm dễ cũ), có dòng `Title SEO:` (= H1, 50–70 ký tự, keyword
  đứng đầu) và `Meta description:` (140–160 ký tự, mở bằng keyword) đầu Doc, sapo trả lời thẳng,
  3–5 H2 đánh số, mục mua hàng, FAQ, giọng tư vấn xưng "bạn". Thiếu Title SEO/Meta thì tự viết
  thêm. Bài GuestPost đang viết kiểu tin báo thì ghi đề xuất chuyển khung cho user quyết.
- Số từ: join toàn bộ `textRun.content` rồi `.split()`. So với lưu ý của báo, không ghi
  thì 900–950 từ.
- Dòng cuối bài là `Nguồn: <Site>` đúng Site.

**3.2 Anchor và link**
- Từng anchor: đúng nguyên văn cột AnchorText, đúng URL, link đúng 1 lần, đúng cụm (không
  dính chuỗi con/chuỗi cha), nằm trọn trong câu hoàn chỉnh, đọc lướt không lộ là câu chèn link.
- URL đúng domain theo Site: đối chiếu sheet KW của dự án (vd sheet `KW_SP` dự án iPhone 18).
  Sai thì báo user, không tự đổi URL. Ngoại lệ đã biết ghi trong file dự án (vd TopZone chèn
  ké URL TGDĐ là cố ý).
- Link đầu ở đoạn thân bài 1–3; báo tỉnh hoặc báo có yêu cầu riêng thì theo yêu cầu đó.
- Nhiều anchor thì rải theo đoạn liên quan, không dồn cuối.
- Không link ở title, sapo, heading, caption. Không có link thừa ngoài danh sách sheet.

**3.2b Search intent (chốt 15/10/2026)**
- Đọc đề tài gốc + link tham khảo (fact pack, hoặc lịch sử ô cột T nếu đã bị thay bằng H1),
  viết ra 1 câu intent. Title và từng H2 phải trả lời đúng intent đó.
- Lệch intent (H2 sinh ra từ chủ đề/domain báo, hoặc từ 1 ý phụ trong nguồn, vd lỗi 410
  lag.vn đưa "chơi game" lên title/H2) thì ghi rõ trong báo cáo kèm đề xuất title/H2 thay thế.
  Đổi góc là viết lại lớn nên để user quyết.

**3.3 Văn phong**
- Áp checklist skill `tranh-van-phong-ai` cho toàn bài (bắt buộc, kể cả bài người viết báo đã rà).
- Đọc như người đọc phổ thông chưa biết gì về chủ đề: câu nào phải đọc 2 lần mới hiểu thì tự
  viết lại (giữ ý, giữ fact). Đặc biệt soi các đoạn lấy ý từ nguồn nước ngoài, theo mục 5 "Viết
  cho người chưa biết gì" của `van-phong-bao-pr.md`.
- **Đọc liền mạch cả bài một lượt** trước khi sửa chữ (chốt 15/10/2026, lỗi bài 364): soi theo
  mục 5 "Mạch văn" của `van-phong-bao-pr.md`. Được tự sửa mạch trong đoạn: thêm từ nối, đổi thứ
  tự câu, viết lại câu chứa anchor/câu "số lượng có hạn"/câu cầu nối cho hoà vào đoạn, chuyển
  câu lạc ý sang đoạn hợp hơn, bỏ đoạn lặp ý sau đoạn thương hiệu. Giữ nguyên fact, số liệu,
  anchor. Đổi bố cục lớn (đổi H2, bỏ cả ý) thì ghi đề xuất cho user quyết.
- Không dấu chấm phẩy (;) và em dash (—) trong toàn bài, kể cả caption: tìm ký tự, có thì tự sửa
  (tách câu hoặc nối bằng phẩy + từ nối). Chốt 15/10/2026.
- Đối chiếu `van-phong-bao-pr.md`: mở bài từ vấn đề thật của người đọc; câu gãy gọn nhưng
  không cụt; ưu tiên số liệu; không câu sáo rỗng; không kiểu dịch word by word từ nguồn
  tiếng Anh; không giọng bán hàng; có nêu giới hạn/trade-off bằng giọng xây dựng; không
  quá tiêu cực.
- Đoạn thương hiệu có cầu nối tự nhiên, không nhảy đột ngột "X hiện đang bán...". Báo PR
  chỉ nhắc nhà bán lẻ ở đoạn này, TRỪ bài đề tài khuyến mãi/chương trình của nhà bán lẻ
  (chốt 15/10/2026): title phải có "tại <Site>" và đoạn giới thiệu chương trình ở vùng đầu
  phải nêu tên Site (viet-bao-PR van-phong-bao-pr.md mục 9). Thiếu thì tự thêm.
  Mọi bài: câu nêu cọc/giờ mở cọc/ngày giao lần đầu ở vùng đầu phải gắn tên Site ("Tại Thế
  Giới Di Động, ..."), thiếu thì tự thêm.

**3.4 Nguồn, trích dẫn, fact**
- Fact sản phẩm khớp nguồn hãng (ưu tiên bản tiếng Việt). Dự án có skill fact-check riêng
  thì chạy thêm (vd `check-content-iphone-18`).
- Trích dẫn: "Theo <hãng>" khoảng 2 lần/bài, tên trang bên thứ ba 1–2 lần, mỗi đoạn tối đa
  1 nguồn được gọi tên. Không nhắc tên báo Việt Nam. Không "Theo (ghi nhận từ) Thế Giới Di
  Động" trừ khi lưu ý của báo yêu cầu.
- Không biến "có thể/ước tính" thành "chắc chắn/hãng xác nhận". Không có nhận định gán cho
  nhà bán lẻ mà nhà bán lẻ chưa công bố.
- Apple: không có tin đồn, rò rỉ về sản phẩm chưa ra mắt; không có nội dung mổ xẻ máy.

**3.5 Giá**
- Mở trang sản phẩm trên web đúng Site (TGDĐ: thegioididong.com, TopZone: topzone.vn, ĐMX:
  dienmayxanh.com), đúng phiên bản, so từng con số giá trong bài.
- Bài dùng giá hãng thì đề tài phải thật sự cần giá hãng và câu văn ghi rõ là giá hãng
  công bố.

**3.6 CTKM có còn đúng thời điểm không**
- So đoạn thương hiệu/CTKM trong bài với đoạn đang áp dụng cho Site và giai đoạn hiện tại
  (file dự án, hoặc bản user đã xác nhận trong phiên). Chưa biết bản hiện hành thì hỏi user.
- Kiểm: còn đúng giai đoạn không (vd bài vẫn ghi "đặt trước" khi đã mở bán, "giao từ ngày X"
  khi đã qua), con số ưu đãi khớp chưa, tên Site và kênh liên hệ đúng Site chưa, ngày đăng dự
  kiến của bài còn nằm trong thời gian chương trình không.
- Báo giới hạn chữ thấp mà CTKM đã rút gọn: kiểm vẫn giữ tên site, ưu đãi chính, con số,
  kênh liên hệ.

**3.7 Ảnh**
- Số ảnh đúng (3 nếu báo không yêu cầu, báo cho tối đa N thì đủ N).
- Mỗi ảnh nằm sau đúng đoạn liên quan, rải đều, không dưới heading, không 2 ảnh liền nhau.
- **Kích thước ảnh trong Doc:** width đúng 460pt (sai là lỗi, vd 468pt hoặc 350pt), không bị
  crop trong Doc, tỉ lệ cao/rộng trong Doc khớp file gốc (không méo). File trên Drive: ảnh 1
  nguồn ngoài đúng 2048×1150; báo quy định chiều ngang tối thiểu thì file phải đạt; thumb đúng
  kích thước báo yêu cầu. Lấy cỡ Doc từ `embeddedObject.size`, cỡ file từ Drive
  `imageMediaMetadata(width,height)` (fileId nằm trong `imageProperties.sourceUri`).
- Caption: mô tả bám đoạn liền kề; ảnh có nguồn rõ thì ghi `... Ảnh: <nguồn>` đúng nguồn;
  ảnh chụp thực tế không rõ nguồn thì không ghi nguồn. Không link trong caption.
- Ảnh nguồn ngoài ≤ 2; bài có ảnh ngoài thì ảnh 1 là ảnh ngoài, cỡ 2048×1150, không watermark.
- Thư mục Ảnh trên Drive: tên file đúng `<slug-H1>-<stt>-thegioididong.<đuôi>`, stt khớp thứ
  tự trong bài, quyền `anyone:writer`, đã bắn metadata theo Site (chạy
  `python3 ~/viet-bao-pr/tools/metatag.py <row> --check`, ảnh nguồn ngoài cũng phải OK; LỖI hoặc
  THIẾU XMP thì chạy `metatag.py <row>` rồi kiểm lại). Báo có quy định thumb thì
  có file `<slug>-thumb-thegioididong.<đuôi>` đúng kích thước.

**3.8 Đồng bộ sheet và Drive**
- Cột Tên đề tài = H1 hiện tại (không còn dòng link tham khảo), tên Doc và tên thư mục bài
  khớp H1. Bước này skill viết đã làm; duyệt chỉ kiểm lại.

**Quét câu "thể lệ chưa rõ" (chốt 15/10/2026):** tìm "chưa rõ", "chưa nêu", "chưa ghi", "chưa có hướng dẫn", "hỏi rõ", "hỏi kỹ" gắn với CTKM của Site. Không giữ trong bài: bỏ câu, hoặc hỏi user thể lệ thật rồi viết khẳng định. Lời khuyên hỏi bên thứ ba (nhà mạng) thì được.

## Bước 4. Sửa

**Tự sửa luôn (lỗi rõ ràng, có căn cứ), ghi vào báo cáo:**
- Giá sai so với web đúng Site.
- Chính tả, Title Case ở heading, từ tuyệt đối, câu sáo/kiểu dịch ở mức sửa câu (không đổi
  fact, không đụng anchor).
- Caption thiếu hoặc sai format/nguồn; tên ảnh sai slug hoặc sai thứ tự; thiếu metadata.
- Ảnh sai width trong Doc (đưa về 460pt), ảnh 1 nguồn ngoài sai cỡ file (crop lại 2048×1150),
  thiếu thumb khi báo yêu cầu.
- Thiếu hoặc sai dòng `Nguồn: <Site>`.
- Sheet/Doc/thư mục chưa khớp H1.
- CTKM rút gọn khi báo giới hạn chữ thấp.

**Liệt kê cho user quyết, không tự sửa:**
- Vượt hoặc thiếu số từ: đề xuất đoạn cắt/bổ sung (ưu tiên cắt đoạn chung chung, ít giá trị).
- Fact chưa chắc, 2 nguồn mâu thuẫn.
- Anchor/URL sai so với sheet KW, thiếu anchor.
- CTKM lỗi thời mà chưa có bản mới được xác nhận.
- Viết lại lớn (đổi góc bài, đổi H2, viết lại cả đoạn).
- Thay ảnh khi kho không có ảnh phù hợp hơn.

## Quy tắc chống lệch index khi sửa Doc (bắt buộc)

Lỗi thật 15–16/09/2026: dùng index cũ sau khi Doc đã đổi độ dài, chèn caption vào giữa chữ.
1. Sau BẤT KỲ edit nào (kể cả 1 ký tự), fetch lại Doc trước khi tính index cho
   `insertText`/`deleteContentRange` tiếp theo. Không tự cộng trừ index cũ.
2. Sửa chữ: ưu tiên `replaceAllText` (khớp theo nội dung, không phụ thuộc index), chọn chuỗi
   đủ dài để chỉ khớp 1 chỗ.
3. Nhiều chỗ chèn theo index: làm từng chỗ, chèn xong → fetch lại → tính chỗ tiếp theo (hoặc
   gom trong 1 `batchUpdate` theo index giảm dần, tính từ cùng 1 lần fetch).
4. Chèn ngay trước 1 heading: gửi kèm `updateParagraphStyle` `NORMAL_TEXT` +
   `updateTextStyle` (`fontSize` 11pt, `bold: false`) cho đoạn vừa chèn, vì đoạn mới có thể
   dính style heading.
5. Xoá vùng cuối Doc: range không được chứa ký tự newline cuối cùng (trừ 1).
6. Sửa xong fetch lại, đọc đoạn quanh chỗ sửa để chắc không vỡ câu, rồi đếm lại số từ.

## Bước 5. Báo cáo

Duyệt nhiều bài thì mỗi bài 1 mục:

```
1. <Tên báo> — <link Doc>
Kết quả check: <lỗi đã tự sửa> | <việc cần user quyết> | <số từ, số ảnh, ảnh nguồn ngoài nếu có>

2. <Tên báo> — <link Doc>
Kết quả check: ...
```

Ngắn gọn, không chép lại nội dung bài. Bài không có lỗi thì ghi "Đạt, không phải sửa".
Không đổi cột Trạng thái trừ khi user dặn.

## Lỗi gws 403/404

Không bắt user login lại. Chạy `gws-fix-account`
(`bash ~/.claude/skills/gws-fix-account/scripts/gws_whoami.sh default --fix`) hoặc xoá
`~/.config/gws/token_cache.json`. Vẫn lỗi thì thử account còn lại theo CLAUDE.md.

## Duyệt nhiều bài bằng subagent

Prompt giao việc phải có: đường dẫn skill này và các file của `viet-bao-PR`, file dự án, bản
CTKM đang áp dụng, danh sách dòng/Doc, rule tự sửa và rule hỏi user ở Bước 4, tên file tạm
riêng cho từng agent. Agent báo xong thì tự fetch lại vài Doc để kiểm chéo trước khi báo user.
