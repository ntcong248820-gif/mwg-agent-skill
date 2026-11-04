# Dựng ảnh minh hoạ

Mục đích: IT nhìn ảnh là hình dung được hiện tại ra sao, khai báo ở đâu, mong muốn trông thế nào.
Ảnh lưu ở `tasks/{task}/data/processed/mo-ta-it/` (WORKDIR), đặt tên `a1-hien-tai-….png`,
khai trong `images` của spec.

## Quy trình từng loại

| Loại | Việc | Công cụ |
| --- | --- | --- |
| Hiện tại (web) | mở URL ví dụ thật, chụp vùng liên quan, khoanh đỏ | `ak-agent-browser` (public) / `ak-chrome-profile` |
| Vùng khai báo | mở đúng bản ghi ví dụ trong CMS/PIM/MDM, chụp màn có trường liên quan, khoanh đỏ trường | `ak-chrome-profile`, tab đã đăng nhập, xác nhận đúng tab bằng URL-anchor |
| Mong muốn - đã có | chụp trang/hệ tương đương đang chạy (vd hàng nút dòng SP ở trang Hãng) | như trên |
| Mong muốn - chưa có | **giả lập** rồi chụp, caption ghi "Minh hoạ" | xem dưới |

Chỉ đọc: không bấm Lưu/Submit, không sửa field, không tạo bản ghi. Không dùng Claude in Chrome
extension (rule Browser Automation của repo).

## Giả lập DOM

1. Mở trang thật bằng `ak-agent-browser`/`ak-chrome-profile`.
2. Chèn vùng mong muốn bằng JS tạm (`insertAdjacentHTML`, copy khối tương tự của trang khác,
   đổi chữ/link), chỉ trong tab, không lưu gì.
3. Chụp. Hoặc dựng mockup HTML riêng nếu trang nền khó chèn, mở bằng trình duyệt rồi chụp.
4. Caption: `Ảnh n - Minh hoạ: …`. Trong Doc ghi rõ đây là minh hoạ, IT làm theo mô tả chữ nếu lệch.

**Task thêm giá trị vào dropdown / ô chọn** (owner chỉ 03/11/2026): ảnh Hiện tại = **mở dropdown**
rồi chụp đủ mọi option (antd: `mousedown` vào `.ant-select-selector`, gỡ `max-height` của
`.rc-virtual-list-holder` để hiện hết, khoanh đỏ cả danh sách). Ảnh Mong muốn = cùng khung đó,
clone option cuối, đổi chữ thành giá trị mới, khoanh đỏ riêng option đó. Hai ảnh đặt cạnh nhau ở
cột Hiện tại / Sau khi bổ sung. Chụp xong reload tab — chỉ mở dropdown, không chọn, không Lưu.

**Ảnh từng khối từ bản demo / design PM** (owner chỉ 03/11/2026): mỗi trường khai báo có ảnh
khối giao diện nó phục vụ, đặt ngay trong ô khai báo. Trang demo public → `ak-agent-browser`:
`set viewport 1280 900`, `eval` thêm `outline: 3px solid #ff0000` vào đúng khối, `screenshot
--full`, cắt bằng `magick -crop`; 2 vùng xa nhau trên trang (câu dẫn + khối dưới lưới) thì cắt 2
mảnh rồi `magick … -append` thành 1 ảnh. Chỉ dùng demo PM khi owner nói vậy, không lẫn demo SEO.

## Ảnh trước/sau

Dùng bảng `Hiện tại | Mong muốn`, hàng ảnh trong `img_row` hoặc `{img:a1}` / `{img:a2}` trong
từng ô. Caption đậm `Ảnh n - …`, chữ nhắc `(Ảnh n)`.

## Đặt ảnh ở đâu

Ảnh nằm ngay dưới chữ nhắc tới nó (hoặc trong cùng ô bảng), không gom về cuối mục. Ảnh màn
khai báo đặt trong dòng bảng mô tả trường đó; ảnh giao diện đánh số khối đặt trước bảng khối.
Luật đủ + lý do: `quy-tac-viet-va-trinh-bay.md` mục Luồng đọc.

