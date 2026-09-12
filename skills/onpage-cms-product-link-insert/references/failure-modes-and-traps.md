# Bẫy và cách chẩn đoán

Tất cả đều đo được trên hệ thật, không phải phỏng đoán.

## 1. `indexOf(plainText)` trên HTML thô luôn trả -1

Đoạn văn trong CMS có markup lồng và HTML entity:

```html
iPhone 15 Plus<span style="...">&nbsp;256 GB</span> được...
```

Cột "Nội dung cũ" trên sheet là plain text. So trực tiếp là trượt 100%.

**Cách đúng:** normalize `textContent` (decode entity → `U+00A0` thành space →
gom whitespace → trim) để **định vị**, rồi splice trên **string thô** để **ghi**.
Hai tầng khác nhau cho hai mục đích khác nhau.

## 2. Replace cả đoạn làm mất link cũ

46/88 đoạn trong đợt đầu **đã có `<a>` sẵn**. Replace nguyên đoạn bằng "Nội dung
mới" từ sheet là xoá sạch link đó.

**Cách đúng:** chỉ **append** câu mới vào trước `</p>`. Kéo theo một lợi ích
ngoài dự tính: lỗi chính tả ở cột "Nội dung mới" của sheet (`Fusion Ultra Wide`
bị find/replace thành `Fusion Duo Wide`) **không vào được CMS**, vì phần văn cũ
không bị ghi lại.

## 3. Đi qua UI editor làm rewrite cả bài

Hai vấn đề chồng nhau:

- `GetAllFormData` không gọi `triggerSave()`. Sync editor→textarea chỉ chạy qua
  `editor.on('change', () => tinyMCE.triggerSave())`, mà `setContent()` **không
  phát `change`**. Sửa bằng script qua UI thì phải gọi `triggerSave()` tay.
- Kể cả gọi đúng, TinyMCE vẫn **format lại toàn bài**. Đo trên 1 sản phẩm:
  editor trả 50.522 ký tự trong khi textarea gốc 45.426.

**Cách đúng:** headless `fetch()`, không nạp bài vào TinyMCE.

## 4. Chạy song song không nhanh hơn

12 request, 3 mức đồng thời:

| conc | Tổng | Latency tối đa 1 request |
| --- | --- | --- |
| 1 | 21,2s | ~8s |
| 4 | 20,7s | — |
| 8 | 19,7s | 18,2s |

Tổng đứng yên, latency từng request phình theo số luồng. CMS serialize theo
session. Muốn nhanh hơn: chia dòng cho nhiều người, mỗi người một session.

## 5. Timeout tầng CDP ở lô > 10 dòng

Lô 12 dòng × ~8s vượt `protocolTimeout` của `Runtime.callFunctionOn`.

Đã kiểm sau sự cố: 12 sản phẩm đều 0 link, lần sửa cuối vẫn là của người khác từ
hôm trước → **timeout không ghi gì**. Nhưng đó là kết luận sau khi đo, không
phải mặc định. Gặp timeout thì **kiểm trạng thái thật từng pid trước**, đừng
re-run mù.

Giới hạn an toàn: **10 dòng/lô**.

## 6. Phân biệt ba kiểu "không tìm thấy đoạn"

Runner chẩn đoán theo thứ tự, **không** dùng một ngưỡng similarity duy nhất:

| Dấu hiệu | Chẩn đoán | Bản chất |
| --- | --- | --- |
| Có block **bắt đầu bằng** đúng Nội dung cũ và dài hơn | Đã chèn ở lần chạy trước (`already: true`) | Thành công |
| Khớp bằng đúng nhưng block là `<h1>`-`<h6>` | Rule cấm chèn link từ `<h3>` trở xuống | User quyết |
| Không có cả hai, `nearest` sim thấp | Đoạn không tồn tại trong bài đang sống | Lỗi dữ liệu sheet |

**Vì sao dùng phép kiểm tiền tố chứ không phải similarity cho ca "đã chèn":**
skill chỉ append, nên đoạn đã xử lý luôn bắt đầu bằng nguyên văn Nội dung cũ —
phép kiểm này đúng tuyệt đối. Ngược lại Jaccard **không** cho ~1,0 như trực giác:
câu chèn làm tăng gần gấp đôi số token nên similarity rơi xuống **~0,5**, lọt
thẳng vào vùng dễ nhầm. Đo được bằng test trong `scripts/`: ca đã chèn 0,48, ca
đoạn không tồn tại 0,10-0,21 — hai vùng này **không tách nhau đủ xa** để đặt
ngưỡng an toàn.

`nearest` (top 3 similarity) chỉ còn dùng để **báo cáo** ca thứ ba, giúp người
đọc thấy bài thật viết gì.

Ca thứ ba đã gặp 8 dòng, xoay quanh 2 đoạn boilerplate. Đã tìm cả `txtContent`,
mọi `textarea` khác của trang, và `document.body` — không có ở đâu. Chèn ép sẽ
đặt câu vào sai ngữ cảnh, nên runner từ chối.

**Đừng gộp 3 ca này vào chung một con số "không tìm thấy".**

## 7. Anchor ngắn ăn vào anchor dài

`iPhone 18` là tiền tố của `iPhone 18 Pro`, `iPhone 18 Pro` là tiền tố của
`iPhone 18 Pro Max`. Bọc theo thứ tự xuất hiện là tạo ra link lồng nhau hoặc
anchor cụt.

**Cách đúng:** sắp anchor giảm dần theo độ dài, thay bằng placeholder, bọc xong
hết mới hoàn nguyên placeholder. Runner đã làm; đừng "tối ưu" bỏ bước placeholder.

Format anchor chuẩn:

```html
<a title="X" href="URL" target="_blank" rel="noopener">X</a>
```

## 8. Một sản phẩm có thể có nhiều dòng trên sheet

11 sản phẩm trong đợt Hệ sinh thái Apple có 2 dòng — **không phải trùng lặp**,
mà là 2 đoạn khác nhau trong cùng một bài. Runner đọc lại trang trước mỗi dòng
nên lần chèn thứ 2 thấy nội dung đã cập nhật từ lần 1. Cả 2 lần đều verify được.

Đừng dedupe theo `pid` khi dựng danh sách dòng.

## 9. Trang live trễ cache

Sau khi CMS báo lưu xong, trang live vẫn có thể hiện bản cũ một lúc. **Kiểm CMS,
không kiểm trang live** để kết luận đã ghi hay chưa.
