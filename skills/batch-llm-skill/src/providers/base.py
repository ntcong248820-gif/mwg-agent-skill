from __future__ import annotations
"""Abstract base class for batch API providers."""
from abc import ABC, abstractmethod


class BatchProvider(ABC):
    """
    Interface contract for batch providers (OpenAI, Gemini).
    All methods raise RuntimeError on unrecoverable errors.
    """

    @abstractmethod
    def submit_batch(self, jsonl_path: str, model: str) -> str:
        """
        Upload a JSONL file and create a batch job.
        Returns batch_id (provider-specific string).
        """

    @abstractmethod
    def poll_status(self, batch_id: str) -> dict:
        """
        Check the current status of a batch job.

        Returns dict with keys:
          - status: "pending" | "in_progress" | "completed" | "failed" | "expired"
          - output_file_id: str | None  (set when status == "completed")
          - error_message: str | None   (set when status == "failed")
        """

    @abstractmethod
    def fetch_results(self, batch_id: str, output_file_id: str) -> list[dict]:
        """
        Download and parse completed batch results.

        Returns list of dicts, each with:
          - custom_id: str   (matches the id field in the submitted JSONL)
          - content: str     (raw text response from the model)
          - error: str|None  (set if this individual request failed)
        """

    def run_direct(
        self,
        custom_id: str,
        model: str,
        system_prompt: str,
        user_text: str,
        output_schema: list[dict] | None = None,
    ) -> dict:
        """Run one synchronous API request for pre-batch output validation."""
        raise NotImplementedError("Provider does not support direct test mode.")

    def is_terminal_status(self, status: str) -> bool:
        return status in {"completed", "failed", "expired", "cancelled"}

    def is_success_status(self, status: str) -> bool:
        return status == "completed"
