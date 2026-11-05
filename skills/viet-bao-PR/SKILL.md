---
name: viet-bao-PR
description: >
  Viết mới, viết lại, enrich hoặc đổi đề tài bài PR báo điện tử và GuestPost cho mọi dự án
  sản phẩm (điện thoại, laptop, tai nghe, đồng hồ, TV, gia dụng... của Apple, Samsung, Sony
  và các hãng khác) thuộc TGDĐ, TopZone, ĐMX. Gồm: đọc sheet plan lấy anchor và lưu ý của
  báo, tạo Drive (thư mục bài, Doc, thư mục Ảnh), research theo thứ bậc nguồn hãng tiếng Việt
  > nguồn hãng quốc tế > trang công nghệ nước ngoài uy tín, viết văn phong báo chí tự nhiên (GuestPost: blog evergreen chuẩn SEO theo mẫu TGDĐ hỏi đáp, có Title SEO + Meta description)
  và hữu ích (title gợi tò mò, sapo 2 câu chuẩn SEO, 2–3 H2, anchor tự nhiên ở vùng đầu),
  dẫn dắt mượt vào đoạn thương hiệu, chạy tranh-van-phong-ai, chèn Google Doc, tự verify
  rồi cập nhật sheet.
user-invocable: true
when_to_use: >
  Trigger khi user giao đề tài (1 dòng, nhiều dòng hoặc 1 khoảng dòng trong sheet plan báo
  PR, hoặc brief dán thẳng) để viết bài PR báo điện tử/GuestPost cho bất kỳ sản phẩm, dự án
  nào; khi user muốn viết lại, bổ sung thông tin mới cho bài đã có, hoặc đổi đề tài; khi user
  muốn chia subagent viết song song cả batch. Không dùng để DUYỆT bài đã viết xong (dùng
  `duyet-bao-PR`), không dùng để chọn báo/phân bổ anchor (dùng `phan-bo-bao-pr`).
---

# Viết bài PR báo điện tử

Skill dùng chung cho mọi dự án. Rule riêng của từng dự án (sheet, đoạn thương hiệu, lịch
mở bán, quy ước tên sản phẩm) nằm trong `references/du-an/<dự-án>.md`.

| File | Đọc khi nào |
|---|---|
| `references/van-phong-bao-pr.md` | **Luôn đọc trước khi viết.** Văn phong, title, sapo, H2, anchor, đoạn thương hiệu, ví dụ đúng/sai |
| `references/nguon-va-trich-dan.md` | Khi research và khi viết câu có số liệu, nhận định |
| `references/anh-bai-viet.md` | Khi làm ảnh: chọn ảnh từ kho, số lượng, vị trí, caption, ảnh ngoài, thumb |
| `references/ky-thuat-docs-drive.md` | Khi tạo Drive, chèn Doc, upload/chèn ảnh, ghi sheet |
| `references/guestpost-blog.md` | **Bắt buộc khi Loại domain = GuestPost**: blog evergreen theo mẫu TGDĐ hỏi đáp, Title SEO + Meta description, H2 đánh số, FAQ. Ghi đè các rule title/sapo/H2 của báo PR |
| `references/du-an/<dự-án>.md` | Khi đề tài thuộc dự án đã có file (vd `iphone-18.md`) |

## Bài viết phải đạt cùng lúc 3 mục tiêu

1. **Hữu ích thật cho người đọc.** Người đọc xong biết thêm điều cụ thể: con số, cách chọn,
   điểm khác biệt, chi phí, ai hợp với sản phẩm nào.
2. **Sản phẩm, thương hiệu xuất hiện tự nhiên.** Sản phẩm là lời giải cho vấn đề trong bài,
   không phải nhân vật được tâng bốc.
3. **Hỗ trợ SEO.** Keyword nằm tự nhiên trong title, sapo, H2; anchor đúng 100%; bài phủ
   đủ các ý người tìm kiếm cần.

Không viết kiểu liệt kê thông số. Bài luôn bắt đầu từ 1 vấn đề, nhu cầu, tình huống hoặc
câu hỏi thật của người dùng, rồi mới đưa sản phẩm vào để giải quyết hoặc phân tích.

