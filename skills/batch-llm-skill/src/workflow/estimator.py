from __future__ import annotations
"""Token and cost estimation for batch jobs. Uses character heuristic (no tiktoken dependency)."""
import math
from pricing import PRICING, SAFETY_MARGIN, AVG_OUTPUT_TOKENS, get_model_pricing
from pricing import effective_input_price, effective_output_price


# Vietnamese text tokenizes at ~1 token per 2-3 chars; English ~1 per 4 chars.
# Conservative estimate: 1 token per 2.5 chars to avoid underestimation.
CHARS_PER_TOKEN = 2.5


def estimate_tokens_per_row(rows: list[dict], text_columns: list[str], sample_size: int = 50) -> float:
    """Sample rows and estimate average prompt tokens per row via char count."""
    sample = rows[:sample_size]
    if not sample:
        return 500  # safe fallback
    total_chars = 0
    for row in sample:
        for col in text_columns:
            val = str(row.get(col, "") or "")
            total_chars += len(val)
    avg_chars = total_chars / len(sample)
    if avg_chars <= 0:
        return 500
    return avg_chars / CHARS_PER_TOKEN


def calc_chunk_size(avg_tokens_per_row: float, max_enqueued_tokens: int) -> int:
    """Max rows per batch chunk using 80% safety margin."""
    safe_limit = max_enqueued_tokens * SAFETY_MARGIN
    size = int(safe_limit / avg_tokens_per_row)
    return max(1, min(size, 10_000))  # cap at 10k rows per chunk


def estimate_cost(rows: list[dict], text_columns: list[str], goal: str, pricing: dict) -> dict:
    """
    Compute cost estimates for all available providers/models.
    Returns dict with:
      - avg_tokens_per_row
      - chunk_size
      - num_chunks
      - per_provider: {provider: {model: {cost, window, supports_webhooks}}}
    """
    avg_tokens = estimate_tokens_per_row(rows, text_columns)
    total_rows = len(rows)
    per_provider = {}

    for provider, models in pricing.items():
        per_provider[provider] = {}
        for model, info in models.items():
            chunk_size = calc_chunk_size(avg_tokens, info.get("max_enqueued_tokens", 2_000_000))
            num_chunks = math.ceil(total_rows / chunk_size)
            input_cost = total_rows * avg_tokens * effective_input_price(provider, model)
            output_cost = total_rows * AVG_OUTPUT_TOKENS * effective_output_price(provider, model)
            per_provider[provider][model] = {
                "cost": round(input_cost + output_cost, 4),
                "chunk_size": chunk_size,
                "num_chunks": num_chunks,
                "window": info.get("window", "24h"),
                "supports_webhooks": info.get("supports_webhooks", False),
            }

    # Default chunk_size from selected provider/model (openai/gpt-4o-mini)
    default_info = per_provider.get("openai", {}).get("gpt-4o-mini", {})
    return {
        "avg_tokens_per_row": round(avg_tokens),
        "chunk_size": default_info.get("chunk_size", 1500),
        "num_chunks": default_info.get("num_chunks", math.ceil(total_rows / 1500)),
        "per_provider": per_provider,
    }
