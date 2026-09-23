#!/usr/bin/env python3
"""Kiểm tra trạng thái kinh doanh + ID + giá sản phẩm TGDĐ bằng HTTP tĩnh.

Rẻ hơn mở browser rất nhiều. Phân loại 3 mức:
  LIVE        - chắc chắn còn kinh doanh
  DISCONTINUED- chắc chắn ngừng kinh doanh
  AMBIGUOUS   - không kết luận được từ HTML tĩnh -> PHẢI mở browser check
                text "SẢN PHẨM NGỪNG KINH DOANH" (render bằng JS)

Tín hiệu (đã verify trên SP thật):
  pageStatus: 'Không kinh doanh'      -> DISCONTINUED (definitive)
  item_web_status: "Ngừng kinh doanh" -> DISCONTINUED (definitive)
  item_web_status: "Còn hàng"         -> LIVE (definitive)
  item_web_status: ""                 -> AMBIGUOUS (cả LIVE và DISC đều gặp)

CẢNH BÁO: JSON-LD "availability" LUÔN trả InStock kể cả SP đã ngừng bán -> KHÔNG
dùng làm tín hiệu. Category grid có cache lag -> SP ngừng bán vẫn hiện trong grid.

Usage:
  python3 check_product_status.py URL_OR_SLUG [URL_OR_SLUG ...]
  python3 check_product_status.py --file urls.txt
  python3 check_product_status.py --grid "https://www.thegioididong.com/laptop?g=laptop-gaming&p=20-25-trieu"
  python3 check_product_status.py --json out.json URL ...
"""
import argparse
import html as htmllib
import json
import re
import sys
import urllib.error
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
BASE = "https://www.thegioididong.com"
TIMEOUT = 30

LIVE, DISCONTINUED, AMBIGUOUS, ERROR = "LIVE", "DISCONTINUED", "AMBIGUOUS", "ERROR"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="ignore")


def norm_url(s):
    """URL day du / path (/laptop/slug) / slug co dau '/'. Chi so (product ID) KHONG
    suy ra duoc URL vi ID khong nam trong path -> bao loi thay vi doan sai nganh hang."""
    if s.startswith("http"):
        return s.split("?")[0]
    s = s.lstrip("/")
    if s.isdigit():
        raise ValueError(
            f"'{s}' la product ID, khong suy ra duoc URL. Truyen URL day du hoac "
            "path dang '{nganh-hang}/{slug}' (lay tu --grid)."
        )
    if "/" not in s:
        raise ValueError(
            f"'{s}' thieu nganh hang. Truyen '{{nganh-hang}}/{s}', vd 'laptop/{s}'."
        )
    return f"{BASE}/{s}"


def _uniq(items):
    """Giữ thứ tự xuất hiện, bỏ trùng."""
    out, seen = [], set()
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _grp(pattern, html, default=""):
    m = re.search(pattern, html)
    return m.group(1) if m else default


def classify(html):
    """Trả (status, page_status, web_status, reason)."""
    page_status = _grp(r"pageStatus:\s*'([^']*)'", html)
    web_status = _grp(r'item_web_status:\s*"([^"]*)"', html)

    if "Không kinh doanh" in page_status:
        return DISCONTINUED, page_status, web_status, "pageStatus='Không kinh doanh'"
    if "Ngừng kinh doanh" in web_status:
        return DISCONTINUED, page_status, web_status, "item_web_status='Ngừng kinh doanh'"
    if "Còn hàng" in web_status:
        return LIVE, page_status, web_status, "item_web_status='Còn hàng'"
    return (AMBIGUOUS, page_status, web_status,
            "item_web_status rỗng -> PHẢI mở browser check 'SẢN PHẨM NGỪNG KINH DOANH'")


def parse_price(html):
    """Trả (price_sale, price_list, source).

    price_sale: datalayer `price: 24990000.0` (key KHÔNG có nháy) = giá bán thật,
    khớp giá trên category grid. Đây là giá phải đưa vào bài.
    price_list: JSON-LD `"price": 29990000.0` = giá gốc, thường CAO hơn giá bán.
    `viewed-product-price` chỉ tồn tại trong CSS, KHÔNG phải markup -> đừng dùng.
    """
    def num(pat):
        m = re.search(pat, html)
        return int(float(m.group(1))) if m else None

    sale = num(r'(?<!")\bprice:\s*([\d.]+)') or num(r'\bvalue:\s*([\d.]+)')
    lst = num(r'"price":\s*"?([\d.]+)')
    if sale:
        return sale, lst, "datalayer price (giá bán thật)"
    if lst:
        return lst, lst, "json-ld (giá gốc, có thể CAO hơn giá bán)"
    return None, None, ""


def check_one(url):
    try:
        url = norm_url(url)
    except ValueError as e:
        return {"url": url, "status": ERROR, "reason": str(e)}
    out = {"url": url}
    try:
        html = fetch(url)
    except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
        out.update(status=ERROR, reason=str(e))
        return out

    status, page_status, web_status, reason = classify(html)
    price, price_list, price_src = parse_price(html)
    out.update(
        status=status,
        product_id=_grp(r'item_id:\s*"(\d+)"', html) or None,
        name=htmllib.unescape(_grp(r'item_name:\s*"([^"]*)"', html)) or None,
        brand=htmllib.unescape(_grp(r'item_brand:\s*"([^"]*)"', html)) or None,
        price=price,
        price_list=price_list,
        price_source=price_src,
        page_status=page_status,
        item_web_status=web_status,
        reason=reason,
        # Banner marketing (Slider/...). Nhiều SP không có banner -> dùng product_images.
        banner_slides=_uniq(re.findall(r'''(?:src|data-src)=["']([^"']*/Slider/[^"']+)''', html)),
        # Fallback: ảnh sản phẩm Products/Images/{cate}/{id}/... (bỏ thumb/resize nhỏ)
        product_images=_uniq(
            u for u in re.findall(r'''(?:src|data-src)=["']([^"']*/Products/Images/[^"']+)''', html)
            if "-thumb-" not in u
        ),
    )
    return out


