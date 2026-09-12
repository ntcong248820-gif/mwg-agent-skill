#!/usr/bin/env python3
"""
image-seo-pipeline/scripts/process_images.py
Pipeline tối ưu hình ảnh chuẩn SEO cho bài viết/infobox TGDĐ.

Features:
- Giữ nguyên tên file gốc (chuẩn hóa kebab-case, đuôi .jpg), KHÔNG đặt lại tên bằng AI
- Nén ImageMagick quality 85
- Gọi Gemini API sinh alt text, title, description tiếng Việt cho SEO
- Bắn EXIF/IPTC metadata (Author, Copyright = Thegioididong.com) bằng exiftool
- Ghi metadata/image-metadata.csv
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

try:
    from PIL import Image
    from google import genai
    from google.genai import types
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Install: pip install google-genai Pillow")
    sys.exit(1)

# ─── Constants ──────────────────────────────────────────────────────────────
AUTHOR          = "Thegioididong.com"
COPYRIGHT       = "Copyright © Thegioididong.com"
GEMINI_MODELS   = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
COMPRESS_QUALITY = 85
IMAGE_EXTS      = ("*.jpg", "*.jpeg", "*.png", "*.webp")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_existing_metadata(metadata_file: Path) -> dict:
    """Load CSV và trả về dict {original_filename: row} cho ảnh đã processed."""
    processed = {}
    if not metadata_file.exists():
        return processed
    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("status") in ("done", "watch"):
                    src = row.get("source", "")
                    orig_name = src.split("/")[-1] if "/" in src else src
                    if orig_name:
                        processed[orig_name] = row
    except Exception as e:
        print(f"[WARN] Could not read CSV: {e}")
    return processed


def collect_images(orig_dir: Path) -> list[Path]:
    images = []
    for ext in IMAGE_EXTS:
        images.extend(orig_dir.glob(ext))
    return sorted(set(images))


def call_gemini(client, img_path: Path, topic_prefix: str) -> Optional[dict]:
    """Gọi Gemini API để sinh alt, title, description tiếng Việt cho SEO."""
    prompt = f"""Analyze this product/marketing image in the context of '{topic_prefix}' (a TGDD/Thegioididong.com article topic).