## Trước khi viết: hỏi user 1 việc

**Đoạn giới thiệu thương hiệu** thay đổi theo dự án và theo giai đoạn (mở bán, đặt cọc, sau
mở bán...). Trước khi viết bài đầu tiên của 1 phiên hoặc 1 batch, LUÔN hỏi user đoạn đang
dùng:
- Nếu file dự án đã lưu sẵn đoạn của giai đoạn trước, đưa đoạn đó ra và hỏi "vẫn dùng bản
  này, hay có bản mới?".
- Chưa có thì hỏi user gửi đoạn CTKM/giới thiệu và cách dẫn (Site nào, ưu đãi nào, kênh
  liên hệ).
- Trong cùng 1 batch đã được xác nhận thì không hỏi lại từng bài.

Nếu file dự án chưa có đường dẫn **kho ảnh báo PR**, hỏi luôn user trong lần này.

Hỏi kèm luôn những gì còn mơ hồ và ảnh hưởng tới nội dung (vd 2 nguồn chính thức mâu thuẫn).
Những việc có quy ước sẵn thì tự làm, không hỏi.

## Quy trình 10 bước

1. **Đọc đề tài.** Từ sheet plan hoặc brief user dán. Với sheet: đọc header thật (dòng 1)
   rồi map cột theo TÊN header, không tin chữ cái cột trong trí nhớ. Cần lấy: Site, Loại
   domain (Báo PR/GuestPost), Tên báo, Lưu ý của báo, AnchorText, URL đích, Tên đề tài
   (dòng 1 là đề tài, dòng sau là link tham khảo), Phụ trách, URL Doc, URL Hình, Trạng thái.
   Ô anchor/URL có nhiều dòng thì tách `\n` và ghép cặp theo thứ tự.
2. **Kiểm anchor.** Anchor dùng NGUYÊN VĂN, kể cả khi viết khác chính tả thông thường. Chỉ
   kiểm URL có đúng domain theo Site không; nghi sai thì đối chiếu sheet KW của dự án rồi
   báo user, không tự đổi.
3. **Tạo Drive sớm.** Thư mục bài trong thư mục "Báo PR" (ID trong file dự án), gồm Doc và
   thư mục `Ảnh`, set `anyone:writer`, điền link vào cột Doc/Hình ngay để user chuẩn bị ảnh
   song song.
4. **Research.** Theo `references/nguon-va-trich-dan.md`. Đọc link tham khảo để hiểu search
   intent, góc bài, cấu trúc; viết lại hoàn toàn, không sao chép câu chữ.
5. **Lập dàn ý.** Trước tiên chốt **search intent** trong 1 câu, lấy từ đề tài + link tham khảo
   cột T (không lấy từ domain báo). Xem mục "Giữ đúng search intent" bên dưới. Sau đó: người đọc đang hỏi gì → title trả lời câu hỏi đó → 2–3 H2, mỗi
   H2 giải quyết 1 luận điểm thực tế → đặt sẵn mỗi anchor vào đoạn có ngữ cảnh hợp, link đầu
   tiên trong đoạn thân bài 1–3 → chọn chỗ dẫn vào đoạn thương hiệu.
6. **Viết.** Theo `references/van-phong-bao-pr.md`.
7. **Rà văn phong.** Chạy skill `tranh-van-phong-ai` cho TOÀN BÀI (bắt buộc, kể cả bài
   enrich/sửa, kể cả bản nháp do Anti/subagent viết: người biên tập cuối vẫn phải tự chạy lại),
   rồi tự kiểm bằng checklist cuối file này. Tìm ký tự `;` và `—` trong toàn bài, có thì sửa
   (không dùng dấu chấm phẩy, chốt 15/10/2026). Cuối cùng **đọc liền cả bài một lượt** từ
   title tới dòng Nguồn để soi mạch văn (van-phong-bao-pr.md mục 5 "Mạch văn"): đoạn nào đọc
   như danh sách fact, câu nào nhảy ý, câu bắt buộc (anchor, số lượng có hạn, mốc ngày) nào
   bị dán vào thì viết lại cả đoạn, không vá từng câu. Sửa xong mới chèn Doc.
