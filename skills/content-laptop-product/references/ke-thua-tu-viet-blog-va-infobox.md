# Quy tắc kế thừa từ skill viết bài khác

Đọc từ skill viet-blog (file bai-hoc-da-chot trong thư mục references của nó) và skill tgdd-infobox-* (file writing-rules), 30/10/2026. Các rule này do team chốt, skill này dùng lại phần hợp với bài SP. Lint kiểm được cái nào thì ghi ở cột cuối.

## Áp dụng nguyên văn
| Rule | Nguồn | Lint |
|---|---|---|
| Câu đủ chủ ngữ, vị ngữ; không câu chuyển ý cụt ("Khác biệt lớn hơn là X."), không câu rào đón ("tùy nhu cầu mỗi người" đứng một mình) | viet-blog, infobox | đọc tay |
| Không dấu `;`. Liệt kê kết thúc ",...". Không "Điện máy XANH" sai chính tả | viet-blog | WARN `;` |
| Không lạm dụng `:` trong văn xuôi: không thay động từ ("Màn hình: 14 inch"), tối đa 1 dấu mỗi đoạn, chỉ mở danh sách/bảng. Heading không kiểu "Về X: giải thích" | infobox, viet-blog | WARN |
| Không từ quảng cáo: đỉnh cao, vượt trội, đột phá, ấn tượng, nâng tầm, hoàn hảo; không "rõ/rõ rệt" để nhấn mạnh, thay bằng số | viet-blog, infobox | ERROR |
| Không "tốt nhất", "số 1" khi không có tiêu chí và dữ liệu | infobox | ERROR |
| Thuật ngữ lạ (NPU, TOPS, VRR, DCI-P3, Pluton, TPM, Vapor Chamber, DisplayHDR, Windows on Arm...) giải thích 1 lần bằng lời thường ở lần đầu: nghĩa + tác động với người dùng. Từ quen (CPU, RAM, SSD, pin, Wi-Fi) dùng thẳng | infobox | WARN nếu câu đầu và câu kế không có lời giải thích |
| Giải thích 1 lần, các lần sau dùng thẳng tên. Ví von chỉ cho khái niệm khó nhất, không lặp mô típ ("bộ não của máy") | infobox | đọc tay |
| Công thức: tính năng/thông số → ảnh hưởng thực tế → gợi ý chọn. Nhắc tính năng phải nói lợi ích. "Ai nên mua" phải cụ thể đối tượng, nhu cầu | infobox, viet-blog | đọc tay |
| Xưng "bạn", có tình huống để người đọc tự liên hệ | infobox | WARN nếu không có "bạn" |
| Không lộ dữ liệu nội bộ/giọng báo cáo: "theo dữ liệu", "trang sản phẩm ghi", "tại thời điểm kiểm tra", "còn hàng", "tạm hết hàng" | viet-blog, infobox | ERROR |
| Không tin đồn, rò rỉ, dự đoán; SP chưa công bố thì "hãng chưa công bố" | viet-blog | đọc tay |
| Thông số bản Việt Nam: dữ liệu TGDĐ và trang hãng VN thắng trang hãng toàn cầu. Mâu thuẫn không giải được thì hỏi owner | viet-blog | `facts` |
| Không ghi tên nguồn trong thân bài ("theo GSMArena..."), bài không có dòng "Nguồn tham khảo". Nguồn chỉ ghi ở report/ghi chú | viet-blog | đọc tay |
| Không xếp hạng, không nhắc đối thủ | infobox, viet-blog | đọc tay |
| Giá nêu kèm ngày cập nhật. Bài SP mặc định không nêu giá (xem dưới) | viet-blog | WARN số giống giá |

## Chỗ hai bên lệch nhau, quyết định của skill này (owner chốt 30/10/2026)
1. **"Theo hãng"**. Infobox bảo đã verify thì nói thẳng, không hạ giọng "theo hãng thì..."; viet-blog cấm tên nguồn. Nhưng task giao yêu cầu số hiệu năng hãng công bố phải ghi rõ là của hãng, và các con số tiếp thị (TOPS, fps, mô hình AI chạy được) không có cách kiểm độc lập. Quy ước: **thông số cấu hình** (RAM, màn hình, cổng, pin) viết thẳng; **số hiệu năng hãng công bố** viết với chủ ngữ là hãng ("NVIDIA cho biết...", "Theo thông số công bố, ... lên đến 1000 TOPS"). Lint: số trong `hedge_numbers` phải nằm trong câu có "theo NVIDIA/theo hãng/theo thông số công bố" hoặc "<hãng> cho biết".
2. **Nhắc TGDĐ**. Infobox chỉ cho nhắc tên TGDĐ ở mục CTA; viet-blog bắt nhắc brand ở bài có SP bán. Bài SP chỉ nhắc ở đoạn chốt và trong `title` link (đã có sẵn ở mẫu live).
3. **Giá**. viet-blog muốn bảng giá khi KW có chữ "giá"; bài SP trên PIM không đưa giá vì trang đã có block giá. Giữ không đưa giá.
4. **Heading**. viet-blog: H3 đánh số, H4 không số, H3 8–15 tiếng. Bài SP mẫu live dùng H3 không số, ngắn hơn. Giữ theo mẫu live, vì đó là khuôn bài SP đang chạy. Lint cảnh báo H3 đánh số. H4 chỉ dùng cho câu hỏi FAQ.
5. **Viết bằng Antigravity**. viet-blog giao bước viết cho Anti. Skill này để agent viết và lint tự kiểm; có thể giao Anti khi viết hàng loạt, brief gồm `references/*.md` của skill này và `facts.json`, Claude duyệt đầu cuối.

## Phát hiện phụ
Bài live đang chạy phạm một số rule này: ví dụ "vượt trội", "ấn tượng" ở heading bài Dell 15 DC15250, link sai domain, link nhiều lần. Rule blog/infobox không bắt buộc với bài SP cũ, nhưng bài mới nên theo.
