#!/usr/bin/env python3
"""
Verify completed CSO Content orders against live TGDD product pages.
Checks if team Content has fulfilled the order:
- Content is live?
- Images are present?
- Internal link to category exists?
- Headings are structured?
If --apply is passed, updates Content_SP_Optimize to "Hoàn thành" and Order Content SP.
"""

import sys
import os
import argparse
import urllib.request
import re
import json
import subprocess
from datetime import datetime
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
ORDER_CONTENT_SHEET_ID = "<orderContent>"
DATA_ORDER_SHEET_ID = ""

def fetch_html(url, timeout=15):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def gws_cmd(cmd_args):
    env = dict(os.environ)
    env.update({
        "GOOGLE_WORKSPACE_CLI_CONFIG_DIR": os.path.expanduser("<configDir>"),
        "PATH": "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin"
    })
    res = subprocess.check_output(cmd_args, env=env)
    return json.loads(res)

def get_order_rows(start_row, end_row):
    params = json.dumps({
        "spreadsheetId": ORDER_CONTENT_SHEET_ID,
        "range": f"'Order Content SP'!A{start_row}:AU{end_row}"
    })
    cmd = ["gws", "sheets", "spreadsheets", "values", "get", "--params", params]
    data = gws_cmd(cmd)
    return data.get("values", [])

def verify_product(row_idx, row):
    prod_id = row[0] if len(row) > 0 else ""
    name = row[4] if len(row) > 4 else ""
    action = row[16] if len(row) > 16 else ""
    url = row[25] if len(row) > 25 else ""
    outline = row[42] if len(row) > 42 else ""
    note = row[45] if len(row) > 45 else ""
    
    if not url:
        return {"row": row_idx, "id": prod_id, "name": name, "status": "FAIL", "reason": "No URL in sheet"}
        
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")
        
        desc = soup.find(id="tab-3") or soup.find(class_=lambda c: c and "description" in c and "tab-content" in c) or soup.find(class_=lambda c: c and "description" in c)
        
        if not desc or len(desc.get_text(strip=True)) < 100:
            return {
                "row": row_idx, "id": prod_id, "name": name, "url": url,
                "status": "FAIL", "reason": "Chưa có nội dung bài viết trên site"
            }
            
        imgs = desc.find_all("img")
        headings = desc.find_all(["h2", "h3", "h4", "h5"])
        links = desc.find_all("a", href=True)
        
        # Check target category link in note
        m_link = re.search(r"https://www\.thegioididong\.com/([a-zA-Z0-9-]+)", note)
        target_slug = m_link.group(1) if m_link else ""
        
        has_cat_link = False
        if target_slug:
            for a in links:
                if target_slug in a["href"].lower():
                    has_cat_link = True
                    break
        else:
            has_cat_link = True # No target link specified
            
        issues = []
        if len(imgs) == 0:
            issues.append("Chưa có hình ảnh trong bài viết")
        if target_slug and not has_cat_link:
            issues.append(f"Thiếu link danh mục: {target_slug}")
        if len(headings) < 3 and "outline" in note.lower():
            issues.append("Bài viết chưa chia heading rõ ràng theo Outline")
            
        passed = (len(issues) == 0)
        return {
            "row": row_idx,
            "id": prod_id,
            "name": name,
            "url": url,
            "status": "PASS" if passed else "FAIL",
            "img_count": len(imgs),
            "headings_count": len(headings),
            "has_cat_link": has_cat_link,
            "issues": issues
        }
    except Exception as e:
        return {
            "row": row_idx, "id": prod_id, "name": name, "url": url,
            "status": "ERROR", "reason": str(e)
        }

def update_status_data_order(passed_urls):
    if not passed_urls:
        return
    # Read Content_SP_Optimize to find matching URLs
    params = json.dumps({
        "spreadsheetId": DATA_ORDER_SHEET_ID,
        "range": "Content_SP_Optimize!C1:D100"
    })
    cmd = ["gws", "sheets", "spreadsheets", "values", "get", "--params", params]
    data = gws_cmd(cmd)
    rows = data.get("values", [])
    
    updates = []
    for i, r in enumerate(rows):
        if len(r) > 0 and r[0] in passed_urls:
            updates.append({
                "range": f"Content_SP_Optimize!D{i+1}",
                "values": [["Hoàn thành"]]
            })
            
    for u in updates:
        p = json.dumps({
            "spreadsheetId": DATA_ORDER_SHEET_ID,
            "range": u["range"],
            "valueInputOption": "USER_ENTERED"
        })
        b = json.dumps({"range": u["range"], "majorDimension": "ROWS", "values": u["values"]})
        c = ["gws", "sheets", "spreadsheets", "values", "update", "--params", p, "--json", b]
        gws_cmd(c)
        print(f"✓ Updated Data Order {u['range']} -> Hoàn thành")

def main():
    parser = argparse.ArgumentParser(description="Verify CSO Content orders.")
    parser.add_argument("--range", required=True, help="Row range e.g. 8333:8359")
    parser.add_argument("--apply", action="store_true", help="Apply status updates to Google Sheets")
    args = parser.parse_args()
    
    m = re.search(r"(\d+)\s*[:\-]\s*(\d+)", args.range)
    if not m:
        print("Invalid range format. Use e.g. 8333:8359")
        sys.exit(1)
        
    start_row = int(m.group(1))
    end_row = int(m.group(2))
    
    print(f"Reading rows {start_row} to {end_row} from 'Order Content SP'...")
    rows = get_order_rows(start_row, end_row)
    print(f"Loaded {len(rows)} order rows. Checking live pages...\n")
    
    results = []
    passed_urls = set()
    
    for i, row in enumerate(rows):
        cur_row = start_row + i
        res = verify_product(cur_row, row)
        results.append(res)
        status_icon = "✓ PASS" if res.get("status") == "PASS" else "✗ FAIL"
        issues_str = f" - {', '.join(res.get('issues', []))}" if res.get("issues") else ""
        print(f"Row {cur_row}: [{res.get('id')}] {res.get('name')[:35]} -> {status_icon}{issues_str}")
        if res.get("status") == "PASS" and res.get("url"):
            passed_urls.add(res["url"])
            
    pass_cnt = sum(1 for r in results if r.get("status") == "PASS")
    fail_cnt = len(results) - pass_cnt
    print(f"\nSummary: {pass_cnt} PASS, {fail_cnt} FAIL / {len(results)} Total")
    
    if args.apply:
        if passed_urls:
            print(f"\nApplying 'Hoàn thành' for {len(passed_urls)} passing products in Data Order...")
            update_status_data_order(passed_urls)
        else:
            print("No passing products to apply.")
    else:
        print("\nDry-run only. Add --apply to update Google Sheets.")

if __name__ == "__main__":
    main()
