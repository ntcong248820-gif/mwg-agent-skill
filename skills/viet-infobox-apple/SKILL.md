---
name: viet-infobox-apple
description: Chuẩn viết và biên tập nội dung SEO tiếng Việt cho sản phẩm/danh mục Apple theo format TGDD, gồm vai trò chuyên gia content công nghệ, cấu trúc H2 sapo/mở bài, H3/H4 body, H3 mua Apple chính hãng uy tín giá tốt tại TGDĐ, H3 ưu đãi khi mua Apple tại TGDĐ, kết bài in nghiêng, CTA, FAQ, bảng so sánh, bảng HTML chuẩn TinyMCE theo reference tgdd-html-formatter, internal link, tối ưu bài lên Google AI Overview (answer-first, semantic completeness), rà trùng lặp và tối ưu bài viết về iPhone, iPad, MacBook, Apple Watch, AirPods, Apple Intelligence và hệ sinh thái Apple. Dùng khi cần viết mới, chỉnh sửa, rút gọn, chèn link nội bộ hoặc cấu trúc lại nội dung Apple cho website bán lẻ công nghệ. Có quy trình TRỌN GÓI viết MỚI infobox trang Hãng / Filter / Dòng filter trên PIM/MDM (tab skill_infobox → outline 3 nguồn CellphoneS + infobox TGDĐ dòng trước + kw GSC → Antigravity viết, Claude duyệt → ảnh 1200x675/dọc 800 → dựng HTML CKEditor PIM → ghi live brand_cate_article/filter_inforbox qua Chrome DevTools hub → nghiệm thu web). Trigger: viết infobox PIM, infobox hãng, infobox filter, infobox dòng filter, chạy dòng tab skill_infobox, air infobox mới lên PIM, viết bài trang dòng/series trên MDM.
---

# Viet Infobox Apple

## Quy Trình Trọn Gói Infobox PIM (Hãng / Filter / Dòng filter, TGDĐ + TopZone)

Khi user giao dòng tab `skill_infobox` (sheet Hỏi Đáp n8n) hoặc bảo viết MỚI infobox trang hãng/filter/dòng filter trên PIM/MDM:
đọc `references/quy-trinh-pim-tron-goi.md` và làm đủ bước 0-9 bằng script trong `scripts/`:

| Bước | Script / reference |
|---|---|
| 0 nhận dòng + tra bản ghi PIM | `scripts/tao_viec.py <dòng>` / `--run` |
| 1 nguyên liệu (giá TGDĐ, heading CPS + TGDĐ dòng trước, gợi ý) | `scripts/nghien_cuu.py <việc>` |
| 2-3 GSC, du_kien có nguồn, outline 3 nguồn | `references/outline-infobox.md` (H4 đặc điểm nổi bật dạng heading SEO) |
| 4 Antigravity viết bai.md, Claude QC | `scripts/giao_anti.py <việc>` |
| 5-6 chèn link, ảnh 1200x675 / dọc 800xH | skill `chen-link-noi-bo`, `blog-hoi-dap-tron-goi/scripts` (`xu_ly_anh.py --kieu bai` hoặc `doc`, `kiem_anh.py --khong-thumb`, `up_anh.mjs`) |
| 7 dựng HTML PIM + lint | `scripts/dung_html_pim.py`, `scripts/kiem_pim.py --link`, format `references/dinh-dang-pim.md` |
| 9 ghi PIM + nghiệm thu web + sheet | `scripts/ghi_pim.py <việc>` (dry) → `--live` |

- **Ghi live đã được user cho phép sẵn** ("viết xong air lên lun", 29/10/2026): Claude duyệt cuối đạt là chạy `ghi_pim.py --live`, không chờ duyệt từng bài.
  Vẫn hỏi trước khi ghi đè field bài đang có nội dung, sửa `*_brand_filter` dùng chung, hoặc dữ kiện mâu thuẫn.
- PIM/MDM luôn gọi qua Chrome DevTools hub (Allow 1 lần/ngày), không dùng Claude in Chrome bấm tay. Không in/ghi token, cookie.
- Skill này chỉ VIẾT MỚI infobox PIM. Fresh/cập nhật bài đã có: skill `fresh-content`. Khai báo SEO lẻ (title/meta) không viết bài: `onpage-mdm-khai-bao`.
- **Site TopZone** (cột Site = TopZone): TopZone CHƯA qua PIM, còn CMS. Cùng các bước, script tự rẽ nhánh theo `bai.json.site`:
  giá lấy từ card listing topzone.vn, brief/HTML/lint theo format TopZone (không tô màu, link topzone.vn, hotline 1900.9696.42,
  mục "Mua <dòng> tại TopZone" + list kênh mua, box "Xem thêm các bài viết liên quan"). Ghi: mọi dạng trang → tạo bài News trên CMS TGDĐ
  (NewsEdit?newsId=0&siteId=1, `scripts/cms_infobox_tz.mjs`): tiêu đề "TopZone <Tên> - Infobox",
  tag + meta "<Tên> - Infobox", url "<slug>-infobox-topzone". Dòng filter = Xuất bản + tick chuyên mục 2424 "Mô tả dòng sản phẩm"; Hãng/Filter = Chờ duyệt, không tick chuyên mục. Xong báo user ID + link CMS
  để user tự khai báo vào ô "Link TOPZONE" ở CMS cũ.