8. **Làm ảnh.** Theo `references/anh-bai-viet.md`: lấy ảnh từ kho ảnh của dự án, xem ảnh
   rồi ghép với đúng đoạn liên quan, rải đều toàn bài. Số lượng: 3 ảnh nếu báo không yêu
   cầu, báo cho tối đa N ảnh thì chèn đủ N. Mỗi ảnh có caption `... Ảnh: <nguồn>`. Kho chưa có
   ảnh phù hợp mới lấy ảnh hãng hoặc trang nước ngoài uy tín, tối đa 2 ảnh ngoài/bài, ảnh ngoài luôn làm ảnh 1
   (bài so sánh ưu tiên ảnh ghép sẵn, không có thì tự ghép). Upload vào thư mục Ảnh, đặt tên theo
   slug title. Báo quy định kích thước thumb thì resize 1 ảnh làm thumb và upload lên Drive.
   Mọi ảnh, nhất là ảnh nguồn ngoài tự tìm, phải gắn metadata theo Site sau khi chốt H1 và
   caption: `metatag.py <row>` rồi `metatag.py <row> --check` (anh-bai-viet.md mục 5).
9. **Chèn Doc và verify độc lập.** Chèn bằng Docs API, fetch lại Doc để kiểm (không tin kết
   quả `batchUpdate` trả `{}`).
10. **Cập nhật sheet.** Cột Tên đề tài = title H1 mới (xoá dòng link tham khảo trong ô); đổi
    tên Doc và thư mục bài theo H1; bắn metadata ảnh theo Site; cột Trạng thái =
    `Chờ duyệt` (không ghi `Xong`). Nếu user dặn không set trạng thái thì bỏ bước này.

## Rule cứng

