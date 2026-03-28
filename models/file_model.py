"""
Nexus AI – File Model (MongoDB Atlas)
======================================
Helper functions for the 'files' collection tracking uploaded
file metadata.
"""

from datetime import datetime, timezone

from extensions import mongo_db


def _collection():
    return mongo_db["files"]


def insert_file(user_id: str, file_name: str, file_path: str, file_type: str) -> dict:
    """Insert a file-metadata document and return it as a dict."""
    doc = {
        "user_id": user_id,
        "file_name": file_name,
        "file_path": file_path,
        "file_type": file_type,
        "uploaded_at": datetime.now(timezone.utc),
    }
    result = _collection().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return _to_dict(doc)


def get_user_files(user_id: str) -> list[dict]:
    """Return all files uploaded by a user (newest first)."""
    cursor = (
        _collection()
        .find({"user_id": user_id})
        .sort("uploaded_at", -1)
    )
    return [_to_dict(doc) for doc in cursor]


def _to_dict(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("user_id"),
        "file_name": doc.get("file_name"),
        "file_path": doc.get("file_path"),
        "file_type": doc.get("file_type"),
        "uploaded_at": doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None,
    }
