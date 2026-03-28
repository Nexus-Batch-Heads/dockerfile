"""
Nexus AI – Chat Routes
=======================
Handles chat interactions: accepts a user message (with optional
file attachment), queries the AI service, persists the conversation
in MS SQL Server, and returns the response.
"""

import logging

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from extensions import db
from models.chat_model import Chat
from models.usage_model import Usage
from services.ai_service import AIService
from services.file_service import save_file
from utils.helpers import error_response, success_response

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")

ai_service = AIService()


# ── POST /api/chat/send ────────────────────────────────────────
@chat_bp.route("/send", methods=["POST"])
@jwt_required()
def send_message():
    """
    Accept a user message (and optional file), call the AI model,
    persist the chat turn, and return the AI response.

    Form fields:
        message (str, required): The user's text input.
        file (file, optional): An image / PDF / text attachment.
    """
    user_id = get_jwt_identity()

    # Accept both JSON and multipart/form-data
    if request.content_type and "multipart" in request.content_type:
        message = request.form.get("message", "").strip()
    else:
        data = request.get_json(silent=True) or {}
        message = data.get("message", "").strip()

    if not message:
        return error_response("Message is required.", 400)

    # ── Optional file attachment ────────────────────────────────
    file_path = None
    file_url = None

    uploaded = request.files.get("file")
    if uploaded and uploaded.filename:
        try:
            meta = save_file(uploaded, current_app.config["UPLOAD_FOLDER"])
            file_path = meta["file_path"]
            file_url = meta["file_path"]  # can be mapped to a public URL later
        except ValueError as exc:
            return error_response(str(exc), 400)

    # ── AI call ─────────────────────────────────────────────────
    try:
        result = ai_service.generate_response(message, file_path)
    except Exception as exc:
        logger.exception("AI service error")
        return error_response(f"AI service error: {exc}", 502)

    ai_response = result["response"]
    usage_data = result["usage"]

    # ── Persist chat turn ───────────────────────────────────────
    chat = Chat(
        user_id=user_id,
        message=message,
        response=ai_response,
        file_url=file_url,
    )
    db.session.add(chat)

    # ── Persist token usage ─────────────────────────────────────
    usage = Usage(
        user_id=user_id,
        prompt_tokens=usage_data.get("prompt_tokens", 0),
        completion_tokens=usage_data.get("completion_tokens", 0),
        total_tokens=usage_data.get("total_tokens", 0),
    )
    db.session.add(usage)
    db.session.commit()

    return success_response(
        data={
            "chat": chat.to_dict(),
            "usage": usage.to_dict(),
        },
        message="Message sent successfully.",
    )


# ── GET /api/chat/history ──────────────────────────────────────
@chat_bp.route("/history", methods=["GET"])
@jwt_required()
def chat_history():
    """Return the authenticated user's chat history (newest first)."""
    user_id = get_jwt_identity()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    pagination = (
        Chat.query.filter_by(user_id=user_id)
        .order_by(Chat.timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return success_response(
        data={
            "chats": [c.to_dict() for c in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }
    )
