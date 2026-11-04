# Prompt Bước 1: semantic + dàn bài (tab "Thầy")

Nguồn: 3 prompt đầu của Bước 1 "Source Gốc" trên tab Thầy (sếp chạy bằng ChatGPT).
Giữ nguyên ý và tiêu chí; `{...}` là trường trong `brief.json`.

## 1a. Bộ Semantic / LSI / Long-tail → `01-semantic.md`

> Bạn đóng vai trò là {chuyen_gia}. Bạn đang lên dàn bài SEO cho bài viết về thương hiệu cho công ty {brand} với chủ đề "{chu_de}" với từ khóa "{kw_chinh}". Hãy đề xuất đầy đủ tất cả Semantic Keywords chiều dọc và chiều ngang cùng LSI Keywords liên quan, bao gồm:
> - Các từ khóa phân bổ theo cụm hóa thành semantic cluster riêng.
> - Các từ khóa mở rộng về {huong_mo_rong_semantic}.
> - Các Semantic liên quan đến lĩnh vực {nganh}.
> - Gợi ý thêm các từ khóa mở rộng chiều sâu semantic để tối ưu Featured Snippet.
> - Các Long-tail search queries.

Định dạng ra (để bước sau đọc được, không đổi tên mục):

```markdown
## Insight người tìm kiếm      # 3-6 gạch: họ là ai, đang lo gì, cần quyết định gì
## Semantic chiều dọc          # đào sâu chủ đề chính, theo cluster
### Cluster: <tên>
## Semantic chiều ngang        # chủ đề lân cận cùng ngành
### Cluster: <tên>
## LSI theo nhóm               # đủ các nhóm trong brief.nhom_lsi, mỗi nhóm 6-12 cụm
### <tên nhóm>
## Long-tail search queries    # 10-20 câu hỏi người dùng gõ thật
## Gợi ý Featured Snippet / PAA # câu hỏi nào trả lời được bằng đoạn 40-60 từ hoặc danh sách
```

Mọi từ khoá viết tiếng Việt. Thuật ngữ gốc tiếng Anh chỉ giữ khi người Việt quen dùng (visa, USCIS, mã biểu mẫu).

## 1b. Dàn bài nháp 3 H2 theo 15 checklist

> Hãy lên outline cho 1 bài viết SEO từ khóa đó dựa trên những phân tích về insight khách hàng và Semantic, LSI keywords, Long-tail Search Queries ở trên. Outline này có 3 H2. Outline này cũng phải thỏa các tiêu chí sau:
> - Tiêu đề hấp dẫn, gây tò mò, thu hút người đọc.
> - Phù hợp với mục tiêu bài viết và Search Intent của người dùng.
> - Cấu trúc hợp lý: có H1 & có 3 H2; H2 đầu tiên có 2 H3; H2 thứ 2 không có H3, có 1 checklist; H2 cuối có 2 H3, 1 checklist.
> - Nội dung định hướng hữu ích, chi tiết và mang tính chuyên sâu.
> - Tập trung giải quyết rõ ràng các "Pain Point" của người đọc.
> - Ngôn ngữ dễ hiểu, trình bày dễ đọc, tối ưu trải nghiệm người dùng.
> - Outline được mở rộng theo hướng Semantic Content.
> - Khả năng mở rộng thành Content Cluster.
> - Thiết kế theo mô hình Semantic Topic Clustering.
> - Tối ưu Featured Snippet & PAA (People Also Ask).
> - Tích hợp E-E-A-T (Experience - Expertise - Authoritativeness - Trustworthiness).
> - Tối ưu SEO Onpage: Từ khoá chính, từ khoá phụ, Semantic Keywords, LSI Keywords.

Cấu trúc H2/H3 lấy từ `brief.cau_truc_h2`; dòng "Cấu trúc hợp lý" ở trên là giá trị mặc định của tab Thầy.
H1 chứa nguyên cụm `{kw_chinh}` và `{brand}`; 2 H2 đầu chứa `{brand}` (theo `brief.brand_tieu_de`).

## 1c. Dàn bài Final → `02-dan-bai.md`

> Bạn đóng vai trò là {chuyen_gia}. Hãy điều chỉnh dàn bài SEO Final với yêu cầu sau:
>
> CẤU TRÚC:
> - Dàn bài phải tích hợp mô hình AIDA (Attention – Interest – Desire – Action) và FAB (Features – Advantages – Benefits).
> - Ở từng H2/H3, nêu rõ các Semantic Keywords & LSI Keywords được hoạch định, bao gồm: Semantic chính (chủ đề cốt lõi); Từ khóa phụ (LSI liên quan theo nhóm ngữ nghĩa); Câu hỏi Long-tail Search Queries phổ biến; Semantic nào hỗ trợ Featured Snippet hoặc PAA.
>
> NGUỒN SEMANTIC:
> - Áp dụng đủ các nhóm Semantic LSI ngành {nganh} trong `brief.nhom_lsi`, phân bổ hợp lý theo từng phần.
>
> MỤC TIÊU:
> - Tối ưu Semantic Coverage 100%
> - Có khả năng mở rộng thành Content Cluster
> - Tối ưu hóa Featured Snippet, PAA (People Also Ask), và E-E-A-T
> - Dễ triển khai thành nội dung không vượt quá {so_tu.muc_tieu} từ

Định dạng ra (người viết đọc trực tiếp file này):

```markdown
# <H1>                                  [AIDA: Attention]
Sapo: <ý chính 1 câu> | Semantic: ... | LSI: ...
## <H2 #1>                              [AIDA: ... | FAB: ...]
- Semantic chính: ...
- LSI (nhóm: <tên>): ...
- Long-tail: ...
- Snippet/PAA: <câu hỏi> → <dạng trả lời: đoạn/danh sách/bảng>
### <H3> ...                            (cùng 4 dòng trên)
...
## Bảng phân bổ nhóm LSI
| Nhóm | Phần dùng | Cụm chính |
## Vị trí biến thể từ khoá phụ          # mỗi biến thể trong brief.kw_phu: đặt ở phần nào
## Vị trí brand                         # H1, sapo, H2 #1, H2 #2, mở bài, thân bài, kết bài
```

## Khi ngành không phải di trú

`brief.nhom_lsi` của tab Thầy là 6 nhóm riêng của ngành di trú. Đổi ngành mà brief chưa có
nhóm LSI thì ở 1a đề xuất 6 nhóm theo đúng khung (luật/cơ quan, giấy tờ, dịch vụ/quy trình,
đối tượng khách, điều kiện/tiêu chuẩn, hành vi/tình trạng/duy trì) cho ngành đó, ghi vào đầu
`01-semantic.md` mục `## Nhóm LSI đề xuất`, và báo người điều phối cập nhật brief.