**Mỗi chỗ nhắc 1 ô trên PIM/MDM là có ảnh ô đó** (owner 03/11/2026: "đọc 'Ô Danh Mục trên PIM'
mà không biết nằm ở đâu"). Áp cả cho rule điều kiện ("Ô Danh Mục = danh mục của trang"), không
chỉ bảng khai báo. Mục sau nhắc lại cùng ô → đặt lại ảnh đó ngay dưới, đánh số mới, không bắt
người đọc kéo lên mục trước. Ảnh: cắt sát cụm ô, khoanh đỏ, caption ghi giá trị mẫu
(vd "ô Danh Mục (13 - Điện thoại)").

## Khoanh đỏ, kích thước

- Khoanh đỏ (viền #ff0000 ~3px) đúng vùng/trường liên quan, không khoanh cả trang. Có thể
  chèn viền bằng JS (`outline`) trước khi chụp.
- Chụp vùng cần, không cả màn hình rộng: rộng ≤1600px, PNG/JPG <5MB. Doc dọc ảnh width ~400pt.
- Zoom vào chữ đọc được; vùng nhỏ thì chụp riêng hoặc phóng lên.
- **Cắt sát, bỏ khoảng trống** (owner 03/11/2026: "chụp hơi rộng làm nhỏ chữ, dư nhiều khoảng
  trống"). Ảnh bị co về ~400pt nên càng rộng thì chữ càng nhỏ: ảnh màn MDM/PIM 1400px co còn
  ~30% là không đọc nổi. Mục tiêu ảnh sau cắt ≤ ~800px ngang. Cách cắt bằng `magick`:
  - Form 2 cột có khoảng trắng giữa → cắt từng cột (`-crop`) rồi `+append` sát nhau.
  - Bảng nhiều cột → chỉ giữ cột IT cần (mã, url, tên, cột liên quan); bỏ cột thứ tự, ngày,
    hành động; ghép bằng `+append`, dòng bị cắt dở ở mép thì bỏ.
  - Lưới / vùng có nửa phải trống → cắt bớt, vẽ lại khung đỏ (`-fill none -stroke '#ff0000'
    -strokewidth 3 -draw "rectangle …"`; zsh không tách biến chứa option, viết thẳng).
  - Khung đỏ cũ bị cắt dở → tô trắng (`-fuzz 30% -fill white -opaque '#ff0000'`) rồi viền lại.
  - Giữ bản gốc ở scratchpad trước khi cắt; xem lại từng ảnh sau cắt. Ảnh owner tự chèn không cắt.
  - Ảnh cắt từng vùng cho cột "Vị trí trên giao diện": chụp full trang bản PM (`agent-browser
    screenshot --full`, viewport 1280), lấy toạ độ vùng bằng `eval` (`getBoundingClientRect` + `scrollY`),
    cắt bằng `magick -crop`; vùng dài (khối SP đang bán) cắt phần đầu + nút cuối rồi `-append`.
    Không khai `width` → `build-doc.py` để ảnh cỡ gốc (1px ≈ 0.75pt), chỉ co khi rộng hơn ô —
    ảnh nhỏ (nút Lọc) không bị phóng mờ.
  - Ảnh ngang (màn MDM/PIM, bảng) trong spec **không đặt `width`** → `build-doc.py` cho full
    khổ trang (~500pt). Chỉ đặt `width` 380–420 cho ảnh dọc (lưới, mockup đánh số khối) để không
    chiếm quá 1 trang. Kiểm lại bằng PDF export (`pdftoppm`), không chỉ nhìn file ảnh.

## Không chụp

Token, cookie, thanh địa chỉ có query chứa khoá, danh sách người dùng, dữ liệu khách hàng,
tên tài khoản/email đang đăng nhập. Thấy lọt vào khung thì cắt hoặc che trước khi lưu.

## Tối thiểu theo khung

- B: ≥1 ảnh hiện tại + ≥1 ảnh vùng khai báo + ≥1 ảnh Mong muốn (thật hoặc giả lập).
- A sửa lỗi: ≥1 ảnh bằng chứng lỗi khoanh đỏ; rule thuần chữ (robots…) thì ghi lý do trong report.
- Lint chỉ WARN, nhưng bỏ qua phải có lý do.
