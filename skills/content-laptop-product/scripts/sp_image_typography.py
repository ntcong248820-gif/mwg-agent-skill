"""Bộ chữ cho hình Content SP, bắt chước hệ chữ của bộ hình AI infobox TGDĐ (đo 02/11/2026 trên các workspace
infobox-laptop-mong-nhe-thoi-trang, infobox-laptop-acer-predator, infobox-laptop-do-hoa-ky-thuat):

- Tiêu đề: sans hình học nét đậm (Avenir Next Bold), VIẾT HOA, 1–2 dòng, chữ nhấn màu vàng TGDĐ #F9C80B.
- Gạch dưới tiêu đề: nền sáng là vạch xám mảnh, nền tối là vạch vàng mờ dần.
- Phụ đề: Medium, xám, từ khoá nhấn vàng đậm.
- Mục đánh số: ô vuông bo góc "01" (nền sáng: xanh đậm chữ trắng; nền tối: vàng chữ xanh đậm),
  tiêu đề mục Demi Bold VIẾT HOA, mô tả Regular xám.
- Con số lớn: số vàng nét đậm, đơn vị nhỏ hơn (16,9 mm; 1000 TOPS).
- Thanh thông số đáy: viên thuốc xanh đậm #031023 (nền sáng) / trắng mờ (nền tối), cột ngăn bằng vạch mảnh.

Cú pháp nhấn trong chuỗi: *chữ* thành màu vàng. Xuống dòng cưỡng bức: "\\n".
Chỉ vẽ chữ, khối, viền; không đụng điểm ảnh SP (compose dán SP trước, kiểm lõi SP sau cùng).
"""
import os
import re
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
ARIAL_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL_R = "/System/Library/Fonts/Supplemental/Arial.ttf"
# vai trò -> (file, index trong .ttc). Avenir Next Heavy THIẾU dấu tiếng Việt nên không dùng (kiểm bằng fontTools).
ROLES = {"title": (AVENIR, 0), "semi": (AVENIR, 2), "medium": (AVENIR, 5), "regular": (AVENIR, 7)}
FALLBACK = {"title": (ARIAL_B, 0), "semi": (ARIAL_B, 0), "medium": (ARIAL_R, 0), "regular": (ARIAL_R, 0)}

YELLOW = (249, 200, 11, 255)
NAVY = (3, 16, 35, 255)

_cache = {}


def font(role, size):
    key = (role, size)
    if key not in _cache:
        path, idx = ROLES[role] if os.path.exists(ROLES[role][0]) else FALLBACK[role]
        _cache[key] = ImageFont.truetype(path, size, index=idx)
    return _cache[key]


def missing_glyphs(text, role="title"):
    """Ký tự font không có (vẽ ra sẽ thành ô vuông). Trả '' khi không có fontTools."""
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError:
        return ""
    path, idx = ROLES[role] if os.path.exists(ROLES[role][0]) else FALLBACK[role]
    f = TTCollection(path).fonts[idx] if path.endswith(".ttc") else TTFont(path)
    cmap = f.getBestCmap()
    return "".join(sorted({c for c in text if not c.isspace() and c != "*" and ord(c) not in cmap}))


def palette(light):
    if light:
        return {"title": (15, 23, 42, 255), "sub": (51, 65, 85, 255), "desc": (71, 85, 105, 255), "acc": YELLOW,
                "acc_small": (206, 150, 0, 255),
                "badge_bg": NAVY, "badge_fg": (255, 255, 255, 255), "rule": (203, 213, 225, 255),
                "bar_bg": NAVY, "bar_fg": (255, 255, 255, 255), "bar_sub": (191, 203, 220, 255), "bar_line": (255, 255, 255, 60),
                "shadow": None}
    return {"title": (255, 255, 255, 255), "sub": (203, 213, 225, 255), "desc": (176, 190, 210, 255), "acc": YELLOW,
            "acc_small": YELLOW,
            "badge_bg": YELLOW, "badge_fg": NAVY, "rule": YELLOW,
            "bar_bg": (255, 255, 255, 26), "bar_fg": (255, 255, 255, 255), "bar_sub": (203, 213, 225, 255), "bar_line": (255, 255, 255, 50),
            "shadow": (0, 0, 0, 150)}


def plain(text):
    return text.replace("*", "").replace("\\n", " ")