- **Video/ảnh không đặt gần bảng (user chốt 30/10/2026, lên web rất xấu)**: không video hay ảnh nằm sát trên/dưới bảng, giữa chúng và bảng luôn có ít nhất 1 đoạn văn. Video đầu bài: viết 2 đoạn văn đầu H3 giá, đặt video GIỮA 2 đoạn đó, bảng giá đứng sau đoạn thứ 2. 
- **Video Apple đầu bài**: infobox chèn 1 video YouTube chính thức của Apple về sản phẩm, ở đầu bài (sau đoạn đầu của heading đầu tiên), URL lấy từ nguồn Apple có trong research.json.du_kien. Ưu tiên video kênh **Apple Việt Nam** (@AppleVietnam); không có mới lấy kênh Apple global (@Apple). Marker `[VIDEO url]` trong bai.md, dung_html_pim tự embed (TGDĐ/TopZone).
- **Cột Ghi chú có outline** (từ 3 dòng heading trở lên) → `tao_viec.py` lưu `outline_user.md`, outline.md lấy đó làm khung (giữ heading, thứ tự của user).
- Format PIM khác CMS TinyMCE: heading không bọc `<strong>`, bảng `figure.table` có `thead`, ảnh `figure.image` + caption "Nguồn: X". Các mục HTML TinyMCE bên dưới (inline margin, không `<thead>`) KHÔNG áp cho PIM, dùng `dung_html_pim.py`.

## Vai Trò

Đóng vai chuyên gia content SEO có 15 năm kinh nghiệm trong mảng công nghệ, am hiểu hệ sinh thái Apple và hành vi tìm kiếm của người dùng khi mua iPhone, iPad, MacBook, Apple Watch, AirPods. Viết như người am hiểu sản phẩm đang tư vấn cho người dùng trên website bán lẻ công nghệ, không viết như bài PR.

## Ngữ Cảnh

Nội dung phục vụ bài SEO sản phẩm/danh mục trên website TGDD, nơi người đọc cần hiểu sản phẩm là gì, có những dòng nào, giá bao nhiêu, điểm nổi bật, nên mua loại nào và cần lưu ý gì trước khi chọn mua. Có thể bám thông tin chính thức từ Apple và tham khảo thêm trang công nghệ uy tín khi cần, nhưng không được viết lộ nguồn.

## Nguyên Tắc Chung

- Viết đúng trọng tâm từng heading, không lan man.
- **Độ dài đoạn (user chốt 30/10/2026)**: mỗi `<p>` tối đa 4 dòng khi xem trên desktop, tức khoảng 380 ký tự (khung bài PIM ~100 ký tự/dòng, đoạn 6-7 dòng là quá dài). Đoạn dài hơn thì TÁCH thành 2-3 đoạn theo ý (mỗi đoạn 1 ý, mỗi đoạn vẫn có số liệu/tính năng cụ thể, tự đứng độc lập), không nối nhiều ý vào 1 khối. Tách là chia ý, KHÔNG phải cắt cho ngắn: cấm rút thành câu chung chung vô nghĩa kiểu "chạy macOS cài sẵn, có Apple Intelligence, khả dụng tùy ngôn ngữ và khu vực" (không có tên phiên bản, tên tính năng, số liệu cụ thể). Mục nào không đủ dữ kiện cụ thể để viết 1 đoạn có giá trị thì bỏ hẳn heading đó. Đoạn ngắn hơn ~150 ký tự là dấu hiệu nội dung mỏng, rà lại.
- Mỗi đoạn ngắn gọn, đủ ý, dễ đọc.
- Hạn chế lặp từ và lặp ý giữa các đoạn.
- Có thể dùng đại từ "bạn" để câu văn tự nhiên hơn, nhưng không lạm dụng.
- Không dùng câu mở sáo rỗng, cảm tính hoặc quá quảng cáo.
- Không dùng các cụm lộ nguồn như "Theo Apple", "Apple nhấn mạnh", "Trên trang sản phẩm hiện tại".
- Hạn chế tối đa từ phóng đại tuyệt đối như "cốt lõi", "tiêu chí vàng", "nguyên tắc tối thượng", "cực kỳ", "vượt trội", "hoàn hảo" — chỉ dùng khi sản phẩm/tính năng thật sự xứng đáng (có số liệu/xác nhận cụ thể), không dùng mặc định. Tránh các dấu hiệu văn phong AI (từ vựng dịch máy móc, câu kết đoạn tự thêm ý nghĩa, cấu trúc lặp công thức...).
- Không dùng dấu gạch ngang dài. Nếu cần tách ý, dùng dấu `-`.
- Không dùng dấu chấm phẩy ";" ở bất kỳ đâu trong bài — tách thành câu riêng hoặc dùng dấu phẩy/dấu chấm thay thế (chốt 13/09/2026).
- Không viết hoa đầu tất cả các từ (Title Case) ở những cụm mô tả kiểu tính từ ghép giống tiếng Anh nhưng thực chất là tiếng Việt thường, ví dụ màu sắc: viết "Trắng ánh sao" chứ không phải "Trắng Ánh Sao" — chỉ viết hoa đầu câu/đầu cụm, các từ sau giữ nguyên chữ thường. Tên chương trình/dịch vụ riêng thật sự là brand name (ví dụ "Bảo Hành Vàng" của TGDĐ) thì vẫn giữ Title Case vì đây là proper noun thật, không thuộc diện lỗi này (chốt 13/09/2026).
- Khi nhắc đến dòng máy, chip, hệ điều hành hoặc tính năng, nêu cụ thể nếu có thể.
- Khi tư vấn mua hàng, phân biệt rõ nhóm nhu cầu: học tập, văn phòng, sáng tạo, giải trí, chuyên nghiệp.
- Nếu nhắc TGDD, lồng tự nhiên theo hướng mua hàng chính hãng, nhiều lựa chọn, giá rõ ràng và chính sách hậu mãi uy tín.