def check_grid(grid_url):
    """Liệt kê SP trong 1 trang category grid (1 request). CHỈ để tìm ứng viên.

    Grid render mỗi SP là <li class=" item __cate_44" data-index data-id data-price>
    chứa <a href='/{nganh-hang}/{slug}?...' data-price data-name data-brand>.
    LƯU Ý href dùng nháy ĐƠN. li[data-price] = giá gốc; a[data-price] = giá bán.

    Grid có cache lag -> SP ngừng bán vẫn xuất hiện. LUÔN check lại từng SP.
    Grid chỉ trả trang 1 (~20 SP) -> SP còn bán vẫn có thể thiếu do phân trang.
    """
    html = fetch(grid_url)
    seen, rows = set(), []
    for m in re.finditer(r'<li[^>]*\sdata-index="\d+"[^>]*>', html):
        li = m.group(0)
        # Bỏ li.merge__item: đó là ô chọn BIẾN THỂ cấu hình bên trong 1 card SP,
        # không phải SP riêng. li của SP thật luôn có data-productcode.
        if "merge__item" in li or "data-productcode" not in li:
            continue
        block = html[m.end():m.end() + 3000]
        href = _grp(r"""href=['"](/[a-z0-9-]+/[^'"?#]+)""", block)
        if not href or href in seen:
            continue
        seen.add(href)

        def num(pat, src):
            v = _grp(pat, src)
            return int(float(v)) if v else None

        rows.append({
            "url": BASE + href,
            "product_id": _grp(r'data-id="(\d+)"', li) or None,
            "name": htmllib.unescape(_grp(r'data-name="([^"]*)"', block)) or None,
            "brand": htmllib.unescape(_grp(r'data-brand="([^"]*)"', block)) or None,
            "price_sale": num(r'<a[^>]*\sdata-price="([\d.]+)"', block),
            "price_list": num(r'data-price="([\d.]+)"', li),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="*", help="URL hoặc slug sản phẩm")
    ap.add_argument("--file", help="File chứa 1 URL/slug mỗi dòng")
    ap.add_argument("--grid", help="Category grid URL -> liệt kê ứng viên (1 request)")
    ap.add_argument("--json", help="Ghi kết quả ra file JSON")
    a = ap.parse_args()

    if a.grid:
        rows = check_grid(a.grid)
        print(f"{len(rows)} SP trong grid (trang 1). Grid có cache lag - PHẢI check lại từng SP.\n")
        for r in rows:
            p = f"{r['price_sale']:,}đ" if r["price_sale"] else "?"
            print(f"  {p:>14}  id={r['product_id'] or '?':<8} {r['name'] or r['url']}")
        if a.json:
            with open(a.json, "w", encoding="utf-8") as f:
                json.dump(rows, f, ensure_ascii=False, indent=2)
            print(f"\n-> {a.json}")
        return 0

    targets = list(a.urls)
    if a.file:
        with open(a.file, encoding="utf-8") as f:
            targets += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not targets:
        ap.error("Cần URL/slug, --file, hoặc --grid")

    results = [check_one(t) for t in targets]
    buckets = {LIVE: [], DISCONTINUED: [], AMBIGUOUS: [], ERROR: []}
    for r in results:
        buckets[r["status"]].append(r)
        icon = {LIVE: "OK  ", DISCONTINUED: "STOP", AMBIGUOUS: "??  ", ERROR: "ERR "}[r["status"]]
        # '~' = giá lấy từ JSON-LD (giá GỐC, không phải giá bán) -> lấy giá bán từ --grid
        mark = "~" if r.get("price") and "json-ld" in (r.get("price_source") or "") else ""
        price = f"{mark}{r['price']:,}đ" if r.get("price") else "?"
        print(f"[{icon}] {r['status']:<12} id={r.get('product_id') or '?':<7} {price:>14}  {r.get('name') or r['url']}")
        if r["status"] != LIVE:
            print(f"         -> {r['reason']}")

    print(f"\nLIVE {len(buckets[LIVE])} | DISCONTINUED {len(buckets[DISCONTINUED])} "
          f"| AMBIGUOUS {len(buckets[AMBIGUOUS])} | ERROR {len(buckets[ERROR])}")
    if any("json-ld" in (r.get("price_source") or "") for r in results):
        print("Giá có dấu '~' là GIÁ GỐC (datalayer trả 0) - lấy giá bán thật từ --grid.")
    if buckets[DISCONTINUED]:
        print("\nNGỪNG KINH DOANH - phải thay:")
        for r in buckets[DISCONTINUED]:
            print(f"  - {r.get('name') or r['url']} (id={r.get('product_id')})")
    if buckets[AMBIGUOUS]:
        print("\nMƠ HỒ - PHẢI mở browser check 'SẢN PHẨM NGỪNG KINH DOANH':")
        for r in buckets[AMBIGUOUS]:
            print(f"  - {r['url']}")

    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n-> {a.json}")

    return 1 if (buckets[DISCONTINUED] or buckets[ERROR]) else 0


if __name__ == "__main__":
    sys.exit(main())
