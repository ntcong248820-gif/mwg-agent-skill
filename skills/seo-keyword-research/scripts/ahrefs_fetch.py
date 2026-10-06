#!/usr/bin/env python3
"""Gọi Ahrefs Keywords Explorer có cổng chi phí (COST_GATE).

Mặc định CHỈ IN ƯỚC LƯỢNG, không gọi API. Gọi thật khi có --approve <units> và
units đó >= ước lượng trường hợp xấu nhất. Công thức + giá cột: references/ahrefs-units-and-api.md

  python3 ahrefs_fetch.py estimate --limit 30 --requests 6
  python3 ahrefs_fetch.py matching --seeds "tai nghe chống ồn" "laptop card rời" --limit 30 --out m.json
  python3 ahrefs_fetch.py matching --seeds ... --limit 30 --out m.json --approve 2500
  python3 ahrefs_fetch.py overview --keywords-file cands.txt --out o.json --approve 6500
  python3 ahrefs_fetch.py smoke      # 0 units: đối chiếu công thức với header thật
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime


BASE = "https://api.ahrefs.com/v3/keywords-explorer"
BASE_COST = 50
# Giá cột theo docs (matching-terms). Cột không liệt kê = 1 unit.
FIELD_COST = {"volume": 10, "difficulty": 10, "global_volume": 10, "intents": 10,
              "traffic_potential": 10, "volume_monthly": 10}
DEFAULT_SELECT = "keyword,volume"   # chỉ keyword + volume: 11 units/dòng
OVERVIEW_CHUNK = 50                 # CHƯA xác minh giới hạn keyword/request — giữ nhỏ để URL không quá dài


def per_row_cost(select: str, where_order_fields: tuple[str, ...] = ()) -> int:
    fields = {f.strip() for f in select.split(",") if f.strip()} | set(where_order_fields)
    return sum(FIELD_COST.get(f, 1) for f in fields)


def units(select: str, rows: int, extra_fields: tuple[str, ...] = ()) -> int:
    return max(BASE_COST, per_row_cost(select, extra_fields) * rows)


def key_var() -> str:
    """Tên biến chứa key: env AHREFS_KEY_VAR, mặc định AHREFS_API_KEY."""
    return os.environ.get("AHREFS_KEY_VAR") or "AHREFS_API_KEY"


def api_key() -> str:
    var = key_var()
    key = os.environ.get(var, "").strip()
    if not key:
        env_file = pathlib.Path(os.environ.get("AHREFS_ENV_FILE", ".env"))   # mặc định .env ở thư mục đang chạy
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith(var + "="):          # chỉ trích đúng biến này, không đụng dòng khác
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        sys.exit(f"Thiếu biến {var} (môi trường hoặc file .env / AHREFS_ENV_FILE). Không in khoá ra.")
    return key


def call(endpoint: str, params: dict, retry: bool = True) -> tuple[dict, dict]:
    url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key()}", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8")), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        if exc.code == 429 and retry:
            time.sleep(20)
            return call(endpoint, params, retry=False)
        sys.exit(f"Ahrefs HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:300]}")


def sheet_volume(v) -> int:
    """Quy ước: Ahrefs nhóm '0-10' (trả 0/null) ghi là 5 để không nhầm với keyword chưa đo."""
    return 5 if not v else int(v)


def ledger(path: str, entry: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), **entry}, ensure_ascii=False) + "\n")


def run(endpoint: str, jobs: list[dict], select: str, approve: int | None, out: str, rows_each: int) -> None:
    est = sum(units(select, rows_each) for _ in jobs)
    print(f"{len(jobs)} request × tối đa {rows_each} dòng × {per_row_cost(select)} units/dòng "
          f"→ ước lượng xấu nhất {est} units (mỗi request tối thiểu {BASE_COST})")
    if approve is None:
        print("CHƯA GỌI API. Thêm --approve <units> (>= ước lượng) sau khi người chịu chi phí xác nhận.")
        return
    if approve < est:
        sys.exit(f"--approve {approve} < ước lượng {est}. Tăng approve hoặc giảm limit/số request.")
    spent, result, log = 0, [], out.replace(".json", "") + ".ledger.jsonl"
    for job in jobs:
        data, h = call(endpoint, {"country": "vn", "select": select, **job["params"]})
        actual = int(h.get("x-api-units-cost-total-actual", h.get("x-api-units-cost-total", 0)) or 0)
        spent += actual
        ledger(log, {"endpoint": endpoint, "tag": job["tag"], "rows": h.get("x-api-rows"),
                     "units_row": h.get("x-api-units-cost-row"), "units_total": h.get("x-api-units-cost-total"),
                     "units_actual": actual, "cache": h.get("x-api-cache")})
        for k in data.get("keywords", []):
            result.append({"keyword": k.get("keyword"), "volume": k.get("volume"),
                           "volume_sheet": sheet_volume(k.get("volume")), "source": job["tag"]})
        if spent > approve:
            sys.exit(f"Dừng: đã tốn {spent} units vượt approve {approve}. Kết quả một phần ở {out}")
        time.sleep(1)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"units_spent": spent, "keywords": result}, f, ensure_ascii=False, indent=1)
    print(f"Xong: {len(result)} keyword, đã tốn {spent}/{approve} units. Ledger: {log}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estimate"); e.add_argument("--limit", type=int, required=True)
    e.add_argument("--requests", type=int, default=1); e.add_argument("--select", default=DEFAULT_SELECT)
    m = sub.add_parser("matching"); m.add_argument("--seeds", nargs="+", required=True)
    m.add_argument("--limit", type=int, default=30); m.add_argument("--select", default=DEFAULT_SELECT)
    m.add_argument("--mode", choices=["terms", "phrase"], default="terms")
    m.add_argument("--out", required=True); m.add_argument("--approve", type=int)
    o = sub.add_parser("overview"); o.add_argument("--keywords-file", required=True)
    o.add_argument("--select", default=DEFAULT_SELECT); o.add_argument("--chunk", type=int, default=OVERVIEW_CHUNK)
    o.add_argument("--out", required=True); o.add_argument("--approve", type=int)
    sub.add_parser("smoke")
    a = ap.parse_args()

    if a.cmd == "estimate":
        print(f"{a.requests} request × {a.limit} dòng × {per_row_cost(a.select)} = {units(a.select, a.limit) * a.requests} units")
    elif a.cmd == "matching":
        if a.select != DEFAULT_SELECT:
            print(f"CẢNH BÁO: select khác '{DEFAULT_SELECT}' — cột difficulty/intents... tốn 10 units/dòng mà thường không cần")
        jobs = [{"tag": s, "params": {"keywords": s, "limit": a.limit, "order_by": "volume:desc", "match_mode": a.mode}}
                for s in a.seeds]
        run("matching-terms", jobs, a.select, a.approve, a.out, a.limit)
    elif a.cmd == "overview":
        kws = [l.strip() for l in open(a.keywords_file, encoding="utf-8") if l.strip()]
        jobs = [{"tag": f"chunk{i // a.chunk}", "params": {"keywords": ",".join(kws[i:i + a.chunk])}}
                for i in range(0, len(kws), a.chunk)]
        est_rows = a.chunk
        run("overview", jobs, a.select, a.approve, a.out, est_rows)
    else:  # smoke: 0 units (keyword chỉ gồm ahrefs/yep/firehose). Đối chiếu bảng giá với header thật.
        probes = [  # (endpoint, params, select) — dòng đủ nhiều/cột đủ đắt để vượt sàn 50 units
            ("matching-terms", {"keywords": "ahrefs", "limit": 100}, DEFAULT_SELECT),
            ("overview", {"keywords": "ahrefs,yep,firehose"}, "keyword,volume,difficulty,global_volume,traffic_potential,intents"),
        ]
        for ep, extra, sel in probes:
            _, h = call(ep, {"country": "vn", "select": sel, **extra})
            real, want = int(h.get("x-api-units-cost-row", -1)), per_row_cost(sel)
            print(f"{ep:15} rows={h.get('x-api-rows'):>3} units/dòng thật={real} bảng giá={want} "
                  f"actual={h.get('x-api-units-cost-total-actual')} → {'KHỚP' if real == want else 'LỆCH: sửa FIELD_COST'}")
        print("Lưu ý: request nhỏ (tổng < 50) header cost_row = 50/số dòng (sàn), không phải giá thật.")

if __name__ == "__main__":
    main()
