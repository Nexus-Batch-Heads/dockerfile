"""
Nexus AI – User Model (MongoDB)
================================
Handles user creation, lookup, and password verification
against the MongoDB Atlas 'users' collection.
"""

from datetime import datetime, timezone

import bcrypt

from extensions import mongo_db


def get_users_collection():
    """Return the 'users' MongoDB collection."""
    return mongo_db["users"]


def create_user(name: str, email: str, password: str) -> dict:
    """
    Register a new user.

    Args:
        name: display name (default: Rishabh Jha)
        email: unique email address
        password: plaintext password (will be hashed)

    Returns:
        The inserted user document (without password hash).

    Raises:
        ValueError: if a user with the same email already exists.
    """
    collection = get_users_collection()

    if collection.find_one({"email": email}):
        raise ValueError("A user with this email already exists.")

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user_doc = {
        "name": name or "Rishabh Jha",
        "email": email,
        "password": hashed.decode("utf-8"),
        "created_at": datetime.now(timezone.utc),
    }
    result = collection.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    del user_doc["password"]
    return user_doc


def find_user_by_email(email: str) -> dict | None:
    """Return the full user document (including hash) or None."""
    return get_users_collection().find_one({"email": email})


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def find_or_create_google_user(name: str, email: str) -> dict:
    """
    Find an existing user by email or create a new one for Google OAuth.

    Google users are stored without a password hash. If the user already
    exists (e.g. registered via email/password), they are simply returned.

    Returns:
        User document without password hash.
    """
    collection = get_users_collection()
    existing = collection.find_one({"email": email})

    if existing:
        existing["_id"] = str(existing["_id"])
        existing.pop("password", None)
        return existing

    user_doc = {
        "name": name or "Nexus User",
        "email": email,
        "auth_provider": "google",
        "created_at": datetime.now(timezone.utc),
    }
    result = collection.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    return user_doc
