#!/usr/bin/env python3
"""Lấy khối bài viết SP (product_articles) từ trang live TGDĐ, chỉ đọc.

Dùng: fetch-live-article.py URL [URL ...] --out-dir DIR [--delay 0.7]
Ra: DIR/<ngành>__<slug>.html (khối <div id="description-text-detail">), in thống kê 1 dòng/URL.
Trang chưa có bài (PIM trống) -> file rỗng, dòng báo EMPTY. Không ghi gì lên hệ thống.
"""
import argparse, os, re, subprocess, sys, time, html

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/128 Safari/537.36"
OPEN = '<div id="description-text-detail">'


def fetch(url):
    r = subprocess.run(["curl", "-s", "-L", "-A", UA, url], capture_output=True, check=True)
    return r.stdout.decode("utf8", "ignore")


def extract(page):
    i = page.find(OPEN)
    if i < 0:
        return ""
    j = page.find('<div id="feedback"', i)
    return page[i:j if j > 0 else i + 80000]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--delay", type=float, default=0.7)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    for u in a.urls:
        parts = u.rstrip("/").split("/")
        name = f"{parts[-2]}__{parts[-1].split('?')[0]}.html"
        art = extract(fetch(u))
        open(os.path.join(a.out_dir, name), "w", encoding="utf8").write(art)
        words = len(html.unescape(re.sub(r"<[^>]+>", " ", art)).split())
        print(f"{'EMPTY' if not art else 'OK   '} {name} h3={art.count('<h3')} từ={words} ảnh={art.count('<img')} link={art.count('<a ')}")
        time.sleep(a.delay)


if __name__ == "__main__":
    sys.exit(main())
