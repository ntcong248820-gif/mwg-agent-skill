#!/usr/bin/env python3
"""Resolve URL đích của internal link về URL CUỐI (sau redirect).

Lý do tồn tại: bài tin/hỏi đáp cũ có slug dạng `hoi-dap/bv-{id}` và trang category
cũ (`/laptop-hp`) đều đang 301/302 sang URL khác. Chèn link bằng URL cũ là bắt
người đọc và bot đi thêm một chặng, và với category thì chặng đó có khi đổ về
trang rộng hơn hẳn (`/laptop-hp` → `/laptop`) — mất đúng cái trang định trỏ tới.

Dùng chung cho `optimize_content.py` (sửa URL trước khi chèn) và
`check_internal_links.py` (bắt link còn redirect trong bài đã build).

Offline: đặt `MWG_LINK_OFFLINE=1` hoặc truyền `offline=True` để bỏ qua toàn bộ
phần mạng (test không có mạng thì mọi URL trả trạng thái `unknown`).
"""
# `str | None` trong annotation cần Python 3.10. Script này chạy bằng python3 hệ
# thống/venv của máy người dùng, không chốt được phiên bản — future import làm
# annotation thành string nên import được từ 3.7 trở đi.
from __future__ import annotations

import concurrent.futures
import os
import re
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")
DEFAULT_TIMEOUT = 12
MAX_HOPS = 5
MAX_WORKERS = 6

# Hệ bài viết: redirect đổi segment đầu = rơi ra khỏi hệ bài, không còn cùng chủ đề.
EXPLAINER_SEGS = ("hoi-dap", "tin-tuc", "kinh-nghiem-hay", "game-app")

INTERNAL_HOSTS = ("thegioididong.com", "dienmayxanh.com", "topzone.vn")

# Cache toàn tiến trình: một lần chạy optimizer có thể hỏi cùng một URL nhiều lần
# (danh sách link từ Sheet có URL lặp), và checker chạy ngay sau đó trong cùng job.
_CACHE: dict[str, dict] = {}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Chặn urllib tự đi theo redirect — ta cần biết CÓ redirect hay không."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def offline(explicit: bool = False) -> bool:
    return bool(explicit) or os.environ.get("MWG_LINK_OFFLINE", "").strip() not in ("", "0")


def path_of(url: str) -> str:
    p = re.sub(r"^https?://[^/]+", "", (url or "").split("?")[0].split("#")[0])
    return p.strip("/")


def first_segment(url: str) -> str:
    p = path_of(url)
    return p.split("/")[0] if p else ""


def is_internal(url: str) -> bool:
    host = urllib.parse.urlparse(url or "").netloc.lower()
    return any(host == h or host.endswith("." + h) for h in INTERNAL_HOSTS)


def _one_hop(url: str, method: str, timeout: float):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            return getattr(r, "status", r.getcode()), None, None
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location") if e.headers else None
        return e.code, loc, None
    except Exception as e:  # URLError, timeout, DNS, SSL...
        return None, None, f"{type(e).__name__}: {e}"


def resolve(url: str, timeout: float = DEFAULT_TIMEOUT, offline_mode: bool = False) -> dict:
    """Trả {'url', 'final_url', 'status', 'redirected', 'error'}.

    `status=None` + `error` != None nghĩa là KHÔNG kết luận được (mất mạng, chặn
    bot) — nơi gọi phải coi đó là "chưa biết", không được coi là link hỏng.
    """
    url = (url or "").strip()
    if not url:
        return {"url": url, "final_url": url, "status": None, "redirected": False,
                "error": "URL rỗng"}
    if url in _CACHE:
        return _CACHE[url]
    if offline(offline_mode):
        res = {"url": url, "final_url": url, "status": None, "redirected": False,
               "error": "offline"}
        _CACHE[url] = res
        return res

    current = url
    error = None
    status = None
    for _ in range(MAX_HOPS):
        status, loc, error = _one_hop(current, "HEAD", timeout)
        # Một số origin trả 403/405 cho HEAD nhưng 200 cho GET.
        if status in (403, 405, 501):
            status, loc, error = _one_hop(current, "GET", timeout)
        if error:
            break
        if status and 300 <= status < 400 and loc:
            current = urllib.parse.urljoin(current, loc)
            continue
        break

    res = {"url": url, "final_url": current, "status": status,
           "redirected": path_of(current) != path_of(url), "error": error}
    _CACHE[url] = res
    return res


