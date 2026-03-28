"""
Nexus AI – Upload Routes
=========================
Handles standalone file uploads (outside of the chat flow).
Validates, saves, and records metadata in MS SQL Server.
"""

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.file_model import File
from services.file_service import save_file
from utils.helpers import error_response, success_response

upload_bp = Blueprint("upload", __name__, url_prefix="/api")


# ── POST /api/upload ───────────────────────────────────────────
@upload_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_file():
    """
    Accept a single file upload (image, PDF, or text), save it
    to the uploads directory, and store its metadata.
    """
    user_id = get_jwt_identity()

    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return error_response("No file provided.", 400)

    try:
        meta = save_file(uploaded, current_app.config["UPLOAD_FOLDER"])
    except ValueError as exc:
        return error_response(str(exc), 400)

    # Persist metadata
    file_record = File(
        user_id=user_id,
        file_name=meta["file_name"],
        file_path=meta["file_path"],
        file_type=meta["file_type"],
    )
    db.session.add(file_record)
    db.session.commit()

    return success_response(
        data=file_record.to_dict(),
        message="File uploaded successfully.",
        status_code=201,
    )


# ── GET /api/files ─────────────────────────────────────────────
@upload_bp.route("/files", methods=["GET"])
@jwt_required()
def list_files():
    """Return all files uploaded by the authenticated user."""
    user_id = get_jwt_identity()

    files = (
        File.query.filter_by(user_id=user_id)
        .order_by(File.uploaded_at.desc())
        .all()
    )

    return success_response(
        data=[f.to_dict() for f in files],
    )
