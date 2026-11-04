# Viết bài (Bước 1, prompt 4-6 tab Thầy)

Sếp chạy 3 prompt này bằng Claude: viết phần đầu ~400 từ, viết nốt + trau chuốt 11 điều kiện,
rồi tự bù Semantic Coverage. Việc chia 400 từ trước là để chat không bị cắt; subagent viết
trong một lượt nhưng vẫn đi đủ 3 lượt kiểm theo thứ tự dưới.
Đầu vào: `brief.json`, `01-semantic.md`, `02-dan-bai.md`. Đầu ra: `bai-v1.md`, `can-kiem-chung.md`.

## Lượt 1 — viết

> Bạn đóng vai trò là {chuyen_gia}. Bạn đang viết bài SEO cho chủ đề "{chu_de}" với từ khóa chính "{kw_chinh}" cho thương hiệu {brand} — {brand_mo_ta}, dựa trên dàn bài `02-dan-bai.md`.
> Nội dung cần thỏa mãn xuất sắc các tiêu chí:
> 1. Cung cấp nhiều thông tin nhưng ngắn gọn, tránh lan man, tránh sáo rỗng. Kết hợp câu ngắn và câu dài linh hoạt để giữ nhịp đọc tự nhiên.
> 2. Dùng gạch đầu dòng, danh sách số ở đoạn cần nhấn mạnh hoặc liệt kê thông tin quan trọng. Không dùng đoạn code, icon. Kết hợp đoạn văn mô tả để nội dung mạch lạc.
> 3. Dùng storytelling để tạo điểm nhấn, phù hợp bối cảnh.
> 4. Giảm tính từ và trạng từ khi không cần, vẫn dùng khi tăng sắc thái biểu đạt.
> 5. Bổ sung câu dẫn để các đoạn nối logic.
> 6. Chèn đủ Semantic Keywords, LSI Keywords, Long-tail Search Queries theo đúng hoạch định của dàn bài.
> 7. Sapo chỉ 1 đoạn (không xuống dòng).
> 8. Không viết tiếng Anh xen tiếng Việt, chuyển từ chuyên ngành sang tiếng Việt đúng chuẩn.

## Lượt 2 — trau chuốt 11 điều kiện, tổng ~{so_tu.muc_tieu} từ

> 1. Nhiều thông tin nhưng ngắn gọn, câu ngắn câu dài linh hoạt.
> 2. Thay câu bị động thành chủ động; giữ bị động khi cần nhấn mạnh kết quả hơn chủ thể.
> 3. Tách câu phức thành câu đơn. Không câu dài dòng. Không ngôn ngữ quá bình dân, thiếu formal. Dùng dấu chấm ngắt mạch nhưng giữ giọng gần gũi.
> 4. Thuật ngữ chuyên môn thì mở ngoặc giải thích ngắn.
> 5. Chèn đủ Semantic, LSI, Long-tail theo hoạch định.
> 6. Các từ trong `brief.tu_han_che` không bao giờ quá {tu_han_che_toi_da} lần; dùng từ thay thế tiếng Việt.
> 7. Từ khóa chính "{kw_chinh}" chỉ xuất hiện nguyên cụm {kw_chinh_nguyen_cum} lần: 1 lần ở H1, 1 lần ở sapo.
> 8. Ở các vị trí khác, dùng mỗi biến thể trong `brief.kw_phu` 1 lần để giảm tần suất từ khóa chính.
> 9. Dùng từ đồng nghĩa để tổng tần suất các cụm trong `brief.tan_suat_toi_da` dưới trần.
> 10. Brand "{brand}" xuất hiện {brand_so_lan} lần: H1, H2 đầu, H2 thứ hai, sapo, mở bài, giữa bài, đoạn kết (câu CTA). Dùng `brief.brand_thay_the` để thay ở các chỗ khác. Cuối bài chèn nguyên văn `brief.cta_ket`.
> 11. Không in đậm, không tiếng Anh xen tiếng Việt.

Câu CTA bắt buộc đã chứa sẵn một số từ hạn chế (vd "tư vấn", "hỗ trợ", "xử lý"): trừ số lần đó
khỏi ngân sách cho phần thân bài.

## Lượt 3 — bù Semantic Coverage

> Hãy đánh giá tỷ lệ đạt Semantic Coverage của cả bài khi xét theo trục Semantic chiều dọc và chiều ngang. Sau đó bổ sung vào bài viết để đạt tỉ lệ coverage semantic 100%. Không trùng lặp từ, cấu trúc câu khi bổ sung. Không viết thêm quá dài, chuyển các từ tiếng Anh sang tiếng Việt, đảm bảo độ dài cả bài dưới {so_tu.toi_da} từ.

## Định dạng `bai-v1.md`

Markdown: `#` H1, sapo, `##` H2, `###` H3, danh sách `-`/`1.`. Không META ở v1 (Bước 3 thêm).
Chạy lint `--stage draft` trước khi giao, sửa hết FAIL trừ lỗi meta.

## Số liệu

Tab Thầy không có bước kiểm chứng. Bài ngành pháp lý/tài chính/sức khoẻ sai số liệu là rủi ro
thật, nên: chỉ nêu mức phí, thời gian xét duyệt, mã biểu mẫu, điều luật khi chắc chắn; không
chắc thì viết định tính ("thường mất nhiều tháng"). Mọi câu có số liệu cụ thể chép sang
`can-kiem-chung.md` kèm lý do để người duyệt kiểm trước khi đăng.