def resolve_many(urls, timeout: float = DEFAULT_TIMEOUT, offline_mode: bool = False,
                 workers: int = MAX_WORKERS) -> dict:
    uniq = []
    seen = set()
    for u in urls:
        u = (u or "").strip()
        if u and u not in seen:
            seen.add(u)
            uniq.append(u)
    if not uniq:
        return {}
    if offline(offline_mode):
        return {u: resolve(u, timeout, True) for u in uniq}
    out = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = {pool.submit(resolve, u, timeout, False): u for u in uniq}
        for fut in concurrent.futures.as_completed(futs):
            u = futs[fut]
            try:
                out[u] = fut.result()
            except Exception as e:  # không để một URL làm chết cả lượt
                out[u] = {"url": u, "final_url": u, "status": None,
                          "redirected": False, "error": f"{type(e).__name__}: {e}"}
    return out


def dest_kind(url: str) -> str:
    """Loại trang đích: tên hệ bài (`hoi-dap`, `tin-tuc`...) hoặc `category`.

    Dùng để ép link thay thế phải CÙNG LOẠI: bài hỏi đáp thay bài hỏi đáp,
    trang danh mục thay trang danh mục. Lấy trang danh mục thay một bài viết đã
    bị xoá là đổi luôn thứ người đọc được mời tới, không phải "thay tương đương".
    """
    seg = first_segment(url)
    return seg if seg in EXPLAINER_SEGS else "category"


def alive_final(url: str, timeout: float = DEFAULT_TIMEOUT,
                offline_mode: bool = False) -> str | None:
    """URL cuối nếu trang còn sống và còn đúng chủ đề; ngược lại None.

    Thận trọng NGƯỢC CHIỀU với `classify()`: ở đây `unknown` trả None. Link đang
    có trong bài mà không đo được thì giữ (mất mạng không được làm rụng link),
    nhưng một ứng viên định chèn MỚI vào bài thì phải tự chứng minh là 200 sạch.
    """
    res = resolve(url, timeout, offline_mode)
    verdict, _ = classify(res)
    return res["final_url"] if verdict in ("ok", "redirect") else None


def classify(res: dict) -> tuple[str, str]:
    """Trả (verdict, giải thích). Verdict:

    - `ok`       : 200, không redirect — dùng thẳng.
    - `redirect` : redirect sang URL cùng hệ/cùng chủ đề — thay bằng `final_url`.
    - `offtopic` : redirect về trang chủ, hoặc rơi sang hệ khác/trang rộng hơn —
                   bỏ link, vì trang đích không còn là cái câu văn đang nói tới.
    - `dead`     : 404/410/5xx — bỏ link.
    - `unknown`  : không đo được (offline, bị chặn) — giữ nguyên, chỉ ghi chú.
    """
    status, err = res.get("status"), res.get("error")
    if err or status is None:
        return "unknown", err or "không đo được"
    if status in (404, 410) or status >= 500:
        return "dead", f"HTTP {status}"
    if not res.get("redirected"):
        return ("ok", f"HTTP {status}") if status < 400 else ("dead", f"HTTP {status}")

    src, dst = res["url"], res["final_url"]
    if not path_of(dst):
        return "offtopic", f"redirect về trang chủ ({status})"
    s0, d0 = first_segment(src), first_segment(dst)
    if s0 in EXPLAINER_SEGS and d0 != s0:
        return "offtopic", f"bài {s0} redirect ra ngoài hệ bài → /{path_of(dst)}"
    if s0 not in EXPLAINER_SEGS and d0 not in EXPLAINER_SEGS:
        # Category → category: /laptop-hp → /laptop là mất đúng trang hãng định
        # trỏ tới. Đích hẹp hơn hoặc bằng thì chỉ là đổi slug, thay URL là xong.
        if len(path_of(dst)) < len(path_of(src)) and path_of(src).startswith(path_of(dst)):
            return "offtopic", f"category redirect về trang rộng hơn /{path_of(dst)}"
    return "redirect", f"HTTP {status} → /{path_of(dst)}"
