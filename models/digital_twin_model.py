"""
Nexus AI – Digital Twin Models (MSSQL)
=======================================
SQLAlchemy models for storing generated avatars and
cloned voice profiles in the MSSQL 'nexus' database.
"""

from datetime import datetime, timezone

from extensions import db


class Avatar(db.Model):
    """Stores a user's generated avatar image and facial feature metadata."""

    __tablename__ = "avatars"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    avatar_url = db.Column(db.String(512), nullable=False)
    face_image_url = db.Column(db.String(512), nullable=True)
    facial_features = db.Column(db.Text, nullable=True)       # JSON string
    expression = db.Column(db.String(32), default="neutral")
    skin_tone = db.Column(db.String(16), default="#e0b48c")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "avatar_url": self.avatar_url,
            "face_image_url": self.face_image_url,
            "facial_features": self.facial_features,
            "expression": self.expression,
            "skin_tone": self.skin_tone,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Avatar id={self.id} user_id={self.user_id}>"


class VoiceProfile(db.Model):
    """Stores a user's cloned voice profile and generated audio samples."""

    __tablename__ = "voice_profiles"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    original_audio_url = db.Column(db.String(512), nullable=True)
    cloned_audio_url = db.Column(db.String(512), nullable=True)
    voice_characteristics = db.Column(db.Text, nullable=True)  # JSON string
    voice_model_config = db.Column(db.Text, nullable=True)     # JSON string
    edge_tts_voice = db.Column(db.String(128), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "original_audio_url": self.original_audio_url,
            "cloned_audio_url": self.cloned_audio_url,
            "voice_characteristics": self.voice_characteristics,
            "voice_model_config": self.voice_model_config,
            "edge_tts_voice": self.edge_tts_voice,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<VoiceProfile id={self.id} user_id={self.user_id}>"
