#!/usr/bin/env python3
"""Lint article.json against the PR article rules before anything is published.

Every rule here is one that is cheap to break by hand and expensive to notice
later: a link dropped into a heading, a 9-sentence paragraph, a caption that
never got written, a draft that drifted to 1,400 words.

Exit code 0 means the draft may go to the verify gate. Exit code 1 lists the
violations. Warnings never block.

Usage:
    check-article.py article.json [--json]
"""
import argparse
import json
import re
import sys

DEFAULT_MIN_WORDS, DEFAULT_MAX_WORDS = 800, 1000
MAX_SENTENCES_PER_PARA = 4
MAX_WORDS_PER_PARA = 90
MAX_TITLE_CHARS = 120
MIN_IMAGES = 2
LINKABLE = {"p"}

BODY_TYPES = ("sapo", "h2", "h3", "p")
URL_IN_TEXT = re.compile(r"https?://\S+")


def words(text):
    return len([w for w in text.split() if w.strip()])


def sentences(text):
    return [s for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s]


def check(article):
    errors, warnings = [], []
    blocks = article["blocks"]

    target_min = article.get("target_words_min", DEFAULT_MIN_WORDS)
    target_max = article.get("target_words_max", DEFAULT_MAX_WORDS)

    titles = [b for b in blocks if b["type"] == "title"]
    sapos = [b for b in blocks if b["type"] == "sapo"]
    images = [b for b in blocks if b["type"] == "image"]
    paras = [b for b in blocks if b["type"] == "p"]

    if len(titles) != 1:
        errors.append("Need exactly 1 title block, found %d." % len(titles))
    elif len(titles[0]["text"]) > MAX_TITLE_CHARS:
        errors.append("Title is %d chars (max %d)."
                      % (len(titles[0]["text"]), MAX_TITLE_CHARS))

    if len(sapos) != 1:
        errors.append("Need exactly 1 sapo block, found %d." % len(sapos))

    if len(images) < MIN_IMAGES:
        errors.append("Need at least %d images, found %d." % (MIN_IMAGES, len(images)))

    for index, image in enumerate(images, start=1):
        if not image.get("caption", "").strip():
            errors.append("Image %d has no caption." % index)
        if not (image.get("source_url") or image.get("source_path")
                or image.get("public_url")):
            errors.append("Image %d has no source." % index)

    body_words = sum(words(b["text"]) for b in blocks if b["type"] in BODY_TYPES)
    if not target_min <= body_words <= target_max:
        errors.append("Body is %d words, outside the %d-%d target."
                      % (body_words, target_min, target_max))

    for index, block in enumerate(blocks):
        kind = block["type"]
        links = block.get("links") or []

        if links and kind not in LINKABLE:
            errors.append(
                "Block %d (%s) carries %d link(s). Links belong in paragraphs "
                "only — never in a title, sapo, heading or caption."
                % (index, kind, len(links)))

        for link in links:
            if link["text"] not in block.get("text", ""):
                errors.append("Block %d: anchor %r is not in the paragraph text."
                              % (index, link["text"]))
            if not link.get("url", "").startswith(("http://", "https://")):
                errors.append("Block %d: link %r has no absolute URL."
                              % (index, link["text"]))

        if kind in ("p", "sapo") and URL_IN_TEXT.search(block.get("text", "")):
            errors.append("Block %d prints a raw URL; use an anchored link." % index)

        if kind == "p":
            count = len(sentences(block["text"]))
            if count > MAX_SENTENCES_PER_PARA:
                errors.append("Block %d has %d sentences (max %d) — split it."
                              % (index, count, MAX_SENTENCES_PER_PARA))
            if words(block["text"]) > MAX_WORDS_PER_PARA:
                errors.append("Block %d is %d words (max %d) — split it."
                              % (index, words(block["text"]), MAX_WORDS_PER_PARA))

    all_links = [l for b in blocks for l in (b.get("links") or [])]
    brand_links = [l for l in all_links
                   if "thegioididong.com" in l["url"] or "dienmayxanh.com" in l["url"]]
    max_brand = article.get("max_brand_links", 3)
    if article.get("placement", "bao-ngoai") == "bao-ngoai" and len(brand_links) > max_brand:
        errors.append("%d links point at MWG sites; a booked press article allows "
                      "at most %d." % (len(brand_links), max_brand))

    seen = {}
    for link in all_links:
        seen[link["url"]] = seen.get(link["url"], 0) + 1
    for url, count in seen.items():
        if count > 1:
            warnings.append("URL linked %d times: %s" % (count, url))

    if paras and not any(b["type"] in ("h2", "h3") for b in blocks):
        warnings.append("No subheadings; a press article normally has 2-4.")

    return errors, warnings, body_words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    article = json.load(open(args.article, encoding="utf-8"))
    errors, warnings, body_words = check(article)

    if args.json:
        print(json.dumps({"ok": not errors, "body_words": body_words,
                          "errors": errors, "warnings": warnings},
                         ensure_ascii=False, indent=2))
    else:
        print("Body words: %d" % body_words)
        for warning in warnings:
            print("WARN  " + warning)
        for error in errors:
            print("ERROR " + error)
        print("RESULT: %s" % ("PASS" if not errors else "FAIL (%d)" % len(errors)))

    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
