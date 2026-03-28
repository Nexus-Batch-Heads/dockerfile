"""
Nexus AI – Chat Model (MS SQL Server)
======================================
SQLAlchemy model for the 'chats' table storing every
user ↔ AI conversation turn.
"""

from datetime import datetime, timezone

from extensions import db


class Chat(db.Model):
    """Represents a single chat turn (user message + AI response)."""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    file_url = db.Column(db.String(512), nullable=True)
    timestamp = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "response": self.response,
            "file_url": self.file_url,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<Chat id={self.id} user_id={self.user_id}>"
