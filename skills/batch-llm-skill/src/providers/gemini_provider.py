from __future__ import annotations
"""Google Gemini Batch API provider — uses /v1beta/batches (async, not batchGenerateContent)."""
import json
import os
import tempfile
import time
import requests
from .base import BatchProvider
from .gemini_key_pool import GeminiKeyPool, RATE_LIMIT, TRANSIENT, OTHER, mask

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Inline payload limit per Google docs
INLINE_SIZE_LIMIT_BYTES = 20 * 1024 * 1024  # 20 MB


class GeminiProvider(BatchProvider):

    def __init__(self):
        # Nhiều key free: GEMINI_API_KEYS (phẩy), rồi GEMINI_API_KEY, rồi GOOGLE_API_KEY
        self._pool = GeminiKeyPool(models=[])
        self._api_key = self._pool.keys[0]
        # Batch job thuộc về project của key đã submit → nhớ để poll/fetch đúng key
        self._job_keys: dict[str, str] = {}

    def _headers(self, key: str | None = None) -> dict:
        return {"Content-Type": "application/json", "x-goog-api-key": key or self._api_key}

    def _post_rotating(self, url: str, model: str, rounds: int = 3, **kwargs) -> tuple[requests.Response, str]:
        """POST, gặp quota/rate-limit thì nhảy sang key kế; chỉ ngủ khi mọi key đều nghẽn."""
        extra_headers = kwargs.pop("headers", {})
        last_err = ""
        for round_idx in range(rounds):
            keys = self._pool.keys_for(model)
            if not keys:
                break
            waitable = False
            for key in keys:
                resp = requests.post(url, headers={**self._headers(key), **extra_headers}, **kwargs)
                if resp.ok:
                    self._api_key = key
                    return resp, key
                last_err = f"{resp.status_code} " + " ".join(resp.text[:300].split())
                kind = self._pool.report(key, model, last_err)
                print(f"  [gemini {mask(key)} {model}] {kind}: {last_err[:100]}")
                if kind == OTHER:
                    # lỗi request, đổi key không cứu được
                    resp.raise_for_status()
                waitable = waitable or kind in (RATE_LIMIT, TRANSIENT)
            if waitable and round_idx < rounds - 1:
                time.sleep(35)
        raise RuntimeError(f"Gemini: hết key dùng được cho {model} ({len(self._pool.keys)} key). Lỗi cuối: {last_err[:200]}")

    def _get_job(self, url: str, batch_id: str, timeout: int) -> requests.Response:
        """GET tài nguyên của một batch job; job lạ key thì dò lần lượt các key còn lại."""
        known = self._job_keys.get(batch_id)
        order = ([known] if known else []) + [k for k in self._pool.keys if k != known]
        resp = None
        for key in order:
            resp = requests.get(url, headers=self._headers(key), timeout=timeout)
            if resp.status_code not in (403, 404):
                self._job_keys[batch_id] = key
                return resp
        return resp

    def submit_batch(self, jsonl_path: str, model: str) -> str:
        """
        Create async batch job via POST /v1beta/batches.
        Auto-selects inline vs file-based mode by payload size.
        Returns batch "name" (e.g. "batches/abc123") as batch_id.
        """
        requests_list = _read_jsonl_requests(jsonl_path)

        # Estimate inline payload size
        inline_payload = {"batch": {"input_config": {"requests": {"requests": requests_list}}}}
        payload_bytes = len(json.dumps(inline_payload, ensure_ascii=False).encode("utf-8"))

        if payload_bytes <= INLINE_SIZE_LIMIT_BYTES:
            return self._submit_inline(requests_list, model)
        else:
            return self._submit_via_file(jsonl_path, requests_list, model)

    def _submit_inline(self, requests_list: list[dict], model: str) -> str:
        """Submit inline requests (< 20MB)."""
        payload = {
            "batch": {
                "input_config": {
                    "requests": {"requests": requests_list}
                }
            }
        }
        resp, key = self._post_rotating(f"{GEMINI_API_BASE}/batches", model, json=payload, timeout=120)
        data = resp.json()
        name = data.get("name", "")
        if not name:
            raise RuntimeError(f"Gemini batch create returned no job name: {data}")
        self._job_keys[name] = key
        return name

    def _submit_via_file(self, jsonl_path: str, requests_list: list[dict], model: str) -> str:
        """Upload JSONL to Files API, then create batch with file reference (> 20MB)."""
        file_name, key = self._upload_jsonl_file(jsonl_path, model)
        payload = {
            "batch": {
                "input_config": {"file_name": file_name}
            }
        }
        # File upload thuộc project của key vừa dùng → create batch bắt buộc cùng key, không xoay
        resp = requests.post(
            f"{GEMINI_API_BASE}/batches",
            headers=self._headers(key),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        name = data.get("name", "")
        if not name:
            raise RuntimeError(f"Gemini batch create (file mode) returned no job name: {data}")
        self._job_keys[name] = key
        return name

    def _upload_jsonl_file(self, path: str, model: str) -> tuple[str, str]:
        """Upload file via Files API, return (file name e.g. 'files/abc123', key đã dùng)."""
        with open(path, "rb") as f:
            data = f.read()
        resp, key = self._post_rotating(
            f"{GEMINI_API_BASE}/files",
            model,
            headers={"Content-Type": "application/jsonl"},
            data=data,
            timeout=120,
        )
        return resp.json().get("file", {}).get("name", ""), key

    def poll_status(self, batch_id: str) -> dict:
        """
        Poll batch job status via GET /v1beta/{batch_name}.
        Returns normalized dict with status, output_file_id, error_message.
        """
        url = f"{GEMINI_API_BASE}/{batch_id}"
        resp = self._get_job(url, batch_id, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        state = data.get("state", "JOB_STATE_PENDING")
        error = data.get("error")

        if state == "JOB_STATE_SUCCEEDED":
            # output_file_id carries the batch_id itself — results fetched by re-GETting the job
            dest = data.get("dest", {})
            output_file_id = dest.get("fileName") or batch_id
            return {"status": "completed", "output_file_id": output_file_id, "error_message": None}

        if state in {"JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}:
            msg = error.get("message") if error else state
            return {"status": "failed", "output_file_id": None, "error_message": msg}

        # JOB_STATE_PENDING or JOB_STATE_RUNNING
        return {"status": "in_progress", "output_file_id": None, "error_message": None}

    def fetch_results(self, batch_id: str, output_file_id: str) -> list[dict]:
        """
        Fetch completed results.
        - If output_file_id == batch_id: inline mode, parse dest.inlinedResponses
        - Otherwise: file-based mode, download JSONL from Files API
        """
        if output_file_id == batch_id:
            return self._fetch_inline_results(batch_id)
        return self._fetch_file_results(output_file_id)

    def run_direct(
        self,
        custom_id: str,
        model: str,
        system_prompt: str,
        user_text: str,
        output_schema: list[dict] | None = None,
    ) -> dict:
        """Run one synchronous generateContent request for direct pilot testing."""
        model_name = model if model.startswith("models/") else f"models/{model}"
        max_output_tokens = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "500"))
        payload = {
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\n{user_text}"}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": max_output_tokens,
            },
        }
        resp, _ = self._post_rotating(
            f"{GEMINI_API_BASE}/{model_name}:generateContent",
            model_name,
            json=payload,
            timeout=120,
        )
        data = resp.json()
        candidates = data.get("candidates", [])
        choice = candidates[0] if candidates else {}
        text = choice.get("content", {}).get("parts", [{}])[0].get("text", "")
        usage = data.get("usageMetadata", {})
        return {
            "custom_id": custom_id,
            "content": text,
            "error": None,
            "meta": {
                "finish_reason": choice.get("finishReason"),
                "prompt_tokens": usage.get("promptTokenCount"),
                "completion_tokens": usage.get("candidatesTokenCount"),
                "total_tokens": usage.get("totalTokenCount"),
            },
        }

    def _fetch_inline_results(self, batch_id: str) -> list[dict]:
        """Parse results from dest.inlinedResponses in the completed batch job."""
        url = f"{GEMINI_API_BASE}/{batch_id}"
        resp = self._get_job(url, batch_id, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        results = []
        inlined = data.get("dest", {}).get("inlinedResponses", [])
        for item in inlined:
            key = item.get("key", str(len(results)))
            response = item.get("response", {})
            candidates = response.get("candidates", [])
            if not candidates:
                results.append({"custom_id": key, "content": None, "error": "no candidates"})
                continue
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            results.append({"custom_id": key, "content": text, "error": None})
        return results

    def _fetch_file_results(self, file_name: str) -> list[dict]:
        """Download JSONL output file from Files API and parse each line."""
        resp = self._get_job(f"{GEMINI_API_BASE}/{file_name}:download", file_name, timeout=120)
        resp.raise_for_status()

        results = []
        for line in resp.content.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            key = obj.get("key", str(len(results)))
            response = obj.get("response", {})
            candidates = response.get("candidates", [])
            if not candidates:
                results.append({"custom_id": key, "content": None, "error": "no candidates"})
                continue
            text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
            results.append({"custom_id": key, "content": text, "error": None})
        return results


def build_gemini_jsonl_line(custom_id: str, system_prompt: str, user_text: str, model: str = "gemini-2.0-flash") -> dict:
    """Build a single request line for Gemini Batch API. Uses 'key' field (not 'customId')."""
    return {
        "key": custom_id,
        "request": {
            "model": f"models/{model}",
            "contents": [
                {"parts": [{"text": f"{system_prompt}\n\n{user_text}"}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "maxOutputTokens": 500,
            },
        },
    }


def _read_jsonl_requests(path: str) -> list[dict]:
    reqs = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                reqs.append(json.loads(line))
    return reqs


def get_provider(provider_name: str) -> BatchProvider:
    """Factory: return provider instance by name."""
    if provider_name == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider()
    if provider_name == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown provider: {provider_name}. Choose: openai, gemini")
