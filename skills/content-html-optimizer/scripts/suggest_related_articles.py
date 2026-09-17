#!/usr/bin/env python3
"""Gợi ý bài viết liên quan cho box "Xem thêm" cuối bài TGDĐ.

Nguồn dữ liệu duy nhất: Google Sheet 'BÀI TIN' (cột B = Link air, C = Hệ bài,
D = Title, E = KW mục tiêu). Script KHÔNG tự suy/bịa URL và KHÔNG tự chèn vào
bài — nó chỉ chấm điểm, xếp hạng và in ra HTML sẵn để người viết duyệt rồi dán.

Chọn bài liên quan là quyết định biên tập, không phải khớp chuỗi. Script chỉ
thu hẹp 6800+ dòng xuống một danh sách ngắn đáng đọc.

Ví dụ:
    python3 suggest_related_articles.py \\
        --workspace content-workspaces/hoidap-top-laptop-sinh-vien \\
        --terms "laptop sinh viên,laptop học tập,laptop dưới 20 triệu"
"""

from __future__ import annotations

import os
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

def _require(name, value, hint):
    """Fail loudly instead of querying the wrong spreadsheet with an empty id."""
    if not value:
        raise SystemExit(
            "%s is not set.\n"
            "Export it to point this skill at your own sheet:\n"
            "    export %s=<spreadsheet-id>\n"
            "%s" % (name, name, hint))
    return value


SHEET_BAI_TIN_ID = _require("SHEET_BAI_TIN_ID", os.environ.get("SHEET_BAI_TIN_ID", ""),
    "Sheet holding article title -> URL rows.")
SHEET_RANGE = "BÀI TIN!A2:E"

# Trọng số: khớp ở KW mục tiêu đáng tin hơn khớp ở Title, vì KW là chủ đích SEO
# của bài đó, còn Title có thể chứa từ chung chung ("tốt nhất", "tại TGDĐ").
WEIGHT_KW = 3
WEIGHT_TITLE = 2
WEIGHT_HE_BAI = 1


def fetch_bai_tin_rows() -> list[list[str]]:
    """Fetch sheet BÀI TIN qua gws CLI.

    ensure_ascii=False là bắt buộc: tên sheet 'BÀI TIN' có dấu, json.dumps mặc
    định escape thành '\\u00c0I TIN' và gws trả exit 5 không rõ nguyên nhân.
    """
    params = json.dumps(
        {"spreadsheetId": SHEET_BAI_TIN_ID, "range": SHEET_RANGE},
        ensure_ascii=False,
    )
    cmd = ["gws", "sheets", "spreadsheets", "values", "get", "--params", params]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError:
        sys.exit("[ERR] Không tìm thấy lệnh `gws`. Cài/GG auth trước khi chạy.")
    except subprocess.CalledProcessError as e:
        sys.exit(f"[ERR] gws lỗi (exit {e.returncode}): {e.stderr.strip()[:300]}")

    # gws in dòng 'Using keyring backend: ...' trước JSON.
    stdout = res.stdout
    brace = stdout.find("{")
    if brace == -1:
        sys.exit("[ERR] gws không trả JSON.")
    try:
        data = json.loads(stdout[brace:])
    except json.JSONDecodeError as e:
        sys.exit(f"[ERR] Không parse được JSON từ gws: {e}")
    return data.get("values", [])


def strip_accents(text: str) -> str:
    """Bỏ dấu để khớp được cả khi người dùng gõ term không dấu."""
    nfkd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", strip_accents(text.lower())).strip()


def derive_terms_from_slug(slug: str) -> list[str]:
    """Fallback khi user không truyền --terms: tách từ tên workspace.

    Bỏ các tiền tố quy ước ('hoidap', 'top') vì chúng khớp với gần như mọi bài
    trong sheet nên chỉ làm loãng điểm.
    """
    parts = [p for p in slug.split("-") if p not in {"hoidap", "top", "bai"}]
    if not parts:
        return []
    joined = " ".join(parts)
    return [joined, " ".join(parts[:2])] if len(parts) > 2 else [joined]


def collect_existing_urls(workspace: Path) -> set[str]:
    """URL đã có trong bài (kể cả link SP) — không gợi ý lại."""
    urls: set[str] = set()
    for name in ("source/source-content.html", "source/final-content.html"):
        path = workspace / name
        if path.exists():
            html = path.read_text(encoding="utf-8")
            urls.update(re.findall(r'href="([^"]+)"', html))
    return urls


def article_id_from_url(url: str) -> str | None:
    """ID bài tin = số cuối slug. Dùng để loại chính bài đang viết."""
    m = re.search(r"-(\d{6,})/?$", url.rstrip("/"))
    return m.group(1) if m else None


