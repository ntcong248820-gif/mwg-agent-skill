#!/usr/bin/env python3
"""Chuỗi gate hoàn thiện ảnh: verify 16:9 -> resize -> logo TGDĐ -> verify size.

Port đúng thứ tự gate của workflow n8n `vTJmWPMVPL8G64dm`:
  Verify Generated Aspect Ratio -> Resize Image -> Composite TGDD Logo
  -> Verify Final Image Dimensions

Gate nào fail thì exit != 0. Không bao giờ stretch ảnh sai tỉ lệ cho vừa khung.
"""

import argparse
import os
import sys

from PIL import Image

MODES = {
    # (width, height) cuối cùng theo từng mode
    "infobox": (1200, 675),
    "blog": (800, 450),
}

TARGET_ASPECT = 16 / 9
ASPECT_TOLERANCE = 0.02       # cho phép lệch 2% do model làm tròn pixel
JPEG_QUALITY = 95

# Logo gốc 64x64, đặt tại (1124, 12) trên khung 1200x675 -> góc phải trên,
# margin 12px. Scale theo bề rộng để mode blog giữ đúng tỉ lệ thị giác.
LOGO_BASE_CANVAS_WIDTH = 1200
LOGO_BASE_SIZE = 64
LOGO_BASE_MARGIN = 12

# Bring your own watermark. No logo ships with this skill: publishing a
# company mark under the repo licence is not something this skill should do.
LOGO_PATH = os.environ.get(
    "WATERMARK_LOGO_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png"))


def verify_aspect(img, path):
    width, height = img.size
    if height == 0:
        sys.exit(f"FAIL aspect-gate: ảnh {path} có height = 0.")
    aspect = width / height
    drift = abs(aspect - TARGET_ASPECT) / TARGET_ASPECT
    if drift > ASPECT_TOLERANCE:
        sys.exit(
            f"FAIL aspect-gate: {path} là {width}x{height} (tỉ lệ {aspect:.3f}), "
            f"không phải 16:9 ({TARGET_ASPECT:.3f}). Lệch {drift * 100:.1f}%. "
            "Không resize để tránh kéo méo ảnh — tạo lại ảnh."
        )
    print(f"PASS aspect-gate: {width}x{height} (tỉ lệ {aspect:.3f})")
    return aspect


def composite_logo(img, canvas_width):
    if not os.path.isfile(LOGO_PATH):
        sys.exit(
            f"FAIL watermark: không thấy logo tại {LOGO_PATH}.\n"
            "Đặt logo của bạn vào assets/logo.png, hoặc trỏ WATERMARK_LOGO_PATH tới file khác.")

    scale = canvas_width / LOGO_BASE_CANVAS_WIDTH
    logo_size = max(1, round(LOGO_BASE_SIZE * scale))
    margin = max(1, round(LOGO_BASE_MARGIN * scale))

    with Image.open(LOGO_PATH) as logo:
        logo = logo.convert("RGBA").resize((logo_size, logo_size), Image.LANCZOS)
        position = (img.width - logo_size - margin, margin)
        base = img.convert("RGBA")
        base.alpha_composite(logo, dest=position)
        result = base.convert("RGB")

    print(f"PASS watermark: logo {logo_size}x{logo_size} tại {position}")
    return result


def verify_dimensions(path, expected):
    with Image.open(path) as img:
        actual = img.size
    if actual != expected:
        sys.exit(
            f"FAIL dimension-gate: {path} là {actual[0]}x{actual[1]}, "
            f"cần đúng {expected[0]}x{expected[1]}."
        )
    print(f"PASS dimension-gate: {actual[0]}x{actual[1]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=sorted(MODES), required=True)
    parser.add_argument("--in", dest="source", required=True, help="Ảnh raw từ generate_image.py")
    parser.add_argument("--out", dest="target", required=True, help="File .jpg đầu ra")
    parser.add_argument("--no-watermark", action="store_true",
                        help="Bỏ logo TGDĐ (mặc định cả 2 mode đều đóng logo)")
    args = parser.parse_args()

    if not os.path.isfile(args.source):
        sys.exit(f"ERROR: không thấy ảnh vào: {args.source}")

    target_size = MODES[args.mode]
    print(f"mode={args.mode} target={target_size[0]}x{target_size[1]}")

    with Image.open(args.source) as img:
        img.load()
        verify_aspect(img, args.source)
        resized = img.convert("RGB").resize(target_size, Image.LANCZOS)
        print(f"PASS resize: -> {target_size[0]}x{target_size[1]}")

        if args.no_watermark:
            final = resized
            print("SKIP watermark (--no-watermark)")
        else:
            final = composite_logo(resized, target_size[0])

        os.makedirs(os.path.dirname(os.path.abspath(args.target)) or ".", exist_ok=True)
        final.save(args.target, "JPEG", quality=JPEG_QUALITY, optimize=True)

    verify_dimensions(args.target, target_size)
    size_kb = os.path.getsize(args.target) / 1024
    print(f"OK -> {args.target} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
