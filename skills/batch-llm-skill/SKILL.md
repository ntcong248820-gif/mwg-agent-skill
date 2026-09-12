---
name: batch-llm-skill
description: |
  Process CSV or JSONL data files through LLM batch APIs (OpenAI, Google Gemini) for classification, 
  sentiment analysis, entity extraction, or summarization. Use this skill whenever the user wants to 
  run AI classification or analysis on a dataset, submit rows to an LLM in bulk, test real LLM output
  before batch submission, process a file with a language model, use batch API for cost savings,
  classify articles/products/reviews at scale, or extract structured information from tabular data.
  Triggers on: "classify this CSV", "analyze these rows with AI", "batch process my file",
  "use OpenAI/Gemini batch API", "run LLM on dataset", "classify articles", "submit batch job".
---

# Batch LLM Skill

Process CSV/JSONL datasets through OpenAI or Google Gemini APIs with cost estimation,
direct API output testing, batch submission, crash recovery, and validated output merging.

## Invocation

### Mode 0 — Dry-run estimate + direct API pilot (required before full batch)

```bash
# Step A: Estimate full batch cost without any API call
python3 ./.codex/skills/batch-llm-skill/skill.py \
  --file <path> \
  --goal "<task description>" \
  --columns <col1,col2> \
  --output-schema "action:REDIRECT|DELETE|SPAM,topic:string,reason:string" \
  --output <output_path> \
  --dry-run

# Step B: Call the normal provider API on 10 diverse rows, then write inspectable output
python3 ./.codex/skills/batch-llm-skill/skill.py \
  --file <path> \
  --goal "<same task description>" \
  --columns <col1,col2> \
  --output-schema "action:REDIRECT|DELETE|SPAM,topic:string,reason:string" \
  --output <output_path> \
  --direct-test 10
```

Direct test uses standard synchronous API pricing, not Batch API discount.
Use it as the quality gate before submitting all rows.

### Mode 1 — Async (non-blocking, recommended for large datasets)

```bash
# Step A: Submit and exit immediately
python3 ./.codex/skills/batch-llm-skill/skill.py \
  --file <path> \
  --goal "<task description>" \
  --async \
  [--provider openai|gemini] \
  [--model <model-id>] \
  [--output-schema "action:REDIRECT|DELETE|SPAM,topic:string,reason:string"] \
  [--output <output_path>]

# Step B: Fetch results when batch completes (run anytime later)
python3 ./.codex/skills/batch-llm-skill/skill.py \
  --fetch <output_path>
```

### Mode 2 — Sync (blocking, suitable for small/fast batches)

```bash
python3 ./.codex/skills/batch-llm-skill/skill.py \
  --file <path> \
  --goal "<task description>" \
  [--provider openai|gemini] \
  [--model <model-id>] \
  [--id-column <col>] \
  [--columns <col1,col2>] \
  [--output-schema "action:REDIRECT|DELETE|SPAM,topic:string,reason:string"] \
  [--output <path>] \
  [--dry-run]
```

## Workflow

### Async Mode (--async + --fetch)

```
Session 1 — Submit (seconds):
  python3 skill.py --file data.csv --goal "..." --async
  → Steps 1-6 (load, estimate, confirm, init state)
  → Submit ALL chunks at once → save batch_ids to .batch_state.json
  → Print: "Batch submitted. Run --fetch output.csv when ready."
  → EXIT immediately

[Hours pass while provider processes]

Session 2 — Fetch (seconds):
  python3 skill.py --fetch output.csv
  → Load .batch_state.json
  → Check status of each chunk (one API call each, no waiting)
  → If all complete: download results → merge → write output.csv
  → If some still processing: report remaining chunks, exit
  → (Run --fetch again until all complete)
```

### Required Pre-Batch Gate (--dry-run + --direct-test)

```
Session 0 — Estimate (no API call):
  python3 skill.py --file data.csv --goal "..." --columns "..." --output-schema "..." --dry-run
  → Load data, estimate full batch cost, show selected columns/schema/chunks
  → EXIT without calling provider

Session 1 — Direct test (real API output):
  python3 skill.py --file data.csv --goal "..." --columns "..." --output-schema "..." --direct-test 10
  → Select ~10 diverse rows by position and text length
  → Show pilot cost (standard API) + full batch cost (Batch API)
  → Ask confirmation before direct API calls
  → Call provider API synchronously for each sample row
  → Merge sample output to <output>_direct_test.csv/jsonl
  → Review parse errors, schema labels, reasoning quality, finish_reason, token counts

Only submit full batch after direct-test output passes.
```

