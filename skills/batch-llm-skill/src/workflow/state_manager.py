from __future__ import annotations
"""Persist and recover batch job state to enable crash recovery."""
import json
import math
import os

STATE_FILE_SUFFIX = ".batch_state.json"


def init_state(
    state_path: str,
    provider: str,
    model: str,
    total_rows: int,
    chunk_size: int,
    rows: list[dict],
    id_column: str | None,
    input_file: str = "",
    output_path: str = "",
    text_columns: list[str] | None = None,
    goal: str = "",
    output_schema: list[dict] | None = None,
) -> dict:
    """Create a fresh state file. Returns the state dict."""
    total_chunks = math.ceil(total_rows / chunk_size)
    chunks = {}
    for i in range(total_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, total_rows)
        chunk_rows = rows[start:end]
        row_ids = [str(r.get(id_column, start + j)) for j, r in enumerate(chunk_rows)]
        chunks[str(i)] = {
            "batch_id": None,
            "status": "pending",
            "output_file_id": None,
            "row_ids": row_ids,
            "start": start,
            "end": end,
        }

    state = {
        "provider": provider,
        "model": model,
        "total_rows": total_rows,
        "chunk_size": chunk_size,
        "total_chunks": total_chunks,
        "completed_chunks": {},
        "chunks": chunks,
        "meta": {
            "input_file": input_file,
            "output_path": output_path,
            "text_columns": text_columns or [],
            "goal": goal,
            "output_schema": output_schema or [],
            "id_column": id_column,
        },
    }
    save_state(state_path, state)
    return state


def load_state(state_path: str) -> dict | None:
    """Load state if file exists, else return None."""
    if not os.path.exists(state_path):
        return None
    try:
        with open(state_path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_state(state_path: str, state: dict) -> None:
    """Atomically write state via temp file to avoid partial writes on crash."""
    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, state_path)


def mark_chunk_submitted(state: dict, state_path: str, chunk_idx: int, batch_id: str) -> None:
    key = str(chunk_idx)
    state["chunks"][key]["batch_id"] = batch_id
    state["chunks"][key]["status"] = "submitted"
    save_state(state_path, state)


def mark_chunk_done(
    state: dict, state_path: str, chunk_idx: int, output_file_id: str
) -> None:
    key = str(chunk_idx)
    state["chunks"][key]["status"] = "completed"
    state["chunks"][key]["output_file_id"] = output_file_id
    state["completed_chunks"][key] = True
    save_state(state_path, state)


def mark_chunk_failed(state: dict, state_path: str, chunk_idx: int, error: str) -> None:
    key = str(chunk_idx)
    state["chunks"][key]["status"] = "failed"
    state["chunks"][key]["error"] = error
    save_state(state_path, state)


def is_chunk_done(state: dict, chunk_idx: int) -> bool:
    return str(chunk_idx) in state.get("completed_chunks", {})


def get_in_progress_batch_id(state: dict, chunk_idx: int) -> str | None:
    """Return existing batch_id if chunk was submitted but not finished (resume after crash)."""
    chunk = state.get("chunks", {}).get(str(chunk_idx), {})
    if chunk.get("status") == "submitted" and chunk.get("batch_id"):
        return chunk["batch_id"]
    return None
