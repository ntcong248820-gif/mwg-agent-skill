from __future__ import annotations
"""Core batch orchestration: build JSONL chunks, submit, poll, collect results."""
import json
import os
import tempfile

from providers.gemini_provider import GeminiProvider, build_gemini_jsonl_line, get_provider
from providers.openai_provider import OpenAIProvider, build_openai_jsonl_line
from workflow.poller import poll_until_complete
from workflow.state_manager import (
    get_in_progress_batch_id, is_chunk_done,
    mark_chunk_done, mark_chunk_failed, mark_chunk_submitted, save_state,
)

MAX_RETRIES = 3


def submit_all_chunks(
    state: dict,
    state_path: str,
    rows: list[dict],
    text_columns: list[str],
    id_column: str | None,
    goal: str,
    output_schema: list[dict],
    provider: str,
    model: str,
) -> list[str]:
    """
    Submit all pending chunks to the batch API without polling.
    Returns list of submitted batch_ids.
    Call fetch_all_results() later to collect output.
    """
    batch_provider = get_provider(provider)
    system_prompt = _build_system_prompt(goal, output_schema)
    total_chunks = state["total_chunks"]
    submitted = []

    for chunk_idx in range(total_chunks):
        if is_chunk_done(state, chunk_idx):
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: already completed, skipping.")
            continue

        existing_batch_id = get_in_progress_batch_id(state, chunk_idx)
        if existing_batch_id:
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: already submitted ({existing_batch_id}), skipping.")
            submitted.append(existing_batch_id)
            continue

        chunk_info = state["chunks"][str(chunk_idx)]
        start, end = chunk_info["start"], chunk_info["end"]
        chunk_rows = rows[start:end]

        print(f"  Submitting chunk {chunk_idx + 1}/{total_chunks}  ({len(chunk_rows)} rows)...")
        jsonl_path = _write_chunk_jsonl(
            chunk_rows, text_columns, id_column, system_prompt,
            model, provider, chunk_idx, global_start=start, output_schema=output_schema,
        )
        batch_id = batch_provider.submit_batch(jsonl_path, model)
        mark_chunk_submitted(state, state_path, chunk_idx, batch_id)
        os.unlink(jsonl_path)
        submitted.append(batch_id)
        print(f"    → {batch_id}")

    return submitted


def fetch_all_results(
    state: dict,
    state_path: str,
    provider: str,
) -> tuple[list[dict], list[int]]:
    """
    Check status of all submitted chunks once (non-blocking).
    Collects results for completed chunks, leaves in-progress ones untouched.
    Returns (results, still_pending_chunk_indices).
    """
    batch_provider = get_provider(provider)
    total_chunks = state["total_chunks"]
    all_results = []
    still_pending = []

    for chunk_idx in range(total_chunks):
        chunk_info = state["chunks"][str(chunk_idx)]

        if is_chunk_done(state, chunk_idx):
            output_file_id = chunk_info.get("output_file_id")
            batch_id = chunk_info.get("batch_id")
            if output_file_id and batch_id:
                results = batch_provider.fetch_results(batch_id, output_file_id)
                all_results.extend(results)
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: done ✓ ({len(results) if output_file_id else 0} rows)")
            continue

        batch_id = get_in_progress_batch_id(state, chunk_idx)
        if not batch_id:
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: not yet submitted.")
            still_pending.append(chunk_idx)
            continue

        status_result = batch_provider.poll_status(batch_id)
        status = status_result.get("status", "in_progress")

        if batch_provider.is_success_status(status):
            output_file_id = status_result.get("output_file_id")
            if not output_file_id:
                mark_chunk_failed(state, state_path, chunk_idx, "completed but output_file_id missing")
                print(f"  Chunk {chunk_idx + 1}/{total_chunks}: FAILED — no output file id")
                continue
            results = batch_provider.fetch_results(batch_id, output_file_id)
            mark_chunk_done(state, state_path, chunk_idx, output_file_id)
            all_results.extend(results)
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: completed ✓  ({len(results)} rows)")
        elif batch_provider.is_terminal_status(status):
            err = status_result.get("error_message", "unknown error")
            mark_chunk_failed(state, state_path, chunk_idx, err)
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: FAILED — {err}")
        else:
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: still processing ({status})")
            still_pending.append(chunk_idx)

    return all_results, still_pending


