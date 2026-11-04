"""Thư viện dựng hình Content SP, xử lý xác định (Pillow + numpy + scipy). KHÔNG dùng AI sinh/sửa ảnh.

Mọi hàm ở đây chỉ được: tách nền trắng, co đều (Lanczos, không phóng to), cắt khung, vẽ nền/chữ/thẻ ở NGOÀI
vùng SP. Điểm ảnh SP luôn dán sau cùng lên trên nền, nên nền, bóng đổ, chữ không bao giờ đè lên lõi SP.
compose-sp-image.py ghép các mảnh này theo bố cục; verify-sp-fidelity.py kiểm độc lập kết quả.
"""
import colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy import ndimage as ndi

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG = "/System/Library/Fonts/Supplemental/Arial.ttf"

# Bảng màu nền (đầu, cuối gradient). Trong một bài nên giữ 1–2 bảng màu cho đồng bộ, đổi bố cục để đỡ đơn điệu.
PALETTES = {
    "night": ("04070e", "13233f"),   # nền tối kiểu bộ AI Predator/đồ hoạ: đen xanh, chữ trắng, nhấn vàng
    "studio": ("f6f7f9", "dfe4eb"),  # nền sáng kiểu bộ AI mỏng nhẹ: trắng xám, chữ xanh đậm, nhấn vàng
    "navy": ("0b1b3a", "1f5fbf"),
    "teal": ("0c2233", "0e7490"),
    "charcoal": ("121418", "3b414d"),
    "purple": ("1a1033", "5b3fa8"),
    "emerald": ("0b231c", "11795a"),
    "warm": ("2a160d", "9a4a1c"),
    "light": ("f7f8fb", "dde4ee"),
}
BG_STYLES = ["gradient", "shapes", "split", "spotlight", "light"]


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def matte(rgb, tol, rim, clear_at=()):
    """Tách nền trắng liên thông với viền ảnh. Trả (alpha, màu F, danh sách vùng trắng kín còn giữ, số vùng đã xoá).

    Điểm trong nền R (và vành `rim` điểm quanh R) chuyển màu-sang-alpha để bóng nhạt thành bán trong suốt;
    mọi điểm còn lại (lõi SP, kể cả cổng, ổ cắm) alpha = 1 và giữ nguyên màu.
    clear_at = [(x, y), ...] toạ độ ảnh gốc: vùng trắng kín chứa điểm đó cũng tính là nền (khe bản lề, giữa chân đế).
    Phải chỉ điểm từng vùng: xoá theo kích thước sẽ xoá nhầm mảng sáng trên màn hình (đã gặp, verify bắt được).
    """
    a = rgb.astype(np.int16)
    dist = (255 - a).max(axis=2)
    cand = dist <= tol
    lab, n = ndi.label(cand)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    border = border[border > 0]
    sizes = ndi.sum(cand, lab, index=np.arange(1, n + 1))
    bset = set(border.tolist())
    cleared = sorted({int(lab[y, x]) for x, y in clear_at if lab[y, x] > 0 and lab[y, x] not in bset})
    R = np.isin(lab, list(bset) + cleared)
    keep = [i for i in range(1, n + 1) if i not in bset and i not in cleared and sizes[i - 1] >= 500]
    objs = ndi.find_objects(lab)
    enclosed = []
    for i in sorted(keep, key=lambda i: -sizes[i - 1]):
        sl = objs[i - 1]
        yy, xx = np.nonzero(lab[sl] == i)
        enclosed.append({"px": int(sizes[i - 1]), "bbox": [sl[1].start, sl[0].start, sl[1].stop, sl[0].stop],
                         "seed": [int(xx[0] + sl[1].start), int(yy[0] + sl[0].start)]})
    Rd = ndi.binary_dilation(R, iterations=rim)
    alpha = np.clip(np.where(Rd, dist / 255.0, 1.0), 0, 1)
    F = a.astype(np.float64)
    m = Rd & (alpha > 1e-3)
    F[m] = 255 - (255 - F[m]) / alpha[m][:, None]
    F = np.clip(F, 0, 255)
    alpha[R & (dist <= 2)] = 0
    return (alpha * 255).round().astype(np.uint8), F.round().astype(np.uint8), enclosed, len(cleared)


def cutout(src_rgb, tol=40, rim=2, clear_at=()):
    """Ảnh gốc RGB -> dict: rgba đã cắt sát SP, bản gốc cắt cùng khung, crop_box, cảnh báo mép."""
    rgb = np.asarray(src_rgb)
    alpha, F, enclosed, cleared = matte(rgb, tol, rim, clear_at)
    ys, xs = np.where(alpha > 8)
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    solid = (255 - rgb.astype(np.int16)).max(axis=2) > tol
    edge_px = int(solid[0].sum() + solid[-1].sum() + solid[:, 0].sum() + solid[:, -1].sum())
    return {
        "rgba": Image.fromarray(np.dstack([F, alpha])).crop(box),
        "orig": src_rgb.crop(box),
        "crop_box": list(box),
        "edge_px": edge_px,
        "enclosed": enclosed,
        "cleared": cleared,
    }


def fit(size, box_w, box_h):
    """Hệ số co để (w,h) vừa khung; không bao giờ > 1 (cấm phóng to ảnh SP)."""
    return min(box_w / size[0], box_h / size[1], 1.0)


def product_tone(cut):
    """Màu chủ đạo của SP (trung bình điểm lõi). Dùng cho nền --bg-auto."""
    arr = np.asarray(cut["rgba"])
    m = arr[..., 3] == 255
    if not m.any():
        return None
    r, g, b = (arr[..., :3][m].mean(axis=0) / 255).tolist()
    return colorsys.rgb_to_hsv(r, g, b)


