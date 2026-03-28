from flask import Blueprint, request, current_app
from flask_jwt_extended import create_access_token

from models.user_model import (
    create_user,
    find_or_create_google_user,
    find_user_by_email,
    verify_password,
)
from utils.helpers import (
    error_response,
    is_strong_password,
    is_valid_email,
    success_response,
    validate_required_fields,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ── POST /api/auth/register ────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json(silent=True) or {}

    # Validate required fields
    missing = validate_required_fields(data, ["email", "password"])
    if missing:
        return error_response(
            f"Missing required fields: {', '.join(missing)}", 400
        )

    email = data["email"].strip().lower()
    password = data["password"]
    name = data.get("name", "Rishabh Jha").strip()

    # Validate email format
    if not is_valid_email(email):
        return error_response("Invalid email format.", 400)

    # Validate password strength
    if not is_strong_password(password):
        return error_response(
            "Password must be at least 8 characters with uppercase, "
            "lowercase, and a digit.",
            400,
        )

    # Create user
    try:
        user = create_user(name, email, password)
    except ValueError as exc:
        return error_response(str(exc), 409)

    # Issue JWT
    token = create_access_token(identity=email)

    return success_response(
        data={"user": user, "access_token": token},
        message="Registration successful.",
        status_code=201,
    )


# ── POST /api/auth/login ───────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data = request.get_json(silent=True) or {}

    missing = validate_required_fields(data, ["email", "password"])
    if missing:
        return error_response(
            f"Missing required fields: {', '.join(missing)}", 400
        )

    email = data["email"].strip().lower()
    password = data["password"]

    user = find_user_by_email(email)
    if not user or not verify_password(password, user["password"]):
        return error_response("Invalid email or password.", 401)

    token = create_access_token(identity=email)

    return success_response(
        data={
            "access_token": token,
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
            },
        },
        message="Login successful.",
    )


# ── POST /api/auth/google ──────────────────────────────────────
@auth_bp.route("/google", methods=["POST"])
def google_auth():
    """Authenticate via Google OAuth – verify ID token and return JWT."""
    data = request.get_json(silent=True) or {}
    credential = data.get("credential")

    if not credential:
        return error_response("Missing Google credential token.", 400)

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        return error_response("Google OAuth is not configured.", 500)

    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests

        id_info = google_id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )

        email = id_info.get("email", "").strip().lower()
        name = id_info.get("name", "")

        if not email:
            return error_response("Could not retrieve email from Google.", 400)

    except ValueError:
        return error_response("Invalid or expired Google token.", 401)

    # Find or create user
    user = find_or_create_google_user(name, email)
    token = create_access_token(identity=email)

    return success_response(
        data={
            "access_token": token,
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
            },
        },
        message="Google login successful.",
    )


# ── GET /api/auth/me ───────────────────────────────────────────
from flask_jwt_extended import jwt_required, get_jwt_identity

@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get the currently authenticated user's profile."""
    email = get_jwt_identity()
    user = find_user_by_email(email)
    
    if not user:
        return error_response("User not found.", 404)
        
    return success_response(
        data={
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
            }
        },
        message="User profile retrieved.",
    )