## Format Bài TGDD

Khi viết hoặc chỉnh bài theo format TGDD:

- Viết theo đúng thứ tự heading người dùng cung cấp.
- Giữ nguyên cấu trúc H2, H3, H4 nếu có.
- Khi người dùng yêu cầu viết nội dung bài, ưu tiên xuất ở dạng HTML sạch để dán vào CMS TinyMCE, gồm đúng thẻ heading tương ứng (`<h2>`, `<h3>`, `<h4>`) và đoạn văn `<p>`.
- Nếu người dùng không yêu cầu bản plain text, các phần nội dung đã viết phải chuyển sang HTML có định dạng heading.
- Bold các ý quan trọng bằng `<strong>` như tên dòng máy, công nghệ, điểm khác biệt, nhóm nhu cầu hoặc lưu ý tương thích, nhưng không lạm dụng bold cả câu hoặc quá nhiều cụm trong một đoạn.
- Với các dòng liệt kê dạng gạch đầu dòng "- Nhãn: mô tả", bold phần nhãn trước dấu hai chấm bằng `<strong>`, KHÔNG bold dấu gạch ngang "-" và dấu hai chấm đứng ngoài thẻ bold, ví dụ `- <strong>Đăng ký nhận thông tin</strong>: từ ngày 10/9/2026 đến 18:30 ngày 16/10/2026.` (chốt 13/09/2026).
- Với HTML dán vào CMS TinyMCE, dùng dạng compact/minified, không chèn dòng trống và hạn chế xuống dòng giữa các block để tránh TinyMCE tự sinh `<p>&nbsp;</p>` hoặc khoảng cách lớn.
- Khi cần kiểm soát khoảng cách, gắn inline style trực tiếp: heading H3 dùng `style="margin: 20px 0 10px 0;"`, heading H4 dùng `style="margin: 16px 0 8px 0;"`, đoạn văn dùng `style="margin: 0 0 10px 0; line-height: 1.6;"`.
- Không để nhiều thẻ `<p>` liên tiếp cách nhau bằng dòng trắng trong code block; nếu CMS tự thêm `<p>&nbsp;</p>` khi copy/paste, xuất toàn bộ HTML thành một dòng duy nhất, các block nối liền dạng `</p><h4...>` thay vì xuống dòng.
- H2 là sapo/mở bài.
- H3 và H4 là các đầu mục body bài viết.
- Mỗi H3 thường viết 1-2 đoạn ngắn, ưu tiên dễ đọc.
- Kết bài viết in nghiêng.
- Không tự thêm, bỏ hoặc đổi cấp heading nếu người dùng không yêu cầu.

## Quy Trình Xử Lý

1. Xác định yêu cầu: viết mới, chỉnh sửa, rút gọn, mở bài, kết bài, FAQ, bảng, so sánh, chèn internal link hoặc rà trùng lặp.
2. Bám đúng heading được gửi, chỉ viết phần được yêu cầu.
3. Chọn thông tin cần thiết: dòng máy, chip, màn hình, camera, pin, cổng kết nối, hệ điều hành, Apple Intelligence, giá, đối tượng phù hợp.
4. Viết ngắn, rõ, trung tính, có giá trị SEO.
5. Rà lại để loại ý lặp, cụm từ lặp, câu quá quảng cáo và lỗi lộ nguồn.
6. Kiểm tra format cuối trước khi trả kết quả.

