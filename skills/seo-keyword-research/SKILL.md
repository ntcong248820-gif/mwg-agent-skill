---
name: seo-keyword-research
description: "Research keyword SEO dùng Ahrefs API và áp dụng bộ lọc intent nghiêm ngặt (general/product intent vs blog/specs/SKUs)."
user-invocable: true
when_to_use: "Trigger: research keyword, tìm từ khóa, nghiên cứu từ khóa, ahrefs keyword explorer, lọc keyword category."
category: seo-ops
keywords: [ahrefs, keyword, research, filter, general, intent]
metadata:
  version: "1.0.0"
---

# seo-keyword-research

Nghiên cứu danh sách từ khóa tìm kiếm (Matching Terms) từ Ahrefs Keyword Explorer API cho các trang danh mục (Category Landing Pages) và tinh lọc sạch theo ý định tìm kiếm (Search Intent).

## Scope

Skill này hướng dẫn và cung cấp bộ quy tắc phân loại, làm sạch từ khóa dành riêng cho **trang danh mục nhóm sản phẩm chung** (không bao gồm bài viết tin tức hay trang sản phẩm chi tiết).

## Ahrefs API Configuration

- **Endpoint:** `GET https://api.ahrefs.com/v3/keywords-explorer/matching-terms`
- **Authentication:** `Authorization: Bearer {AHREFS_API_KEY}` (lấy từ tệp `.env` ở gốc dự án)
- **Parameters thường dùng:**
  - `country=vn` (Thị trường Việt Nam)
  - `select=keyword,volume,difficulty,cpc,parent_topic`
  - `limit`: Điều chỉnh linh hoạt tùy thuộc số lượng API units còn lại.
    - *Lưu ý quan trọng:* Mỗi dòng từ khóa trả về tiêu tốn khoảng 23 API units. Hãy thiết lập `limit=15` hoặc `limit=20` khi quét các seed keywords phổ biến (như Asus Vivobook, Dell Inspiron...) để tiết kiệm tối đa quota, tránh bị lỗi `403 Forbidden` do cạn kiệt API units.

## Strict Intent Filtering Rules

Đối với Category Landing Pages, mục tiêu của người dùng là tìm dòng sản phẩm chung. Do đó, cần loại trừ toàn bộ từ khóa chi tiết hoặc không liên quan đến mua sắm dòng sản phẩm đó.

### 1. Từ khóa KHÔNG HỢP LỆ (Bị loại bỏ vào `irrelevant`)
- **Dòng sản phẩm con / Tiểu mục (Sub-lineups):** Chứa các từ như `flip`, `aero`, `go`, `pro`, `360`, `fli`.
- **Kích thước màn hình (Screen sizes):** Chứa `13`, `14`, `15`, `16`, `17`, `inch`, `"`, `oled`, `ips`, `2k`, `3k`, `4k`.
- **Thông số kỹ thuật chi tiết (Hardware configs):**
    - CPU: `i3`, `i5`, `i7`, `i9`, `ryzen`, `snapdragon`, `amd`, `intel`, `core x` (ngoại trừ tên riêng của dòng sản phẩm như HP OmniBook Ultra được phép giữ lại chữ `ultra`).
    - RAM/SSD: `8gb`, `16gb`, `32gb`, `64gb`, `256gb`, `512gb`, `1tb`.
- **Mã sản phẩm / SKU Codes:** Các ký tự kết hợp chữ và số (như `m5406wa-pp071ws`, `bz7q9pa`, `fp0023dx`, `bz7s1pa`,...).
- **Intent Blog / Review / So sánh / Hỗ trợ kỹ thuật:**
    - So sánh, đánh giá: `review`, `danh gia`, `đánh giá`, `vs`, `so sánh`.
    - Thông số: `specs`, `specification`, `specifications`.
    - Thời gian: `2024`, `2025`, `2026`.
    - Hỗ trợ / Phụ kiện: `driver`, `keyboard`, `màn hình` (nếu nghĩa thay màn hình), `sạc`...
    - Nguồn tin tức: `notebookcheck`, tin tức khác.
- **Off-brand:** Chứa tên của các thương hiệu đối thủ khi đang làm dòng sản phẩm cụ thể (ví dụ: chứa `dell`, `macbook`, `surface` khi đang làm HP).

### 2. Từ khóa HỢP LỆ (Giữ lại trong `relevant`)
- **Thuần tên dòng sản phẩm:** `laptop asus vivobook s`, `hp omnibook 5`, `máy tính vivobook s`.
- **Giá dòng sản phẩm bằng tiếng Việt:** `hp omnibook 5 giá`, `vivobook s giá`, `hp omnibook 5 giá bao nhiêu`.
- **Tiền tố Spec đặc trưng đi kèm hậu tố sản phẩm:** `hp omnibook 5 ai laptop` (AI chỉ đặc trưng dòng).
- **Ý định mua hàng trực tiếp:** `mua asus vivobook s`, `nơi bán hp omnibook`.

