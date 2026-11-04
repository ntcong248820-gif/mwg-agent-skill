#!/usr/bin/env python3
"""Kiểm độc lập: mọi mảnh ảnh SP trong ảnh ra có y nguyên ảnh gốc không. Chỉ đọc.

Dùng: verify-sp-fidelity.py --out ANH_RA --report ra.json [--src ANH_GOC] [--core-dist 60] [--erode 4]
Đọc `placements` trong report (mỗi mảnh: ảnh gốc + sha256, khung cắt, vị trí dán). Với mỗi mảnh: co ảnh gốc theo
cùng Lanczos, lấy điểm SP rõ (cách trắng > --core-dist, bỏ thêm --erode điểm quanh vùng gần trắng để loại vành tách
nền) và so từng điểm với bản PNG không nén. Không dùng lại mặt nạ của compose-sp-image.py nên bắt được lỗi tách nền.
Mảnh `detail` (thẻ phóng chi tiết) được so theo cùng cách. Kiểm thêm sha256 ảnh gốc còn đúng, tỷ lệ khung mỗi mảnh,
PSNR(JPG, PNG) >= --psnr-min. Nén JPG 4:2:0 làm lệch vài đơn vị ở nét tương phản cao nên KHÔNG so JPG với ảnh gốc.
Report đời cũ (không có placements) vẫn đọc được: cần --src.
Exit 0 = đạt; 1 = lệch.
"""
import argparse, hashlib, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def check_piece(src, crop_box, placed, out, a):
    ox, oy, nw, nh = placed
    ref_a = np.asarray(src.crop(tuple(crop_box)).resize((nw, nh), Image.LANCZOS)).astype(int)
    got = np.asarray(out.crop((ox, oy, ox + nw, oy + nh))).astype(int)
    dist = (255 - ref_a).max(axis=2)
    pad = a.erode + 1  # ngoài khung cắt coi như nền trắng
    near = np.pad(dist <= 40, pad, constant_values=True)
    near = ndi.binary_dilation(near, iterations=a.erode)[pad:-pad, pad:-pad]
    core = (dist > a.core_dist) & ~near
    diff = np.abs(got - ref_a).max(axis=2)
    n = int(core.sum())
    bad = int((diff[core] > a.tol).sum()) if n else -1
    ar0 = (crop_box[2] - crop_box[0]) / (crop_box[3] - crop_box[1])
    ar1 = nw / nh
    return {"core_pixels": n, "max_diff": int(diff[core].max()) if n else -1, "diff_pixels_over_tol": bad,
            "diff_frac": round(bad / max(n, 1), 5), "aspect_err_pct": round(abs(ar1 - ar0) / ar0 * 100, 3)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--src", help="chỉ cần cho report đời cũ không có placements")
    ap.add_argument("--core-dist", type=int, default=60)
    ap.add_argument("--tol", type=int, default=2, help="sai số cho phép mỗi điểm (làm tròn khi co ảnh)")
    ap.add_argument("--bad-frac", type=float, default=0.001, help="tỷ lệ điểm lõi vượt --tol cho phép")
    ap.add_argument("--erode", type=int, default=4)
    ap.add_argument("--psnr-min", type=float, default=33.0)
    a = ap.parse_args()
    r = json.load(open(a.report, encoding="utf8"))
    out = Image.open(r.get("lossless_png") or a.out).convert("RGB")
    jpg = Image.open(a.out).convert("RGB")
    pieces = r.get("placements") or [{"kind": "cutout", "src": a.src, "src_sha256": None, "crop_box": r["crop_box"], "placed": r["placed"]}]
    ok, rows = True, []
    for i, p in enumerate(pieces):
        path = p["src"] if os.path.exists(p["src"] or "") else a.src
        raw = open(path, "rb").read()
        sha_ok = p.get("src_sha256") in (None, hashlib.sha256(raw).hexdigest())
        res = check_piece(Image.open(path).convert("RGB"), p["crop_box"], p["placed"], out, a)
        good = sha_ok and res["core_pixels"] > 0 and res["diff_frac"] <= a.bad_frac and res["aspect_err_pct"] < 0.5
        ok &= good
        rows.append({"piece": i, "kind": p["kind"], "src": os.path.basename(path), "sha256_ok": sha_ok, **res, "pass": good})
    mse = float(((np.asarray(jpg).astype(float) - np.asarray(out).astype(float)) ** 2).mean())
    psnr = 99.0 if mse == 0 else 10 * np.log10(255 ** 2 / mse)
    ok &= psnr >= a.psnr_min
    print(json.dumps({"pieces": rows, "jpg_psnr_db": round(float(psnr), 2), "out_size": list(jpg.size),
                      "out_kb": round(os.path.getsize(a.out) / 1024, 1)}, ensure_ascii=False))
    print("ĐẠT: mọi mảnh SP khớp ảnh gốc, tỷ lệ khung giữ nguyên" if ok else "KHÔNG ĐẠT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
