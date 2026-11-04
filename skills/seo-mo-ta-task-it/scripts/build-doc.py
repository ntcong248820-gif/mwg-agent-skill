#!/usr/bin/env python3
"""Dựng Google Doc mô tả task IT từ spec JSON (native docs.batchUpdate).

    python3 build-doc.py <spec.json> [--folder ID]                 # tạo Doc mới
    python3 build-doc.py <spec.json> --doc ID --rebuild            # xoá sạch rồi dựng lại (chỉ khi IT chưa nhận)
    python3 build-doc.py <update.json> --doc ID --append-update    # thêm dòng lịch sử + khối Update ở cuối
    python3 build-doc.py <spec.json> --doc ID --section 4.1        # dựng lại riêng 1 mục, các mục khác giữ nguyên

Cách dựng: nối từng khối vào cuối Doc. Riêng --section: xoá đúng mục đó rồi chèn tại chỗ, bằng cách
giữ cố định độ dài phần Doc phía sau mục (self.tail) — điểm chèn luôn là cuối Doc trừ tail. Đoạn văn: insertText rồi set style ngay trên range vừa
chèn — font/size/bold set tường minh từng run (đổi font hàng loạt sau đó qua API làm mất bold).
Bảng: insertTable, đọc lại Doc, điền ô ngược từ ô cuối để index phía trước không lệch.
Ảnh local: upload vào thư mục con "Ảnh mô tả", mở anyone-reader lúc chèn, chèn xong gỡ quyền.
In ra JSON {documentId, url, outline} để readback.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from mo_ta_common import cfg, gws, image_path, load_spec, parse_md, plain, walk_blocks
from mo_ta_heading_links import link_section_refs

FONT, CODE_FONT = "Times New Roman", "Courier New"
PT = {"TITLE": 14, "HEADING_1": 13, "HEADING_2": 13, "HEADING_3": 12, "NORMAL_TEXT": 12, "CODE": 10}
BLUE = {"color": {"rgbColor": {"red": 0xC9 / 255, "green": 0xDA / 255, "blue": 0xF7 / 255}}}
GREY = {"color": {"rgbColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}}
RED = {"color": {"rgbColor": {"red": 0.8, "green": 0.0, "blue": 0.0}}}
BLACK = {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}}
u16 = lambda s: len(s.encode("utf-16-le")) // 2


class Builder:
    def __init__(self, did: str, uris: dict, px: dict | None = None):
        self.did, self.uris, self.px = did, uris, px or {}
        self.width = 468.0
        self.tail = 0  # --section: số index phía sau điểm chèn, không đổi trong lúc dựng

    # ---- API ----------------------------------------------------------------
    def get(self):
        return gws("docs", "documents", "get", params={"documentId": self.did})

    def batch(self, reqs):
        if reqs:
            gws("docs", "documents", "batchUpdate", params={"documentId": self.did}, body={"requests": reqs})

    def end(self, d=None):
        d = d or self.get()
        return d["body"]["content"][-1]["endIndex"] - 1 - self.tail

    def para_at(self, d, idx):
        """Phần tử đoạn chứa index idx (đoạn trống cuối khi dựng nối cuối Doc)."""
        return next(el for el in d["body"]["content"] if el.get("startIndex", 0) <= idx < el["endIndex"])

    def measure(self):
        s = self.get()["documentStyle"]
        is_pageless = s.get("documentFormat", {}).get("documentMode") == "PAGELESS"
        w, h = s["pageSize"]["width"]["magnitude"], s["pageSize"]["height"]["magnitude"]
        page_w = h if s.get("flipPageOrientation") else w
        self.width = page_w - s["marginLeft"]["magnitude"] - s["marginRight"]["magnitude"]
        if is_pageless:
            # Pageless mode: rộng rãi, không bị gò bó ngắt trang giấy cố định, tối thiểu 794pt (box - 14 = 780pt)
            self.width = max(self.width, 794.0)

    # ---- runs ---------------------------------------------------------------
    def lines_reqs(self, lines, start, named="NORMAL_TEXT", box=None, code=False, split=False):
        """Chèn các dòng từ start. Trả (requests, vị trí cuối), hoặc (chèn, định dạng, vị trí cuối) nếu split.

        split dùng cho đoạn ngoài bảng: style đoạn (namedStyleType) phải áp GIỮA chèn và định dạng chữ,
        áp sau thì nó đè mất font/bold vừa set (đo 09/10/2026 trên Doc test)."""
        reqs, fmt, p = [], [], start
        size = PT["CODE"] if code else PT[named]
        box = box or self.width
        for li, line in enumerate(lines):
            if li:
                reqs.append({"insertText": {"location": {"index": p}, "text": "\n"}}); p += 1
            line_start = p
            for r in line["runs"]:
                if "img" in r:
                    # không khai width: cỡ gốc (1px ≈ 0.75pt), chỉ co khi rộng hơn khung — ảnh nhỏ không bị phóng mờ
                    natural = self.px[r["img"]] * 0.75 if self.px.get(r["img"]) else box - 14
                    w = min(r.get("width") or natural, box - 14)
                    reqs.append({"insertInlineImage": {"location": {"index": p}, "uri": self.uris[r["img"]],
                                 "objectSize": {"width": {"magnitude": w, "unit": "PT"}}}})
                    p += 1
                    continue
                t = r["t"]
                if not t:
                    continue
                reqs.append({"insertText": {"location": {"index": p}, "text": t}})
                style = {"bold": bool(r.get("bold")) or named in ("TITLE", "HEADING_1", "HEADING_2", "HEADING_3"),
                         "weightedFontFamily": {"fontFamily": CODE_FONT if code else FONT},
                         "fontSize": {"magnitude": size, "unit": "PT"},
                         "foregroundColor": RED if r.get("red") else BLACK}
                fields = ["bold", "weightedFontFamily", "fontSize", "foregroundColor"]
                if r.get("link"):
                    style["link"] = {"url": r["link"]}; fields.append("link")
                fmt.append({"updateTextStyle": {"range": {"startIndex": p, "endIndex": p + u16(t)}, "textStyle": style, "fields": ",".join(fields)}})
                p += u16(t)
            if line["level"] and p > line_start:
                fmt.append({"createParagraphBullets": {"range": {"startIndex": line_start, "endIndex": p}, "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"}})
                if line["level"] >= 2:
                    # cấp 2: lùi 54/36pt; cấp 3: lùi thêm 36pt
                    start = 54 + 36 * (line["level"] - 2)
                    fmt.append({"updateParagraphStyle": {"range": {"startIndex": line_start, "endIndex": p},
                                "paragraphStyle": {"indentStart": {"magnitude": start, "unit": "PT"}, "indentFirstLine": {"magnitude": start - 18, "unit": "PT"}},
                                "fields": "indentStart,indentFirstLine"}})
        return (reqs, fmt, p) if split else (reqs + fmt, p)

    # ---- khối ---------------------------------------------------------------
    def para(self, text, named="NORMAL_TEXT", center=False):
        e = self.end()
        reqs, fmt, p = self.lines_reqs(parse_md(text), e, named, split=True)
        reqs.append({"insertText": {"location": {"index": p}, "text": "\n"}})
        ps = {"namedStyleType": named, "lineSpacing": 150,
              "spaceAbove": {"magnitude": 12 if named != "NORMAL_TEXT" else 6, "unit": "PT"},
              "spaceBelow": {"magnitude": 4 if named != "NORMAL_TEXT" else 0, "unit": "PT"}}
        fields = "namedStyleType,lineSpacing,spaceAbove,spaceBelow"
        if center:
            ps["alignment"] = "CENTER"; fields += ",alignment"
        reqs.append({"updateParagraphStyle": {"range": {"startIndex": e, "endIndex": p + 1}, "paragraphStyle": ps, "fields": fields}})
        # đoạn mới nối sau đoạn bullet kế thừa bullet — gỡ trước, bullet thật áp lại trong fmt
        reqs.append({"deleteParagraphBullets": {"range": {"startIndex": e, "endIndex": p + 1}}})
        self.batch(reqs + fmt)

    def table(self, t, code=False):
        header = t.get("header")
        rows = ([header] if header else []) + [list(r) for r in t.get("rows", [])]
        nc = len(rows[0])
        if t.get("img_row"):
            rows.append([t["img_row"]] + [""] * (nc - 1))
        nr = len(rows)
        self.finish()  # đoạn cuối còn bullet thì Docs sinh 1 dòng chấm tròn trống ngay trên bảng
        if self.tail:
            e = self.end()
            self.batch([{"insertTable": {"rows": nr, "columns": nc, "location": {"index": e}}}])
            d = self.get()
            tstart = next(el for el in d["body"]["content"] if "table" in el and el["startIndex"] >= e)["startIndex"]
        else:
            self.batch([{"insertTable": {"rows": nr, "columns": nc, "endOfSegmentLocation": {"segmentId": ""}}}])
            d = self.get()
            tstart = [el for el in d["body"]["content"] if "table" in el][-1]["startIndex"]
        if t.get("img_row") and nc > 1:
            self.batch([{"mergeTableCells": {"tableRange": {"tableCellLocation": {"tableStartLocation": {"index": tstart}, "rowIndex": nr - 1, "columnIndex": 0}, "rowSpan": 1, "columnSpan": nc}}}])
            d = self.get()
        tbl = next(el for el in d["body"]["content"] if el.get("startIndex") == tstart)
        rel = t.get("widths") or [1] * nc
        widths = [round(w / sum(rel) * (self.width - 2), 1) for w in rel]
        reqs = []
        for ri in range(nr - 1, -1, -1):
            for ci in range(nc - 1, -1, -1):
                txt = rows[ri][ci]
                if txt in ("", None):
                    continue
                s = tbl["table"]["tableRows"][ri]["tableCells"][ci]["content"][0]["startIndex"]
                box = self.width if (t.get("img_row") and ri == nr - 1) else widths[ci]
                rr, _ = self.lines_reqs(parse_md(str(txt)), s, box=box, code=code)
                reqs += rr
        for ci, w in enumerate(widths):
            reqs.append({"updateTableColumnProperties": {"tableStartLocation": {"index": tstart}, "columnIndices": [ci],
                         "tableColumnProperties": {"widthType": "FIXED_WIDTH", "width": {"magnitude": w, "unit": "PT"}}, "fields": "width,widthType"}})
        loc = lambda r, c, rs, cs: {"tableCellLocation": {"tableStartLocation": {"index": tstart}, "rowIndex": r, "columnIndex": c}, "rowSpan": rs, "columnSpan": cs}
        if header:
            reqs.append({"updateTableCellStyle": {"tableRange": loc(0, 0, 1, nc), "tableCellStyle": {"backgroundColor": BLUE}, "fields": "backgroundColor"}})
            reqs.append({"pinTableHeaderRows": {"tableStartLocation": {"index": tstart}, "pinnedHeaderRowsCount": 1}})
        if t.get("label_col"):
            reqs.append({"updateTableCellStyle": {"tableRange": loc(1 if header else 0, 0, nr - (1 if header else 0), 1), "tableCellStyle": {"backgroundColor": GREY}, "fields": "backgroundColor"}})
        if code:
            reqs.append({"updateTableCellStyle": {"tableRange": loc(0, 0, nr, nc), "tableCellStyle": {"backgroundColor": GREY}, "fields": "backgroundColor"}})
        self.batch(reqs)
        # hàng tiêu đề: đậm + giữa; cột nhãn: đậm; hàng ảnh: giữa — đọc lại index sau khi điền
        d = self.get()
        tbl = next(el for el in d["body"]["content"] if el.get("startIndex") == tstart)
        fmt = []
        for ri, row in enumerate(tbl["table"]["tableRows"]):
            for ci, c in enumerate(row["tableCells"]):
                a, b = c["startIndex"] + 1, c["endIndex"] - 1
                if b <= a:
                    continue
                if t.get("img_row") and ri == nr - 1:
                    fmt.append({"updateParagraphStyle": {"range": {"startIndex": a, "endIndex": b}, "paragraphStyle": {"alignment": "CENTER"}, "fields": "alignment"}})
                    continue
                if (header and ri == 0) or (t.get("label_col") and ci == 0):
                    fmt.append({"updateTextStyle": {"range": {"startIndex": a, "endIndex": b}, "textStyle": {"bold": True}, "fields": "bold"}})
                if header and ri == 0:
                    fmt.append({"updateParagraphStyle": {"range": {"startIndex": a, "endIndex": b}, "paragraphStyle": {"alignment": "CENTER"}, "fields": "alignment"}})
        self.batch(fmt)
        self.para("")  # đoạn trống ngăn cách sau bảng

    def finish(self):
        """Đoạn trống cuối Doc kế thừa bullet của đoạn trước khi tách dòng — gỡ đi."""
        d = self.get()
        last = self.para_at(d, self.end(d))
        p = last.get("paragraph", {})
        if "bullet" in p:
            si, ei = last.get("startIndex", 0), last.get("endIndex", 0)
            if ei > si:
                self.batch([{"deleteParagraphBullets": {"range": {"startIndex": si, "endIndex": ei}}}])

    def block(self, kind, b):
        if kind in ("h1", "h2", "h3"):
            self.para(b[kind], {"h1": "HEADING_1", "h2": "HEADING_2", "h3": "HEADING_3"}[kind])
        elif kind == "p":
            self.para(b["p"])
        elif kind == "bullets":
            self.para("\n".join(("    - " + x.strip()) if x.startswith("    ") else ("  - " + x.strip()) if x.startswith("  ") else ("- " + x)
                                 for x in b["bullets"]))
        elif kind == "table":
            self.table(b["table"])
        elif kind == "code":
            self.table({"rows": [[b["code"]]]}, code=True)
        elif kind == "img":
            w = f"|{b['width']}" if b.get("width") else ""
            self.para(f"{{img:{b['img']}{w}}}", center=True)
            if b.get("caption"):
                self.para(f"**{b['caption']}**", center=True)


# ---- khung 1-2 tự sinh ---------------------------------------------------------
def header_blocks(spec):
    i, tpl = spec["info"], spec["template"]
    lab = lambda k, v="": f"**{k}:** {v}".rstrip()
    out = [("TITLE", spec["title"])]
    if tpl in ("A", "B"):
        extra = list(i.get("extra", {}).items())
        first = lab(*extra.pop(0)) if extra else ""
        rows = [[lab("Bộ phận yêu cầu", i["bo_phan_yeu_cau"]), lab("Ngày khởi tạo mô tả", i["ngay_khoi_tao"])],
                [lab("Lead task", i["lead_task"]), lab("Support task", i.get("support_task", ""))],
                [lab("Designer", i.get("designer", "")), lab("Link design", i.get("link_design", ""))],
                [lab("Ngày bắt đầu Live task"), lab("Ngày kết thúc Live task")],
                [lab("Site áp dụng", i["site_ap_dung"]), first]]
        rows += [[lab(k, v), ""] for k, v in extra]
        rows += [[lab("Xác nhận trưởng bộ phận / trưởng nhóm"), ""], [lab("Trưởng nhóm"), lab("Ngày xác nhận")], [lab("Trưởng BP"), lab("Ngày xác nhận")]]
        hh = ["Ngày thay đổi", "Name", "Mô tả thay đổi"] if tpl == "A" else ["Ngày cập nhật", "Người cập nhật", "Nội dung cập nhật"]
        out += [("h1", "1. Thông tin yêu cầu task"), ("table", {"rows": rows}),
                ("h1", "2. Lịch sử cập nhật"),
                ("table", {"header": hh, "widths": [1, 1.3, 3], "rows": [[h["ngay"], h["name"], h["mo_ta"]] for h in spec["history"]]})]
    else:
        out += [("h1", "1. Lịch sử thay đổi"),
                ("table", {"header": ["Ngày", "Phiên bản", "Nội dung thay đổi", "Người yêu cầu", "Người xác nhận", "Note"], "widths": [1, 0.8, 3, 1.3, 1.3, 1],
                           "rows": [[h["ngay"], h.get("phien_ban", "1.0"), h["mo_ta"], h["name"], "", ""] for h in spec["history"]]}),
                ("h1", "2. Các bên yêu cầu và xác nhận"),
                ("table", {"header": ["No.", "Các bên yêu cầu", "Bộ phận", "Xác nhận", "Ngày", "Note"], "widths": [0.5, 1.6, 1.3, 1, 1, 1],
                           "rows": [["1", i["lead_task"], i["bo_phan_yeu_cau"], "", "", "Người yêu cầu"], ["2", "", "", "", "", "Trưởng nhóm"], ["3", "", "", "", "", "Trưởng BP"]]})]
    return out


def used_images(spec, blocks=None):
    import re
    keys = set()
    for kind, b in (blocks if blocks is not None else walk_blocks(spec)):
        if kind == "img":
            keys.add(b["img"])
        keys |= set(re.findall(r"\{img:([\w.\-]+)", json.dumps(b, ensure_ascii=False)))
    return sorted(keys)


def png_width(p: pathlib.Path):
    """Chiều ngang ảnh PNG (đọc header IHDR); định dạng khác trả None."""
    head = p.read_bytes()[:24]
    return int.from_bytes(head[16:20], "big") if head[:8] == b"\x89PNG\r\n\x1a\n" else None


def upload_images(spec, folder, blocks=None):
    """Upload ảnh local vào '<folder>/Ảnh mô tả', mở quyền đọc tạm. Trả (uris, file_ids, px)."""
    keys = used_images(spec, blocks)
    if not keys:
        return {}, [], {}
    q = f"name='Ảnh mô tả' and '{folder}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    found = gws("drive", "files", "list", params={"q": q, "fields": "files(id)", "supportsAllDrives": True, "includeItemsFromAllDrives": True})["files"]
    sub = found[0]["id"] if found else gws("drive", "files", "create", params={"supportsAllDrives": True},
                                           body={"name": "Ảnh mô tả", "mimeType": "application/vnd.google-apps.folder", "parents": [folder]})["id"]
    cache_p = pathlib.Path(spec["_dir"]) / ".uploaded-images.json"
    cache = json.loads(cache_p.read_text()) if cache_p.is_file() else {}
    uris, ids, px = {}, [], {}
    for k in keys:
        p = image_path(spec, k)
        px[k] = png_width(p)
        sig = f"{p}:{p.stat().st_mtime_ns}:{sub}"
        fid = cache.get(sig)
        if not fid:
            fid = gws("drive", "+upload", str(p), "--parent", sub)["id"]
            cache[sig] = fid
        gws("drive", "permissions", "create", params={"fileId": fid, "supportsAllDrives": True}, body={"type": "anyone", "role": "reader"})
        uris[k] = f"https://drive.google.com/uc?export=view&id={fid}"
        ids.append(fid)
    cache_p.write_text(json.dumps(cache, indent=1))
    return uris, ids, px


def revoke(ids):
    for fid in ids:
        gws("drive", "permissions", "delete", params={"fileId": fid, "permissionId": "anyoneWithLink", "supportsAllDrives": True}, ok_fail=True)


def outline(b: Builder):
    d = b.get()
    heads = [plain("".join(e.get("textRun", {}).get("content", "") for e in el["paragraph"]["elements"])).strip()
             for el in d["body"]["content"] if "paragraph" in el and el["paragraph"]["paragraphStyle"].get("namedStyleType", "").startswith(("HEADING", "TITLE"))]
    return {"headings": heads, "tables": sum(1 for el in d["body"]["content"] if "table" in el), "images": len(d.get("inlineObjects", {}))}


HEAD_LV = {"h1": 1, "h2": 2, "h3": 3, "HEADING_1": 1, "HEADING_2": 2, "HEADING_3": 3}


def label_re(label):
    import re
    return re.compile(rf"^\s*{re.escape(label.rstrip('.'))}(\.|\s|$)")


def spec_section(spec, label):
    """Các khối spec của mục label (vd "4.1"): từ heading của mục tới trước heading cùng / cao cấp hơn."""
    blocks, rx = list(walk_blocks(spec)), label_re(label)
    i = next((k for k, (kind, b) in enumerate(blocks) if kind in HEAD_LV and rx.match(b[kind])), None)
    if i is None:
        sys.exit(f"Spec không có mục '{label}'.")
    lv = HEAD_LV[blocks[i][0]]
    j = next((k for k in range(i + 1, len(blocks)) if blocks[k][0] in HEAD_LV and HEAD_LV[blocks[k][0]] <= lv), len(blocks))
    return blocks[i:j], lv


def doc_section(d, label, lv):
    """(start mục, start heading kế tiếp hoặc None, paragraphStyle heading kế tiếp) trong Doc."""
    rx, els = label_re(label), d["body"]["content"]
    text = lambda el: "".join(e.get("textRun", {}).get("content", "") for e in el["paragraph"]["elements"])
    style = lambda el: el["paragraph"]["paragraphStyle"].get("namedStyleType", "") if "paragraph" in el else ""
    hits = [k for k, el in enumerate(els) if HEAD_LV.get(style(el)) == lv and rx.match(text(el))]
    if len(hits) != 1:
        sys.exit(f"Doc có {len(hits)} heading khớp mục '{label}' (cần đúng 1) — sửa tay hoặc --rebuild.")
    k = hits[0]
    nxt = next((el for el in els[k + 1:] if HEAD_LV.get(style(el), 9) <= lv or style(el) == "TITLE"), None)
    return els[k]["startIndex"], (nxt["startIndex"] if nxt else None), (nxt["paragraph"]["paragraphStyle"] if nxt else None)


def rebuild_section(b: Builder, blocks, label, lv):
    d = b.get()
    s, nxt, nstyle = doc_section(d, label, lv)
    full_end = lambda d: d["body"]["content"][-1]["endIndex"] - 1
    if nxt is None:  # mục cuối Doc: xoá tới hết, dựng nối cuối như thường
        b.batch([{"deleteContentRange": {"range": {"startIndex": s, "endIndex": full_end(d)}}}])
        b.finish()
    else:
        # đoạn trống làm mốc chèn ngay trước heading kế tiếp, xoá mục cũ, mốc lùi về s
        b.batch([{"insertText": {"location": {"index": nxt}, "text": "\n"}},
                 {"deleteContentRange": {"range": {"startIndex": s, "endIndex": nxt}}}])
        d = b.get()
        b.tail = full_end(d) - s
        b.batch([{"updateParagraphStyle": {"range": {"startIndex": s, "endIndex": s + 1}, "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"}, "fields": "namedStyleType"}},
                 {"deleteParagraphBullets": {"range": {"startIndex": s, "endIndex": s + 1}}}])
    for kind, blk in blocks:
        b.block(kind, blk)
    b.finish()
    if nxt is not None:
        # bỏ đoạn mốc (gộp vào heading kế tiếp), áp lại style heading cho chắc
        m = b.end()
        b.batch([{"deleteContentRange": {"range": {"startIndex": m, "endIndex": m + 1}}}])
        keep = {k: v for k, v in nstyle.items() if k in ("namedStyleType", "lineSpacing", "spaceAbove", "spaceBelow", "alignment")}
        reqs = [{"updateParagraphStyle": {"range": {"startIndex": m, "endIndex": m + 1}, "paragraphStyle": keep, "fields": ",".join(keep)}}]
        # gộp đoạn mốc làm heading mất đậm/font/cỡ — set lại như para() set cho heading
        h = b.para_at(b.get(), m)
        named = keep.get("namedStyleType", "NORMAL_TEXT")
        if h["endIndex"] - 1 > m:
            reqs.append({"updateTextStyle": {"range": {"startIndex": m, "endIndex": h["endIndex"] - 1},
                         "textStyle": {"bold": named in ("TITLE", "HEADING_1", "HEADING_2", "HEADING_3"), "weightedFontFamily": {"fontFamily": FONT},
                                       "fontSize": {"magnitude": PT.get(named, 12), "unit": "PT"}, "foregroundColor": BLACK},
                         "fields": "bold,weightedFontFamily,fontSize,foregroundColor"}})
        b.batch(reqs)
    b.tail = 0  # finish() ở main kiểm đoạn cuối Doc như thường, không đụng đoạn cuối của mục


def append_history_row(b: Builder, u):
    d = b.get()
    cell_text = lambda c: "".join(r.get("textRun", {}).get("content", "") for p in c["content"] if "paragraph" in p for r in p["paragraph"]["elements"]).strip()
    tbl = next((el for el in d["body"]["content"] if "table" in el and cell_text(el["table"]["tableRows"][0]["tableCells"][0]).startswith("Ngày")), None)
    if not tbl:
        sys.exit("Không tìm thấy bảng lịch sử (ô đầu bắt đầu bằng 'Ngày') — thêm dòng lịch sử bằng tay.")
    nrow, ncol = len(tbl["table"]["tableRows"]), len(tbl["table"]["tableRows"][0]["tableCells"])
    b.batch([{"insertTableRow": {"tableCellLocation": {"tableStartLocation": {"index": tbl["startIndex"]}, "rowIndex": nrow - 1, "columnIndex": 0}, "insertBelow": True}}])
    vals = [u["ngay"], u["name"], u["mo_ta"]] if ncol == 3 else [u["ngay"], u.get("phien_ban", ""), u["mo_ta"], u["name"], "", ""][:ncol]
    d = b.get()
    tbl = next(el for el in d["body"]["content"] if el.get("startIndex") == tbl["startIndex"])
    row = tbl["table"]["tableRows"][-1]["tableCells"]
    reqs = []
    for ci in range(len(vals) - 1, -1, -1):
        if vals[ci]:
            rr, _ = b.lines_reqs(parse_md(vals[ci]), row[ci]["content"][0]["startIndex"])
            reqs += rr
    b.batch(reqs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--folder")
    ap.add_argument("--doc")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--append-update", action="store_true")
    ap.add_argument("--section", help='dựng lại riêng 1 mục theo số heading, vd "4.1" hoặc "5"')
    ap.add_argument("--force", action="store_true", help="rebuild dù tiêu đề Doc khác tiêu đề spec")
    a = ap.parse_args()
    spec = load_spec(a.spec)

    if a.append_update or a.rebuild or a.section:
        if not a.doc:
            sys.exit("--rebuild / --append-update / --section cần --doc ID")
        meta = gws("drive", "files", "get", params={"fileId": a.doc, "fields": "name,parents", "supportsAllDrives": True})
        folder = (meta.get("parents") or [None])[0]
        did = a.doc
        if (a.rebuild or a.section) and meta["name"].strip() != spec["title"].strip() and not a.force:
            sys.exit(f"Tiêu đề Doc '{meta['name']}' khác spec — sai Doc? Thêm --force nếu chắc.")
    else:
        folder = a.folder or cfg("drive.itSpecRoot")
        did = None

    sec = spec_section(spec, a.section) if a.section else None
    uris, ids, px = upload_images(spec, folder, sec[0] if sec else None)
    try:
        if did is None:
            did = gws("drive", "files", "create", params={"supportsAllDrives": True},
                      body={"name": spec["title"], "mimeType": "application/vnd.google-apps.document", "parents": [folder]})["id"]
        b = Builder(did, uris, px)
        if sec:
            b.measure()
            rebuild_section(b, sec[0], a.section, sec[1])
        elif a.append_update:
            b.measure()
            u = spec["update"]
            append_history_row(b, u)
            b.para(f"Update mô tả ngày {u['ngay']} - {u['name']}", "HEADING_1")
            for kind, blk in walk_blocks(spec):
                b.block(kind, blk)
        else:
            if a.rebuild:
                e = b.end()
                if e > 1:
                    b.batch([{"deleteContentRange": {"range": {"startIndex": 1, "endIndex": e}}}])
                b.finish()
            wide = any(len((blk["table"].get("header") or blk["table"]["rows"][0])) >= 3 for k, blk in walk_blocks(spec) if k == "table") or spec["template"] == "C"
            land = spec.get("orientation", "auto") == "landscape" or (spec.get("orientation", "auto") == "auto" and wide)
            b.batch([{"updateDocumentStyle": {
                "documentStyle": {
                    "documentFormat": {"documentMode": "PAGELESS"},
                    "flipPageOrientation": land
                },
                "fields": "documentFormat.documentMode,flipPageOrientation"
            }}])
            b.measure()
            for kind, blk in header_blocks(spec):
                if kind == "TITLE":
                    b.para(blk, "TITLE")
                elif kind == "table":
                    b.table(blk)
                else:
                    b.block(kind, {kind: blk})
            for kind, blk in walk_blocks(spec):
                b.block(kind, blk)
        b.finish()
        # headingId đổi sau mỗi lần dựng → gắn lại link "mục x.y" trên cả Doc
        link_section_refs(did)
    finally:
        revoke(ids)
    print(json.dumps({"documentId": did, "url": f"https://docs.google.com/document/d/{did}/edit", **outline(b)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
