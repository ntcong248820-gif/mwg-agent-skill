#!/usr/bin/env python3
"""Rule phân loại keyword theo dạng trang. Verdict: keep | review | drop.

Nguyên tắc (chi tiết + bằng chứng: references/keyword-rules.md):
- sp   : keyword phải ĐỊNH DANH được đúng sản phẩm (mã model, hoặc hãng + tên dòng). Volume không dùng để loại.
- hang : bộ lọc intent nghiêm ngặt.
- nh / dong (filter): thuộc tính của filter là từ BẮT BUỘC, không bao giờ bị loại
  (filter "oled" thì `oled` được giữ). Chỉ loại thông số KHÁC filter, mã SKU, intent blog.
- review = mơ hồ, cần người xem; chỉ `keep` nên được đưa vào danh sách cuối.
"""
from __future__ import annotations

import re

U = r"(?:hz|ghz|mhz|gb|tb|mb|mah|mp|w|wh|v|inch|in|mm|cm|ml|l|kg|g|k|nits|rpm|ms|fps|ah|db|lm|btu|hp)"
UNIT = re.compile(rf"^\d+(?:[.,]\d+)?{U}$")
SPEC_PREFIX = re.compile(  # token thông số/tên dòng, KHÔNG phải mã SKU (khớp nguyên token để m6702dw không bị nhầm với chip m3)
    r"^(?:(?:rtx|gtx|rx|arc)\d*|i[3579](?:-\w+)?|ryzen\w*|core\w*|ultra\w*|m[1-9](?:pro|max|ultra)?|snapdragon\w*|"
    r"gen\d+|usb\w*|hdmi\w*|wifi\d*|iphon\w*|ipad\w*|galaxy\w*|airpod\w*|macbook\w*|imac\w*|watch\w*)$")
INTENT = re.compile(
    r"(?<!\w)(review|đánh giá|danh gia|so sánh|so sanh|vs|versus|specs?|specification|thông số|hướng dẫn|cách(?!\s*(?:âm|nhiệt|điện))|"
    r"how to|là gì|của nước nào|có tốt không|tốt không|driver|tải|download|cài đặt|firmware|lỗi|sửa chữa|"
    r"reset|mực in|hộp mực|đổ mực|crack|wiki|reddit|youtube|tin tức|release date|ngày ra mắt|notebookcheck|"
    r"hdsd|thay pin|thay màn hình|hình ảnh|hình nền|wallpaper|các loại|video|test|screen|refresh|rate)(?!\w)|"
    r"^(?:các|độ phân giải) |"
    r"(?<!chụp )(?<!máy )(?<!phim )(?<!film )(?<!in )(?<!\w)ảnh(?!\w)")
INFO_DROP = re.compile(  # tầng 1: hỏi/tư vấn/sự cố -> người tìm không đang mua
    r"(?<!\w)(nên mua|nên chọn|đáng mua|đáng tiền|có nên|loại nào|nào tốt|nào ngon|nào bền|ưu nhược|ưu điểm|nhược điểm|"
    r"kinh nghiệm|mẹo|tư vấn|xuất xứ|bảo hành bao lâu|có bền|bền không|ổn không|được không|có tốt|"
    r"bị nóng|bị đơ|bị treo|bị lag|hay bị|không lên|không nhận|nâng cấp)(?!\w)")
INFO_REVIEW = re.compile(  # tầng 2: mơ hồ (có thể là intent mua hoặc đọc) -> để người xem, không tự ghi
    r"(?<!giá )(?<!\w)(top|best|mới nhất|ra mắt|tốt nhất|tốt|phù hợp)(?!\w)")  # "giá tốt" là intent mua, không vào đây
OUT_OF_PATTERN = re.compile(  # dạng hiếm gặp ở keyword hợp lệ -> để người xem
    r"(?<!\w)(cũ|second hand|secondhand|ngày xưa|retro|tiếng anh|english|best|top|gần đây|gần tôi|near me|"
    r"đà nẵng|cần thơ|hà nội|hải phòng|sài gòn|hcm|tphcm|biên hòa|huế|nha trang|vũng tàu|đà lạt|quận \d+)(?!\w)")
