# Quy tắc viết và trình bày

Số liệu dẫn ở đây đo trên 58 Doc mô tả IT ngày 09/10/2026.

## Nguyên tắc gốc — chỉ nhu cầu + data

IT chỉ cần biết **vấn đề, mong muốn, vị trí hiển thị, data cần nhập**. Cách xử lý là việc
của IT. Owner chê Doc Giới thiệu hãng (28/09/2026) là "trình bày dư thừa" vì kể chuyện SEO.

| Không viết | Vì |
| --- | --- |
| "SEO đã sửa link / gỡ link / chọn ngành nhiều SP nhất…" | IT không cần biết SEO đã làm gì |
| Số liệu rà soát: bao nhiêu hãng giống/khác, bao nhiêu link sai | Log rà soát giữ ở task folder |
| Đề xuất cách code, tên bảng DB, framework | Lấn việc IT, dễ sai |
| Lý thuyết SEO dài | 1 câu lợi ích + 1 link Google Search Central là đủ |

Được giữ số **phạm vi** (172 hãng, 332 trang) vì IT cần ước lượng khối lượng.

Phép thử trước khi gửi: đọc từng câu, hỏi "IT có cần câu này để làm không?" — không thì bỏ.

Bảng khai báo (4.1) chỉ có vùng IT phải đụng (thêm giá trị, thêm trường, đổi cách dùng trường).
Vùng giữ nguyên (Title/Meta/banner, dữ liệu PIM khai như cũ) không thành dòng "Không đổi":
owner hỏi 03/11/2026 "thêm giá trị vào dropdown thì quan tâm vùng khác làm gì". Rule nào nằm
trong vùng đó mà trang mới cần (vd danh mục lấy SP theo quan hệ ngành/hãng/filter trên PIM)
thì chuyển vào đúng mục giao diện (đoạn Điều kiện 4.x).

Cờ / trạng thái SEO khai tay mà không có ngày hết hạn (vd kịch bản "Chưa kinh doanh" không cần
Thời gian kết thúc) phải kèm **điều kiện tự thoát** theo dữ liệu thật, ghi ở Điều kiện 4.x và có dòng
nghiệm thu: "sản phẩm đã có giá bán thì bỏ qua kịch bản, hiện như sản phẩm đang bán, dù SEO chưa
tắt". Không có thì quên tắt = trang đang bán bị khoá giá, mất đơn (owner chốt 03/11/2026).

