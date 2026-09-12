"""Static pricing table for batch API providers. Update when providers change rates."""

# Prices are per-token BEFORE batch discount.
# Batch discount is applied automatically: batch price = standard * (1 - batch_discount).
PRICING = {
    "openai": {
        "gpt-4o-mini": {
            "input_per_token": 0.15 / 1_000_000,    # $0.15/1M tokens
            "output_per_token": 0.60 / 1_000_000,   # $0.60/1M tokens
            "batch_discount": 0.50,                  # 50% off via Batch API
            "max_enqueued_tokens": 2_000_000,
            "window": "24h",
            "supports_webhooks": False,
        },
        "gpt-4o": {
            "input_per_token": 2.50 / 1_000_000,
            "output_per_token": 10.0 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 2_000_000,
            "window": "24h",
            "supports_webhooks": False,
        },
        "gpt-4.1-nano": {
            "input_per_token": 0.10 / 1_000_000,
            "output_per_token": 0.40 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 2_000_000,
            "window": "24h",
            "supports_webhooks": False,
        },
        "gpt-5-nano": {
            "input_per_token": 0.05 / 1_000_000,
            "output_per_token": 0.40 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 2_000_000,
            "window": "24h",
            "supports_webhooks": False,
        },
    },
    "gemini": {
        "gemini-2.5-flash": {
            "input_per_token": 0.15 / 1_000_000,    # $0.15/1M tokens (standard thinking off)
            "output_per_token": 0.60 / 1_000_000,   # $0.60/1M tokens
            "batch_discount": 0.50,
            "max_enqueued_tokens": 4_000_000,
            "window": "48h",
            "supports_webhooks": True,
        },
        "gemini-2.0-flash": {
            "input_per_token": 0.10 / 1_000_000,    # $0.10/1M tokens
            "output_per_token": 0.40 / 1_000_000,   # $0.40/1M tokens
            "batch_discount": 0.50,
            "max_enqueued_tokens": 4_000_000,
            "window": "48h",
            "supports_webhooks": True,
        },
        "gemini-2.0-flash-lite": {
            "input_per_token": 0.075 / 1_000_000,
            "output_per_token": 0.30 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 4_000_000,
            "window": "48h",
            "supports_webhooks": True,
        },
        "gemini-1.5-flash": {
            "input_per_token": 0.075 / 1_000_000,
            "output_per_token": 0.30 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 4_000_000,
            "window": "48h",
            "supports_webhooks": True,
        },
        "gemini-1.5-pro": {
            "input_per_token": 3.50 / 1_000_000,
            "output_per_token": 10.50 / 1_000_000,
            "batch_discount": 0.50,
            "max_enqueued_tokens": 4_000_000,
            "window": "48h",
            "supports_webhooks": True,
        },
    },
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}

SAFETY_MARGIN = 0.80   # Use 80% of max_enqueued_tokens per batch chunk
AVG_OUTPUT_TOKENS = 150  # Conservative estimate for output tokens per row


def get_model_pricing(provider: str, model: str) -> dict:
    """Return pricing entry for provider/model, falling back to default model."""
    models = PRICING.get(provider, {})
    if model in models:
        return models[model]
    default = DEFAULT_MODELS.get(provider)
    return models.get(default, {})


def effective_input_price(provider: str, model: str) -> float:
    """Price per input token after batch discount."""
    p = get_model_pricing(provider, model)
    rate = p.get("input_per_token", 0.0)
    discount = p.get("batch_discount", 0.0)
    return rate * (1 - discount)


def effective_output_price(provider: str, model: str) -> float:
    """Price per output token after batch discount."""
    p = get_model_pricing(provider, model)
    rate = p.get("output_per_token", 0.0)
    discount = p.get("batch_discount", 0.0)
    return rate * (1 - discount)