| Hạng mục | Rule |
|---|---|
| Độ dài | Theo lưu ý của báo. Báo không ghi gì thì 900–950 từ (tối thiểu 900, tối đa 950) |
| Title | ≤ 80 ký tự, có keyword sản phẩm, gợi tò mò, đúng chất báo chí, không chép y đề tài |
| Sapo | 2 câu (trừ khi báo yêu cầu khác), ≤ 150 ký tự để dùng làm meta description, chứa keyword chính, không link. Ngay dưới sapo được viết thêm 1 đoạn mở bài ngắn |
| Thân bài | 2–3 H2 nội dung, mỗi H2 một luận điểm; H2 8–15 từ, có thông tin, không cụt |
| Anchor | Nguyên văn, mỗi anchor link đúng 1 lần, nằm trọn trong câu hoàn chỉnh |
| Vị trí link | Link đầu ở đoạn thân bài 1–3 (không tính sapo). Báo tỉnh hoặc báo có yêu cầu riêng thì theo yêu cầu đó (báo tỉnh: từ đoạn 3 trở đi) |
| Cấm link | Title, sapo, H2, H3, caption ảnh |
| Dòng nguồn cuối bài | Dòng cuối cùng của bài, đúng 1 dòng theo Site: `Nguồn: Thế Giới Di Động` / `Nguồn: TopZone` / `Nguồn: Điện Máy Xanh` |
| Ảnh | 3 ảnh nếu báo không yêu cầu, báo cho tối đa N thì chèn đủ N; ảnh từ kho dự án; rải đều theo đoạn liên quan; caption `... Ảnh: <nguồn>`; tối đa 2 ảnh nguồn ngoài/bài; có ảnh ngoài thì ảnh ngoài là ảnh 1 |
| Báo PR vs GuestPost | Báo PR: chỉ nhắc nhà bán lẻ ở đoạn thương hiệu. **Ngoại lệ bài đề tài khuyến mãi/chương trình của nhà bán lẻ (chốt 15/10/2026):** title có "tại <Site>" và đoạn giới thiệu chương trình ở vùng đầu (đoạn thân bài 1–2) nêu tên Site (van-phong-bao-pr.md mục 9). Không viết "Theo (ghi nhận từ) Thế Giới Di Động" trừ khi lưu ý của báo yêu cầu (vd VnExpress). **GuestPost (chốt 15/10/2026): viết dạng blog evergreen, không phải tin báo**, theo `references/guestpost-blog.md`: dòng Title SEO + Meta description đầu Doc, title keyword đứng đầu 50–70 ký tự (được câu hỏi), meta 140–160 ký tự, sapo trả lời thẳng, 3–5 H2 đánh số, mục mua hàng, FAQ ≥ 2 câu, giọng tư vấn xưng "bạn". Các dòng Title/Sapo/Thân bài ở bảng này chỉ áp cho báo PR |
| Nguồn | Hãng (bản tiếng Việt) > hãng (bản quốc tế) > trang công nghệ nước ngoài uy tín. Không nhắc tên báo Việt Nam khác |
| Trích dẫn | Trích ít, viết thẳng. "Theo Apple/hãng" tối đa ~2 lần/bài; tên trang thử nghiệm bên thứ ba tối đa 1–2 lần/bài; mỗi đoạn tối đa 1 nguồn được gọi tên; fact chung từ trang nước ngoài viết thẳng |
| Giá | Giá đang hiển thị lúc viết trên web của đúng Site: TGDĐ lấy thegioididong.com, TopZone lấy topzone.vn, ĐMX lấy dienmayxanh.com. Chỉ dùng giá hãng khi đề tài bắt buộc nói tới giá hãng, và ghi rõ là giá hãng công bố |
| Nguồn tiếng Anh | Không dịch word by word: hiểu ý rồi viết lại theo cách người Việt nói (xem mục 5 file văn phong) |
| Apple | Không viết tin đồn, rò rỉ về sản phẩm chưa ra mắt chính thức. Không viết bài mổ xẻ, tháo máy |
| Giọng | Trung tính, có thông tin, không tâng bốc, không viết quá tiêu cực hay chê bai |
| Fact | Không bịa số liệu, ý kiến, nhận định. Không tìm được nguồn thì bỏ ý đó |
| Thể lệ CTKM chưa rõ | Không viết "chưa rõ / chưa có hướng dẫn / nên hỏi kỹ khi đặt" về CTKM của chính Site (chốt 15/10/2026). Ghi vào "Cần Claude quyết" để hỏi user trước khi chèn Doc, chưa có trả lời thì bỏ ý |
| Search intent | Title + mọi H2 trả lời đúng intent của đề tài và link tham khảo cột T. Không bẻ góc theo chủ đề/domain báo. Ý phụ không được lên title/H2 (xem mục "Giữ đúng search intent") |
| Mạch văn | Mỗi đoạn trả lời 1 câu hỏi, câu sau móc vào câu trước, đoạn sau nối đoạn trước. Câu bắt buộc (anchor, số lượng có hạn, mốc ngày, cầu nối) phải hoà vào đoạn. Sau đoạn thương hiệu chỉ còn dòng Nguồn (van-phong-bao-pr.md mục 5 "Mạch văn") |
| Dễ hiểu | Người đọc phổ thông đọc 1 lần là hiểu. Đoạn lấy ý từ nguồn nước ngoài phải viết lại theo cách người Việt nói (van-phong-bao-pr.md mục 5) |

## Giữ đúng search intent (chốt 15/10/2026)

Lỗi thật dòng 410 (lag.vn): đề tài "Adaptive Power… nên bật hay tắt", link tham khảo là trang
hỗ trợ Apple + bài Tom's Guide về pin dừng sạc ở 80%. Bài lại đưa "chơi game" lên title và H2
đầu, vì lag.vn là site game và trang Apple có đúng 1 câu nhắc Chế độ trò chơi.

- **Intent = đề tài + link tham khảo.** Viết ra 1 câu "người tìm muốn biết gì" trước khi lập
  dàn ý. Title và từng H2 phải trả lời một phần của câu đó.
- **Domain báo không đổi intent.** Báo game, báo gia đình, báo thiết kế, báo tỉnh... vẫn viết
  đúng intent gốc. Domain chỉ quyết định giới hạn ở cột Lưu ý (số từ, sapo, link) và các báo
  không nhận bài so sánh. Không thêm H2, không đổi title để "hợp chất báo".