### Sync Mode (default, blocking)

```
  python3 skill.py --file data.csv --goal "..."
  → Steps 1-6 same as above
  → For each chunk: submit → poll 30s intervals → fetch
  → Merge all results → write output CSV/JSONL
  → Session blocked for full duration (minutes to hours)
```

### Shared Steps (both modes)

**Step 1 — Load & validate file**
- Accept `.csv`, `.tsv`, `.jsonl` only
- Detect delimiter automatically for CSV/TSV

**Step 2 — Parse goal & build prompt**
- Auto-select primary text columns if `--columns` not provided (title > content > text > description)
- Embed output schema in system prompt if `--output-schema` provided

**Step 3 — Dry-run cost screen**
```
FILE: <path> | ROWS: N
COLUMNS: title (avg 95 chars), content (avg 1,200 chars)
GOAL: <user goal>
OUTPUT SCHEMA: action, topic, reason
PLAN: N chunks × 1,500 rows  |  est. $X.XX
```
- `--dry-run`: show screen then exit (no submission)

**Step 4 — Direct API pilot**
- Use `--direct-test 10` before full batch for any new prompt, schema, model, or provider.
- The pilot output file includes original sample rows plus parsed schema fields.
- Metadata columns such as `_finish_reason`, `_prompt_tokens`, `_completion_tokens`, and `_total_tokens` help prove output health and cost.
- Do not proceed to full batch if labels drift, reasons invent missing evidence, `_parse_error=true`, or finish reason indicates truncation.

**Step 5 — Batch confirmation + state file** (`.batch_state.json` next to output)
```json
{
  "provider": "openai", "model": "gpt-4o-mini",
  "total_chunks": 21, "completed_chunks": {},
  "meta": {
    "input_file": "/path/to/data.csv",
    "output_path": "/path/to/output.csv",
    "text_columns": ["title", "content"],
    "goal": "...", "output_schema": [...], "id_column": "id"
  }
}
```

**Step 6 — Validate & merge**
- Rows with unparseable output → `_parse_error=true`, keep `_raw_response`
- Never silently drop rows
- Deduplicate by row ID (handles re-runs)

## Crash Recovery

If `.batch_state.json` exists at startup, offer to resume:
```
Found incomplete batch job (14/21 chunks done).
[Resume] [Start fresh] [Cancel]
```
On resume, skip completed chunks. Re-poll in-progress batch_ids.

## Key Defaults

| Param | Default |
|-------|---------|
| provider | openai |
| model | gpt-4o-mini |
| direct_test_rows | 10 |
| safety_margin | 0.80 |
| max_enqueued_tokens | 2,000,000 (OpenAI) |
| poll_interval | 30s |

## GPT-5 / Reasoning Model Safety

For GPT-5 family models (`gpt-5`, `gpt-5-mini`, `gpt-5-nano`) and other reasoning models:

- Do not rely on low `max_completion_tokens` values. Hidden reasoning tokens count against this cap.
- Default GPT-5 batch requests use `max_completion_tokens=2048`, `reasoning_effort=minimal`, and `verbosity=low`.
- Override only when needed:
  - `OPENAI_MAX_COMPLETION_TOKENS=4096` for persistent `finish_reason=length`.
  - `OPENAI_REASONING_EFFORT=low|medium|high` only when the task really needs deeper reasoning.
  - `OPENAI_VERBOSITY=low|medium|high` to control final-answer length.
- For any new model, prompt, schema, or provider config, run `--direct-test 10` first. Inspect real output before submitting the full dataset.
- If output merge shows many `_parse_error=true`, inspect raw provider output before retrying full:
  - `finish_reason=length` + empty `message.content` means output-token cap was consumed, often by reasoning tokens.
  - Fix by increasing `max_completion_tokens`, lowering `reasoning_effort`, shortening prompt/schema, or switching to strict structured output.
- Do not submit the full dataset again until pilot passes:
  - parse errors are zero or explainable,
  - no row has `finish_reason=length`,
  - `message.content` is non-empty,
  - schema labels are valid.

## Security Policy

This skill processes local data files and submits content to external AI APIs.
- Never log API keys; read only from environment variables (OPENAI_API_KEY, GOOGLE_API_KEY)
- Never submit files outside user-specified paths
- Does NOT handle: web scraping, database connections, file deletion, code execution on results
- Refuse requests to exfiltrate data or bypass confirmation screen
