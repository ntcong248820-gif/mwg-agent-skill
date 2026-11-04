"""Suy ngành hàng của bài và của trang đích link, dùng chung cho optimizer và gate.

Nguồn duy nhất là `references/link-category-map.json`. Optimizer dùng để KHÔNG
chèn link sang ngành sản phẩm khác; `check_internal_links.py` dùng để gắn cờ B4.
Hai bên phải cùng một cách hiểu, nên logic nằm ở đây chứ không chép hai nơi.
"""
import json
import re
from pathlib import Path

MAP_FILE = Path(__file__).resolve().parent.parent / "references" / "link-category-map.json"

UNKNOWN = "khong-ro"
NEUTRAL = "trung-tinh"
# Ngành phụ kiện: lệch ngành nhưng nhiều khi là lời mời mua thật (chuột cho máy
# bàn, balo cho laptop), nên optimizer không tự bỏ — để gate gắn cờ cho người đọc câu.
ACCESSORY = "phu-kien"


def load_map():
    return json.loads(MAP_FILE.read_text(encoding="utf-8"))


def path_of(url):
    p = re.sub(r"^https?://[^/]+", "", url.split("?")[0].split("#")[0])
    return p.strip("/")


def first_segment(url):
    p = path_of(url)
    return p.split("/")[0] if p else ""


def _prefix_hit(seg, prefix):
    return seg == prefix or seg.startswith(prefix + "-")


def nganh_of_url(url, cfg):
    """Ngành của trang đích. Khớp prefix dài nhất: 'laptop-acer-aspire' -> laptop."""
    seg = first_segment(url)
    if seg in cfg["trung_tinh"]:
        return NEUTRAL
    best = None
    for ng, prefixes in cfg["nganh_hang"].items():
        for p in prefixes:
            if _prefix_hit(seg, p) and (best is None or len(p) > len(best[0])):
                best = (p, ng)
    return best[1] if best else UNKNOWN


def article_nganh(workspace_name, self_url, cfg):
    """(ngành, segment URL) của chính bài.

    Ưu tiên URL bài (`article-url.txt`): trang danh mục nói thẳng bài thuộc ngành
    nào, không phải đoán theo tên thư mục. Bài hỏi đáp/tin tức có URL trung tính
    thì rơi về map theo tên workspace.
    """
    if self_url:
        ng = nganh_of_url(self_url, cfg)
        if ng not in (NEUTRAL, UNKNOWN):
            return ng, first_segment(self_url)
    for prefix, ng in cfg["nganh_theo_slug"].items():
        if workspace_name.startswith(prefix):
            return ng, ""
    return UNKNOWN, ""


def allowed_cross(cfg, nganh, article_seg):
    """Prefix đích lệch ngành nhưng hợp lệ cho bài này.

    Key cụ thể theo URL bài thắng key theo ngành: máy bàn thùng cần màn hình rời,
    còn máy AIO có sẵn màn hình nên không được hưởng mục đó.
    """
    table = {k: v for k, v in cfg.get("phu_kien_hop_le", {}).items() if not k.startswith("_")}
    best = None
    for key in table:
        if article_seg and _prefix_hit(article_seg, key) and (best is None or len(key) > len(best)):
            best = key
    if best is None:
        best = nganh
    return table.get(best, [])


def scoped_to_other(url, nganh, cfg):
    """Ngành X nếu đích là phụ kiện dành riêng cho X ('loa-laptop' -> laptop).

    Anchor chung ('loa') trong bài máy bàn mà trỏ về loa laptop là sai vật, dù
    phụ kiện 'loa' nói chung có thể hợp lệ — nên whitelist không cứu ca này.
    """
    seg = first_segment(url)
    for ng, prefixes in cfg["nganh_hang"].items():
        if ng in (nganh, ACCESSORY):
            continue
        if any(seg != p and seg.endswith("-" + p) for p in prefixes):
            return ng
    return None


def is_cross(url, nganh, article_seg, cfg):
    """Ngành đích lệch ngành bài, trả về ngành đích; không lệch thì None."""
    if nganh == UNKNOWN:
        return None
    scoped = scoped_to_other(url, nganh, cfg)
    if scoped:
        return scoped
    dest = nganh_of_url(url, cfg)
    if dest in (NEUTRAL, UNKNOWN, nganh):
        return None
    seg = first_segment(url)
    if any(_prefix_hit(seg, p) for p in allowed_cross(cfg, nganh, article_seg)):
        return None
    return dest


def optimizer_skip_reason(keyword, url, nganh, article_seg, cfg, bare_brands):
    """Lý do optimizer KHÔNG chèn link này, hoặc None.

    Chỉ 2 ca chắc chắn sai vật. Link sang ngành sản phẩm khác theo nghĩa thường
    ('khác với laptop', 'đồng bộ với iPhone') vẫn chèn — đúng hay sai phụ thuộc
    câu, việc đó của gate B4 + người review, không phải của máy.
    """
    if not is_cross(url, nganh, article_seg, cfg):
        return None
    if keyword.strip().lower() in bare_brands:
        return "hang-tran-lech-nganh"
    if scoped_to_other(url, nganh, cfg):
        return "phu-kien-rieng-nganh-khac"
    return None
