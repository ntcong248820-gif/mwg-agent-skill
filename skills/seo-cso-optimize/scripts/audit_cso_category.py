#!/usr/bin/env python3
"""
Audit all products in a TGDD category page for CSO (Content Sản Phẩm Optimize).
Checks:
1. Has product description (Thông tin sản phẩm)?
2. Is it only bullet checklist or has clear headings?
3. Has images in content?
4. Has internal link back to category URL?
5. Has keyword mention of category topic?
"""

import sys
import os
import argparse
import urllib.request
import re
import json
import subprocess
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
ALL_KW_SHEET_ID = ""

def load_all_kw_map():
    env = dict(os.environ)
    env.update({
        "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.path.expanduser("<configDir>"),
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
    })
    params = json.dumps({"spreadsheetId": ALL_KW_SHEET_ID, "range": "'All KW'!L2:O"})
    cmd = ["gws", "sheets", "spreadsheets", "values", "get", "--params", params]
    try:
        res = subprocess.check_output(cmd, env=env)
        rows = json.loads(res).get("values", [])
        kw_map = {}
        for r in rows:
            if len(r) >= 4:
                kw = r[0].strip()
                try:
                    vol = int(r[1].replace(",", "").replace(".", "").strip()) if r[1] else 0
                except:
                    vol = 0
                url = r[3].strip()
                if url:
                    if url not in kw_map:
                        kw_map[url] = []
                    kw_map[url].append((kw, vol))
        return kw_map
    except Exception as e:
        print(f"Warning: Could not fetch All KW ({e})")
        return {}

def get_product_keyword(prod_url, prod_name, kw_map):
    if kw_map and prod_url in kw_map:
        sorted_kws = sorted(kw_map[prod_url], key=lambda x: (x[1], len(x[0])), reverse=True)
        if sorted_kws:
            return sorted_kws[0][0], f"All KW (Vol: {sorted_kws[0][1]})"
    # Fallback: clean distinct model name
    clean = re.sub(r"(?i)^(màn hình gaming|màn hình|laptop|máy in)\s+", "", prod_name).strip()
    clean = re.sub(r"\(.*?\)", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean).lower()
    return clean, "Fallback (Normalized model)"

def fetch_html(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def extract_products_from_category(cat_url):
    html = fetch_html(cat_url)
    soup = BeautifulSoup(html, "html.parser")
    products = []
    seen = set()
    
    cat_slug = cat_url.rstrip("/").split("/")[-1]
    
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/") and len(href.split("/")) == 3 and not href.endswith("-cong") and not href.endswith("/"):
            full_url = "https://www.thegioididong.com" + href
            if full_url not in seen and not any(k in href for k in ["#", "?", "javascript"]):
                seen.add(full_url)
                products.append(full_url)
    return products

def audit_product(prod_url, target_cat_url, target_keyword=None):
    html = fetch_html(prod_url)
    soup = BeautifulSoup(html, "html.parser")
    
    # 1. Product ID
    m = re.search(r"""['"]productId['"]\s*:\s*['"]?(\d+)""", html)
    if not m: m = re.search(r"dfpId\s*=\s*['\"]?(\d+)", html)
    if not m: m = re.search(r"/sp-(\d+)", html)
    if not m: m = re.search(r"""data-id=['"]?(\d+)""", html)
    prod_id = m.group(1) if m else ""
    
    # 2. Product Name
    h1 = soup.find("h1")
    name = h1.get_text(strip=True) if h1 else prod_url.split("/")[-1]
    name = re.sub(r"<[^>]+>", "", name).strip()
    
    # 3. Description container
    desc = soup.find(id="tab-3") or soup.find(class_=lambda c: c and "description" in c and "tab-content" in c) or soup.find(class_=lambda c: c and "description" in c)
    
    text = desc.get_text(strip=True) if desc else ""
    has_content = bool(desc and len(text) > 100)
    
    headings = []
    bullets = 0
    img_count = 0
    has_link = False
    mention_count = 0
    
    target_slug = target_cat_url.rstrip("/").split("/")[-1]
    kw = target_keyword or target_slug.replace("-", " ")
    
    if has_content:
        headings = [h.get_text(strip=True) for h in desc.find_all(["h2", "h3", "h4", "h5"])]
        bullets = desc.get_text().count("•") + len(desc.find_all("li"))
        img_count = len(desc.find_all("img"))
        
        for a in desc.find_all("a", href=True):
            if target_slug in a["href"].lower():
                has_link = True
                break
                
        mention_count = text.lower().count(kw.lower())
        
    has_clear_headings = len(headings) >= 3
    is_only_bullets = (len(headings) == 0 and bullets >= 3)
    
    issues = []
    if not has_content:
        action = "Viết mới"
        issues.append("Chưa có nội dung thông tin sản phẩm")
    else:
        action = "Tối ưu"
        if is_only_bullets:
            issues.append("Bài viết chỉ có bullet checklist, chưa có heading phân cấp")
        if img_count == 0:
            issues.append("Nội dung thiếu hình ảnh minh họa")
        if not has_link:
            issues.append(f"Thiếu internal link trỏ về danh mục: {target_cat_url}")
        if mention_count == 0:
            issues.append(f"Nội dung chưa nhắc đến chủ đề/từ khóa danh mục '{kw}'")
            
    return {
        "id": prod_id,
        "name": name,
        "url": prod_url,
        "has_content": has_content,
        "headings_count": len(headings),
        "headings": headings[:4],
        "bullets_count": bullets,
        "is_only_bullets": is_only_bullets,
        "has_clear_headings": has_clear_headings,
        "img_count": img_count,
        "has_link": has_link,
        "mention_count": mention_count,
        "action": action,
        "issues": issues,
        "notes": "; ".join(issues)
    }

def main():
    parser = argparse.ArgumentParser(description="Audit products in a category for CSO.")
    parser.add_argument("--category-url", required=True, help="Target category URL")
    parser.add_argument("--keyword", help="Target keyword to check mention")
    parser.add_argument("--urls", nargs="*", help="Direct product URLs to audit")
    parser.add_argument("--fetch-kw", action="store_true", help="Fetch highest volume keyword from All KW sheet")
    args = parser.parse_args()
    
    kw_map = load_all_kw_map() if args.fetch_kw else {}
    
    prod_urls = args.urls or extract_products_from_category(args.category_url)
    print(f"Found {len(prod_urls)} products to audit for {args.category_url}...")
    
    results = []
    for u in prod_urls:
        try:
            r = audit_product(u, args.category_url, args.keyword)
            if args.fetch_kw:
                kw, source = get_product_keyword(u, r["name"], kw_map)
                r["target_keyword"] = kw
                r["keyword_source"] = source
            results.append(r)
            kw_info = f" | KW={r.get('target_keyword')}" if args.fetch_kw else ""
            print(f"✓ [{r['id']}] {r['name'][:35]} | Content={r['has_content']} | Img={r['img_count']} | Link={r['has_link']}{kw_info}")
        except Exception as e:
            print(f"✗ Error auditing {u}: {e}")
            
    print("\n--- Summary ---")
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