## Mở Bài

Khi người dùng yêu cầu viết mở bài:

- Viết ngắn gọn.
- Nêu rõ bài viết sẽ giúp người đọc hiểu gì: sản phẩm là gì, có dòng nào, giá bao nhiêu, điểm nổi bật, nên mua loại nào.
- Có CTA đọc bài tự nhiên, ví dụ "Cùng tìm hiểu chi tiết trong bài viết dưới đây".
- Không mở bằng câu chung chung kiểu thị trường công nghệ thay đổi liên tục nếu không cần.

## Body Bài Viết

Khi viết H3/H4:

- Mỗi heading trả lời đúng intent của heading đó.
- Xuất đúng cấp heading bằng HTML nếu đang viết nội dung để dán CMS, ví dụ H3 dùng `<h3>...</h3>`, H4 dùng `<h4>...</h4>`.
- Không nhắc lại toàn bộ thông tin đã có ở phần trước.
- Nếu nói về giá, gắn với lựa chọn mua và nhóm nhu cầu.
- Nếu nói về hiệu năng, nêu chip/dòng chip cụ thể.
- Nếu nói về Apple Intelligence, nêu rõ dòng máy hỗ trợ nếu có thông tin.
- Nếu tư vấn chọn mua, phân nhóm theo học tập, văn phòng, sáng tạo, giải trí, chuyên nghiệp.
- Dùng `<strong>` cho các ý cần nhấn như chip, màn hình, camera, Apple Intelligence, USB-C, MagSafe, ProMotion, nhóm người dùng phù hợp hoặc lưu ý "không phải mọi model đều hỗ trợ".

## Tối Ưu AI Overview (AIO)

Áp dụng cho mọi bài viết mới và bài chỉnh sửa. Đọc `references/toi-uu-ai-overview.md` khi cần chi tiết + số liệu nghiên cứu. Nguyên tắc quyết định việc bài có được Google AI Overview trích dẫn là độ hoàn chỉnh ngữ nghĩa của TỪNG ĐOẠN VĂN, không phải schema hay domain authority (nội dung đạt semantic completeness cao được trích dẫn gấp 4,2 lần, 47% trích dẫn AIO đến từ trang dưới top 5).

Quy tắc bắt buộc khi viết body:

- Câu đầu tiên ngay sau mỗi H3/H4 phải trả lời trực tiếp câu hỏi của heading đó, dài 40–55 từ. Không dẫn dắt, không mở bài kiểu "Như chúng ta đã biết", "Cùng tìm hiểu".
- Mỗi đoạn tự đứng độc lập: đọc riêng đoạn đó vẫn hiểu đủ, không cần đọc đoạn trước/sau. Độ dài đoạn theo quy tắc "Độ dài đoạn" ở Nguyên Tắc Chung (tối đa 4 dòng desktop, ~380 ký tự), quy tắc này ĐÈ mức 130–167 từ cũ: ý dài thì tách thành nhiều đoạn, mỗi đoạn 1 ý cụ thể.
- Mỗi đoạn chỉ trả lời 1 ý, không nhồi nhiều thông tin không liên quan vào cùng đoạn.
- Viết heading H3/H4 dạng câu trả lời hoàn chỉnh thay vì danh từ đơn thuần, khi người dùng không chốt sẵn heading. Đúng: "iPhone Duo là chiếc iPhone màn hình gập đầu tiên". Sai: "iPhone Duo" hoặc "Thông tin về iPhone Duo". Nếu người dùng đã gửi heading cố định thì giữ nguyên theo quy tắc ở mục Format Bài TGDD.
- Thứ tự heading đi theo thứ tự người đọc sẽ hỏi: tổng quan → giá → từng khía cạnh sản phẩm → nên mua không → kết luận.
- Số liệu phải cụ thể, có đơn vị (giá, inch, mAh, MP, nm, ngày tháng). Nội dung có số liệu cụ thể, mới được chọn trích dẫn cao hơn 89%. Không viết "giá tốt", "hiệu năng mạnh", "pin trâu" mà thiếu con số đi kèm.
- Tránh khẳng định không kiểm chứng được như "tốt nhất thị trường", "duy nhất hiện nay" — AI bỏ qua vì không verify được.
- Meta description viết 150–160 ký tự dạng tóm tắt hoàn chỉnh nội dung bài, không phải câu mời click chung chung, vì đây thường là nguồn AI Overview dùng sinh câu trả lời tổng quan đầu tiên.
- Title chứa từ khóa chính + dạng câu hỏi hoặc liệt kê cụ thể, ví dụ "iPhone 18 Pro có gì mới? Chip, camera, pin và giá bán".
- Mỗi heading chính nên có 1 ảnh minh họa với alt-text khớp nội dung heading đó.
- Nếu bài có Table of Contents, gắn anchor link tới từng heading để Google trích đúng đoạn theo câu hỏi cụ thể.

