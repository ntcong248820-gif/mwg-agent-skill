#!/usr/bin/env python3
"""Gắn link heading cho mọi chỗ nhắc "mục 4.1", "mục 4.3, 4.4", "mục 4.1 – 4.4" trong Doc.

Owner 04/11/2026: người đọc bấm "mục xxx" là nhảy tới đúng mục. headingId đổi mỗi lần dựng lại
heading, nên build-doc.py gọi hàm này sau mọi lần dựng (full, --rebuild, --section); chạy lại
nhiều lần vẫn cho cùng kết quả.

Chạy riêng trên Doc có sẵn:
  python3 mo_ta_heading_links.py --doc ID [--dry-run]
"""
from __future__ import annotations

import argparse
import re

from mo_ta_common import gws

# "mục 4.1" rồi các số nối tiếp bằng "," / "–" / "-" / "và": mỗi số link về heading của nó
REF = re.compile(r"[Mm]ục\s+\d+(?:\.\d+)*(?:\s*(?:,|–|-|và)\s*\d+(?:\.\d+)*)*")
NUM = re.compile(r"\d+(?:\.\d+)*")
HEAD_NUM = re.compile(r"^(\d+(?:\.\d+)*)\.?\s")


def u16(s: str) -> int:
    return len(s.encode("utf-16-le")) // 2


def paragraphs(content):
    """Mọi paragraph trong thân Doc, kể cả trong ô bảng."""
    for el in content:
        if "paragraph" in el:
            yield el["paragraph"]
        elif "table" in el:
            for row in el["table"]["tableRows"]:
                for cell in row["tableCells"]:
                    yield from paragraphs(cell["content"])


def para_text(p) -> str:
    # phần tử không phải chữ (ảnh inline…) chiếm 1 index → giữ chỗ bằng 1 ký tự
    return "".join(e["textRun"]["content"] if "textRun" in e else "￼" for e in p["elements"])


def heading_ids(d) -> dict[str, str]:
    out = {}
    for p in paragraphs(d["body"]["content"]):
        ps = p.get("paragraphStyle", {})
        if ps.get("namedStyleType", "").startswith("HEADING") and ps.get("headingId"):
            m = HEAD_NUM.match(para_text(p).strip())
            if m:
                out.setdefault(m.group(1), ps["headingId"])
    return out


def link_requests(d) -> list[dict]:
    heads = heading_ids(d)
    reqs = []
    for p in paragraphs(d["body"]["content"]):
        if p.get("paragraphStyle", {}).get("namedStyleType", "").startswith("HEADING"):
            continue
        text = para_text(p)
        base = p["elements"][0]["startIndex"]
        for m in REF.finditer(text):
            first = True
            for n in NUM.finditer(m.group()):
                hid = heads.get(n.group())
                if not hid:
                    first = False
                    continue
                # số đầu link cả chữ "mục": vùng bấm rộng, dễ thấy
                s = m.start() if first else m.start() + n.start()
                e = m.start() + n.end()
                first = False
                reqs.append({"updateTextStyle": {
                    "range": {"startIndex": base + u16(text[:s]), "endIndex": base + u16(text[:e])},
                    "textStyle": {"link": {"headingId": hid}}, "fields": "link"}})
    return reqs


def link_section_refs(did: str, dry_run: bool = False) -> int:
    d = gws("docs", "documents", "get", params={"documentId": did})
    reqs = link_requests(d)
    if reqs and not dry_run:
        gws("docs", "documents", "batchUpdate", params={"documentId": did},
            body={"requests": reqs, "writeControl": {"requiredRevisionId": d["revisionId"]}})
    return len(reqs)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    print(f"{'(dry-run) ' if a.dry_run else ''}link heading: {link_section_refs(a.doc, a.dry_run)}")
