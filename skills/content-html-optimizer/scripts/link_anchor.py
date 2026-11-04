#!/usr/bin/env python3
"""Rule "anchor phải trọn nghĩa" — dùng chung cho optimizer và QC.

Reviewer MWG 29/09/2026 bắt mẫu "laptop [HP]", "laptop [Lenovo]", "màn hình
[OLED]": link chỉ bọc tên hãng/tên công nghệ, để lại danh từ đầu cụm nằm trần
ngay trước. Anchor như vậy cắt nghĩa của cụm — "laptop HP" là một vật, "HP" một
mình là cái khác.

`optimize_content.py` dùng để NỚI anchor lúc chèn; `check_internal_links.py` và
`validate_article.py` dùng để BẮT anchor viết tay còn sót.
"""
import re

# Danh từ đầu cụm: từ đứng trước tên hãng/công nghệ và là một phần nghĩa của cụm.
# Khác BRAND_CONTEXT_WORDS trong optimizer: danh sách kia trả lời "câu có đang
# nói về hãng không" nên gồm cả giới từ ("của", "từ") — không dùng để nới anchor,
# vì "<a>của HP</a>" là anchor sai ngữ pháp.
ANCHOR_HEAD_NOUNS = (
    "màn hình máy tính", "máy tính để bàn", "máy tính bảng", "card màn hình",
    "card đồ họa", "card đồ hoạ", "màn hình", "máy tính", "máy in", "laptop",
    "thương hiệu", "tấm nền", "ổ cứng", "bàn phím", "cảm biến", "chuột",
    "hãng", "card", "chip", "cpu", "gpu", "ram", "pin",
)
_HEAD_NOUN_SET = {n.lower() for n in ANCHOR_HEAD_NOUNS}
_BY_LENGTH = tuple(sorted(ANCHOR_HEAD_NOUNS, key=len, reverse=True))


def is_single_latin_token(text: str) -> bool:
    """True khi text là MỘT token latin trần: tên hãng ('hp') hoặc tên công nghệ
    ('oled', 'ips', 'ssd').

    Chỉ loại này mới cần nới/bị bắt. Anchor nhiều chữ đã tự trọn nghĩa — "dòng
    <a>Acer Aspire</a>" là tên dòng đầy đủ, reviewer xác nhận KHÔNG phải lỗi.
    Chính danh từ đầu cụm cũng bị loại, nếu không thì "màn hình laptop" sẽ được
    nới rồi trỏ về /laptop — đổi nghĩa cụm.
    """
    text = (text or "").strip()
    if " " in text or text.lower() in _HEAD_NOUN_SET:
        return False
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9+\-]*", text))


def head_noun_span_before(before_text: str):
    """Trả (vị_trí_bắt_đầu, chữ_nguyên_văn) của danh từ đầu cụm đứng sát anchor,
    hoặc None. Giữ nguyên hoa/thường của bài — anchor là chữ trong bài, không
    phải chữ trong danh sách."""
    if not re.search(r"[ \t ]$", before_text or ""):
        return None
    stem = before_text[:-1]
    low = stem.lower()
    for noun in _BY_LENGTH:
        if not low.endswith(noun):
            continue
        start = len(stem) - len(noun)
        if start > 0 and re.match(r"[\w]", stem[start - 1], re.UNICODE):
            continue  # dính vào chữ khác, không phải ranh giới từ
        return start, before_text[start:]
    return None


def ends_with_head_noun(text: str) -> bool:
    """True khi đoạn text kết thúc bằng một danh từ đầu cụm (đã chuẩn hoá khoảng
    trắng). Dùng để biết danh từ đó có nằm trong một link khác hay không."""
    tail = re.sub(r"\s+", " ", (text or "").lower()).strip()
    return any(tail.endswith(n) for n in ANCHOR_HEAD_NOUNS)


def partial_phrase_anchor(anchor: str, before_text: str):
    """Trả cụm đầy đủ đáng lẽ phải bọc ("laptop HP"), hoặc None nếu anchor ổn."""
    if not is_single_latin_token(anchor):
        return None
    span = head_noun_span_before(before_text)
    if not span:
        return None
    return f"{span[1].strip()} {anchor.strip()}"
