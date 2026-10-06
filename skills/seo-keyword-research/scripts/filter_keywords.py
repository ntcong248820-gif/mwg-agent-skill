#!/usr/bin/env python3
"""Lọc + gán KW chính cho keyword ứng viên theo từng URL (lô nhiều URL một lần).

Input JSON: {"jobs": [{"key": "...", "ctx": {...}, "candidates": [{"keyword": "...", "volume": 120}]}]}
  ctx theo dạng trang (xem references/keyword-rules.md):
    sp   : {"type":"sp","name":"<tên SP>","url":"<slug>","id_sp":"<ID>"}
    hang : {"type":"hang","nganh":"<ngành>","hang":"<hãng>","url":"<slug>"}
    nh / dong : {"type":"nh|dong","nganh":"<ngành>","filter":"<tên filter>","url":"<slug>"}
  volume: 0/null (Ahrefs nhóm 0-10) được đổi thành 5. `volume_sheet` từ ahrefs_fetch.py dùng được luôn.
  Mọi khoá phụ khác trong ctx (vd "row", "id_sp") được giữ nguyên ở output để bạn ghép ngược.

  python3 filter_keywords.py --in jobs.json --out classified.json [--existing-file da-co.txt]
Output: cùng cấu trúc, mỗi ứng viên có verdict (keep|review|drop), reason, volume_sheet, main.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from kw_rules import classify, dedupe, normalize


def sheet_volume(v) -> int:
    return 5 if not v else int(v)


def assign_main(ctx: dict, keep: list[dict]) -> None:
    """Gán cờ KW chính. Mặc định mọi keyword giữ lại đều True; sửa ở đây nếu bạn muốn chọn riêng một keyword chính."""
    for it in keep:
        it["main"] = True


def existing_keywords(path: str) -> dict[str, list[str]]:
    """keyword -> nơi đã có. File .txt: mỗi dòng một keyword. File .json: {"keyword": ["nơi 1", ...]}."""
    out: dict[str, list[str]] = defaultdict(list)
    if path.endswith(".json"):
        for kw, where in json.load(open(path, encoding="utf-8")).items():
            out[normalize(kw)] += where if isinstance(where, list) else [str(where)]
    else:
        for line in open(path, encoding="utf-8"):
            if line.strip():
                out[normalize(line)].append("danh sách đã có")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--existing-file", help="keyword đã dùng ở nơi khác (.txt mỗi dòng một keyword, hoặc .json keyword→nơi): trùng thì hạ keep→review")
    a = ap.parse_args()
    jobs = json.load(open(a.inp, encoding="utf-8"))["jobs"]
    known = existing_keywords(a.existing_file) if a.existing_file else {}
    summary = {"keep": 0, "review": 0, "drop": 0}
    for job in jobs:
        ctx = job["ctx"]
        cands = dedupe([{"keyword": c["keyword"], "volume_sheet": sheet_volume(c.get("volume", c.get("volume_sheet")))}
                        for c in job["candidates"]])
        for it in cands:
            it["verdict"], it["reason"] = classify(it["keyword"], ctx)
            where = known.get(it["keyword"], [])
            if it["verdict"] == "keep" and where:
                it["verdict"], it["reason"] = "review", f"trùng keyword đã có ở: {where[0]}"
            summary[it["verdict"]] += 1
        keep = [it for it in cands if it["verdict"] == "keep"]
        assign_main(ctx, keep)
        job["candidates"] = sorted(cands, key=lambda x: (-("keep" == x["verdict"]), -x["volume_sheet"]))
    json.dump({"jobs": jobs}, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(jobs)} URL | keep {summary['keep']} | review {summary['review']} | drop {summary['drop']} → {a.out}")
    if summary["review"]:
        print("Có keyword 'review': người xem quyết định trước khi dùng (chỉ keyword 'keep' là tự động hợp lệ).")


if __name__ == "__main__":
    sys.exit(main())
