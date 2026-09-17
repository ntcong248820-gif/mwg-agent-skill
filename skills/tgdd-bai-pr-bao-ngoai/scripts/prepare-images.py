#!/usr/bin/env python3
"""Download, resize to 2048x1150, upload to Drive, and make the images public.

The Docs API fetches an inline image by URL at insert time, so every image must
be readable without a session before the Doc is built. That is why each file is
shared as `anyone/reader` here rather than later.

Reads image blocks from article.json, writes `public_url`, `drive_file_id`,
`src_w` and `src_h` back into the same file.

Usage:
    prepare-images.py article.json --folder <drive-folder-id>
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from gws_helper import assert_account, folder_id_from, share_anyone_reader, upload_file

TARGET_W, TARGET_H = 2048, 1150
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def slugify(value):
    value = re.sub(r"[^a-z0-9]+", "-", value.lower().strip())
    return re.sub(r"-{2,}", "-", value).strip("-") or "anh"


def fetch(source, dest):
    """Fetch a remote URL or copy a local path into dest."""
    if source.startswith(("http://", "https://")):
        result = subprocess.run(
            ["curl", "-sL", "-m", "60", "-A", UA, "-o", dest, "-w", "%{http_code}",
             source], capture_output=True, text=True)
        if result.returncode != 0 or result.stdout.strip() != "200":
            sys.stderr.write("Download failed (%s): %s\n"
                             % (result.stdout.strip() or "error", source))
            return False
    else:
        if not os.path.exists(source):
            sys.stderr.write("Local image not found: %s\n" % source)
            return False
        shutil.copyfile(source, dest)

    probe = subprocess.run(["magick", "identify", "-format", "%m %w %h", dest],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        sys.stderr.write("Not a readable image: %s\n" % source)
        return False
    return True


def resize(src, dest):
    """Fill 2048x1150 exactly: scale to cover, then centre-crop the overflow."""
    result = subprocess.run(
        ["magick", src, "-auto-orient",
         "-resize", "%dx%d^" % (TARGET_W, TARGET_H),
         "-gravity", "center", "-extent", "%dx%d" % (TARGET_W, TARGET_H),
         "-strip", "-quality", "88", dest],
        capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write("Resize failed: %s\n" % result.stderr[-400:])
        return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--folder", required=True, help="Destination Drive folder ID")
    ap.add_argument("--keep-local", help="Directory to also keep the resized files in")
    args = ap.parse_args()

    article = json.load(open(args.article, encoding="utf-8"))
    folder = folder_id_from(args.folder)
    assert_account()

    images = [b for b in article["blocks"] if b["type"] == "image"]
    if len(images) < 2:
        sys.stderr.write("A PR article needs at least 2 images; found %d.\n"
                         % len(images))
        raise SystemExit(1)

    workdir = args.keep_local or tempfile.mkdtemp(prefix="pr-images-")
    os.makedirs(workdir, exist_ok=True)
    failures = []

    for index, block in enumerate(images, start=1):
        if block.get("public_url"):
            continue
        source = block.get("source_url") or block.get("source_path")
        if not source:
            failures.append("image %d has no source_url/source_path" % index)
            continue

        base = block.get("filename") or "%02d-%s" % (index, slugify(
            block.get("caption", "anh-minh-hoa"))[:60])
        raw = os.path.join(workdir, "raw-%02d" % index)
        out = os.path.join(workdir, base + ".jpg")

        if not fetch(source, raw) or not resize(raw, out):
            failures.append("image %d could not be prepared from %s" % (index, source))
            continue

        file_id = upload_file(out, folder, os.path.basename(out))
        share_anyone_reader(file_id)

        block["drive_file_id"] = file_id
        block["local_path"] = out
        block["src_w"], block["src_h"] = TARGET_W, TARGET_H
        # uc?export=view serves the full-resolution original; the lh3 host
        # silently returns a downscaled copy.
        block["public_url"] = "https://drive.google.com/uc?export=view&id=" + file_id
        block["drive_url"] = "https://drive.google.com/file/d/%s/view" % file_id

    if failures:
        sys.stderr.write("Unprepared images:\n  - %s\n" % "\n  - ".join(failures))
        raise SystemExit(1)

    with open(args.article, "w", encoding="utf-8") as handle:
        json.dump(article, handle, ensure_ascii=False, indent=2)

    print(json.dumps(
        [{"caption": b.get("caption", ""), "drive_url": b["drive_url"],
          "local_path": b["local_path"]} for b in images],
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
