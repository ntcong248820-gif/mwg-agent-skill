from __future__ import annotations
"""Google Gemini Batch API provider — uses /v1beta/batches (async, not batchGenerateContent)."""
import json
import os
import tempfile
import requests
from .base import BatchProvider

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Inline payload limit per Google docs
INLINE_SIZE_LIMIT_BYTES = 20 * 1024 * 1024  # 20 MB


class GeminiProvider(BatchProvider):

    def __init__(self):
        self._api_key = os.environ.get("GOOGLE_API_KEY")
        if not self._api_key:
            raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "x-goog-api-key": self._api_key}

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
        resp = requests.post(
            f"{GEMINI_API_BASE}/batches",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        name = data.get("name", "")
        if not name:
            raise RuntimeError(f"Gemini batch create returned no job name: {data}")
        return name

    def _submit_via_file(self, jsonl_path: str, requests_list: list[dict], model: str) -> str:
        """Upload JSONL to Files API, then create batch with file reference (> 20MB)."""
        file_name = self._upload_jsonl_file(jsonl_path)
        payload = {
            "batch": {
                "input_config": {"file_name": file_name}
            }
        }
        resp = requests.post(
            f"{GEMINI_API_BASE}/batches",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        name = data.get("name", "")
        if not name:
            raise RuntimeError(f"Gemini batch create (file mode) returned no job name: {data}")
        return name

    def _upload_jsonl_file(self, path: str) -> str:
        """Upload file via Files API, return file name (e.g. 'files/abc123')."""
        with open(path, "rb") as f:
            data = f.read()
        resp = requests.post(
            f"{GEMINI_API_BASE}/files",
            headers={**self._headers(), "Content-Type": "application/jsonl"},
            data=data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json().get("file", {}).get("name", "")

    def poll_status(self, batch_id: str) -> dict:
        """
        Poll batch job status via GET /v1beta/{batch_name}.
        Returns normalized dict with status, output_file_id, error_message.
        """
        url = f"{GEMINI_API_BASE}/{batch_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
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
        resp = requests.post(
            f"{GEMINI_API_BASE}/{model_name}:generateContent",
            headers=self._headers(),
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
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
        resp = requests.get(url, headers=self._headers(), timeout=60)
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
        resp = requests.get(
            f"{GEMINI_API_BASE}/{file_name}:download",
            headers={**self._headers(), "Content-Type": None},
            timeout=120,
        )
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
