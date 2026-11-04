# Nguồn và luật từ khoá cho Plan SEO nhóm SP

## Thứ tự nguồn (dừng ở nguồn đầu tiên đủ dùng cho từng URL)

1. `--kw-file`: file research từ khoá đã có (JSON như raw Ahrefs `{"keywords":[{keyword,volume}]}`, hoặc CSV keyword,volume[,url]).
2. Tab research của sheet Research SP/Hãng mới (`sheets.researchSpHangMoi`): `Research NH Filter`, `Research Dòng Filter`
   (URL cột D, từ khoá F, volume G), `KW_Sản_phẩm_Mới` (nối URL qua ID ở `Data_Sản_Phẩm_Mới`).
3. Tab `All KW` của sheet Import Data All KW (`sheets.allKw`): URL TGDD cột O, từ khoá L, volume M.
4. URL không có từ khoá nào từ các nguồn trên (owner chốt 29/10): skill KHÔNG tự gọi Ahrefs; Ahrefs chỉ qua `seo-keyword-research`
   khi owner xác nhận units, kết quả truyền lại bằng `--kw-file`. Mặc định skill làm tiếp hai bước:
   - **Dò SERP từ chung chung hơn** (`kw_sources.candidate_terms`): SP cắt 4 và 5 từ đầu của tên bỏ mã model; Filter dùng cả slug. Từ nào mà
     đúng URL này vào top 10 thì nhận làm từ khoá (volume chưa đo, ghi 0, ghi chú SERP) vì một SP đôi khi rank cho từ rộng hơn.
   - Dò không ra: **tự sinh 1 từ khoá đại diện** từ slug (SP: tới mã model cuối, vd `msi prestige n16 flip ai c1xmt 017vn`; Filter: cả slug),
     volume 0, ghi chú "Tự sinh, cần duyệt".

## Luật lọc (owner chốt 28/10/2026, code ở `kw_sources.drop_reason`)

- Chỉ giữ từ liên quan trực tiếp tới URL: phải chứa thực thể có trong slug URL.
- Loại: từ blog/tìm hiểu (là gì, benchmark, cách, so sánh, review, hiệu năng...), tiếng Anh, hãng khác, PC để bàn/mini PC.
- Từ khoá không có URL được gán: mã model riêng của một SP thì về SP đó; tên SP/dòng chung về SP đầu tiên của nhóm;
  khái niệm chung (vd RTX Spark) + "laptop" về trang Filter.
- Volume 0 ghi 0 cho từ tự sinh; Ahrefs nhóm 0-10 ghi 5 (quy ước team ở `seo-keyword-research`).
- Không có trần số từ khoá/URL: lấy mọi từ đúng intent (owner chốt 29/10; `--max-kw N` chỉ để cắt thử).
- KW chính: tick mọi từ khoá đưa vào (luật team ở tab `Rule_Từ_Khóa` của sheet All KW).

## Kiểm SERP bằng SerpApi (`serp_check.py`)

Mặc định chỉ đọc cache `--serp-cache` ({từ khoá: [[hạng, url, tiêu đề]]}). Gọi thật cần `--serp --approve-serp <số credit>`
sau khi owner thấy số từ khoá chưa có cache (1 credit/từ). Chỉ từ đã qua luật lọc tĩnh mới bị kiểm SERP, nên không tốn credit cho từ sẽ bị loại. Khoá `SERP_API_KEY` lấy từ biến môi trường hoặc `.env` gốc,
không in ra. Kết luận theo top 10: >= 3 trang bán hàng là "bán hàng"; <= 1 là "bài viết/tin" (loại khỏi plan URL,
hợp bài blog); còn lại "lẫn" (giữ, ghi chú SERP để owner xem).
Ngoại lệ luật owner: từ chứa đủ khái niệm của Filter + "laptop" thuộc Filter, không loại theo SERP.