Task cần **dựng trang chưa từng có** (vd ngành hàng mới chưa có bản ghi danh mục) thì nói thẳng ở
3.3 Phạm vi + có dòng nghiệm thu riêng (URL 200, ra đúng giao diện), không để IT tự suy từ một
bullet "SEO tạo bản ghi" trong bảng khai báo (owner hỏi 03/11/2026 "khúc nào nói nhu cầu dựng
trang mới toanh").

Ô "Sau khi bổ sung" của một trường / giá trị khai báo viết theo thứ tự: **Để làm gì** = khối nào
trên giao diện dùng nó, kèm **ảnh bản demo khối đó khoanh đỏ ngay trong ô** → **Khi nào phải
khai** → **Khai gì** (kèm kết quả ví dụ trên trang) → **Khai ở đâu** (cấp trang) → **Không khai /
sai thì sao**. IT đọc ô nào phải hiểu ngay ô đó phục vụ gì, không phải nhảy sang mục giao diện
(owner 03/11/2026: đọc "Mã danh mục liên quan" vẫn hỏi "để làm gì" vì Doc chưa nói đó là danh mục
của khối promote SP đang bán). Dẫn mục khác chỉ để xem chi tiết, không thay câu nói mục đích;
không viết "(trường hợp 2, mục 4.2)" mà nói thẳng "ngành TGDĐ chưa bán (vd RAM máy tính)".

Mục đích task ghi đúng mục tiêu SEO (vd "trang lên Google cho từ khoá X"), không tự thêm việc
cho IT ngoài mục tiêu đó (owner 03/11/2026 bác "IT mở lối vào bộ lọc": trang chưa KD sống bằng
traffic Google). Việc SEO đã tự làm được (tạo trang, khai báo) thì ghi "SEO làm như bình thường",
và nói rõ chỗ **không đổi** (bộ lọc, menu) để IT không làm thừa. Task xoay quanh 1 rule thì rule đó
thành **1 mục riêng ngay sau mục Khai báo, trước các mục giao diện**; các trường hợp áp rule thành
bảng `Trường hợp | Ví dụ | SEO khai báo | Chỗ khác nhau`, mục giao diện dẫn "Điều kiện: thoả rule mục 4.x".

## Form khai báo: chỉ rõ trường cần khai, còn lại gom 1 dòng

Mô tả lưu 1 bản ghi (MDM/PIM/CMS) thì đọc **đủ mọi trường đang có trên form**, đúng tên nhãn trên
màn, rồi chỉ viết ra các trường **cần khai** và **không bắt buộc**, mỗi trường 1 bullet kèm giá trị /
điều kiện. Các trường còn lại gom **1 dòng** "không cần khai, để trống" — không liệt kê từng cái
(owner 04/11/2026: ghi mỗi "Mã ERP không bắt buộc" thì IT không biết các trường khác ra sao; nhưng
liệt kê hết 11 trường không cần khai thì quá dài):

```text
- Lưu bản ghi …: form hiện có N trường, khai như sau:
  - Cần khai:          <trường>: <giá trị / điều kiện>
  - Không bắt buộc:    <trường>: <trống thì sao, có nhập thì sao>
  - Các trường còn lại: không cần khai, để trống.
  - IT kiểm: bản ghi lưu được khi chỉ khai các trường ở nhóm "Cần khai".
```

Trường nào để trống mà dễ gây lỗi (vd URL Redirect làm trang chuyển hướng) thì mới tách riêng 1
bullet. Lấy danh sách trường bằng cách mở 1 bản ghi mẫu (chỉ đọc, `ak-chrome-profile`) rồi
`take_snapshot`: nhãn + dấu `*` bắt buộc hiện ngay trong cây. Dùng đúng tên nhãn trên form — vd công
tắc góc trên form kịch bản MDM tên là "Trạng thái", không phải "Kích hoạt". Không bấm Lưu.

## Trình bày phân cấp, không viết cục

Đoạn có ≥ 2 điều kiện / ý ngang hàng → tách bullet phân cấp, mỗi ý 1 dòng (owner 03/11/2026:
"breakdown ra thành phân cấp bullet, không nên viết một cục"). Mẫu:

```text
**Điều kiện** (đủ cả 3):
- Sản phẩm có kịch bản "Chưa kinh doanh"
- Kịch bản đang bật Kích hoạt
- Chưa có giá bán
**Trường hợp bỏ qua giao diện này:**
- Ý 1
- Ý 2
```

- Nhãn nhóm (Điều kiện, Trường hợp bỏ qua, Ưu tiên, Ví dụ) đậm, đứng riêng 1 dòng; ý con bên dưới.
- Áp cả trong ô bảng ("- " / "  - " / "    - "), cả Mục tiêu trang, Phạm vi, Xác định vấn đề.
- Câu owner tự viết: tách thành bullet nhưng giữ nguyên chữ.
- Tối đa 3 cấp (`"    "` 4 dấu cách = cấp 3 trong `bullets`).

## Ngôn từ

- Câu mong muốn mở bằng **"IT hỗ trợ …"**, "IT tạo rule …", "Core mới hiển thị …" — câu
  ngắn, chủ ngữ là hệ thống hoặc IT. Không xưng "chúng tôi / mình / bạn" (gần như 0 Doc dùng).
- Nối nguyên nhân → hệ quả bằng `=>` (135 lần / 23 Doc). Dòng hệ quả SEO in đậm.
- **Ví dụ ở khắp nơi** ("Ví dụ"/"VD" 324 lần): mỗi rule có ≥1 URL thật + kết quả mong muốn
  đã điền giá trị thật. Rule dạng công thức rồi ví dụ ngay dưới:
  ```text
  Title = [Tên NH] + [Tên hãng] + chính hãng, giá rẻ
  Ví dụ: Sạc cáp Apple chính hãng, giá rẻ
  ```
- Rule có thứ tự ưu tiên: **Ưu tiên 1** (có khai báo) / **Ưu tiên 2** (trống → rule sinh động).
  Mẫu Title / Meta sinh động cho trang chưa kinh doanh / tin đồn **không** ghi "chưa bán",
  "chưa kinh doanh": dùng kiểu "…, cập nhật mới nhất tại [Tên site]". Owner 03/11/2026: thấy
  "chưa bán" trên SERP user không click, Google cũng khó cho rank. Chữ trên giao diện thì được.
- Trường hợp rẽ nhánh: "TRƯỜNG HỢP 01 - Có bài viết", "TRƯỜNG HỢP 02 - Chưa có bài viết".
- **Lưu ý:** cho ngoại lệ; "Ngoài phạm vi" ghi rõ thứ KHÔNG làm để IT khỏi làm lan.
- Ví dụ mượn từ loại trang nằm trong "Ngoài phạm vi" → gắn nhãn vai trò ngay ở câu ví dụ
  ("Giao diện kịch bản tin đồn hiện tại: …", "Mẫu cách khai theo Mã model: …"), và dòng
  "Ngoài phạm vi" nói rõ phần giữ nguyên. Owner bắt lỗi 03/11/2026: Doc chưa KD lấy trang tin
  đồn HONOR X5d làm ví dụ trong khi ghi "trang tin đồn ngoài phạm vi".
- Giữ thuật ngữ nội bộ, không dịch: NH, NH + Hãng, NH + Filter, Trang đệm, TSKT, Infobox,
  CMS V1/V2, PIM/MDM, core cũ/core mới, site 1/2/16, hệ trang, rule sinh động, gán cứng,
  ontop, xtask. Lần đầu dùng chữ tắt hiếm thì ghi đầy đủ trong ngoặc.
- Không dùng từ "lưới" cho danh sách sản phẩm trên trang danh mục: viết "các sản phẩm của trang",
  "hiện trên trang", "hiển thị trên trang" (owner 04/11/2026: "lưới" xa, khó hiểu). Tên vùng trong
  bảng giao diện cũng vậy: "Các sản phẩm của trang".
- Mọi chỗ nhắc "mục 4.1", "mục 4.3, 4.4", "mục 4.1 – 4.4" là link bấm nhảy tới heading đó (owner
  04/11/2026: dễ điều hướng). `build-doc.py` tự gắn sau mỗi lần dựng (`mo_ta_heading_links.py`), nên
  trong spec cứ viết chữ thường "mục x.y", đừng tự viết link. Sửa tay Doc rồi thì chạy
  `python3 scripts/mo_ta_heading_links.py --doc ID` để gắn lại.
- Chữ "Ảnh n" nhắc hình nằm **xa** (mục khác) → link về bookmark đặt ở caption hình đó (owner
  04/11/2026). Docs API không tạo được bookmark: mở Doc bằng `ak-chrome-profile`, Cmd+F tìm caption,
  Esc, menu Insert → Bookmark (dispatch mousedown/mouseup/click vào `#docs-insert-menu` rồi mục
  "Bookmark"); URL đổi thành `#bookmark=id.xxx` → `updateTextStyle` `link.bookmarkId` cho chữ
  "Ảnh n". Dựng lại mục chứa caption hoặc chứa chữ nhắc là mất → làm lại. Hình ngay dưới chữ
  nhắc thì không cần link.
- Gọi chỗ khai báo trên MDM/PIM/CMS là **"mục [tên trên menu] trên MDM"**, không gọi "màn"
  (owner thấy khó hiểu, 03/11/2026). Không dùng "trang" cho chỗ khai báo vì Doc đã dùng
  "trang" cho trang web. Hai site thì "bên TGDĐ / bên ĐMX".
- Câu mô tả hiện trạng khai báo viết thành thao tác: "Muốn [kết quả], hiện SEO tạo 1 bản ghi
  trong mục này: chọn …, nhập …, bật …" — không liệt kê trơn tên trường.
- Ngày `dd/mm/yyyy`. Người `Tên - MãNV`.

## Bằng chứng

- URL web thật (mở được) + link CMS/PIM của đúng bản ghi ví dụ.
- Ảnh: chụp vùng lỗi, **khoanh đỏ**, caption đậm `Ảnh n - mô tả ngắn`, trong chữ nhắc lại `(Ảnh n)`.
  Trung vị 6 ảnh / Doc; 10/58 Doc không ảnh (robots, rule thuần chữ).
- Ảnh minh hoạ "mong muốn" khi chưa có giao diện: **bắt buộc** với mọi task tạo mới tính năng /
  vùng khai báo — giả lập DOM tạm rồi chụp, caption ghi rõ "Minh hoạ". Ảnh hiện tại + ảnh vùng
  khai báo CMS/PIM/MDM phải tự chụp, không chỉ dựa ảnh owner gửi. Quy trình: `dung-anh-minh-hoa.md`.
- Ảnh đặt theo luồng đọc, xem mục **Luồng đọc** dưới.
- Danh sách URL / nội dung dài → Sheet riêng, Doc chỉ link sang và nói cột nào dùng làm khoá.
- Trích Google: chỉ khi cần thuyết phục, dẫn link developers.google.com, 1 câu tóm tắt.

## Mô tả chi tiết đi theo loại trang

Task đụng nhiều loại trang (Sản phẩm, Ngành hàng, Hãng, Filter / Dòng Filter…) thì mục 4 chia
**một mục con cho mỗi loại trang**, không chia theo vấn đề hay theo trường hợp. Lý do (owner
03/11/2026): mỗi loại trang là một màn MDM/PIM khác nhau, IT làm theo từng màn; viết theo luồng
vấn đề thì chỉ nhắc được `tgdd_category`, mất màn Hãng (`tgdd_brand_category`) và Filter
(`tgdd_filter_atb`).

Mỗi mục con 4 bước, cùng thứ tự:

| Bước | Viết |
| --- | --- |
| a. Mục tiêu | Trang này có ở trường hợp nào, ví dụ thật + ảnh giao diện đích |
| b. Khai báo | Chỉ 1 câu "Khai như [sản phẩm / danh mục / hãng] bình thường. Riêng trường X cần IT bổ sung như sau:" + bảng Hiện tại / Sau khi bổ sung. **Không** nhắc lại / chụp lại vùng khai báo có sẵn (owner 03/11/2026: đang nhắc lại cái có sẵn). Loại trang IT không bổ sung gì → 1 bullet tên màn MDM/PIM (TGDĐ + ĐMX) + link bản ghi mẫu + "IT không bổ sung trường nào", không ảnh |
| c. Sản phẩm nào vào trang | Ô nào trên PIM nối sản phẩm vào trang + điều kiện (kịch bản, giá, đang bán) |
| d. Giao diện | Dòng "Giao diện: [link bản PM]" + bảng **Vùng \| Vị trí trên giao diện (bản PM) \| Rule hiển thị \| Lấy dữ liệu từ đâu** (widths ~0.8 / 2.6 / 2.4 / 1). Mỗi dòng 1 vùng, cột Vị trí là **ảnh cắt đúng vùng đó** trên bản PM (owner 03/11/2026: "có hình, nhưng là hình từng phần được nhắc đến trong bảng"); vùng không hiện trên giao diện (SEO, H1 ẩn) ghi chữ thay ảnh. Không dùng 1 ảnh toàn trang đánh số. Vùng có sẵn → "Theo rule hiện tại của [trang]", chỉ ghi phần khác. Loại trang dùng chung giao diện: "Giống 4.x, khác ở N vùng:" + bảng **Vùng \| Vị trí \| Khác 4.x thế nào** có ảnh từng vùng, không viết bullet suông |

Trước khi viết, kiểm tên màn ĐMX trong sheet danh sách link MDM/PIM ĐMX owner đưa (link trong
`dung-anh-minh-hoa.md` / journal task), không suy `dmx_` từ `tgdd_` khi chưa thấy.

## Luồng đọc — ảnh nằm ngay chỗ chữ nói tới nó

Owner chê nhiều lần, lần gần nhất 03/11/2026: "hình ở một chỗ, nội dung ở một chỗ, không có
luồng đọc". Câu nhắc `(Ảnh 4, Ảnh 5)` ở mục 3.2 mà ảnh nằm cuối mục 4.2 / 4.3 bắt người đọc
kéo xuống xem rồi kéo về tìm chỗ đang đọc.

| Luật | Làm |
| --- | --- |
| Ảnh đi liền chữ | Ảnh là khối **ngay dưới** đoạn / bullet nhắc tới nó, hoặc nằm trong cùng ô bảng (chữ trên, ảnh dưới). Không gom ảnh thành bảng ảnh cuối mục |
| Một ảnh, một chỗ | Mỗi ảnh đặt ở mục IT dùng nó để làm việc (ảnh màn khai báo → dòng bảng khai báo trường đó ở 4.x). Mục tóm tắt (Giải pháp đề xuất) không nhắc số ảnh; cần thì ghi "chi tiết + ảnh: mục 4.1" |
| Ảnh minh hoạ cho bảng khối | Ảnh đánh số khối (giao diện, annotation) đặt **trước** bảng khối, ngay sau đoạn Điều kiện: đọc ảnh xong đọc bảng theo số |
| Bullet có ảnh riêng | Tách bullet đó thành khối riêng, ảnh ngay dưới, rồi mới tới bullet kế / dòng kết luận `=>` |
| Đánh số | Số ảnh tăng dần theo thứ tự xuất hiện trong Doc |

`lint-spec.py` báo ERROR khi chữ nhắc `Ảnh n` cách chỗ đặt caption `Ảnh n - …` quá 1 khối,
hoặc số ảnh không tăng dần. Sửa bằng cách dời ảnh, không phải bỏ câu nhắc cho qua lint.

## Tên task / tên Doc

`[Site] + động từ + đối tượng + (nơi khai báo / hệ trang)` — tên Doc = tên task trên sheet.

- Site: `[TGDĐ]`, `[ĐMX]`, `[TGDĐ - ĐMX]`, `[TGDĐ/ĐMX/TopZone]`, `[Site 2 - ĐMX]`, `[AVAKids]`, `[An Khang]`, `[Erablue]`, `[All Site]`.
- Động từ: Mô tả, Bổ sung, Update, Fix lỗi, Khai báo, Lấy lên, Điều chỉnh, Loại bỏ.
- Ví dụ thật: `[TGDĐ - ĐMX] Lấy lên khai báo Meta SEO cho Trang đệm Hãng trong CMS V2`,
  `[TGDĐ] Loại bỏ tính năng xem Mobile View làm sinh link 3xx`.

## Trình bày (do `build-doc.py` áp, ghi ở đây để biết vì sao)

| Thứ | Chuẩn | Căn cứ |
| --- | --- | --- |
| Font | Times New Roman 12, heading 13 đậm đen, title 14 | owner chốt 09/10/2026 |
| Giãn dòng | 1.5, trên đoạn 6pt | Doc Giới thiệu hãng |
| Header bảng | nền `#c9daf7`, đậm, căn giữa, ghim lặp khi sang trang | 183 bảng — màu phổ biến nhất |
| Cột nhãn (bảng Phạm vi) | nền xám nhạt, đậm | |
| Định dạng trang | Luôn dùng **Pageless Format (không ngắt trang)** để tối ưu vùng nhìn, bảng và ảnh mockup bung rộng rãi, không bị đứt trang | Quyết định 27/10/2026 |
| Heading | đánh số `1.` `3.1.` `3.3.1.`, không trùng số | 2 Doc có lỗi trùng `3.2` |
| Code (JSON-LD, robots, dataLayer) | bảng 1 ô, Courier New 10, nền xám | Doc Schema/Tracking |

## Dòng trên sheet tổng hợp

Xem `sheet-tong-hop-task-it.md`. Cột "Mục đích" 2–4 câu theo mạch
`vấn đề => giải pháp => lợi ích SEO`, ví dụ thật:

> IT hỗ trợ lấy lên vùng khai báo Meta SEO cho Trang Đệm+Hãng trong CMS V2 vì Title/des của
> Trang Đệm+Hãng đang tự kéo Title/des của Trang NH+Hãng => trùng lặp Title/des hàng loạt,
> ảnh hưởng ontop từ khoá.