def auto_palette(cut):
    """Bảng màu tối theo sắc của SP; SP xám/đen/bạc (bão hoà thấp) thì dùng charcoal."""
    hsv = product_tone(cut)
    if hsv is None or hsv[1] < 0.18:
        return PALETTES["charcoal"]
    h = hsv[0]
    c0 = colorsys.hsv_to_rgb(h, 0.55, 0.14)
    c1 = colorsys.hsv_to_rgb(h, 0.65, 0.55)
    return tuple("".join(f"{round(v * 255):02x}" for v in c) for c in (c0, c1))


def _grad(W, H, c0, c1, wx=0.65, wy=0.35):
    t = np.clip(np.arange(W)[None, :] / (W - 1) * wx + np.arange(H)[:, None] / (H - 1) * wy, 0, 1)[..., None]
    g = np.array(c0)[None, None, :] * (1 - t) + np.array(c1)[None, None, :] * t
    return Image.fromarray(g.round().astype(np.uint8)).convert("RGBA")


def background(W, H, style, c0, c1, focus=(0.7, 0.5), split_at=0.42):
    """Nền theo kiểu. focus = tâm vùng SP (tỷ lệ), dùng cho spotlight/shapes."""
    c0, c1 = hex2rgb(c0), hex2rgb(c1)
    if style == "light":
        return _grad(W, H, c0, c1, 0.3, 0.7)
    if style == "split":
        bg = _grad(W, H, c1, c0, 0.2, 0.8)
        panel = _grad(W, H, c0, tuple(int(v * 0.8) for v in c0), 0.0, 1.0)
        mask = Image.new("L", (W, H), 0)
        x = int(W * split_at)
        ImageDraw.Draw(mask).polygon([(0, 0), (x + 60, 0), (x - 20, H), (0, H)], fill=255)
        bg.paste(panel, (0, 0), mask)
        return bg
    if style == "spotlight":
        yy, xx = np.mgrid[0:H, 0:W]
        fx, fy = focus[0] * W, focus[1] * H
        d = np.sqrt(((xx - fx) / (W * 0.55)) ** 2 + ((yy - fy) / (H * 0.75)) ** 2)
        t = np.clip(d, 0, 1)[..., None]
        g = np.array(c1)[None, None, :] * (1 - t) + np.array(c0)[None, None, :] * t
        return Image.fromarray(g.round().astype(np.uint8)).convert("RGBA")
    bg = _grad(W, H, c0, c1)
    if style == "shapes":
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        fx, fy = int(focus[0] * W), int(focus[1] * H)
        r = int(H * 0.62)
        d.ellipse((fx - r, fy - r, fx + r, fy + r), fill=(255, 255, 255, 22))
        r2 = int(H * 0.40)
        d.ellipse((fx - r2, fy - r2, fx + r2, fy + r2), outline=(255, 255, 255, 40), width=2)
        d.polygon([(int(W * 0.10), H), (int(W * 0.34), 0), (int(W * 0.40), 0), (int(W * 0.16), H)], fill=(255, 255, 255, 14))
        for i in range(6):
            for j in range(4):
                x, y = 40 + i * 18, H - 90 + j * 18
                d.ellipse((x, y, x + 3, y + 3), fill=(255, 255, 255, 60))
        layer = layer.filter(ImageFilter.GaussianBlur(0.6))
        bg.alpha_composite(layer)
    return bg


def drop_shadow(canvas, rgba, ox, oy, strength=0.45):
    """Bóng mềm dưới SP, vẽ TRƯỚC khi dán SP (không chạm điểm SP)."""
    w, h = rgba.size
    sh = Image.new("L", canvas.size, 0)
    d = ImageDraw.Draw(sh)
    cx, by = ox + w / 2, oy + h
    d.ellipse((cx - w * 0.46, by - h * 0.06, cx + w * 0.46, by + h * 0.05), fill=int(255 * strength))
    sh = sh.filter(ImageFilter.GaussianBlur(max(6, h * 0.05)))
    black = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
    black.putalpha(sh)
    canvas.alpha_composite(black)


def text_colors(light):
    """(tiêu đề, mô tả, nhấn, nền thẻ chip) theo nền sáng/tối."""
    if light:
        return (17, 24, 39, 255), (55, 65, 81, 255), (29, 78, 216, 255), (255, 255, 255, 200)
    return (255, 255, 255, 255), (205, 222, 245, 255), (125, 211, 252, 255), (255, 255, 255, 30)


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, width, lines_spec):
    """Vẽ lần lượt [(chữ, font, màu, giãn dòng, cách sau)], trả y kết thúc."""
    for txt, fnt, col, lh, after in lines_spec:
        if not txt:
            continue
        for ln in wrap(draw, txt, fnt, width):
            draw.text((x, y), ln, font=fnt, fill=col)
            y += lh
        y += after
    return y


def rounded_card(canvas, box, radius, fill, outline=None, shadow=True):
    """Thẻ bo góc (nền thẻ), vẽ trước khi dán ảnh chi tiết vào trong."""
    x0, y0, x1, y1 = box
    if shadow:
        sh = Image.new("L", canvas.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 8), radius, fill=110)
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        black = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
        black.putalpha(sh)
        canvas.alpha_composite(black)
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle(box, radius, fill=fill, outline=outline, width=2 if outline else 0)
    canvas.alpha_composite(layer)
