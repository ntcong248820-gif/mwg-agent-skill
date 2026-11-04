#!/usr/bin/env python3
"""Kiểm spec mô tả task IT trước khi gửi red-team / dựng Doc.

    python3 lint-spec.py <spec.json> [--md <preview.md>]

Exit 0: không lỗi (có thể còn WARN). Exit 1: còn ERROR — sửa spec rồi chạy lại.
--md: xuất bản preview markdown (owner đọc, red-team đọc) — không cần mạng.
"""
from __future__ import annotations

import argparse
import re
import sys

from mo_ta_common import DATE_RE, PERSON_RE, image_path, load_spec, plain, walk_blocks

# Heading bắt buộc theo khung (regex, không phân biệt hoa thường, so trên chữ thuần).
REQUIRED = {
    "A": [r"mô tả chi tiết yêu cầu", r"mục đích task", r"phạm vi áp dụng", r"chi tiết task", r"tiêu chí nghiệm thu"],
    "B": [r"mục đích task", r"xác định vấn đề", r"giải pháp đề xuất", r"phạm vi áp dụng", r"mô tả chi tiết", r"tiêu chí nghiệm thu"],
    "C": [r"yêu cầu kinh doanh", r"phạm vi", r"(business rules|rule nghiệp vụ|rule)", r"tiêu chí nghiệm thu"],
}
# Câu kể SEO đã làm gì / xưng hô — owner chê "dư thừa" (28/09/2026), IT không cần.
BANNED = [
    (r"\bSEO đã (sửa|gỡ|chọn|gom|rà|lọc|ghép)", "kể SEO đã làm gì — IT chỉ cần nhu cầu + data"),
    (r"\bchúng tôi\b|\bchúng ta\b", "xưng 'chúng tôi' — viết câu không chủ ngữ hoặc 'IT …'"),
    (r"(?<![\wÀ-ỹ])(bạn|mình)(?![\wÀ-ỹ])", "xưng hô 'bạn/mình' — bỏ"),
    (r"\bTODO\b|\?\?\?|xxx", "còn chỗ chưa điền"),
]
CURRENT = re.compile(r"hiện (tại|trạng)|trong cms", re.I)
WANT = re.compile(r"mong muốn|sau (điều chỉnh|khi)|đề xuất", re.I)
# Caption "Ảnh n - …" = chỗ đặt ảnh; "Ảnh n" không kèm gạch = chỗ nhắc tới ảnh.
CAPTION_RE = re.compile(r"Ảnh\s+(\d+)\s*[-–]")
MENTION_RE = re.compile(r"Ảnh\s+(\d+)(?!\s*[-–\d])")
# Owner chê 03/11/2026: ảnh một chỗ, chữ một chỗ, người đọc phải kéo đi kéo về.
# Cho phép ảnh cùng khối với chữ nhắc (trong ô bảng) hoặc là khối liền trước / liền sau.
MAX_IMAGE_GAP = 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--md")
    a = ap.parse_args()
    spec = load_spec(a.spec)
    err, warn = [], []
    tpl = spec.get("template")
    if tpl not in REQUIRED:
        err.append("template phải là A | B | C")
        tpl = "A"

    title = spec.get("title", "")
    if not re.match(r"^\[[^\]]+\]", title):
        err.append("title phải mở bằng [Site], vd '[TGDĐ - ĐMX] Lấy lên khai báo …'")

    info = spec.get("info", {})
    for k in ("bo_phan_yeu_cau", "ngay_khoi_tao", "lead_task", "site_ap_dung"):
        if not str(info.get(k, "")).strip():
            err.append(f"info.{k} trống")
    if info.get("ngay_khoi_tao") and not DATE_RE.match(info["ngay_khoi_tao"]):
        err.append("info.ngay_khoi_tao phải dd/mm/yyyy")
    for k in ("lead_task", "support_task"):
        v = str(info.get(k, "")).strip()
        if v and not all(PERSON_RE.match(x.strip()) for x in v.split(",")):
            err.append(f"info.{k} phải dạng 'Tên - MãNV' (nhiều người cách dấu phẩy): {v!r}")
    for k in info:
        if re.search(r"xac_nhan|dong_y|truong_bp|truong_nhom", k):
            err.append(f"info.{k}: agent không tự điền ô duyệt/xác nhận — để trống cho sếp")

    hist = spec.get("history", [])
    if not hist:
        err.append("history trống — dòng đầu là 'Khởi tạo tài liệu'")
    else:
        if not str(hist[0].get("mo_ta", "")).lower().startswith("khởi tạo"):
            warn.append("history[0].mo_ta nên là 'Khởi tạo tài liệu'")
        for h in hist:
            if not DATE_RE.match(str(h.get("ngay", ""))):
                err.append(f"history.ngay phải dd/mm/yyyy: {h.get('ngay')!r}")

    # Gom chữ theo heading để kiểm từng mục
    headings, sections, cur = [], {}, "_"
    tables, imgs, urls = [], [], 0
    for kind, b in walk_blocks(spec):
        if kind in ("h1", "h2", "h3"):
            cur = plain(b[kind]); headings.append((kind, cur)); sections[cur] = []
            continue
        txt = ""
        if kind == "p": txt = b["p"]
        elif kind == "bullets": txt = "\n".join(b["bullets"])
        elif kind == "code": txt = b["code"]
        elif kind == "img":
            imgs.append(b["img"]); txt = b.get("caption", "")
        elif kind == "table":
            t = b["table"]; tables.append((cur, t))
            txt = "\n".join([" | ".join(t.get("header", []))] + [" | ".join(map(str, r)) for r in t.get("rows", [])] + [t.get("img_row", "")])
            imgs += re.findall(r"\{img:([\w.\-]+)", txt)
        imgs += re.findall(r"\{img:([\w.\-]+)", txt) if kind != "table" else []
        urls += len(re.findall(r"https?://", txt))
        sections.setdefault(cur, []).append(txt)

    names = [h for _, h in headings]
    for pat in REQUIRED[tpl]:
        if not any(re.search(pat, h, re.I) for h in names):
            err.append(f"thiếu mục bắt buộc của khung {tpl}: /{pat}/")
    nums = [re.match(r"^([\dA-Z]+(\.\d+)*)[.\s]", h) for h in names]
    seen = set()
    for m, h in zip(nums, names):
        if m and m.group(1) in seen and not re.search(r"update", h, re.I):
            warn.append(f"đánh số heading trùng: {m.group(1)} ({h})")
        if m: seen.add(m.group(1))

    def section_text(pat):
        return "\n".join(t for h, ts in sections.items() if re.search(pat, h, re.I) for t in ts)

    if tpl == "A":
        md = section_text(r"mục đích task")
        for lab in ("Mục đích", "Hiện tại", "Mong muốn"):
            if lab.lower() not in md.lower():
                warn.append(f"3.1 Mục đích task thiếu nhãn '{lab}:'")
        if "=>" not in md:
            warn.append("3.1 nên kết bằng dòng '=> hệ quả SEO' in đậm")
    if tpl in ("A", "B"):
        ok = any(CURRENT.search(" ".join(t.get("header", []))) and WANT.search(" ".join(t.get("header", []))) for _, t in tables)
        if not ok:
            warn.append("chưa có bảng 'Hiện tại | Mong muốn' nào trong phần chi tiết")
    # owner 03/11/2026: "Hiện tại:" và "Sau khi / Mong muốn:" chung một ô thì IT khó đọc → tách cột
    both = re.compile(r"\*\*\s*Hiện tại\s*:?\s*\*\*.*\*\*\s*(Sau khi[^*]*|Mong muốn)\s*:?\s*\*\*", re.I | re.S)
    for h, t in tables:
        for row in t.get("rows", []):
            for cell in row:
                if isinstance(cell, str) and both.search(cell):
                    err.append(f"ô bảng ({h}) gộp nhãn 'Hiện tại' với 'Sau khi / Mong muốn' — tách thành 2 cột 'Hiện tại | Sau khi bổ sung'")
                    break
        # vùng giữ nguyên không phải việc của IT → không thành dòng bảng
        hdr = " ".join(t.get("header", []))
        if CURRENT.search(hdr) and re.search(r"sau khi|mong muốn", hdr, re.I):
            for row in t.get("rows", []):
                if len(row) > 2 and re.match(r"^\s*(-\s*)?Không đổi", str(row[-1]), re.I):
                    warn.append(f"dòng '{str(row[0]).splitlines()[0]}' ({h}) ghi 'Không đổi' — vùng IT không phải đụng thì bỏ khỏi bảng, rule cần giữ chuyển vào mục giao diện")
    if tpl == "B":
        n_img = len(set(imgs))
        if n_img < 3:
            warn.append(f"khung B có {n_img} ảnh (<3: hiện tại + vùng khai báo + mong muốn) — dựng ảnh theo SKILL bước 3 / references/dung-anh-minh-hoa.md")
    if tpl in ("A", "B"):
        want_tables = [t for _, t in tables if WANT.search(" ".join(t.get("header", [])))]
        if want_tables and not any("{img:" in (t.get("img_row", "") + str(t.get("rows", ""))) for t in want_tables):
            warn.append("bảng 'Mong muốn' không có ảnh nào — chụp ảnh thật hoặc giả lập (ghi 'Minh hoạ'), xem references/dung-anh-minh-hoa.md")
    acc = [t for h, t in tables if re.search(r"tiêu chí nghiệm thu", h, re.I)]
    if not acc:
        err.append("mục Tiêu chí nghiệm thu phải có bảng 'Hạng mục | Kết quả mong muốn'")
    elif len(acc[0].get("rows", [])) < 3:
        warn.append("Tiêu chí nghiệm thu < 3 dòng — thêm case biên (trống dữ liệu, trang lỗi, mobile…)")
    if urls == 0:
        err.append("không có URL ví dụ nào — mỗi rule cần ít nhất 1 URL thật")

    full = "\n".join(t for ts in sections.values() for t in ts) + "\n" + title
    for pat, why in BANNED:
        for m in re.finditer(pat, full, re.I):
            warn.append(f"'{m.group(0)}': {why}")
    check_image_flow(spec, err, warn)
    for k in sorted(set(imgs)):
        try:
            if not image_path(spec, k).is_file():
                err.append(f"ảnh {k}: file không tồn tại ({image_path(spec, k)})")
        except KeyError as e:
            err.append(str(e))

    tr = spec.get("tracker")
    if not tr:
        warn.append("chưa có khối tracker — không thêm được dòng sheet")
    else:
        for k in ("tab", "uu_tien", "site", "du_an", "pic", "loai_task", "muc_dich", "phu_trach"):
            if not str(tr.get(k, "")).strip():
                err.append(f"tracker.{k} trống")
        if len(str(tr.get("muc_dich", ""))) > 900:
            warn.append("tracker.muc_dich dài — cột H nên 2–4 câu")

    if a.md:
        write_preview(spec, a.md)
    for w in warn: print("WARN ", w)
    for e in err: print("ERROR", e)
    print(f"{'FAIL' if err else 'OK'}: {len(err)} lỗi, {len(warn)} cảnh báo, {len(headings)} heading, {len(tables)} bảng, {len(set(imgs))} ảnh, {urls} URL")
    sys.exit(1 if err else 0)


