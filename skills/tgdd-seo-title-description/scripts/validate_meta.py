#!/usr/bin/env python3
"""Validate Vietnamese SEO Title and Meta Description for TGDĐ workflows."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass


TITLE_MIN = 50
TITLE_MAX = 60
DESC_MIN = 150
DESC_MAX = 160

EVERGREEN_POLICY_PATTERNS = (
    r"trả\s+góp\s*0%",
    r"góp\s*0%",
    r"1\s*đổi\s*1",
    r"hư\s+gì\s+đổi\s+nấy",
    r"bảo\s+hành(?:\s+chính\s+hãng)?(?:\s+\d+\s*(?:tháng|năm))?",
    r"thu\s+cũ\s+đổi\s+mới",
    r"giao\s+nhanh",
)

EVERGREEN_TECH_PATTERNS = (
    r"\b(?:cpu|gpu|ram|ssd|oled|miniled|mini-led|ips|va|amoled|qled|rtx|gtx|ryzen|intel|amd|snapdragon|core\s+ultra|core\s+[3579]|apple\s+m\d|wifi|wi-fi|bluetooth|usb|hdmi|thunderbolt|ai)\b",
    r"\b\d+(?:[.,]\d+)?\s*(?:hz|khz|mhz|ghz|gb|tb|mb|inch|w|mah|tops)\b",
    r"\b(?:full\s*hd|2k|3k|4k|5k|8k|wqxga|qhd|uhd)\b",
    r"\bchip\b",
)

def has_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

# Common Vietnamese/function words and generic SEO glue that should not trigger
# repeated-word warnings by themselves.
REPEAT_STOPWORDS = {
    "các", "cho", "có", "của", "và", "với", "phù", "hợp", "mua", "nhiều",
    "được", "hỗ", "trợ", "theo", "đến", "từ", "trong", "khi", "giúp", "dùng",
    "sản", "phẩm", "chính", "hãng", "giá", "tốt", "trả", "góp", "không", "một",
    "nhu", "cầu", "lựa", "chọn", "thiết", "kế", "hiệu", "năng", "laptop", "máy",
    "tính", "màn", "hình", "điện", "thoại", "tivi", "tai", "nghe",
}


@dataclass
class ValidationResult:
    title_length: int
    description_length: int
    errors: list[str]
    warnings: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip())


def normalize_for_prefix(text: str) -> str:
    text = normalize(text).lower()
    text = re.sub(r"\s+", " ", text)
    return text


def has_valid_description_start(description: str, page_name: str) -> bool:
    """Require Description to start with `Mua <page name>` or `<page name>`."""
    desc = normalize_for_prefix(description)
    entity = normalize_for_prefix(page_name)
    if not entity:
        return False

    for prefix in (f"mua {entity}", entity):
        if desc == prefix:
            return True
        if desc.startswith(prefix) and desc[len(prefix):len(prefix) + 1] in {" ", ",", ".", "("}:
            return True
    return False


def normalized_words(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text.lower())
    return re.findall(r"[0-9a-zà-ỹ]+", text, flags=re.IGNORECASE)


def has_nonzero_percentage(text: str) -> bool:
    """Detect likely promotional non-zero percentages, excluding technical color-gamut percentages."""
    for match in re.finditer(r"\b\d+(?:[.,]\d+)?\s*%", text):
        value = match.group(0).replace(" ", "")
        if value.startswith("0%"):
            continue
        context = text[match.start(): match.end() + 24].lower()
        if re.search(r"%\s*(?:srgb|dci[- ]?p3|ntsc|adobe\s*rgb|adobergb|display\s*p3)\b", context):
            continue
        return True
    return False


def has_invalid_hyphen(title: str) -> bool:
    """Allow hyphens only when they connect two numeric range endpoints."""
    without_numeric_ranges = re.sub(r"(?<=\d)\s*-\s*(?=\d)", "", title)
    return "-" in without_numeric_ranges


def repeated_content_words(description: str) -> list[tuple[str, int]]:
    counts = Counter(
        word
        for word in normalized_words(description)
        if len(word) >= 4 and word not in REPEAT_STOPWORDS and not word.isdigit()
    )
    return sorted(
        ((word, count) for word, count in counts.items() if count >= 3),
        key=lambda item: (-item[1], item[0]),
    )


def repeated_long_phrases(title: str, description: str) -> list[str]:
    """Find exact 3-word phrases repeated from Title into Description.

    This is intentionally conservative. Semantic overlap still requires a manual
    information-budget check in SKILL.md.
    """
    title_words = normalized_words(title)
    desc_words = normalized_words(description)
    title_ngrams = {
        tuple(title_words[i : i + 3])
        for i in range(max(0, len(title_words) - 2))
    }
    desc_ngrams = {
        tuple(desc_words[i : i + 3])
        for i in range(max(0, len(desc_words) - 2))
    }
    overlaps = title_ngrams & desc_ngrams
    # Ignore a few generic transactional trigrams; they are handled elsewhere.
    ignored = {
        ("trả", "góp", "0"),
        ("bảo", "hành", "chính"),
    }
    phrases = [" ".join(ngram) for ngram in overlaps if ngram not in ignored]
    return sorted(phrases)


def validate(title: str, description: str, mode: str, page_name: str) -> ValidationResult:
    title = normalize(title)
    description = normalize(description)
    errors: list[str] = []
    warnings: list[str] = []

    title_len = len(title)
    desc_len = len(description)

    if not TITLE_MIN <= title_len <= TITLE_MAX:
        errors.append(f"Title phải dài {TITLE_MIN}-{TITLE_MAX} ký tự, hiện có {title_len}.")
    if not DESC_MIN <= desc_len <= DESC_MAX:
        errors.append(f"Description phải dài {DESC_MIN}-{DESC_MAX} ký tự, hiện có {desc_len}.")

    forbidden = [char for char in (";", ":") if char in title]
    if forbidden:
        errors.append("Title chứa dấu cấm: " + ", ".join(forbidden))
    if has_invalid_hyphen(title):
        errors.append("Title chỉ được dùng dấu - cho khoảng số liệu có số ở cả hai phía, ví dụ 24 - 49 inch.")
    if title.count("|") > 1:
        errors.append("Title chỉ được dùng tối đa một dấu |.")

    if re.search(r"\bkhám\s+phá\b", f"{title} {description}", flags=re.IGNORECASE):
        errors.append("Không dùng `Khám phá` trong Title/Description.")

    if not has_valid_description_start(description, page_name):
        errors.append(
            "Description phải bắt đầu bằng `Mua [tên trang]...` hoặc chính `[Tên trang]...`; "
            f"tên trang đang kiểm tra là `{normalize(page_name)}`."
        )

    repeated_price_terms = len(re.findall(r"\b(?:giá rẻ|giá tốt|giá siêu rẻ|giá cực tốt)\b", title.lower()))
    if repeated_price_terms > 1:
        warnings.append("Title lặp nhiều cụm CTA về giá.")

    if re.search(r"(?<!trả )\bgóp\s*0%(?!\w)", title, flags=re.IGNORECASE) and title_len + len("trả ") <= TITLE_MAX:
        warnings.append("Title còn đủ chỗ; ưu tiên `trả góp 0%` thay vì `góp 0%`.")

    repeated_words = repeated_content_words(description)
    if repeated_words:
        detail = ", ".join(f"{word}×{count}" for word, count in repeated_words)
        warnings.append(
            "Description có từ nội dung lặp nhiều lần; kiểm tra khả năng gom/rút gọn để tiết kiệm ký tự: " + detail + "."
        )

    shared_phrases = repeated_long_phrases(title, description)
    page_words = normalized_words(page_name)
    page_ngrams = {
        " ".join(page_words[i : i + 3])
        for i in range(max(0, len(page_words) - 2))
    }
    shared_phrases = [phrase for phrase in shared_phrases if phrase not in page_ngrams]
    if shared_phrases:
        warnings.append(
            "Title và Description lặp cụm 3 từ; kiểm tra information budget và thay bằng intent mới nếu không bắt buộc: "
            + "; ".join(shared_phrases[:3])
            + "."
        )

    title_lower = title.lower()
    desc_lower = description.lower()

    if "chính hãng" in title_lower:
        errors.append("Title TGDĐ không dùng `chính hãng`; dành ngân sách ký tự cho USP/đặc điểm riêng. Nếu cần, đặt `bảo hành chính hãng` trong Description sau khi xác minh.")
    for cta in ("trả góp 0%", "giá tốt", "giao nhanh", "bảo hành chính hãng", "1 đổi 1", "hư gì đổi nấy", "thu cũ đổi mới"):
        if cta in title_lower and cta in desc_lower:
            warnings.append(
                f"CTA/chính sách `{cta}` xuất hiện ở cả Title và Description; ưu tiên dùng Description cho thông tin mới."
            )

    combined = f"{title} {description}".lower()

    if mode == "evergreen":
        if not has_any_pattern(title, EVERGREEN_TECH_PATTERNS):
            errors.append("Title Evergreen phải có ít nhất một term công nghệ/kỹ thuật đã verify.")
        if not has_any_pattern(title, EVERGREEN_POLICY_PATTERNS):
            errors.append("Title Evergreen phải có ít nhất một term chính sách evergreen đã verify.")

        volatile_patterns = {
            "mốc ngày/tháng": r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b|\btừ\s+\d{1,2}/\d{1,2}\b|\bđến\s+\d{1,2}/\d{1,2}\b",
            "giảm giá cụ thể": r"\bgiảm\s+(?:ngay\s+|đến\s+|tới\s+)?\d",
            "giá cụ thể": r"\b(?:chỉ|giá)\s+(?:còn|từ)?\s*\d+(?:[.,]\d+)?\s*(?:k|tr|triệu|đ|đồng)\b",
            "quà tặng/hoàn tiền": r"\b(?:tặng|quà|hoàn)\b",
            "đặt trước/mở bán": r"\b(?:đặt trước|đặt ngay|mở bán|đăng ký nhận tin|ra mắt)\b",
            "thu cũ kèm mức tiền/% cụ thể": r"\bthu cũ\b.*\b\d+(?:[.,]\d+)?\s*(?:k|tr|triệu|đ|đồng|%)\b",
        }
        for label, pattern in volatile_patterns.items():
            if re.search(pattern, combined, flags=re.IGNORECASE):
                errors.append(f"Evergreen chứa thông tin ngắn hạn: {label}.")
        if has_nonzero_percentage(combined):
            errors.append("Evergreen chứa phần trăm khác 0%, có khả năng là khuyến mãi ngắn hạn.")
    else:
        strong_cta = re.search(
            r"\b(?:giảm|tặng|quà|thu cũ|đặt trước|mở bán|trả trước|góp 0%|trả góp 0%|hoàn|giá chỉ|giá từ|ưu đãi)\b",
            combined,
            flags=re.IGNORECASE,
        )
        if not strong_cta:
            warnings.append("Mode CTA mạnh chưa có CTA/offer nổi bật.")

    for phrase in ("rẻ nhất", "tốt nhất", "số 1", "hot nhất"):
        if phrase in combined:
            warnings.append(f"Claim so sánh tuyệt đối cần nguồn chứng minh: {phrase}.")

    return ValidationResult(title_len, desc_len, errors, warnings)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--mode", choices=("evergreen", "strong-cta"), default="evergreen")
    parser.add_argument("--page-name", required=True, help="Tên trang/thực thể chính xác của URL, ví dụ: Laptop Acer Aspire")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    result = validate(args.title, args.description, args.mode, args.page_name)
    payload = {"valid": result.valid, **asdict(result)}

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Title: {result.title_length} ký tự")
        print(f"Description: {result.description_length} ký tự")
        for error in result.errors:
            print(f"ERROR: {error}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        print("PASS" if result.valid else "FAIL")

    return 0 if result.valid else 1


if __name__ == "__main__":
    sys.exit(main())
