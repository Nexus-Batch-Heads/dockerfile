"""
Nexus AI – Usage Model (MongoDB Atlas)
=======================================
Helper functions for the 'usage' collection tracking AI token
consumption per user.
"""

from datetime import datetime, timezone

from extensions import mongo_db


def _collection():
    return mongo_db["usage"]


def insert_usage(
    user_id: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
) -> dict:
    """Insert a usage document and return it as a dict."""
    doc = {
        "user_id": user_id,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "timestamp": datetime.now(timezone.utc),
    }
    result = _collection().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return _to_dict(doc)


def get_usage_stats(user_id: str) -> dict:
    """Return aggregated token usage for a user (replaces SQL SUM/COUNT)."""
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "prompt_tokens": {"$sum": "$prompt_tokens"},
                "completion_tokens": {"$sum": "$completion_tokens"},
                "total_tokens": {"$sum": "$total_tokens"},
                "total_requests": {"$sum": 1},
            }
        },
    ]
    results = list(_collection().aggregate(pipeline))
    if results:
        r = results[0]
        return {
            "prompt_tokens": r["prompt_tokens"],
            "completion_tokens": r["completion_tokens"],
            "total_tokens": r["total_tokens"],
            "total_requests": r["total_requests"],
        }
    return {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "total_requests": 0,
    }


def _to_dict(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("user_id"),
        "prompt_tokens": doc.get("prompt_tokens", 0),
        "completion_tokens": doc.get("completion_tokens", 0),
        "total_tokens": doc.get("total_tokens", 0),
        "timestamp": doc["timestamp"].isoformat() if doc.get("timestamp") else None,
    }
