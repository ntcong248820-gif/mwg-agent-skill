from __future__ import annotations
"""Validate LLM output rows against schema, deduplicate, and merge with original data."""
import csv
import json
import os


def validate_and_merge(
    original_rows: list[dict],
    results: list[dict],
    output_schema: list[dict],
    id_column: str | None,
    output_path: str,
) -> None:
    """
    Merge batch results back into original rows, validate schema, write output file.
    - Deduplicates results by custom_id (handles crash-resume re-runs).
    - Rows with parse errors keep _parse_error=true and _raw_response columns.
    - Never silently drops rows.
    """
    # Deduplicate results — last write wins for same custom_id
    deduped: dict[str, dict] = {}
    for r in results:
        deduped[r["custom_id"]] = r

    # Build lookup: custom_id → parsed output dict
    schema_fields = [s["name"] for s in output_schema] if output_schema else []
    parsed_map: dict[str, dict] = {}
    for custom_id, result in deduped.items():
        parsed_map[custom_id] = _parse_result(result, schema_fields)

    # Map global row index → parsed result (custom_id format: "row-{global_idx}")
    row_results: list[dict] = [{} for _ in range(len(original_rows))]
    for custom_id, parsed in parsed_map.items():
        row_idx = _resolve_row_index(custom_id, len(original_rows))
        if row_idx is not None:
            row_results[row_idx] = parsed

    # Merge original rows with results
    merged = []
    for i, orig in enumerate(original_rows):
        row = dict(orig)
        row.update(row_results[i] or {"_parse_error": True, "_raw_response": "missing"})
        merged.append(row)

    _write_output(merged, output_path)
    _print_summary(merged, schema_fields)


def _parse_result(result: dict, schema_fields: list[str]) -> dict:
    """Parse content JSON and validate fields. Returns dict with parsed values or error flags."""
    if result.get("error"):
        return _with_metadata(
            {"_parse_error": True, "_raw_response": result.get("error", "")}, result
        )
    content = result.get("content", "")
    if not content:
        return _with_metadata({"_parse_error": True, "_raw_response": ""}, result)
    try:
        # Strip markdown code fences if present
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        parsed = json.loads(text)
        if schema_fields:
            parsed = {f: parsed.get(f, "") for f in schema_fields}
        return _with_metadata(parsed, result)
    except (json.JSONDecodeError, ValueError):
        return _with_metadata(
            {"_parse_error": True, "_raw_response": content[:500]}, result
        )


def _with_metadata(parsed: dict, result: dict) -> dict:
    metadata = result.get("meta") or {}
    for key, value in metadata.items():
        parsed[f"_{key}"] = "" if value is None else value
    return parsed


def _resolve_row_index(custom_id: str, total_rows: int) -> int | None:
    """Extract global row index from custom_id format 'row-{global_idx}'."""
    try:
        idx = int(custom_id.replace("row-", ""))
        if 0 <= idx < total_rows:
            return idx
        return None
    except ValueError:
        return None


def _write_output(rows: list[dict], output_path: str) -> None:
    ext = os.path.splitext(output_path)[1].lower()
    if ext == ".jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    else:
        if not rows:
            return
        fieldnames = list(rows[0].keys())
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


def _print_summary(rows: list[dict], schema_fields: list[str]) -> None:
    total = len(rows)
    errors = sum(1 for r in rows if r.get("_parse_error"))
    ok = total - errors
    print(f"\nMerge complete: {ok:,} OK  |  {errors:,} parse errors  |  {total:,} total rows")
    if schema_fields and ok > 0:
        # Show value distribution for first schema field
        field = schema_fields[0]
        counts: dict[str, int] = {}
        for r in rows:
            v = str(r.get(field, "_error"))
            counts[v] = counts.get(v, 0) + 1
        print(f"  {field} distribution:")
        for val, cnt in sorted(counts.items(), key=lambda x: -x[1])[:8]:
            pct = cnt / total * 100
            print(f"    {val:<20} {cnt:>6,}  ({pct:.1f}%)")