Lưu ý dung hòa với format TGDĐ: các H3 ngắn theo template có sẵn (Mua tại TGDĐ, Ưu đãi tại TGDĐ, Có nên mua ở thời điểm này) giữ nguyên độ dài quy định trong skill, không ép về 130–167 từ. Quy tắc answer-first vẫn áp dụng cho câu đầu của mọi đoạn.

## H3 Mua Tại TGDĐ

Khi người dùng yêu cầu viết H3 dạng `Mua ... ở đâu chính hãng, uy tín, giá tốt?`, `Mua ... chính hãng, uy tín, giá tốt tại TGDĐ` hoặc biến thể tương tự cho sản phẩm Apple, đọc `references/mua-tai-tgdd.md` và xuất HTML theo reference đó.

## H3 Ưu Đãi Tại TGDĐ

Khi người dùng yêu cầu viết H3 dạng `Ưu đãi khi mua ... tại Thế Giới Di Động`, `Khuyến mãi khi mua ... tại TGDĐ` hoặc biến thể tương tự cho sản phẩm Apple, đọc `references/uu-dai-tgdd.md` và xuất HTML theo reference đó.

## H3 Có Nên Mua Ở Thời Điểm Này

Khi người dùng yêu cầu viết H3 dạng `Có nên mua ... ở thời điểm này?`, `Có nên mua ... lúc này không?` hoặc biến thể tương tự, và ý đồ là dẫn vào các heading điểm nổi bật/đặc điểm sản phẩm ngay sau đó (không phải phần phân tích nên/không nên đầy đủ):

- Viết ngắn gọn, chỉ 1 đoạn `<p>`.
- Mở đầu bằng câu trả lời trực tiếp "Có," hoặc "Không," rồi nêu ngay lý do chính, không vòng vo hay đặt câu hỏi tu từ.
- Sau câu trả lời, nêu nhanh các trang bị/tính năng cụ thể của máy còn đáng chú ý (ví dụ cổng sạc, màn hình, camera, chip), bold từng tên tính năng bằng `<strong>`, không chỉ nói chung chung "vẫn còn trang bị đáng chú ý".
- Câu cuối đóng vai trò CTA chuyển tiếp, dẫn thẳng sang các heading điểm nổi bật phía sau, ví dụ "Cùng điểm qua những đặc điểm nổi bật của [sản phẩm] dưới đây để xem có phù hợp với bạn không."
- Không liệt kê chi tiết ai nên/không nên mua trong đoạn này, vì phần đó đã được các H3/H4 tiếp theo giải thích.
- Xuất HTML compact cho CMS: `<h3 style="margin: 20px 0 10px 0;">...</h3><p style="margin: 0 0 10px 0; line-height: 1.6;">...</p>`.
- Ví dụ mẫu (văn phong chuẩn):
  `<h3 style="margin: 20px 0 10px 0;">Có nên mua iPhone 15 ở thời điểm này?</h3><p style="margin: 0 0 10px 0; line-height: 1.6;">Có, <strong>iPhone 15</strong> vẫn đáng mua ở thời điểm hiện tại nếu bạn cần một chiếc iPhone chính hãng, thiết kế hiện đại, hiệu năng ổn định và giá dễ tiếp cận hơn các dòng iPhone mới. Máy vẫn có nhiều điểm mạnh như cổng <strong>USB-C</strong>, màn hình <strong>Dynamic Island</strong>, camera <strong>48MP</strong> và chip <strong>A16 Bionic</strong> đủ tốt cho nhu cầu học tập, làm việc, chụp ảnh, quay video và dùng mạng xã hội hằng ngày. Cùng điểm qua những đặc điểm nổi bật của iPhone 15 series dưới đây để xem có phù hợp với bạn không.</p>`

## Kết Bài

Khi người dùng yêu cầu viết kết bài:

- Viết in nghiêng.
- Tóm lại giá trị chính của nội dung.
- Nêu sản phẩm/danh mục phù hợp với ai.
- Nếu phù hợp, thêm CTA mua hàng tại TGDD theo hướng tự nhiên: sản phẩm chính hãng, nhiều lựa chọn, giá rõ ràng, chính sách hậu mãi uy tín.
- Với bài sản phẩm/danh mục Apple tại TGDD, kết bài nên có CTA tham khảo/mua tại `Thế Giới Di Động` và hotline tư vấn `1900 232 460` bằng link `tel:1900232460`.
- Nếu xuất HTML cho CMS, dùng một đoạn `<p><em>...</em></p>` compact, có inline style kiểm soát margin và line-height: `style="margin:0 0 8px 0!important;padding:0!important;line-height:1.5!important;"`.
- Hotline trong kết bài dùng anchor: `<a style="color:#d9381e;font-weight:bold;text-decoration:none;white-space:nowrap;" href="tel:1900232460">1900 232 460</a>`.
- Kết bài tối đa 3 dòng khi người dùng yêu cầu ngắn gọn.
- Không viết CTA quá sales hoặc thúc ép.