def _tokens(text):
    """'Màn *OLED 2K*, 16 inch' -> [(chữ, nhấn?, dính_trái?)]. Cụm nhấn giữ thành 1 khối để không bị ngắt dòng giữa
    cụm ("RTX / SPARK"); dấu câu ngay sau cụm dính vào trước, không chèn dấu cách. '\\n' -> ('\\n', None, False)."""
    out = []
    prev_tail_space = True  # chuỗi gốc ngay trước ranh giới có khoảng trắng không
    for i, part in enumerate(text.split("*")):
        accent = i % 2 == 1
        for line_i, seg in enumerate(part.split("\\n")):
            if line_i:
                out.append(("\n", None, False))
                prev_tail_space = True
            if not seg:
                continue
            if seg.strip():
                # dính khi cả hai phía ranh giới đều không có khoảng trắng: "*1.9 kg*," hoặc "USB*4*"
                glue = bool(out) and out[-1][1] is not None and not prev_tail_space and not seg[0].isspace()
                words = [seg.strip()] if accent else seg.split()
                for k, w in enumerate(words):
                    out.append((w, accent, glue and k == 0))
            prev_tail_space = seg[-1].isspace()
    return out


def rich(canvas, x, y, text, fnt, color, acc, max_w, lh, upper=False, shadow=None, align="left", acc_font=None):
    """Vẽ chữ có nhấn, tự xuống dòng trong max_w. acc_font: font riêng cho chữ nhấn (vd đậm hơn). Trả y cuối."""
    d = ImageDraw.Draw(canvas)
    af = acc_font or fnt
    space = d.textlength(" ", font=fnt)
    # cụm nhấn quá dài cho một dòng thì tách lại thành từng từ
    toks = []
    for w, a, g in _tokens(text):
        w = w.upper() if upper else w
        if a and " " in w and d.textlength(w, font=af) > max_w:
            toks += [(p, a, g and j == 0) for j, p in enumerate(w.split())]
        else:
            toks.append((w, a, g))
    lines, cur, cur_w = [], [], 0
    for w, a, g in toks:
        if a is None:
            lines.append(cur); cur, cur_w = [], 0; continue
        ww = d.textlength(w, font=af if a else fnt)
        gap = 0 if (g or not cur) else space
        if cur and not g and cur_w + gap + ww > max_w:
            lines.append(cur); cur, cur_w, gap = [], 0, 0
        cur.append((w, a, ww, gap)); cur_w += gap + ww
    if cur:
        lines.append(cur)
    for line in lines:
        lw = sum(t[2] + t[3] for t in line)
        cx = x + (max_w - lw) / 2 if align == "center" else x
        if shadow:
            sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            sd = ImageDraw.Draw(sh)
            sx = cx
            for w, a, ww, gap in line:
                sx += gap
                sd.text((sx + 1, y + 2), w, font=af if a else fnt, fill=shadow); sx += ww
            canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)))
            d = ImageDraw.Draw(canvas)
        for w, a, ww, gap in line:
            cx += gap
            d.text((cx, y), w, font=af if a else fnt, fill=acc if a else color)
            cx += ww
        y += lh
    return y


