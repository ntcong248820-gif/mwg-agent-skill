#!/usr/bin/env python3
"""
batch-llm-skill entry point.

Modes:
  default              Submit + poll + merge in one blocking session
  --async              Submit all chunks, save state, exit immediately
  --fetch <output>     Check status and collect results for a prior --async run
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from parsers.csv_parser import load_file
from workflow.estimator import estimate_cost
from workflow.confirmation import show_confirmation
from workflow.state_manager import load_state, init_state, STATE_FILE_SUFFIX
from workflow.batch_runner import run_batches, submit_all_chunks, fetch_all_results
from workflow.direct_tester import (
    estimate_direct_test_cost,
    resolve_direct_test_output_path,
    run_direct_test,
    select_diverse_rows,
    show_direct_test_confirmation,
)
from workflow.output_validator import validate_and_merge
from pricing import PRICING, DEFAULT_MODELS


def parse_args():
    p = argparse.ArgumentParser(description="Batch LLM processing via OpenAI or Gemini")
    p.add_argument("--file", default=None, help="Input file path (CSV, TSV, JSONL)")
    p.add_argument("--goal", default=None, help="Task goal in plain text")
    p.add_argument("--provider", choices=["openai", "gemini"], default="openai")
    p.add_argument("--model", default=None, help="Model ID (default per provider)")
    p.add_argument("--id-column", default=None, help="Column to use as row ID")
    p.add_argument("--columns", default=None, help="Comma-separated text columns for prompt")
    p.add_argument("--output-schema", default=None,
                   help="Output columns: 'col:type,...' e.g. 'action:REDIRECT|DELETE,topic:string'")
    p.add_argument("--output", default=None, help="Output file path (default: <input>_llm_results)")
    p.add_argument("--dry-run", action="store_true", help="Show cost estimate only, do not submit")
    p.add_argument("--direct-test", nargs="?", const=10, type=int, default=None,
                   metavar="N",
                   help="Call the normal provider API on N diverse rows before batch submit (default: 10)")
    p.add_argument("--direct-test-output", default=None,
                   help="Output path for --direct-test results")
    p.add_argument("--async", dest="async_mode", action="store_true",
                   help="Submit all batches and exit immediately (non-blocking)")
    p.add_argument("--fetch", default=None, metavar="OUTPUT_PATH",
                   help="Fetch results for a prior --async run. Pass the original output path.")
    return p.parse_args()


def resolve_output_path(input_path, output_arg):
    if output_arg:
        return output_arg
    base, ext = os.path.splitext(input_path)
    return base + "_llm_results" + (ext if ext in (".csv", ".jsonl") else ".csv")


def parse_columns(columns_arg):
    if not columns_arg:
        return []
    return [c.strip() for c in columns_arg.split(",") if c.strip()]


def parse_output_schema(schema_arg):
    """Parse 'action:REDIRECT|DELETE,topic:string' into list of {name, type}."""
    if not schema_arg:
        return []
    schema = []
    for part in schema_arg.split(","):
        part = part.strip()
        if ":" in part:
            name, col_type = part.split(":", 1)
            schema.append({"name": name.strip(), "type": col_type.strip()})
        elif part:
            schema.append({"name": part, "type": "string"})
    return schema


def auto_select_columns(all_columns):
    """Pick text columns by priority keywords if user didn't specify."""
    priority = ["title", "content", "text", "body", "description", "article", "review"]
    selected = []
    cols_lower = {c.lower(): c for c in all_columns}
    for kw in priority:
        for col_l, col in cols_lower.items():
            if kw in col_l and col not in selected:
                selected.append(col)
                if len(selected) >= 2:
                    return selected
    return all_columns[:2] if not selected else selected


def resolve_text_columns(columns_arg, all_columns):
    requested = parse_columns(columns_arg)
    if requested:
        missing = [col for col in requested if col not in all_columns]
        if missing:
            print(f"ERROR: Requested column(s) not found: {', '.join(missing)}")
            print(f"Available columns: {', '.join(all_columns)}")
            sys.exit(1)
        return requested
    return auto_select_columns(all_columns)


def detect_id_column(all_columns, id_column_arg):
    if id_column_arg and id_column_arg in all_columns:
        return id_column_arg
    for kw in ["id", "url", "slug", "key", "uuid"]:
        for col in all_columns:
            if kw == col.lower():
                return col
    return None


def main_fetch(args):
    """--fetch mode: check status and collect results for a prior --async run."""
    output_path = args.fetch
    state_path = output_path + STATE_FILE_SUFFIX

    state = load_state(state_path)
    if not state:
        print(f"ERROR: No batch state found at: {state_path}")
        print("Run with --async first to submit a batch job.")
        sys.exit(1)

    meta = state.get("meta", {})
    provider = state.get("provider", "openai")
    total_chunks = state.get("total_chunks", 0)
    done_count = len(state.get("completed_chunks", {}))

    print(f"\nBatch state loaded: {done_count}/{total_chunks} chunks completed")
    print(f"Provider: {provider}  |  Model: {state.get('model', '?')}")
    print(f"Checking status of all chunks...\n")

    all_results, still_pending = fetch_all_results(state, state_path, provider)

    if still_pending:
        print(f"\n{len(still_pending)} chunk(s) still processing.")
        print("Run --fetch again when they complete.")
        sys.exit(0)

    # All done — merge and export
    input_file = meta.get("input_file", "")
    if not input_file or not os.path.exists(input_file):
        print(f"\nERROR: Original input file not found: {input_file!r}")
        print("Cannot merge results without the original rows.")
        sys.exit(1)

    print(f"\nAll chunks complete. Loading original file for merge...")
    rows, _ = load_file(input_file)
    output_schema = [
        {"name": s["name"], "type": s["type"]} for s in meta.get("output_schema", [])
    ]
    id_column = meta.get("id_column")

    validate_and_merge(
        original_rows=rows,
        results=all_results,
        output_schema=output_schema,
        id_column=id_column,
        output_path=output_path,
    )

    print(f"\nDone. Results saved to: {output_path}")
    # Clean up state file
    try:
        os.remove(state_path)
    except OSError:
        pass


