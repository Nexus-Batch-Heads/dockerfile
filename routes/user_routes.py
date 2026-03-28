"""
Nexus AI – User Routes
=======================
Profile retrieval and token-usage statistics for the
authenticated user.
"""

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from extensions import db
from models.usage_model import Usage
from models.user_model import find_user_by_email
from utils.helpers import error_response, success_response

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


# ── GET /api/user/profile ──────────────────────────────────────
@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    """Return the authenticated user's profile."""
    email = get_jwt_identity()
    user = find_user_by_email(email)

    if not user:
        return error_response("User not found.", 404)

    return success_response(
        data={
            "name": user.get("name"),
            "email": user.get("email"),
            "created_at": (
                user["created_at"].isoformat() if user.get("created_at") else None
            ),
        }
    )


# ── GET /api/user/usage ────────────────────────────────────────
@user_bp.route("/usage", methods=["GET"])
@jwt_required()
def usage_stats():
    """Return aggregated token usage for the authenticated user."""
    user_id = get_jwt_identity()

    totals = (
        db.session.query(
            func.coalesce(func.sum(Usage.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(Usage.completion_tokens), 0).label(
                "completion_tokens"
            ),
            func.coalesce(func.sum(Usage.total_tokens), 0).label("total_tokens"),
            func.count(Usage.id).label("total_requests"),
        )
        .filter(Usage.user_id == user_id)
        .first()
    )

    return success_response(
        data={
            "prompt_tokens": totals.prompt_tokens,
            "completion_tokens": totals.completion_tokens,
            "total_tokens": totals.total_tokens,
            "total_requests": totals.total_requests,
        }
    )
