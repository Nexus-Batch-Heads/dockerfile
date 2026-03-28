"""
Nexus AI – Token Counter Utility
=================================
Helpers for parsing and normalising token usage data
returned by AI API responses.
"""

from __future__ import annotations


def parse_usage(raw_usage: dict | None) -> dict[str, int]:
    """
    Normalise a usage dict from an AI API response.

    Args:
        raw_usage: dict that may contain prompt_tokens,
                   completion_tokens, total_tokens.

    Returns:
        dict with guaranteed integer keys for all three fields.
    """
    if not raw_usage:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    prompt = int(raw_usage.get("prompt_tokens", 0))
    completion = int(raw_usage.get("completion_tokens", 0))
    total = int(raw_usage.get("total_tokens", prompt + completion))

    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


def aggregate_usage(records: list[dict]) -> dict[str, int]:
    """
    Sum token counts across multiple usage records.

    Args:
        records: list of dicts each containing the three token fields.

    Returns:
        Aggregated totals.
    """
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for rec in records:
        for key in totals:
            totals[key] += int(rec.get(key, 0))
    return totals
