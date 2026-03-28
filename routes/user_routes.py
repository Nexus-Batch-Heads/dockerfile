"""
Nexus AI – User Routes
=======================
Profile retrieval and token-usage statistics for the
authenticated user.
"""

from flask import Blueprint
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.usage_model import get_usage_stats
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
    totals = get_usage_stats(user_id)
    return success_response(data=totals)