def block_text(kind, b):
    if kind == "img": return b.get("caption", "")
    if kind == "table":
        t = b["table"]
        return "\n".join(map(str, t.get("header", []) + [c for r in t.get("rows", []) for c in r] + [t.get("img_row", "")]))
    if kind == "bullets": return "\n".join(b["bullets"])
    return str(b.get(kind, ""))


def check_image_flow(spec, err, warn):
    """Ảnh phải nằm ngay cạnh chữ nhắc tới nó, và đánh số theo thứ tự xuất hiện."""
    placed, mentions, heading = {}, [], "_"
    for i, (kind, b) in enumerate(walk_blocks(spec)):
        txt = block_text(kind, b)
        if kind in ("h1", "h2", "h3"):
            heading = plain(b[kind])
        for n in CAPTION_RE.findall(txt):
            placed.setdefault(int(n), (i, heading))
        for n in MENTION_RE.findall(txt):
            mentions.append((int(n), i, heading))
    order = list(placed)
    if order != sorted(order):
        err.append(f"số ảnh không theo thứ tự xuất hiện trong Doc ({order}) — đánh lại số từ trên xuống")
    for n, i, h in mentions:
        if n not in placed:
            warn.append(f"mục '{h}' nhắc Ảnh {n} nhưng không có caption 'Ảnh {n} - …'")
            continue
        j, hj = placed[n]
        if abs(i - j) > MAX_IMAGE_GAP:
            err.append(f"mục '{h}' nhắc Ảnh {n} nhưng ảnh đặt ở mục '{hj}' (cách {abs(i - j)} khối) — "
                       "đặt ảnh ngay dưới đoạn nhắc tới nó, hoặc bỏ câu nhắc; xem quy-tac-viet-va-trinh-bay.md mục Luồng đọc")


