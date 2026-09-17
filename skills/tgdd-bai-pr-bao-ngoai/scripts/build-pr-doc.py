#!/usr/bin/env python3
"""Build a rich-text Google Doc for a PR article from article.json.

Why this builds the Doc natively instead of uploading HTML and letting Drive
convert it: both routes produce correct headings, links and inline images, but
the converted file arrives with borderBottom/borderBetween/padding baked onto
every paragraph (measured 2026-09-17: 42.9 KB vs 22.8 KB for the same article).
A newspaper editor restyling the file then fights those overrides.

Index safety: text is inserted once as a single block, then paragraph and
character styles are applied (neither changes any index), then inline images
are inserted in reverse document order so an insertion can never shift an
index computed before it.

Usage:
    build-pr-doc.py article.json --parent <folder-id-or-url> [--folder-name NAME]
    build-pr-doc.py article.json --folder <existing-folder-id>
"""
import argparse
import json
import sys

from gws_helper import (assert_account, create_folder, folder_id_from, gws,
                        share_anyone_reader, share_anyone_writer)

# Letter page (612pt) minus the default 1-inch margin on each side.
DOC_WIDTH_PT = 468.0

HEADING_STYLE = {"title": "HEADING_1", "h2": "HEADING_2", "h3": "HEADING_3"}
TEXT_BLOCKS = ("title", "sapo", "h2", "h3", "p", "caption")


def layout(blocks):
    """Walk the blocks once, assigning each its absolute start index.

    An image block contributes an empty paragraph that will later hold the
    inline image; its caption becomes a separate paragraph so it can be
    centred and italicised independently.
    """
    cursor = 1
    laid = []
    for block in blocks:
        if block["type"] == "image":
            laid.append({**block, "start": cursor, "text_len": 0})
            cursor += 1  # the empty paragraph's newline
            caption = block.get("caption", "").strip()
            if caption:
                laid.append({"type": "caption", "text": caption,
                             "start": cursor, "text_len": len(caption)})
                cursor += len(caption) + 1
        else:
            text = block["text"]
            laid.append({**block, "start": cursor, "text_len": len(text)})
            cursor += len(text) + 1
    return laid


def full_text(laid):
    return "".join(("" if b["type"] == "image" else b["text"]) + "\n" for b in laid)


def build_requests(laid):
    requests = [{"insertText": {"location": {"index": 1}, "text": full_text(laid)}}]

    for block in laid:
        kind = block["type"]
        para_range = {"startIndex": block["start"],
                      "endIndex": block["start"] + block["text_len"] + 1}
        run_range = {"startIndex": block["start"],
                     "endIndex": block["start"] + block["text_len"]}

        if kind in HEADING_STYLE:
            requests.append({"updateParagraphStyle": {
                "range": para_range,
                "paragraphStyle": {"namedStyleType": HEADING_STYLE[kind]},
                "fields": "namedStyleType"}})
        elif kind == "caption":
            requests.append({"updateParagraphStyle": {
                "range": para_range,
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT",
                                   "alignment": "CENTER"},
                "fields": "namedStyleType,alignment"}})
            requests.append({"updateTextStyle": {
                "range": run_range,
                "textStyle": {
                    "italic": True,
                    "fontSize": {"magnitude": 10, "unit": "PT"},
                    "foregroundColor": {"color": {"rgbColor": {
                        "red": 0.4, "green": 0.4, "blue": 0.4}}}},
                "fields": "italic,fontSize,foregroundColor"}})
        elif kind == "sapo":
            requests.append({"updateParagraphStyle": {
                "range": para_range,
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"}})
            requests.append({"updateTextStyle": {
                "range": run_range, "textStyle": {"bold": True},
                "fields": "bold"}})
        elif kind == "p":
            requests.append({"updateParagraphStyle": {
                "range": para_range,
                "paragraphStyle": {"namedStyleType": "NORMAL_TEXT"},
                "fields": "namedStyleType"}})

        for link in block.get("links") or []:
            offset = block["text"].find(link["text"])
            if offset < 0:
                sys.stderr.write(
                    "Anchor not found in its paragraph: %r\n" % link["text"])
                raise SystemExit(1)
            requests.append({"updateTextStyle": {
                "range": {"startIndex": block["start"] + offset,
                          "endIndex": block["start"] + offset + len(link["text"])},
                "textStyle": {"link": {"url": link["url"]}},
                "fields": "link"}})

    for block in reversed([b for b in laid if b["type"] == "image"]):
        width = block.get("src_w", 2048)
        height = block.get("src_h", 1150)
        requests.append({"insertInlineImage": {
            "location": {"index": block["start"]},
            "uri": block["public_url"],
            "objectSize": {
                "width": {"magnitude": DOC_WIDTH_PT, "unit": "PT"},
                "height": {"magnitude": round(DOC_WIDTH_PT * height / width, 1),
                           "unit": "PT"}}}})
    return requests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--parent", help="Parent Drive folder ID or URL")
    ap.add_argument("--folder", help="Existing destination folder ID")
    ap.add_argument("--folder-name", help="Name for the folder to create")
    ap.add_argument("--no-share", action="store_true",
                    help="Skip link sharing (draft that is not being handed over yet)")
    args = ap.parse_args()

    article = json.load(open(args.article, encoding="utf-8"))
    assert_account()

    if args.folder:
        folder = folder_id_from(args.folder)
    elif args.parent:
        name = args.folder_name or article.get("slug") or article["title"][:80]
        folder = create_folder(name, folder_id_from(args.parent))
    else:
        sys.stderr.write("Need --parent or --folder\n")
        raise SystemExit(1)

    for block in article["blocks"]:
        if block["type"] == "image" and not block.get("public_url"):
            sys.stderr.write(
                "Image block has no public_url — run prepare-images.py first.\n")
            raise SystemExit(1)

    doc_id = gws("docs", "documents", "create",
                 body={"title": article["title"]})["documentId"]
    gws("docs", "documents", "batchUpdate",
        params={"documentId": doc_id},
        body={"requests": build_requests(layout(article["blocks"]))})
    gws("drive", "files", "update",
        params={"fileId": doc_id, "addParents": folder, "removeParents": "root"})

    # The newspaper edits the article in place, so the Doc goes out as
    # link-editable. The folder stays read-only: the editor needs to fetch the
    # image files, not to reorganise the delivery folder.
    if not args.no_share:
        share_anyone_writer(doc_id)
        share_anyone_reader(folder)

    print(json.dumps({
        "folder_id": folder,
        "folder_url": "https://drive.google.com/drive/folders/" + folder,
        "doc_id": doc_id,
        "doc_url": "https://docs.google.com/document/d/" + doc_id,
        "doc_access": "private" if args.no_share else "anyone-with-link can edit",
        "folder_access": "private" if args.no_share else "anyone-with-link can view",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
