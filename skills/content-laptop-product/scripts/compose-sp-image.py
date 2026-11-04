#!/usr/bin/env python3
"""Dựng hình Content SP từ ảnh gallery thật, xử lý xác định. KHÔNG dùng AI sinh/sửa ảnh.
Chữ theo hệ chữ của bộ hình AI infobox TGDĐ (xem sp_image_typography.py).

Dùng:
  compose-sp-image.py --src gallery.jpg [--src ...] --out ra.jpg --layout KIỂU
      [--headline "Màn hình *OLED* 16 inch"] [--sub "..."] [--tag "..."] [--callout "Tiêu đề|Mô tả" ...]
      [--zoom X0,Y0,X1,Y1] [--bg gradient|shapes|split|spotlight|light] [--palette ...]
      [--article bai.html] [--report ra.json]
Chữ: *từ* thành màu vàng nhấn; "\\n" xuống dòng. Tiêu đề tự VIẾT HOA.

Bố cục (--layout), mỗi hình trong một bài dùng một kiểu khác nhau (check-image-set.py kiểm):
  right / left  SP một bên; tiêu đề + phụ đề + mục đánh số 01/02/03 bên kia
  center        tiêu đề giữa trên, SP dưới (dùng ít)
  hero          con số lớn vàng (callout đầu, vd "1000 TOPS") + SP, hợp mục chip, màn hình, pin
  strip         SP giữa, thanh thông số xanh đậm 2–4 cột ở chân, hợp mục cấu hình, kết nối
  zoom          SP + thẻ phóng chi tiết cắt từ CHÍNH ảnh gốc (--zoom, toạ độ điểm ảnh gốc) + mục đánh số
  multi         2–3 ảnh gallery khác góc, tiêu đề giữa + nhãn vàng (--tag), chú thích dưới từng ảnh

Ra: JPG đúng --size, bản PNG không nén (-lossless.png) + report JSON có `placements` để verify-sp-fidelity.py kiểm
độc lập. Exit 0 = đạt; 1 = không đạt; 2 = lỗi đầu vào.
"""
import argparse, hashlib, html, json, os, re, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sp_image_lib as L  # noqa: E402
import sp_image_typography as T  # noqa: E402

LAYOUTS = ["right", "left", "center", "hero", "strip", "zoom", "multi"]
MAX_CALLOUTS = {"strip": 4, "multi": 3}


def numbers_not_in_article(texts, article_path):
    art = html.unescape(re.sub(r"<[^>]+>", " ", open(article_path, encoding="utf8").read()))
    art_n = re.sub(r"\s+", "", art.lower())
    return [f"chữ trên ảnh có số '{tok}' không có trong bài" for t in texts for tok in re.findall(r"\d+(?:[.,]\d+)*", T.plain(t)) if tok not in art_n]