RETAILER = re.compile(  # không lấy tên brand nhà bán lẻ làm keyword
    r"(?<!\w)(thegioididong|thế giới di động|the gioi di dong|tgdd|tgdđ|dienmayxanh|điện máy xanh|dien may xanh|dmx|"
    r"fpt ?shop|cellphones?|hoàng hà mobile|phong vũ|nguyễn kim|nguyen kim|mediamart|hacom|gearvn|an phát|"
    r"topzone|shopee|lazada|tiki)(?!\w)")
NO_DIACRITIC_VI = re.compile(  # cụm tiếng Việt viết thiếu dấu (keyword tiếng Việt nên có dấu)
    r"(?<!\w)(man hinh|may tinh|may choi|choi game|cam tay|tay cam|dien thoai|gia re|ban phim|may in|"
    r"may anh|may xach|chinh hang|do phan giai|may chieu|loa may tinh)(?!\w)")
# Chỉ áp cho trang filter ngành hàng: từ trỏ riêng tới 1 hãng/dòng/nền tảng -> thuộc trang hãng/dòng, không phải filter.
FILTER_ENTITIES = {"rog", "omen", "legion", "thinkpad", "predator", "nitro", "tuf", "alienware", "kuycon", "nintendo", "switch",
                   "ps5", "ps4", "playstation", "xbox", "steam", "ally", "claw", "android", "ideapad", "vivobook", "zenbook",
                   "inspiron", "pavilion", "macbook", "surface"}
OTHER_CATEGORY = re.compile(  # keyword MỞ ĐẦU bằng ngành hàng khác (chỉ vị trí đầu: 'màn hình di động cho laptop' vẫn hợp lệ) (vd "laptop màn hình 8k" ở filter của màn hình máy tính)
    r"^(laptop|điện thoại|tivi|máy tính bảng|máy in|tai nghe|đồng hồ|loa|tủ lạnh|máy lạnh|máy giặt)(?!\w)")
PRICE_SEGMENT = re.compile(r"(?<!\w)(?:giá|rẻ|dưới|trên|từ|khoảng|tầm)\s*(?:rẻ\s*)?\d+(?:[.,]\d+)?\s*(?:k|tr|triệu|nghìn|ngàn|củ)(?!\w)")
SERIES_SEGMENT = re.compile(r"(?<!\w)(?:\d{3,5}\s*series|series)(?!\w)")
YEAR = re.compile(r"(?<!\d)(20(?:1[5-9]|2\d))(?!\d)")
BRANDS = {"dell", "hp", "asus", "acer", "lenovo", "msi", "apple", "macbook", "imac", "iphone", "ipad", "samsung",
          "galaxy", "lg", "sony", "xiaomi", "huawei", "oppo", "vivo", "realme", "honor", "gigabyte", "razer",
          "microsoft", "surface", "canon", "epson", "brother", "pantum", "viewsonic", "benq", "aoc", "philips",
          "logitech", "dareu", "rapoo", "corsair", "garmin", "casio", "nokia", "tecno", "infinix", "jbl", "anker"}
ALIAS = [{"apple", "macbook", "imac", "iphone", "ipad", "airpods", "mac"}, {"samsung", "galaxy"}, {"microsoft", "surface"}]
GENERIC = {"laptop", "máy", "tính", "màn", "hình", "điện", "thoại", "và", "cho", "của", "series", "gaming", "chính",
           "hãng", "giá", "mua", "the", "with", "va", "de", "ban", "bàn", "in", "để"}
HANG_SUBLINEUP = {"flip", "aero", "go", "pro", "360", "fli"}
SPEC_RES = [
    r"(?<!\w)(?:oled|amoled|qled|ips|va|tn|miniled|mini-led|[2-8]k|uhd|qhd|fhd|wqhd)(?!\w)",
    r"(?<!\d)\d{2,3}\s?hz", r"(?<!\d)\d{2}(?:[.,]\d)?\s?(?:inch|in\b|\")",
    r"(?<!\w)(?:i[3579]|ryzen\s?\d?|core\s?(?:ultra\s?)?\d|intel|amd|snapdragon|m[1-5](?:\s?(?:pro|max|ultra))?)(?!\w)",
    r"(?<!\d)\d+\s?(?:gb|tb)(?!\w)", r"(?<!\w)(?:rtx|gtx|rx)\s?\d{3,4}"]


