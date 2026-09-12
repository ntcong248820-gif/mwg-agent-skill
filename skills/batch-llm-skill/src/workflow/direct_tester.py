from __future__ import annotations
"""Run a small synchronous API pilot before submitting a full batch job."""
import os

from pricing import AVG_OUTPUT_TOKENS, get_model_pricing
from providers.gemini_provider import get_provider
from workflow.batch_runner import _build_system_prompt, _build_user_text
from workflow.estimator import estimate_tokens_per_row
from workflow.output_validator import validate_and_merge


def resolve_direct_test_output_path(output_path: str) -> str:
    """Derive a pilot output path from the planned batch output path."""
    base, ext = os.path.splitext(output_path)
    return f"{base}_direct_test{ext or '.csv'}"


def select_diverse_rows(
    rows: list[dict], text_columns: list[str], sample_size: int = 10
) -> list[tuple[int, dict]]:
    """Select deterministic samples by row position and text length diversity."""
    if sample_size <= 0 or not rows:
        return []
    if len(rows) <= sample_size:
        return list(enumerate(rows))

    selected: list[int] = []

    def add(idx: int) -> None:
        if 0 <= idx < len(rows) and idx not in selected and len(selected) < sample_size:
            selected.append(idx)

    add(0)
    add(len(rows) - 1)
    add(len(rows) // 2)

    lengths = sorted(
        ((idx, _row_text_len(row, text_columns)) for idx, row in enumerate(rows)),
        key=lambda item: item[1],
    )
    for idx, text_len in lengths:
        if text_len > 0:
            add(idx)
            break
    if lengths:
        add(lengths[-1][0])
        add(lengths[len(lengths) // 4][0])
        add(lengths[(len(lengths) * 3) // 4][0])

    for i in range(sample_size):
        if sample_size == 1:
            add(0)
        else:
            add(round(i * (len(rows) - 1) / (sample_size - 1)))

    idx = 0
    while len(selected) < sample_size and idx < len(rows):
        add(idx)
        idx += 1

    return [(idx, rows[idx]) for idx in sorted(selected)]


def estimate_direct_test_cost(
    sample_rows: list[dict], text_columns: list[str], provider: str, model: str
) -> dict:
    """Estimate standard synchronous API cost for the direct test sample."""
    pricing = get_model_pricing(provider, model)
    avg_tokens = estimate_tokens_per_row(
        sample_rows, text_columns, sample_size=len(sample_rows)
    )
    input_cost = len(sample_rows) * avg_tokens * pricing.get("input_per_token", 0.0)
    output_cost = (
        len(sample_rows) * AVG_OUTPUT_TOKENS * pricing.get("output_per_token", 0.0)
    )
    return {
        "rows": len(sample_rows),
        "avg_tokens_per_row": round(avg_tokens),
        "cost": round(input_cost + output_cost, 4),
    }


def show_direct_test_confirmation(
    file_path: str,
    total_rows: int,
    sample_indices: list[int],
    text_columns: list[str],
    goal: str,
    output_schema: list[dict],
    provider: str,
    model: str,
    direct_estimate: dict,
    full_batch_cost: float,
    output_path: str,
    dry_run: bool = False,
) -> bool:
    """Print direct-test review screen and capture user decision."""
    print("\n" + "=" * 62)
    print("  DIRECT API PILOT REVIEW")
    print("=" * 62)
    print(f"  FILE       {file_path}")
    print(f"  ROWS       {total_rows:,} total | {len(sample_indices)} pilot cases")
    print(f"  SAMPLE     {', '.join(str(i + 1) for i in sample_indices)}")
    print(f"  COLUMNS    {', '.join(text_columns)}")
    print(f"\n  GOAL       {goal}")
    if output_schema:
        schema = ", ".join(f"{s['name']} ({s['type']})" for s in output_schema)
        print(f"  OUTPUT     {schema}")
    print(f"\n  PROVIDER   {provider}/{model}")
    print(f"  PILOT COST ~${direct_estimate['cost']:.4f} (standard API estimate)")
    print(f"  FULL COST  ~${full_batch_cost:.4f} (batch API estimate)")
    print(f"  OUTPUT     {output_path}")
    print("\n" + "-" * 62)

    if dry_run:
        print("  DRY-RUN mode: no direct API calls will occur.\n")
        return False

    print("  [c] Confirm & Run Direct Test   [x] Cancel")
    answer = input("  Choice: ").strip().lower()
    print()
    return answer == "c"


def run_direct_test(
    rows: list[dict],
    text_columns: list[str],
    goal: str,
    output_schema: list[dict],
    provider: str,
    model: str,
    output_path: str,
) -> None:
    """Call the provider directly for sampled rows and write merged pilot output."""
    batch_provider = get_provider(provider)
    system_prompt = _build_system_prompt(goal, output_schema)
    sample_rows = []
    results = []

    for sample_pos, (source_idx, row) in enumerate(rows):
        custom_id = f"row-{sample_pos}"
        sample_row = dict(row)
        sample_row["_source_row_number"] = source_idx + 1
        sample_rows.append(sample_row)
        user_text = _build_user_text(row, text_columns)
        print(f"  Direct test row {sample_pos + 1}/{len(rows)} (source row {source_idx + 1})...")
        try:
            result = batch_provider.run_direct(
                custom_id=custom_id,
                model=model,
                system_prompt=system_prompt,
                user_text=user_text,
                output_schema=output_schema,
            )
        except Exception as exc:  # Provider errors should be visible in pilot output.
            result = {"custom_id": custom_id, "content": "", "error": str(exc)}
        results.append(result)

    validate_and_merge(
        original_rows=sample_rows,
        results=results,
        output_schema=output_schema,
        id_column=None,
        output_path=output_path,
    )


def _row_text_len(row: dict, text_columns: list[str]) -> int:
    return sum(len(str(row.get(col, "") or "")) for col in text_columns)