def title(canvas, x, y, text, max_w, pal, size=44, align="left", rule=True):
    """Tiêu đề VIẾT HOA nét đậm + gạch dưới. Tự giảm cỡ để tối đa 2 dòng."""
    d = ImageDraw.Draw(canvas)
    while size > 26:
        f = font("title", size)
        words = plain(text).upper().split()
        lines, cur = 1, ""
        for w in words:
            t = (cur + " " + w).strip()
            if d.textlength(t, font=f) > max_w and cur:
                lines += 1; cur = w
            else:
                cur = t
        lines += text.count("\\n")
        if lines <= 2:
            break
        size -= 3
    f = font("title", size)
    y = rich(canvas, x, y, text, f, pal["title"], pal["acc"], max_w, int(size * 1.12), upper=True, shadow=pal["shadow"], align=align)
    if rule:
        y += 8
        rule_line(canvas, x if align == "left" else x + max_w // 2 - 120, y, min(max_w, 360 if align == "left" else 240), pal)
        y += 14
    return y


def rule_line(canvas, x, y, w, pal):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if pal["shadow"]:  # nền tối: vạch vàng mờ dần sang phải
        for i in range(w):
            a = int(230 * (1 - i / w) ** 1.4)
            d.line((x + i, y, x + i, y + 2), fill=pal["rule"][:3] + (a,))
    else:
        d.line((x, y, x + w, y), fill=pal["rule"], width=2)
    canvas.alpha_composite(layer)


def subtitle(canvas, x, y, text, max_w, pal, size=21, align="left"):
    """Phụ đề Medium; chữ nhấn đậm. Nền sáng dùng vàng đậm (acc_small) vì vàng tươi trên nền trắng chữ nhỏ khó đọc."""
    f = font("medium", size)
    return rich(canvas, x, y, text, f, pal["sub"], pal["acc_small"], max_w, int(size * 1.35), align=align,
                acc_font=font("title", size)) + 6


def tag(canvas, x, y, text, pal, size=17):
    """Viên thuốc vàng chữ xanh đậm (kiểu 'Ổ cứng SSD tốc độ cao' của bộ AI)."""
    f = font("semi", size)
    d = ImageDraw.Draw(canvas)
    w = d.textlength(plain(text), font=f)
    d.rounded_rectangle((x, y, x + w + 28, y + size + 16), (size + 16) // 2, fill=YELLOW)
    d.text((x + 14, y + 6), plain(text), font=f, fill=NAVY)
    return y + size + 16 + 14


def numbered(canvas, x, y, n, head, desc, max_w, pal, size=22):
    """Mục đánh số: ô '01' + tiêu đề VIẾT HOA + mô tả."""
    d = ImageDraw.Draw(canvas)
    b = int(size * 1.9)
    d.rounded_rectangle((x, y, x + b, y + b), 9, fill=pal["badge_bg"])
    fb = font("title", int(size * 0.95))
    s = f"{n:02d}"
    d.text((x + (b - d.textlength(s, font=fb)) / 2, y + b * 0.17), s, font=fb, fill=pal["badge_fg"])
    tx = x + b + 14
    yy = rich(canvas, tx, y + 1, head, font("semi", size), pal["title"], pal["acc_small"], max_w - b - 14, int(size * 1.25), upper=True, shadow=pal["shadow"])
    if desc:
        yy = rich(canvas, tx, yy + 2, desc, font("regular", int(size * 0.78)), pal["desc"], pal["acc_small"], max_w - b - 14, int(size * 1.05),
                  acc_font=font("semi", int(size * 0.78)))
    return max(yy, y + b) + 16


def big_number(canvas, x, y, text, pal, size=104, max_w=400):
    """'1000 TOPS' -> số vàng cỡ lớn + đơn vị nhỏ. Giảm cỡ nếu tràn max_w."""
    t = plain(text).split()
    num, unit = (t[0], " ".join(t[1:])) if t and re.match(r"^[\d.,]+[+x%]?$", t[0]) else (plain(text), "")
    d = ImageDraw.Draw(canvas)
    while True:
        fn, fu = font("title", size), font("semi", int(size * 0.36))
        w = d.textlength(num, font=fn) + (12 + d.textlength(unit, font=fu) if unit else 0)
        if w <= max_w or size <= 48:
            break
        size -= 4
    if pal["shadow"]:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((x + 2, y + 4), num, font=fn, fill=pal["shadow"])
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
        d = ImageDraw.Draw(canvas)
    d.text((x, y), num, font=fn, fill=pal["acc"])
    if unit:
        asc = fn.getmetrics()[0]
        d.text((x + d.textlength(num, font=fn) + 12, y + asc - fu.getmetrics()[0]), unit, font=fu, fill=pal["title"])
    return y + int(size * 1.08)


def spec_bar(canvas, box, items, pal, light):
    """Thanh thông số đáy: [(giá trị, nhãn)], giá trị vàng nét đậm, nhãn nhỏ, cột ngăn vạch mảnh."""
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rounded_rectangle(box, (y1 - y0) // 2 if (y1 - y0) < 90 else 22, fill=pal["bar_bg"],
                         outline=None if light else (255, 255, 255, 70), width=0 if light else 1)
    n = len(items)
    cw = (x1 - x0) / n
    for i in range(1, n):
        cx = int(x0 + i * cw)
        ld.line((cx, y0 + 16, cx, y1 - 16), fill=pal["bar_line"], width=1)
    canvas.alpha_composite(layer)
    d = ImageDraw.Draw(canvas)
    fv, fl = font("title", 22), font("regular", 15)
    for i, (val, lab) in enumerate(items):
        cx = x0 + i * cw + 22
        h = 28 + (22 if lab else 0)
        yy = y0 + ((y1 - y0) - h) / 2
        yy = rich(canvas, cx, yy, val, fv, YELLOW, YELLOW, cw - 36, 28)
        if lab:
            rich(canvas, cx, yy, lab, fl, pal["bar_sub"], YELLOW, cw - 36, 20)

