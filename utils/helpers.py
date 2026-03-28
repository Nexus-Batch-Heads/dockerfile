"""
Nexus AI – Helper Utilities
=============================
Standardised JSON response builders and input validators.
"""

from __future__ import annotations

import re
from typing import Any

from flask import jsonify


# ── Response Builders ───────────────────────────────────────────

def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = 200,
):
    """
    Build a standardised success JSON response.

    Returns:
        A Flask Response with structure:
        ``{"success": true, "message": "...", "data": ...}``
    """
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status_code


def error_response(
    message: str = "An error occurred",
    status_code: int = 400,
    errors: dict | list | None = None,
):
    """
    Build a standardised error JSON response.

    Returns:
        A Flask Response with structure:
        ``{"success": false, "message": "...", "errors": ...}``
    """
    body: dict[str, Any] = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status_code


# ── Input Validators ───────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)


def is_valid_email(email: str) -> bool:
    """Return True if *email* matches a basic email pattern."""
    return bool(_EMAIL_RE.match(email))


def is_strong_password(password: str, min_length: int = 8) -> bool:
    """
    Check basic password strength:
    - at least *min_length* characters
    - at least one uppercase letter
    - at least one lowercase letter
    - at least one digit
    """
    if len(password) < min_length:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True


def validate_required_fields(data: dict, fields: list[str]) -> list[str]:
    """
    Return a list of missing field names (empty list = all present).
    """
    return [f for f in fields if not data.get(f)]
