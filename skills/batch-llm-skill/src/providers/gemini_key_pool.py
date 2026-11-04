"""
gemini_key_pool.py — xoay vòng nhiều Gemini API key free khi hết quota.

Nguồn key (gộp theo thứ tự, bỏ trùng):
  1. GEMINI_API_KEYS  — nhiều key, phân cách bằng dấu phẩy / khoảng trắng / xuống dòng
  2. GEMINI_API_KEY
  3. GOOGLE_API_KEY

Quota free tier tính theo (project, model), và project tạo sau có thể bị chặn một số
model ("no longer available to new users"). Vì vậy pool đánh dấu chết theo cặp
(key, model), không chết cả key, trừ khi key sai hẳn (401/403 API_KEY_INVALID).

Module không phụ thuộc SDK: nhận message lỗi dạng string, dùng được cho cả
google-genai lẫn requests thuần.
"""

from __future__ import annotations

import os
import re

# Trạng thái phân loại lỗi
DEAD_COMBO = "dead_combo"   # hết quota ngày hoặc model không cấp cho key này → bỏ cặp
DEAD_KEY = "dead_key"       # key sai/bị thu hồi → bỏ cả key
RATE_LIMIT = "rate_limit"   # quá RPM/TPM → nhảy cặp khác, quay lại sau
TRANSIENT = "transient"     # 5xx / quá tải → thử lại được
OTHER = "other"             # lỗi request (prompt, ảnh...) → đổi key không cứu được


def load_keys() -> list[str]:
    raw = [os.environ.get("GEMINI_API_KEYS", ""),
           os.environ.get("GEMINI_API_KEY", ""),
           os.environ.get("GOOGLE_API_KEY", "")]
    keys: list[str] = []
    for chunk in raw:
        for k in re.split(r"[,\s]+", chunk.strip()):
            if k and k not in keys:
                keys.append(k)
    return keys


def mask(key: str) -> str:
    """Chỉ hiện 4 ký tự cuối khi log."""
    return f"…{key[-4:]}" if key else "(none)"


def classify_error(err: str) -> str:
    e = err or ""
    if "API_KEY_INVALID" in e or "API key not valid" in e or "API key expired" in e \
            or ("PERMISSION_DENIED" in e and "API key" in e):
        return DEAD_KEY
    if "PerDay" in e or "per day" in e.lower() or "no longer available" in e \
            or ("404" in e and "model" in e.lower()) or "NOT_FOUND" in e:
        return DEAD_COMBO
    if "429" in e or "RESOURCE_EXHAUSTED" in e:
        return RATE_LIMIT
    if "503" in e or "UNAVAILABLE" in e or "500" in e or "INTERNAL" in e or "overloaded" in e.lower():
        return TRANSIENT
    return OTHER


class GeminiKeyPool:
    """Danh sách cặp (key, model) còn sống, ưu tiên theo thứ tự key rồi model."""

    def __init__(self, models: list[str], keys: list[str] | None = None):
        self.keys = keys if keys is not None else load_keys()
        if not self.keys:
            raise RuntimeError("Chưa có Gemini key: set GEMINI_API_KEYS hoặc GEMINI_API_KEY")
        self.models = models
        self._dead_keys: set[str] = set()
        self._dead_combos: set[tuple[str, str]] = set()

    def combos(self) -> list[tuple[str, str]]:
        """Các cặp còn dùng được, key đầu tiên được dùng hết model trước khi sang key sau."""
        return [(k, m) for k in self.keys if k not in self._dead_keys
                for m in self.models if (k, m) not in self._dead_combos]

    def alive(self, key: str, model: str) -> bool:
        """Cặp còn dùng được không — kiểm lại giữa vòng vì key có thể vừa chết ở model trước."""
        return key not in self._dead_keys and (key, model) not in self._dead_combos

    def keys_for(self, model: str) -> list[str]:
        """Key còn dùng được cho đúng một model (khi caller cố định model, chỉ xoay key)."""
        return [k for k in self.keys
                if k not in self._dead_keys and (k, model) not in self._dead_combos]

    def report(self, key: str, model: str, err: str) -> str:
        """Ghi nhận lỗi của một cặp, trả về loại lỗi để caller quyết định chờ hay nhảy."""
        kind = classify_error(err)
        if kind == DEAD_KEY:
            self._dead_keys.add(key)
        elif kind == DEAD_COMBO:
            self._dead_combos.add((key, model))
        return kind

    @property
    def exhausted(self) -> bool:
        return not self.combos()

    def status_line(self) -> str:
        alive = self.combos()
        return f"{len(alive)} cặp key×model còn sống / {len(self.keys)} key"