- **Ý phụ không lên title/H2.** Một chi tiết chỉ xuất hiện thoáng qua trong nguồn (1 câu, 1 ngoại
  lệ, 1 tình huống) thì đặt trong thân đoạn, không nâng thành luận điểm.
- **Hai báo cùng đề tài:** tạo khác biệt bằng cách đổi thứ tự, đổi ý trọng tâm hoặc đổi cách
  trình bày giữa các ý *nằm trong* intent gốc (vd bài A giải thích cơ chế, bài B đi theo câu hỏi
  "bật hay tắt" và chuyện pin dừng 80%). Không mở thêm góc ngoài intent cho khác.
- **Tự kiểm:** che tên báo đi, đọc title + H2. Người vừa search đề tài có thấy đúng câu trả lời
  mình cần không? Nếu đoán được tên báo qua heading thì đã lệch.

## Checklist tự kiểm trước khi chèn Doc

Đọc lại cả bài như biên tập viên báo, trả lời từng câu:

- [ ] (GuestPost) Bài là blog evergreen, không có từ chỉ thời điểm dễ cũ? Có dòng Title SEO + Meta description đúng độ dài, keyword đứng đầu? H2 đánh số, có mục mua hàng và FAQ? (guestpost-blog.md)
- [ ] Bài mở bằng vấn đề/nhu cầu thật của người đọc chứ không mở bằng thông số hay câu sáo?
- [ ] Người đọc xong có thêm được ít nhất 2–3 thông tin cụ thể dùng được (số liệu, cách chọn, chi phí)?
- [ ] Keyword chính có trong title, sapo, ít nhất 1 H2, và đọc vẫn tự nhiên? Có chỗ nào nhồi keyword không?
- [ ] Từng anchor đúng 100% nguyên văn, đúng URL, link đúng 1 lần, đúng cụm (không dính chuỗi con/chuỗi cha)?
- [ ] Câu chứa anchor đọc lướt có bình thường không, hay lộ ra là câu chèn link?
- [ ] Link đầu nằm ở đoạn thân bài 1–3 (hoặc đúng yêu cầu riêng của báo)? Nhiều anchor thì đã rải theo đoạn liên quan, không dồn cuối?
- [ ] Có câu nào quá quảng cáo, có từ tuyệt đối ("tốt nhất", "hoàn hảo", "vượt trội"...) không?
- [ ] Có nêu giới hạn/trade-off của sản phẩm với giọng xây dựng không?
- [ ] Title và từng H2 có trả lời đúng intent của đề tài + link tham khảo không? Có H2 nào sinh ra từ chủ đề của báo (game, gia đình, thiết kế...) hoặc từ 1 câu phụ trong nguồn không?
- [ ] Có câu nào đọc như dịch từ tiếng Anh, khó hiểu, hoặc cụt ý không? Đoạn lấy ý từ nguồn tiếng Anh, người chưa đọc nguồn có hiểu ngay không? Khái niệm lạ đã được giải thích ngay lần đầu chưa?
- [ ] Giá trong bài khớp giá đang hiển thị trên web của đúng Site (TGDĐ/TopZone/ĐMX) (hoặc ghi rõ là giá hãng nếu đề tài bắt buộc)?
- [ ] Nhận định nào cũng dựa trên số liệu/nguồn? Độ chắc chắn giữ đúng như nguồn ("có thể" không thành "chắc chắn")?
- [ ] (Bài đề tài KM/chương trình của nhà bán lẻ) Title có "tại <Site>" và đoạn giới thiệu chương trình ở vùng đầu có nêu tên Site chưa?
- [ ] Đoạn thương hiệu có cầu nối tự nhiên, không nhảy đột ngột "X hiện đang bán..."?
- [ ] Title đủ hấp dẫn mà vẫn đúng chất báo chí, ≤ 80 ký tự? Sapo 2 câu, ≤ 150 ký tự, có keyword?
- [ ] Ảnh đủ số lượng, đúng đoạn liên quan, rải đều, caption có nguồn, không quá 2 ảnh ngoài, có thumb nếu báo yêu cầu? Mọi ảnh (kể cả ảnh ngoài) đã gắn metadata theo Site, `metatag.py <row> --check` ra OK?
- [ ] Dòng cuối bài là `Nguồn: <Site>` đúng Site?
- [ ] Đọc liền cả bài một lượt: mỗi đoạn có trả lời đúng 1 câu hỏi không, câu nào đứng riêng không móc được vào câu trước, đoạn nào đọc như danh sách fact?
- [ ] Câu chứa anchor, câu "số lượng có hạn", mốc ngày có nằm đúng ý của đoạn không, hay bị dán thêm vào?
- [ ] Câu cầu nối có dẫn đúng vào nội dung đoạn thương hiệu không? Sau đoạn thương hiệu có còn đoạn lặp ý nào không (chỉ được còn dòng Nguồn)?
- [ ] Khi cắt số từ, có lỡ cắt mất từ nối/vế "vì sao" làm câu rời nhau không?
- [ ] Đã chạy `tranh-van-phong-ai` cho toàn bài? Toàn bài (kể cả caption) không còn dấu chấm phẩy `;` và em dash `—`?