def strip_diacritics(text: str) -> str:
    import unicodedata
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def has_diacritics(text: str) -> bool:
    return strip_diacritics(text) != text


def normalize(kw: str) -> str:
    kw = re.sub(r"[:,\-_+\s.]+$", "", str(kw).lower().strip())
    return re.sub(r"\s+", " ", kw)


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[^\W_]+", normalize(text)))


def ws_tokens(text: str) -> set[str]:
    return {t.strip("()[]\"',") for t in normalize(text).replace("/", " ").split()}


def sub_tokens(text: str) -> set[str]:
    """Tách chữ/số (fold8 -> fold, 8) để so tên ngắn với tên đầy đủ; bỏ từ chung chung."""
    return {p for t in tokens(text) for p in re.findall(r"[a-z]+|\d+", t) if t not in GENERIC and p not in GENERIC}


def code_like(t: str, strict: bool = False) -> bool:
    if not re.fullmatch(r"[a-z0-9][a-z0-9\-/.]{3,}", t) or UNIT.match(t) or SPEC_PREFIX.match(t):
        return False
    letters, digits = len(re.findall(r"[a-z]", t)), len(re.findall(r"\d", t))
    if strict:  # mã model cụ thể: p2200, m6702dw, g27c4x, 83jc007hvn (1 chữ + >=3 số, hoặc >=2 chữ + >=2 số)
        return len(t) >= 5 and ((letters >= 1 and digits >= 3) or (letters >= 2 and digits >= 2))
    return bool(letters and digits)


def spec_set(text: str) -> set[str]:
    t = normalize(text)
    return {re.sub(r"\s", "", m.group(0)) for p in SPEC_RES for m in re.finditer(p, t)}


def ctx_text(ctx: dict) -> str:
    return " ".join(str(ctx.get(k, "")) for k in ("name", "nganh", "hang", "filter", "url")).replace("-", " ")


def own_codes(ctx: dict) -> set[str]:
    src = ctx_text(ctx) + " " + str(ctx.get("url", ""))
    cand = ws_tokens(src) | set(re.findall(r"[a-z0-9]+", normalize(src)))
    return {t for t in cand if len(t) >= 4 and re.search(r"\d", t) and re.search(r"[a-z]", t)}


def brand_allowed(b: str, ctx_tokens: set[str]) -> bool:
    return b in ctx_tokens or any(b in g and g & ctx_tokens for g in ALIAS)


def classify(kw: str, ctx: dict) -> tuple[str, str]:
    kw = normalize(kw)
    kind, ctx_t = ctx["type"], tokens(ctx_text(ctx))
    kw_t = ws_tokens(kw)
    if len(kw) < 3:
        return "drop", "quá ngắn"
    if INTENT.search(kw):
        return "drop", "intent blog/review/hỗ trợ"
    if INFO_DROP.search(kw):
        return "drop", "intent hỏi/tư vấn/sự cố (blog)"
    if RETAILER.search(kw):
        return "drop", "tên nhà bán lẻ"
    if not has_diacritics(kw) and NO_DIACRITIC_VI.search(kw):
        return "drop", "tiếng Việt thiếu dấu"
    if YEAR.search(kw) and kind == "hang" and not YEAR.search(ctx_text(ctx)):
        return "drop", "năm (xu hướng/tin tức)"
    off = [b for b in kw_t & BRANDS if not brand_allowed(b, ctx_t)]
    if off and kind == "hang":
        return "drop", f"khác hãng: {off[0]}"
    if off and ctx_t & BRANDS:          # trang đã gắn một hãng khác -> loại
        return "drop", f"khác hãng: {off[0]}"
    if off and kind != "sp":            # filter ngành hàng không gắn hãng: keyword trỏ một hãng thuộc trang hãng
        return "drop", f"trỏ riêng một hãng ({off[0]}) — thuộc trang hãng"
    if kind == "sp":
        verdict = _sp(kw, kw_t, ctx)
    elif kind == "hang":
        verdict = _hang(kw, kw_t, ctx, ctx_t)
    else:
        verdict = _filter(kw, kw_t, ctx, ctx_t)
    if verdict[0] == "keep" and INFO_REVIEW.search(kw) and not INFO_REVIEW.search(ctx_text(ctx)):
        return "review", "từ mơ hồ giữa mua và đọc (top/best/tốt/mới nhất...)"
    return verdict


