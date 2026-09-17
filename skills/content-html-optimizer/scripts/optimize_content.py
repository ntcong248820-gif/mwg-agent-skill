#!/usr/bin/env python3
"""
content-html-optimizer/scripts/optimize_content.py
Pipeline tối ưu HTML source content cho bài viết/infobox TGDĐ:
1. Di chuyển ảnh vào đúng section theo image-placement.json, lấy URL ảnh từ
   {workspace}/cdn-urls.json (dữ liệu riêng từng bài, không hardcode trong script)
2. Thêm alt, title, caption từ image-metadata.csv
3. Tự động fetch keyword ↔ URL từ 2 Sheet MWG và chèn Internal Link (1 link / 1 URL)
4. Review & lọc các link chèn kém tự nhiên
5. Chuẩn hóa table HTML theo MWG standard mới (header đen #000000/chữ vàng #ffe14c,
   border #cccccc, table-layout fixed, width % tự tính theo cột, cột giá tự nhận diện)
6. Bọc <strong> cho <h3>/<h4>, xóa dump images & empty headings.

Usage:
    python3 .agents/skills/content-html-optimizer/scripts/optimize_content.py \
        --workspace content-workspaces/{topic-slug} \
        [--fetch-links] [--links-json custom_links.json]
"""

import os
import argparse
import csv
import json
import math
import re
import unicodedata
import subprocess
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString

# ─── Constants ──────────────────────────────────────────────────────────────
def _require(name, value, hint):
    """Fail loudly instead of querying the wrong spreadsheet with an empty id."""
    if not value:
        raise SystemExit(
            "%s is not set.\n"
            "Export it to point this skill at your own sheet:\n"
            "    export %s=<spreadsheet-id>\n"
            "%s" % (name, name, hint))
    return value


SHEET_ALL_KW_ID = _require("SHEET_ALL_KW_ID", os.environ.get("SHEET_ALL_KW_ID", ""),
    "Sheet holding keyword -> URL rows.")
SHEET_BAI_TIN_ID = _require("SHEET_BAI_TIN_ID", os.environ.get("SHEET_BAI_TIN_ID", ""),
    "Sheet holding article title -> URL rows.")

# Sàn số dòng đọc được từ 2 Sheet. Đặt thấp hơn nhiều so với kích thước thật
# (06/09/2026: 15941 và 6843) để Sheet co giãn bình thường không chạm sàn, nhưng
# vẫn bắt được lượt fetch trả về một phần. Đã gặp: chạy hàng loạt, một lượt fetch
# thiếu làm bài rụng 5 link nguồn BÀI TIN mà script vẫn exit 0, chỉ lộ ra khi so
# tập URL với bản build lại.
MIN_ROWS_ALL_KW = 5000
MIN_ROWS_BAI_TIN = 2000

