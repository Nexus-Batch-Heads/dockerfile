"""
Nexus AI – Usage Model (MS SQL Server)
=======================================
SQLAlchemy model for the 'usage' table tracking AI token
consumption per user.
"""

from datetime import datetime, timezone

from extensions import db


class Usage(db.Model):
    """Tracks token consumption for a single AI interaction."""

    __tablename__ = "usage"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    prompt_tokens = db.Column(db.Integer, default=0, nullable=False)
    completion_tokens = db.Column(db.Integer, default=0, nullable=False)
    total_tokens = db.Column(db.Integer, default=0, nullable=False)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<Usage id={self.id} user={self.user_id} tokens={self.total_tokens}>"