Output a JSON object with:
- alt: Descriptive Vietnamese alt text for SEO. Describe what is VISUALLY seen. Natural language, no stuffing. STRICTLY DO NOT use any prefix such as "Hình ảnh...", "Ảnh...", "Hình ảnh minh họa...".
- title: Short natural Vietnamese title (under 60 chars).
- description: A Vietnamese image caption (1-2 sentences) that explains and illustrates the concept or value of the image in the context of the article. Do NOT just physically describe what is visually visible (e.g. do not describe case lighting, LED colors, hầm hố design, or list keyboard/mouse/monitor). Instead, focus on explaining the technical meaning, performance value, or importance of the component or layout shown.
  CRITICAL NEGATIVE CONSTRAINTS FOR DESCRIPTION:
  1. DO NOT refer to the article itself (NEVER write "Bài viết này sẽ...", "Trong bài viết này...", "Bài viết giới thiệu...").
  2. DO NOT use meta intro phrases (NEVER write "Hình ảnh giới thiệu...", "Hình ảnh minh họa...", "Hình ảnh thể hiện...").
  3. Write a direct, natural caption explaining the feature or product value."""

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "alt":         types.Schema(type=types.Type.STRING),
                "title":       types.Schema(type=types.Type.STRING),
                "description": types.Schema(type=types.Type.STRING),
            },
            required=["alt", "title", "description"],
        ),
    )

    img = Image.open(img_path)
    max_retries = 3

    for model_name in GEMINI_MODELS:
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=[prompt, img],
                    config=config
                )
                return json.loads(resp.text)
            except Exception as e:
                err = str(e)
                print(f"    [{model_name}] Attempt {attempt+1} failed: {err[:80]}")
                if "GenerateRequestsPerDay" in err:
                    raise RuntimeError("QUOTA_EXHAUSTED")
                elif "429" in err or "RESOURCE_EXHAUSTED" in err:
                    time.sleep(35)
                elif "503" in err or "UNAVAILABLE" in err:
                    time.sleep(10)
                else:
                    time.sleep(5)
    return None


def compress_image(src: Path, dest: Path):
    """Nén ảnh bằng ImageMagick, quality 85, strip metadata cũ."""
    result = subprocess.run(
        ["magick", str(src), "-quality", str(COMPRESS_QUALITY), "-strip", str(dest)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ImageMagick failed: {result.stderr}")


def inject_exif(img_path: Path, title: str, alt: str):
    """Bắn EXIF/IPTC metadata vào file ảnh bằng exiftool với UTF-8 encoding."""
    cmd = [
        "exiftool", "-overwrite_original",
        "-codedcharacterset=utf8",
        "-charset", "IPTC=UTF8",
        f"-Artist={AUTHOR}",
        f"-By-line={AUTHOR}",
        f"-Credit={AUTHOR}",
        f"-Source={AUTHOR}",
        f"-Copyright={COPYRIGHT}",
        f"-CopyrightNotice={COPYRIGHT}",
        f"-Title={title}",
        f"-ObjectName={title}",
        f"-ImageDescription={alt}",
        f"-Caption-Abstract={alt}",
        str(img_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    [WARN] exiftool failed: {result.stderr[:120]}")


def has_exif(img_path: Path) -> bool:
    """Kiểm tra file ảnh đã có metadata EXIF/IPTC (Artist hoặc Title) chưa."""
    res = subprocess.run(
        ["exiftool", "-Artist", "-Title", "-Copyright", str(img_path)],
        capture_output=True, text=True
    )
    out = res.stdout.strip()
    return bool("Artist" in out or "Title" in out or "Copyright" in out)


def get_target_filename(img_path: Path) -> str:
    """Giữ nguyên tên file gốc, chuyển về đuôi .jpg và kebab-case."""
    stem = img_path.stem.lower().replace(" ", "-").replace("_", "-")
    return f"{stem}.jpg"


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Image SEO Pipeline for TGDD content workspaces")
    parser.add_argument("--workspace", required=True, help="Path to content workspace")
    parser.add_argument("--reprocess-exif", action="store_true", help="Force re-inject EXIF metadata for processed images")
    parser.add_argument("--keep-filename", action="store_true", help="Backward compatibility flag (always true)")
    args = parser.parse_args()

    workspace_dir = Path(args.workspace).resolve()
    if not workspace_dir.exists():
        print(f"[ERROR] Workspace not found: {workspace_dir}")
        sys.exit(1)

    orig_dir      = workspace_dir / "images-original"
    proc_dir      = workspace_dir / "images-processed"
    metadata_file = workspace_dir / "metadata" / "image-metadata.csv"

    if not orig_dir.exists() and not proc_dir.exists():
        print(f"[ERROR] Neither images-original/ nor images-processed/ found at {workspace_dir}")
        sys.exit(1)

    proc_dir.mkdir(parents=True, exist_ok=True)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)

    topic_slug   = workspace_dir.name
    topic_prefix = topic_slug.replace("infobox-", "")

    print(f"[INFO] Workspace : {workspace_dir}")
    print(f"[INFO] Topic     : {topic_prefix}")
    print(f"[INFO] Author    : {AUTHOR} (fixed)")

    processed_originals = load_existing_metadata(metadata_file)
    images = collect_images(orig_dir) if orig_dir.exists() else []
    print(f"[INFO] Found {len(images)} original images, {len(processed_originals)} already recorded in CSV.\n")

    client = None
    metadata_rows = list(processed_originals.values())
    quota_exhausted = False
    stats = {"done": 0, "skipped": 0, "watch": 0, "reprocessed_exif": 0, "error": 0}

    for idx, img_path in enumerate(images):
        label = f"[{idx+1}/{len(images)}] {img_path.name}"
        target_name = get_target_filename(img_path)
        proc_img = proc_dir / target_name

        # Skip already done if physical image exists and has EXIF
        if img_path.name in processed_originals:
            row = processed_originals[img_path.name]
            if proc_img.exists() and (args.reprocess_exif or not has_exif(proc_img)):
                title = row.get("title", "") or f"{topic_prefix} {img_path.stem}"
                alt = row.get("alt", "") or f"Hình ảnh {topic_prefix} {img_path.stem}"
                print(f"{label} → Re-injecting EXIF metadata into {target_name}...")
                inject_exif(proc_img, title, alt)
                stats["reprocessed_exif"] += 1
            else:
                print(f"{label} → SKIP (already done)")
                stats["skipped"] += 1
            continue

        # Lazy init client
        if client is None and not quota_exhausted:
            client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

        print(f"{label} → processing...")

        # Fallback nếu quota hết
        if quota_exhausted:
            compress_image(img_path, proc_img)
            inject_exif(proc_img, topic_prefix, f"Hình ảnh {topic_prefix} {img_path.stem}")
            metadata_rows.append({
                "file-name": target_name,
                "alt": f"Hình ảnh {topic_prefix} {img_path.stem}",
                "title": f"{topic_prefix} {img_path.stem}",
                "description": f"Hình ảnh thực tế {topic_prefix}",
                "source": f"images-original/{img_path.name}",
                "status": "watch",
                "notes": "Quota exhausted, fallback used"
            })
            stats["watch"] += 1
            continue

        try:
            # Gọi Gemini API sinh Alt/Title/Desc
            data = call_gemini(client, img_path, topic_prefix)
            if data is None:
                raise RuntimeError("No response from Gemini after all retries")

            alt         = data.get("alt", "").strip()
            title       = data.get("title", "").strip()
            description = data.get("description", "").strip()

            # Nén ảnh giữ nguyên tên gốc (.jpg)
            print(f"  → Compress → {target_name}")
            compress_image(img_path, proc_img)

            # Bắn EXIF
            print(f"  → Inject EXIF (Author={AUTHOR})")
            inject_exif(proc_img, title, alt)

            metadata_rows.append({
                "file-name":   target_name,
                "alt":         alt,
                "title":       title,
                "description": description,
                "source":      f"images-original/{img_path.name}",
                "status":      "done",
                "notes":       ""
            })
            stats["done"] += 1
            time.sleep(2)

        except RuntimeError as e:
            if "QUOTA_EXHAUSTED" in str(e):
                print("  [WARN] Daily quota exhausted — switching to fallback mode")
                quota_exhausted = True
                compress_image(img_path, proc_img)
                inject_exif(proc_img, topic_prefix, f"Hình ảnh {topic_prefix} {img_path.stem}")
                metadata_rows.append({
                    "file-name": target_name,
                    "alt": f"Hình ảnh {topic_prefix} {img_path.stem}",
                    "title": f"{topic_prefix} {img_path.stem}",
                    "description": f"Hình ảnh thực tế {topic_prefix}",
                    "source": f"images-original/{img_path.name}",
                    "status": "watch",
                    "notes": "Quota exhausted, fallback used"
                })
                stats["watch"] += 1
            else:
                print(f"  [ERROR] {e}")
                stats["error"] += 1

    # Sweep scan ALL processed images missing EXIF
    proc_csv_map = {row["file-name"]: row for row in metadata_rows if row.get("file-name")}
    proc_files = []
    for ext in IMAGE_EXTS:
        proc_files.extend(proc_dir.glob(ext))

    for proc_img in sorted(set(proc_files)):
        if args.reprocess_exif or not has_exif(proc_img):
            row = proc_csv_map.get(proc_img.name, {})
            title = row.get("title", "") or proc_img.stem.replace("-", " ").title()
            alt = row.get("alt", "") or title
            print(f"[RE-INJECT EXIF] {proc_img.name} → Injecting EXIF...")
            inject_exif(proc_img, title, alt)
            stats["reprocessed_exif"] += 1

    # Ghi CSV
    fieldnames = ["file-name", "alt", "title", "description", "source", "status", "notes"]
    with open(metadata_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metadata_rows)

    print(f"\n{'─'*50}")
    print(f"[DONE] Processed: {stats['done']} | EXIF Reprocessed: {stats['reprocessed_exif']} | Skipped: {stats['skipped']} | Watch: {stats['watch']} | Error: {stats['error']}")
    print(f"[DONE] CSV saved → {metadata_file}")
    print(f"[DONE] Images    → {proc_dir}")


if __name__ == "__main__":
    main()