## Báo cáo cuối cho user (tiếng Việt)

Mỗi bài: title, link Doc, số từ, vị trí từng anchor (đoạn số mấy, câu nào), danh sách nguồn
(URL), danh sách ảnh (từ kho hay nguồn ngoài, kèm URL) và thumb nếu có, đoạn thương hiệu đã rút gọn hay chưa, các điểm chưa chắc cần user duyệt.

## Viết song song bằng subagent

- Prompt giao việc phải tự chứa đủ: cách đọc sheet, đoạn thương hiệu user đã xác nhận, đường
  dẫn tới SKILL.md này và các file references cần đọc, file dự án, rule riêng của từng báo.
- Fact pack/brief phải ghi câu search intent (từ đề tài + link tham khảo) và nhắc rule "Giữ
  đúng search intent". Người lập fact pack không được gợi ý góc bài theo domain báo.
- Prompt cho cả người viết (Anti/subagent) lẫn người duyệt phải ghi rõ: bắt buộc đọc và áp
  `~/.claude/skills/tranh-van-phong-ai/SKILL.md` cho toàn bài, không dùng dấu chấm phẩy.
- Fact pack không chỉ là danh sách F1..Fn (lỗi bài 364: người viết biến mỗi fact thành một câu
  rời). Fact pack phải có dàn ý theo mạch lập luận: mỗi đoạn trả lời câu hỏi gì, dùng fact nào,
  nối sang đoạn sau bằng ý gì, câu bắt buộc nằm ở đoạn nào và mang ý gì.
- Người biên tập cuối (Claude) nhận bản nháp thì đọc liền cả bài trước, sửa theo đoạn. Không
  sửa nhiều vòng ở mức câu (thêm câu bắt buộc, cắt từ) mà không đọc lại cả bài.
- Mỗi agent dùng tên file tạm riêng (có số dòng trong tên) để không ghi đè lẫn nhau.
- Agent báo xong thì vẫn tự fetch lại từng Doc và verify như bước 9. Agent tự báo "đã review"
  vẫn từng sót lỗi thật.
- Script và brief lưu ở `~/viet-bao-pr/tools/` (scratchpad bị xoá khi reboot).

## Lỗi gws 403/404

Không bắt user login lại. Chạy skill `gws-fix-account`
(`bash ~/.claude/skills/gws-fix-account/scripts/gws_whoami.sh default --fix`), hoặc xoá
`~/.config/gws/token_cache.json` rồi thử lại. Vẫn lỗi thì thử account còn lại theo CLAUDE.md.

## Skill liên quan

`tranh-van-phong-ai` (bắt buộc ở bước 7), `duyet-bao-PR` (duyệt sau khi viết),
`phan-bo-bao-pr` (chọn báo, phân anchor, phân đề tài), `check-content-iphone-18` (fact-check
riêng dự án iPhone 18).