## Workflow

1. **Khởi tạo:** Tạo thư mục làm việc cho đợt research, có `data/raw/`, `data/processed/` và `reports/`.
2. **Thu thập dữ liệu:**
   - Đọc `AHREFS_API_KEY` từ `.env`.
   - Gửi yêu cầu API matching-terms tuần tự theo từng seed keyword.
   - *Xử lý lỗi quota:* Nếu API trả về 403 units limit, quét các tệp dữ liệu backup của đợt research trước để tìm từ khóa tương ứng trước khi cấu trúc lại.
3. **Phân lọc & Làm sạch (Relevance Filtering):**
   - Viết hoặc chạy kịch bản Python lọc nghiêm ngặt theo quy tắc ở trên.
   - Định dạng chuẩn hóa từ khóa: Cắt bỏ khoảng trắng dư thừa, dấu câu đặc biệt hoặc ký tự lạ ở cuối từ (dấu hai chấm, dấu phẩy, dấu gạch ngang...).
4. **Bổ sung Manual Seed:**
   - Trong nhiều trường hợp, Ahrefs Matching Terms API có thể bỏ sót các từ khóa core chính xác của seed hoặc trả về volume = 0 do giới hạn limit.
   - Chủ động thêm thủ công các từ khóa core sạch (ví dụ: `hp omnibook x` - Vol: 200, `asus vivobook s` - Vol: 150) và cập nhật số liệu volume chính xác nếu tệp raw bị thiếu hoặc sai lệch.
5. **Xuất Deliverables:** Lưu trữ tại thư mục làm việc:
   - `data/raw/ahrefs-matching-terms-raw.json` (dữ liệu thô thu thập từ API)
   - `data/processed/keywords-filtered-relevant.csv` (danh sách sạch được phân loại target_url và lineup_category)
   - `data/processed/keywords-filtered-irrelevant.csv` (danh sách từ khóa rác/bị loại bỏ để kiểm chứng)
   - `data/processed/keywords-all-dedup.csv` (toàn bộ từ khóa unique)
6. **Lập Báo Cáo:** Tạo tệp `reports/{yymmdd-hhmm}-keyword-research-{slug}.md` hiển thị thống kê tổng quan, các bảng markdown của từng lineup/URL kèm theo Search Volume, KD, CPC và Seed Source.

## Script Template Tham Khảo

Một đoạn mã Python mẫu áp dụng bộ lọc intent nghiêm ngặt:

```python
import re

exclude_patterns = [
    r"\bflip\b", r"\baero\b", r"\bgo\b", r"\bpro\b", r"\b360\b", r"\bfli\b",
    r"\b13\b", r"\b14\b", r"\b15\b", r"\b16\b", r"\b17\b",
    r"\binch\b", r"\"", r"\b2-in-1\b", r"\b2 in 1\b",
    r"\boled\b", r"\bips\b", r"\b2k\b", r"\b3k\b", r"\b4k\b",
    r"\bi3\b", r"\bi5\b", r"\bi7\b", r"\bi9\b",
    r"\bcore\s+\d+\b",
    r"\bryzen\b", r"\bsnapdragon\b", r"\bamd\b", r"\bintel\b",
    r"\b8gb\b", r"\b16gb\b", r"\b32gb\b", r"\b64gb\b",
    r"\b256gb\b", r"\b512gb\b", r"\b1tb\b",
    r"\b\w+-\w+\b",
    r"\b(?=[a-zA-Z]*\d)(?=\d*[a-zA-Z])[a-zA-Z0-9]{4,}\b"
]

blog_exclude_patterns = [
    r"\breview\b", r"\bdanh gia\b", r"đánh giá",
    r"\bspecs\b", r"\bspecification\b", r"\bspecifications\b",
    r"\brelease date\b", r"\bnotebookcheck\b", r"\bdesign\b",
    r"\bnext gen ai\b", r"\bvs\b", r"\b202\d\b",
    r"\bdriver\b", r"\bkeyboard\b"
]

def clean_and_filter(raw_keyword, brand_context=""):
    # Xóa ký tự lạ ở cuối
    kw = re.sub(r"[:,\-\_\s\+]+$", "", raw_keyword).strip()
    kw_lower = kw.lower()
    
    # Loại trừ thương hiệu đối thủ
    if brand_context == "hp" and any(b in kw_lower for b in ["dell", "lenovo", "asus", "macbook", "acer", "surface"]):
        return None, "Off-brand"
        
    # Lọc specs / dòng con
    for pat in exclude_patterns:
        if re.search(pat, kw_lower):
            return None, "Sub-model/Specs"
            
    # Lọc blog/review
    for pat in blog_exclude_patterns:
        if re.search(pat, kw_lower):
            return None, "Blog/Review Intent"
            
    return kw, "Relevant"
```