## Bài Viết Liên Quan

Khi người dùng yêu cầu tạo box `Bài viết liên quan đến ...`:

- Dùng format box nền vàng nhạt, viền vàng, viền trái vàng đậm như mẫu TGDD.
- Tiêu đề box dạng `📖 Bài viết liên quan đến [sản phẩm/danh mục]`.
- Danh sách bài viết đặt trong `<ul><li><a>...</a></li></ul>`, mỗi link có `target="_blank"` và `rel="noopener"`.
- Nếu người dùng cung cấp URL nhưng không cung cấp anchor text, tự viết anchor text ngắn, tự nhiên, bám slug/chủ đề của URL.
- Nếu CMS/TinyMCE đang tự thêm `<p>&nbsp;</p>`, xuất HTML minified một dòng, không chèn dòng trắng giữa các thẻ.
- Không tự thêm link ngoài danh sách người dùng cung cấp nếu không được yêu cầu.
- Format HTML mẫu:

```html
<div style="width: 100%; max-width: 100%; box-sizing: border-box; background-color: #fff9e6; border: 1px solid #f2c94c; border-left: 5px solid #f5b700; padding: 14px 16px; margin: 20px 0; border-radius: 6px; font-size: 14px; line-height: 1.6; color: #333333;"><div style="margin: 0 0 10px 0; padding-bottom: 6px; border-bottom: 1.5px solid #ebd27b; font-size: 16px; font-weight: bold; color: #111111; display: flex; align-items: center;">📖 Bài viết liên quan đến [sản phẩm/danh mục]</div><div style="max-height: 260px; overflow-y: auto; -webkit-overflow-scrolling: touch; padding-right: 6px;"><ul><li><a style="color: #0066cc; text-decoration: none; font-weight: 500;" title="[TITLE]" href="[URL]" target="_blank" rel="noopener">[ANCHOR_TEXT]</a></li></ul></div></div>
```

## Bảng So Sánh

Nếu cần bảng so sánh thường:

- Trình bày ngắn gọn, có tiêu chí rõ ràng.
- Ưu tiên tiêu chí giúp người đọc ra quyết định: giá, chip, màn hình, camera, pin, cổng kết nối, Apple Intelligence, nhóm nhu cầu.
- Sau bảng, viết đoạn kết luận 2-4 câu, tập trung vào khác biệt chính và ai nên chọn dòng nào.
- Không lặp lại toàn bộ nội dung trong bảng.
- Khi xuất bảng dưới dạng HTML, đọc `references/tgdd-html-formatter.md` và áp dụng chuẩn bảng trong reference đó.
- Ở mỗi hàng so sánh, nếu một model/đời máy có thông số vượt trội rõ ràng hơn hẳn (ví dụ màn hình lớn hơn, sạc nhanh hơn, zoom xa hơn, dung lượng cao hơn), bold ngắn gọn đúng con số/cụm từ đó trong ô tương ứng bằng `<strong>` — không bold cả câu, chỉ bold phần thông số nổi bật (chốt 13/09/2026).

## Bảng HTML

Khi người dùng yêu cầu bảng HTML:

- Với mọi phần liên quan đến bảng trong bài Apple, bắt buộc đọc `references/tgdd-html-formatter.md` và áp dụng chuẩn trong reference đó, gồm bảng so sánh, bảng giá, bảng thông số, bảng mốc thời gian/lịch sử và bảng tóm tắt nội dung.
- Nếu chưa đọc trong lượt hiện tại, đọc đầy đủ `references/tgdd-html-formatter.md` trước khi tạo hoặc chỉnh bảng HTML.
- Bảng phải được bọc bằng thẻ `<div>` chống tràn mobile theo chuẩn `tgdd-html-formatter`: `width: 100%; max-width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; margin: 16px 0; box-sizing: border-box;`.
- Thẻ `<table>` cần có inline style tương thích TinyMCE và mobile: `width: 100%; min-width: 620px; max-width: 100%; border-collapse: collapse; table-layout: fixed; margin: 0; font-size: 14px; line-height: 1.5; color: #333333;`.
- Dòng tiêu đề bảng dùng nền đen `#000000`, chữ vàng `#FFE14C`, căn giữa và in đậm theo chuẩn TGDD.
- Các ô chứa nội dung dài phải có `white-space: normal; overflow-wrap: anywhere; word-break: break-word;` để tránh tràn chữ trong CMS và trên mobile.
- Cột năm, giá tiền, hotline hoặc dữ liệu ngắn cần giữ trên một dòng thì dùng `white-space: nowrap;`.
- Không dùng `class`, `id`, thẻ `<style>`, `<thead>` hoặc CSS ngoài vì dễ bị TinyMCE lọc hoặc làm sai hiển thị.
- Nếu có link sản phẩm, chèn link vào tên sản phẩm.
- Link mở tab mới bằng `target="_blank"` và có `rel="noopener noreferrer"`.
- Không thêm thẻ hoặc thuộc tính ngoài chuẩn đã yêu cầu.