def _sp(kw: str, kw_t: set[str], ctx: dict) -> tuple[str, str]:
    codes = own_codes(ctx)
    kw_codes = {t for t in kw_t | set(re.findall(r"[a-z0-9]+", kw)) if code_like(t)}
    model = sub_tokens(ctx.get("name", "") + " " + ctx.get("url", ""))
    foreign = {c for c in kw_codes if c not in codes and not any(c in o or o in c for o in codes)
               and not sub_tokens(c) <= model}
    if foreign:
        return "drop", f"mã SKU khác sản phẩm: {sorted(foreign)[0]}"
    if len(kw.split()) > 6 and len(spec_set(kw)) >= 2:
        return "drop", "câu dài kèm thông số"
    overlap = sub_tokens(kw) & model
    if kw_codes & codes or len(overlap) >= 2:
        return "keep", "định danh được sản phẩm"
    return ("review", "chưa đủ định danh sản phẩm") if kw_codes or overlap else ("drop", "không liên quan sản phẩm")


def _hang(kw: str, kw_t: set[str], ctx: dict, ctx_t: set[str]) -> tuple[str, str]:
    if code_like_any(kw_t, ctx_t):
        return "drop", "mã model cụ thể (thuộc trang SP)"
    if spec_set(kw) - spec_set(ctx_text(ctx)) or (kw_t & HANG_SUBLINEUP) - ctx_t:
        return "drop", "dòng con/thông số chi tiết"
    brand = tokens(ctx.get("hang", "")) - GENERIC
    if brand and not brand <= set(re.findall(r"[^\W_]+", kw)):
        return "review", "không chứa tên hãng"
    return "keep", "tên hãng/ngành + ý định mua"


def _filter(kw: str, kw_t: set[str], ctx: dict, ctx_t: set[str]) -> tuple[str, str]:
    ent = sorted((kw_t & FILTER_ENTITIES) - ctx_t)
    if ent:
        return "drop", f"trỏ riêng một dòng/hãng/nền tảng ({ent[0]}) — thuộc trang khác"
    ct = ctx_text(ctx)
    other = [m for m in OTHER_CATEGORY.findall(kw) if m not in ct]
    if other:
        return "drop", f"thuộc ngành hàng khác ({other[0]})"
    if PRICE_SEGMENT.search(kw) and not PRICE_SEGMENT.search(ct) and "giá" not in ct:
        return "drop", "phân khúc giá chi tiết hơn filter"
    if SERIES_SEGMENT.search(kw) and not SERIES_SEGMENT.search(ct):
        return "drop", "phân khúc dòng/series chi tiết hơn filter"
    if code_like_any(kw_t, ctx_t):
        return "drop", "mã model cụ thể (thuộc trang SP)"
    extra = spec_set(kw) - spec_set(ctx_text(ctx))
    own = spec_set(ctx_text(ctx))
    for e in extra:                     # ryzen5 trong filter ryzen3: cùng họ, khác số -> thuộc filter khác
        fam = re.match(r"[a-z]+", e)
        for o in own:
            if fam and o.startswith(fam.group(0)) and not o.startswith(e) and not e.startswith(o) \
                    and re.sub(r"\D", "", e) and re.sub(r"\D", "", o):
                return "drop", f"thuộc filter khác ({e} ≠ {o})"
    if OUT_OF_PATTERN.search(kw):
        return "review", "dạng chưa từng được duyệt (cũ/địa danh/best/top/tiếng Anh)"
    need = [t for t in tokens(ctx.get("filter", "")) if t not in GENERIC and (len(t) > 1 or t.isdigit())]
    flat = kw.replace(" ", "")
    if need and not any(t in flat for t in need):
        return "review", "không chứa thuộc tính của filter"
    if extra:
        return "review", f"thông số khác filter: {sorted(extra)[0]}"
    return "keep", "khớp filter"


def code_like_any(kw_t: set[str], ctx_t: set[str]) -> bool:
    return any(code_like(t, strict=True) and t not in ctx_t for t in kw_t)


def dedupe(items: list[dict]) -> list[dict]:
    seen, out = set(), []
    for it in items:
        key = normalize(it["keyword"])
        if key not in seen:
            seen.add(key)
            out.append({**it, "keyword": key})
    return out