def run_batches(
    state: dict,
    state_path: str,
    rows: list[dict],
    text_columns: list[str],
    id_column: str | None,
    goal: str,
    output_schema: list[dict],
    provider: str,
    model: str,
) -> list[dict]:
    """
    Iterate through chunks, submit each to the batch API, poll for completion,
    and return aggregated results as a flat list of {custom_id, content, error}.
    Skips chunks already marked done in state (crash recovery).
    """
    batch_provider = get_provider(provider)
    system_prompt = _build_system_prompt(goal, output_schema)
    total_chunks = state["total_chunks"]
    all_results = []

    for chunk_idx in range(total_chunks):
        if is_chunk_done(state, chunk_idx):
            print(f"  Chunk {chunk_idx + 1}/{total_chunks}: already done, skipping.")
            continue

        chunk_info = state["chunks"][str(chunk_idx)]
        start, end = chunk_info["start"], chunk_info["end"]
        chunk_rows = rows[start:end]

        print(f"\nChunk {chunk_idx + 1}/{total_chunks}  ({len(chunk_rows)} rows)")

        # Resume in-progress chunk after crash
        batch_id = get_in_progress_batch_id(state, chunk_idx)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if not batch_id:
                    jsonl_path = _write_chunk_jsonl(
                        chunk_rows, text_columns, id_column, system_prompt,
                        model, provider, chunk_idx, global_start=start, output_schema=output_schema,
                    )
                    print(f"  Submitting... (attempt {attempt})")
                    batch_id = batch_provider.submit_batch(jsonl_path, model)
                    mark_chunk_submitted(state, state_path, chunk_idx, batch_id)
                    os.unlink(jsonl_path)

                status_result = poll_until_complete(
                    batch_provider, batch_id, chunk_label=f"{chunk_idx + 1}/{total_chunks}"
                )
                results = batch_provider.fetch_results(batch_id, status_result["output_file_id"])
                mark_chunk_done(state, state_path, chunk_idx, status_result["output_file_id"])
                all_results.extend(results)
                break

            except RuntimeError as e:
                print(f"  ERROR (attempt {attempt}/{MAX_RETRIES}): {e}")
                batch_id = None  # Force re-submit on retry
                if attempt == MAX_RETRIES:
                    mark_chunk_failed(state, state_path, chunk_idx, str(e))
                    print(f"  Chunk {chunk_idx} failed after {MAX_RETRIES} attempts. Continuing.")

    return all_results


def _build_system_prompt(goal: str, output_schema: list[dict]) -> str:
    schema_lines = ""
    if output_schema:
        fields = "\n".join(f'  "{s["name"]}": "{s["type"]}"' for s in output_schema)
        schema_lines = f"\n\nRespond ONLY with valid JSON matching this schema:\n{{\n{fields}\n}}"
    return f"You are a data processing assistant. Task: {goal}.{schema_lines}"


def _write_chunk_jsonl(
    chunk_rows: list[dict],
    text_columns: list[str],
    id_column: str | None,
    system_prompt: str,
    model: str,
    provider: str,
    chunk_idx: int,
    global_start: int = 0,
    output_schema: list[dict] | None = None,
) -> str:
    """Write chunk to a temp JSONL file and return path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", prefix=f"batch_chunk_{chunk_idx}_",
        delete=False, encoding="utf-8",
    )
    for i, row in enumerate(chunk_rows):
        # Use global row index so output_validator can map back without knowing chunk_size
        custom_id = f"row-{global_start + i}"
        user_text = _build_user_text(row, text_columns)
        if provider == "openai":
            line = build_openai_jsonl_line(
                custom_id, model, system_prompt, user_text, output_schema
            )
        else:
            line = build_gemini_jsonl_line(custom_id, system_prompt, user_text, model)
        tmp.write(json.dumps(line, ensure_ascii=False) + "\n")
    tmp.close()
    return tmp.name


def _build_user_text(row: dict, text_columns: list[str]) -> str:
    parts = []
    for col in text_columns:
        val = str(row.get(col, "") or "").strip()
        if val:
            parts.append(f"{col}: {val}")
    return "\n".join(parts)
