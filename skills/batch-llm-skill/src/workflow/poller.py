from __future__ import annotations
"""Poll a batch job until it reaches a terminal state."""
import time
from providers.base import BatchProvider

POLL_INTERVAL_SECONDS = 30
MAX_WAIT_HOURS = 50  # Gemini window is 48h; add buffer


def poll_until_complete(provider: BatchProvider, batch_id: str, chunk_label: str = "") -> dict:
    """
    Poll provider until batch_id reaches a terminal status.
    Returns the final status dict: {status, output_file_id, error_message}
    Raises RuntimeError on failure or expiry.
    """
    max_polls = int((MAX_WAIT_HOURS * 3600) / POLL_INTERVAL_SECONDS)
    label = f"[{chunk_label}] " if chunk_label else ""

    for attempt in range(max_polls):
        result = provider.poll_status(batch_id)
        status = result.get("status", "in_progress")

        if provider.is_terminal_status(status):
            if provider.is_success_status(status):
                print(f"  {label}Complete.")
                return result
            raise RuntimeError(
                f"{label}Batch {batch_id} ended with status '{status}': "
                f"{result.get('error_message', 'no details')}"
            )

        elapsed_min = ((attempt + 1) * POLL_INTERVAL_SECONDS) // 60
        print(f"  {label}Status: {status}  (waited ~{elapsed_min}m, polling every {POLL_INTERVAL_SECONDS}s)")
        time.sleep(POLL_INTERVAL_SECONDS)

    raise RuntimeError(f"{label}Timed out after {MAX_WAIT_HOURS}h waiting for batch {batch_id}.")
