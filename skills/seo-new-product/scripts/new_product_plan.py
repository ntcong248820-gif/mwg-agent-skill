#!/usr/bin/env python3
"""seo-new-product: dựng file Plan SEO cho nhóm sản phẩm mới từ tab Danh_Sách_Order của file chính NH Order.

Mặc định DRY-RUN: chỉ đọc và in kế hoạch. Tạo file Drive/ghi sheet chỉ khi có --apply.

  scan                          liệt kê nhóm đang chờ plan (có URL, cột G trống)
  plan --order ORD-001          dựng kế hoạch (dry-run); thêm --apply để tạo file phụ
  briefs --order ORD-001        sinh brief 2 job Anti (research bài mới, research bài renew)
  verify-links URL [URL...]     kiểm link 200 và kiểm bài đã có trên site
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys

import order_reader as orders
from nh_order_lib import fmt_date, parse_date, url_path


def _date(s: str) -> dt.date:
    return parse_date(s)


def _print_plan(plan: dict) -> None:
    print(f"\n=== NHÓM: {plan['group']} ({plan['code']}), bắt đầu {plan['start']} ===")
    print(f"KM/thời gian: {plan['km'] or '-'}")
    print(f"Dòng cột G sẽ điền: {plan['target_rows']}")
    for u in plan["urls"]:
        kws = plan["keywords"][u["url"]]
        print(f"\n[{u['page_type']}] {url_path(u['url'])}  ({len(kws)} từ khoá)")
        for k in kws:
            print(f"   {'*' if k['main'] else ' '} {k['keyword']:<45} {k['volume']:>6}  [{k['source']}] {k.get('serp', '')}")
        tm = plan["title_meta"].get(u["url_norm"])
        if tm:
            print(f"   Title ({len(tm['title'])}): {tm['title']}")
            print(f"   Meta  ({len(tm['description'])}): {tm['description']}")
    if plan["dropped"]:
        print(f"\nTừ khoá bị loại ({len(plan['dropped'])}):")
        for d in plan["dropped"]:
            print(f"   - {d['keyword']} ({d['volume']}) -> {url_path(d['url'])}: {d['reason']}")
    print(f"\nHành_Động_SEO ({len(plan['actions'])} dòng):")
    for a in plan["actions"]:
        print(f"   {fmt_date(a['date']) or '          '} | {a['action']:<28} | {a['owner']:<14} | {a['note'][:70]}{(' | ' + a['link']) if a['link'] else ''}")
    for w in plan["warnings"]:
        print(f"CẢNH BÁO: {w}")


def _serializable(plan: dict) -> dict:
    out = json.loads(json.dumps(plan, default=lambda o: fmt_date(o) if isinstance(o, dt.date) else str(o), ensure_ascii=False))
    return out


def cmd_scan(_args) -> int:
    rows = orders.read_orders()
    groups = orders.group_orders(rows)
    if not groups:
        print("Không có dòng nào chờ plan (mọi URL đã có link ở cột G).")
        return 0
    for g in groups:
        print(f"{g['code']}  {g['name']}  mode={g['mode']}  dòng {[r['row'] for r in g['pending']]}")
        for r in g["pending"]:
            print(f"    {r['page_type']:<9} {r['url']}")
        if g["mode"] == "extend":
            print(f"    ! nhóm đã có file Plan ({', '.join(sorted(g['links']))}): plan --apply sẽ THÊM dòng vào file đó, không tạo file mới")
    return 0


def cmd_plan(args) -> int:
    import plan_builder as pb

    rows = orders.read_orders()
    groups = orders.group_orders(rows, args.order, args.group, args.include_linked)
    if not groups:
        print("Không tìm thấy nhóm chờ plan khớp bộ lọc (nếu đã có link ở cột G, thêm --include-linked để thử/đối chiếu).")
        return 1
    if len(groups) > 1:
        print("Khớp nhiều nhóm, chọn một bằng --order/--group:", [g["name"] for g in groups])
        return 1
    extend = groups[0]["mode"] == "extend"
    if extend and len(groups[0]["links"]) != 1:
        print("Nhóm có nhiều link Plan khác nhau, không biết thêm vào file nào:", sorted(groups[0]["links"]))
        return 1
    plan = pb.build_plan(groups[0], args)
    if extend:
        print(f"\nNHÓM ĐÃ CÓ FILE PLAN: sẽ THÊM dòng cho {len(groups[0]['pending'])} URL mới vào {next(iter(groups[0]['links']))}")
    _print_plan(plan)
    if args.out:
        json.dump(_serializable(plan), open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\nĐã lưu kế hoạch: {args.out}")
    if not args.apply:
        print("\nDRY-RUN: chưa tạo file nào. Thêm --apply để tạo file phụ (cần owner đồng ý nếu không phải --test).")
        return 0
    import plan_writer as pw

    name = args.name or (f"{'[TEST] ' if args.test else ''}Plan SEO - {plan['group']}")
    if args.write_main_link and args.test:
        print("Từ chối: --test không được ghi cột G của file chính.")
        return 2
    if extend:
        link = next(iter(groups[0]["links"]))
        sid = pw.extend_plan_file(plan, link)
    else:
        sid = pw.create_plan_file(plan, name)
        link = pw.sheet_url(sid)
    if args.write_main_link:
        pw.write_main_links(plan, link, args.include_linked)
    return 0


def cmd_briefs(args) -> int:
    import research_briefs as rb

    rows = orders.read_orders()
    groups = orders.group_orders(rows, args.order, args.group, True)
    if len(groups) != 1:
        print("Chọn đúng một nhóm bằng --order/--group")
        return 1
    return rb.write_briefs(groups[0], args.out_dir)


def cmd_verify(args) -> int:
    import verify_links as vl

    return vl.main(args.urls)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan").set_defaults(fn=cmd_scan)

    pl = sub.add_parser("plan")
    pl.add_argument("--order")
    pl.add_argument("--group")
    pl.add_argument("--include-linked", action="store_true", help="tính cả dòng đã có link ở cột G (đối chiếu/thử)")
    pl.add_argument("--kw-file", help="file research từ khoá có sẵn (JSON/CSV)")
    pl.add_argument("--research", help="JSON research bài viết đã được Claude kiểm")
    pl.add_argument("--title-meta", help="JSON đề xuất Title/Meta [{url,title,description,mode,note}]")
    pl.add_argument("--start", type=_date, help="ngày dựng plan dd/mm/yyyy (mặc định hôm nay)")
    pl.add_argument("--serp", action="store_true", help="cho phép gọi SerpApi (cần --approve-serp)")
    pl.add_argument("--serp-cache")
    pl.add_argument("--approve-serp", type=int, default=0, help="số credit SerpApi owner đã duyệt")
    pl.add_argument("--max-kw", type=int, help="trần từ khoá/URL (mặc định không có trần)")
    pl.add_argument("--no-news", action="store_true", help="không thêm dòng Lên bài viết mới Tin tức")
    pl.add_argument("--out", help="lưu kế hoạch ra JSON")
    pl.add_argument("--apply", action="store_true", help="tạo file phụ thật trong Drive")
    pl.add_argument("--test", action="store_true", help="đặt tên [TEST], không cho ghi cột G")
    pl.add_argument("--name")
    pl.add_argument("--write-main-link", action="store_true", help="sau khi tạo, ghi link vào cột G của đúng dòng")
    pl.set_defaults(fn=cmd_plan)

    br = sub.add_parser("briefs")
    br.add_argument("--order")
    br.add_argument("--group")
    br.add_argument("--out-dir", required=True)
    br.set_defaults(fn=cmd_briefs)

    vl = sub.add_parser("verify-links")
    vl.add_argument("urls", nargs="+")
    vl.set_defaults(fn=cmd_verify)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