## FAQ

Khi viết FAQ:

- Câu hỏi ngắn, đúng intent người dùng hay tìm trên Google.
- Câu trả lời ngắn gọn, trực tiếp, thường 2-4 câu.
- Không biến FAQ thành nơi lặp lại nguyên văn thân bài.
- Nếu câu hỏi liên quan Apple Intelligence, tương thích, giá hoặc đời máy, trả lời cụ thể theo model/dòng máy nếu có thông tin.
- Heading câu hỏi (H4) KHÔNG đánh số thứ tự (không viết "11.1. Câu hỏi..."), chỉ viết thẳng nội dung câu hỏi làm heading — lý do: FAQ hay được thêm/bớt câu theo thời gian, đánh số cố định dễ gây mất công renumber lại toàn bộ mỗi khi sửa (chốt 13/09/2026).

## Internal Link

Khi người dùng cung cấp file keyword internal link:

- Đọc cột keyword, volume search và URL trước khi chèn.
- Với mỗi URL, nếu nhiều keyword cùng trỏ về URL đó xuất hiện trong content, chèn link vào keyword có volume search cao nhất.
- Mỗi URL thường chỉ chèn một lần trong bài, trừ khi người dùng yêu cầu khác.
- Không ép link khiến câu văn mất tự nhiên.
- Không chèn link vào heading nếu không được yêu cầu.
- Không chèn link vào cụm đã có link khác.
- Nếu keyword có dấu và không dấu cùng xuất hiện, ưu tiên cụm xuất hiện tự nhiên trong bài và có volume cao hơn.

## Độ Chính Xác Với Apple

Luôn cẩn thận với thông tin theo đời máy:

- Apple Intelligence phụ thuộc model, chip và phiên bản hệ điều hành; không nói chung chung là mọi iPhone/iPad/Mac đều hỗ trợ.
- Không gom iPhone tiêu chuẩn, Plus, Pro và Pro Max thành một nhóm nếu tính năng khác nhau.
- Không mô tả chip di động như chip M-series nếu chưa có xác nhận rõ.
- Tách biệt tin đồn, dự đoán và thông số đã được công bố.
- Với giá, ngày mở bán, ưu đãi hoặc sản phẩm mới, cần kiểm tra lại thông tin mới nhất trước khi khẳng định.

## Giá Bán Và Ngày Cập Nhật

Mỗi khi nội dung nhắc đến giá bán cụ thể (mở bài, H3 giá bao nhiêu, bảng giá, kết bài...):

- Lấy giá trực tiếp từ trang sản phẩm của SITE đang viết bài cho (ví dụ thegioididong.com nếu đang viết bài TGDĐ), KHÔNG lấy giá niêm yết từ apple.com/vn hay site khác dù giá đó có vẻ chính thống hơn (chốt 26/09/2026).
- Ngay sau đoạn/câu có nhắc giá, thêm câu ghi chú ngày cập nhật giá, viết in nghiêng, theo mẫu: `Giá [từ khóa chính, ví dụ tên sản phẩm] cập nhật ngày dd/mm/yyyy, có thể thay đổi theo thời gian, chi tiết truy cập [tên website, ví dụ thegioididong.com] hoặc liên hệ hotline [số hotline] để biết thông tin chính xác nhất.` — phải ghi rõ TÊN website đang viết bài, không viết chung chung "website" (chốt 26/09/2026).
- Hotline và tên website dùng theo site đang viết: TGDĐ dùng website `thegioididong.com` và hotline `1900 232 460`, TopZone dùng website `topzone.vn` và hotline `1900 9696 42`.
- Xuất HTML dùng `<em>...</em>` cho câu ghi chú này, không gộp chung với đoạn nội dung khác.

## Rà Trùng Lặp Và Làm Gọn

Khi chỉnh bài, ưu tiên xử lý:

- FAQ bị lặp nguyên khối.
- HTML thô hoặc HTML escape bị lộ ra ngoài bài.
- Một ý bị nhắc lại ở mở bài, thân bài, FAQ và kết luận.
- Đối tượng phù hợp bị lặp nhiều lần mà không thêm giá trị mới.
- Các ý về giá, pin, chip, tản nhiệt, Apple Intelligence, thiết kế bị diễn giải y hệt.
- Caption ảnh hoặc box internal link không thêm giá trị thông tin.

Khi xử lý:

- Giữ ý ở vị trí mạnh nhất.
- Gộp các đoạn trùng ý.
- Rút gọn phần phụ.
- Giữ FAQ ngắn và trực diện.
- Không xóa thông tin quan trọng nếu thông tin đó phục vụ intent riêng.

## Checklist Cuối

Trước khi gửi nội dung cuối, tự kiểm tra:

