"""
Nexus AI – Digital Twin Models (MongoDB Atlas)
===============================================
Helper functions for storing generated avatars and
cloned voice profiles.
"""

from datetime import datetime, timezone

from extensions import mongo_db


# ── Avatar helpers ──────────────────────────────────────────────

def _avatars():
    return mongo_db["avatars"]


def deactivate_avatars(user_id: str):
    """Set is_active=False for all of a user's avatars."""
    _avatars().update_many(
        {"user_id": user_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )


def insert_avatar(
    user_id: str,
    avatar_url: str,
    face_image_url: str = None,
    facial_features: str = None,
    expression: str = "neutral",
    skin_tone: str = "#e0b48c",
) -> dict:
    """Insert a new avatar document (auto-deactivates previous ones)."""
    deactivate_avatars(user_id)
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "avatar_url": avatar_url,
        "face_image_url": face_image_url,
        "facial_features": facial_features,
        "expression": expression,
        "skin_tone": skin_tone,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = _avatars().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return _avatar_to_dict(doc)


def get_active_avatar(user_id: str) -> dict | None:
    """Return the user's active avatar or None."""
    doc = _avatars().find_one({"user_id": user_id, "is_active": True})
    return _avatar_to_dict(doc) if doc else None


def _avatar_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("user_id"),
        "avatar_url": doc.get("avatar_url"),
        "face_image_url": doc.get("face_image_url"),
        "facial_features": doc.get("facial_features"),
        "expression": doc.get("expression"),
        "skin_tone": doc.get("skin_tone"),
        "is_active": doc.get("is_active"),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
    }


# ── Voice Profile helpers ──────────────────────────────────────

def _voice_profiles():
    return mongo_db["voice_profiles"]


def deactivate_voice_profiles(user_id: str):
    """Set is_active=False for all of a user's voice profiles."""
    _voice_profiles().update_many(
        {"user_id": user_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc)}},
    )


def insert_voice_profile(
    user_id: str,
    original_audio_url: str = None,
    cloned_audio_url: str = None,
    voice_characteristics: str = None,
    voice_model_config: str = None,
    edge_tts_voice: str = None,
) -> dict:
    """Insert a new voice profile (auto-deactivates previous ones)."""
    deactivate_voice_profiles(user_id)
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "original_audio_url": original_audio_url,
        "cloned_audio_url": cloned_audio_url,
        "voice_characteristics": voice_characteristics,
        "voice_model_config": voice_model_config,
        "edge_tts_voice": edge_tts_voice,
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }
    result = _voice_profiles().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return _vp_to_dict(doc)


def get_active_voice_profile(user_id: str) -> dict | None:
    """Return the user's active voice profile or None."""
    doc = _voice_profiles().find_one({"user_id": user_id, "is_active": True})
    return _vp_to_dict(doc) if doc else None


def _vp_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc.get("_id", "")),
        "user_id": doc.get("user_id"),
        "original_audio_url": doc.get("original_audio_url"),
        "cloned_audio_url": doc.get("cloned_audio_url"),
        "voice_characteristics": doc.get("voice_characteristics"),
        "voice_model_config": doc.get("voice_model_config"),
        "edge_tts_voice": doc.get("edge_tts_voice"),
        "is_active": doc.get("is_active"),
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
        "updated_at": doc["updated_at"].isoformat() if doc.get("updated_at") else None,
    }
