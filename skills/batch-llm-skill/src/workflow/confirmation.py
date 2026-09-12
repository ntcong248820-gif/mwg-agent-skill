from __future__ import annotations
"""Display the pre-submission review screen and capture user decision."""
from parsers.csv_parser import get_column_stats


def show_confirmation(
    file_path: str,
    rows: list[dict],
    columns: list[str],
    text_columns: list[str],
    goal: str,
    output_schema: list[dict],
    provider: str,
    model: str,
    estimates: dict,
    output_path: str,
    dry_run: bool = False,
) -> bool:
    """
    Print the confirmation screen and prompt user.
    Returns True if user confirms, False otherwise.
    In dry_run mode, always returns False (caller should exit after this).
    """
    stats = get_column_stats(rows, text_columns)
    per_provider = estimates.get("per_provider", {})
    selected_info = per_provider.get(provider, {}).get(model, {})

    print("\n" + "═" * 62)
    print("  BATCH LLM SUBMISSION REVIEW")
    print("═" * 62)

    # File & data
    print(f"  FILE    {file_path}")
    print(f"  ROWS    {len(rows):,}   OUTPUT  {output_path}")

    # Columns
    print("\n  INPUT COLUMNS")
    for col in text_columns:
        s = stats.get(col, {})
        avg = s.get("avg_len", "?")
        print(f"    {col}  (avg {avg} chars)")

    # Goal
    print(f"\n  GOAL    {goal}")

    # Output schema
    if output_schema:
        schema_str = ", ".join(f"{s['name']} ({s['type']})" for s in output_schema)
        print(f"  OUTPUT  {schema_str}")

    # Cost comparison across providers
    print("\n  COST COMPARISON (batch pricing, 50% off standard)")
    _print_cost_row(per_provider, provider, model, selected=True)

    # Show cheapest alternative if different from selected
    cheapest_p, cheapest_m, cheapest_info = _find_cheapest(per_provider, provider, model)
    if cheapest_p and cheapest_info:
        _print_cost_row(per_provider, cheapest_p, cheapest_m, selected=False, label="cheapest alt")

    # Batch plan
    num_chunks = selected_info.get("num_chunks", "?")
    chunk_size = selected_info.get("chunk_size", "?")
    window = selected_info.get("window", "?")
    print(f"\n  PLAN    {num_chunks} chunks × {chunk_size:,} rows  |  window: {window}")
    print(f"  TOKENS  ~{estimates.get('avg_tokens_per_row', '?')} tokens/row")

    print("\n" + "─" * 62)

    if dry_run:
        print("  DRY-RUN mode: no submission will occur.\n")
        return False

    print("  [c] Confirm & Submit   [x] Cancel")
    answer = input("  Choice: ").strip().lower()
    print()
    return answer == "c"


def _print_cost_row(
    per_provider: dict, provider: str, model: str, selected: bool, label: str = ""
) -> None:
    info = per_provider.get(provider, {}).get(model, {})
    cost = info.get("cost", 0)
    window = info.get("window", "?")
    webhooks = " + webhooks" if info.get("supports_webhooks") else ""
    marker = ">>>" if selected else "   "
    tag = f"  [{label}]" if label else ""
    print(f"  {marker}  {provider}/{model}  →  ${cost:.4f}{tag}  ({window}{webhooks})")


def _find_cheapest(per_provider: dict, current_provider: str, current_model: str):
    """Return (provider, model, info) of cheapest option excluding current."""
    best = None
    best_cost = float("inf")
    best_p = best_m = None
    for p, models in per_provider.items():
        for m, info in models.items():
            if p == current_provider and m == current_model:
                continue
            c = info.get("cost", float("inf"))
            if c < best_cost:
                best_cost = c
                best = info
                best_p, best_m = p, m
    return best_p, best_m, best