def write_preview(spec, out):
    L = [f"# {spec.get('title','')}", "", f"_Khung {spec.get('template')}_", ""]
    info = spec.get("info", {})
    L += ["## Thông tin yêu cầu task", ""] + [f"- **{k}**: {v}" for k, v in info.items() if k != "extra"]
    L += [f"- **{k}**: {v}" for k, v in info.get("extra", {}).items()] + ["", "## Lịch sử cập nhật", ""]
    L += [f"- {h.get('ngay')} | {h.get('name')} | {h.get('mo_ta')}" for h in spec.get("history", [])] + [""]
    for kind, b in walk_blocks(spec):
        if kind in ("h1", "h2", "h3"):
            L += ["#" * (int(kind[1]) + 1) + " " + b[kind], ""]
        elif kind == "p": L += [b["p"], ""]
        elif kind == "bullets": L += [("    - " + x.strip()) if x.startswith("    ") else ("  - " + x.strip()) if x.startswith("  ") else ("- " + x)
                                    for x in b["bullets"]] + [""]
        elif kind == "code": L += ["```", b["code"], "```", ""]
        elif kind == "img": L += [f"[Ảnh {b['img']}] {b.get('caption','')}", ""]
        elif kind == "table":
            t = b["table"]; h = t.get("header") or [""] * len(t["rows"][0])
            cell = lambda c: str(c).replace("\n", "<br>")
            L += ["| " + " | ".join(h) + " |", "|" + " --- |" * len(h)]
            L += ["| " + " | ".join(cell(c) for c in r) + " |" for r in t.get("rows", [])]
            if t.get("img_row"): L += [f"| {cell(t['img_row'])} |"]
            L += [""]
    tr = spec.get("tracker")
    if tr:
        L += ["## Dòng sheet tổng hợp", ""] + [f"- **{k}**: {v}" for k, v in tr.items()]
    open(out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("preview:", out)


if __name__ == "__main__":
    main()
