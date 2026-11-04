#!/usr/bin/env python3
"""Kiểm bộ hình của MỘT bài có đủ đa dạng không (chống hình đơn điệu). Chỉ đọc.

Dùng: check-image-set.py REPORT.json [REPORT.json ...]   (report do compose-sp-image.py ghi)
ERROR: 2 hình cùng --layout.
WARN : 2 hình dùng lại đúng một ảnh gốc (gallery thường chỉ 4–6 góc nên đôi khi không tránh được, ưu tiên góc khác);
       1 kiểu nền (--bg) dùng cho quá nửa bộ hình; quá 2 bảng màu khác nhau (bài mất đồng bộ).
Exit 0 = không có ERROR.
"""
import json, os, sys
from collections import Counter


def main():
    paths = sys.argv[1:]
    if not paths:
        print(__doc__); return 2
    reps = [(os.path.basename(p), json.load(open(p, encoding="utf8"))) for p in paths]
    errors, warns = [], []
    layouts = Counter(r.get("layout", "right") for _, r in reps)
    for k, n in layouts.items():
        if n > 1:
            errors.append(f"{n} hình cùng bố cục '{k}': " + ", ".join(f for f, r in reps if r.get("layout", "right") == k))
    seen = {}
    for f, r in reps:
        for p in r.get("placements", []):
            if p["kind"] != "cutout":
                continue
            if p["src_sha256"] in seen and r.get("layout") != "zoom":
                warns.append(f"{f} dùng lại đúng ảnh gốc của {seen[p['src_sha256']]} ({os.path.basename(p['src'])}): chọn góc chụp khác")
            seen.setdefault(p["src_sha256"], f)
    bgs = Counter(r.get("bg", "gradient") for _, r in reps)
    for k, n in bgs.items():
        if len(reps) >= 3 and n > len(reps) / 2:
            warns.append(f"nền '{k}' dùng {n}/{len(reps)} hình")
    pals = {r.get("palette") for _, r in reps}
    if len(pals) > 2:
        warns.append(f"{len(pals)} bảng màu khác nhau ({', '.join(sorted(map(str, pals)))}): giữ 1–2 bảng màu cho một bài")
    print(json.dumps({"images": len(reps), "layouts": dict(layouts), "bg": dict(bgs), "palettes": sorted(map(str, pals))}, ensure_ascii=False))
    for e in errors:
        print("ERROR", e)
    for w in warns:
        print("WARN", w)
    print("ĐẠT" if not errors else "KHÔNG ĐẠT")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