def place_cutout(canvas, cut, box, align="center", valign="center", shadow=0.0):
    """Co SP vừa khung box=(x,y,w,h) rồi dán. Trả placement dict."""
    x, y, w, h = box
    s = L.fit(cut["rgba"].size, w, h)
    nw, nh = max(1, round(cut["rgba"].size[0] * s)), max(1, round(cut["rgba"].size[1] * s))
    ox = {"left": x, "right": x + w - nw}.get(align, x + (w - nw) // 2)
    oy = {"top": y, "bottom": y + h - nh}.get(valign, y + (h - nh) // 2)
    prod = cut["rgba"].resize((nw, nh), Image.LANCZOS)
    if shadow:
        L.drop_shadow(canvas, prod, ox, oy, shadow)
    canvas.alpha_composite(prod, (ox, oy))
    return {"kind": "cutout", "crop_box": cut["crop_box"], "placed": [ox, oy, nw, nh], "scale": round(s, 4),
            "_core": ndi.binary_erosion(np.asarray(prod)[..., 3] == 255, iterations=4),
            "_ref": cut["orig"].resize((nw, nh), Image.LANCZOS)}


def place_detail(canvas, src, zbox, card, light):
    """Thẻ trắng bo góc chứa vùng cắt nguyên trạng từ ảnh gốc (không tách nền), chỉ co, không phóng."""
    x0, y0, x1, y1 = card
    L.rounded_card(canvas, card, 18, (255, 255, 255, 255), outline=None if light else (249, 200, 11, 255))
    inner_w, inner_h = x1 - x0 - 20, y1 - y0 - 20
    crop = src.crop(tuple(zbox))
    s = L.fit(crop.size, inner_w, inner_h)
    nw, nh = round(crop.size[0] * s), round(crop.size[1] * s)
    det = crop.resize((nw, nh), Image.LANCZOS)
    ox, oy = x0 + 10 + (inner_w - nw) // 2, y0 + 10 + (inner_h - nh) // 2
    canvas.alpha_composite(det.convert("RGBA"), (ox, oy))
    return {"kind": "detail", "crop_box": list(zbox), "placed": [ox, oy, nw, nh], "scale": round(s, 4),
            "_core": np.ones((nh, nw), bool), "_ref": det}


def split_callout(c):
    t, _, d = c.partition("|")
    return t.strip(), d.strip()


def text_column(canvas, x, y, w, a, callouts, pal, title_size=42):
    """Cột chữ chuẩn: nhãn vàng, tiêu đề, phụ đề, mục đánh số."""
    if a.tag:
        y = T.tag(canvas, x, y, a.tag, pal)
    if a.headline:
        y = T.title(canvas, x, y, a.headline, w, pal, size=title_size)
    if a.sub:
        y = T.subtitle(canvas, x, y, a.sub, w, pal)
    y += 10
    for i, (t, d) in enumerate(callouts):
        y = T.numbered(canvas, x, y, i + 1, t, d, w, pal, size=20)
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", action="append", required=True, help="ảnh gallery; --layout multi nhận 2–3 lần")
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", default="1020x570")
    ap.add_argument("--layout", choices=LAYOUTS, default="right")
    ap.add_argument("--headline", default="", help="tiêu đề VIẾT HOA, *nhấn vàng*")
    ap.add_argument("--sub", default="", help="phụ đề 1 câu, *nhấn vàng*")
    ap.add_argument("--tag", default="", help="nhãn vàng nhỏ (vd 'Bản lề xoay gập 360°')")
    ap.add_argument("--callout", action="append", default=[], help="'Tiêu đề|Mô tả' (mô tả tuỳ chọn)")
    ap.add_argument("--zoom", help="X0,Y0,X1,Y1 vùng chi tiết trên ảnh gốc (layout zoom)")
    ap.add_argument("--bg", choices=L.BG_STYLES, default="gradient")
    ap.add_argument("--palette", default="night", help="|".join(list(L.PALETTES) + ["auto"]))
    ap.add_argument("--bg-from")
    ap.add_argument("--bg-to")
    ap.add_argument("--no-shadow", action="store_true")
    ap.add_argument("--bg-tol", type=int, default=40)
    ap.add_argument("--rim", type=int, default=2)
    ap.add_argument("--clear-at", action="append", default=[], metavar="I:X,Y",
                    help="xoá vùng trắng kín chứa điểm X,Y (toạ độ ảnh gốc) của --src thứ I (từ 0), vd khe bản lề. "
                         "Lấy seed từ enclosed trong report sau khi nhìn ảnh; không bao giờ xoá đoán")
    ap.add_argument("--article", help="HTML bài; mọi số trong chữ trên ảnh phải có trong bài")
    ap.add_argument("--max-kb", type=int, default=250)
    ap.add_argument("--report")
    a = ap.parse_args()
    W, H = (int(x) for x in a.size.lower().split("x"))
    problems, warnings = [], []

    n_src = len(a.src)
    if (a.layout == "multi") != (n_src > 1) or n_src > 3:
        print("--layout multi cần 2–3 --src; các kiểu khác đúng 1 --src", file=sys.stderr); return 2
    if len(a.callout) > MAX_CALLOUTS.get(a.layout, 3):
        print(f"{a.layout}: tối đa {MAX_CALLOUTS.get(a.layout, 3)} callout", file=sys.stderr); return 2
    if a.layout == "zoom" and not a.zoom:
        print("--layout zoom cần --zoom X0,Y0,X1,Y1", file=sys.stderr); return 2
    if a.layout == "hero" and not a.callout:
        print("--layout hero cần ít nhất 1 callout (callout đầu là con số lớn)", file=sys.stderr); return 2
    if a.palette != "auto" and a.palette not in L.PALETTES:
        print(f"--palette không có: {a.palette}", file=sys.stderr); return 2
    all_text = [a.headline, a.sub, a.tag] + a.callout
    if a.article:
        problems += numbers_not_in_article(all_text, a.article)
    miss = T.missing_glyphs("".join(all_text), "title") + T.missing_glyphs("".join(all_text), "regular")
    if miss:
        problems.append(f"font thiếu ký tự (sẽ ra ô vuông): {''.join(sorted(set(miss)))}")

    clear = {}
    for c in a.clear_at:
        i, _, xy = c.partition(":")
        clear.setdefault(int(i), []).append(tuple(int(v) for v in xy.split(",")))
    srcs = []
    for k, p in enumerate(a.src):
        raw = open(p, "rb").read()
        im = Image.open(p).convert("RGB")
        cut = L.cutout(im, a.bg_tol, a.rim, clear.get(k, ()))
        if cut["edge_px"] >= 20:
            problems.append(f"{os.path.basename(p)}: SP bị cắt ở mép ảnh gốc ({cut['edge_px']} điểm), chọn ảnh khác")
        elif cut["edge_px"]:
            warnings.append(f"{os.path.basename(p)}: {cut['edge_px']} điểm SP chạm mép ảnh gốc, xem góc có bị cụt")
        if cut["cleared"]:
            warnings.append(f"{os.path.basename(p)}: đã xoá {cut['cleared']} vùng trắng kín theo --clear-at, nhìn lại SP")
        if cut["enclosed"]:
            warnings.append(f"{os.path.basename(p)} (src {k}): {len(cut['enclosed'])} vùng trắng kín giữ nguyên; lớn nhất "
                            + "; ".join(f"{e['px']} điểm bbox {e['bbox']} seed {e['seed'][0]},{e['seed'][1]}" for e in cut["enclosed"][:3]))
        srcs.append({"path": p, "sha256": hashlib.sha256(raw).hexdigest(), "size": list(im.size), "im": im, "cut": cut})

    light = a.bg == "light" or a.palette in ("light", "studio")
    if a.bg_from and a.bg_to:
        c0, c1 = a.bg_from, a.bg_to
    elif a.palette == "auto":
        c0, c1 = L.auto_palette(srcs[0]["cut"])
    else:
        c0, c1 = L.PALETTES["studio" if a.bg == "light" and a.palette not in ("light", "studio") else a.palette]
    focus = {"left": (0.3, 0.5), "zoom": (0.3, 0.55), "strip": (0.5, 0.45), "multi": (0.5, 0.5), "center": (0.5, 0.6)}.get(a.layout, (0.7, 0.55))
    canvas = L.background(W, H, a.bg, c0, c1, focus=focus, split_at=0.58 if a.layout == "left" else 0.42)
    shadow = 0.0 if a.no_shadow else (0.22 if light else 0.5)
    pal = T.palette(light)
    pad, top_safe = 34, 84  # top_safe: lề trên cho SP, chừa chỗ tiêu đề cột bên
    placements = []
    callouts = [split_callout(c) for c in a.callout]
    text_end = 0

    # SP dán trước, chữ vẽ sau ở vùng riêng; lõi SP được kiểm sau cùng nên chữ đè SP sẽ bị bắt.
    if a.layout in ("right", "left", "hero"):
        prod_left = a.layout == "left"
        col = int(W * 0.42)
        box = (pad, top_safe - 20, W - col - pad, H - top_safe - pad + 20) if prod_left else (col, top_safe, W - col - pad, H - top_safe - pad)
        placements.append(place_cutout(canvas, srcs[0]["cut"], box, align="left" if prod_left else "right", shadow=shadow))
        tx = W - col + 8 if prod_left else pad + 6
        tw = col - pad - 14
        ty = top_safe if prod_left else 52
        if a.layout == "hero":
            t0, d0 = callouts[0]
            if a.tag:
                ty = T.tag(canvas, tx, ty, a.tag, pal)
            if a.headline:
                ty = T.title(canvas, tx, ty, a.headline, tw, pal, size=32)
            ty = T.big_number(canvas, tx - 4, ty + 4, t0, pal, size=104, max_w=tw)
            if d0:
                ty = T.subtitle(canvas, tx, ty, d0, tw, pal, size=20)
            ty += 12
            for i, (t, d) in enumerate(callouts[1:]):
                ty = T.numbered(canvas, tx, ty, i + 1, t, d, tw, pal, size=19)
            text_end = ty
        else:
            text_end = text_column(canvas, tx, ty, tw, a, callouts, pal)

    elif a.layout == "center":
        ty = T.title(canvas, pad, 48, a.headline, W - 2 * pad - 90, pal, size=40, align="center") if a.headline else 48
        if a.sub:
            ty = T.subtitle(canvas, pad, ty, a.sub, W - 2 * pad, pal, align="center")
        placements.append(place_cutout(canvas, srcs[0]["cut"], (pad, ty + 10, W - 2 * pad, H - ty - 10 - pad), shadow=shadow))
        text_end = ty

    elif a.layout == "strip":
        bar_h = 92
        ty = 44
        if a.tag:
            ty = T.tag(canvas, pad + 6, ty, a.tag, pal)
        if a.headline:
            ty = T.title(canvas, pad + 6, ty, a.headline, int(W * 0.46), pal, size=38)
        if a.sub:
            ty = T.subtitle(canvas, pad + 6, ty, a.sub, int(W * 0.40), pal, size=19)
        box = (int(W * 0.40), top_safe - 10, int(W * 0.56) - pad, H - bar_h - pad - 22 - (top_safe - 10))
        placements.append(place_cutout(canvas, srcs[0]["cut"], box, valign="bottom", shadow=shadow))
        if callouts:
            T.spec_bar(canvas, (pad, H - pad - bar_h, W - pad, H - pad), callouts, pal, light)
        text_end = max(ty, H - pad)

    elif a.layout == "zoom":
        zb = [int(v) for v in a.zoom.split(",")]
        sw, sh = srcs[0]["size"]
        if not (0 <= zb[0] < zb[2] <= sw and 0 <= zb[1] < zb[3] <= sh):
            print(f"--zoom ngoài ảnh {sw}x{sh}", file=sys.stderr); return 2
        placements.append(place_cutout(canvas, srcs[0]["cut"], (pad, top_safe, int(W * 0.52) - pad, H - top_safe - pad), shadow=shadow))
        cx0, cx1 = int(W * 0.55), W - pad
        ty = top_safe - 30
        if a.tag:
            ty = T.tag(canvas, cx0, ty, a.tag, pal)
        if a.headline:
            ty = T.title(canvas, cx0, ty, a.headline, cx1 - cx0, pal, size=32)
        card_h = min(200, int((cx1 - cx0 - 20) * (zb[3] - zb[1]) / (zb[2] - zb[0])) + 20)
        card = (cx0, ty + 2, cx1, ty + 2 + card_h)
        placements.append(place_detail(canvas, srcs[0]["im"], zb, card, light))
        ty = card[3] + 20
        for i, (t, d) in enumerate(callouts):
            ty = T.numbered(canvas, cx0, ty, i + 1, t, d, cx1 - cx0, pal, size=18)
        text_end = ty
        # tiêu đề cột trái phía trên SP (nếu có --sub) để cân bố cục
        if a.sub:
            T.subtitle(canvas, pad + 6, 40, a.sub, int(W * 0.48), pal, size=19)

    else:  # multi
        ty = 38
        if a.headline:
            ty = T.title(canvas, pad + 80, ty, a.headline, W - 2 * pad - 160, pal, size=36, align="center", rule=False)
        if a.tag:
            tw_ = int(T.font("semi", 17).getlength(T.plain(a.tag))) + 28
            ty = T.tag(canvas, (W - tw_) // 2, ty + 4, a.tag, pal)
        cap_h = 66 if callouts else 0
        gap = 22
        cw = (W - 2 * pad - gap * (n_src - 1)) // n_src
        ch = H - ty - pad - cap_h - 6
        for i, s in enumerate(srcs):
            placements.append(place_cutout(canvas, s["cut"], (pad + i * (cw + gap), ty + 6, cw, ch), valign="bottom", shadow=shadow))
        cy = H - pad - cap_h + 8
        for i, (t, d) in enumerate(callouts[:n_src]):
            cx = pad + i * (cw + gap)
            T.rule_line(canvas, cx + cw // 2 - 18, cy - 6, 36, pal)
            yy = T.rich(canvas, cx, cy + 2, t, T.font("semi", 19), pal["title"], pal["acc"], cw, 24, upper=True, shadow=pal["shadow"], align="center")
            if d:
                yy = T.rich(canvas, cx, yy, d, T.font("regular", 15), pal["desc"], pal["acc_small"], cw, 20, align="center", acc_font=T.font("semi", 15))
            text_end = max(text_end, yy)

    if text_end > H - 6:
        problems.append("chữ tràn khung dưới: rút ngắn chữ")
    final = canvas.convert("RGB")

    # Kiểm giữ nguyên SP trên bản chưa nén: lõi của mỗi mảnh phải trùng ảnh gốc đã co (max diff = 0).
    rep_places = []
    for i, pl in enumerate(placements):
        ox, oy, nw, nh = pl["placed"]
        fin = np.asarray(final.crop((ox, oy, ox + nw, oy + nh))).astype(int)
        ref = np.asarray(pl["_ref"].convert("RGB")).astype(int)
        core = pl["_core"]
        diff = np.abs(fin - ref).max(axis=2)
        n = int(core.sum())
        maxd = int(diff[core].max()) if n else -1
        if n == 0 or maxd != 0:
            problems.append(f"mảnh {i} ({pl['kind']}): lõi SP không trùng ảnh gốc (max diff {maxd}, {int((diff[core] > 0).sum())} điểm), chữ đè lên SP?")
        src = srcs[0] if pl["kind"] == "detail" or len(srcs) == 1 else srcs[i]
        cb = pl["crop_box"]
        rep_places.append({"kind": pl["kind"], "src": src["path"], "src_sha256": src["sha256"], "crop_box": cb, "placed": pl["placed"],
                           "enclosed_white": src["cut"]["enclosed"] if pl["kind"] == "cutout" else [],
                           "scale": pl["scale"], "aspect_before": round((cb[2] - cb[0]) / (cb[3] - cb[1]), 4),
                           "aspect_after": round(nw / nh, 4), "core_pixels": n, "core_max_diff": maxd})

    lossless_path = os.path.splitext(a.out)[0] + "-lossless.png"
    final.save(lossless_path, "PNG")
    # JPG 4:4:4 (không gộp màu) để mép chữ vàng/chi tiết SP không nhoè; chọn chất lượng thấp nhất đạt PSNR >= 34 dB
    # so với bản PNG (verify đòi >= 33) mà vẫn <= --max-kb.
    ref_px = np.asarray(final).astype(float)
    for q in (88, 91, 94, 96):
        final.save(a.out, "JPEG", quality=q, optimize=True, progressive=True, subsampling=0)
        mse = float(((np.asarray(Image.open(a.out).convert("RGB")).astype(float) - ref_px) ** 2).mean())
        psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
        if psnr >= 34 or os.path.getsize(a.out) > a.max_kb * 1024:
            break
    if os.path.getsize(a.out) > a.max_kb * 1024:
        problems.append(f"JPG {os.path.getsize(a.out) // 1024} KB > {a.max_kb} KB ở chất lượng {q}")
    kb = os.path.getsize(a.out) / 1024
    chk = Image.open(a.out)
    if chk.size != (W, H):
        problems.append(f"size ra {chk.size}")
    rep = {
        "out": a.out, "lossless_png": lossless_path, "out_size": list(chk.size), "out_kb": round(kb, 1), "jpeg_quality": q, "jpeg_psnr_db": round(float(psnr), 2),
        "layout": a.layout, "bg": a.bg, "palette": a.palette, "bg_colors": [c0, c1],
        "headline": a.headline, "sub": a.sub, "tag": a.tag, "callouts": a.callout, "placements": rep_places,
        # khoá cũ cho mảnh đầu, giữ tương thích
        "src": rep_places[0]["src"], "src_sha256": rep_places[0]["src_sha256"], "crop_box": rep_places[0]["crop_box"], "placed": rep_places[0]["placed"],
        "problems": problems, "warnings": warnings,
    }
    if a.report:
        json.dump(rep, open(a.report, "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps({"layout": a.layout, "bg": a.bg, "out_kb": rep["out_kb"],
                      "pieces": [(p["kind"], p["scale"], p["core_max_diff"]) for p in rep_places]}, ensure_ascii=False))
    for w in warnings:
        print("CHÚ Ý", w)
    for p in problems:
        print("VẤN ĐỀ", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
