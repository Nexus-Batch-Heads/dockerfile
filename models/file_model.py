"""
Nexus AI – File Model (MS SQL Server)
======================================
SQLAlchemy model for the 'files' table tracking uploaded
file metadata.
"""

from datetime import datetime, timezone

from extensions import db


class File(db.Model):
    """Represents metadata for an uploaded file."""

    __tablename__ = "files"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(64), nullable=False, index=True)
    file_name = db.Column(db.String(256), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(32), nullable=False)
    uploaded_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
        }

    def __repr__(self):
        return f"<File id={self.id} name={self.file_name}>"