def main():
    args = parse_args()

    if args.fetch:
        return main_fetch(args)

    # Submit mode (default or --async): --file and --goal are required
    if not args.file:
        print("ERROR: --file is required.")
        sys.exit(1)
    if not args.goal:
        print("ERROR: --goal is required.")
        sys.exit(1)

    # ── 1. Load file
    print(f"Loading {args.file}...")
    rows, columns = load_file(args.file)
    if not rows:
        print("ERROR: File is empty or could not be parsed.")
        sys.exit(1)

    # ── 2. Resolve columns + model
    model = args.model or DEFAULT_MODELS[args.provider]
    text_columns = resolve_text_columns(args.columns, columns)
    id_column = detect_id_column(columns, args.id_column)
    output_schema = parse_output_schema(args.output_schema)
    output_path = resolve_output_path(args.file, args.output)
    state_path = output_path + STATE_FILE_SUFFIX

    # ── 3. Check for existing incomplete batch state
    existing_state = load_state(state_path)
    if existing_state:
        answer = input(
            f"\nFound incomplete batch job "
            f"({len(existing_state.get('completed_chunks', {}))}/"
            f"{existing_state.get('total_chunks', '?')} chunks done).\n"
            f"[r]esume / [s]tart fresh / [c]ancel: "
        ).strip().lower()
        if answer == "c":
            print("Cancelled.")
            sys.exit(0)
        elif answer == "s":
            existing_state = None

    # ── 4. Cost estimation
    estimates = estimate_cost(rows, text_columns, args.goal, PRICING)

    # ── 5a. Direct API test mode: real output quality gate before batch submit
    if args.direct_test is not None:
        sample_size = max(1, args.direct_test)
        sampled_rows = select_diverse_rows(rows, text_columns, sample_size)
        sample_only_rows = [row for _, row in sampled_rows]
        direct_output_path = (
            args.direct_test_output or resolve_direct_test_output_path(output_path)
        )
        selected_estimates = estimates["per_provider"].get(args.provider, {}).get(model, {})
        direct_estimate = estimate_direct_test_cost(
            sample_only_rows, text_columns, args.provider, model
        )
        confirmed = show_direct_test_confirmation(
            file_path=args.file,
            total_rows=len(rows),
            sample_indices=[idx for idx, _ in sampled_rows],
            text_columns=text_columns,
            goal=args.goal,
            output_schema=output_schema,
            provider=args.provider,
            model=model,
            direct_estimate=direct_estimate,
            full_batch_cost=selected_estimates.get("cost", 0.0),
            output_path=direct_output_path,
            dry_run=args.dry_run,
        )
        if args.dry_run or not confirmed:
            print("Dry-run complete. No direct API calls made." if args.dry_run else "Cancelled.")
            sys.exit(0)
        run_direct_test(
            rows=sampled_rows,
            text_columns=text_columns,
            goal=args.goal,
            output_schema=output_schema,
            provider=args.provider,
            model=model,
            output_path=direct_output_path,
        )
        print(f"\nDirect test done. Results saved to: {direct_output_path}")
        return

    # ── 5. Confirmation screen
    confirmed = show_confirmation(
        file_path=args.file,
        rows=rows,
        columns=columns,
        text_columns=text_columns,
        goal=args.goal,
        output_schema=output_schema,
        provider=args.provider,
        model=model,
        estimates=estimates,
        output_path=output_path,
        dry_run=args.dry_run,
    )

    if args.dry_run or not confirmed:
        print("Dry-run complete. No batches submitted." if args.dry_run else "Cancelled.")
        sys.exit(0)

    # ── 6. Initialize or resume state
    selected_estimates = estimates["per_provider"][args.provider][model]
    chunk_size = selected_estimates["chunk_size"]

    state = existing_state or init_state(
        state_path=state_path,
        provider=args.provider,
        model=model,
        total_rows=len(rows),
        chunk_size=chunk_size,
        rows=rows,
        id_column=id_column,
        input_file=args.file,
        output_path=output_path,
        text_columns=text_columns,
        goal=args.goal,
        output_schema=output_schema,
    )

    # ── 7a. Async mode: submit all chunks and exit
    if args.async_mode:
        print(f"\nAsync mode: submitting all chunks without waiting...\n")
        batch_ids = submit_all_chunks(
            state=state,
            state_path=state_path,
            rows=rows,
            text_columns=text_columns,
            id_column=id_column,
            goal=args.goal,
            output_schema=output_schema,
            provider=args.provider,
            model=model,
        )
        total = state["total_chunks"]
        print(f"\n✓ {len(batch_ids)}/{total} chunk(s) submitted.")
        print(f"\nTo fetch results when ready:")
        print(f"  python3 skill.py --fetch {output_path}")
        return

    # ── 7b. Sync mode: submit + poll + collect (original behavior)
    results = run_batches(
        state=state,
        state_path=state_path,
        rows=rows,
        text_columns=text_columns,
        id_column=id_column,
        goal=args.goal,
        output_schema=output_schema,
        provider=args.provider,
        model=model,
    )

    # ── 8. Validate + merge + export
    validate_and_merge(
        original_rows=rows,
        results=results,
        output_schema=output_schema,
        id_column=id_column,
        output_path=output_path,
    )

    print(f"\nDone. Results saved to: {output_path}")


if __name__ == "__main__":
    main()