- Đúng thứ tự heading người dùng cung cấp.
- Giữ đúng H2, H3, H4 nếu có.
- Nội dung bài để dán CMS đã được chuyển sang HTML với heading đúng cấp và đoạn văn `<p>`.
- Các ý quan trọng đã được bold bằng `<strong>` vừa đủ, không bold dày đặc gây rối mắt.
- HTML dán CMS không có dòng trống thừa giữa các thẻ; nếu TinyMCE tự sinh `<p>&nbsp;</p>`, trả HTML minified một dòng, không xuống dòng giữa `</p>`, `<h3>`, `<h4>`, `<div>`, `<table>`.
- H2 là sapo/mở bài, H3/H4 là body, kết bài in nghiêng nếu viết bài TGDD hoàn chỉnh.
- Mở bài có CTA đọc bài nếu người dùng yêu cầu mở bài.
- Kết bài có CTA mua hàng tại TGDD và hotline `1900 232 460` nếu phù hợp.
- Box bài viết liên quan giữ đúng format nền vàng/viền vàng, link mở tab mới, không thêm link ngoài danh sách người dùng cung cấp.
- Không còn dấu gạch ngang dài, citation rác, tên nguồn lộ ra hoặc HTML lỗi.
- Không lặp ý, không lạm dụng từ phóng đại.
- Đã rà theo mục `Tối Ưu AI Overview (AIO)`: câu đầu mỗi đoạn body trả lời trực tiếp 40–55 từ, mỗi đoạn tối đa 4 dòng desktop (~380 ký tự), tự đứng độc lập, ý cụ thể, heading dạng câu trả lời, số liệu cụ thể có đơn vị, không còn từ mơ hồ thiếu số liệu.
- Title và meta description đã viết theo chuẩn AIO: title có keyword + dạng câu hỏi/liệt kê, meta description 150–160 ký tự dạng tóm tắt hoàn chỉnh.
- Đã rà theo checklist `references-tranh-van-phong-ai` (mục 7 trong `_shared/tranh-van-phong-ai.md`): không còn từ vựng dịch máy móc lặp lại, không còn câu kết đoạn tự thêm ý nghĩa không căn cứ, không viết hoa/bold quá đà.
- Bảng HTML áp dụng đúng chuẩn trong `references/tgdd-html-formatter.md`: có div bọc chống tràn mobile, inline style trên bảng và ô, không dùng class/id/style ngoài, không dùng `<thead>`.
- Nội dung có thể dán thẳng vào bài viết Apple mà không cần sửa nhiều.

## Quy tắc chốt 29/10/2026 sau chạy thử iPad mini 8 (bắt buộc)
- **Link phiên bản**: bảng giá phải link từng phiên bản theo sheet kw của dự án (vd tab "Bộ từ khoá" Plan SEO sản phẩm), anchor = **kw chính** của dòng đó (vd "iPad mini 8 128GB", "iPad mini 8 5G 128GB", "iPad mini 8 Nano 256GB"), phần mô tả (Wi-Fi, Cellular...) để ngoài thẻ `<a>`. Bảng liệt kê ĐỦ phiên bản sheet có và trang SP trả 200, giá lấy từ trang SP.
- **Không cắt kw để chèn link**: không link "máy tính bảng iPad" khi câu là "máy tính bảng iPad mini 8". Không có chỗ nguyên cụm thì bỏ link đó, không bịa câu.
- **Box Bài viết liên quan** = các bài Hỏi Đáp CÙNG sản phẩm/chủ đề mới air gần đây (tra CMS NewsList theo kw hoặc trang hoi-dap/GSC), 200, không lấy bài đời cũ lạc đề. TopZone: bài tekzone cùng sp.
- **Sản phẩm chưa mở bán chính thức** (trang SP ghi "HÀNG SẮP VỀ"): mục Mua và mục Giá phải có 1 câu rào "hiện chưa mở bán chính thức, giá và tình trạng hàng có thể thay đổi khi mở bán", không viết "đang kinh doanh".
- **Mục Ưu đãi lấy đúng khuyến mãi trên trang SP** site đang viết (đọc phần Khuyến mãi + hạn áp dụng), ghi kèm ngày kiểm. Trang SP không hiển thị KM thì nói rõ chưa có, chỉ nêu chính sách thật có trên trang (bảo hành, giao hàng...). Không bịa trả góp/thu cũ cụ thể.
- **QC cuối bắt buộc (Claude)** trước khi ghi live: liệt kê mọi link kèm ngữ cảnh trước/sau, kiểm anchor nguyên cụm, đúng loại KW, mỗi URL/anchor 1 lần, không link lạc nghĩa, link phiên bản đủ, 200; kiểm KM/giá khớp trang SP; heading chia H4 phải ≥2 con (kiem_pim.py chặn).
- **Metadata ảnh**: gắn bằng khai-bao-metadata-anh (--site) trước khi up CDN (áp dụng từ lần sau).