# Table style (MWG comparison-table standard: header đen/chữ vàng, cột giá tự nhận diện)
TABLE_MIN_WIDTH_PX = 620
TABLE_BORDER_COLOR = "#cccccc"
TABLE_HEADER_BG = "#000000"
TABLE_HEADER_COLOR = "#ffe14c"
TABLE_HIGHLIGHT_COLOR = "#d9381e"
PRICE_COLUMN_WIDTH_PCT = 15
# Cột giá dùng width px cố định, KHÔNG dùng %. Lý do: 15% chỉ đủ chỗ ở bề rộng
# desktop (15% của 620px = 93px). Trên mobile 375px container còn ~355px thì 15%
# = 53px, mà "1.090.000₫" với `white-space: nowrap` cần ~79px → chữ giá bị cắt.
# Width px giữ nguyên ở mọi bề rộng nên giá không bị cắt cả trên mobile lẫn desktop.
PRICE_COLUMN_WIDTH_PX = 100
# Sàn width cột text (xem `_min_text_column_pct`)
MIN_TEXT_COLUMN_WIDTH_PCT = 15
MAX_TEXT_COLUMN_WIDTH_PCT = 40
# Dưới 2 vì chữ xuống dòng theo ranh giới từ, không bao giờ chia đều được
LABEL_WRAP_LINE_BUDGET = 1.8
CHAR_PX_AT_14 = 7.2
TABLE_CELL_PADDING_PX = 22
PRICE_PATTERN = re.compile(r"\d[\d.,]*\s*(₫|đ)", re.IGNORECASE)
PRICE_MATCH_RATIO = 0.6
HIGHLIGHT_HEADER_KEYWORDS = (
    "ưu đãi", "khuyến mãi", "giá sốc", "giá sale", "giá online",
    "giá giảm", "giảm giá", "còn lại", "sau khi giảm",
)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_image_metadata(metadata_csv: Path) -> dict:
    """Trả về dict {file_name: {'alt': ..., 'title': ...}}"""
    meta = {}
    if not metadata_csv.exists():
        print(f"[WARN] Metadata CSV not found at {metadata_csv}")
        return meta
    with open(metadata_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = (row.get("filename") or row.get("file-name") or "").strip()
            if fname:
                meta[fname] = {
                    "alt": (row.get("alt") or "").strip(),
                    "title": (row.get("title") or "").strip(),
                    "caption": (row.get("caption") or row.get("description") or "").strip()
                }
    return meta


def load_cdn_urls(cdn_json: Path) -> dict:
    """Trả về dict {file_name: cdn_url} của riêng workspace.

    URL CDN là dữ liệu của từng bài (mỗi bài upload ảnh lên CMS một lần, ra một
    bộ URL riêng), nên phải nằm cạnh bài trong cdn-urls.json — không được nhét
    vào script dùng chung: hai workspace đặt trùng tên file ảnh sẽ nhận nhầm
    URL của nhau mà không có lỗi nào bắn ra.
    """
    if not cdn_json.exists():
        return {}
    with open(cdn_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        print(f"[WARN] {cdn_json.name} phải là object {{\"ten-file.jpg\": \"url\"}}, bỏ qua.")
        return {}
    return {str(k).strip(): str(v).strip() for k, v in data.items() if str(v).strip()}


def fetch_sheet_data(spreadsheet_id: str, range_str: str) -> list:
    """Gọi gws CLI để fetch data từ Google Sheet."""
    params_json = json.dumps({"spreadsheetId": spreadsheet_id, "range": range_str})
    cmd = f"command gws sheets spreadsheets values get --params '{params_json}'"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        return data.get("values", [])
    except Exception as e:
        print(f"[WARN] Failed to fetch sheet {spreadsheet_id} ({range_str}): {e}")
        return []


def load_internal_links_from_sheets() -> list[dict]:
    """Fetch keyword ↔ URL từ cả 2 Google Sheets."""
    links = []
    seen_urls = set()

    print("[INFO] Fetching keywords from Sheet 'All KW'...")
    rows_kw = fetch_sheet_data(SHEET_ALL_KW_ID, "All KW!L2:O")
    for row in rows_kw:
        if len(row) >= 4:
            kw = row[0].strip()
            url = row[3].strip()
            if kw and url and url.startswith("http") and url not in seen_urls:
                links.append({"keyword": kw, "url": url, "source": "All KW"})
                seen_urls.add(url)

    print(f"[INFO] Fetched {len(links)} links from 'All KW'")

    print("[INFO] Fetching keywords from Sheet 'BÀI TIN'...")
    rows_tin = fetch_sheet_data(SHEET_BAI_TIN_ID, "BÀI TIN!A2:E")
    count_tin = 0
    for row in rows_tin:
        if len(row) >= 5:
            url = row[1].strip()
            kw = row[4].strip()
            if kw and url and url.startswith("http") and url not in seen_urls:
                links.append({"keyword": kw, "url": url, "source": "BÀI TIN"})
                seen_urls.add(url)
                count_tin += 1

    print(f"[INFO] Fetched {count_tin} new links from 'BÀI TIN'")

    # Cổng chặn fetch hụt. Đã gặp lượt chạy hàng loạt trả về ít dòng hơn hẳn mà
    # vẫn exit 0: bài mất 5 link nguồn BÀI TIN, không có lỗi nào bắn ra và chỉ lộ
    # ra khi so tập URL với bản build lại. Thà dừng còn hơn ghi đè final bằng bản
    # thiếu link.
    count_kw = len(links) - count_tin
    if count_kw < MIN_ROWS_ALL_KW or count_tin < MIN_ROWS_BAI_TIN:
        sys.exit(
            f"[ERROR] Fetch Sheet hụt: All KW {count_kw} (sàn {MIN_ROWS_ALL_KW}), "
            f"BÀI TIN {count_tin} (sàn {MIN_ROWS_BAI_TIN}). Dừng để không ghi đè "
            f"final-content.html bằng bản thiếu link. Chạy lại lệnh."
        )
    # Sort by keyword length descending so longer compound keywords match first
    links.sort(key=lambda x: len(x["keyword"]), reverse=True)
    return links


# --- Tên hãng đứng trần: chỉ link khi câu đang nói về HÃNG hoặc máy của hãng ---

BARE_BRANDS = {
    "hp", "dell", "asus", "acer", "msi", "lenovo", "apple", "samsung", "lg",
    "xiaomi", "gigabyte", "viewsonic", "aoc", "philips", "sony", "brother",
    "canon", "epson", "huawei", "honor", "microsoft",
}

# Tên dòng máy hay đứng ngay sau tên hãng. Giữ danh sách này để bắt cả khi
# người viết viết thường ("hp victus"), trường hợp mà rule chữ-hoa bỏ lọt.
BRAND_MODEL_WORDS = {
    "victus", "omen", "pavilion", "probook", "elitebook", "envy", "compaq",
    "tuf", "rog", "legion", "loq", "nitro", "predator", "katana", "cyborg",
    "g15", "g16", "thin", "strix", "zephyrus", "helios", "vivobook", "zenbook",
    "inspiron", "vostro", "latitude", "xps", "modern", "prestige", "summit",
    "thinkpad", "ideapad", "yoga", "swift", "aspire", "omnibook", "macbook",
    "galaxy", "gram", "expertbook", "proart", "alienware", "stealth", "raider",
    "surface", "imac",
}

# Từ đứng ngay TRƯỚC tên hãng, cho biết câu đang nói về hãng/máy của hãng
BRAND_CONTEXT_WORDS = (
    "laptop", "máy", "máy tính", "hãng", "thương hiệu", "của", "dòng", "mẫu",
    "sản phẩm", "nhà sản xuất", "chính hãng", "từ", "bởi", "thuộc",
    "điện thoại", "màn hình", "máy in", "tablet", "pc",
)

RELATED_BOX_HINTS = ("xem thêm", "xem them", "tham khảo thêm")


def _next_word_after_match(after_text: str) -> str:
    """
    Từ đứng ngay sau match, CHỈ khi giữa hai từ đúng là khoảng trắng.
    Có dấu câu chen vào ("của Acer. Máy này...") -> trả rỗng, vì lúc đó từ
    viết hoa phía sau là câu mới, không phải tên riêng đi kèm hãng.
    """
    m = re.match(r"[ \t ]+([^\s]+)", after_text)
    return m.group(1) if m else ""


def _brand_followed_by_proper_noun(after_text: str) -> bool:
    """
    True khi tên hãng đứng ngay trước một tên riêng viết hoa — tên dòng máy
    ("HP Victus") hoặc tên công nghệ độc quyền ("Acer ComfyView", "Acer
    Purified Voice", "Asus Lumina OLED", "AMD FreeSync").

    Cả hai trường hợp đều KHÔNG phải nhắc tới hãng, nên không được nhận link
    hãng: người đọc click vào "Acer" trong "Acer ComfyView" là đang click vào
    tên một công nghệ màn hình, không phải vào hãng Acer.
    """
    word = _next_word_after_match(after_text)
    if not word:
        return False
    token = word.strip("(),.;:!?/\"'“”…-–—")
    if not token:
        return False
    if token.lower() in BRAND_MODEL_WORDS:
        return True
    return token[:1].isupper()


SPEC_UNIT_AFTER = re.compile(
    r"^[ \t\u00a0]*\d+(?:[.,]\d+)?[ \t\u00a0]*"
    r"(?:w|wh|kw|v|a|mah|gb|tb|mb|ghz|mhz|hz|inch|kg|g|mm|cm|nits|nit|bit|fps|core|nhân|luồng)\b",
    re.IGNORECASE,
)


def _is_spec_label_usage(after_text: str) -> bool:
    """True khi keyword đang làm nhãn thông số ("sạc 150 W", "pin 60 Wh").

    Trong ngữ cảnh này keyword nói về bộ phận có sẵn của máy, không phải lời mời
    mua phụ kiện rời — link sang category phụ kiện là lệch ngữ cảnh.
    """
    return bool(SPEC_UNIT_AFTER.match(after_text))


def _has_brand_context_before(before_text: str) -> bool:
    """True khi ngay trước tên hãng là từ chỉ hãng/ngành hàng."""
    tail = re.sub(r"\s+", " ", before_text.lower()).rstrip()
    return any(tail.endswith(w) for w in BRAND_CONTEXT_WORDS)


def _clean_inline_text(tag) -> str:
    """
    Text phẳng của một tag, dùng cho anchor/title.

    Nối bằng khoảng trắng để chữ ở hai tag cạnh nhau không bị dính
    ("nhất" + "bền" -> "nhất bền"), rồi gỡ khoảng trắng dư trước dấu câu
    ("tốt nhất , bền" -> "tốt nhất, bền").
    """
    text = re.sub(r"\s+", " ", tag.get_text(" ", strip=True)).strip()
    return re.sub(r"\s+([,.;:!?)\]…])", r"\1", text)


def _is_related_box_marker(tag) -> bool:
    """<p><strong>Xem thêm</strong>:</p> — dòng mở đầu box bài liên quan."""
    if tag is None or getattr(tag, "name", None) != "p":
        return False
    text = re.sub(r"\s+", " ", tag.get_text(strip=True)).lower()
    if len(text) > 40:
        return False
    return any(hint in text for hint in RELATED_BOX_HINTS)


def _p_starts_related_box(p) -> bool:
    """<p> dạng 'Xem thêm: {link}, {link}' — link nằm inline trong cùng thẻ <p>."""
    text = re.sub(r"\s+", " ", p.get_text(strip=True)).lower().lstrip("-•* ")
    return any(text.startswith(hint) for hint in RELATED_BOX_HINTS)


def related_box_lists(soup: BeautifulSoup) -> list:
    """
    Các <ul>/<ol> thuộc box "Xem thêm" — nhận diện qua marker
    <p><strong>Xem thêm</strong>: đứng ngay trước list.
    """
    lists = []
    for lst in soup.find_all(["ul", "ol"]):
        checked = 0
        prev = lst.previous_sibling
        while prev is not None and checked < 2:
            if isinstance(prev, NavigableString):
                prev = prev.previous_sibling
                continue
            checked += 1
            if _is_related_box_marker(prev):
                lists.append(lst)
                break
            prev = prev.previous_sibling
    return lists


def normalize_related_article_links(soup: BeautifulSoup) -> dict:
    """
    Box "Xem thêm": anchor phải là TOÀN BỘ tiêu đề bài liên quan.

    Bài paste từ CMS hay chỉ bọc 1 cụm trong tiêu đề — "Bật mí top <a>8 laptop
    tốt nhất</a>, bền nhất trên thị trường hiện nay" — anchor vừa không nói
    được bài đích viết gì, vừa cho vùng click bé xíu. Hàm này nới anchor ra
    hết tiêu đề và gán luôn title="{tiêu đề}".

    Chỉ đụng vào <li> trong box "Xem thêm". Dạng inline (nhiều link trong cùng
    một <p>) không tự sửa được vì script không biết ranh giới từng tiêu đề →
    chỉ cảnh báo.

    Trả về {"expanded": [...], "warnings": [...]}.
    """
    expanded = []
    warnings = []

    for lst in related_box_lists(soup):
        for li in lst.find_all("li"):
            full_text = _clean_inline_text(li)
            if not full_text:
                continue

            anchors = li.find_all("a")
            if not anchors:
                warnings.append(f"dòng 'Xem thêm' không có link: {full_text[:70]}")
                continue

            keep = anchors[0]
            href = (keep.get("href") or "").strip()
            if not href:
                warnings.append(f"link 'Xem thêm' thiếu href: {full_text[:70]}")
                continue

            dropped = [
                (a.get("href") or "").strip()
                for a in anchors[1:]
                if (a.get("href") or "").strip() and (a.get("href") or "").strip() != href
            ]
            anchor_text = _clean_inline_text(keep)

            if anchor_text == full_text and keep.get("title") == full_text and not dropped:
                continue

            new_a = soup.new_tag("a", href=href, target="_blank", rel="noopener noreferrer")
            new_a["title"] = full_text
            new_a.string = full_text

            li.clear()
            li.append(new_a)

            expanded.append({
                "url": href,
                "anchor_before": anchor_text,
                "anchor_after": full_text,
                "dropped_urls": dropped,
            })

    # Dạng inline: cảnh báo anchor ngắn bất thường, người viết tự nới ra full title
    for p in soup.find_all("p"):
        if not _p_starts_related_box(p):
            continue
        for a in p.find_all("a"):
            anchor_text = _clean_inline_text(a)
            if 0 < len(anchor_text) < 25:
                warnings.append(
                    f"anchor 'Xem thêm' inline có thể chỉ là 1 cụm trong tiêu đề, "
                    f"nới ra hết tiêu đề: '{anchor_text}'"
                )

    return {"expanded": expanded, "warnings": warnings}


def _article_own_ids(soup: BeautifulSoup, self_url: str = "") -> set:
    """ID của chính bài đang xử lý, để không chèn link trỏ về chính nó.

    Nguồn 1: `--self-url` hoặc `source/article-url.txt`.
    Nguồn 2: đường dẫn ảnh CDN dạng `cdn.tgdd.vn/News/{id}/` — chỉ có ở bài
    upload ảnh vào thư mục bài của chính nó, nên không đủ dùng một mình.
    """
    ids = set()
    if self_url:
        m = re.search(r"(\d{5,8})/?$", self_url.split("?")[0].rstrip("/"))
        if m:
            ids.add(m.group(1))
    ids.update(re.findall(r"cdn\.tgdd\.vn/+News/+(\d{5,8})/", str(soup)))
    return ids


def _fold(s: str) -> str:
    """Bỏ dấu + hạ chữ thường, để so anchor không phụ thuộc hoa/thường và dấu."""
    d = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in d if unicodedata.category(c) != "Mn")


def load_no_link_anchors(workspace: Path, cli_anchors=None) -> list:
    """Anchor KHÔNG được chèn internal link (nội dung ngoài danh mục TGDĐ).

    Bài infobox được phép viết phần kiến thức về loại/dòng SP mà TGDĐ không
    kinh doanh, nhưng phần đó không được dẫn về trang bán — link sẽ trỏ tới
    trang filter rỗng sản phẩm, hại UX và SEO.

    Nguồn: `metadata/no-link-anchors.txt` (1 anchor/dòng, `#` là ghi chú)
    cộng với các giá trị `--no-link-anchor` truyền trên CLI.
    """
    anchors = list(cli_anchors or [])
    f = workspace / "metadata" / "no-link-anchors.txt"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                anchors.append(line)
    return [a for a in {_fold(x) for x in anchors} if a]


def filter_no_link_anchors(links: list[dict], no_link: list[str]) -> list[dict]:
    """Bỏ mọi link có keyword khớp anchor loại trừ. Khớp cả biến thể chứa nó."""
    if not no_link:
        return links
    kept = []
    for item in links:
        folded = _fold(item["keyword"])
        hit = next((n for n in no_link if n in folded), None)
        if hit:
            print(f"[SKIP] skip-link: {item['keyword']} (no-link-anchor)")
        else:
            kept.append(item)
    return kept


def _is_self_link(url: str, own_ids: set) -> bool:
    """URL có trỏ về chính bài này không. Sheet All KW / BÀI TIN map keyword của
    bài về đúng URL bài đó, nên bài 'top laptop pin trâu' tự chèn link 'laptop
    pin trâu' về chính nó — link chết vô nghĩa, phải chặn."""
    if not own_ids:
        return False
    tail = re.search(r"(\d{5,8})/?$", url.split("?")[0].split("#")[0].rstrip("/"))
    return bool(tail and tail.group(1) in own_ids)


def insert_internal_links(soup: BeautifulSoup, links: list[dict], self_url: str = "") -> list[dict]:
    """
    Chèn Internal Link vào HTML:
    - Target containers: Thẻ <p> thường (bỏ qua p.titleOfImages), <li> (bullet list), và thẻ <h2> (H2 ĐƯỢC PHÉP chèn link).
    - CẤM chèn trong: <h3>, <h4>, <h5>, <h6>, <table>, <img>, thẻ <a> đã có, và <li>/<p> của box "Xem thêm".
    - Rule 1: 1 URL chỉ chèn tối đa 1 lần duy nhất trong toàn bài.
    - Rule 2: Chống cắt chữ (không cắt lẻ từ thương hiệu như 'HP' trong 'HP Victus').
    - Rule 3: Xóa bỏ khoảng trắng thừa bên trong thẻ <a> (<a>sạc</a> thay vì <a> sạc </a>).
    - Rule 4: Loại bỏ match sai ngữ cảnh (ví dụ: 'di động' trong 'Thế Giới Di Động' không trỏ về trang Điện thoại ĐTDĐ, 'máy tính' trong laptop không trỏ về Máy tính để bàn).
    - Rule 5: Tên hãng trần chỉ link ở chỗ đang nói về hãng, không link khi hãng
      là một phần tên công nghệ/dòng máy ('Acer' trong 'Acer ComfyView').
    """
    inserted_records = []
    used_urls = set()

    own_ids = _article_own_ids(soup, self_url)
    if own_ids:
        links = [it for it in links if not _is_self_link(it["url"], own_ids)]

    # Thu thập các URL đã có sẵn trong bài
    for a in soup.find_all("a"):
        href = a.get("href", "").strip()
        if href:
            used_urls.add(href)

    # Containers hợp lệ: H2 và P
    target_containers = []
    for h2 in soup.find_all("h2"):
        if not h2.find("a"):
            target_containers.append(h2)

    # Box "Xem thêm" nằm ngoài vùng chèn: anchor ở đó phải là full tiêu đề bài
    # liên quan (xem normalize_related_article_links), không phải link keyword
    # cắt ngang tiêu đề.
    related_li_ids = {
        id(li)
        for lst in related_box_lists(soup)
        for li in lst.find_all("li")
    }

    for p in soup.find_all("p"):
        if "titleOfImages" in p.get("class", []):
            continue
        if p.find_parent(["table", "h3", "h4", "h5", "h6"]):
            continue
        if _p_starts_related_box(p):
            continue
        text_content = p.get_text(strip=True)
        if text_content and not (len(p.find_all("img")) > 0 and len(text_content) < 5):
            target_containers.append(p)

    for li in soup.find_all("li"):
        if li.find_parent(["table", "h3", "h4", "h5", "h6"]):
            continue
        if id(li) in related_li_ids:
            continue
        text_content = li.get_text(strip=True)
        if text_content and not (len(li.find_all("img")) > 0 and len(text_content) < 5):
            target_containers.append(li)

    # Ngữ cảnh cấm match nhầm (keyword, url_contains, forbidden_adjacent_words)
    CONTEXT_EXCLUSIONS = [
        ("di động", "dtdd", ["thế giới", "thế giới di động", "máy tính"]),
        ("máy tính", "may-tinh-de-ban", ["xách tay", "bảng", "laptop", "chơi game", "gaming", "linh kiện"]),
        ("bộ sạc", "cap-dien-thoai", ["laptop", "thân máy"]),
        ("sạc", "sac-cap", ["laptop", "thân máy", "pin", "thời gian", "công suất", "đầy pin"]),
        ("pin", "/pin", ["thời lượng", "laptop", "làm nguồn", "chính", "trong", "dung lượng", "tuổi thọ", "sạc đầy", "hiệu năng"]),
        ("camera", "camera-giam-sat", ["xoay", "game", "fps", "bóng mờ", "chuyển động"]),
    ]

    for item in links:
        kw = item["keyword"].strip()
        url = item["url"].strip()
        if url in used_urls or len(kw) < 2:
            continue

        kw_lower = kw.lower()

        # Build regex pattern với boundary chuẩn
        pattern_str = r'(?<!\w)' + re.escape(kw) + r'(?!\w)'
        pattern = re.compile(pattern_str, re.IGNORECASE)

        # Tên hãng trần: quét 2 lượt. Lượt 1 chỉ nhận chỗ câu đang thật sự nói
        # về hãng ("laptop Acer", "của Acer"); hết chỗ đó mới hạ xuống lượt 2
        # nhận chỗ trung tính. Keyword thường chỉ cần 1 lượt.
        pass_modes = ("brand-context", "any") if kw_lower in BARE_BRANDS else ("any",)

        inserted_this_kw = False
        for pass_mode in pass_modes:
            if inserted_this_kw:
                break

            for container in target_containers:
                if inserted_this_kw:
                    break

                text_nodes = [
                    node for node in container.find_all(string=True)
                    if not node.find_parent(["a", "script", "style", "table", "h3", "h4", "h5", "h6"])
                ]

                for node in text_nodes:
                    if not isinstance(node, NavigableString):
                        continue

                    for match in pattern.finditer(str(node)):
                        start, end = match.span()
                        raw_matched = str(node)[start:end]
                        before_text = str(node)[:start]
                        after_text = str(node)[end:]

                        # 1. Tên hãng trần: chống cắt chữ VÀ chống link vào tên
                        #    công nghệ độc quyền ("Acer" trong "Acer ComfyView")
                        if kw_lower in BARE_BRANDS:
                            if _brand_followed_by_proper_noun(after_text):
                                continue
                            if pass_mode == "brand-context" and not _has_brand_context_before(before_text):
                                continue

                        # 2. Kiểm tra ngữ cảnh cấm (Exclusions)
                        skip_match = False
                        full_context_snippet = re.sub(r'\s+', ' ', (before_text[-150:] + raw_matched + after_text[:150]).lower())
                        for ex_kw, ex_url, forbidden_list in CONTEXT_EXCLUSIONS:
                            if ex_kw.lower() in kw_lower and ex_url in url:
                                if any(f_word in full_context_snippet for f_word in forbidden_list):
                                    skip_match = True
                                    break
                                # "sạc 150 W", "pin 60 Wh": đang tả thông số của
                                # máy, không phải rủ mua phụ kiện rời
                                if _is_spec_label_usage(after_text):
                                    skip_match = True
                                    break
                        if skip_match:
                            continue

                        # 3. Trim khoảng trắng thừa trong anchor text để thẻ <a> không bị lỡ space
                        l_trim = len(raw_matched) - len(raw_matched.lstrip())
                        r_trim = len(raw_matched) - len(raw_matched.rstrip())

                        clean_anchor = raw_matched.strip()
                        if not clean_anchor:
                            continue

                        before_text += raw_matched[:l_trim]
                        after_text = raw_matched[len(raw_matched) - r_trim:] + after_text

                        a_tag = soup.new_tag(
                            "a",
                            href=url,
                            target="_blank",
                            rel="noopener noreferrer"
                        )
                        a_tag.string = clean_anchor

                        new_nodes = []
                        if before_text:
                            new_nodes.append(NavigableString(before_text))
                        new_nodes.append(a_tag)
                        if after_text:
                            new_nodes.append(NavigableString(after_text))

                        node.replace_with(*new_nodes)

                        used_urls.add(url)
                        inserted_this_kw = True
                        inserted_records.append({
                            "keyword": kw,
                            "anchor_text": clean_anchor,
                            "url": url,
                            "source": item.get("source", ""),
                            "container": container.name,
                            "snippet": container.get_text(strip=True)[:120] + "..."
                        })
                        break

                    if inserted_this_kw:
                        break

    return inserted_records




def _table_column_profile(table):
    """
    Phân tích cấu trúc cột: trả về list[dict] {"is_price": bool, "avg_len": int}
    theo thứ tự cột, hoặc None nếu bảng có colspan/rowspan lệch cột (dùng fallback).
    """
    rows = table.find_all("tr")
    if not rows:
        return None

    header_cells = rows[0].find_all(["td", "th"])
    ncols = len(header_cells)
    if ncols == 0:
        return None

    texts_by_col = [[c.get_text(strip=True)] for c in header_cells]
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) != ncols or any(c.get("colspan") or c.get("rowspan") for c in cells):
            return None
        for i, cell in enumerate(cells):
            texts_by_col[i].append(cell.get_text(strip=True))

    profile = []
    for texts in texts_by_col:
        body_texts = [t for t in texts[1:] if t]
        is_price = bool(body_texts) and (
            sum(1 for t in body_texts if PRICE_PATTERN.search(t)) / len(body_texts)
            >= PRICE_MATCH_RATIO
        )
        avg_len = max(sum(len(t) for t in texts) // max(len(texts), 1), 1)
        max_len = max((len(t) for t in texts), default=1)
        profile.append({"is_price": is_price, "avg_len": avg_len, "max_len": max_len})

    return profile


def _min_text_column_pct(max_len):
    """Sàn width cho 1 cột text: đủ để ô dài nhất xuống khoảng 2 dòng.

    Bảng rộng TABLE_MIN_WIDTH_PX px, font 14px (~CHAR_PX_AT_14 px/ký tự có dấu),
    padding 2 bên 20px + viền. Chia tỉ lệ thuần theo độ dài trung bình làm cột
    nhãn (trung bình ~15 ký tự) tụt xuống 10% = 62px, nhãn 20+ ký tự vỡ 4-5 dòng
    và ngắt giữa từ vì `word-break: break-word`.
    """
    need_px = (max_len / LABEL_WRAP_LINE_BUDGET) * CHAR_PX_AT_14 + TABLE_CELL_PADDING_PX
    pct = math.ceil(need_px / TABLE_MIN_WIDTH_PX * 100 / 5) * 5
    return min(max(pct, MIN_TEXT_COLUMN_WIDTH_PCT), MAX_TEXT_COLUMN_WIDTH_PCT)


def _compute_column_widths(profile):
    """Cột giá cố định PRICE_COLUMN_WIDTH_PCT%; phần còn lại chia cho cột text
    theo tỉ lệ độ dài nội dung trung bình, làm tròn về mốc 5%, nhưng không cột
    nào được xuống dưới sàn `_min_text_column_pct` của chính nó."""
    price_total = sum(PRICE_COLUMN_WIDTH_PCT for col in profile if col["is_price"])
    remaining = max(100 - price_total, 0)
    text_idx = [i for i, col in enumerate(profile) if not col["is_price"]]

    widths = [PRICE_COLUMN_WIDTH_PCT if col["is_price"] else 0 for col in profile]
    if not text_idx:
        return widths

    lengths = [profile[i]["avg_len"] for i in text_idx]
    total_len = sum(lengths) or 1
    rounded = [max(round(remaining * length / total_len / 5) * 5, 10) for length in lengths]

    # Nâng cột hẹp lên sàn, bù lại bằng cột rộng nhất (cột rộng nhất luôn là cột
    # câu văn dài, thừa chỗ nhất khi bị cắt bớt).
    floors = [_min_text_column_pct(profile[i].get("max_len", profile[i]["avg_len"]))
              for i in text_idx]
    if len(rounded) > 1:
        for k, floor in enumerate(floors):
            deficit = floor - rounded[k]
            if deficit <= 0:
                continue
            donor = max((j for j in range(len(rounded)) if j != k),
                        key=lambda j: rounded[j])
            if rounded[donor] - deficit < floors[donor]:
                continue
            rounded[k] += deficit
            rounded[donor] -= deficit

    rounded[-1] += 100 - price_total - sum(rounded)

    for i, w in zip(text_idx, rounded):
        widths[i] = w
    return widths


def _detect_highlight_column(header_cells, profile):
    """Cột 'giá ưu đãi' cần bôi đậm đỏ #d9381e: match keyword header trước,
    fallback về cột giá cuối cùng khi có ≥2 cột giá. None nếu không có cột giá."""
    price_idx = [i for i, col in enumerate(profile) if col["is_price"]]
    if not price_idx:
        return None

    for i in price_idx:
        if any(kw in header_cells[i].get_text(strip=True).lower() for kw in HIGHLIGHT_HEADER_KEYWORDS):
            return i

    return price_idx[-1] if len(price_idx) >= 2 else None


def _cell_style(is_price: bool, width_pct=None, highlight=False, is_header=False) -> str:
    wrap = (
        "white-space: nowrap;"
        if is_price
        else "white-space: normal; overflow-wrap: anywhere; word-break: break-word;"
    )
    if is_price:
        width = f"width: {PRICE_COLUMN_WIDTH_PX}px; "
    else:
        width = f"width: {width_pct}%; " if width_pct is not None else ""
    align = "center" if (is_header or is_price) else "left"
    style = (
        f"{width}box-sizing: border-box; border: 1px solid {TABLE_BORDER_COLOR}; "
        f"padding: 8px 10px; text-align: {align}; vertical-align: middle; {wrap}"
    )
    if is_header:
        style += f" background: {TABLE_HEADER_BG}; color: {TABLE_HEADER_COLOR}; font-weight: bold;"
    elif highlight:
        style += f" font-weight: bold; color: {TABLE_HIGHLIGHT_COLOR};"
    return style


def normalize_tables(soup: BeautifulSoup):
    """
    Chuẩn hóa bảng HTML theo MWG standard mới (bảng so sánh cấu hình/giá):
    - `<table>`: table-layout fixed, border-collapse collapse, width 100% (KHÔNG min-width).
    - `<th>`: nền đen #000000, chữ vàng #ffe14c, bold, canh giữa, border #cccccc.
    - Cột giá (tự nhận diện qua ký hiệu ₫/đ trong nội dung): canh giữa, không xuống dòng,
      width cố định PRICE_COLUMN_WIDTH_PX px/cột (px chứ không phải %, xem comment ở constant).
    - Cột text: canh trái, cho phép wrap (overflow-wrap/word-break chống tràn layout),
      width tự chia theo tỉ lệ độ dài nội dung trung bình trên phần % còn lại.
    - Cột "giá ưu đãi" (theo keyword header hoặc cột giá cuối khi có ≥2 cột giá):
      bôi đậm đỏ #d9381e để nổi bật.
    Bảng có colspan/rowspan lệch cột dùng fallback: style border/padding/wrap chuẩn,
    không set width % hay phát hiện cột giá.
    """
    for table in soup.find_all("table"):
        for attr in ("border", "cellspacing", "cellpadding", "align"):
            if table.has_attr(attr):
                del table[attr]
        # KHÔNG set min-width. `min-width` thắng `max-width` trong CSS, nên
        # `min-width: 620px; max-width: 100%` làm bảng đứng cứng 620px trong
        # container mobile ~355px. Container bài viết TGDĐ có `overflow-x: hidden`
        # nên phần tràn bị CẮT chứ không scroll được — cột giá mất hẳn khỏi màn
        # hình. Bọc bảng trong <div style="overflow-x:auto"> cũng không cứu được:
        # CMS TGDĐ chỉ giữ inline style trên img/table/th/td, style của div và p
        # đều bị xoá. Để bảng co theo container là cách duy nhất đúng ở cả 2 phía.
        table["style"] = (
            "width: 100%; max-width: 100%; "
            "border-collapse: collapse; table-layout: fixed; margin: 0; "
            "font-size: 14px; line-height: 1.5; color: #333333;"
        )

        rows = table.find_all("tr")
        if not rows:
            continue

        tbody = table.find("tbody")
        if tbody is None:
            tbody = soup.new_tag("tbody")
            for row in rows:
                tbody.append(row.extract())
            table.append(tbody)
            for leftover in table.find_all(["thead", "tfoot"]):
                if not leftover.find("tr"):
                    leftover.decompose()

        header_cells = rows[0].find_all(["td", "th"])
        for cell in header_cells:
            cell.name = "th"
            for p in cell.find_all("p"):
                p.unwrap()

        profile = _table_column_profile(table)
        widths = _compute_column_widths(profile) if profile else None
        highlight_idx = _detect_highlight_column(header_cells, profile) if profile else None

        for i, th in enumerate(header_cells):
            is_price = bool(profile) and profile[i]["is_price"]
            width_pct = widths[i] if widths else None
            th["style"] = _cell_style(is_price, width_pct, is_header=True)

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            for cell in cells:
                cell.name = "td"
                for p in cell.find_all("p"):
                    p.unwrap()
            for i, td in enumerate(cells):
                is_price = bool(profile) and i < len(profile) and profile[i]["is_price"]
                width_pct = widths[i] if widths and i < len(widths) else None
                highlight = profile is not None and i == highlight_idx
                td["style"] = _cell_style(is_price, width_pct, highlight=highlight)


def normalize_headings(soup: BeautifulSoup):
    """
    Chuẩn hóa Heading theo đúng tiêu chuẩn Thế Giới Di Động (TGDD):
    - H2: Không bold, không chứa <strong>/<b>, gỡ sạch <span style="font-weight: 400"> hoặc unwrap <span>.
      Output mẫu: <h2>Tiêu đề H2</h2>
    - H3, H4, H5, H6: Bắt buộc bọc <strong>, gỡ sạch style font-weight:400 trên <span> bên trong
      để chữ hiển thị ĐẬM (bold) chuẩn trên CMS TGDD.
      Output mẫu: <h3><strong>Tiêu đề H3</strong></h3>
    """
    # 1. Chuẩn hóa H2 (Không bold, gỡ <span>/<strong>/<b>)
    for h2 in list(soup.find_all("h2")):
        text = h2.get_text(strip=True)
        if not text:
            h2.decompose()
            continue
        for tag in list(h2.find_all(["strong", "b", "span"])):
            tag.unwrap()

    # 2. Chuẩn hóa H3, H4, H5, H6 (Bắt buộc <strong>, gỡ <span>/font-weight:400)
    for tag_name in ["h3", "h4", "h5", "h6"]:
        for heading in list(soup.find_all(tag_name)):
            text = heading.get_text(strip=True)
            if not text:
                heading.decompose()
                continue

            for inner in list(heading.find_all(["strong", "b", "span"])):
                inner.unwrap()

            contents = list(heading.contents)
            heading.clear()
            strong_tag = soup.new_tag("strong")
            for c in contents:
                strong_tag.append(c)
            heading.append(strong_tag)




def clean_dump_images_and_empty_headings(soup: BeautifulSoup):
    """Xóa các h2/h3/h4 rỗng và tất cả các thẻ ảnh/caption cũ trước khi re-placement."""
    for h in list(soup.find_all(["h2", "h3", "h4"])):
        text = h.get_text(strip=True)
        if not text:
            h.decompose()

    for p in list(soup.find_all("p", class_="titleOfImages")):
        p.decompose()

    for img in list(soup.find_all("img")):
        parent = img.parent
        img.decompose()
        if parent and parent.name == "p" and not parent.get_text(strip=True) and not parent.find_all(True):
            parent.decompose()


def format_image_element(soup: BeautifulSoup, img_src: str, meta: dict, rule_fname: str = "") -> tuple:
    """Tạo tag <p><img .../></p> và <p class="titleOfImages">caption</p>"""
    src_fname = img_src.split("/")[-1]
    info = meta.get(rule_fname, {}) or meta.get(src_fname, {})
    alt_text = info.get("alt") or ("Hình ảnh " + src_fname)
    title_text = info.get("title") or src_fname
    caption_text = info.get("caption") or info.get("description") or info.get("title") or alt_text

    p_img = soup.new_tag("p")
    img_tag = soup.new_tag(
        "img",
        src=img_src,
        alt=alt_text,
        title=title_text,
        width="845",
        height="475"
    )
    img_tag["class"] = ""
    p_img.append(img_tag)

    p_cap = soup.new_tag(
        "p",
        attrs={"class": "titleOfImages", "style": "font-size: 15px; color: #777777; text-align: center; font-style: italic;"}
    )
    p_cap.string = caption_text
    return p_img, p_cap


def normalize_lineup_links(soup: BeautifulSoup):
    """
    1. Gỡ link lineup khỏi các đoạn văn bản thường (như trong section Lịch sử ASUS).
    2. Gắn link cho tất cả các lineup tại Cột 1 của Bảng 'Các dòng laptop ASUS hiện có tại Thế Giới Di Động'.
    """
    LINEUP_URL_MAP = {
        "vivobook": "https://www.thegioididong.com/laptop-asus-vivobook",
        "vivobook s": "https://www.thegioididong.com/laptop-asus-vivobook",
        "zenbook": "https://www.thegioididong.com/laptop-asus-zenbook",
        "tuf gaming": "https://www.thegioididong.com/laptop-asus-tuf-gaming",
        "asus gaming (v-series)": "https://www.thegioididong.com/laptop-asus-gaming-vivobook",
        "rog (republic of gamers)": "https://www.thegioididong.com/laptop-asus-rog",
        "expertbook": "https://www.thegioididong.com/laptop-asus-expertbook",
        "proart": "https://www.thegioididong.com/laptop-asus-proart",
    }

    # 1. Gỡ link lineup ở văn bản thường (ngoài table) — CHỈ khi bài thật sự có
    #    bảng lineup ASUS (cột 1 khớp LINEUP_URL_MAP). Nếu không, các link
    #    zenbook/vivobook trong <p> là link hãng/dòng hợp lệ do rule "Link hãng
    #    + dòng sản phẩm" chèn ở bài top sản phẩm khác — không được gỡ.
    has_lineup_table = any(
        row.find_all(["td", "th"]) and row.find_all(["td", "th"])[0].get_text(strip=True).lower() in LINEUP_URL_MAP
        for table in soup.find_all("table")
        for row in table.find_all("tr")[1:]
    )
    if has_lineup_table:
        for a in list(soup.find_all("a")):
            if not a.find_parent("table"):
                href = a.get("href", "").lower()
                text = a.get_text(strip=True).lower()
                if any(path in href for path in ["laptop-asus-zenbook", "laptop-asus-vivobook", "laptop-asus-rog", "laptop-asus-tuf-gaming", "laptop-asus-gaming-vivobook"]) or text in LINEUP_URL_MAP:
                    a.unwrap()

    # 2. Gắn link cho cột 1 trong Bảng
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows[1:]:  # Bỏ qua header
            cols = row.find_all(["td", "th"])
            if cols:
                c1 = cols[0]
                text = c1.get_text(strip=True)
                key = text.lower()
                if key in LINEUP_URL_MAP:
                    url = LINEUP_URL_MAP[key]
                    c1.clear()
                    a_tag = soup.new_tag("a", href=url, target="_blank", rel="noopener noreferrer")
                    a_tag.string = text
                    c1.append(a_tag)


# ─── Main Pipeline ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Optimize HTML source content for MWG content workspaces")
    parser.add_argument("--workspace", required=True, help="Path to workspace folder")
    parser.add_argument("--fetch-links", action="store_true", help="Fetch internal links from MWG Google Sheets")
    parser.add_argument("--links-json", help="Path to local links JSON file")
    parser.add_argument("--no-link-anchor", action="append", default=[],
                        help="Anchor KHONG duoc chen internal link (noi dung ngoai danh muc TGDD). "
                             "Lap duoc nhieu lan. Cong voi metadata/no-link-anchors.txt.")
    parser.add_argument("--self-url", help="URL live cua chinh bai nay, de khong chen link tro ve chinh no. "
                                           "Neu bo trong, doc tu source/article-url.txt")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    source_html_path = workspace / "source" / "source-content.html"
    self_url_path = workspace / "source" / "article-url.txt"
    metadata_csv_path = workspace / "metadata" / "image-metadata.csv"
    placement_json_path = workspace / "image-placement.json"
    cdn_urls_path = workspace / "cdn-urls.json"
    final_html_path = workspace / "source" / "final-content.html"
    links_log_path = workspace / "metadata" / "inserted-links-report.json"

    if not source_html_path.exists():
        print(f"[ERROR] source-content.html not found at {source_html_path}")
        sys.exit(1)

    print(f"[INFO] Reading {source_html_path}")
    with open(source_html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    self_url = (args.self_url or "").strip()
    if not self_url and self_url_path.exists():
        lines = [ln.strip() for ln in self_url_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self_url = lines[0] if lines else ""
    if self_url:
        print(f"[INFO] URL bai nay: {self_url} — se khong chen link tro ve chinh no")
    else:
        print("[WARN] Khong biet URL bai nay (thieu --self-url / source/article-url.txt). "
              "Link tro ve chinh bai se khong bi chan.")

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Load image metadata + URL CDN của riêng workspace
    metadata = load_image_metadata(metadata_csv_path)
    cdn_urls = load_cdn_urls(cdn_urls_path)
    if cdn_urls:
        print(f"[INFO] Loaded {len(cdn_urls)} CDN URL(s) from cdn-urls.json")
    else:
        print("[WARN] cdn-urls.json not found/empty. Ảnh sẽ dùng src trong source-content.html.")

    # 2. Extract placement rules
    placement = []
    if placement_json_path.exists():
        with open(placement_json_path, "r", encoding="utf-8") as f:
            placement = json.load(f)
        print(f"[INFO] Loaded {len(placement)} image placement rules from image-placement.json")
    else:
        print(f"[WARN] image-placement.json not found. Images will not be auto-relocated.")

    # 3. Collect dump images and clean (chỉ khi có placement rules để re-place;
    #    nếu không có image-placement.json, ảnh coi như đã đặt đúng vị trí inline
    #    trong source rồi -> không được đụng vào, tránh xóa mất ảnh không re-insert lại được)
    dump_imgs = {}
    dump_imgs_list = []
    if placement:
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src:
                fname = src.split("/")[-1]
                dump_imgs[fname] = src
                dump_imgs_list.append(src)

        clean_dump_images_and_empty_headings(soup)


    # 4. Re-insert images according to placement rules
    headings = soup.find_all(["h2", "h3", "h4"])

    for idx, rule in enumerate(placement):
        fname = rule.get("file")
        heading_text_kw = rule.get("after_heading_contains", "").lower()
        block_idx = rule.get("block_index", 1)

        img_src = (rule.get("cdn_url") or "").strip() or cdn_urls.get(fname)
        if not img_src:
            img_src = dump_imgs.get(fname)
        if not img_src and idx < len(dump_imgs_list):
            img_src = dump_imgs_list[idx]
        if not img_src:
            img_src = f"https://cdnv2.tgdd.vn/mwg-static/common/News/1581609/{fname}"

        p_img, p_cap = format_image_element(soup, img_src, metadata, rule_fname=fname)

        target_heading = None
        # 1st pass: Exact match
        for h in headings:
            h_text = h.get_text(strip=True).lower()
            if len(h_text) > 100:
                continue
            if heading_text_kw == h_text:
                target_heading = h
                break
        # 2nd pass: Substring match fallback (excluding long intro headings)
        if not target_heading:
            for h in headings:
                h_text = h.get_text(strip=True).lower()
                if len(h_text) > 100:
                    continue
                if heading_text_kw in h_text:
                    target_heading = h
                    break

        if target_heading:
            blocks = []
            curr = target_heading.next_sibling
            while curr:
                if curr.name in ["h2", "h3", "h4"]:
                    break
                if curr.name in ["p", "ul", "ol", "table"] and curr.get_text(strip=True):
                    blocks.append(curr)
                curr = curr.next_sibling

            if blocks:
                target_block = blocks[min(block_idx - 1, len(blocks) - 1)]
                target_block.insert_after(p_img)
                p_img.insert_after(p_cap)
                print(f"  [PLACED] {fname} → after block in '{target_heading.get_text(strip=True)[:40]}...'")
            else:
                target_heading.insert_after(p_img)
                p_img.insert_after(p_cap)
                print(f"  [PLACED] {fname} → directly under '{target_heading.get_text(strip=True)[:40]}...'")

    # 5. Handle Internal Linking
    ws_name = workspace.name.lower()
    if "laptop" in ws_name:
        CUSTOM_LINK_OVERRIDES = [
            {"keyword": "laptop gaming", "url": "https://www.thegioididong.com/laptop?g=laptop-gaming", "source": "CUSTOM"},
            {"keyword": "laptop học tập", "url": "https://www.thegioididong.com/laptop?g=hoc-tap-van-phong", "source": "CUSTOM"},
            {"keyword": "laptop văn phòng", "url": "https://www.thegioididong.com/laptop?g=hoc-tap-van-phong", "source": "CUSTOM"},
            {"keyword": "laptop đồ họa", "url": "https://www.thegioididong.com/laptop?g=do-hoa-ky-thuat", "source": "CUSTOM"},
            {"keyword": "asus vivobook", "url": "https://www.thegioididong.com/laptop-asus-vivobook", "source": "CUSTOM"},
            {"keyword": "asus zenbook", "url": "https://www.thegioididong.com/laptop-asus-zenbook", "source": "CUSTOM"},
            {"keyword": "asus tuf", "url": "https://www.thegioididong.com/laptop-asus-tuf-gaming", "source": "CUSTOM"},
            {"keyword": "dell inspiron", "url": "https://www.thegioididong.com/laptop-dell-inspiron", "source": "CUSTOM"},
            {"keyword": "hp victus", "url": "https://www.thegioididong.com/laptop-hp-compaq-victus", "source": "CUSTOM"},
            {"keyword": "hp omnibook 5", "url": "https://www.thegioididong.com/laptop-hp-compaq-omnibook-5", "source": "CUSTOM"},
            {"keyword": "hp omnibook x", "url": "https://www.thegioididong.com/laptop-hp-compaq-omnibook-x", "source": "CUSTOM"},
            {"keyword": "hp omnibook", "url": "https://www.thegioididong.com/laptop-hp-compaq-omnibook", "source": "CUSTOM"},
            {"keyword": "hp elitebook", "url": "https://www.thegioididong.com/laptop-hp-compaq-elitebook", "source": "CUSTOM"},
            {"keyword": "hp pavilion", "url": "https://www.thegioididong.com/laptop-hp-compaq-pavilion", "source": "CUSTOM"},
            {"keyword": "hp probook", "url": "https://www.thegioididong.com/laptop-hp-compaq-probook", "source": "CUSTOM"},
            {"keyword": "msi modern", "url": "https://www.thegioididong.com/laptop-msi-modern", "source": "CUSTOM"},
            {"keyword": "msi prestige", "url": "https://www.thegioididong.com/laptop-msi-prestige", "source": "CUSTOM"},
            {"keyword": "acer nitro", "url": "https://www.thegioididong.com/laptop-acer-nitro", "source": "CUSTOM"},
            {"keyword": "acer aspire", "url": "https://www.thegioididong.com/laptop-acer-aspire", "source": "CUSTOM"},
            {"keyword": "acer swift", "url": "https://www.thegioididong.com/laptop-acer-swift", "source": "CUSTOM"},
            {"keyword": "lenovo legion", "url": "https://www.thegioididong.com/laptop-lenovo-legion", "source": "CUSTOM"},
            {"keyword": "lenovo ideapad", "url": "https://www.thegioididong.com/laptop-lenovo-ideapad", "source": "CUSTOM"},
            {"keyword": "macbook air", "url": "https://www.thegioididong.com/laptop-apple-macbook-air", "source": "CUSTOM"},
            {"keyword": "macbook pro", "url": "https://www.thegioididong.com/laptop-apple-macbook-pro", "source": "CUSTOM"},
            {"keyword": "macbook", "url": "https://www.thegioididong.com/laptop-apple-macbook", "source": "CUSTOM"},
            {"keyword": "asus", "url": "https://www.thegioididong.com/laptop-asus", "source": "CUSTOM"},
            {"keyword": "dell", "url": "https://www.thegioididong.com/laptop-dell", "source": "CUSTOM"},
            {"keyword": "hp", "url": "https://www.thegioididong.com/laptop-hp", "source": "CUSTOM"},
            {"keyword": "msi", "url": "https://www.thegioididong.com/laptop-msi", "source": "CUSTOM"},
            {"keyword": "lenovo", "url": "https://www.thegioididong.com/laptop-lenovo", "source": "CUSTOM"},
            {"keyword": "acer", "url": "https://www.thegioididong.com/laptop-acer", "source": "CUSTOM"},
        ]
    elif "may-in" in ws_name or "printer" in ws_name or "hoa-don" in ws_name:
        CUSTOM_LINK_OVERRIDES = [
            {"keyword": "máy in nhiệt trực tiếp", "url": "https://www.thegioididong.com/may-in?g=may-in-nhiet", "source": "CUSTOM"},
            {"keyword": "máy in nhiệt", "url": "https://www.thegioididong.com/may-in?g=may-in-nhiet", "source": "CUSTOM"},
            {"keyword": "máy in kim", "url": "https://www.thegioididong.com/may-in?g=may-in-kim", "source": "CUSTOM"},
            {"keyword": "máy in hóa đơn", "url": "https://www.thegioididong.com/may-in", "source": "CUSTOM"},
            {"keyword": "máy in bill", "url": "https://www.thegioididong.com/may-in", "source": "CUSTOM"},
            {"keyword": "máy in", "url": "https://www.thegioididong.com/may-in", "source": "CUSTOM"},
            {"keyword": "canon", "url": "https://www.thegioididong.com/may-in-canon", "source": "CUSTOM"},
            {"keyword": "hp", "url": "https://www.thegioididong.com/may-in-hp", "source": "CUSTOM"},
            {"keyword": "pantum", "url": "https://www.thegioididong.com/may-in-pantum", "source": "CUSTOM"},
        ]
    else:
        CUSTOM_LINK_OVERRIDES = [
            {"keyword": "màn hình 2k", "url": "https://www.thegioididong.com/man-hinh-may-tinh-2k", "source": "CUSTOM"},
            {"keyword": "màn hình máy tính", "url": "https://www.thegioididong.com/man-hinh-may-tinh", "source": "CUSTOM"},
            {"keyword": "màn hình cong samsung", "url": "https://www.thegioididong.com/man-hinh-may-tinh-samsung", "source": "CUSTOM"},
            {"keyword": "màn hình samsung", "url": "https://www.thegioididong.com/man-hinh-may-tinh-samsung", "source": "CUSTOM"},
            {"keyword": "màn hình cong lg", "url": "https://www.thegioididong.com/man-hinh-may-tinh-lg", "source": "CUSTOM"},
            {"keyword": "màn hình lg", "url": "https://www.thegioididong.com/man-hinh-may-tinh-lg", "source": "CUSTOM"},
            {"keyword": "màn hình cong msi", "url": "https://www.thegioididong.com/man-hinh-may-tinh-msi", "source": "CUSTOM"},
            {"keyword": "màn hình msi", "url": "https://www.thegioididong.com/man-hinh-may-tinh-msi", "source": "CUSTOM"},
            {"keyword": "màn hình cong asus", "url": "https://www.thegioididong.com/man-hinh-may-tinh-asus", "source": "CUSTOM"},
            {"keyword": "màn hình asus", "url": "https://www.thegioididong.com/man-hinh-may-tinh-asus", "source": "CUSTOM"},
            {"keyword": "màn hình cong dell", "url": "https://www.thegioididong.com/man-hinh-may-tinh-dell", "source": "CUSTOM"},
            {"keyword": "màn hình dell", "url": "https://www.thegioididong.com/man-hinh-may-tinh-dell", "source": "CUSTOM"},
            {"keyword": "màn hình cong viewsonic", "url": "https://www.thegioididong.com/man-hinh-may-tinh-viewsonic", "source": "CUSTOM"},
            {"keyword": "màn hình viewsonic", "url": "https://www.thegioididong.com/man-hinh-may-tinh-viewsonic", "source": "CUSTOM"},
            {"keyword": "màn hình cong hp", "url": "https://www.thegioididong.com/man-hinh-may-tinh-hp", "source": "CUSTOM"},
            {"keyword": "màn hình hp", "url": "https://www.thegioididong.com/man-hinh-may-tinh-hp", "source": "CUSTOM"},
            {"keyword": "màn hình cong lenovo", "url": "https://www.thegioididong.com/man-hinh-may-tinh-lenovo", "source": "CUSTOM"},
            {"keyword": "màn hình lenovo", "url": "https://www.thegioididong.com/man-hinh-may-tinh-lenovo", "source": "CUSTOM"},
            {"keyword": "màn hình cong acer", "url": "https://www.thegioididong.com/man-hinh-may-tinh-acer", "source": "CUSTOM"},
            {"keyword": "màn hình acer", "url": "https://www.thegioididong.com/man-hinh-may-tinh-acer", "source": "CUSTOM"},
            {"keyword": "màn hình cong", "url": "https://www.thegioididong.com/man-hinh-may-tinh-man-hinh-cong", "source": "CUSTOM"},
            {"keyword": "màn hình", "url": "https://www.thegioididong.com/man-hinh-may-tinh", "source": "CUSTOM"},
            {"keyword": "pc gaming", "url": "https://www.thegioididong.com/may-tinh-de-ban-pc-gaming", "source": "CUSTOM"},
            {"keyword": "máy tính để bàn", "url": "https://www.thegioididong.com/may-tinh-de-ban", "source": "CUSTOM"},
        ]

    internal_links = []
    if args.links_json and Path(args.links_json).exists():
        with open(args.links_json, "r", encoding="utf-8") as f:
            internal_links = json.load(f)
        print(f"[INFO] Loaded {len(internal_links)} links from {args.links_json}")
    elif args.fetch_links:
        internal_links = load_internal_links_from_sheets()

    # Prepend custom overrides and filter sheet list
    override_kws = {item["keyword"].lower() for item in CUSTOM_LINK_OVERRIDES}
    if "man-hinh" in ws_name or "monitor" in ws_name or "screen" in ws_name:
        FORBIDDEN_BARE_BRANDS = {"samsung", "lg", "msi", "asus", "dell", "hp", "lenovo", "acer", "viewsonic", "apple"}
        filtered_links = [
            item for item in internal_links
            if item["keyword"].lower() not in override_kws and item["keyword"].lower() not in FORBIDDEN_BARE_BRANDS
        ]
    elif "laptop" in ws_name:
        # Bài laptop: "màn hình 15.6 inch", "màn hình 16 inch" là tấm nền tích hợp
        # của máy, không phải màn hình rời để mua thêm. Link sang category
        # man-hinh-may-tinh luôn lệch ngữ cảnh nên loại ngay từ nguồn. Bài
        # /hoi-dap/ giải thích khái niệm (tần số quét, tấm nền) thì vẫn giữ.
        filtered_links = [
            item for item in internal_links
            if item["keyword"].lower() not in override_kws
            and not (
                "man-hinh-may-tinh" in item["url"] and "/hoi-dap/" not in item["url"]
            )
        ]
    else:
        filtered_links = [item for item in internal_links if item["keyword"].lower() not in override_kws]

    internal_links = CUSTOM_LINK_OVERRIDES + filtered_links

    no_link_anchors = load_no_link_anchors(workspace, args.no_link_anchor)
    if no_link_anchors:
        before = len(internal_links)
        internal_links = filter_no_link_anchors(internal_links, no_link_anchors)
        print(f"[INFO] no-link-anchor: {len(no_link_anchors)} anchor loai tru, "
              f"bo {before - len(internal_links)} link.")

    internal_links.sort(key=lambda x: len(x["keyword"]), reverse=True)

    inserted_report = []
    if internal_links:
        print("[INFO] Processing internal link insertion...")
        inserted_report = insert_internal_links(soup, internal_links, self_url=self_url)
        print(f"[DONE] Inserted {len(inserted_report)} internal links into HTML.")

        # Save inserted links log for review
        links_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(links_log_path, "w", encoding="utf-8") as f:
            json.dump(inserted_report, f, ensure_ascii=False, indent=2)
        print(f"[REPORT] Inserted links log saved to {links_log_path}")

    # 6. Normalize tables, lineup links & headings
    normalize_tables(soup)
    normalize_lineup_links(soup)
    normalize_headings(soup)

    # 6.2 Box "Xem thêm": anchor phải là full tiêu đề bài liên quan
    related_result = normalize_related_article_links(soup)
    for record in related_result["expanded"]:
        print(f"  [XEM THÊM] anchor '{record['anchor_before'][:40]}...' → full tiêu đề ({record['url']})")
        for dropped in record["dropped_urls"]:
            print(f"      [WARN] bỏ link phụ trong cùng dòng, kiểm lại nếu cần: {dropped}")
    if related_result["expanded"]:
        print(f"[DONE] Nới {len(related_result['expanded'])} anchor box 'Xem thêm' thành full tiêu đề.")
    for warning in related_result["warnings"]:
        print(f"  [WARN] {warning}")

    # 6.5 Ensure all <a> tags have target="_blank" and rel="noopener noreferrer"
    for a in soup.find_all("a"):
        a["target"] = "_blank"
        a["rel"] = "noopener noreferrer"

    # 7. Save output
    final_html_path.parent.mkdir(parents=True, exist_ok=True)
    with open(final_html_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"\n[DONE] Optimized HTML written to {final_html_path}")


if __name__ == "__main__":
    main()
