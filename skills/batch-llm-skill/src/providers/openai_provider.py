from __future__ import annotations
"""OpenAI Batch API provider implementation."""
import json
import os
from .base import BatchProvider


class OpenAIProvider(BatchProvider):

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")
        self._client = OpenAI(api_key=api_key)

    def submit_batch(self, jsonl_path: str, model: str) -> str:
        """Upload JSONL file and create a batch job. Returns batch_id."""
        with open(jsonl_path, "rb") as f:
            uploaded = self._client.files.create(file=f, purpose="batch")

        batch = self._client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
        )
        return batch.id

    def poll_status(self, batch_id: str) -> dict:
        """Return normalized status dict."""
        batch = self._client.batches.retrieve(batch_id)
        status_map = {
            "validating": "in_progress",
            "in_progress": "in_progress",
            "finalizing": "in_progress",
            "completed": "completed",
            "failed": "failed",
            "expired": "expired",
            "cancelling": "in_progress",
            "cancelled": "failed",
        }
        normalized = status_map.get(batch.status, "in_progress")
        return {
            "status": normalized,
            "output_file_id": batch.output_file_id,
            "error_message": _extract_openai_error(batch),
        }

    def fetch_results(self, batch_id: str, output_file_id: str) -> list[dict]:
        """Download output JSONL and parse into normalized result rows."""
        content = self._client.files.content(output_file_id).content
        results = []
        for line in content.decode("utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            custom_id = obj.get("custom_id", "")
            response_body = obj.get("response", {}).get("body", {})
            error = obj.get("error")

            if error:
                results.append({"custom_id": custom_id, "content": None, "error": str(error)})
                continue

            choices = response_body.get("choices", [])
            content_text = choices[0]["message"]["content"] if choices else None
            results.append({"custom_id": custom_id, "content": content_text, "error": None})
        return results

    def run_direct(
        self,
        custom_id: str,
        model: str,
        system_prompt: str,
        user_text: str,
        output_schema: list[dict] | None = None,
    ) -> dict:
        """Run one synchronous Chat Completions request for direct pilot testing."""
        body = build_openai_jsonl_line(
            custom_id, model, system_prompt, user_text, output_schema
        )["body"]
        response = self._client.chat.completions.create(**body)
        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice else None
        usage = getattr(response, "usage", None)
        return {
            "custom_id": custom_id,
            "content": content,
            "error": None,
            "meta": {
                "finish_reason": getattr(choice, "finish_reason", None) if choice else None,
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }


def build_openai_jsonl_line(
    custom_id: str,
    model: str,
    system_prompt: str,
    user_text: str,
    output_schema: list[dict] | None = None,
) -> dict:
    """Build a single JSONL request line for OpenAI Batch API."""
    max_completion_tokens = int(
        os.environ.get("OPENAI_MAX_COMPLETION_TOKENS")
        or (2048 if model.startswith("gpt-5") else 500)
    )
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_completion_tokens": max_completion_tokens,
        "response_format": _build_response_format(output_schema),
    }
    if model.startswith("gpt-5"):
        body["reasoning_effort"] = os.environ.get("OPENAI_REASONING_EFFORT", "minimal")
        body["verbosity"] = os.environ.get("OPENAI_VERBOSITY", "low")
    # Reasoning models (o-series, gpt-5+) don't support temperature — omit entirely.
    return {
        "custom_id": custom_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": body,
    }


def _build_response_format(output_schema: list[dict] | None) -> dict:
    """Use strict Structured Outputs when a schema is available."""
    if not output_schema:
        return {"type": "json_object"}

    properties = {}
    required = []
    for field in output_schema:
        name = field["name"]
        raw_type = field.get("type", "string")
        required.append(name)
        if raw_type == "boolean":
            properties[name] = {"type": "boolean"}
        elif "|" in raw_type:
            properties[name] = {"type": "string", "enum": raw_type.split("|")}
        else:
            properties[name] = {"type": "string"}

    return {
        "type": "json_schema",
        "json_schema": {
            "name": "batch_row_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


def _extract_openai_error(batch) -> str | None:
    if hasattr(batch, "errors") and batch.errors:
        msgs = [e.message for e in (batch.errors.data or []) if hasattr(e, "message")]
        return "; ".join(msgs) if msgs else None
    return None