def score_row(
    row: list[str], terms: list[str], prefer_he_bai: str | None
) -> tuple[int, list[str]]:
    """Chấm điểm 1 dòng sheet. Trả (điểm, các term đã khớp)."""
    url = row[1].strip() if len(row) > 1 else ""
    he_bai = row[2].strip() if len(row) > 2 else ""
    title = row[3].strip() if len(row) > 3 else ""
    kw = row[4].strip() if len(row) > 4 else ""

    if not url or not title:
        return 0, []

    kw_n, title_n = normalize(kw), normalize(title)
    score = 0
    matched: list[str] = []
    for term in terms:
        term_n = normalize(term)
        if not term_n:
            continue
        hit = 0
        if term_n in kw_n:
            hit += WEIGHT_KW
        if term_n in title_n:
            hit += WEIGHT_TITLE
        if hit:
            score += hit
            matched.append(term)

    if score and prefer_he_bai and normalize(prefer_he_bai) in normalize(he_bai):
        score += WEIGHT_HE_BAI
    return score, matched


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--workspace",
        help="Đường dẫn content workspace. Dùng để tự loại URL đã có trong bài.",
    )
    ap.add_argument(
        "--terms",
        help="Các cụm chủ đề, cách nhau bằng dấu phẩy. Không có thì suy từ tên workspace.",
    )
    ap.add_argument("--top", type=int, default=8, help="Số gợi ý in ra (mặc định 8).")
    ap.add_argument(
        "--he-bai",
        help="Ưu tiên hệ bài này (vd 'Top sản phẩm', 'Tư vấn chọn mua'). Cộng điểm, không lọc cứng.",
    )
    ap.add_argument(
        "--exclude-id",
        action="append",
        default=[],
        help="ID bài tin cần loại (lặp lại được). Bài đang viết nên loại ở đây.",
    )
    args = ap.parse_args()

    workspace = Path(args.workspace).resolve() if args.workspace else None
    if workspace and not workspace.exists():
        sys.exit(f"[ERR] Không thấy workspace: {workspace}")

    if args.terms:
        terms = [t.strip() for t in args.terms.split(",") if t.strip()]
    elif workspace:
        terms = derive_terms_from_slug(workspace.name)
        print(f"[INFO] Không có --terms, suy từ tên workspace: {terms}")
    else:
        sys.exit("[ERR] Cần --terms hoặc --workspace.")

    if not terms:
        sys.exit("[ERR] Không có term nào để tra.")

    existing_urls = collect_existing_urls(workspace) if workspace else set()
    excluded_ids = set(args.exclude_id)
    for url in existing_urls:
        aid = article_id_from_url(url)
        if aid:
            excluded_ids.add(aid)

    print(f"[INFO] Fetching sheet 'BÀI TIN'...")
    rows = fetch_bai_tin_rows()
    print(f"[INFO] {len(rows)} dòng. Loại sẵn {len(excluded_ids)} ID đã có trong bài.")

    scored = []
    seen_urls: set[str] = set()
    for row in rows:
        score, matched = score_row(row, terms, args.he_bai)
        if score <= 0:
            continue
        url = row[1].strip()
        if url in existing_urls or url in seen_urls:
            continue
        aid = article_id_from_url(url)
        if aid and aid in excluded_ids:
            continue
        seen_urls.add(url)
        scored.append(
            {
                "score": score,
                "matched": matched,
                "url": url,
                "he_bai": row[2].strip() if len(row) > 2 else "",
                "title": row[3].strip() if len(row) > 3 else "",
                "kw": row[4].strip() if len(row) > 4 else "",
            }
        )

    scored.sort(key=lambda x: (-x["score"], x["title"]))
    top = scored[: args.top]

    if not top:
        print("\n[KẾT QUẢ] Không tìm được bài liên quan nào khớp term.")
        print("Thử nới term (bỏ bớt chữ) hoặc kiểm lại chính tả.")
        return

    print(f"\n=== {len(top)} gợi ý (trên tổng {len(scored)} bài khớp) ===\n")
    for i, item in enumerate(top, 1):
        print(f"{i}. [{item['score']}đ] {item['title']}")
        print(f"   hệ bài : {item['he_bai']}")
        print(f"   KW     : {item['kw']}")
        print(f"   khớp   : {', '.join(item['matched'])}")
        print(f"   URL    : {item['url']}\n")

    print("=== HTML sẵn để dán vào [info] (tự chọn 2-3 dòng, đừng dán hết) ===\n")
    print("<p>[info]</p>")
    print("<p><strong>Xem thêm</strong>:</p>")
    print("<ul>")
    # Anchor = TOÀN BỘ tiêu đề, không cắt lấy 1 cụm trong tiêu đề.
    for item in top:
        print(
            f'<li><a title="{item["title"]}" href="{item["url"]}" '
            f'target="_blank" rel="noopener">{item["title"]}</a></li>'
        )
    print("</ul>")
    print("<p>[/info]</p>")
    print("\n[LƯU Ý] Đây là gợi ý, chưa phải quyết định. Đọc lại tiêu đề xem có")
    print("thật sự liên quan với bài đang viết không rồi mới giữ 2-3 dòng.")


if __name__ == "__main__":
    main()
