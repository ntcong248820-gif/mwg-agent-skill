# Outline mặc định - Trang Ngành Hàng + Dòng Sản Phẩm (Type 4)

## Cấu trúc đề xuất

```markdown
## Tổng quan về {dòng sản phẩm}
Sapo 3-5 câu: định vị dòng, nhóm người dùng và các nhóm phiên bản đang có tại TGDĐ.

### Tổng quan về {dòng sản phẩm}
Section H3 đầu tiên, bắt buộc. Giới thiệu và lịch sử của dòng: dòng ra đời khi
nào và hãng định vị cho ai, vị trí của dòng so với các họ sản phẩm khác của cùng
hãng, dòng phát triển ra sao qua các thế hệ, cách đọc tên máy nếu dòng có quy
tắc đặt tên. Không nhắc TGDĐ, không nhắc danh mục, không nhắc nơi lấy tin — xem
`references/writing-rules.md` mục "Giọng người giới thiệu dòng".

### {Dòng sản phẩm} có gì nổi bật?
4-6 điểm nổi bật, giải thích lợi ích sử dụng và giới hạn khi cần. Nếu triển khai các điểm nổi bật / lý do nên mua / tại sao nên sử dụng thành các mục con, **BẮT BUỘC mỗi mục con là một H4 riêng (#### [Tên mục] / <h4>...</h4>)** để chuẩn heading và luôn được tạo ảnh AI riêng, tuyệt đối không dùng nhãn in đậm giả heading.

### Các nhóm phiên bản hoặc dòng con phổ biến
Chỉ nhắc dòng con có sản phẩm trong URL danh mục. Bỏ section nếu dòng không có nhánh rõ ràng.

### Các sản phẩm {dòng sản phẩm} tại Thế Giới Di Động
Section **duy nhất** được phép nói TGDĐ đang bán gì. Dạng mặc định: mở heading
bằng 1-2 câu dẫn -> một bảng duy nhất -> 1-3 đoạn kết. Không tách H4 theo từng
sản phẩm. Bảng lấy từ sản phẩm thực sự xuất hiện trong URL danh mục, không thêm
model bên ngoài.

4 cột mặc định:

| Cột | Nội dung |
|---|---|
| Tên sản phẩm | Tên đầy đủ kèm mã SKU |
| Thông số kỹ thuật cơ bản | Màn hình, CPU, RAM, GPU, trọng lượng |
| Đối tượng sử dụng | Ai phù hợp nhất với **chính máy này** và vì sao. Phải chi tiết và phân biệt được giữa các dòng trong bảng: cùng là chơi game nhưng máy này đủ cho game online/eSports nhẹ, máy kia mới kham được game đồ họa nặng, máy khác lại nghiêng về nhu cầu CPU mạnh cho dựng phim, biên dịch, máy ảo. Không viết chung chung kiểu "phù hợp cho game và làm việc" |
| Giá tham khảo | Giá trực tiếp trên trang sản phẩm, kèm mốc ngày cập nhật ở câu dẫn hoặc đoạn kết |

Khi đã dùng bảng 4 cột này thì **không** dựng thêm section `Bảng thông số chính`
hay `Bảng giá` — chúng trùng nội dung. Chỉ tách bảng riêng khi người dùng yêu
cầu rõ.

### Hướng dẫn chọn {dòng sản phẩm} phù hợp
Hướng dẫn chọn trong phạm vi **cả dòng**, không co lại thành nhánh con hay danh
mục TGDĐ đang bán. Khi tư vấn theo nhu cầu sử dụng, mỗi nhu cầu là một heading
con (H4) riêng, ví dụ "{Dòng sản phẩm} cho văn phòng", "... cho chơi game". Mỗi
H4 viết 2-4 câu nêu cấu hình, kích thước, tính năng hoặc dung lượng phù hợp với
nhu cầu đó, không gộp mọi nhu cầu vào một đoạn văn dài. Không nhắc mã sản phẩm
và không đếm số phiên bản trong danh mục.

### Vì sao nên mua {dòng sản phẩm} tại Thế Giới Di Động?
Viết theo references/cta-rules.md.

### Câu hỏi thường gặp
5-8 câu hỏi đặc thù của dòng.
```


## Heading theo CMS Type 4

- Sapo dùng H2.
- Section chính dùng H3.
- Heading con và câu hỏi FAQ dùng H4.
- Không dùng H1.

## Giới hạn nội dung

- Chỉ model trong URL danh mục mới được nhắc tên.
- Không bắt buộc kiểm tra tồn kho, khu vực hoặc hiệu lực giá theo ngày.
- Không viết trải nghiệm thực tế như một bài review nếu không có dữ liệu thử nghiệm.

## CTA presentation override

The "Vi sao nen mua ... tai The Gioi Di Dong?" section must use one main section heading, a short lead, and checklist bullets. Do not create a smaller heading for each benefit. Follow `references/cta-rules.md`.

## Ranh giới nhắc TGDĐ

Chỉ 2 section được nhắc tên Thế Giới Di Động và nói TGDĐ đang bán gì:
`Các sản phẩm {dòng} tại Thế Giới Di Động` và section CTA. Các section còn lại
viết như bài giới thiệu dòng sản phẩm trên thị trường.
