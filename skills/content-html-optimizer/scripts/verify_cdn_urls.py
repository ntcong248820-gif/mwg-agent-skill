#!/usr/bin/env python3
"""Kiểm URL CDN dự đoán của ảnh trong một content workspace.

Dùng 2 lần trong vòng đời một bài:

  --expect free   TRƯỚC khi upload: mọi URL phải 404. Có cái 200 nghĩa là tên file
                  đã bị bài khác chiếm — đổi tên, đừng up đè.
  --expect live   SAU khi upload: mọi URL phải 200. Có cái 404 nghĩa là CMS không
                  giữ nguyên tên file, URL đã ghi vào bài là URL chết.

Vì sao cần script: thư mục `/News/{id}/` khác nhau theo bài, nên phần thư mục phải
được chốt bằng phép đo chứ không đoán. Phần tên file thì CMS giữ nguyên.
"""
from __future__ import annotations

import argparse, csv, json, re, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

DEFAULT_BASE = "https://cdnv2.tgdd.vn/mwg-static/common/News/0/"
TIMEOUT = 15


def infer_base(ws: Path) -> str | None:
    """Lấy tiền tố CDN từ ảnh đã có sẵn trong source của chính workspace này.

    Đây là căn cứ tốt nhất: cùng một bài thì CMS bỏ ảnh vào cùng một thư mục.
    """
    for name in ("source/final-content.html", "source/source-content.html"):
        f = ws / name
        if not f.exists():
            continue
        m = re.findall(r'src="(https://[^"]*/)[^/"]+\.(?:jpg|jpeg|png|webp)"', f.read_text())
        if m:
            return max(set(m), key=m.count)
    return None


def filenames(ws: Path) -> list[str]:
    csv_path = ws / "metadata" / "image-metadata.csv"
    if csv_path.exists():
        rows = [r["file-name"] for r in csv.DictReader(csv_path.open()) if r.get("file-name")]
        if rows:
            return rows
    return sorted(p.name for p in (ws / "images-processed").glob("*.jpg"))


def probe(url: str) -> int:
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--base", help=f"tiền tố URL; mặc định suy từ source, không có thì {DEFAULT_BASE}")
    ap.add_argument("--expect", choices=["free", "live"], required=True)
    ap.add_argument("--write-json", action="store_true", help="ghi cdn-urls.json khi --expect live đạt")
    a = ap.parse_args()

    ws = Path(a.workspace)
    base = a.base or infer_base(ws) or DEFAULT_BASE
    if not base.endswith("/"):
        base += "/"
    names = filenames(ws)
    if not names:
        print("[ERROR] không tìm thấy tên ảnh nào (metadata/image-metadata.csv hoặc images-processed/)")
        return 1

    src = "--base" if a.base else ("suy từ source" if infer_base(ws) else "mặc định")
    print(f"[INFO] base   : {base}  ({src})")
    print(f"[INFO] số ảnh : {len(names)}   kỳ vọng: {a.expect}\n")

    with ThreadPoolExecutor(max_workers=8) as ex:
        codes = list(ex.map(lambda n: probe(base + n), names))

    want = 404 if a.expect == "free" else 200
    bad = [(n, c) for n, c in zip(names, codes) if c != want]
    for n, c in bad:
        print(f"  {c}  {n}")

    ok = len(names) - len(bad)
    print(f"\n{ok}/{len(names)} đúng kỳ vọng ({want}).")
    if bad:
        if a.expect == "free":
            print("Tên đã bị chiếm — đổi tên file trước khi upload, đừng up đè lên ảnh bài khác.")
        else:
            print("URL chết. CMS có thể đã đổi tên file hoặc đổi thư mục.")
            print("Mở 1 ảnh trong CMS, lấy URL thật, chạy lại với --base cho đúng.")
        return 1

    if a.expect == "live" and a.write_json:
        out = ws / "cdn-urls.json"
        out.write_text(json.dumps({n: base + n for n in names}, ensure_ascii=False, indent=2))
        print(f"đã ghi {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
