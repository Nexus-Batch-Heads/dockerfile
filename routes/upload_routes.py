"""
Nexus AI – Upload Routes
=========================
Handles standalone file uploads (outside of the chat flow).
Validates, saves, and records metadata in MongoDB Atlas.
"""

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.file_model import insert_file, get_user_files
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
    file_record = insert_file(
        user_id=user_id,
        file_name=meta["file_name"],
        file_path=meta["file_path"],
        file_type=meta["file_type"],
    )

    return success_response(
        data=file_record,
        message="File uploaded successfully.",
        status_code=201,
    )


# ── GET /api/files ─────────────────────────────────────────────
@upload_bp.route("/files", methods=["GET"])
@jwt_required()
def list_files():
    """Return all files uploaded by the authenticated user."""
    user_id = get_jwt_identity()
    files = get_user_files(user_id)
    return success_response(data=files)
