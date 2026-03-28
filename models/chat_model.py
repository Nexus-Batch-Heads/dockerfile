"""
Nexus AI – Chat Model (MongoDB Atlas)
======================================
Helper functions for the 'chats' collection storing every
user ↔ AI conversation turn.
"""

from datetime import datetime, timezone

from extensions import mongo_db


def _collection():
    return mongo_db["chats"]


def insert_chat(user_id: str, message: str, response: str = None, file_url: str = None) -> dict:
    """Insert a chat document and return it as a dict."""
    doc = {
        "user_id": user_id,
        "message": message,
        "response": response,
        "file_url": file_url,
        "timestamp": datetime.now(timezone.utc),
    }
    result = _collection().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return _to_dict(doc)


def get_chats_paginated(user_id: str, page: int = 1, per_page: int = 20) -> dict:
    """Return paginated chat history for a user (newest first)."""
    col = _collection()
    total = col.count_documents({"user_id": user_id})
    skip = (page - 1) * per_page

    cursor = (
        col.find({"user_id": user_id})
        .sort("timestamp", -1)
        .skip(skip)
        .limit(per_page)
    )
    chats = [_to_dict(doc) for doc in cursor]
    pages = max(1, -(-total // per_page))  # ceil division

    return {
        "chats": chats,
        "total": total,
        "page": page,
        "pages": pages,
    }


def _to_dict(doc: dict) -> dict:
    """Convert a MongoDB document to a serialisable dict."""
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("user_id"),
        "message": doc.get("message"),
        "response": doc.get("response"),
        "file_url": doc.get("file_url"),
        "timestamp": doc["timestamp"].isoformat() if doc.get("timestamp") else None,
    }
